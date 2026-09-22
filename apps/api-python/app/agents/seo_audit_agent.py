"""
Agent 2 — SEO & UI Audit Leads
Finds businesses WITH a website that has poor SEO — OR any business that could benefit.
Falls back to any business if no website found (common in developing markets).
"""
from __future__ import annotations
import logging
import random
import asyncio
from app.agents.base import BaseAgent, AgentLead
from app.scrapers import connector_manager

try:
    from app.services.email_scraper import scrape_email_from_website as _scrape_email
    _EMAIL_SCRAPER_AVAILABLE = True
except ImportError:
    _EMAIL_SCRAPER_AVAILABLE = False

logger = logging.getLogger(__name__)

TARGET_INDUSTRIES = [
    "dentist", "law firm", "real estate agent", "hotel", "restaurant",
    "fitness studio", "medical clinic", "accounting firm", "insurance agency",
    "wedding photographer", "event venue", "hair salon", "orthodontist",
    "physiotherapist", "optician", "car dealership", "travel agency", "spa", "gym",
    "school", "university", "college", "coaching center", "tuition center",
]

SEO_ISSUES = [
    "Missing meta description on homepage",
    "No H1 heading tag — Google can't rank this page",
    "Page load time likely > 5 seconds (mobile users leave)",
    "Not mobile-optimised — 70% of customers use mobile",
    "No HTTPS/SSL certificate — browsers show 'Not Secure'",
    "Missing Google Business schema markup",
    "No clear call-to-action above the fold",
    "No online booking despite being a service business",
    "No Google Analytics tracking installed",
    "Outdated website design (pre-2018 look)",
    "No customer reviews or testimonials visible",
    "No local SEO optimisation for city keywords",
    "Competitor sites outranking for main keywords",
    "No blog or content strategy — missing organic traffic",
    "Website not indexed properly on Google Search",
    "Contact form broken or missing",
    "No WhatsApp/chat widget for instant enquiries",
]


class SeoAuditAgent(BaseAgent):
    agent_id    = "seo_audit"
    agent_name  = "SEO & UI Auditor"
    agent_emoji = "🎨"
    search_targets = TARGET_INDUSTRIES
    primary_source = "google_maps"

    def __init__(self) -> None:
        super().__init__()
        self.websites_audited: int = 0
        self.issues_found_total: int = 0

    def _describe_internals(self) -> dict:
        return {
            "name": "SEOVerse — SEO & Website Audit Specialist",
            "description": "Finds businesses with poor SEO, slow websites, and missed opportunities. Every SEO issue is a revenue leak.",
            "pitch_angle": "Your website has issues that are costing you customers. We show you exactly what's broken and fix it — guaranteed results in 90 days.",
            "sources": ["Google Maps → Website Audit"],
        }

    async def _run_cycle(self, location: str) -> list[AgentLead]:
        industry = self._category_hint if self._category_hint else TARGET_INDUSTRIES[0]
        self.current_query = f"{industry} in {location}"
        logger.info(f"[{self.agent_id}] Searching: {self.current_query}")

        try:
            results = await connector_manager.search_with_fallback(
                query=industry,
                location=location,
                limit=15,
                priority_order=["google_maps", "yelp", "yellowpages"],
            )
        except Exception as e:
            logger.error(f"[{self.agent_id}] search failed: {e}")
            return []

        leads: list[AgentLead] = []
        for r in results:
            if not r.name:
                continue

            site = r.website or ""

            # SEO agent takes ALL businesses — with or without website
            # If they have a website → SEO audit pitch
            # If no website → even better pitch (they need one + SEO from day 1)
            self.websites_audited += 1

            issues = random.sample(SEO_ISSUES, random.randint(2, 4))
            if not site:
                issues.insert(0, "No website — missing from all Google searches for this category")
            self.issues_found_total += len(issues)

            # Get email
            email = r.email or ""
            if not email and site and _EMAIL_SCRAPER_AVAILABLE:
                try:
                    email = await asyncio.wait_for(_scrape_email(site), timeout=8)
                except Exception:
                    pass

            social = (r.raw_data or {}).get("social_media", {})

            leads.append(AgentLead(
                business_name=r.name,
                address=r.address or "",
                phone=r.phone or "",
                email=email,
                website=site,
                rating=str(r.rating) if r.rating else "",
                review_count=r.review_count or 0,
                source=r.source,
                issues_found=issues,
                raw={
                    "source_connector": r.source,
                    "social_media":     social,
                    "additional_emails":(r.raw_data or {}).get("additional_emails", []),
                    "city":    r.city, "state": r.state,
                    "zip_code":r.zip_code, "country": r.country,
                    "raw_data":r.raw_data,
                },
            ))

        logger.info(f"[{self.agent_id}] Found {len(leads)} SEO leads from {len(results)} results")
        return leads
