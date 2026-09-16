"""ntfy.sh push notification dispatcher with urgent priority and direct links."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import config
from monitor import get_http_session

if TYPE_CHECKING:
    from monitor import FileItem

logger = logging.getLogger("page_sentinel.notifiers.ntfy")


def send(title: str, message: str, files: list[FileItem]) -> None:
    """Send high-priority push notification to configured ntfy topic.

    Args:
        title: Notification headline.
        message: Descriptive summary.
        files: List of discovered file items.
    """
    topic = config.NTFY_TOPIC
    if not topic:
        raise ValueError("NTFY_TOPIC is not configured")

    session = get_http_session()
    endpoint = f"{config.NTFY_SERVER}/{topic}"

    body_lines = [message]
    if files:
        body_lines.append("\nDetected Documents:")
        for item in files[:10]:
            body_lines.append(f"• {item.filename}")
        if len(files) > 10:
            body_lines.append(f"... and {len(files) - 10} more files.")

    body_content = "\n".join(body_lines)

    headers: dict[str, str] = {
        "Title": title[:100],
        "Priority": "urgent",
        "Tags": "rotating_light,file_folder",
    }

    if files:
        headers["Click"] = files[0].url
        headers["Actions"] = f"view, Open Document, {files[0].url}"

    response = session.post(
        endpoint,
        data=body_content.encode("utf-8"),
        headers=headers,
        timeout=config.REQUEST_TIMEOUT,
    )

    response.raise_for_status()
