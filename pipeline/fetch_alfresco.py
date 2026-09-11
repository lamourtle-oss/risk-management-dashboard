from __future__ import annotations

import os
from pathlib import Path

import requests


class AlfrescoError(RuntimeError):
    pass


def configured() -> bool:
    return all(
        os.environ.get(k)
        for k in ("ALFRESCO_BASE_URL", "ALFRESCO_USERNAME", "ALFRESCO_PASSWORD", "ALFRESCO_FOLDER_ID")
    )


def download_folder(dest: Path) -> list[Path]:
    base = os.environ["ALFRESCO_BASE_URL"].rstrip("/")
    folder_id = os.environ["ALFRESCO_FOLDER_ID"]
    auth = (os.environ["ALFRESCO_USERNAME"], os.environ["ALFRESCO_PASSWORD"])
    list_url = f"{base}/alfresco/api/-default-/public/alfresco/versions/1/nodes/{folder_id}/children"
    response = requests.get(
        list_url,
        auth=auth,
        params={"where": "(isFile=true)", "maxItems": 200},
        timeout=60,
    )
    if response.status_code >= 400:
        raise AlfrescoError(f"อ่านโฟลเดอร์ Alfresco ไม่ได้: {response.status_code} {response.text}")
    entries = response.json().get("list", {}).get("entries", [])
    dest.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for item in entries:
        entry = item.get("entry", {})
        name = entry.get("name", "")
        if not name.lower().endswith((".xlsx", ".xls", ".xlsm", ".pptx", ".pptm")):
            continue
        node_id = entry["id"]
        content = requests.get(
            f"{base}/alfresco/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content",
            auth=auth,
            timeout=120,
        )
        content.raise_for_status()
        path = dest / name
        path.write_bytes(content.content)
        saved.append(path)
        print(f"Downloaded {path.name}")
    if not saved:
        raise AlfrescoError("ไม่พบไฟล์ Excel หรือ PowerPoint ในโฟลเดอร์ Alfresco")
    return saved
