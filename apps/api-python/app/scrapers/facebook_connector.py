"""
Facebook Business scraper connector.

Uses sync Playwright in a thread pool to avoid event-loop conflicts.
Note: Facebook aggressively blocks bots — treat results as best-effort.
"""
from __future__ import annotations

import asyncio
import re
import logging
from typing import List, Optional

from .base_connector import BaseConnector, ConnectorResult

logger = logging.getLogger(__name__)


def _scrape_sync(query: str, location: str, limit: int) -> list[dict]:
    """Synchronous Facebook scrape — runs in thread pool."""
    results: list[dict] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            ctx  = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = ctx.new_page()

            search_query = f"{query} {location}"
            encoded      = search_query.replace(" ", "%20")
            url          = f"https://www.facebook.com/search/pages/?q={encoded}"

            page.goto(url, wait_until="domcontentloaded", timeout=25_000)

            # Bail if redirected to login wall
            if "login" in page.url or "checkpoint" in page.url:
                logger.warning("[facebook] Login wall — skipping")
                browser.close()
                return results

            page.wait_for_timeout(2_500)

            for _ in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(1_000)

            listings = page.query_selector_all('[role="article"]')

            for listing in listings[:limit]:
                try:
                    name_el = listing.query_selector('a[role="link"] span, h2, h3')
                    name    = (name_el.inner_text() if name_el else "").strip()
                    if not name or len(name) < 2:
                        continue

                    link_el  = listing.query_selector('a[href*="facebook.com"]')
                    page_url = link_el.get_attribute("href") if link_el else ""
                    if page_url and not page_url.startswith("http"):
                        page_url = f"https://www.facebook.com{page_url}"

                    rating_el = listing.query_selector('[aria-label*="star"], [aria-label*="rating"]')
                    rating    = None
                    if rating_el:
                        lbl = rating_el.get_attribute("aria-label") or ""
                        m   = re.search(r"([\d.]+)", lbl)
                        if m:
                            rating = float(m.group(1))

                    results.append({
                        "name": name,
                        "website": page_url,
                        "rating": rating,
                        "facebook_url": page_url,
                    })
                except Exception:
                    continue

            browser.close()

    except Exception as exc:
        logger.error(f"[facebook] scrape_sync failed: {exc}")

    return results


class FacebookConnector(BaseConnector):
    """Facebook Business scraper — experimental, best-effort."""

    @property
    def name(self) -> str:
        return "facebook"

    @property
    def display_name(self) -> str:
        return "Facebook Business"

    @property
    def requires_api_key(self) -> bool:
        return False

    async def search(
        self,
        query: str,
        location: str,
        limit: int = 10,
        **kwargs,
    ) -> List[ConnectorResult]:
        raw = await asyncio.to_thread(_scrape_sync, query, location, limit)

        results: List[ConnectorResult] = []
        for item in raw:
            results.append(ConnectorResult(
                name=item.get("name", ""),
                phone=None,
                email=None,
                website=item.get("website") or None,
                address=None,
                city=None, state=None, zip_code=None, country=None,
                rating=item.get("rating"),
                review_count=None,
                category=query,
                source=self.name,
                raw_data={"facebook_url": item.get("facebook_url", "")},
            ))

        logger.info(f"[facebook] Found {len(results)} results for '{query}' in '{location}'")
        return results
