"""
Google Maps connector — scrapes Google Maps then enriches every result with:
  1. Email   — from website HTML + Google Search fallback
  2. Social  — from website HTML + Google Search fallback
  3. Phone   — extracted by Google Maps scraper (cleaned)
  4. Address — extracted by Google Maps scraper (cleaned)

Works globally: US, Pakistan, UAE, India, etc.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import List, Dict
from urllib.parse import quote_plus

import aiohttp

from .base_connector import BaseConnector, ConnectorResult
from ..services.scraper.google_maps import scrape as gmaps_scrape
from ..utils.social_extractor import SocialMediaExtractor, extract_emails_from_text

logger = logging.getLogger(__name__)

_ENRICH_CONCURRENCY = 3
_WEBSITE_TIMEOUT    = 12
_GSEARCH_TIMEOUT    = 10

_EMAIL_BLACKLIST = {
    "example.com", "test.com", "localhost", "domain.com", "email.com",
    "sentry.io", "wixpress.com", "squarespace.com", "schema.org",
    "w3.org", "cloudflare.com", "google.com", "googleapis.com",
    "jquery.com", "wordpress.com", "shopify.com",
}

_SOCIAL_BLACKLIST = {
    "share", "sharer", "sharer.php", "intent", "dialog", "plugins",
    "home", "login", "signup", "register", "logout", "oauth",
    "groups", "events", "pages", "watch", "gaming", "marketplace",
    "undefined", "null",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class GoogleMapsConnector(BaseConnector):
    """Google Maps Places scraper with contact enrichment."""

    @property
    def name(self) -> str:
        return "google_maps"

    @property
    def display_name(self) -> str:
        return "Google Maps"

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
        search_query = f"{query} in {location}"
        logger.info(f"[google_maps] Searching: {search_query}")

        businesses = await gmaps_scrape(search_query, max_results=limit)
        if not businesses:
            return []

        semaphore = asyncio.Semaphore(_ENRICH_CONCURRENCY)

        async def enrich(biz) -> ConnectorResult:
            """Enrich a single business result with email + social."""
            email        = biz.email or ""
            social       : Dict[str, str] = {}
            extra_emails : List[str]      = []

            # ── Step 1: Scrape website for email + social links ───────────────
            if biz.website:
                try:
                    async with semaphore:
                        html = await _fetch_html_robust(biz.website, _WEBSITE_TIMEOUT)
                    if html:
                        social = SocialMediaExtractor.extract_from_text(html)
                        if not email:
                            found = _extract_emails_safe(html)
                            if found:
                                email        = found[0]
                                extra_emails = found[1:4]
                except Exception as exc:
                    logger.debug(f"[google_maps] website enrich failed ({biz.website}): {exc}")

            # ── Step 2: Google Search fallback for email + social ─────────────
            try:
                async with semaphore:
                    gs = await _google_search_contact(
                        biz.name, location, has_website=bool(biz.website)
                    )
                if not email and gs.get("email"):
                    email = gs["email"]
                for k, v in gs.get("social", {}).items():
                    if k not in social:
                        social[k] = v
            except Exception as exc:
                logger.debug(f"[google_maps] google search fallback failed ({biz.name}): {exc}")

            # ── Step 3: Parse rating ─────────────────────────────────────────
            try:
                rating = float(biz.rating) if biz.rating and biz.rating not in ("N/A", "") else None
            except (ValueError, TypeError):
                rating = None

            return ConnectorResult(
                name         = biz.name,
                phone        = biz.phone or None,
                email        = email.strip() or None,
                website      = biz.website or None,
                address      = biz.address or None,
                city         = None,
                state        = None,
                zip_code     = None,
                country      = None,
                rating       = rating,
                review_count = biz.review_count,
                category     = query,
                source       = self.name,
                raw_data     = {
                    "reference_link":    biz.reference_link,
                    "lat":               biz.lat,
                    "lng":               biz.lng,
                    "has_website":       biz.has_website,
                    "social_media":      social,
                    "additional_emails": extra_emails,
                },
            )

        tasks   = [enrich(b) for b in businesses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        cleaned = []
        for r in results:
            if isinstance(r, Exception):
                logger.debug(f"[google_maps] enrich exception: {r}")
            elif r is not None:
                cleaned.append(r)
        return cleaned


# ── HTTP helpers ──────────────────────────────────────────────────────────────

async def _fetch_html_robust(url: str, timeout: int = 12) -> str:
    """Robust HTTP fetch that handles SSL errors and encoding issues."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url

    for verify_ssl in (True, False):
        try:
            conn = aiohttp.TCPConnector(ssl=verify_ssl)
            async with aiohttp.ClientSession(
                connector=conn,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers=_HEADERS,
            ) as session:
                async with session.get(url, allow_redirects=True, max_redirects=5) as resp:
                    if resp.status in (200, 201):
                        ct = resp.headers.get("content-type", "")
                        if "text" in ct or "html" in ct or not ct:
                            try:
                                return await resp.text(errors="replace")
                            except Exception:
                                raw = await resp.read()
                                for enc in ("utf-8", "latin-1", "cp1252"):
                                    try:
                                        return raw.decode(enc, errors="replace")
                                    except Exception:
                                        continue
        except aiohttp.ClientSSLError:
            if verify_ssl:
                continue   # retry without SSL verify
        except Exception:
            pass
        break

    return ""


def _extract_emails_safe(html: str) -> List[str]:
    """Extract and rank valid business emails from HTML."""
    if not html:
        return []

    raw = re.findall(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b', html)
    seen: set = set()
    valid: List[str] = []

    for em in raw:
        em = em.lower().strip()
        if em in seen:
            continue
        seen.add(em)

        domain = em.split("@")[-1] if "@" in em else ""
        if any(bl in domain for bl in _EMAIL_BLACKLIST):
            continue
        if re.search(r'noreply|no.reply|donotreply|bounce|spam|abuse', em):
            continue
        if len(domain.split(".")[-1]) < 2:
            continue

        valid.append(em)

    def _prio(e: str) -> int:
        local = e.split("@")[0]
        for i, kw in enumerate(["info", "contact", "hello", "sales", "support",
                                  "office", "enquiry", "inquiry", "mail", "admin"]):
            if local.startswith(kw):
                return i
        return 99

    valid.sort(key=_prio)
    return valid[:5]


async def _google_search_contact(name: str, location: str, has_website: bool = False) -> Dict:
    """Search Google to find email + social links for a business."""
    result: Dict = {"email": "", "social": {}}
    name_clean = re.sub(r'[^\w\s]', '', name)[:50]

    async def _search(q: str) -> str:
        url = f"https://www.google.com/search?q={quote_plus(q)}&num=5"
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=_GSEARCH_TIMEOUT),
                headers={**_HEADERS, "Accept-Language": "en-US,en;q=0.9"},
            ) as session:
                async with session.get(url, allow_redirects=True, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.text(errors="replace")
        except Exception:
            pass
        return ""

    # Search for email
    html_email = await _search(f'"{name_clean}" {location} email contact')
    if html_email:
        emails = _extract_emails_safe(html_email)
        if emails:
            result["email"] = emails[0]
            logger.info(f"[google_maps] Found email for {name_clean}: {emails[0]}")

    # Search for Facebook
    html_fb = await _search(f'"{name_clean}" {location} site:facebook.com')
    if html_fb:
        fb_urls = re.findall(
            r'https?://(?:www\.)?facebook\.com/(?!sharer|share|dialog|plugins|groups/)([a-zA-Z0-9._\-]+)',
            html_fb,
        )
        for handle in fb_urls:
            if handle.lower() not in _SOCIAL_BLACKLIST and len(handle) > 2:
                result["social"]["facebook"] = f"https://www.facebook.com/{handle}"
                logger.info(f"[google_maps] Found Facebook for {name_clean}: {handle}")
                break

    # Search for Instagram
    html_ig = await _search(f'"{name_clean}" site:instagram.com')
    if html_ig:
        ig_urls = re.findall(r'instagram\.com/([a-zA-Z0-9._]+)', html_ig)
        for handle in ig_urls:
            if handle.lower() not in _SOCIAL_BLACKLIST and len(handle) > 2:
                result["social"]["instagram"] = f"https://www.instagram.com/{handle}"
                logger.info(f"[google_maps] Found Instagram for {name_clean}: {handle}")
                break

    await asyncio.sleep(0.3)  # Be polite to Google
    return result
