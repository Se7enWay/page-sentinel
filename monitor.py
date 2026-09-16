"""Scraping and change detection engine for Page Sentinel.

Handles HTTP connection reuse, conditional GET requests (ETag / If-Modified-Since),
and robust HTML link extraction for Apache autoindex directories.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger("page_sentinel.monitor")

# Module-level reusable HTTP session for connection pooling
_session: requests.Session | None = None


def get_http_session() -> requests.Session:
    """Return a shared requests.Session instance."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": config.APP_USER_AGENT})
    return _session


@dataclass
class FileItem:
    """Represents a discovered file entry on the target page."""
    filename: str
    url: str

    def to_dict(self) -> dict[str, str]:
        return {"filename": self.filename, "url": self.url}


@dataclass
class ScrapeResult:
    """Result of an inspection cycle."""
    status_code: int
    not_modified: bool
    files: list[FileItem]
    etag: str | None
    last_modified: str | None
    error: str | None = None


def fetch_and_parse(
    url: str = config.TARGET_URL,
    cached_etag: str | None = None,
    cached_last_modified: str | None = None,
) -> ScrapeResult:
    """Fetch the target URL using conditional HTTP headers and parse matching files.

    Args:
        url: Page URL to inspect.
        cached_etag: Previous ETag value for If-None-Match header.
        cached_last_modified: Previous Last-Modified for If-Modified-Since header.

    Returns:
        A ScrapeResult containing status code, change status, and discovered files.
    """
    session = get_http_session()
    headers: dict[str, str] = {}

    if cached_etag:
        headers["If-None-Match"] = cached_etag
    if cached_last_modified:
        headers["If-Modified-Since"] = cached_last_modified

    try:
        response = session.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)

        # 304 Not Modified: Server confirms content hasn't changed
        if response.status_code == 304:
            return ScrapeResult(
                status_code=304,
                not_modified=True,
                files=[],
                etag=cached_etag,
                last_modified=cached_last_modified,
            )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        msg = f"Request timed out after {config.REQUEST_TIMEOUT}s"
        logger.error("%s: %s", url, msg)
        return ScrapeResult(status_code=408, not_modified=False, files=[], etag=None, last_modified=None, error=msg)

    except requests.exceptions.RequestException as err:
        msg = f"HTTP request failed: {err}"
        logger.error("%s: %s", url, msg)
        status = getattr(err.response, "status_code", 500) if getattr(err, "response", None) else 500
        return ScrapeResult(status_code=status, not_modified=False, files=[], etag=None, last_modified=None, error=msg)

    new_etag = response.headers.get("ETag")
    new_last_modified = response.headers.get("Last-Modified")

    files = parse_directory_listing(response.text, base_url=response.url)

    return ScrapeResult(
        status_code=response.status_code,
        not_modified=False,
        files=files,
        etag=new_etag,
        last_modified=new_last_modified,
    )


def parse_directory_listing(html_content: str, base_url: str) -> list[FileItem]:
    """Extract and normalize matching file links from raw HTML.

    Args:
        html_content: Raw HTML text of the page.
        base_url: The actual response URL used to resolve relative references.

    Returns:
        List of unique FileItem instances that match configured extension rules.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    elements = soup.select(config.LINK_SELECTOR)

    seen_urls: set[str] = set()
    results: list[FileItem] = []

    for tag in elements:
        href = tag.get("href")
        if not href or not isinstance(href, str):
            continue

        raw_href = href.strip()
        link_text = tag.get_text(strip=True)

        # Skip explicit parent directory links
        if link_text.lower() in ("parent directory", "..", "parent directory/"):
            continue

        # Resolve relative and root-relative URLs cleanly
        full_url = urljoin(base_url, raw_href)
        parsed = urlsplit(full_url)

        # Extract normalized filename
        filename = unquote(Path(parsed.path).name)

        if not filename:
            continue

        # Filter by watched file extensions if configured
        if config.WATCHED_EXTENSIONS:
            filename_lower = filename.lower()
            if not any(filename_lower.endswith(ext) for ext in config.WATCHED_EXTENSIONS):
                continue

        if full_url not in seen_urls:
            seen_urls.add(full_url)
            results.append(FileItem(filename=filename, url=full_url))

    return results
