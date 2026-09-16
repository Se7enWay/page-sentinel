"""Interactive Live Test Server for Page Sentinel.

Serves a mock HTML page at http://127.0.0.1:8080 and provides an interactive
prompt to simulate the release of new documents in real time.
"""

from __future__ import annotations

import http.server
import os
from pathlib import Path
import socketserver
import threading
import time

DEMO_DIR = Path(__file__).resolve().parent
HTML_FILE = DEMO_DIR / "index.html"
PORT = 8080

BASE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Faculté des Sciences - Listes Concours Master</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 750px; margin: 40px auto; padding: 0 20px; background: #f8fafc; color: #1e293b; }
        header { background: #1e40af; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        h1 { margin: 0 0 6px 0; font-size: 22px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 12px 14px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
        a { color: #2563eb; text-decoration: none; font-weight: 500; }
        .badge { background: #e2e8f0; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
        .badge.new { background: #dcfce7; color: #15803d; font-weight: bold; }
    </style>
</head>
<body>
    <header>
        <h1>Faculté des Sciences — Rabat</h1>
        <p style="margin:0; opacity:0.9; font-size:13px;">Affichage Officiel des Concours Master 2026</p>
    </header>

    <div class="card">
        <h3>Documents Publiés</h3>
        <ul id="documents">
            <li>
                <a href="Avis_Concours_Masters_2026.pdf">📄 Avis_Concours_Masters_2026.pdf</a>
                <span class="badge">Initial</span>
            </li>
            <li>
                <a href="Calendrier_Des_Epreuves.pdf">📄 Calendrier_Des_Epreuves.pdf</a>
                <span class="badge">Initial</span>
            </li>
<!-- INJECT_POINT -->
        </ul>
    </div>
</body>
</html>
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress routine GET logs for clean console
        pass


def reset_html() -> None:
    HTML_FILE.write_text(BASE_HTML, encoding="utf-8")


def add_document(filename: str) -> None:
    content = HTML_FILE.read_text(encoding="utf-8")
    new_entry = f"""            <li style="background: #f0fdf4;">
                <a href="{filename}">🔥 {filename}</a>
                <span class="badge new">NOUVEAU !</span>
            </li>
<!-- INJECT_POINT -->"""
    content = content.replace("<!-- INJECT_POINT -->", new_entry)
    HTML_FILE.write_text(content, encoding="utf-8")
    print(f"\n[DEMO WEB] 🌐 Added new file to page: {filename}")


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler) as httpd:
        print(f"[DEMO WEB] Serving mock page at: http://127.0.0.1:{PORT}/index.html")
        httpd.serve_forever()


if __name__ == "__main__":
    reset_html()
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    print("\n" + "=" * 60)
    print(" 🧪 PAGE SENTINEL LIVE SIMULATOR")
    print("=" * 60)
    print(f"Mock site is running at: http://127.0.0.1:{PORT}/index.html")
    print("Baseline has 2 initial files.\n")
    print("Commands:")
    print("  [1] Add 'Resultats_Admissibilite_Master_DS_2026.pdf'")
    print("  [2] Add 'Liste_Finale_Admis_Master_Cyber_2026.pdf'")
    print("  [r] Reset page to initial state")
    print("  [q] Quit\n")

    while True:
        try:
            cmd = input("Enter choice [1, 2, r, q]: ").strip().lower()
            if cmd == "1":
                add_document("Resultats_Admissibilite_Master_DS_2026.pdf")
            elif cmd == "2":
                add_document("Liste_Finale_Admis_Master_Cyber_2026.pdf")
            elif cmd == "r":
                reset_html()
                print("[DEMO WEB] 🔄 Reset page to initial state.")
            elif cmd == "q":
                print("Exiting demo server.")
                break
        except (KeyboardInterrupt, EOFError):
            break
