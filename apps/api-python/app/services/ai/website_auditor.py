"""Website Auditor — Playwright-based heuristic + optional AI narrative."""
from __future__ import annotations
import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

TECH_PATTERNS: list[tuple[str, str]] = [
    ("WordPress",        r"wp-content|wp-includes|wordpress"),
    ("Shopify",          r"shopify|myshopify"),
    ("Wix",              r"wix\.com|wixstatic"),
    ("Squarespace",      r"squarespace"),
    ("Webflow",          r"webflow"),
    ("React",            r"react\.js|reactdom|__reactfiber"),
    ("Next.js",          r"__next|_next/static"),
    ("Bootstrap",        r"bootstrap\.min\.css"),
    ("jQuery",           r"jquery\.min\.js"),
    ("Tailwind",         r"tailwindcss"),
    ("Google Analytics", r"google-analytics|gtag\("),
    ("Facebook Pixel",   r"connect\.facebook\.net|fbq\("),
    ("HubSpot",          r"hubspot|hs-scripts"),
]


@dataclass
class WebsiteAudit:
    url: str
    reachable: bool
    load_time_ms: Optional[int]
    has_contact_form: bool
    has_booking_flow: bool
    has_phone_visible: bool
    has_email_visible: bool
    has_cta: bool
    has_social_links: bool
    has_blog: bool
    is_https: bool
    mobile_viewport: bool
    page_title: Optional[str]
    meta_description: Optional[str]
    has_h1: bool
    h1_text: Optional[str]
    missing_alt_images: int
    tech_stack: list[str] = field(default_factory=list)
    site_health_score: int = 0
    opportunity_score: int = 0
    gaps: list[str] = field(default_factory=list)
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None
    audited_at: str = ""


def _audit_sync(url: str) -> dict:
    """Synchronous Playwright page analysis — runs in thread pool."""
    result: dict = {
        "reachable": False, "load_time_ms": None, "page_title": None,
        "meta_description": None, "has_h1": False, "h1_text": None,
        "has_contact_form": False, "has_booking_flow": False, "has_cta": False,
        "has_social_links": False, "has_blog": False,
        "has_phone_visible": False, "has_email_visible": False,
        "mobile_viewport": False, "missing_alt_images": 0,
        "tech_stack": [], "body_text": "", "html": "",
    }
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            t0 = time.monotonic()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            result["load_time_ms"] = int((time.monotonic() - t0) * 1000)
            result["reachable"] = True

            html = page.content()
            body_text = page.evaluate("() => document.body?.innerText || ''")
            result["html"] = html
            result["body_text"] = body_text[:4000]

            result["page_title"] = page.title() or None
            try:
                result["meta_description"] = page.get_attribute('meta[name="description"]', "content")
            except Exception:
                pass
            try:
                result["h1_text"] = page.inner_text("h1")
                result["has_h1"] = True
            except Exception:
                pass
            try:
                result["missing_alt_images"] = page.evaluate(
                    "() => [...document.querySelectorAll('img')].filter(i => !i.alt || !i.alt.trim()).length"
                )
            except Exception:
                pass
            try:
                vp = page.get_attribute('meta[name="viewport"]', "content")
                result["mobile_viewport"] = bool(vp)
            except Exception:
                pass

            hl = html.lower()
            result["has_contact_form"]  = bool(re.search(r"contact|enquir|inquiry", hl) and re.search(r"<form", hl))
            result["has_booking_flow"]  = bool(re.search(r"book|schedule|appointment|calendar|reserve|calendly|acuity", hl))
            result["has_cta"]           = bool(re.search(r"get.?started|free.?trial|request.?demo|contact.?us|call.?us|buy.?now|sign.?up", hl))
            result["has_social_links"]  = bool(re.search(r"facebook\.com|instagram\.com|linkedin\.com|twitter\.com|tiktok\.com", hl))
            result["has_blog"]          = bool(re.search(r"/blog|/news|/articles|/insights", hl))
            result["has_phone_visible"] = bool(re.search(r"\+?\d[\d\s\-(). ]{7,}", body_text[:3000]))
            result["has_email_visible"] = bool(re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", body_text[:3000]))
            result["tech_stack"] = [name for name, pat in TECH_PATTERNS if re.search(pat, html, re.IGNORECASE)]
            browser.close()
    except Exception as exc:
        logger.warning(f"Website audit failed for {url}: {exc}")
    return result


async def audit(website_url: str) -> WebsiteAudit:
    from datetime import datetime, timezone
    url = website_url if website_url.startswith("http") else f"https://{website_url}"
    is_https = url.startswith("https://")

    raw = await asyncio.to_thread(_audit_sync, url)

    # Build gap list
    gaps: list[str] = []
    if not raw["has_cta"]:            gaps.append("No clear call-to-action")
    if not raw["has_contact_form"]:   gaps.append("No contact/enquiry form")
    if not raw["has_booking_flow"]:   gaps.append("No online booking or scheduling")
    if not raw["has_phone_visible"]:  gaps.append("Phone number not prominently displayed")
    if not raw["has_email_visible"]:  gaps.append("Email address not visible")
    if not raw["mobile_viewport"]:    gaps.append("Missing mobile viewport meta tag")
    if not raw["has_h1"]:             gaps.append("Missing H1 heading (SEO)")
    if not raw["meta_description"]:   gaps.append("Missing meta description (SEO)")
    if not is_https:                  gaps.append("Not using HTTPS")
    if raw["missing_alt_images"] > 5: gaps.append(f"{raw['missing_alt_images']} images missing alt text")
    if raw["load_time_ms"] and raw["load_time_ms"] > 5000:
        gaps.append(f"Slow load ({raw['load_time_ms'] / 1000:.1f}s)")
    if not raw["has_social_links"]:   gaps.append("No social media links")
    if not raw["reachable"]:          gaps.append("Website unreachable")

    # Health score
    h = 40
    if raw["reachable"]:          h += 15
    if is_https:                  h += 8
    if raw["mobile_viewport"]:    h += 8
    if raw["has_cta"]:            h += 7
    if raw["has_contact_form"]:   h += 5
    if raw["has_booking_flow"]:   h += 5
    if raw["has_phone_visible"]:  h += 3
    if raw["has_email_visible"]:  h += 3
    if raw["has_h1"]:             h += 3
    if raw["meta_description"]:   h += 3
    h -= min(20, len(gaps) * 2)
    if raw["load_time_ms"] and raw["load_time_ms"] > 5000:
        h -= 10
    site_health = max(0, min(100, h))
    opportunity = 100 - site_health

    # Optional AI narrative
    ai_summary = ai_rec = None
    try:
        from app.services.ai.provider import AI_AVAILABLE, complete_json
        if AI_AVAILABLE and raw["reachable"] and raw["body_text"]:
            result = await complete_json(
                [
                    {"role": "system", "content": "You are a digital marketing expert. Analyse website data and return JSON with 'summary' (2 sentences) and 'recommendation' (2 sentences on biggest improvement opportunity)."},
                    {"role": "user", "content": f"URL: {url}\nTitle: {raw['page_title']}\nGaps: {'; '.join(gaps[:5])}\nTech: {', '.join(raw['tech_stack']) or 'unknown'}\nExcerpt:\n{raw['body_text'][:1000]}"},
                ],
                temperature=0.3,
                max_tokens=250,
                fallback_fn=lambda: {
                    "summary": f"Website has {len(gaps)} identified improvement areas.",
                    "recommendation": gaps[0] if gaps else "Review site for conversion improvements.",
                },
            )
            if result and isinstance(result, dict):
                ai_summary = result.get("summary")
                ai_rec = result.get("recommendation")
    except Exception as exc:
        logger.warning(f"AI website narrative failed: {exc}")

    return WebsiteAudit(
        url=url, reachable=raw["reachable"], load_time_ms=raw["load_time_ms"],
        has_contact_form=raw["has_contact_form"], has_booking_flow=raw["has_booking_flow"],
        has_phone_visible=raw["has_phone_visible"], has_email_visible=raw["has_email_visible"],
        has_cta=raw["has_cta"], has_social_links=raw["has_social_links"],
        has_blog=raw["has_blog"], is_https=is_https, mobile_viewport=raw["mobile_viewport"],
        page_title=raw["page_title"], meta_description=raw["meta_description"],
        has_h1=raw["has_h1"], h1_text=raw["h1_text"],
        missing_alt_images=raw["missing_alt_images"], tech_stack=raw["tech_stack"],
        site_health_score=site_health, opportunity_score=opportunity,
        gaps=gaps, ai_summary=ai_summary, ai_recommendation=ai_rec,
        audited_at=datetime.now(timezone.utc).isoformat(),
    )
