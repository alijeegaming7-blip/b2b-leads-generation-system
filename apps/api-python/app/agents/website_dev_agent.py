"""
Agent 1 — Website Development Leads
Finds businesses that have NO website or a severely outdated one.
Works globally — US, Pakistan, UAE, India, etc.
"""
from __future__ import annotations
import logging
import random
from app.agents.base import BaseAgent, AgentLead
from app.scrapers import connector_manager

logger = logging.getLogger(__name__)

TARGET_INDUSTRIES = [
    "restaurant", "cafe", "beauty salon", "hair salon", "nail salon",
    "spa", "gym", "dental clinic", "dentist", "law firm", "lawyer",
    "accounting firm", "accountant", "real estate agent", "plumber",
    "electrician", "contractor", "construction", "cleaning service",
    "bakery", "flower shop", "photography studio", "tutoring center",
    "tailor", "laundry", "hardware store", "auto repair", "mechanic",
    "pharmacy", "clinic", "doctor", "optician", "physiotherapist",
    "driving school", "travel agency", "tour operator", "catering",
    "wedding hall", "event planner", "printing shop", "stationery store",
]

ISSUES_TEMPLATES = [
    "No website found — losing online customers every day",
    "Competitors have websites — this business does not",
    "No online presence beyond a Google Maps pin",
    "Only reachable by phone — missing 70% of potential customers who search online",
    "High review count but zero web presence — huge missed opportunity",
    "No online booking available despite being a service business",
    "Relying on walk-in traffic only — website would double enquiries",
]


class WebsiteDevAgent(BaseAgent):
    agent_id   = "website_dev"
    agent_name = "Website Dev Hunter"
    agent_emoji = "💻"
    search_targets = TARGET_INDUSTRIES
    primary_source = "google_maps"

    def _describe_internals(self) -> dict:
        return {
            "name": "WebVerse — Website Development Hunter",
            "description": "Finds businesses with NO website. These are the warmest leads for web development — they have proven demand (Google Maps reviews) but zero online presence.",
            "strategy": "Searches Google Maps for businesses in high-value industries. Filters only those with NO website URL listed. These businesses are losing customers every day.",
            "ideal_customer_profile": [
                "Service business with Google Maps listing",
                "Has phone number (contactable)",
                "No website URL listed",
                "Industries: restaurant, salon, clinic, law firm, pharmacy",
            ],
            "pitch_angle": "Your competitors have websites — you don't. Every day without a website costs you customers. Let's fix that this week.",
            "sources": ["Google Maps + Yellow Pages"],
        }

    async def _run_cycle(self, location: str) -> list[AgentLead]:
        industry = self._category_hint if self._category_hint else TARGET_INDUSTRIES[0]
        self.current_query = f"{industry} in {location}"
        logger.info(f"[{self.agent_id}] Searching: {self.current_query}")

        try:
            results = await connector_manager.search_with_fallback(
                query=industry,
                location=location,
                limit=20,
                priority_order=["google_maps", "yelp", "yellowpages"],
            )
        except Exception as e:
            logger.error(f"[{self.agent_id}] search failed: {e}")
            return []

        leads: list[AgentLead] = []
        for r in results:
            if not r.name:
                continue
            # Only businesses WITHOUT a website
            if r.website:
                continue

            issues = [random.choice(ISSUES_TEMPLATES)]
            if not r.phone:
                issues.append("No contact phone number listed on Google Maps")

            leads.append(AgentLead(
                business_name=r.name,
                address=r.address or "",
                phone=r.phone or "",
                email=r.email or "",
                website="",
                rating=str(r.rating) if r.rating else "",
                review_count=r.review_count or 0,
                source=r.source,
                issues_found=issues,
                raw={
                    "source_connector": r.source,
                    "social_media":     (r.raw_data or {}).get("social_media", {}),
                    "additional_emails":(r.raw_data or {}).get("additional_emails", []),
                    "city":             r.city,
                    "state":            r.state,
                    "zip_code":         r.zip_code,
                    "country":          r.country,
                    "raw_data":         r.raw_data,
                },
            ))

        logger.info(f"[{self.agent_id}] Found {len(leads)} no-website leads from {len(results)} total")
        return leads
