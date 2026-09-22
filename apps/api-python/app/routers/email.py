from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.email import EmailCampaign, EmailLog
from app.models.outreach import OutreachApproval

router = APIRouter(prefix="/email", tags=["Email"])


class SendSingleRequest(BaseModel):
    to: str
    subject: str
    body: str
    lead_id: Optional[str] = None
    email_campaign_id: Optional[str] = None


class SendBulkRequest(BaseModel):
    subject: str
    body_template: str
    lead_ids: list[str]
    daily_limit: int = 50
    delay_seconds: int = 90
    email_campaign_id: Optional[str] = None
    require_approval: bool = True


class CreateEmailCampaignRequest(BaseModel):
    name: str
    subject: str
    body: str
    daily_limit: int = 50
    delay_seconds: int = 90
    require_approval: bool = True


class RejectRequest(BaseModel):
    reason: str = ""


@router.post("/send")
async def send_single(
    body: SendSingleRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from app.services.email_service import send_single as do_send
        msg_id = await do_send(db, body.to, body.subject, body.body, body.lead_id, body.email_campaign_id)
        return {"sent": True, "messageId": msg_id}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/bulk")
async def send_bulk(
    body: SendBulkRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.email_service import send_bulk as do_bulk
    return await do_bulk(
        db, current.workspace_id, body.lead_ids, body.subject,
        body.body_template, body.daily_limit, body.delay_seconds,
        body.email_campaign_id, body.require_approval,
    )


@router.get("/stats")
async def stats(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.email_service import get_email_stats
    return await get_email_stats(db, current.workspace_id)


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CreateEmailCampaignRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ec = EmailCampaign(
        id=new_id(), name=body.name, subject=body.subject, body=body.body,
        daily_limit=body.daily_limit, delay_seconds=body.delay_seconds,
        require_approval=body.require_approval, workspace_id=current.workspace_id,
    )
    db.add(ec)
    await db.commit()
    await db.refresh(ec)
    return {
        "id": ec.id, "name": ec.name, "subject": ec.subject, "status": ec.status,
        "sentCount": ec.sent_count, "replyCount": ec.reply_count,
        "dailyLimit": ec.daily_limit, "requireApproval": ec.require_approval,
    }


@router.get("/campaigns")
async def list_campaigns(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailCampaign)
        .where(EmailCampaign.workspace_id == current.workspace_id)
        .order_by(EmailCampaign.created_at.desc())
    )
    cams = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "subject": c.subject, "status": c.status,
         "sentCount": c.sent_count, "replyCount": c.reply_count,
         "bounceCount": c.bounce_count, "dailyLimit": c.daily_limit}
        for c in cams
    ]


@router.get("/campaigns/{campaign_id}/logs")
async def campaign_logs(
    campaign_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailLog)
        .where(EmailLog.email_campaign_id == campaign_id)
        .order_by(EmailLog.sent_at.desc())
        .limit(100)
    )
    logs = result.scalars().all()
    return [
        {"id": l.id, "to": l.to_address, "subject": l.subject, "status": l.status,
         "sentAt": l.sent_at.isoformat() if l.sent_at else None}
        for l in logs
    ]


@router.get("/approvals")
async def list_approvals(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OutreachApproval)
        .where(OutreachApproval.workspace_id == current.workspace_id, OutreachApproval.status == "pending")
        .order_by(OutreachApproval.created_at.desc())
    )
    items = result.scalars().all()
    return [
        {"id": i.id, "channel": i.channel, "to": i.to_address, "subject": i.subject,
         "body": i.body, "status": i.status, "leadId": i.lead_id,
         "createdAt": i.created_at.isoformat() if i.created_at else None}
        for i in items
    ]


@router.post("/approvals/{approval_id}/approve")
async def approve(
    approval_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from app.services.email_service import approve_and_send
        return await approve_and_send(db, approval_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/approvals/{approval_id}/reject")
async def reject(
    approval_id: str,
    body: RejectRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from app.services.email_service import reject_approval
        await reject_approval(db, approval_id, body.reason)
        return {"rejected": True}
    except ValueError as e:
        raise HTTPException(400, str(e))
