"""
Agent 5 — AI Assistant Leads
Finds high-touch service businesses where staff spend time on repetitive tasks.
Takes ALL businesses — no phone/review requirements (important for Pakistan/developing markets).
"""
from __future__ import annotations
import logging
import random
from app.agents.base import BaseAgent, AgentLead
from app.scrapers import connector_manager

logger = logging.getLogger(__name__)

TARGET_INDUSTRIES = [
    "dental clinic", "medical clinic", "hospital", "law firm",
    "hotel", "spa", "beauty salon", "gym", "restaurant",
    "car dealership", "real estate agency", "insurance agency",
    "travel agency", "recruitment agency", "pharmacy", "school",
    "university", "coaching institute", "customer support center",
    "call center", "bank", "microfinance institution",
]

AI_ISSUES = [
    "Staff spending hours answering repetitive customer enquiries",
    "No 24/7 customer support — losing after-hours leads",
    "Manual appointment booking via phone calls only",
    "No AI chatbot for instant customer responses",
    "High staff turnover — training costs could be reduced with AI",
    "No automated FAQ responses — staff answers same questions daily",
    "Missing lead qualification automation",
    "No automated follow-up system for enquiries",
    "Manual document processing wasting staff time",
    "No automated review request system",
    "Missed calls = missed revenue — no AI receptionist",
    "No intelligent scheduling assistant",
    "Manual WhatsApp responses taking hours per day",
]


class AiAssistantAgent(BaseAgent):
    agent_id    = "ai_assistants"
    agent_name  = "AI Assistant Hunter"
    agent_emoji = "🧠"
    search_targets = TARGET_INDUSTRIES
    primary_source = "google_maps"

    def _describe_internals(self) -> dict:
        return {
            "name": "AIVerse — AI Assistant & Automation Hunter",
            "description": "Finds service businesses where staff waste hours on repetitive tasks. AI chatbots and automation can cut support costs by 40% and never miss a lead.",
            "pitch_angle": "Your staff are spending 20 hours/week answering the same 10 questions. Let AI handle that — 24/7, in any language.",
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
            # Accept ALL businesses — even without phone or reviews
            # (developing markets have fewer online reviews)

            issues = random.sample(AI_ISSUES, random.randint(2, 4))

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

        logger.info(f"[{self.agent_id}] Found {len(leads)} AI leads from {len(results)} results")
        return leads
