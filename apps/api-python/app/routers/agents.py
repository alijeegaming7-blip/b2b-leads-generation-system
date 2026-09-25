"""
Agents Router
=============
REST + SSE endpoints for the multi-agent sales intelligence system.

Endpoints:
  GET  /agents                    — list all agents + their state
  GET  /agents/{id}               — single agent detail + internals
  POST /agents/start              — start all agents (or specific one)
  POST /agents/{id}/start         — start a single agent
  POST /agents/{id}/stop          — stop a single agent
  POST /agents/{id}/pause         — pause a single agent
  POST /agents/{id}/resume        — resume a single agent
  GET  /agents/stream             — SSE stream of all agent events
  GET  /agents/leads              — all leads collected by agents this session
  GET  /agents/stats              — aggregate stats across all agents
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.security import get_current_user, CurrentUser, decode_token
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])

# ── Singleton agent registry (lives for the server lifetime) ─────────────────

from app.agents.website_dev_agent import WebsiteDevAgent
from app.agents.seo_audit_agent import SeoAuditAgent
from app.agents.inventory_systems_agent import InventorySystemsAgent
from app.agents.analytics_dashboard_agent import AnalyticsDashboardAgent
from app.agents.ai_assistant_agent import AiAssistantAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.base import AgentEvent

_coordinator = CoordinatorAgent()
_specialists: dict[str, WebsiteDevAgent | SeoAuditAgent | InventorySystemsAgent | AnalyticsDashboardAgent | AiAssistantAgent] = {
    "website_dev":           WebsiteDevAgent(),
    "seo_audit":             SeoAuditAgent(),
    "inventory_systems":     InventorySystemsAgent(),
    "analytics_dashboards":  AnalyticsDashboardAgent(),
    "ai_assistants":         AiAssistantAgent(),
}

# Wire specialists → coordinator using a properly-closed callback
def _make_lead_callback(agent_id: str):
    """Return a callback that forwards leads to the coordinator with the correct agent_id."""
    async def _cb(lead):
        await _coordinator.receive_lead(lead, agent_id)
    return _cb

for _aid, _agent in _specialists.items():
    _agent.on_lead(_make_lead_callback(_aid))

# Shared SSE broadcast queue (coordinator events merged with specialist events)
_broadcast_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1000)

# In-memory lead log for this session
_session_leads: list[dict] = []


def _event_to_sse(event: AgentEvent) -> str:
    data = json.dumps({
        "agent_id": event.agent_id,
        "event_type": event.event_type,
        "payload": event.payload,
        "timestamp": event.timestamp,
    })
    return f"data: {data}\n\n"


async def _coordinator_event_pump() -> None:
    """Background task: pump coordinator events into broadcast queue."""
    q = _coordinator.events()
    while True:
        try:
            event = await asyncio.wait_for(q.get(), timeout=30)
            sse = _event_to_sse(event)
            try:
                _broadcast_queue.put_nowait(sse)
            except asyncio.QueueFull:
                pass

            # Cache verified leads in session memory
            if event.event_type == "verified":
                _session_leads.append({**event.payload, "timestamp": event.timestamp})
                if len(_session_leads) > 500:
                    _session_leads.pop(0)

        except asyncio.TimeoutError:
            # Heartbeat every 30s so SSE connections stay alive
            hb = json.dumps({
                "agent_id": "coordinator",
                "event_type": "heartbeat",
                "payload": {
                    "total_received": _coordinator.total_received,
                    "total_verified": _coordinator.total_verified,
                    "total_saved": _coordinator.total_saved,
                    "all_statuses": {aid: a.status.value for aid, a in _specialists.items()},
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            try:
                _broadcast_queue.put_nowait(f"data: {hb}\n\n")
            except asyncio.QueueFull:
                pass
        except Exception as exc:
            logger.error(f"[coordinator_pump] {exc}")
            await asyncio.sleep(1)


async def _specialist_event_pump(agent_id: str) -> None:
    """Background task: pump one specialist's events into broadcast queue."""
    agent = _specialists[agent_id]
    async for event in agent.events():
        sse = _event_to_sse(event)
        try:
            _broadcast_queue.put_nowait(sse)
        except asyncio.QueueFull:
            pass


# Start pumps when the module is first imported (FastAPI lifespan hooks this)
_pumps_started = False


def ensure_pumps_running() -> None:
    global _pumps_started
    if _pumps_started:
        return
    _pumps_started = True
    asyncio.create_task(_coordinator_event_pump())
    for aid in _specialists:
        asyncio.create_task(_specialist_event_pump(aid))
    _coordinator.start()
    logger.info("[agents] Event pumps started")


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.get("")
async def list_agents(current: CurrentUser = Depends(get_current_user)):
    ensure_pumps_running()
    agents_out = [a.describe() for a in _specialists.values()]
    return {
        "coordinator": _coordinator.describe(),
        "agents": agents_out,
        "session_leads_count": len(_session_leads),
    }


@router.get("/stats")
async def agent_stats(current: CurrentUser = Depends(get_current_user)):
    total_leads = sum(a.leads_found for a in _specialists.values())
    total_errors = sum(a.errors for a in _specialists.values())
    return {
        "total_leads_found": total_leads,
        "total_verified": _coordinator.total_verified,
        "total_saved": _coordinator.total_saved,
        "total_duplicates": _coordinator.total_duplicates,
        "total_errors": total_errors,
        "agents_running": sum(1 for a in _specialists.values() if a.status.value == "running"),
        "agents_stopped": sum(1 for a in _specialists.values() if a.status.value == "stopped"),
        "agents_error": sum(1 for a in _specialists.values() if a.status.value == "error"),
        "per_agent": {
            aid: {
                "leads_found": a.leads_found,
                "errors": a.errors,
                "status": a.status.value,
                "cycle_count": a.cycle_count,
            }
            for aid, a in _specialists.items()
        },
    }


@router.get("/leads")
async def session_leads(
    limit: int = Query(100, ge=1, le=500),
    agent_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
):
    leads = _session_leads[-limit:]
    if agent_id:
        leads = [l for l in leads if l.get("from_agent") == agent_id]
    return {"leads": list(reversed(leads)), "total": len(_session_leads)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str, current: CurrentUser = Depends(get_current_user)):
    if agent_id == "coordinator":
        return _coordinator.describe()
    agent = _specialists.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return agent.describe()


class StartRequest(BaseModel):
    location: str = "New York"
    country: Optional[str] = None          # e.g. "United States"
    city: Optional[str] = None             # e.g. "New York"
    category: Optional[str] = None         # e.g. "restaurant", "salon"
    max_leads: int = 100
    workspace_id: Optional[str] = None
    campaign_id: Optional[str] = None
    agent_ids: Optional[list[str]] = None  # None = start all

    @property
    def resolved_location(self) -> str:
        """Build location string from city+country if provided."""
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        if self.city:
            return self.city
        return self.location


@router.post("/start")
async def start_agents(
    body: StartRequest,
    current: CurrentUser = Depends(get_current_user),
):
    ensure_pumps_running()

    loc = body.resolved_location
    ws_id = body.workspace_id or current.workspace_id
    campaign_id = body.campaign_id

    # ALWAYS configure coordinator with workspace — create auto campaign row if needed
    if not campaign_id:
        from app.core.ids import new_id
        from app.core.database import AsyncSessionLocal
        from app.models.campaign import Campaign
        campaign_id = new_id()
        try:
            async with AsyncSessionLocal() as _db:
                _db.add(Campaign(
                    id=campaign_id,
                    name=f"Dashboard — {loc}",
                    industry=body.category or "general",
                    location=loc,
                    your_service="digital services",
                    workspace_id=ws_id,
                    status="active",
                ))
                await _db.commit()
            logger.info(f"[agents/start] Auto-created campaign {campaign_id}")
        except Exception as _e:
            logger.warning(f"[agents/start] Campaign create failed ({_e}), continuing anyway")

    _coordinator.configure(ws_id, campaign_id)

    # In demo mode: seed 30 pre-loaded leads AND cap agents at 30 leads total
    from app.core.demo import is_demo
    if is_demo():
        body.max_leads = 30
        logger.info("[agents/start] Demo mode — capping at 30 leads")
        # Seed demo leads in background
        try:
            from app.core.demo_seeder import seed_demo_leads
            asyncio.create_task(seed_demo_leads(ws_id, campaign_id))
        except Exception as _se:
            logger.warning(f"[agents/start] Demo seed failed: {_se}")
    logger.info(f"[agents/start] Coordinator configured: workspace={ws_id}, campaign={campaign_id}")

    targets = body.agent_ids or list(_specialists.keys())
    started = []
    for aid in targets:
        agent = _specialists.get(aid)
        if agent:
            # Always stop first to allow re-running
            agent.stop()

            # Set category hint BEFORE start
            if body.category and hasattr(agent, "set_category_hint"):
                agent.set_category_hint(body.category)
                logger.info(f"[agents/start] Set category hint for {aid}: {body.category}")

            # Small pause to ensure stop is processed
            await asyncio.sleep(0.2)
            agent.start(location=loc, max_leads=body.max_leads)
            started.append(aid)

    return {
        "started": started,
        "location": loc,
        "category": body.category,
        "max_leads": body.max_leads,
        "coordinator_configured": True,
        "workspace_id": ws_id,
        "campaign_id": campaign_id,
    }


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    body: StartRequest,
    current: CurrentUser = Depends(get_current_user),
):
    ensure_pumps_running()
    agent = _specialists.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    agent.start(location=body.location, max_leads=body.max_leads)
    return {"started": agent_id, "status": agent.status.value}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, current: CurrentUser = Depends(get_current_user)):
    agent = _specialists.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    agent.stop()
    return {"stopped": agent_id, "status": agent.status.value}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: str, current: CurrentUser = Depends(get_current_user)):
    agent = _specialists.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    agent.pause()
    return {"paused": agent_id, "status": agent.status.value}


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: str, current: CurrentUser = Depends(get_current_user)):
    agent = _specialists.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    agent.resume()
    return {"resumed": agent_id, "status": agent.status.value}


@router.post("/stop-all")
async def stop_all(current: CurrentUser = Depends(get_current_user)):
    for agent in _specialists.values():
        agent.stop()
    return {"stopped": list(_specialists.keys())}


# ── SSE Stream endpoint ───────────────────────────────────────────────────────

@router.get("/stream")
async def agent_stream(
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events stream — accepts JWT as query param because
    browser EventSource API cannot set custom headers.
    """
    # Auth: accept ?token= query param OR Authorization header
    raw_token = token
    if not raw_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:]
    if not raw_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(raw_token)
        user_id = payload.get("sub", "")
        result = await db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            raise Exception("User not found")
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")

    ensure_pumps_running()

    async def event_generator():
        # Send initial snapshot so frontend can render current state immediately
        snapshot = json.dumps({
            "agent_id": "system",
            "event_type": "snapshot",
            "payload": {
                "coordinator": _coordinator.describe(),
                "agents": [a.describe() for a in _specialists.values()],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        yield f"data: {snapshot}\n\n"

        # Tap into broadcast queue — each SSE client gets its own local queue
        local_q: asyncio.Queue[str] = asyncio.Queue(maxsize=500)

        async def _drain():
            """Tap broadcast into local queue."""
            while True:
                msg = await _broadcast_queue.get()
                try:
                    local_q.put_nowait(msg)
                except asyncio.QueueFull:
                    pass

        drain_task = asyncio.create_task(_drain())
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(local_q.get(), timeout=30)
                    yield msg
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'agent_id': 'system', 'event_type': 'ping', 'payload': {}, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            drain_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── WhatsApp helper endpoints (used by WhatsApp page) ─────────────────────────

@router.get("/whatsapp/leads")
async def whatsapp_leads(
    limit: int = Query(200, ge=1, le=500),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all session leads that have a phone number, enriched with wa.me links."""
    import re
    leads_out = []
    for lead in list(reversed(_session_leads))[:limit]:
        phone = lead.get("phone", "") or ""
        digits = re.sub(r"\D", "", phone)
        if not digits:
            continue
        wa_url = f"https://wa.me/{digits}"
        name = lead.get("business_name", "there")
        template_msg = (
            f"Hi {name}! I noticed your business and wanted to reach out about "
            f"how we can help you grow online. Would you be open to a quick chat? 😊"
        )
        leads_out.append({**lead, "waUrl": wa_url, "templateMessage": template_msg, "digits": digits})
    return {"leads": leads_out, "total": len(leads_out)}
