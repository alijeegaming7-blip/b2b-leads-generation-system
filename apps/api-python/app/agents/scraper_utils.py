"""
Shared scraper utility for all specialist agents.
Wraps the Google Maps Playwright scraper with retry logic.
Falls back to a MINIMAL simulation ONLY when playwright itself is unavailable
(e.g. browser not installed), and logs loudly when that happens.
"""
from __future__ import annotations

import asyncio
import logging
import random

logger = logging.getLogger(__name__)

_PLAYWRIGHT_OK: bool | None = None   # cached after first check


async def scrape_google_maps(query: str, max_results: int = 12, retries: int = 2) -> list[dict]:
    """
    Run Google Maps scrape for `query`, returning up to `max_results` raw dicts.
    Retries up to `retries` times on transient failures.
    Returns empty list (NOT fake data) on persistent failure so the caller
    can decide what to do.
    """
    global _PLAYWRIGHT_OK

    for attempt in range(1, retries + 2):
        try:
            from app.services.scraper.google_maps import _scrape_sync
            results = await asyncio.to_thread(_scrape_sync, query, max_results)
            if results:
                logger.info(f"[scraper] '{query}' → {len(results)} real results (attempt {attempt})")
                _PLAYWRIGHT_OK = True
                return results
            # Empty result is not necessarily an error — location may have no matches
            logger.info(f"[scraper] '{query}' → 0 results (attempt {attempt})")
            _PLAYWRIGHT_OK = True
            return []
        except Exception as exc:
            logger.warning(f"[scraper] Attempt {attempt} failed for '{query}': {exc}")
            if attempt <= retries:
                await asyncio.sleep(3 * attempt)   # back-off: 3s, 6s

    logger.error(f"[scraper] All {retries+1} attempts failed for '{query}'. Playwright may not be installed.")
    _PLAYWRIGHT_OK = False
    return []


def is_playwright_available() -> bool:
    """Quick sync check — returns cached value after first real attempt."""
    if _PLAYWRIGHT_OK is not None:
        return _PLAYWRIGHT_OK
    try:
        from playwright.sync_api import sync_playwright  # noqa
        return True
    except ImportError:
        return False
