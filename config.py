"""Configuration loader for Page Sentinel.

Loads runtime configuration from environment variables and an optional .env file.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
except ImportError:
    pass

# Application metadata
APP_NAME: str = "Page Sentinel"
APP_VERSION: str = "1.1.0"
APP_USER_AGENT: str = f"{APP_NAME}/{APP_VERSION} (+https://github.com/Se7enWay/page-sentinel)"

# Target configuration
TARGET_URL: str = os.getenv(
    "TARGET_URL",
    "http://fsr.ac.ma/DOC/Preselections/Cycle_Masters/LISTES_CONCOURS_ECRIT/",
).strip()

# Polling interval (enforce a safe lower bound to prevent unintentional DoS)
raw_interval = int(os.getenv("CHECK_INTERVAL", "30"))
CHECK_INTERVAL: int = max(5, raw_interval)

# Notifier toggles and credentials
NTFY_ENABLED: bool = os.getenv("NTFY_ENABLED", "true").lower() in ("true", "1", "yes")
NTFY_TOPIC: str = os.getenv("NTFY_TOPIC", "page-sentinel").strip()
NTFY_SERVER: str = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_PRIORITY: int = int(os.getenv("NTFY_PRIORITY", "4"))

DISCORD_ENABLED: bool = os.getenv("DISCORD_ENABLED", "true").lower() in ("true", "1", "yes")
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Scraping & filtering rules
LINK_SELECTOR: str = os.getenv("LINK_SELECTOR", "a[href]").strip()
raw_extensions: str = os.getenv("FILE_EXTENSIONS", ".pdf").strip()

WATCHED_EXTENSIONS: list[str] = [
    ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}"
    for ext in raw_extensions.split(",")
    if ext.strip()
]

# State persistence
_PROJECT_DIR: Path = Path(__file__).resolve().parent
STATE_FILE: Path = Path(os.getenv("STATE_FILE", str(_PROJECT_DIR / "state.json")))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
