"""State persistence manager for Page Sentinel.

Provides atomic file writes to prevent state corruption on crashes,
plus backup recovery for corrupted state files.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("page_sentinel.storage")


def get_default_state() -> dict[str, Any]:
    """Return a pristine default state dictionary."""
    return {
        "known_files": [],
        "etag": None,
        "last_modified": None,
        "last_checked": None,
        "check_count": 0,
        "first_run": True,
    }


def load_state(path: Path | None = None) -> dict[str, Any]:
    """Load persistent state from disk with corruption safeguards.

    Args:
        path: Optional path override. Defaults to config.STATE_FILE.

    Returns:
        The deserialized state dictionary or a fresh default state.
    """
    target = path or config.STATE_FILE

    if not target.exists():
        return get_default_state()

    try:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("State root must be a dictionary")
            # Ensure required keys exist
            default = get_default_state()
            for key, val in default.items():
                data.setdefault(key, val)
            return data

    except (json.JSONDecodeError, ValueError) as err:
        logger.error("State file %s is corrupted: %s", target, err)

        # Check for backup file
        bak_file = target.with_suffix(".json.bak")
        if bak_file.exists():
            try:
                with open(bak_file, "r", encoding="utf-8") as f:
                    logger.warning("Restoring state from backup %s", bak_file)
                    return json.load(f)
            except Exception as bak_err:
                logger.error("Backup file also unreadable: %s", bak_err)

        # Preserve the corrupted file for post-mortem debugging
        corrupt_target = target.with_suffix(f".corrupt.{int(datetime.now().timestamp())}")
        try:
            os.replace(target, corrupt_target)
            logger.info("Moved corrupted state to %s", corrupt_target)
        except OSError:
            pass

        return get_default_state()


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    """Save state atomically using a temporary file and atomic rename.

    Args:
        state: State dictionary to persist.
        path: Optional path override. Defaults to config.STATE_FILE.
    """
    target = path or config.STATE_FILE
    target_dir = target.parent.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    state["last_checked"] = datetime.now(timezone.utc).isoformat()
    state["first_run"] = False

    # Create backup of current valid state before overwriting
    if target.exists():
        bak_path = target.with_suffix(".json.bak")
        try:
            target.replace(bak_path)
        except OSError:
            pass

    # Atomic write pattern: write to temp file in same directory, then rename
    temp_fd, temp_path = tempfile.mkstemp(
        dir=target_dir,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )

    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, target)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


def get_new_files(current_files: list[str], state: dict[str, Any]) -> list[str]:
    """Identify new filenames not present in previously known state.

    Args:
        current_files: List of discovered filenames from the latest scrape.
        state: Persistent state containing 'known_files'.

    Returns:
        List of filenames that are newly appeared, preserving discovery order.
    """
    known = set(state.get("known_files", []))
    seen = set()
    new_items: list[str] = []

    for filename in current_files:
        if filename not in known and filename not in seen:
            seen.add(filename)
            new_items.append(filename)

    return new_items
