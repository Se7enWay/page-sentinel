"""Console notifier providing structured stdout output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import logger

if TYPE_CHECKING:
    from monitor import FileItem


def send(title: str, message: str, files: list[FileItem]) -> None:
    """Print notification summary and items to stdout."""
    logger.alert(title)
    if message:
        logger.info(message)
    for item in files:
        logger.file_item(item.filename)
