"""Download Excel and PowerPoint files from SharePoint / OneDrive via Microsoft Graph."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests

GRAPH = "https://graph.microsoft.com/v1.0"
ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / ".sharepoint-token.json"
OFFICE_SUFFIXES = {".xlsx", ".xls", ".xlsm", ".pptx", ".pptm"}

DEFAULT_HOST = "singerthaicoth.sharepoint.com"
DEFAULT_SITE_PATH = "/sites/ITAudit"
DEFAULT_LIBRARY = "Shared Documents"
DEFAULT_FOLDER = "Risk Management"
DEFAULT_LOCAL = (
    Path.home()
    / "OneDrive - Singer Thailand Public Company Limited"
    / "Internal Audit and Risk Management - Risk Management"
)


class OneDriveError(RuntimeError):
    pass


def parse_sharepoint_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    hostname = parsed.netloc or DEFAULT_HOST
    item_path = unquote(parse_qs(parsed.query).get("id", [""])[0]).strip("/")
    parts = [p for p in item_path.split("/") if p] if item_path else [p for p in unquote(parsed.path).split("/") if p]
    site_path = DEFAULT_SITE_PATH
    rest = parts
    if len(parts) >= 2 and parts[0].lower() == "sites":
        site_path = f"/{parts[0]}/{parts[1]}"
        rest = parts[2:]
        if rest and rest[0].lower() == "forms":
            rest = []
    library = DEFAULT_LIBRARY
    folder = DEFAULT_FOLDER
    if rest:
        library = rest[0]
        folder = "/".join(rest[1:]) if len(rest) > 1 else ""
    return {
        "hostname": hostname,
        "site_path": site_path,
        "library": library,
        "folder": folder,
    }


def target() -> dict[str, str]:
    url = (os.environ.get("SHAREPOINT_URL") or "").strip()
    if url:
        info = parse_sharepoint_url(url)
    else:
        info = {
            "hostname": os.environ.get("SHAREPOINT_HOSTNAME") or DEFAULT_HOST,
            "site_path": os.environ.get("SHAREPOINT_SITE_PATH") or DEFAULT_SITE_PATH,
            "library": os.environ.get("SHAREPOINT_LIBRARY") or DEFAULT_LIBRARY,
            "folder": os.environ.get("SHAREPOINT_FOLDER_PATH")
            or os.environ.get("ONEDRIVE_FOLDER_PATH")
            or DEFAULT_FOLDER,
        }
    if os.environ.get("SHAREPOINT_FOLDER_PATH"):
        info["folder"] = os.environ["SHAREPOINT_FOLDER_PATH"].strip().strip("/")
    if os.environ.get("SHAREPOINT_LIBRARY"):
        info["library"] = os.environ["SHAREPOINT_LIBRARY"].strip()
    return info


def local_path() -> Path | None:
    raw = (os.environ.get("SHAREPOINT_LOCAL_PATH") or "").strip()
    path = Path(raw) if raw else DEFAULT_LOCAL
    return path if path.exists() else None


def _is_office(name: str) -> bool:
    lower = name.lower()
    return any(lower.endswith(ext) for ext in OFFICE_SUFFIXES) and not name.startswith("~$")


def has_office_files(folder: Path) -> bool:
    if not folder.exists():
        return False
    return any(p.is_file() and _is_office(p.name) for p in folder.rglob("*"))


def local_ready() -> bool:
    path = local_path()
    return bool(path and has_office_files(path))


def graph_configured() -> bool:
    return bool(os.environ.get("ONEDRIVE_TENANT_ID") and os.environ.get("ONEDRIVE_CLIENT_ID"))


def configured() -> bool:
    return local_ready() or (graph_configured() and bool(os.environ.get("ONEDRIVE_CLIENT_SECRET") or TOKEN_PATH.exists()))


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _tenant() -> str:
    tenant = (os.environ.get("ONEDRIVE_TENANT_ID") or "").strip()
    if not tenant:
        raise OneDriveError("ยังไม่ได้ตั้ง ONEDRIVE_TENANT_ID")
    return tenant


def _client_credentials_token() -> str:
    data = {
        "client_id": os.environ["ONEDRIVE_CLIENT_ID"],
        "client_secret": os.environ["ONEDRIVE_CLIENT_SECRET"],
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    url = f"https://login.microsoftonline.com/{_tenant()}/oauth2/v2.0/token"
    response = requests.post(url, data=data, timeout=60)
    if response.status_code >= 400:
        raise OneDriveError(f"ไม่ได้รับ token จาก Microsoft: {response.status_code} {response.text}")
    return response.json()["access_token"]


def _load_cached_token() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _save_cached_token(payload: dict) -> None:
    payload = dict(payload)
    payload["obtained_at"] = int(time.time())
    TOKEN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _refresh_delegated_token(refresh_token: str) -> dict:
    data = {
        "client_id": os.environ["ONEDRIVE_CLIENT_ID"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://graph.microsoft.com/Sites.Read.All Files.Read.All offline_access",
    }
    secret = os.environ.get("ONEDRIVE_CLIENT_SECRET")
    if secret:
        data["client_secret"] = secret
    url = f"https://login.microsoftonline.com/{_tenant()}/oauth2/v2.0/token"
    response = requests.post(url, data=data, timeout=60)
    if response.status_code >= 400:
        raise OneDriveError(f"ต่ออายุ token ไม่ได้: {response.status_code} {response.text}")
    payload = response.json()
    _save_cached_token(payload)
    return payload


def device_code_login() -> str:
    tenant = _tenant()
    client_id = os.environ.get("ONEDRIVE_CLIENT_ID")
    if not client_id:
        raise OneDriveError("ต้องมี ONEDRIVE_CLIENT_ID สำหรับการล็อกอิน")
    start = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode",
        data={
            "client_id": client_id,
            "scope": "https://graph.microsoft.com/Sites.Read.All Files.Read.All offline_access",
        },
        timeout=60,
    )
    if start.status_code >= 400:
        raise OneDriveError(f"เริ่ม device login ไม่ได้: {start.status_code} {start.text}")
    info = start.json()
    print(info.get("message") or f"เปิด {info.get('verification_uri')} แล้วใส่รหัส {info.get('user_code')}")
    interval = int(info.get("interval") or 5)
    expires = int(info.get("expires_in") or 900)
    deadline = time.time() + expires
    while time.time() < deadline:
        time.sleep(interval)
        poll = requests.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "client_id": client_id,
                "device_code": info["device_code"],
            },
            timeout=60,
        )
        payload = poll.json()
        if poll.status_code < 400 and payload.get("access_token"):
            _save_cached_token(payload)
            print("ล็อกอิน SharePoint สำเร็จ")
            return payload["access_token"]
        error = payload.get("error")
        if error in {"authorization_pending", "slow_down"}:
            if error == "slow_down":
                interval += 2
            continue
        raise OneDriveError(f"ล็อกอินไม่สำเร็จ: {payload}")
    raise OneDriveError("หมดเวลารอการล็อกอิน")


def _token() -> str:
    if os.environ.get("ONEDRIVE_CLIENT_SECRET"):
        return _client_credentials_token()
    cached = _load_cached_token()
    if cached and cached.get("access_token"):
        obtained = int(cached.get("obtained_at") or 0)
        expires_in = int(cached.get("expires_in") or 0)
        if obtained and expires_in and time.time() < obtained + expires_in - 120:
            return cached["access_token"]
        if cached.get("refresh_token"):
            return _refresh_delegated_token(cached["refresh_token"])["access_token"]
    raise OneDriveError("ยังไม่มีสิทธิ์เข้า SharePoint — รัน python pipeline/connect_sharepoint.py หรือใส่ ONEDRIVE_CLIENT_SECRET")


def _site_id(token: str, info: dict[str, str]) -> str:
    site_path = info["site_path"].strip("/")
    url = f"{GRAPH}/sites/{info['hostname']}:/{site_path}"
    response = requests.get(url, headers=_headers(token), timeout=60)
    if response.status_code >= 400:
        raise OneDriveError(f"หาไซต์ SharePoint ไม่เจอ ({url}): {response.status_code} {response.text}")
    return response.json()["id"]


def _drive_id(token: str, site_id: str, library: str) -> str:
    drives = requests.get(f"{GRAPH}/sites/{site_id}/drives", headers=_headers(token), timeout=60)
    if drives.status_code < 400:
        wanted = library.strip().lower()
        aliases = {wanted, "documents", "shared documents"}
        for drive in drives.json().get("value", []):
            name = str(drive.get("name") or "").strip().lower()
            if name in aliases:
                return drive["id"]
        if drives.json().get("value"):
            return drives.json()["value"][0]["id"]
    fallback = requests.get(f"{GRAPH}/sites/{site_id}/drive", headers=_headers(token), timeout=60)
    if fallback.status_code >= 400:
        raise OneDriveError(f"หาไลบรารีเอกสารไม่ได้: {drives.status_code} {drives.text}")
    return fallback.json()["id"]


def _children(token: str, url: str) -> list[dict]:
    items: list[dict] = []
    while url:
        response = requests.get(url, headers=_headers(token), timeout=60)
        if response.status_code >= 400:
            raise OneDriveError(f"อ่านโฟลเดอร์ SharePoint ไม่ได้: {response.status_code} {response.text}")
        payload = response.json()
        items.extend(payload.get("value", []))
        url = payload.get("@odata.nextLink")
    return items


def _list_folder(token: str, drive_id: str, folder: str) -> list[dict]:
    folder = folder.strip().strip("/")
    if folder:
        url = f"{GRAPH}/drives/{drive_id}/root:/{quote(folder, safe='/')}:/children"
    else:
        url = f"{GRAPH}/drives/{drive_id}/root/children"
    return _children(token, url)


def _walk_and_download(token: str, drive_id: str, folder: str, dest_root: Path, prefix: Path | None = None) -> list[Path]:
    saved: list[Path] = []
    for item in _list_folder(token, drive_id, folder):
        name = item.get("name") or "item"
        rel = (prefix / name) if prefix else Path(name)
        if item.get("folder"):
            child_folder = f"{folder}/{name}" if folder else name
            saved.extend(_walk_and_download(token, drive_id, child_folder, dest_root, rel))
            continue
        if not _is_office(name):
            continue
        path = dest_root / rel
        download_url = item.get("@microsoft.graph.downloadUrl")
        if download_url:
            content = requests.get(download_url, timeout=180)
        else:
            content = requests.get(
                f"{GRAPH}/drives/{drive_id}/items/{item['id']}/content",
                headers=_headers(token),
                timeout=180,
            )
        content.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.content)
        saved.append(path)
        print(f"Downloaded {rel}")
    return saved


def _clear_office_files(dest: Path) -> None:
    if not dest.exists():
        return
    for path in dest.rglob("*"):
        if path.is_file() and _is_office(path.name):
            path.unlink()


def download_folder(dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    if local_ready():
        print(f"ใช้ไฟล์ที่ซิงค์บนเครื่อง: {local_path()}")
        return list(local_path().rglob("*"))

    info = target()
    print(f"กำลังดึงจาก SharePoint {info['hostname']}{info['site_path']} / {info['library']} / {info['folder']}")
    token = _token()
    site_id = _site_id(token, info)
    drive_id = _drive_id(token, site_id, info["library"])
    _clear_office_files(dest)
    saved = _walk_and_download(token, drive_id, info["folder"], dest)
    if not saved:
        raise OneDriveError("ไม่พบไฟล์ Excel หรือ PowerPoint ในโฟลเดอร์ Risk Management")
    return saved
