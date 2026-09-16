"""Discord webhook notification sender with embed batching and rate-limit handling."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import config
from monitor import get_http_session

if TYPE_CHECKING:
    from monitor import FileItem

logger = logging.getLogger("page_sentinel.notifiers.discord")

MAX_FIELDS_PER_EMBED = 25
MAX_EMBEDS_PER_PAYLOAD = 10
EMBED_COLOR_ALERT = 0x5865F2  # Blurple
MAX_RETRIES = 1


def _create_embed(
    title: str,
    description: str,
    fields: list[dict[str, Any]],
    is_primary: bool = True,
) -> dict[str, Any]:
    """Construct a compliant Discord embed dictionary."""
    embed: dict[str, Any] = {
        "color": EMBED_COLOR_ALERT,
        "fields": fields,
    }
    if is_primary:
        embed["title"] = title[:256]
        embed["description"] = description[:4096]
        embed["footer"] = {"text": f"{config.APP_NAME} • Autonomous Monitor"}
        embed["timestamp"] = datetime.now(timezone.utc).isoformat()

    return embed


def send(title: str, message: str, files: list[FileItem]) -> None:
    """Send alert to Discord webhook, respecting embed field and rate limits.

    Args:
        title: Notification headline.
        message: Descriptive summary text.
        files: Discovered file items with names and URLs.
    """
    webhook_url = config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL is not configured")

    session = get_http_session()

    # Format each file as a field
    raw_fields: list[dict[str, Any]] = [
        {
            "name": f"📄 {item.filename[:250]}",
            "value": f"[⬇ Direct Download]({item.url})",
            "inline": True,
        }
        for item in files
    ]

    # Chunk fields to prevent exceeding Discord's 25-field limit per embed
    embeds: list[dict[str, Any]] = []

    if not raw_fields:
        embeds.append(_create_embed(title, message, []))
    else:
        for i in range(0, len(raw_fields), MAX_FIELDS_PER_EMBED):
            if len(embeds) >= MAX_EMBEDS_PER_PAYLOAD:
                break
            chunk = raw_fields[i : i + MAX_FIELDS_PER_EMBED]
            is_primary = (i == 0)
            embeds.append(_create_embed(title, message, chunk, is_primary=is_primary))

    payload = {
        "username": config.APP_NAME,
        "embeds": embeds,
    }

    # Send with rate-limit retry
    for attempt in range(1 + MAX_RETRIES):
        response = session.post(
            webhook_url,
            json=payload,
            timeout=config.REQUEST_TIMEOUT,
        )

        if response.status_code == 429:
            if attempt < MAX_RETRIES:
                retry_after = response.json().get("retry_after", 5)
                logger.warning("Discord rate-limited. Retrying after %.1fs...", retry_after)
                time.sleep(retry_after)
                continue
            else:
                logger.error("Discord rate-limited after %d retries.", MAX_RETRIES)

        break

    response.raise_for_status()
