"""Notifier registry and dispatch coordinator for Page Sentinel."""

from __future__ import annotations

import logging
from typing import Callable, NamedTuple

import config
from monitor import FileItem

logger = logging.getLogger("page_sentinel.notifiers")


class DispatchResult(NamedTuple):
    succeeded: list[str]
    failed: list[str]

    @property
    def has_external_success(self) -> bool:
        """Return True if at least one remote channel (non-console) delivered successfully."""
        return any(name != "console" for name in self.succeeded)


# Registered notifiers: (name, is_external, callable)
_registry: list[tuple[str, bool, Callable[[str, str, list[FileItem]], None]]] = []


def _initialize_registry() -> None:
    """Register enabled notification channels based on active configuration."""
    _registry.clear()

    if config.NTFY_ENABLED:
        from notifiers.ntfy import send as ntfy_send
        _registry.append(("ntfy", True, ntfy_send))

    if config.DISCORD_ENABLED:
        from notifiers.discord import send as discord_send
        _registry.append(("discord", True, discord_send))

    from notifiers.console import send as console_send
    _registry.append(("console", False, console_send))


def get_enabled_channels() -> list[str]:
    """Return the list of names of configured notification channels."""
    if not _registry:
        _initialize_registry()
    return [name for name, _, _ in _registry]


def dispatch(title: str, message: str, files: list[FileItem]) -> DispatchResult:
    """Send notifications across all enabled delivery channels.

    Args:
        title: Notification headline.
        message: Descriptive notification body.
        files: List of discovered FileItem instances.

    Returns:
        A DispatchResult categorizing successful and failed delivery channels.
    """
    if not _registry:
        _initialize_registry()

    succeeded: list[str] = []
    failed: list[str] = []

    for name, _, send_fn in _registry:
        try:
            send_fn(title, message, files)
            succeeded.append(name)
        except Exception as err:
            logger.error("Notifier '%s' failed: %s", name, err)
            failed.append(name)

    return DispatchResult(succeeded=succeeded, failed=failed)


def send_test() -> DispatchResult:
    """Dispatch a test notification with synthetic data to verify credentials."""
    sample_files = [
        FileItem(
            filename="Test_Sample_Document.pdf",
            url="https://example.com/test_sample.pdf",
        )
    ]
    return dispatch(
        title=f"🧪 {config.APP_NAME} Test Alert",
        message="Integration verification: your notification channels are successfully configured.",
        files=sample_files,
    )
