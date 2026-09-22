"""Email service with Gmail SMTP, approval queue, bounce handling."""
from __future__ import annotations
import asyncio
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.config import get_settings
from app.core.ids import new_id
from app.models.email import EmailLog, EmailCampaign
from app.models.lead import Lead
from app.models.outreach import OutreachApproval

logger = logging.getLogger(__name__)
settings = get_settings()

UNSUBSCRIBE_FOOTER = "\n\n---\nTo unsubscribe, reply with UNSUBSCRIBE in the subject line.\nSent in compliance with CAN-SPAM regulations."

_sending_lock = asyncio.Lock()


def _send_smtp(to: str, subject: str, body: str) -> str:
    """Synchronous Gmail SMTP send — run in thread pool."""
    user = settings.GMAIL_USER
    pwd = settings.GMAIL_APP_PASSWORD
    if not user or not pwd:
        raise ValueError("Gmail credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD.")

    msg = MIMEMultipart("alternative")
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    full_body = body + UNSUBSCRIBE_FOOTER
    msg.attach(MIMEText(full_body, "plain"))
    msg.attach(MIMEText(full_body.replace("\n", "<br>"), "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(user, pwd)
        server.sendmail(user, to, msg.as_string())

    return f"<{new_id()}@smtp.gmail.com>"


async def send_single(
    db: AsyncSession,
    to: str,
    subject: str,
    body: str,
    lead_id: Optional[str] = None,
    email_campaign_id: Optional[str] = None,
) -> str:
    message_id = await asyncio.to_thread(_send_smtp, to, subject, body)

    log = EmailLog(
        id=new_id(), to=to, subject=subject, status="sent",
        message_id=message_id, lead_id=lead_id, email_campaign_id=email_campaign_id,
    )
    db.add(log)

    if lead_id:
        await db.execute(
            update(Lead).where(Lead.id == lead_id).values(
                email_sent=True, email_sent_at=datetime.now(timezone.utc),
                pipeline_stage="OUTREACH",
            )
        )
    await db.commit()
    return message_id


async def send_bulk(
    db: AsyncSession,
    workspace_id: str,
    lead_ids: list[str],
    subject_template: str,
    body_template: str,
    daily_limit: int = 50,
    delay_seconds: int = 90,
    email_campaign_id: Optional[str] = None,
    require_approval: bool = True,
) -> dict:
    if require_approval:
        # Queue for approval instead of sending
        count = 0
        for lid in lead_ids:
            result = await db.execute(select(Lead).where(Lead.id == lid, Lead.workspace_id == workspace_id))
            lead = result.scalar_one_or_none()
            if not lead or not lead.email or lead.email_sent:
                continue
            body = body_template.replace("{{name}}", lead.name).replace("{{business}}", lead.name).replace("{{address}}", lead.address or "")
            subj = subject_template.replace("{{name}}", lead.name).replace("{{business}}", lead.name)
            approval = OutreachApproval(
                id=new_id(), channel="email", to=lead.email,
                subject=subj, body=body, status="pending",
                lead_id=lid, workspace_id=workspace_id,
            )
            db.add(approval)
            count += 1
        await db.commit()
        return {"queued_for_approval": count, "sent": 0}

    async with _sending_lock:
        result = await db.execute(
            select(Lead).where(
                Lead.id.in_(lead_ids),
                Lead.workspace_id == workspace_id,
                Lead.email_sent == False,
                Lead.email != None,
            ).limit(daily_limit)
        )
        leads = result.scalars().all()

        sent = errors = 0
        for i, lead in enumerate(leads):
            body = body_template.replace("{{name}}", lead.name).replace("{{business}}", lead.name).replace("{{address}}", lead.address or "")
            subj = subject_template.replace("{{name}}", lead.name).replace("{{business}}", lead.name)
            try:
                await send_single(db, lead.email, subj, body, lead.id, email_campaign_id)
                sent += 1
                logger.info(f"Email sent to {lead.email} ({sent}/{len(leads)})")
            except Exception as exc:
                errors += 1
                logger.error(f"Email failed for {lead.email}: {exc}")
            if i < len(leads) - 1:
                await asyncio.sleep(delay_seconds)

        if email_campaign_id:
            await db.execute(
                update(EmailCampaign).where(EmailCampaign.id == email_campaign_id).values(
                    sent_count=EmailCampaign.sent_count + sent,
                    status="completed", completed_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

        return {"sent": sent, "skipped": len(lead_ids) - len(leads), "errors": errors}


async def approve_and_send(db: AsyncSession, approval_id: str) -> dict:
    result = await db.execute(select(OutreachApproval).where(OutreachApproval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise ValueError("Approval item not found")
    if approval.status != "pending":
        raise ValueError(f"Approval is already {approval.status}")

    msg_id = await asyncio.to_thread(_send_smtp, approval.to, approval.subject or "Outreach", approval.body)
    approval.status = "sent"
    approval.approved_at = datetime.now(timezone.utc)
    approval.sent_at = datetime.now(timezone.utc)

    log = EmailLog(
        id=new_id(), to=approval.to, subject=approval.subject or "",
        status="sent", message_id=msg_id, lead_id=approval.lead_id,
    )
    db.add(log)
    if approval.lead_id:
        await db.execute(
            update(Lead).where(Lead.id == approval.lead_id).values(
                email_sent=True, email_sent_at=datetime.now(timezone.utc), pipeline_stage="OUTREACH",
            )
        )
    await db.commit()
    return {"sent": True, "message_id": msg_id}


async def reject_approval(db: AsyncSession, approval_id: str, reason: str = "") -> None:
    result = await db.execute(select(OutreachApproval).where(OutreachApproval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise ValueError("Approval item not found")
    approval.status = "rejected"
    approval.rejected_at = datetime.now(timezone.utc)
    approval.rejected_reason = reason
    await db.commit()


async def get_email_stats(db: AsyncSession, workspace_id: str) -> dict:
    from sqlalchemy import func
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total = await db.scalar(select(func.count(EmailLog.id)))
    sent_today = await db.scalar(select(func.count(EmailLog.id)).where(EmailLog.sent_at >= today))
    replied = await db.scalar(select(func.count(EmailLog.id)).where(EmailLog.status == "replied"))
    bounced = await db.scalar(select(func.count(EmailLog.id)).where(EmailLog.status == "bounced"))

    daily_limit = settings.GMAIL_DAILY_LIMIT
    return {
        "totalSent": total or 0,
        "sentToday": sent_today or 0,
        "replied": replied or 0,
        "bounced": bounced or 0,
        "replyRate": round((replied or 0) / max(total or 1, 1) * 100),
        "dailyLimit": daily_limit,
        "remaining": max(0, daily_limit - (sent_today or 0)),
    }
