"""Service Recommendation + Case Study Matching."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.opportunity_finder import Opportunity
    from app.services.ai.sales_research import SalesBrief

logger = logging.getLogger(__name__)

EZITECH_SERVICES: list[dict] = [
    {"name": "Website Design & Development",
     "opp_ids": ["no-website", "no-booking-flow", "no-contact-form", "weak-cta", "no-mobile", "outdated-tech", "slow-site"],
     "industries": []},
    {"name": "SEO & Local Search Optimisation",
     "opp_ids": ["seo-gaps", "no-website"],
     "industries": []},
    {"name": "Online Booking & Appointment System",
     "opp_ids": ["no-booking-flow"],
     "industries": ["restaurant", "cafe", "healthcare", "beauty", "spa", "gym", "dental", "consulting"]},
    {"name": "Social Media Management",
     "opp_ids": ["no-social"],
     "industries": []},
    {"name": "CRM & Lead Management System",
     "opp_ids": ["no-contact-form", "low-rating"],
     "industries": []},
    {"name": "Email Marketing & Automation",
     "opp_ids": ["no-contact-form"],
     "industries": []},
    {"name": "Reputation Management",
     "opp_ids": ["low-rating"],
     "industries": []},
    {"name": "Google Ads / PPC Campaigns",
     "opp_ids": ["seo-gaps", "weak-cta"],
     "industries": []},
    {"name": "Business Process Automation",
     "opp_ids": ["no-booking-flow", "no-contact-form"],
     "industries": ["legal", "finance", "accounting", "consulting", "realestate"]},
    {"name": "E-commerce Setup & Optimisation",
     "opp_ids": ["no-website", "weak-cta", "outdated-tech"],
     "industries": ["retail", "ecommerce", "food", "bakery"]},
]

SEED_CASE_STUDIES: list[dict] = [
    {"id": "seed-dental-booking",   "title": "2x Bookings for Dubai Dental Clinic",
     "client_industry": "dental",
     "problem": "No online booking — all appointments by phone.",
     "solution": "Custom booking system + mobile-first website.",
     "outcome": "Bookings doubled in 3 months. 40% came outside business hours.",
     "tags": ["dental", "healthcare", "booking", "website", "mobile"]},
    {"id": "seed-restaurant-seo",   "title": "Restaurant Ranks #1 on Google Maps",
     "client_industry": "restaurant",
     "problem": "Invisible on Google — losing to nearby chains.",
     "solution": "Full SEO + Google Business Profile management.",
     "outcome": "#1 for primary keyword in 6 weeks. 65% more walk-ins.",
     "tags": ["restaurant", "cafe", "seo", "google", "local"]},
    {"id": "seed-retail-ecommerce", "title": "Retail Store Launches E-commerce",
     "client_industry": "retail",
     "problem": "Physical-only retailer losing to online competitors.",
     "solution": "Shopify store with inventory integration.",
     "outcome": "Online sales = 30% of total revenue in 4 months.",
     "tags": ["retail", "ecommerce", "shopify"]},
    {"id": "seed-law-crm",          "title": "Law Firm Automates Lead Follow-up",
     "client_industry": "legal",
     "problem": "Follow-up was manual and inconsistent.",
     "solution": "CRM + email automation for enquiry pipeline.",
     "outcome": "90% of enquiries get response within 1 hour. Conversion +35%.",
     "tags": ["legal", "crm", "automation", "email"]},
    {"id": "seed-salon-reputation", "title": "Salon Recovers From Low Rating",
     "client_industry": "beauty",
     "problem": "Stuck at 3.2 stars on Google.",
     "solution": "Review management workflow.",
     "outcome": "Rating rose to 4.6 in 8 weeks. Booked 3 weeks in advance.",
     "tags": ["beauty", "salon", "spa", "reputation", "reviews"]},
    {"id": "seed-gym-social",       "title": "Gym Grows 500 Instagram Followers in 60 Days",
     "client_industry": "gym",
     "problem": "No social presence.",
     "solution": "Content strategy + local Instagram ads.",
     "outcome": "500 new followers, 12 new memberships from Instagram.",
     "tags": ["gym", "fitness", "social-media", "instagram"]},
    {"id": "seed-agency-website",   "title": "Agency Website Redesign — 3x Enquiry Rate",
     "client_industry": "consulting",
     "problem": "Slow, outdated website with no CTA.",
     "solution": "Full redesign: fast load, clear service pages, forms everywhere.",
     "outcome": "Load time 7s→1.4s. Enquiry rate tripled in 30 days.",
     "tags": ["consulting", "agency", "website", "cta", "conversion"]},
]


@dataclass
class ServiceMatch:
    service_id: Optional[str]
    service_name: str
    description: str
    why_this_lead: str
    confidence: str       # high | medium | low
    opportunity_ids: list[str] = field(default_factory=list)


@dataclass
class CaseStudyMatch:
    case_study_id: Optional[str]
    title: str
    client_industry: str
    problem: str
    solution: str
    outcome: str
    relevance_score: int
    relevance_reason: str
    matched_opportunity_ids: list[str] = field(default_factory=list)


async def recommend_services(
    opportunities: "list[Opportunity]",
    brief: "SalesBrief",
    kb_items: Optional[list[dict]] = None,
) -> list[ServiceMatch]:
    opp_ids = {o.id for o in opportunities}
    ind = brief.industry.lower()
    matched: list[ServiceMatch] = []
    used: set[str] = set()

    for svc in EZITECH_SERVICES:
        matching = [oid for oid in svc["opp_ids"] if oid in opp_ids]
        if not matching:
            continue
        if svc["industries"] and not any(i in ind for i in svc["industries"]):
            continue
        if svc["name"] in used:
            continue
        used.add(svc["name"])

        top_opp = next((o for o in opportunities if o.id in matching), None)
        why = (
            f"{brief.business_name} has \"{top_opp.title}\" — {svc['name']} directly solves this."
            if top_opp else
            f"{brief.business_name} matches businesses that benefit from {svc['name']}."
        )
        conf = "high" if (len(matching) >= 2 or (top_opp and top_opp.urgency == "high")) else "medium"

        kb_match = next(
            (kb for kb in (kb_items or [])
             if svc["name"].split()[0].lower() in kb.get("title", "").lower()),
            None,
        )
        matched.append(ServiceMatch(
            service_id=kb_match["id"] if kb_match else None,
            service_name=kb_match["title"] if kb_match else svc["name"],
            description=kb_match.get("description", f"Professional {svc['name']} service.") if kb_match else f"Professional {svc['name']} service.",
            why_this_lead=why,
            confidence=conf,
            opportunity_ids=matching,
        ))

    cmap = {"high": 0, "medium": 1, "low": 2}
    result = sorted(matched, key=lambda m: (cmap[m.confidence], -len(m.opportunity_ids)))[:5]

    # Optional AI contextualisation
    try:
        from app.services.ai.provider import AI_AVAILABLE, complete_json
        if AI_AVAILABLE and result:
            ai_result = await complete_json(
                [
                    {"role": "system", "content": "Contextualise why each service is perfect for this specific business. Return JSON only."},
                    {"role": "user", "content": (
                        f"Business: {brief.business_name} ({brief.industry})\nSummary: {brief.one_liner}\n"
                        f"Pain points: {', '.join(p.title for p in brief.pain_points[:3])}\n"
                        f"Services:\n{chr(10).join(f'{i+1}. {m.service_name}' for i, m in enumerate(result))}\n\n"
                        'Return JSON: {"recommendations":[{"serviceName":"...","whyThisLead":"one sentence specific to THIS business","confidence":"high|medium|low"}]}'
                    )},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            if ai_result and isinstance(ai_result, dict) and "recommendations" in ai_result:
                for match in result:
                    rec = next(
                        (r for r in ai_result["recommendations"]
                         if isinstance(r, dict) and match.service_name.split()[0].lower() in r.get("serviceName", "").lower()),
                        None,
                    )
                    if rec:
                        match.why_this_lead = rec.get("whyThisLead", match.why_this_lead)
                        match.confidence = rec.get("confidence", match.confidence)
    except Exception as exc:
        logger.warning(f"AI service contextualisation failed: {exc}")

    return result


async def match_case_study(
    opportunities: "list[Opportunity]",
    brief: "SalesBrief",
    db_case_studies: Optional[list[dict]] = None,
) -> Optional[CaseStudyMatch]:
    import json as _json

    def _parse_tags(v: object) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                parsed = _json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        return []

    all_studies = list(SEED_CASE_STUDIES) + (db_case_studies or [])
    if not all_studies:
        return None

    ind = brief.industry.lower()
    opp_cats = {o.category for o in opportunities}
    opp_ids = {o.id for o in opportunities}

    def _score(cs: dict) -> int:
        tags = _parse_tags(cs.get("tags", []))
        s = 0
        if any(ind in t or t in ind for t in tags): s += 40
        if "website" in opp_cats and any(t in ["website", "booking", "cta", "mobile"] for t in tags): s += 20
        if "digital-marketing" in opp_cats and any(t in ["seo", "google", "social-media", "local"] for t in tags): s += 20
        if "crm" in opp_cats and any(t in ["crm", "automation", "email"] for t in tags): s += 20
        if "no-booking-flow" in opp_ids and "booking" in tags: s += 15
        if "low-rating" in opp_ids and "reputation" in tags: s += 15
        if "seo-gaps" in opp_ids and "seo" in tags: s += 15
        return s

    best = max(all_studies, key=_score)
    best_score = _score(best)
    if best_score == 0:
        return None

    tags = _parse_tags(best.get("tags", []))
    matched_opps = [o.id for o in opportunities if any(t in o.category or o.category in t for t in tags)]
    reason = f"Similar {best.get('client_industry', '')} industry with matching challenges."

    try:
        from app.services.ai.provider import AI_AVAILABLE, complete_json
        if AI_AVAILABLE:
            r = await complete_json(
                [
                    {"role": "system", "content": "Write one sentence explaining why this case study is relevant to this specific prospect. Be specific."},
                    {"role": "user", "content": (
                        f"Prospect: {brief.business_name} ({brief.industry}) — {brief.one_liner}\n"
                        f"Problems: {', '.join(o.title for o in opportunities[:3])}\n"
                        f'Case study: "{best["title"]}" — Outcome: {best["outcome"]}\n\n'
                        'Return JSON: {"relevanceReason": "..."}'
                    )},
                ],
                temperature=0.3,
                max_tokens=120,
                fallback_fn=lambda: {"relevanceReason": reason},
            )
            if r and isinstance(r, dict):
                reason = r.get("relevanceReason", reason)
    except Exception:
        pass

    is_seed = best.get("id", "").startswith("seed-")
    return CaseStudyMatch(
        case_study_id=None if is_seed else best.get("id"),
        title=best["title"], client_industry=best.get("client_industry", ""),
        problem=best["problem"], solution=best["solution"], outcome=best["outcome"],
        relevance_score=min(100, best_score), relevance_reason=reason,
        matched_opportunity_ids=matched_opps,
    )
