"""
Demo Mode — controls trial access for client demos.

When demo_mode = true:
  - Phone numbers are blurred  →  "+92 3** ****999"
  - Emails are blurred         →  "c****@****.pk"
  - Social media links hidden  →  {"facebook": "DEMO_LOCKED", ...}
  - Additional emails hidden
  - All connectors disabled except Google Maps
  - API returns a demo_mode=true flag so frontend can show upgrade prompts
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent.parent / "demo_config.json"

_cache: dict | None = None


def _load() -> dict:
    global _cache
    try:
        _cache = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        _cache = {"demo_mode": False}
    return _cache


def get_config() -> dict:
    """Always re-read from disk so toggling takes effect without restart."""
    return _load()


def is_demo() -> bool:
    return bool(get_config().get("demo_mode", False))


# ── blurring helpers ───────────────────────────────────────────────────────────

def blur_phone(phone: str | None) -> str | None:
    """'+92 300 1234567'  →  '+92 3** ****567'"""
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 6:
        return "*** *** ***"
    # Keep first 3 and last 3 digits visible
    visible_start = digits[:3]
    visible_end   = digits[-3:]
    middle_stars  = "*" * (len(digits) - 6)
    blurred_digits = visible_start + middle_stars + visible_end
    # Rebuild with + prefix if international
    if phone.strip().startswith("+"):
        return f"+{blurred_digits[:2]} {blurred_digits[2:5]}** ****{blurred_digits[-3:]}"
    return f"{blurred_digits[:3]}** ****{blurred_digits[-3:]}"


def blur_email(email: str | None) -> str | None:
    """'contact@dentist.pk'  →  'c*****@*****.pk'"""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    # Blur local part — keep first char
    blurred_local = local[0] + "*" * min(len(local) - 1, 5)
    # Blur domain — keep TLD
    domain_parts = domain.rsplit(".", 1)
    if len(domain_parts) == 2:
        blurred_domain = "*" * min(len(domain_parts[0]), 5) + "." + domain_parts[1]
    else:
        blurred_domain = "*" * 5
    return f"{blurred_local}@{blurred_domain}"


def blur_website(url: str | None) -> str | None:
    """Keep the domain visible — website isn't as sensitive."""
    return url  # Websites stay visible — they're on Google Maps anyway


def blur_social(social: dict | None) -> dict:
    """Replace social links with DEMO_LOCKED placeholder."""
    if not social:
        return {}
    return {k: "DEMO_LOCKED" for k in social}


def apply_demo_blur(lead: dict) -> dict:
    """
    Given a serialised lead dict, blur all sensitive contact fields.
    Returns a new dict — never mutates the original.
    """
    if not is_demo():
        return lead

    d = dict(lead)

    d["phone"]            = blur_phone(d.get("phone"))
    d["email"]            = blur_email(d.get("email"))
    d["socialMedia"]      = blur_social(d.get("socialMedia"))
    d["additionalEmails"] = []          # hide extra emails completely
    # Keep: name, address, rating, reviewCount, score, website, referenceUrl

    return d


def demo_status_payload() -> dict:
    """Returns extra keys injected into responses when demo mode is active."""
    cfg = get_config()
    return {
        "demo_mode":   True,
        "buy_link":    cfg.get("demo_buy_link",    ""),
        "demo_price":  cfg.get("demo_price",       "$500"),
        "seller_name": cfg.get("demo_contact_name",""),
        "upgrade_msg": (
            "🔒 Contact details are hidden in Demo Mode. "
            "Purchase the full system to unlock phone numbers, "
            "emails, and social media profiles for every lead."
        ),
    }
