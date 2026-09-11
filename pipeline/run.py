"""Fetch from OneDrive/Alfresco (or local files), then rebuild dashboard data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from generate_sample import main as generate_sample  # noqa: E402
from process import process  # noqa: E402


INBOX = ROOT / "inbox"
SAMPLE = ROOT / "sample-data"


def _has_office_files(folder: Path) -> bool:
    if not folder.exists():
        return False
    return any(
        p.is_file() and p.suffix.lower() in {".xlsx", ".xls", ".xlsm", ".pptx", ".pptm"} and not p.name.startswith("~$")
        for p in folder.rglob("*")
    )


def collect_input() -> tuple[Path, str]:
    INBOX.mkdir(parents=True, exist_ok=True)

    from fetch_onedrive import download_folder, local_path, local_ready

    if local_ready():
        path = local_path()
        print(f"ใช้ไฟล์ SharePoint ที่ซิงค์บนเครื่อง: {path}")
        return path, "sharepoint-local"

    if os.environ.get("ONEDRIVE_TENANT_ID") or os.environ.get("SHAREPOINT_URL"):
        from fetch_onedrive import configured, graph_configured

        if configured():
            print("กำลังดึงไฟล์จาก SharePoint...")
            download_folder(INBOX)
            return INBOX, "sharepoint"
        if graph_configured() and not os.environ.get("ONEDRIVE_CLIENT_SECRET"):
            print("ตั้งค่า SharePoint แล้ว แต่ยังไม่ได้ล็อกอิน")
            print("รัน: .\\.venv\\Scripts\\python pipeline\\connect_sharepoint.py")
        elif os.environ.get("SHAREPOINT_URL") and not graph_configured():
            print("รู้จักโฟลเดอร์ SharePoint แล้ว แต่ยังไม่มี Azure app (ONEDRIVE_CLIENT_ID)")
            print("หรือซิงค์โฟลเดอร์ Risk Management ลงเครื่อง แล้วกดรีเฟรชอีกครั้ง")

    if os.environ.get("ALFRESCO_BASE_URL"):
        from fetch_alfresco import configured, download_folder

        if configured():
            print("กำลังดึงไฟล์จาก Alfresco...")
            download_folder(INBOX)
            return INBOX, "alfresco"

    if _has_office_files(INBOX):
        print("ใช้ไฟล์ในโฟลเดอร์ inbox/")
        return INBOX, "inbox"

    if not _has_office_files(SAMPLE):
        print("ยังไม่มีไฟล์ตัวอย่าง กำลังสร้างให้...")
        generate_sample()
    print("ใช้ไฟล์ตัวอย่างใน sample-data/")
    return SAMPLE, "sample"


def main() -> None:
    input_dir, source = collect_input()
    process(input_dir, source)


if __name__ == "__main__":
    main()
