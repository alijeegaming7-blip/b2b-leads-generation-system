"""
Social Media Link Extractor

Extracts social media profiles from business websites and text.
Handles all countries including Pakistan, UAE, India, etc.
"""
from __future__ import annotations

import re
import logging
from typing import Dict, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ── False-positive handle blacklist ───────────────────────────────────────────
_HANDLE_BLACKLIST = {
    # Facebook share/utility paths
    "share", "sharer", "sharer.php", "intent", "dialog", "plugins",
    "home", "login", "signup", "register", "logout", "oauth", "callback",
    "groups", "events", "pages", "watch", "gaming", "marketplace",
    "help", "legal", "about", "privacy", "terms", "policy",
    # Twitter/X utility
    "hashtag", "search", "explore", "notifications", "messages",
    # Generic noise
    "undefined", "null", "true", "false", "none", "n/a",
    # Image/file extensions
    "jpg", "jpeg", "png", "gif", "svg", "webp", "ico",
}

# Regex patterns for each platform
_PATTERNS: Dict[str, List[str]] = {
    "facebook": [
        r'facebook\.com/(?:pages/[^/]+/)?([a-zA-Z0-9][a-zA-Z0-9._\-]{1,})',
        r'fb\.com/([a-zA-Z0-9][a-zA-Z0-9._\-]{1,})',
    ],
    "instagram": [
        r'instagram\.com/([a-zA-Z0-9][a-zA-Z0-9._]{1,})',
    ],
    "twitter": [
        r'twitter\.com/([a-zA-Z0-9_]{2,})',
        r'x\.com/([a-zA-Z0-9_]{2,})',
    ],
    "linkedin": [
        r'linkedin\.com/company/([a-zA-Z0-9\-]+)',
        r'linkedin\.com/in/([a-zA-Z0-9\-]+)',
    ],
    "youtube": [
        r'youtube\.com/(?:c/|channel/|user/|@)([a-zA-Z0-9_\-]+)',
        r'youtube\.com/([a-zA-Z0-9_\-]{3,})',
    ],
    "tiktok": [
        r'tiktok\.com/@([a-zA-Z0-9._\-]+)',
    ],
    "pinterest": [
        r'pinterest\.com/([a-zA-Z0-9_\-]+)',
    ],
    "whatsapp": [
        r'wa\.me/(\+?[0-9]{7,15})',
        r'api\.whatsapp\.com/send\?phone=(\+?[0-9]{7,15})',
    ],
    "telegram": [
        r't\.me/([a-zA-Z0-9_]{3,})',
        r'telegram\.me/([a-zA-Z0-9_]{3,})',
    ],
}

# Full URL templates for each platform
_URL_TEMPLATES: Dict[str, str] = {
    "facebook":  "https://www.facebook.com/{handle}",
    "instagram": "https://www.instagram.com/{handle}",
    "twitter":   "https://twitter.com/{handle}",
    "linkedin":  "https://www.linkedin.com/company/{handle}",
    "youtube":   "https://www.youtube.com/{handle}",
    "tiktok":    "https://www.tiktok.com/@{handle}",
    "pinterest": "https://www.pinterest.com/{handle}",
    "whatsapp":  "https://wa.me/{handle}",
    "telegram":  "https://t.me/{handle}",
}


class SocialMediaExtractor:
    """Extracts social media links from HTML content."""

    @classmethod
    def extract_from_text(cls, text: str) -> Dict[str, str]:
        """
        Extract all social media links from HTML/text.

        Returns dict mapping platform → full URL.
        """
        if not text:
            return {}

        results: Dict[str, str] = {}

        for platform, patterns in _PATTERNS.items():
            if platform in results:
                continue

            for pattern in patterns:
                # Search in full text
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    handle = match.group(1).strip().strip("/").rstrip("?")

                    # Skip blacklisted handles
                    if handle.lower() in _HANDLE_BLACKLIST:
                        continue
                    # Skip very short handles (likely noise)
                    if len(handle) < 2:
                        continue
                    # Skip handles that look like file paths
                    if re.search(r'\.(php|html|htm|js|css|jpg|png|gif)$', handle, re.I):
                        continue

                    url = _URL_TEMPLATES.get(platform, "").format(handle=handle)
                    if url:
                        results[platform] = url
                        break

                if platform in results:
                    break

        return results

    @classmethod
    def validate_social_links(cls, links: Dict[str, str]) -> Dict[str, str]:
        """Filter to only valid URLs."""
        valid = {}
        for platform, url in links.items():
            if not url or not url.startswith("http"):
                continue
            try:
                p = urlparse(url)
                if p.netloc and p.scheme in ("http", "https"):
                    valid[platform] = url
            except Exception:
                continue
        return valid


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract valid email addresses from text.
    Returns list sorted by business-email priority (info@, contact@, etc.)
    """
    if not text:
        return []

    _EMAIL_DOMAIN_BLACKLIST = {
        "example.com", "test.com", "localhost", "domain.com", "email.com",
        "sentry.io", "wixpress.com", "squarespace.com", "shopify.com",
        "schema.org", "w3.org", "cloudflare.com", "akamai.net",
        "google.com", "googleapis.com", "jquery.com", "wordpress.com",
    }

    raw = re.findall(
        r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b',
        text,
    )

    seen: set = set()
    valid: List[str] = []

    for em in raw:
        em = em.lower().strip()
        if em in seen:
            continue
        seen.add(em)

        domain = em.split("@")[-1] if "@" in em else ""

        if any(bl in domain for bl in _EMAIL_DOMAIN_BLACKLIST):
            continue
        if re.search(r'noreply|no.reply|donotreply|bounce|spam|abuse', em):
            continue
        if len(domain.split(".")[-1]) < 2:
            continue

        valid.append(em)

    # Prioritise business contact emails
    def _priority(e: str) -> int:
        local = e.split("@")[0]
        for i, kw in enumerate(["info", "contact", "hello", "sales", "support",
                                  "office", "enquiry", "inquiry", "mail", "admin"]):
            if local.startswith(kw):
                return i
        return 99

    valid.sort(key=_priority)
    return valid[:5]


def extract_phone_numbers_from_text(text: str) -> List[str]:
    """Extract phone numbers from text."""
    if not text:
        return []

    patterns = [
        r'\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # international
        r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',                        # US (555) 123-4567
        r'\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',                            # 555-123-4567
        r'\d{4}[\s\-]?\d{3}[\s\-]?\d{4}',                            # PK 0300 1234567
        r'0\d{2,3}[\s\-]?\d{7,8}',                                    # PK/IN local
    ]

    phones: List[str] = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            phone = m.group(0).strip()
            digits = re.sub(r'\D', '', phone)
            if 7 <= len(digits) <= 15:
                phones.append(phone)

    return list(dict.fromkeys(phones))[:3]   # deduplicate, max 3
