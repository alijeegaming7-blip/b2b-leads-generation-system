from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.email import EmailLog
from app.models.crm import Deal

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def overview(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wid = current.workspace_id

    total_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.workspace_id == wid)) or 0
    active_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.workspace_id == wid, Campaign.status.in_(["running", "completed"])
        )
    ) or 0
    email_sent = await db.scalar(
        select(func.count(Lead.id)).where(Lead.workspace_id == wid, Lead.email_sent == True)
    ) or 0
    deals_won = await db.scalar(
        select(func.count(Deal.id)).where(Deal.workspace_id == wid, Deal.stage == "won")
    ) or 0
    deals_total = await db.scalar(
        select(func.count(Deal.id)).where(Deal.workspace_id == wid)
    ) or 0
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Deal.value), 0.0)).where(Deal.workspace_id == wid, Deal.stage == "won")
    ) or 0.0

    replied = await db.scalar(
        select(func.count(Lead.id)).where(Lead.workspace_id == wid, Lead.crm_status == "replied")
    ) or 0
    won = await db.scalar(
        select(func.count(Lead.id)).where(Lead.workspace_id == wid, Lead.crm_status == "won")
    ) or 0

    crm_result = await db.execute(
        select(Lead.crm_status, func.count(Lead.id))
        .where(Lead.workspace_id == wid)
        .group_by(Lead.crm_status)
    )
    crm_pipeline = [{"status": row[0], "count": row[1]} for row in crm_result.all()]

    return {
        "totalLeads": total_leads,
        "activeCampaigns": active_campaigns,
        "emailSent": email_sent,
        "dealsWon": deals_won,
        "totalRevenue": float(total_revenue),
        "conversionRate": f"{round(won / max(total_leads, 1) * 100, 1)}%",
        "replyRate": f"{round(replied / max(total_leads, 1) * 100, 1)}%",
        "dealWinRate": f"{round(deals_won / max(deals_total, 1) * 100, 1)}%",
        "crmPipeline": crm_pipeline,
    }


@router.get("/funnel")
async def conversion_funnel(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wid = current.workspace_id

    async def count(extra=None):
        stmt = select(func.count(Lead.id)).where(Lead.workspace_id == wid)
        if extra is not None:
            stmt = stmt.where(extra)
        return await db.scalar(stmt) or 0

    total     = await count()
    contacted = await count(Lead.crm_status.in_(["contacted", "replied", "meeting", "proposal", "won", "lost"]))
    replied   = await count(Lead.crm_status.in_(["replied", "meeting", "proposal", "won"]))
    meeting   = await count(Lead.crm_status.in_(["meeting", "proposal", "won"]))
    proposal  = await count(Lead.crm_status.in_(["proposal", "won"]))
    won       = await count(Lead.crm_status == "won")

    return [
        {"stage": "Discovered",  "count": total,     "pct": 100},
        {"stage": "Contacted",   "count": contacted, "pct": round(contacted / max(total, 1) * 100)},
        {"stage": "Replied",     "count": replied,   "pct": round(replied / max(total, 1) * 100)},
        {"stage": "Meeting",     "count": meeting,   "pct": round(meeting / max(total, 1) * 100)},
        {"stage": "Proposal",    "count": proposal,  "pct": round(proposal / max(total, 1) * 100)},
        {"stage": "Won",         "count": won,       "pct": round(won / max(total, 1) * 100)},
    ]


@router.get("/pipeline-stages")
async def pipeline_stages(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead.pipeline_stage, func.count(Lead.id))
        .where(Lead.workspace_id == current.workspace_id)
        .group_by(Lead.pipeline_stage)
    )
    return [{"stage": row[0], "count": row[1]} for row in result.all()]


@router.get("/by-industry")
async def by_industry(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead.category, func.count(Lead.id), func.avg(Lead.score))
        .where(Lead.workspace_id == current.workspace_id, Lead.category.isnot(None))
        .group_by(Lead.category)
        .order_by(func.count(Lead.id).desc())
    )
    return [{"category": row[0], "count": row[1], "avgScore": round(row[2] or 0)} for row in result.all()]


@router.get("/by-source")
async def by_source(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(Lead.workspace_id == current.workspace_id)
        .group_by(Lead.source)
    )
    return [{"source": row[0], "count": row[1]} for row in result.all()]


@router.get("/campaigns")
async def campaign_stats(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign).where(Campaign.workspace_id == current.workspace_id).order_by(Campaign.created_at.desc())
    )
    return [
        {
            "id": c.id, "name": c.name, "status": c.status,
            "totalLeads": c.total_leads, "priorityLeads": c.priority_leads,
            "averageScore": c.average_score,
            "createdAt": c.created_at.isoformat() if c.created_at else None,
            "completedAt": c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in result.scalars().all()
    ]


@router.get("/revenue")
async def revenue(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deal.stage, func.count(Deal.id), func.coalesce(func.sum(Deal.value), 0.0))
        .where(Deal.workspace_id == current.workspace_id)
        .group_by(Deal.stage)
    )
    return [{"stage": r[0], "count": r[1], "value": float(r[2])} for r in result.all()]
