"""Opportunity Finder — surfaces multiple distinct problems per company."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.sales_research import SalesBrief
    from app.services.ai.website_auditor import WebsiteAudit

logger = logging.getLogger(__name__)

_URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Opportunity:
    id: str
    title: str
    problem: str
    impact: str
    urgency: str          # high | medium | low
    category: str         # website | digital-marketing | automation | crm | branding
    evidence_tags: list[str] = field(default_factory=list)


_TEMPLATES = [
    {
        "id": "no-website",
        "title": "No online presence",
        "problem": "No website — invisible to customers searching online.",
        "impact": "Losing revenue to competitors easily found on Google.",
        "urgency": "high", "category": "website",
        "condition": lambda lead, audit: not lead.get("website"),
    },
    {
        "id": "no-booking-flow",
        "title": "No online booking/scheduling",
        "problem": "Customers can't book online — must call during business hours.",
        "impact": "Missing bookings from customers who won't call, especially evenings/weekends.",
        "urgency": "high", "category": "website",
        "condition": lambda lead, audit: audit is not None and not audit.has_booking_flow,
    },
    {
        "id": "no-contact-form",
        "title": "No enquiry/contact form",
        "problem": "No online form — leads have no easy way to reach out.",
        "impact": "Lost leads who visit the site but don't take action.",
        "urgency": "high", "category": "website",
        "condition": lambda lead, audit: audit is not None and not audit.has_contact_form,
    },
    {
        "id": "weak-cta",
        "title": "Poor website conversion",
        "problem": "No clear call-to-action — visitors confused about next steps.",
        "impact": "High bounce rate and low conversion from web traffic.",
        "urgency": "high", "category": "website",
        "condition": lambda lead, audit: audit is not None and not audit.has_cta,
    },
    {
        "id": "seo-gaps",
        "title": "SEO gaps hurting visibility",
        "problem": "Missing basic SEO — harder to find on Google.",
        "impact": "Lower ranking, losing customers to better-optimised competitors.",
        "urgency": "medium", "category": "digital-marketing",
        "condition": lambda lead, audit: audit is not None and (not audit.meta_description or not audit.has_h1),
    },
    {
        "id": "no-mobile",
        "title": "Poor mobile experience",
        "problem": "Website not optimised for mobile users.",
        "impact": "60%+ of web traffic is mobile; poor UX drives users away.",
        "urgency": "medium", "category": "website",
        "condition": lambda lead, audit: audit is not None and not audit.mobile_viewport,
    },
    {
        "id": "no-social",
        "title": "No social media presence",
        "problem": "No social links — missing a major brand-awareness channel.",
        "impact": "Competitors with active social capture more attention.",
        "urgency": "low", "category": "digital-marketing",
        "condition": lambda lead, audit: audit is not None and not audit.has_social_links,
    },
    {
        "id": "slow-site",
        "title": "Slow website performance",
        "problem": "Website takes over 5 seconds to load.",
        "impact": "53% of users abandon sites that take over 3s to load.",
        "urgency": "medium", "category": "website",
        "condition": lambda lead, audit: audit is not None and bool(audit.load_time_ms and audit.load_time_ms > 5000),
    },
    {
        "id": "low-rating",
        "title": "Reputation management opportunity",
        "problem": "Below-average rating signals unresolved customer issues.",
        "impact": "Low ratings directly reduce conversion.",
        "urgency": "medium", "category": "crm",
        "condition": lambda lead, audit: float(lead.get("rating") or 5) < 4.0 and (lead.get("review_count") or 0) >= 5,
    },
    {
        "id": "outdated-tech",
        "title": "Outdated or no CMS",
        "problem": "Website built on outdated platform, limiting capabilities.",
        "impact": "Difficult to update, maintain or scale without expensive help.",
        "urgency": "low", "category": "website",
        "condition": lambda lead, audit: audit is not None and audit.reachable and not audit.tech_stack,
    },
]


async def find_opportunities(
    lead: dict,
    brief: "SalesBrief",
    audit: "Optional[WebsiteAudit]" = None,
) -> list[Opportunity]:
    heuristic = _heuristic(lead, audit)

    try:
        from app.services.ai.provider import AI_AVAILABLE
        if AI_AVAILABLE and (brief.ai_enriched or (audit and audit.ai_summary)):
            enriched = await _enrich_ai(lead, brief, audit, heuristic)
            if enriched:
                return enriched
    except Exception as exc:
        logger.warning(f"AI opportunity enrichment failed: {exc}")

    return heuristic


def _heuristic(lead: dict, audit: "Optional[WebsiteAudit]") -> list[Opportunity]:
    results: list[Opportunity] = []
    for t in _TEMPLATES:
        try:
            if t["condition"](lead, audit):  # type: ignore[operator]
                tags = []
                if audit:
                    tags.append(f"Site health: {audit.site_health_score}/100")
                if lead.get("rating"):
                    tags.append(f"Rating: {lead['rating']}★")
                results.append(Opportunity(
                    id=t["id"], title=t["title"],
                    problem=t["problem"], impact=t["impact"],
                    urgency=t["urgency"], category=t["category"],
                    evidence_tags=tags,
                ))
        except Exception:
            continue
    return sorted(results, key=lambda o: _URGENCY_ORDER.get(o.urgency, 1))


async def _enrich_ai(
    lead: dict,
    brief: "SalesBrief",
    audit: "Optional[WebsiteAudit]",
    heuristic: list[Opportunity],
) -> Optional[list[Opportunity]]:
    from app.services.ai.provider import complete_json
    heur_summary = "\n".join(f"- {o.title} ({o.urgency})" for o in heuristic)
    result = await complete_json(
        [
            {"role": "system", "content": "You are a B2B sales expert. Identify distinct business problems. Return JSON only."},
            {"role": "user", "content": (
                f"Business: {brief.business_name}\nIndustry: {brief.industry}\n"
                f"Summary: {brief.one_liner}\n"
                f"Website health: {audit.site_health_score if audit else 'no website'}/100\n"
                f"Existing opportunities found:\n{heur_summary}\n\n"
                "Add up to 3 additional AI-identified opportunities. Keep total under 8.\n"
                'Return JSON: {"opportunities":[{"id":"...","title":"...","problem":"...","impact":"...",'
                '"urgency":"high|medium|low","category":"website|digital-marketing|automation|crm|branding",'
                '"evidenceTags":["..."]}]}'
            )},
        ],
        temperature=0.4,
        max_tokens=800,
    )
    if not result or not isinstance(result, dict) or "opportunities" not in result:
        return None

    ai_opps: list[Opportunity] = []
    for o in result["opportunities"]:
        if isinstance(o, dict):
            ai_opps.append(Opportunity(
                id=o.get("id", f"ai-{len(ai_opps)}"),
                title=o.get("title", ""),
                problem=o.get("problem", ""),
                impact=o.get("impact", ""),
                urgency=o.get("urgency", "medium"),
                category=o.get("category", "website"),
                evidence_tags=o.get("evidenceTags", []),
            ))

    ai_ids = {o.id for o in ai_opps}
    merged = ai_opps + [h for h in heuristic if h.id not in ai_ids]
    return sorted(merged, key=lambda o: _URGENCY_ORDER.get(o.urgency, 1))[:8]
