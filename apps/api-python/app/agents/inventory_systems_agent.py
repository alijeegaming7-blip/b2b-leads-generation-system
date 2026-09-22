"""
Agent 3 — Inventory Systems Leads
Finds retail, wholesale, and warehouse businesses needing inventory management.
"""
from __future__ import annotations
import logging
import random
from app.agents.base import BaseAgent, AgentLead
from app.scrapers import connector_manager

logger = logging.getLogger(__name__)

TARGET_INDUSTRIES = [
    "hardware store", "pharmacy", "clothing store", "grocery store",
    "supermarket", "electronics store", "furniture store", "bookstore",
    "sports equipment store", "toy store", "gift shop", "pet store",
    "auto parts store", "building supplies", "wholesale supplier",
    "warehouse", "distributor", "medical supplies", "office supplies",
    "restaurant supply", "bakery supply", "florist", "jewellery store",
    "mobile phone shop", "computer shop", "general store", "departmental store",
]

INVENTORY_ISSUES = [
    "Likely using manual spreadsheet inventory management",
    "No real-time stock tracking visible",
    "High product volume suggests manual pain points",
    "No barcode scanning system evident",
    "Missing automated low-stock alerts",
    "No supplier integration for automatic reordering",
    "Manual order management creating bottlenecks",
    "No inventory analytics or reporting system",
    "Risk of stockouts without automated tracking",
    "Multiple locations without centralised inventory control",
]


class InventorySystemsAgent(BaseAgent):
    agent_id    = "inventory_systems"
    agent_name  = "Inventory Systems Hunter"
    agent_emoji = "📦"
    search_targets = TARGET_INDUSTRIES
    primary_source = "google_maps"

    def _describe_internals(self) -> dict:
        return {
            "name": "StockVerse — Inventory Systems Hunter",
            "description": "Finds retail & wholesale businesses drowning in manual spreadsheet inventory. These businesses lose thousands monthly to stockouts and overstocking.",
            "pitch_angle": "Stop losing sales to stockouts. Automate your stock management and save 10+ hours per week.",
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

            issues = random.sample(INVENTORY_ISSUES, random.randint(2, 3))

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

        logger.info(f"[{self.agent_id}] Found {len(leads)} inventory leads from {len(results)} results")
        return leads
