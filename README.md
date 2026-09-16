<div align="center">

# 🛡️ Page Sentinel

**Production-grade, real-time web directory change monitor with delivery guarantees.**

[![CI](https://github.com/Se7enWay/page-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/Se7enWay/page-sentinel/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style: Clean](https://img.shields.io/badge/code%20style-pep8-blueviolet.svg)](https://peps.python.org/pep-0008/)

</div>

---

## Overview

**Page Sentinel** is an autonomous web watcher engineered to poll HTTP directories (such as Apache `mod_autoindex` listing indexes) and dispatch instant, high-priority notifications across **ntfy.sh** (mobile push alarms) and **Discord Webhooks** (rich embeds).

Designed with production reliability principles:
- **HTTP 304 Optimization**: Employs `ETag` and `If-Modified-Since` conditional headers to minimize bandwidth and eliminate unnecessary HTML parsing.
- **Delivery Guarantee**: Does not advance the persistent state unless at least one remote delivery channel acknowledges receipt, preventing permanently dropped alerts during network interruptions.
- **Crash Resilience**: State synchronization uses atomic temporary writes (`fsync` + rename) with automatic `.bak` recovery.
- **Discord Embed Compliance**: Handles batch uploads by chunking fields to strictly adhere to Discord's 25-field embed limits.

---

## Architecture

```
page-sentinel/
├── sentinel.py               # Main daemon orchestrator & CLI
├── config.py                 # Typed configuration & environment parser
├── monitor.py                # HTTP session pool & BeautifulSoup parser
├── storage.py                # Atomic state persistence & recovery
├── logger.py                 # Formatted ANSI logger
├── notifiers/
│   ├── __init__.py           # Multi-channel dispatch coordinator
│   ├── ntfy.py               # Mobile push notifications (urgent priority)
│   ├── discord.py            # Discord webhook dispatcher with field chunking
│   └── console.py            # Standard output logger
├── tests/
│   ├── test_monitor.py       # Scraper & URL normalization tests
│   ├── test_storage.py       # Atomic persistence & corrupt recovery tests
│   └── test_discord.py       # Discord field chunking limits tests
├── .github/workflows/ci.yml  # GitHub Actions automated test matrix
├── requirements.txt          # Production & test dependencies
├── .env.example              # Environment variables template
└── README.md
```

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/Se7enWay/page-sentinel.git
cd page-sentinel
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set your notification credentials in `.env`:

```ini
TARGET_URL=https://example.university.edu/admissions/results/
CHECK_INTERVAL=60

# ntfy.sh (Mobile push alarm)
NTFY_ENABLED=true
NTFY_TOPIC=my-unique-secret-channel

# Discord Webhook
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 3. Verification & Execution

```bash
# Verify webhook & push configurations without polling
python sentinel.py --test

# Perform single dry-run check without updating state
python sentinel.py --dry-run

# Start autonomous background monitoring
python sentinel.py
```

---

## Test Suite

Run the full automated test suite with `pytest`:

```bash
pytest tests/ -v
```

---

## License

MIT © 2026. Released under the [MIT License](LICENSE).
