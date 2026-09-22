from __future__ import annotations
import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.lead import Lead

router = APIRouter(prefix="/export", tags=["Export"])


def _safe_json(val: object) -> object:
    if not val:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return None
    return val


async def _get_leads(db: AsyncSession, workspace_id: str, campaign_id: Optional[str]):
    stmt = (select(Lead)
            .where(Lead.workspace_id == workspace_id)
            .options(selectinload(Lead.campaign))
            .order_by(Lead.score.desc()))
    if campaign_id:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/csv")
async def export_csv(
    campaign_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = await _get_leads(db, current.workspace_id, campaign_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Address", "Phone", "Email", "Website", "Rating", "Reviews",
        "Score", "ICP Fit", "Intent", "Priority", "Pipeline Stage", "CRM Status",
        "Source", "Campaign", "Has Website", "Email Sent", "Scraped At",
    ])
    for l in leads:
        writer.writerow([
            l.name, l.address, l.phone, l.email, l.website, l.rating, l.review_count,
            l.score, l.icp_fit_score, l.intent_score, l.priority, l.pipeline_stage,
            l.crm_status, l.source,
            getattr(l.campaign, "name", "") if l.campaign else "",
            "Yes" if l.has_website else "No",
            "Yes" if l.email_sent else "No",
            l.scraped_at.isoformat() if l.scraped_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/json")
async def export_json(
    campaign_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = await _get_leads(db, current.workspace_id, campaign_id)
    data = [
        {
            "id": l.id, "name": l.name, "address": l.address,
            "phone": l.phone, "email": l.email, "website": l.website,
            "rating": l.rating, "reviewCount": l.review_count,
            "score": l.score, "icpFitScore": l.icp_fit_score,
            "intentScore": l.intent_score, "priority": l.priority,
            "pipelineStage": l.pipeline_stage, "crmStatus": l.crm_status,
            "source": l.source, "hasWebsite": l.has_website, "emailSent": l.email_sent,
            "campaign": getattr(l.campaign, "name", None) if l.campaign else None,
            "marketingContent": _safe_json(l.marketing_content),
            "aiAnalysis": _safe_json(l.ai_analysis),
            "scrapedAt": l.scraped_at.isoformat() if l.scraped_at else None,
        }
        for l in leads
    ]
    content = json.dumps(data, indent=2, ensure_ascii=False)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=leads.json"},
    )


@router.get("/vcard")
async def export_vcard(
    campaign_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = await _get_leads(db, current.workspace_id, campaign_id)
    vcards = []
    for l in leads:
        if not (l.phone or l.email):
            continue
        lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{l.name}"]
        if l.phone:   lines.append(f"TEL;TYPE=WORK:{l.phone}")
        if l.email:   lines.append(f"EMAIL;TYPE=WORK:{l.email}")
        if l.address: lines.append(f"ADR;TYPE=WORK:;;{l.address};;;;")
        if l.website:
            url = l.website if l.website.startswith("http") else f"https://{l.website}"
            lines.append(f"URL:{url}")
        lines.append(f"NOTE:Score:{l.score}|Priority:{l.priority}|Stage:{l.pipeline_stage}|Source:{l.source}")
        lines.append("END:VCARD")
        vcards.append("\r\n".join(lines))

    return StreamingResponse(
        iter(["\r\n".join(vcards)]),
        media_type="text/vcard",
        headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
    )


@router.get("/whatsapp-csv")
async def export_whatsapp(
    campaign_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = await _get_leads(db, current.workspace_id, campaign_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Phone", "WhatsApp Link", "Address", "Score", "Priority", "Rating", "Source", "Pre-written Message"])
    for l in leads:
        if not l.phone:
            continue
        digits = "".join(c for c in l.phone if c.isdigit())
        wa_link = f"https://wa.me/{digits}" if digits else ""
        mc = _safe_json(l.marketing_content)
        msg = (mc.get("whatsapp") if isinstance(mc, dict) else None) or f"Hi {l.name}! I came across your business and would love to connect."
        writer.writerow([l.name, l.phone, wa_link, l.address, l.score, l.priority, l.rating, l.source, msg])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=whatsapp_leads.csv"},
    )
