"""ntfy.sh push notification dispatcher with urgent priority and direct links.

Uses ntfy's JSON publishing API for full UTF-8 support in titles
and messages (raw HTTP headers are limited to latin-1 encoding).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import config
from monitor import get_http_session

if TYPE_CHECKING:
    from monitor import FileItem

logger = logging.getLogger("page_sentinel.notifiers.ntfy")


def send(title: str, message: str, files: list[FileItem]) -> None:
    """Send high-priority push notification to configured ntfy topic.

    Args:
        title: Notification headline (UTF-8 safe via JSON body).
        message: Descriptive summary.
        files: List of discovered file items.
    """
    topic = config.NTFY_TOPIC
    if not topic:
        raise ValueError("NTFY_TOPIC is not configured")

    session = get_http_session()

    body_lines = [message]
    if files:
        body_lines.append("\nDetected Documents:")
        for item in files[:10]:
            body_lines.append(f"• {item.filename}")
        if len(files) > 10:
            body_lines.append(f"... and {len(files) - 10} more files.")

    payload: dict[str, Any] = {
        "topic": topic,
        "title": title[:100],
        "message": "\n".join(body_lines),
        "priority": 5,  # urgent
        "tags": ["rotating_light", "file_folder"],
    }

    if files:
        payload["click"] = files[0].url
        payload["actions"] = [
            {"action": "view", "label": "Open Document", "url": files[0].url}
        ]

    response = session.post(
        config.NTFY_SERVER,
        json=payload,
        timeout=config.REQUEST_TIMEOUT,
    )

    response.raise_for_status()
