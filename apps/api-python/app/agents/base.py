"""
Base Agent — shared state machine and event bus for all specialist agents.
Every agent runs its own asyncio task, emits events, and stores found leads
into the database via the coordinator.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentLead:
    """A lead discovered by a specialist agent."""
    business_name: str
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    rating: str = ""
    review_count: int = 0
    source: str = "google_maps"
    issues_found: list[str] = field(default_factory=list)
    agent_id: str = ""
    raw: dict = field(default_factory=dict)
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentEvent:
    agent_id: str
    event_type: str          # lead_found | status_change | error | heartbeat | verified
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseAgent:
    """
    Shared base for all specialist sales agents.

    Subclasses implement:
      - async _run_cycle() -> list[AgentLead]   (called repeatedly while running)
      - _describe_internals() -> dict           (for the inspector modal)
    """

    agent_id: str = "base"
    agent_name: str = "Base Agent"
    agent_emoji: str = "🤖"
    search_targets: list[str] = []   # what it searches for
    primary_source: str = "google_maps"

    def __init__(self) -> None:
        self.status: AgentStatus = AgentStatus.IDLE
        self.leads_found: int = 0
        self.leads_verified: int = 0
        self.errors: int = 0
        self.last_error: Optional[str] = None
        self.last_active: Optional[str] = None
        self.cycle_count: int = 0
        self.current_query: str = ""
        self._task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=200)
        self._stop_event = asyncio.Event()
        self._on_lead_callbacks: list[Callable[[AgentLead], Any]] = []
        self._category_hint: Optional[str] = None  # User's selected category

    def set_category_hint(self, category: str) -> None:
        """Set the user's selected category — agents will search ONLY this category"""
        self._category_hint = category
        logger.info(f"[{self.agent_id}] Category hint set: {category}")

    # ── Public control API ────────────────────────────────────────────────

    def start(self, location: str = "New York", max_leads: int = 50) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        # Reset counters for fresh run
        self.leads_found    = 0
        self.leads_verified = 0
        self.errors         = 0
        self.cycle_count    = 0
        self.current_query  = ""
        self._task = asyncio.create_task(self._agent_loop(location, max_leads))
        self._set_status(AgentStatus.RUNNING)

    def stop(self) -> None:
        self._stop_event.set()
        self._set_status(AgentStatus.STOPPED)

    def pause(self) -> None:
        self._set_status(AgentStatus.PAUSED)

    def resume(self) -> None:
        if self.status == AgentStatus.PAUSED:
            self._set_status(AgentStatus.RUNNING)

    def on_lead(self, callback: Callable[[AgentLead], Any]) -> None:
        self._on_lead_callbacks.append(callback)

    async def events(self) -> AsyncIterator[AgentEvent]:
        """Async generator — yields events as they arrive."""
        while True:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=30)
                yield event
            except asyncio.TimeoutError:
                yield AgentEvent(
                    agent_id=self.agent_id,
                    event_type="heartbeat",
                    payload={"status": self.status, "leads_found": self.leads_found},
                )

    def describe(self) -> dict:
        return {
            "id": self.agent_id,
            "name": self.agent_name,
            "emoji": self.agent_emoji,
            "status": self.status.value,
            "leads_found": self.leads_found,
            "leads_verified": self.leads_verified,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_active": self.last_active,
            "cycle_count": self.cycle_count,
            "current_query": self.current_query,
            "search_targets": self.search_targets,
            "primary_source": self.primary_source,
            "internals": self._describe_internals(),
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _set_status(self, status: AgentStatus) -> None:
        old = self.status
        self.status = status
        if old != status:
            self._emit(AgentEvent(
                agent_id=self.agent_id,
                event_type="status_change",
                payload={"old": old.value, "new": status.value},
            ))

    def _emit(self, event: AgentEvent) -> None:
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # drop if full — non-blocking

    def _emit_lead(self, lead: AgentLead) -> None:
        self.leads_found += 1
        self.last_active = datetime.now(timezone.utc).isoformat()
        lead.agent_id = self.agent_id
        self._emit(AgentEvent(
            agent_id=self.agent_id,
            event_type="lead_found",
            payload={
                "business_name": lead.business_name,
                "address": lead.address,
                "phone": lead.phone,
                "email": lead.email,
                "website": lead.website,
                "rating": lead.rating,
                "issues_found": lead.issues_found,
                "source": lead.source,
                "discovered_at": lead.discovered_at,
            },
        ))
        for cb in self._on_lead_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(lead))
                else:
                    cb(lead)
            except Exception:
                pass

    # ── Main loop ─────────────────────────────────────────────────────────

    async def _agent_loop(self, location: str, max_leads: int) -> None:
        logger.info(f"[{self.agent_id}] Agent loop starting. location={location}")
        try:
            while not self._stop_event.is_set() and self.leads_found < max_leads:
                if self.status == AgentStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue

                self.cycle_count += 1
                try:
                    leads = await self._run_cycle(location)
                    for lead in leads:
                        if self._stop_event.is_set():
                            break
                        self._emit_lead(lead)
                        await asyncio.sleep(0.3)   # small delay between lead events
                except Exception as exc:
                    self.errors += 1
                    self.last_error = str(exc)
                    logger.warning(f"[{self.agent_id}] cycle error: {exc}")
                    self._emit(AgentEvent(
                        agent_id=self.agent_id,
                        event_type="error",
                        payload={"message": str(exc), "cycle": self.cycle_count},
                    ))
                    await asyncio.sleep(5)

                # Wait between cycles so we don't hammer scraper
                await asyncio.sleep(8)

        except asyncio.CancelledError:
            pass
        finally:
            self._set_status(AgentStatus.STOPPED)
            logger.info(f"[{self.agent_id}] Agent loop ended. leads={self.leads_found}")

    # ── Must be overridden ────────────────────────────────────────────────

    async def _run_cycle(self, location: str) -> list[AgentLead]:
        raise NotImplementedError

    def _describe_internals(self) -> dict:
        return {}
