from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.campaign import Campaign
from app.models.workspace import Workspace

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CreateCampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    industry: str
    location: str
    search_queries: list[str]
    max_results: int = 20
    your_service: str
    content_style: str = "balanced"
    language: str = "english"
    sources: list[str] = ["google_maps"]


class UpdateCampaignRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    search_queries: Optional[list[str]] = None
    max_results: Optional[int] = None
    your_service: Optional[str] = None
    content_style: Optional[str] = None
    language: Optional[str] = None
    sources: Optional[list[str]] = None


def _serialize(c: Campaign) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "industry": c.industry,
        "location": c.location,
        "searchQueries": json.loads(c.search_queries or "[]"),
        "sources": json.loads(c.sources or '["google_maps"]'),
        "yourService": c.your_service,
        "contentStyle": c.content_style,
        "language": c.language,
        "maxResults": c.max_results,
        "status": c.status,
        "progress": c.progress,
        "error": c.error,
        "totalLeads": c.total_leads,
        "priorityLeads": c.priority_leads,
        "highQualityLeads": c.high_quality_leads,
        "averageScore": c.average_score,
        "startedAt": c.started_at.isoformat() if c.started_at else None,
        "completedAt": c.completed_at.isoformat() if c.completed_at else None,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
        "workspaceId": c.workspace_id,
    }


async def _ensure_workspace(db: AsyncSession, workspace_id: str) -> None:
    ws = await db.get(Workspace, workspace_id)
    if not ws:
        import re, time
        slug = re.sub(r"[^a-z0-9]+", "-", workspace_id.lower()).strip("-")
        ws = Workspace(id=workspace_id, name="Default Workspace", slug=f"default-{slug[:8]}")
        db.add(ws)
        await db.flush()


@router.get("")
async def list_campaigns(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.workspace_id == current.workspace_id)
        .order_by(Campaign.created_at.desc())
    )
    return [_serialize(c) for c in result.scalars().all()]


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.workspace_id == current.workspace_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    return _serialize(c)


@router.post("", status_code=201)
async def create_campaign(
    body: CreateCampaignRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_workspace(db, current.workspace_id)
    c = Campaign(
        id=new_id(),
        name=body.name,
        description=body.description,
        industry=body.industry,
        location=body.location,
        search_queries=json.dumps(body.search_queries),
        max_results=body.max_results,
        your_service=body.your_service,
        content_style=body.content_style,
        language=body.language,
        sources=json.dumps(body.sources),
        workspace_id=current.workspace_id,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _serialize(c)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    body: UpdateCampaignRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.workspace_id == current.workspace_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")

    if body.name is not None:           c.name = body.name
    if body.description is not None:    c.description = body.description
    if body.industry is not None:       c.industry = body.industry
    if body.location is not None:       c.location = body.location
    if body.search_queries is not None: c.search_queries = json.dumps(body.search_queries)
    if body.max_results is not None:    c.max_results = body.max_results
    if body.your_service is not None:   c.your_service = body.your_service
    if body.content_style is not None:  c.content_style = body.content_style
    if body.language is not None:       c.language = body.language
    if body.sources is not None:        c.sources = json.dumps(body.sources)

    await db.commit()
    await db.refresh(c)
    return _serialize(c)


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.workspace_id == current.workspace_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    await db.delete(c)
    await db.commit()


@router.post("/{campaign_id}/run")
async def run_campaign(
    campaign_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.workspace_id == current.workspace_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    if c.status == "running":
        raise HTTPException(400, "Campaign already running")

    c.status = "running"
    c.progress = 0
    c.error = None
    c.started_at = datetime.now(timezone.utc)
    await db.commit()

    # Fire-and-forget asyncio background task — no Celery/Redis needed
    asyncio.create_task(_run_campaign_background(campaign_id, current.workspace_id))

    return {"message": "Campaign started", "campaign_id": campaign_id}


async def _run_campaign_background(campaign_id: str, workspace_id: str) -> None:
    """Run the full lead-discovery pipeline as a native asyncio task."""
    import json as _json
    from app.core.database import AsyncSessionLocal
    from app.models.lead import Lead
    from app.core.ids import new_id
    from app.agents.base import AgentLead
    from app.agents.coordinator_agent import CoordinatorAgent

    logger = __import__("logging").getLogger(__name__)
    logger.info(f"[pipeline] Starting campaign {campaign_id}")

    async with AsyncSessionLocal() as db:
        try:
            c = await db.get(Campaign, campaign_id)
            if not c:
                return

            location = c.location or "New York"
            industry = c.industry or "restaurant"
            max_results = min(c.max_results or 20, 100)
            search_queries: list[str] = _json.loads(c.search_queries or "[]") or [f"{industry} in {location}"]

            # ── Stage 1: DISCOVER via agents ──────────────────────────────
            from app.agents.website_dev_agent import WebsiteDevAgent
            from app.agents.seo_audit_agent import SeoAuditAgent
            from app.agents.inventory_systems_agent import InventorySystemsAgent
            from app.agents.analytics_dashboard_agent import AnalyticsDashboardAgent
            from app.agents.ai_assistant_agent import AiAssistantAgent

            agent_classes = [WebsiteDevAgent, SeoAuditAgent, InventorySystemsAgent,
                             AnalyticsDashboardAgent, AiAssistantAgent]

            all_raw: list[dict] = []
            seen: set[str] = set()

            for AgentClass in agent_classes:
                agent = AgentClass()
                try:
                    for q in search_queries[:3]:
                        agent.current_query = q
                        leads = await agent._run_cycle(location)
                        for lead in leads:
                            key = f"{lead.business_name.lower()}|{lead.address.lower()}"
                            if key not in seen:
                                seen.add(key)
                                all_raw.append({
                                    "name": lead.business_name, "address": lead.address,
                                    "phone": lead.phone, "email": lead.email,
                                    "website": lead.website, "rating": lead.rating,
                                    "review_count": lead.review_count,
                                    "issues_found": lead.issues_found,
                                    "source": lead.source, "agent_id": AgentClass.agent_id,
                                    "category": industry,
                                })
                except Exception as e:
                    logger.warning(f"[pipeline] {AgentClass.agent_id} error: {e}")

                # Update progress after each agent
                c_prog = await db.get(Campaign, campaign_id)
                if c_prog:
                    c_prog.progress = int((agent_classes.index(AgentClass) + 1) / len(agent_classes) * 70)
                    await db.commit()

            # ── Stage 2: SCORE + SAVE ─────────────────────────────────────
            from app.services.scoring import score_lead
            saved = 0
            for raw in all_raw[:max_results]:
                try:
                    score_data = score_lead(raw)
                    lead = Lead(
                        id=new_id(),
                        name=raw.get("name", "Unknown"),
                        address=raw.get("address", ""),
                        phone=raw.get("phone", ""),
                        email=raw.get("email", ""),
                        website=raw.get("website", ""),
                        rating=str(raw.get("rating", "")),
                        review_count=raw.get("review_count", 0),
                        category=raw.get("agent_id", industry),
                        source=raw.get("source", "google_maps"),
                        has_website=bool(raw.get("website")),
                        score=score_data.get("score", 0),
                        icp_fit_score=score_data.get("icp_fit_score", 0),
                        intent_score=score_data.get("intent_score", 0),
                        priority=score_data.get("priority", "LOW"),
                        pipeline_stage="DISCOVER",
                        campaign_id=campaign_id,
                        workspace_id=workspace_id,
                    )
                    db.add(lead)
                    saved += 1
                except Exception as e:
                    logger.warning(f"[pipeline] save lead error: {e}")

            await db.commit()

            # ── Stage 3: COMPLETE ─────────────────────────────────────────
            c_final = await db.get(Campaign, campaign_id)
            if c_final:
                c_final.status = "completed"
                c_final.progress = 100
                c_final.total_leads = saved
                c_final.priority_leads = len([r for r in all_raw[:max_results] if r.get("priority") in ("HIGH", "MEDIUM")])
                c_final.completed_at = datetime.now(timezone.utc)
                await db.commit()

            logger.info(f"[pipeline] Campaign {campaign_id} complete — {saved} leads saved")

        except Exception as exc:
            logger.error(f"[pipeline] Campaign {campaign_id} FAILED: {exc}")
            try:
                c_err = await db.get(Campaign, campaign_id)
                if c_err:
                    c_err.status = "failed"
                    c_err.error = str(exc)
                    await db.commit()
            except Exception:
                pass


@router.get("/{campaign_id}/status")
async def campaign_status(
    campaign_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.workspace_id == current.workspace_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    return {"status": c.status, "progress": c.progress, "error": c.error, "totalLeads": c.total_leads}
