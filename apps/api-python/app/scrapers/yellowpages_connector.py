"""
Yellow Pages scraper connector.

Uses Playwright sync API in a thread pool (same pattern as google_maps.py)
to avoid event-loop conflicts with the uvicorn async loop.
"""
from __future__ import annotations

import asyncio
import re
import logging
from typing import List, Optional

from .base_connector import BaseConnector, ConnectorResult

logger = logging.getLogger(__name__)


def _scrape_sync(query: str, location: str, limit: int) -> list[dict]:
    """Run Yellow Pages scrape synchronously — called via asyncio.to_thread."""
    results: list[dict] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            ctx  = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()

            q_enc   = query.replace(" ", "+")
            loc_enc = location.replace(" ", "+")
            url     = (
                f"https://www.yellowpages.com/search"
                f"?search_terms={q_enc}&geo_location_terms={loc_enc}"
            )

            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(2_500)

            # Scroll to load lazy content
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                page.wait_for_timeout(700)

            # Single JS extraction pass — most reliable approach for YP
            raw = page.evaluate(r"""(limit) => {
                const cards = Array.from(document.querySelectorAll(
                    'div[class*="result"], div[class*="listing"], article'
                )).slice(0, limit * 3);   // grab extra, filter empties

                const out = [];
                for (const card of cards) {
                    if (out.length >= limit) break;

                    // Name — multiple fallback selectors
                    const nameEl = card.querySelector(
                        'a.business-name, .business-name a, .n a, h2 a, a[class*="businessName"], a[class*="BusinessName"]'
                    );
                    const name = (nameEl?.textContent || '').trim();
                    if (!name || name.length < 2) continue;

                    // Phone
                    const phoneEl = card.querySelector(
                        '.phone, .phones, [class*="phone"], a[href^="tel:"]'
                    );
                    let phone = '';
                    if (phoneEl) {
                        phone = phoneEl.href
                            ? phoneEl.href.replace('tel:', '').trim()
                            : phoneEl.textContent.trim();
                    }

                    // Full address string
                    const addrEl = card.querySelector(
                        '.street-address, [class*="streetAddress"], .address, .adr'
                    );
                    const address = (addrEl?.textContent || '').trim();

                    // Locality "City, ST  ZIP"
                    const localEl = card.querySelector('.locality, [class*="locality"]');
                    const locality = (localEl?.textContent || '').trim();
                    const [cityPart, restPart] = locality.split(/,\s*/, 2);
                    const restWords = (restPart || '').trim().split(/\s+/);
                    const city  = cityPart || '';
                    const state = restWords[0] || '';
                    const zip   = restWords[1] || '';

                    // Website link
                    const siteEl = card.querySelector(
                        'a[class*="website"], a[class*="Website"], a.track-visit-website'
                    );
                    const website = siteEl ? siteEl.href : '';

                    // Rating from CSS class like "rating-45" => 4.5
                    const ratingEl = card.querySelector('[class*="rating"], [class*="stars"]');
                    let rating = null;
                    if (ratingEl) {
                        const cls = ratingEl.getAttribute('class') || '';
                        const m   = cls.match(/(\d+)$/);
                        if (m) rating = parseInt(m[1], 10) / 10;
                    }

                    // Review count
                    const countEl = card.querySelector(
                        '[class*="count"], [class*="Count"], a[href*="review"]'
                    );
                    let reviewCount = null;
                    if (countEl) {
                        const m = countEl.textContent.match(/\d+/);
                        if (m) reviewCount = parseInt(m[0], 10);
                    }

                    out.push({ name, phone, address, city, state, zip, website, rating, reviewCount });
                }
                return out;
            }""", limit)

            browser.close()

            for item in (raw or []):
                if item.get("name"):
                    results.append(item)

    except Exception as exc:
        logger.error(f"[yellowpages] scrape_sync failed: {exc}")

    return results


class YellowPagesConnector(BaseConnector):
    """Yellow Pages web scraper connector"""

    @property
    def name(self) -> str:
        return "yellowpages"

    @property
    def display_name(self) -> str:
        return "Yellow Pages"

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
        """Run sync scraper in thread pool to avoid event-loop conflicts."""
        raw = await asyncio.to_thread(_scrape_sync, query, location, limit)

        results: List[ConnectorResult] = []
        for item in raw:
            results.append(ConnectorResult(
                name=item.get("name", ""),
                phone=item.get("phone") or None,
                email=None,
                website=item.get("website") or None,
                address=item.get("address") or None,
                city=item.get("city")  or None,
                state=item.get("state") or None,
                zip_code=item.get("zip") or None,
                country="United States",
                rating=item.get("rating"),
                review_count=item.get("reviewCount"),
                category=query,
                source=self.name,
                raw_data={},
            ))

        logger.info(
            f"[yellowpages] Found {len(results)} results for '{query}' in '{location}'"
        )
        return results
