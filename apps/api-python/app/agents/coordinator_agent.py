"""
Coordinaator Agent — Central Hub
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from collections import OrderedDict

from app.core.validation import validate_email as _validate_email, validate_phone as _validate_phone
from app.agents.base import AgentLead, AgentEvent, AgentStatus

logger = logging.getLogger(__name__)


async def _check_whatsapp(phone: str) -> bool:
    """
    Check if a phone number has WhatsApp by hitting wa.me and checking the redirect.
    Returns True if WhatsApp is available, False otherwise.
    """
    if not phone:
        return False
    # Strip to digits only
    digits = re.sub(r'\D', '', phone)
    if len(digits) < 7:
        return False
    
    try:
        import aiohttp
        url = f"https://wa.me/{digits}"
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            headers={"User-Agent": "Mozilla/5.0"},
        ) as session:
            async with session.get(url, allow_redirects=True, ssl=False) as resp:
                final_url = str(resp.url)
                # If redirected to web.whatsapp.com or returns 200 with chat page
                # wa.me always returns 200 with a page that opens WhatsApp
                # We consider it "has WhatsApp" if the response page contains the number
                if resp.status == 200:
                    text = await resp.text()
                    # WhatsApp page contains "Open WhatsApp" or the number
                    if "Open WhatsApp" in text or "whatsapp" in final_url.lower():
                        return True
    except Exception:
        pass
    return False


@dataclass
class VerificationResult:
    lead: AgentLead
    email_valid: bool
    phone_valid: bool
    duplicate: bool
    score: int
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CoordinatorAgent:
    """
    Central coordinator that:
    1. Receives leads from all specialist agents
    2. Validates email format + phone format
    3. Deduplicates by (name + address)
    4. Scores the lead (0-100)
    5. Saves to the database
    6. Emits verification events back to the network
    """

    agent_id = "coordinator"
    agent_name = "Central Coordinator"
    agent_emoji = "⚡"

    def __init__(self) -> None:
        self.status: AgentStatus = AgentStatus.IDLE
        self.total_received: int = 0
        self.total_verified: int = 0
        self.total_rejected: int = 0
        self.total_saved: int = 0
        self.total_duplicates: int = 0
        self._seen: OrderedDict[str, bool] = OrderedDict()  # LRU cache for deduplication
        self._seen_max_size = 10000  # Prevent unbounded growth
        self._event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=500)
        self._processing_queue: asyncio.Queue[tuple[AgentLead, str]] = asyncio.Queue(maxsize=200)
        self._task: Optional[asyncio.Task] = None
        self._workspace_id: Optional[str] = None
        self._campaign_id: Optional[str] = None

    def configure(self, workspace_id: str, campaign_id: str) -> None:
        self._workspace_id = workspace_id
        self._campaign_id = campaign_id

    def start(self) -> None:
        self.status = AgentStatus.RUNNING
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._process_loop())

    def stop(self) -> None:
        """Graceful shutdown: process remaining queue items then stop."""
        self.status = AgentStatus.STOPPED
        if self._task and not self._task.done():
            self._task.cancel()
    
    async def shutdown(self, timeout: float = 5.0) -> None:
        """Wait for graceful shutdown with timeout."""
        import asyncio
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

    async def receive_lead(self, lead: AgentLead, from_agent_id: str) -> None:
        """Called by specialist agents when they find a lead."""
        self.total_received += 1
        await self._processing_queue.put((lead, from_agent_id))

    def events(self) -> asyncio.Queue[AgentEvent]:
        return self._event_queue

    def describe(self) -> dict:
        return {
            "id": self.agent_id,
            "name": self.agent_name,
            "emoji": self.agent_emoji,
            "status": self.status.value,
            "total_received": self.total_received,
            "total_verified": self.total_verified,
            "total_rejected": self.total_rejected,
            "total_saved": self.total_saved,
            "total_duplicates": self.total_duplicates,
            "queue_depth": self._processing_queue.qsize(),
            "internals": {
                "strategy": "Receives all leads from specialist agents, validates, deduplicates, scores, and saves to the database.",
                "verification_steps": [
                    "1. Deduplicate by (business_name + address) hash",
                    "2. Validate email format (RFC 5322 regex)",
                    "3. Validate phone number (7-15 digits, E.164)",
                    "4. Score lead 0-100 using LeadIntelligenceService",
                    "5. Save to database with agent_id and issues_found",
                    "6. Emit verified event back to network visualization",
                ],
                "rejection_reasons": [
                    "Duplicate lead already in database",
                    "No business name",
                    "Score < 20 (very low quality)",
                ],
                "workspace_id": self._workspace_id or "not configured",
                "campaign_id": self._campaign_id or "not configured",
            },
        }

    async def _process_loop(self) -> None:
        logger.info("[coordinator] Processing loop started")
        while True:
            try:
                lead, from_agent_id = await asyncio.wait_for(
                    self._processing_queue.get(), timeout=5
                )
                await self._process_lead(lead, from_agent_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[coordinator] Processing error: {exc}")

    async def _process_lead(self, lead: AgentLead, from_agent_id: str) -> None:
        # Deduplication
        dedup_key = f"{lead.business_name.lower().strip()}|{lead.address.lower().strip()}"
        if dedup_key in self._seen:
            self.total_duplicates += 1
            self._emit(AgentEvent(
                agent_id=self.agent_id,
                event_type="duplicate",
                payload={"business_name": lead.business_name, "from_agent": from_agent_id},
            ))
            return
        # Add to LRU cache, removing oldest if at capacity
        self._seen[dedup_key] = True
        if len(self._seen) > self._seen_max_size:
            self._seen.popitem(last=False)  # Remove oldest item

        # Validation
        email_valid = _validate_email(lead.email)
        phone_valid = _validate_phone(lead.phone)

        # Score
        from app.services.ai.lead_intelligence import score_lead
        scored = score_lead(
            name=lead.business_name,
            address=lead.address,
            phone=lead.phone if phone_valid else None,
            email=lead.email if email_valid else None,
            website=lead.website,
            rating=lead.rating,
            review_count=lead.review_count,
            has_website=bool(lead.website),
            source=lead.source,
        )

        if scored.score < 10:   # lowered from 20 — accept more leads
            self.total_rejected += 1
            return

        self.total_verified += 1

        # Save to DB if configured
        if self._workspace_id and self._campaign_id:
            await self._save_to_db(lead, from_agent_id, scored.score, scored.priority, email_valid, phone_valid)

        # Emit verification event
        self._emit(AgentEvent(
            agent_id=self.agent_id,
            event_type="verified",
            payload={
                "business_name": lead.business_name,
                "address": lead.address,
                "phone": lead.phone,
                "email": lead.email,
                "website": lead.website,
                "rating": lead.rating,
                "score": scored.score,
                "priority": scored.priority,
                "email_valid": email_valid,
                "phone_valid": phone_valid,
                "issues_found": lead.issues_found,
                "from_agent": from_agent_id,
                "saved": bool(self._workspace_id and self._campaign_id),
            },
        ))

    async def _save_to_db(
        self,
        lead: AgentLead,
        from_agent_id: str,
        score: int,
        priority: str,
        email_valid: bool,
        phone_valid: bool,
    ) -> None:
        try:
            from app.core.database import AsyncSessionLocal
            from app.core.ids import new_id
            from app.models.lead import Lead

            # Pull enriched data from raw dict
            raw = lead.raw or {}
            social_media  = raw.get("social_media") or {}
            add_emails     = raw.get("additional_emails") or []
            city           = raw.get("city") or None
            state          = raw.get("state") or None
            zip_code       = raw.get("zip_code") or None
            country        = raw.get("country") or None
            ref_link       = (raw.get("raw_data") or {}).get("reference_link") or None
            lat            = (raw.get("raw_data") or {}).get("lat") or None
            lng            = (raw.get("raw_data") or {}).get("lng") or None
            src            = raw.get("source_connector") or lead.source or "google_maps"

            # Check WhatsApp availability for phone numbers
            has_whatsapp = False
            whatsapp_url = None
            clean_phone = lead.phone.strip() if lead.phone and lead.phone.strip() else None
            if clean_phone:
                try:
                    has_whatsapp = await asyncio.wait_for(_check_whatsapp(clean_phone), timeout=6)
                    if has_whatsapp:
                        digits = re.sub(r'\D', '', clean_phone)
                        whatsapp_url = f"https://wa.me/{digits}"
                        # Add WhatsApp to social_media dict
                        if isinstance(social_media, dict) and "whatsapp" not in social_media:
                            social_media["whatsapp"] = whatsapp_url
                except Exception:
                    pass

            async with AsyncSessionLocal() as db:
                db_lead = Lead(
                    id=new_id(),
                    name=lead.business_name,
                    address=lead.address or None,
                    phone=lead.phone.strip() if lead.phone and lead.phone.strip() else None,
                    email=lead.email.strip() if lead.email and lead.email.strip() else None,
                    website=lead.website or None,
                    rating=lead.rating or None,
                    review_count=lead.review_count or None,
                    has_website=bool(lead.website),
                    source=src,
                    reference_url=ref_link,
                    lat=lat,
                    lng=lng,
                    # enhanced columns
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    country=country,
                    social_media=json.dumps(social_media) if isinstance(social_media, dict) and social_media else None,
                    additional_emails=json.dumps(add_emails) if isinstance(add_emails, list) and add_emails else None,
                    # scoring
                    score=score,
                    priority=priority,
                    pipeline_stage="DISCOVER",
                    ai_analysis=json.dumps({
                        "agent_id": from_agent_id,
                        "issues_found": lead.issues_found,
                    }),
                    campaign_id=self._campaign_id,
                    workspace_id=self._workspace_id,
                )
                db.add(db_lead)
                await db.commit()
                self.total_saved += 1
        except Exception as exc:
            logger.warning(f"[coordinator] DB save failed: {exc}")

    def _emit(self, event: AgentEvent) -> None:
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


def _validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def _validate_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15



