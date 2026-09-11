"""Update docs/js/config.js with a new dashboard password hash."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "docs" / "js" / "config.js"


def main() -> None:
    if len(sys.argv) < 2:
        print("ใช้แบบ: python pipeline/set_password.py รหัสผ่านใหม่")
        sys.exit(1)
    password = sys.argv[1]
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG.exists():
        text = CONFIG.read_text(encoding="utf-8")
        updated = re.sub(r'passwordHash:\s*"[^"]*"', f'passwordHash: "{digest}"', text)
        if updated == text and "passwordHash" not in text:
            updated = (
                "window.APP_CONFIG = {\n"
                f'  passwordHash: "{digest}",\n'
                '  githubRepo: ""\n'
                "};\n"
            )
        CONFIG.write_text(updated, encoding="utf-8")
    else:
        CONFIG.write_text(
            "window.APP_CONFIG = {\n"
            f'  passwordHash: "{digest}",\n'
            '  githubRepo: ""\n'
            "};\n",
            encoding="utf-8",
        )
    print("อัปเดตรหัสผ่านใน docs/js/config.js แล้ว — อย่าลืม commit และ push")


if __name__ == "__main__":
    main()
