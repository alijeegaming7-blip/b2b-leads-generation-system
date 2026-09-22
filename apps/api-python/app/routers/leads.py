from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.lead import Lead, LeadActivity
from app.core.demo import apply_demo_blur, is_demo, demo_status_payload

router = APIRouter(prefix="/leads", tags=["Leads"])


def _parse_json(val: object) -> object:
    if not val:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return None
    return val


def _serialize(lead: Lead) -> dict:
    d: dict = {
        "id": lead.id,
        "name": lead.name,
        "address": lead.address,
        "lat": lead.lat,
        "lng": lead.lng,
        "phone": lead.phone,
        "email": lead.email,
        "website": lead.website,
        "rating": lead.rating,
        "reviewCount": lead.review_count,
        "category": lead.category,
        "source": lead.source,
        "referenceUrl": lead.reference_url,
        "hasWebsite": lead.has_website,
        "score": lead.score,
        "icpFitScore": lead.icp_fit_score,
        "intentScore": lead.intent_score,
        "priority": lead.priority,
        "pipelineStage": lead.pipeline_stage,
        "crmStatus": lead.crm_status,
        "crmNotes": lead.crm_notes,
        "followUpDate": lead.follow_up_date.isoformat() if lead.follow_up_date else None,
        "contactedAt": lead.contacted_at.isoformat() if lead.contacted_at else None,
        "repliedAt": lead.replied_at.isoformat() if lead.replied_at else None,
        "closedAt": lead.closed_at.isoformat() if lead.closed_at else None,
        "emailSent": lead.email_sent,
        "emailSentAt": lead.email_sent_at.isoformat() if lead.email_sent_at else None,
        "emailOpened": lead.email_opened,
        "emailReplied": lead.email_replied,
        "emailBounced": lead.email_bounced,
        "whatsappSent": lead.whatsapp_sent,
        "lastReplyIntent": lead.last_reply_intent,
        "lastReplySentiment": lead.last_reply_sentiment,
        "lastReplyUrgency": lead.last_reply_urgency,
        "recommendedAction": lead.recommended_action,
        "lastReplyAt": lead.last_reply_at.isoformat() if lead.last_reply_at else None,
        "campaignId": lead.campaign_id,
        "workspaceId": lead.workspace_id,
        "scrapedAt": lead.scraped_at.isoformat() if lead.scraped_at else None,
        "createdAt": lead.created_at.isoformat() if lead.created_at else None,
        "aiAnalysis": _parse_json(lead.ai_analysis),
        "marketingContent": _parse_json(lead.marketing_content),
        "salesBrief": _parse_json(lead.sales_brief),
        "websiteAudit": _parse_json(lead.website_audit),
        "opportunities": _parse_json(lead.opportunities),
        "matchedServices": _parse_json(lead.matched_services),
        "matchedCaseStudy": _parse_json(lead.matched_case_study),
        # Enhanced fields
        "city": lead.city,
        "state": lead.state,
        "zipCode": lead.zip_code,
        "country": lead.country,
        "socialMedia": _parse_json(lead.social_media) or {},
        "additionalEmails": _parse_json(lead.additional_emails) or [],
    }
    # Lazy-loaded relationships
    if hasattr(lead, "activities") and lead.activities is not None:
        try:
            d["activities"] = [
                {"id": a.id, "type": a.type, "note": a.note,
                 "createdAt": a.created_at.isoformat() if a.created_at else None}
                for a in lead.activities
            ]
        except Exception:
            pass
    if hasattr(lead, "campaign") and lead.campaign is not None:
        try:
            d["campaign"] = {"id": lead.campaign.id, "name": lead.campaign.name}
        except Exception:
            pass
    return d


@router.get("")
async def list_leads(
    campaign_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    pipeline_stage: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).where(Lead.workspace_id == current.workspace_id)
    cnt = select(func.count(Lead.id)).where(Lead.workspace_id == current.workspace_id)

    if campaign_id:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
        cnt = cnt.where(Lead.campaign_id == campaign_id)
    if q:
        stmt = stmt.where(Lead.name.ilike(f"%{q}%"))
        cnt = cnt.where(Lead.name.ilike(f"%{q}%"))
    if priority:
        stmt = stmt.where(Lead.priority == priority)
        cnt = cnt.where(Lead.priority == priority)
    if status:
        stmt = stmt.where(Lead.crm_status == status)
        cnt = cnt.where(Lead.crm_status == status)
    if source:
        stmt = stmt.where(Lead.source == source)
        cnt = cnt.where(Lead.source == source)
    if pipeline_stage:
        stmt = stmt.where(Lead.pipeline_stage == pipeline_stage)
        cnt = cnt.where(Lead.pipeline_stage == pipeline_stage)

    stmt = (stmt.order_by(Lead.score.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .options(selectinload(Lead.activities), selectinload(Lead.campaign)))

    data_result = await db.execute(stmt)
    count_result = await db.execute(cnt)
    leads = data_result.scalars().all()
    total = count_result.scalar() or 0

    serialized = [apply_demo_blur(_serialize(l)) for l in leads]

    response = {"data": serialized, "total": total, "page": page, "limit": limit}
    if is_demo():
        response.update(demo_status_payload())
    return response


@router.get("/whatsapp")
async def whatsapp_leads(
    campaign_id: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).where(Lead.workspace_id == current.workspace_id, Lead.phone.isnot(None))
    if campaign_id:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    stmt = stmt.order_by(Lead.score.desc())
    result = await db.execute(stmt)
    leads = result.scalars().all()

    return [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "address": l.address,
            "score": l.score,
            "priority": l.priority,
            "source": l.source,
            "whatsappSent": l.whatsapp_sent,
            "marketingContent": _parse_json(l.marketing_content),
            "whatsappUrl": f"https://wa.me/{''.join(c for c in l.phone if c.isdigit())}" if l.phone else None,
        }
        for l in leads
    ]


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (select(Lead)
            .where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
            .options(selectinload(Lead.activities), selectinload(Lead.follow_ups), selectinload(Lead.campaign)))
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    result_dict = apply_demo_blur(_serialize(lead))
    if is_demo():
        result_dict.update(demo_status_payload())
    return result_dict


class UpdateCrmRequest(BaseModel):
    crmStatus: Optional[str] = None
    crmNotes: Optional[str] = None
    followUpDate: Optional[str] = None


@router.patch("/{lead_id}/crm")
async def update_crm(
    lead_id: str,
    body: UpdateCrmRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    now = datetime.now(timezone.utc)
    if body.crmStatus:    lead.crm_status = body.crmStatus
    if body.crmNotes:     lead.crm_notes = body.crmNotes
    if body.followUpDate:
        lead.follow_up_date = datetime.fromisoformat(body.followUpDate.replace("Z", "+00:00"))
    if body.crmStatus == "contacted":      lead.contacted_at = now
    if body.crmStatus == "replied":        lead.replied_at = now
    if body.crmStatus in ("won", "lost"):  lead.closed_at = now

    activity = LeadActivity(
        id=new_id(), lead_id=lead_id, type="crm_update",
        note=f"Status changed to {body.crmStatus}",
        extra=json.dumps(body.model_dump()),
    )
    db.add(activity)
    await db.commit()
    await db.refresh(lead)
    return _serialize(lead)


@router.post("/{lead_id}/research")
async def trigger_research(
    lead_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Lead not found")

    try:
        from app.services.pipeline import research_lead_task
        task = research_lead_task.delay(lead_id, current.workspace_id)
        return {"message": "Research started", "task_id": task.id}
    except Exception:
        return {"message": "Research queued (Celery not running — start worker for background tasks)"}


# ── Social / enrichment patch ─────────────────────────────────────────────────

class UpdateSocialRequest(BaseModel):
    socialMedia: Optional[dict] = None
    additionalEmails: Optional[list] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None


@router.patch("/{lead_id}/social")
async def update_social(
    lead_id: str,
    body: UpdateSocialRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    if body.socialMedia is not None:
        lead.social_media = json.dumps(body.socialMedia)
    if body.additionalEmails is not None:
        lead.additional_emails = json.dumps(body.additionalEmails)
    if body.city is not None:
        lead.city = body.city
    if body.state is not None:
        lead.state = body.state
    if body.zipCode is not None:
        lead.zip_code = body.zipCode
    if body.country is not None:
        lead.country = body.country

    await db.commit()
    await db.refresh(lead)
    return _serialize(lead)


# ── Pitch generator ───────────────────────────────────────────────────────────

class GeneratePitchRequest(BaseModel):
    tone: str = "professional"        # professional | friendly | urgent
    service: str = "website"          # website | seo | inventory | analytics | ai


@router.post("/{lead_id}/pitch")
async def generate_pitch(
    lead_id: str,
    body: GeneratePitchRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI pitch / cold outreach message for a lead."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    issues = []
    try:
        ai_data = json.loads(lead.ai_analysis or "{}")
        issues = ai_data.get("issues_found", [])
    except Exception:
        pass

    # Build pitch based on service type and tone
    pitch = _build_pitch(
        name=lead.name,
        service=body.service,
        tone=body.tone,
        issues=issues,
        website=lead.website,
        rating=lead.rating,
        review_count=lead.review_count,
    )

    # Save generated pitch back to lead
    lead.sales_brief = json.dumps({"pitch": pitch, "service": body.service, "tone": body.tone})
    db.add(LeadActivity(
        id=new_id(),
        lead_id=lead_id,
        type="pitch_generated",
        note=f"Pitch generated — service: {body.service}, tone: {body.tone}",
    ))
    await db.commit()

    return {"pitch": pitch, "service": body.service, "tone": body.tone}


def _build_pitch(
    name: str,
    service: str,
    tone: str,
    issues: list,
    website: Optional[str],
    rating: Optional[str],
    review_count: Optional[int],
) -> str:
    """Build a contextual pitch message from lead data."""

    greetings = {
        "professional": f"Dear {name} Team,",
        "friendly":     f"Hi {name}! 👋",
        "urgent":       f"Hi {name},",
    }
    greeting = greetings.get(tone, greetings["professional"])

    # Opening line based on service
    openings = {
        "website": (
            f"I noticed that {name} doesn't have a website yet — or the current one isn't "
            "mobile-friendly or easily found on Google."
        ) if not website else (
            f"I took a quick look at {name}'s website and spotted a few things that could be "
            "costing you new customers every day."
        ),
        "seo": (
            f"When I searched for businesses like {name} in your area, your listing didn't come "
            "up on the first page of Google — which means you're missing leads daily."
        ),
        "inventory": (
            f"Many businesses like {name} are losing sales because they don't have a real-time "
            "inventory system that customers can check online."
        ),
        "analytics": (
            f"Without clear data dashboards, it's hard to know what's working for {name} — "
            "and what's quietly costing you money."
        ),
        "ai": (
            f"AI tools are transforming businesses like {name} — automating customer follow-ups, "
            "bookings, and support at a fraction of the cost of hiring staff."
        ),
    }
    opening = openings.get(service, openings["website"])

    # Issue bullets
    issue_block = ""
    if issues:
        bullets = "\n".join(f"  • {issue}" for issue in issues[:3])
        issue_block = f"\n\nSpecifically, I noticed:\n{bullets}"

    # Social proof if rating available
    proof = ""
    if rating and rating not in ("", "N/A") and review_count and review_count > 10:
        proof = (
            f"\n\nYou already have a great reputation — {rating}⭐ from {review_count} customers. "
            "Imagine converting even 20% more visitors into paying clients."
        )

    # CTA based on tone
    ctas = {
        "professional": (
            "\n\nI'd love to schedule a brief 15-minute call to walk you through what we can do. "
            "There's no cost or commitment — just a conversation.\n\n"
            "Would you be available this week?\n\nBest regards,\n[Your Name]"
        ),
        "friendly": (
            "\n\nI'd love to show you what we can do — no commitment, totally free consultation. "
            "Want to hop on a quick call? 🚀\n\nCheers,\n[Your Name]"
        ),
        "urgent": (
            "\n\nEvery day without this fix is costing you customers. "
            "I have a slot open this week — can we talk?\n\nBest,\n[Your Name]"
        ),
    }
    cta = ctas.get(tone, ctas["professional"])

    return f"{greeting}\n\n{opening}{issue_block}{proof}{cta}"


# ── Add note / activity ───────────────────────────────────────────────────────

class AddNoteRequest(BaseModel):
    note: str
    type: str = "note"   # note | call | meeting | email | whatsapp


@router.post("/{lead_id}/notes")
async def add_note(
    lead_id: str,
    body: AddNoteRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == current.workspace_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Lead not found")

    activity = LeadActivity(
        id=new_id(),
        lead_id=lead_id,
        type=body.type,
        note=body.note,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return {
        "id": activity.id,
        "type": activity.type,
        "note": activity.note,
        "createdAt": activity.created_at.isoformat() if activity.created_at else None,
    }
