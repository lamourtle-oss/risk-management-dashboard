"""Local dashboard server with a /api/refresh endpoint."""

from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RUN = ROOT / "pipeline" / "run.py"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/refresh":
            self.send_error(404)
            return
        completed = subprocess.run(
            [sys.executable, str(RUN)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        payload = {
            "ok": completed.returncode == 0,
            "log": (completed.stdout or "") + (completed.stderr or ""),
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200 if payload["ok"] else 500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"เปิดแดชบอร์ดที่ http://127.0.0.1:{port}")
    print("รหัสผ่านเริ่มต้น: Risk2026")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nปิดเซิร์ฟเวอร์แล้ว")


if __name__ == "__main__":
    main()
