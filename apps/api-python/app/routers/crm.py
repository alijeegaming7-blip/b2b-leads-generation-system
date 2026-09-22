from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.crm import Deal, Meeting, Proposal

router = APIRouter(prefix="/crm", tags=["CRM Pipeline"])


def _deal_out(d: Deal) -> dict:
    return {
        "id": d.id, "title": d.title, "value": d.value, "currency": d.currency,
        "stage": d.stage, "probability": d.probability,
        "closeDate": d.close_date.isoformat() if d.close_date else None,
        "lostReason": d.lost_reason,
        "wonAt": d.won_at.isoformat() if d.won_at else None,
        "lostAt": d.lost_at.isoformat() if d.lost_at else None,
        "notes": d.notes, "leadId": d.lead_id,
        "createdAt": d.created_at.isoformat() if d.created_at else None,
    }


def _meeting_out(m: Meeting) -> dict:
    return {
        "id": m.id, "title": m.title,
        "scheduledAt": m.scheduled_at.isoformat() if m.scheduled_at else None,
        "duration": m.duration, "type": m.meeting_type, "status": m.status,
        "notes": m.notes, "outcome": m.outcome, "dealId": m.deal_id,
    }


def _proposal_out(p: Proposal) -> dict:
    return {
        "id": p.id, "title": p.title, "value": p.value, "currency": p.currency,
        "status": p.status,
        "sentAt": p.sent_at.isoformat() if p.sent_at else None,
        "acceptedAt": p.accepted_at.isoformat() if p.accepted_at else None,
        "rejectedAt": p.rejected_at.isoformat() if p.rejected_at else None,
        "notes": p.notes, "dealId": p.deal_id,
    }


# ── Deals ─────────────────────────────────────────────────────────────────────

class CreateDealRequest(BaseModel):
    title: str
    value: float = 0.0
    currency: str = "USD"
    stage: str = "lead"
    probability: int = 0
    close_date: Optional[str] = None
    notes: Optional[str] = None
    lead_id: Optional[str] = None


class UpdateDealRequest(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    close_date: Optional[str] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None


@router.get("/deals")
async def list_deals(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deal).where(Deal.workspace_id == current.workspace_id).order_by(Deal.created_at.desc())
    )
    return [_deal_out(d) for d in result.scalars().all()]


@router.get("/deals/pipeline")
async def pipeline_summary(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal).where(Deal.workspace_id == current.workspace_id))
    stages: dict = {}
    for d in result.scalars().all():
        if d.stage not in stages:
            stages[d.stage] = {"count": 0, "value": 0.0}
        stages[d.stage]["count"] += 1
        stages[d.stage]["value"] += d.value
    return [{"stage": s, **v} for s, v in stages.items()]


@router.post("/deals", status_code=201)
async def create_deal(
    body: CreateDealRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deal = Deal(
        id=new_id(), title=body.title, value=body.value, currency=body.currency,
        stage=body.stage, probability=body.probability,
        close_date=datetime.fromisoformat(body.close_date.replace("Z", "+00:00")) if body.close_date else None,
        notes=body.notes, lead_id=body.lead_id, workspace_id=current.workspace_id,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return _deal_out(deal)


@router.patch("/deals/{deal_id}")
async def update_deal(
    deal_id: str,
    body: UpdateDealRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.workspace_id == current.workspace_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, "Deal not found")

    now = datetime.now(timezone.utc)
    if body.title is not None:       deal.title = body.title
    if body.value is not None:       deal.value = body.value
    if body.probability is not None: deal.probability = body.probability
    if body.notes is not None:       deal.notes = body.notes
    if body.close_date:              deal.close_date = datetime.fromisoformat(body.close_date.replace("Z", "+00:00"))
    if body.stage is not None:
        deal.stage = body.stage
        if body.stage == "won":  deal.won_at = now
        if body.stage == "lost": deal.lost_at = now; deal.lost_reason = body.lost_reason

    await db.commit()
    await db.refresh(deal)
    return _deal_out(deal)


@router.delete("/deals/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.workspace_id == current.workspace_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, "Deal not found")
    await db.delete(deal)
    await db.commit()


# ── Meetings ──────────────────────────────────────────────────────────────────

class CreateMeetingRequest(BaseModel):
    title: str
    scheduled_at: str
    duration: int = 30
    meeting_type: str = "call"
    notes: Optional[str] = None
    deal_id: Optional[str] = None


@router.get("/meetings")
async def list_meetings(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Meeting).where(Meeting.workspace_id == current.workspace_id).order_by(Meeting.scheduled_at)
    )
    return [_meeting_out(m) for m in result.scalars().all()]


@router.post("/meetings", status_code=201)
async def create_meeting(
    body: CreateMeetingRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = Meeting(
        id=new_id(), title=body.title, duration=body.duration, meeting_type=body.meeting_type,
        scheduled_at=datetime.fromisoformat(body.scheduled_at.replace("Z", "+00:00")),
        notes=body.notes, deal_id=body.deal_id, workspace_id=current.workspace_id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return _meeting_out(m)


@router.patch("/meetings/{meeting_id}")
async def update_meeting(
    meeting_id: str,
    body: dict,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id, Meeting.workspace_id == current.workspace_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Meeting not found")
    for k, v in body.items():
        attr = "meeting_type" if k == "type" else k
        if hasattr(m, attr):
            setattr(m, attr, v)
    await db.commit()
    await db.refresh(m)
    return _meeting_out(m)


# ── Proposals ─────────────────────────────────────────────────────────────────

class CreateProposalRequest(BaseModel):
    title: str
    value: float
    currency: str = "USD"
    content: Optional[str] = None
    notes: Optional[str] = None
    deal_id: Optional[str] = None


@router.get("/proposals")
async def list_proposals(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Proposal).where(Proposal.workspace_id == current.workspace_id).order_by(Proposal.created_at.desc())
    )
    return [_proposal_out(p) for p in result.scalars().all()]


@router.post("/proposals", status_code=201)
async def create_proposal(
    body: CreateProposalRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = Proposal(
        id=new_id(), title=body.title, value=body.value, currency=body.currency,
        content=body.content, notes=body.notes, deal_id=body.deal_id,
        workspace_id=current.workspace_id,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _proposal_out(p)


@router.patch("/proposals/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    body: dict,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.workspace_id == current.workspace_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Proposal not found")
    now = datetime.now(timezone.utc)
    for k, v in body.items():
        if hasattr(p, k):
            setattr(p, k, v)
    if body.get("status") == "sent" and not p.sent_at:         p.sent_at = now
    if body.get("status") == "accepted" and not p.accepted_at: p.accepted_at = now
    if body.get("status") == "rejected" and not p.rejected_at: p.rejected_at = now
    await db.commit()
    await db.refresh(p)
    return _proposal_out(p)
