"""End-to-end automated live test runner for Page Sentinel.

Launches the mock server, runs Sentinel against http://127.0.0.1:8080/index.html,
waits for initial baseline, injects a new PDF into the page, and demonstrates
real-time change detection with live dispatch to Discord and ntfy.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

DEMO_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DEMO_DIR.parent
HTML_FILE = DEMO_DIR / "index.html"
STATE_FILE = DEMO_DIR / "demo_state.json"

from demo import BASE_HTML, add_document, reset_html, run_server
import threading


def main():
    print("\n" + "=" * 65)
    print(" 🚀 STARTING LIVE REAL-TIME TEST FOR PAGE SENTINEL")
    print("=" * 65)

    # 1. Clean previous test state & reset HTML
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    reset_html()

    # 2. Start local HTTP server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    print("[STEP 1] Mock server online at http://127.0.0.1:8080/index.html")
    print("[STEP 2] Launching Sentinel with 5-second polling interval...")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["TARGET_URL"] = "http://127.0.0.1:8080/index.html"
    env["CHECK_INTERVAL"] = "5"
    env["STATE_FILE"] = str(STATE_FILE)

    proc = subprocess.Popen(
        [sys.executable, str(PROJECT_DIR / "sentinel.py")],
        cwd=str(PROJECT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    def read_output():
        for line in proc.stdout:
            print(f"  | {line.rstrip()}")

    out_thread = threading.Thread(target=read_output, daemon=True)
    out_thread.start()

    # Wait for sentinel to complete first run baseline
    print("\n[STEP 3] Waiting for Sentinel to establish baseline snapshot...")
    time.sleep(7)

    print("\n[STEP 4] ⚡ SIMULATING FACULTY PUBLISHING A NEW RESULT PDF ⚡")
    add_document("Resultats_Admissibilite_Master_2026.pdf")
    print("Waiting for next Sentinel polling cycle (5 seconds)...")

    # Wait for check cycle to pick up change and send alerts
    time.sleep(10)

    print("\n[STEP 5] Stopping test...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()

    print("\n" + "=" * 65)
    print(" ✅ LIVE DEMO COMPLETED!")
    print(" Check your Discord channel and phone (ntfy) for the alert!")
    print("=" * 65)


if __name__ == "__main__":
    main()
