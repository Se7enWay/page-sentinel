"""Terminal formatting and logging infrastructure for Page Sentinel."""

from __future__ import annotations

import logging
import sys
from datetime import datetime


class Colors:
    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"
    RED: str = "\033[91m"
    GREEN: str = "\033[92m"
    YELLOW: str = "\033[93m"
    CYAN: str = "\033[96m"
    MAGENTA: str = "\033[95m"


def _enable_windows_ansi() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


_enable_windows_ansi()


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def info(msg: str) -> None:
    print(f"{Colors.DIM}[{_ts()}]{Colors.RESET} {Colors.CYAN}ℹ{Colors.RESET}  {msg}")


def success(msg: str) -> None:
    print(f"{Colors.DIM}[{_ts()}]{Colors.RESET} {Colors.GREEN}✅{Colors.RESET} {msg}")


def warning(msg: str) -> None:
    print(f"{Colors.DIM}[{_ts()}]{Colors.RESET} {Colors.YELLOW}⚠️{Colors.RESET}  {msg}")


def error(msg: str) -> None:
    print(f"{Colors.DIM}[{_ts()}]{Colors.RESET} {Colors.RED}❌{Colors.RESET} {msg}")


def alert(msg: str) -> None:
    print(f"{Colors.DIM}[{_ts()}]{Colors.RESET} {Colors.BOLD}{Colors.MAGENTA}🚨 {msg}{Colors.RESET}")


def file_item(filename: str) -> None:
    print(f"           {Colors.CYAN}📄 {filename}{Colors.RESET}")


def separator() -> None:
    print(f"{Colors.DIM}{'━' * 55}{Colors.RESET}")


# Integrate with Python logging module
class ConsoleLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            error(msg)
        elif record.levelno >= logging.WARNING:
            warning(msg)
        else:
            info(msg)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger("page_sentinel")
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(ConsoleLogHandler())
