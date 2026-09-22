"""
Lead Intelligence — composite 0-100 score.
Weights: 50% contact/data quality + 30% ICP fit + 20% buying intent.
No AI required — runs entirely on heuristics.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

INDUSTRY_ICP: dict[str, int] = {
    "restaurant": 85, "cafe": 88, "bakery": 80, "hotel": 82, "catering": 78,
    "healthcare": 88, "beauty": 82, "gym": 78, "spa": 78, "dental": 90,
    "legal": 90, "finance": 90, "realestate": 88, "accounting": 85,
    "consulting": 85, "insurance": 85, "tech": 90, "agency": 85,
    "it_services": 82, "telecom": 80, "startup": 82, "retail": 75,
    "ecommerce": 78, "automotive": 80, "electronics": 78, "supermarket": 72,
    "education": 78, "tutoring": 76, "event": 80, "photography": 75,
    "media": 78, "construction": 80, "interior": 78, "plumbing": 75,
    "landscaping": 72, "cleaning": 70, "professional": 82, "general": 70,
}

CITY_SCORES: dict[str, int] = {
    "new york": 95, "nyc": 95, "los angeles": 90, "chicago": 88, "houston": 85,
    "miami": 88, "seattle": 88, "boston": 88, "dallas": 83, "atlanta": 83,
    "austin": 85, "denver": 82, "san diego": 82, "san jose": 85, "washington": 88,
    "london": 95, "manchester": 88, "birmingham": 82, "edinburgh": 82,
    "toronto": 90, "vancouver": 88, "montreal": 85, "calgary": 80,
    "sydney": 90, "melbourne": 90, "brisbane": 82, "perth": 78,
    "jakarta": 95, "surabaya": 85, "bandung": 80, "bali": 88, "denpasar": 85,
    "dubai": 92, "abu dhabi": 88, "riyadh": 88, "doha": 85,
    "berlin": 88, "paris": 90, "amsterdam": 88, "barcelona": 85,
    "singapore": 92, "hong kong": 90, "kuala lumpur": 82, "bangkok": 80,
    "mumbai": 82, "bangalore": 85, "delhi": 83, "hyderabad": 80, "pune": 78,
    "shanghai": 88, "beijing": 85, "shenzhen": 82,
    # Pakistan cities
    "karachi": 90, "lahore": 88, "islamabad": 88, "rawalpindi": 82,
    "faisalabad": 78, "multan": 76, "peshawar": 75, "quetta": 73,
    "sialkot": 76, "gujranwala": 74, "hyderabad": 75, "bahawalpur": 72,
    # UAE
    "abu dhabi": 88, "sharjah": 84, "ajman": 78,
    # Saudi Arabia
    "jeddah": 86, "mecca": 80, "medina": 78, "dammam": 82,
}


@dataclass
class LeadScore:
    score: int
    icp_fit_score: int
    intent_score: int
    priority: str          # HIGH | MEDIUM | LOW
    category: str
    factors: list[str] = field(default_factory=list)
    recommendation: str = ""
    verification_level: str = "unverified"  # verified | partial | unverified


def score_lead(
    name: str,
    address: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    website: Optional[str] = None,
    rating: Optional[str] = None,
    review_count: Optional[int] = None,
    has_website: bool = False,
    reference_url: Optional[str] = None,
    source: Optional[str] = None,
    industry: Optional[str] = None,
    website_audit_score: Optional[int] = None,
    website_opportunity_score: Optional[int] = None,
    has_booking_flow: Optional[bool] = None,
    has_cta: Optional[bool] = None,
    pain_point_count: int = 0,
) -> LeadScore:
    factors: list[str] = []

    # ── 1. Data quality (50% weight) ──────────────────────────────────────
    quality = 40
    if phone:
        quality += 12
        factors.append("✓ Phone number available")
    if email:
        quality += 15
        factors.append("✓ Email address available")
    if address and len(address) > 5:
        quality += 8
        factors.append("✓ Physical address verified")
    if website or has_website:
        quality += 8
        factors.append("✓ Has website")
    else:
        quality += 6
        factors.append("⚡ No website — high pitch opportunity")

    raw_rating = float(rating or 0)
    if raw_rating > 0:
        n = review_count or 1
        bayes = (25 * 4.0 + n * raw_rating) / (25 + n)
        if bayes >= 4.5:       quality += 15; factors.append(f"⭐ Excellent rating {rating}★")
        elif bayes >= 4.0:     quality += 10; factors.append(f"⭐ Good rating {rating}★")
        elif bayes >= 3.5:     quality += 5;  factors.append(f"⭐ Average rating {rating}★")
        rc = review_count or 0
        if rc >= 500:          quality += 8;  factors.append("📊 500+ reviews")
        elif rc >= 100:        quality += 5;  factors.append("📊 100+ reviews")
        elif rc >= 20:         quality += 2;  factors.append("📊 20+ reviews")

    if source == "google_maps":   quality += 5; factors.append("✓ Google Maps verified")
    elif source == "yelp":        quality += 4; factors.append("✓ Yelp verified")
    elif source == "demo_data":   quality -= 20; factors.append("⚠️ Demo data")
    if reference_url:             quality += 3; factors.append("✓ Listing URL available")

    quality = max(0, min(100, quality))

    # ── 2. ICP fit (30% weight) ────────────────────────────────────────────
    icp = 50
    ind_lower = (industry or "").lower().replace(" ", "_")
    for key, val in INDUSTRY_ICP.items():
        if key in ind_lower or ind_lower in key:
            icp = round(val * 0.9)
            factors.append(f"🏢 ICP match: {industry}")
            break

    addr_lower = (address or "").lower()
    for city, city_score in CITY_SCORES.items():
        if city in addr_lower:
            bonus = round((city_score - 70) / 4)
            if bonus > 0:
                icp = min(100, icp + bonus)
                factors.append(f"📍 Premium market: {city.title()}")
            break
    icp = max(0, min(100, icp))

    # ── 3. Buying intent (20% weight) ──────────────────────────────────────
    intent = 30
    if not website and not has_website:
        intent += 40
        factors.append("🔥 No website — immediate opportunity")
    if has_website and website_opportunity_score is not None:
        if website_opportunity_score >= 70:
            intent += 30
            factors.append(f"🔥 High site opportunity score ({website_opportunity_score}/100)")
        elif website_opportunity_score >= 50:
            intent += 15
            factors.append("📈 Moderate website improvement potential")
    if has_website and has_booking_flow is False:
        intent += 10
        factors.append("⚡ No booking flow on site")
    if has_website and has_cta is False:
        intent += 10
        factors.append("⚡ No call-to-action on site")
    if pain_point_count >= 3:
        intent += 10
        factors.append(f"🎯 {pain_point_count} pain points identified")
    if raw_rating > 0 and raw_rating < 4.0:
        intent += 8
        factors.append("📉 Below-average rating — reputation pain")
    intent = max(0, min(100, intent))

    # ── Composite ──────────────────────────────────────────────────────────
    composite = max(0, min(100, round(quality * 0.50 + icp * 0.30 + intent * 0.20)))
    priority = "HIGH" if composite >= 75 else "MEDIUM" if composite >= 52 else "LOW"
    category = industry or "General Business"

    has_contact = bool(phone or email)
    has_addr = bool(address)
    if has_contact and has_addr:    verification = "verified"
    elif has_contact or has_addr:   verification = "partial"
    else:                            verification = "unverified"

    if priority == "HIGH":
        rec = ("High-value lead with verified contact. Reach out today."
               if verification == "verified"
               else "High-value lead. Enrich contact data before outreach.")
    elif priority == "MEDIUM":
        rec = "Moderate potential. Include in bulk outreach sequences."
    else:
        rec = "Lower priority. Keep in pipeline for follow-up."

    return LeadScore(
        score=composite, icp_fit_score=icp, intent_score=intent,
        priority=priority, category=category, factors=factors,
        recommendation=rec, verification_level=verification,
    )
