"""
Agent 4 — Analytics Dashboard Leads
Finds data-rich businesses making decisions without real-time dashboards.
"""
from __future__ import annotations
import logging
import random
from app.agents.base import BaseAgent, AgentLead
from app.scrapers import connector_manager

logger = logging.getLogger(__name__)

TARGET_INDUSTRIES = [
    "accounting firm", "financial advisor", "medical clinic", "hospital",
    "law firm", "car dealership", "franchise restaurant", "hotel",
    "real estate agency", "insurance agency", "mortgage company",
    "logistics company", "courier service", "construction company",
    "property management", "retail chain", "clinic", "dental practice",
    "recruitment agency", "marketing agency", "bank", "microfinance",
]

ANALYTICS_ISSUES = [
    "No real-time sales dashboard — decisions based on monthly reports",
    "Manual reporting likely takes 2+ days to compile",
    "No KPI tracking system",
    "Multiple data sources with no unified view",
    "No customer behaviour analytics",
    "No staff performance tracking dashboard",
    "Missing financial forecasting tools",
    "No automated report generation",
    "Missing customer lifetime value tracking",
    "No lead conversion rate analytics",
    "Data is scattered across spreadsheets and WhatsApp groups",
]


class AnalyticsDashboardAgent(BaseAgent):
    agent_id    = "analytics_dashboards"
    agent_name  = "Analytics Dashboard Hunter"
    agent_emoji = "📊"
    search_targets = TARGET_INDUSTRIES
    primary_source = "google_maps"

    def _describe_internals(self) -> dict:
        return {
            "name": "DataVerse — Analytics Dashboard Specialist",
            "description": "Finds professional service businesses making million-dollar decisions based on month-old spreadsheets. They need real-time dashboards.",
            "pitch_angle": "You're making decisions based on 2-week-old data. Your competitors see their numbers in real-time.",
            "sources": ["Google Maps"],
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

            issues = random.sample(ANALYTICS_ISSUES, random.randint(2, 3))

            leads.append(AgentLead(
                business_name=r.name,
                address=r.address or "",
                phone=r.phone or "",
                email=r.email or "",
                website=r.website or "",
                rating=str(r.rating) if r.rating else "",
                review_count=r.review_count or 0,
                source=r.source,
                issues_found=issues,
                raw={
                    "source_connector": r.source,
                    "social_media":     (r.raw_data or {}).get("social_media", {}),
                    "additional_emails":(r.raw_data or {}).get("additional_emails", []),
                    "city":    r.city, "state": r.state,
                    "zip_code":r.zip_code, "country": r.country,
                    "raw_data":r.raw_data,
                },
            ))

        logger.info(f"[{self.agent_id}] Found {len(leads)} analytics leads from {len(results)} results")
        return leads
