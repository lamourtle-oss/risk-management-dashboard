"""Log in to Singer SharePoint once, then download Risk Management files."""

from __future__ import annotations

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

from fetch_onedrive import device_code_login, download_folder, graph_configured, target


def main() -> None:
    info = target()
    print("เป้าหมาย:", f"{info['hostname']}{info['site_path']} / {info['library']} / {info['folder']}")
    if not graph_configured():
        print("ยังไม่มี ONEDRIVE_TENANT_ID หรือ ONEDRIVE_CLIENT_ID ในไฟล์ .env")
        print("สร้าง App registration ใน Azure แล้วใส่ Client ID ก่อน แล้วรันคำสั่งนี้อีกครั้ง")
        sys.exit(1)
    device_code_login()
    inbox = ROOT / "inbox"
    files = download_folder(inbox)
    print(f"ดึงมา {len(files)} ไฟล์ ไว้ที่ {inbox}")


if __name__ == "__main__":
    main()
