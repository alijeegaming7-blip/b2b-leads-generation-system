"""Sales Research Agent — produces a SalesBrief per lead (heuristic + optional Grok enrichment)."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.website_auditor import WebsiteAudit

logger = logging.getLogger(__name__)


@dataclass
class PainPoint:
    title: str
    evidence: str
    severity: str  # high | medium | low


@dataclass
class BuyingSignal:
    signal: str
    strength: str  # strong | moderate | weak


@dataclass
class SalesBrief:
    business_name: str
    industry: str
    location: str
    one_liner: str
    business_maturity: str        # new | growing | established | unknown
    pain_points: list[PainPoint] = field(default_factory=list)
    buying_signals: list[BuyingSignal] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    digital_presence_grade: str = "F"  # A–F
    urgency_level: str = "low"         # high | medium | low
    best_channel: str = "email"        # email | whatsapp | linkedin | call
    talk_track_opener: str = ""
    researched_at: str = ""
    ai_enriched: bool = False


async def research(
    name: str,
    industry: str,
    address: Optional[str] = None,
    website: Optional[str] = None,
    rating: Optional[str] = None,
    review_count: Optional[int] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    score: int = 0,
    website_audit: "Optional[WebsiteAudit]" = None,
) -> SalesBrief:
    brief = _heuristic(name, industry, address, website, rating, review_count, phone, email, website_audit)
    try:
        from app.services.ai.provider import AI_AVAILABLE
        if AI_AVAILABLE:
            enriched = await _enrich_ai(name, industry, address, rating, review_count, website, website_audit, brief)
            if enriched:
                return enriched
    except Exception as exc:
        logger.warning(f"AI research enrichment failed for {name}: {exc}")
    return brief


def _heuristic(
    name: str, industry: str,
    address: Optional[str], website: Optional[str],
    rating: Optional[str], review_count: Optional[int],
    phone: Optional[str], email: Optional[str],
    audit: "Optional[WebsiteAudit]",
) -> SalesBrief:
    pain_points: list[PainPoint] = []
    buying_signals: list[BuyingSignal] = []
    strengths: list[str] = []
    raw = float(rating or 0)
    reviews = review_count or 0

    if audit:
        if not audit.has_contact_form:
            pain_points.append(PainPoint("No online enquiry form", "Website audit: no contact form detected", "high"))
        if not audit.has_booking_flow:
            pain_points.append(PainPoint("No online booking/scheduling", "Website audit: no booking flow detected", "high"))
        if not audit.has_cta:
            pain_points.append(PainPoint("Weak conversion flow", "No clear call-to-action on homepage", "high"))
        if not audit.mobile_viewport:
            pain_points.append(PainPoint("Poor mobile experience", "Missing viewport meta tag", "medium"))
        if not audit.meta_description:
            pain_points.append(PainPoint("SEO gaps", "Missing meta description", "medium"))
        if audit.opportunity_score >= 60:
            buying_signals.append(BuyingSignal(f"Website opportunity score {audit.opportunity_score}/100", "strong"))
        if audit.tech_stack:
            strengths.append(f"Uses {', '.join(audit.tech_stack[:3])}")
        if audit.has_blog:
            strengths.append("Has content/blog presence")
    elif not website:
        pain_points.append(PainPoint("No website", "No website URL found", "high"))
        buying_signals.append(BuyingSignal("No digital presence — prime opportunity", "strong"))

    if raw >= 4.5 and reviews >= 50:
        strengths.append(f"Strong reputation: {rating}★ ({reviews} reviews)")
        buying_signals.append(BuyingSignal("Established business with strong reviews", "moderate"))
    elif 0 < raw < 4.0 and reviews >= 10:
        pain_points.append(PainPoint("Reputation management needed", f"{rating}★ rating ({reviews} reviews)", "medium"))

    if not email: pain_points.append(PainPoint("No email contact", "Not found in lead data", "low"))
    if not phone: pain_points.append(PainPoint("No phone contact", "Not found in lead data", "low"))

    maturity = ("established" if reviews >= 200 else "growing" if reviews >= 30
                else "new" if reviews >= 1 else "unknown")
    health = audit.site_health_score if audit else (40 if website else 0)
    grade = "A" if health >= 80 else "B" if health >= 65 else "C" if health >= 50 else "D" if health >= 35 else "F"
    high_pains = sum(1 for p in pain_points if p.severity == "high")
    urgency = "high" if high_pains >= 2 else "medium" if pain_points else "low"
    channel = "email" if email else "whatsapp" if phone else "call"

    loc_parts = (address or "").split(",")
    loc = loc_parts[-1].strip() if len(loc_parts) > 1 else (address or "")
    rating_tag = f" rated {rating}★" if rating and rating != "N/A" else ""
    loc_tag = f" in {loc}" if loc else ""
    one_liner = f"{name} is a{' ' + maturity if maturity != 'unknown' else ''} {industry} business{loc_tag}{rating_tag}."

    opener = (
        f"I noticed {name} has '{pain_points[0].title.lower()}' — I'd love to show you how we've solved this for similar businesses."
        if pain_points else f"I came across {name} and see a real opportunity to help you grow."
    )

    return SalesBrief(
        business_name=name, industry=industry, location=address or "",
        one_liner=one_liner, business_maturity=maturity,
        pain_points=pain_points, buying_signals=buying_signals, strengths=strengths,
        digital_presence_grade=grade, urgency_level=urgency, best_channel=channel,
        talk_track_opener=opener, researched_at=datetime.now(timezone.utc).isoformat(),
        ai_enriched=False,
    )


async def _enrich_ai(
    name: str, industry: str,
    address: Optional[str], rating: Optional[str], review_count: Optional[int],
    website: Optional[str], audit: "Optional[WebsiteAudit]",
    heuristic: SalesBrief,
) -> Optional[SalesBrief]:
    from app.services.ai.provider import complete_json
    audit_line = (
        f"Website health: {audit.site_health_score}/100 | Gaps: {'; '.join(audit.gaps[:4])}"
        if audit else (f"Website: {website}" if website else "No website")
    )
    result = await complete_json(
        [
            {"role": "system", "content": "You are a B2B sales intelligence analyst. Return a structured JSON sales brief. Be evidence-based and concise."},
            {"role": "user", "content": (
                f"Business: {name}\nIndustry: {industry}\nLocation: {address or 'unknown'}\n"
                f"Rating: {rating or 'N/A'} ({review_count or 0} reviews)\n{audit_line}\n\n"
                'Return JSON:\n{"oneLiner":"...","businessMaturity":"new|growing|established|unknown",'
                '"painPoints":[{"title":"...","evidence":"...","severity":"high|medium|low"}],'
                '"buyingSignals":[{"signal":"...","strength":"strong|moderate|weak"}],'
                '"strengths":["..."],"urgencyLevel":"high|medium|low",'
                '"bestChannel":"email|whatsapp|linkedin|call","talkTrackOpener":"..."}'
            )},
        ],
        temperature=0.3,
        max_tokens=700,
    )
    if not result or not isinstance(result, dict):
        return None

    return SalesBrief(
        business_name=name, industry=industry, location=address or "",
        one_liner=result.get("oneLiner", heuristic.one_liner),
        business_maturity=result.get("businessMaturity", heuristic.business_maturity),
        pain_points=[
            PainPoint(p.get("title", ""), p.get("evidence", ""), p.get("severity", "medium"))
            for p in (result.get("painPoints") or [])
        ],
        buying_signals=[
            BuyingSignal(s.get("signal", ""), s.get("strength", "moderate"))
            for s in (result.get("buyingSignals") or [])
        ],
        strengths=result.get("strengths", heuristic.strengths),
        digital_presence_grade=heuristic.digital_presence_grade,
        urgency_level=result.get("urgencyLevel", heuristic.urgency_level),
        best_channel=result.get("bestChannel", heuristic.best_channel),
        talk_track_opener=result.get("talkTrackOpener", heuristic.talk_track_opener),
        researched_at=heuristic.researched_at,
        ai_enriched=True,
    )
