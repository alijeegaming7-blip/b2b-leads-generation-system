"""
8-Stage Sales Pipeline Orchestrator
DISCOVER → RESEARCH → SCORE → MATCH → PITCH → OUTREACH → RESPOND → CONVERT

Runs as a Celery task for campaigns. Can also be triggered per-lead.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from celery import Celery
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.ids import new_id
from app.models.campaign import Campaign
from app.models.lead import Lead, LeadActivity
from app.models.scraper import ScraperJob

logger = logging.getLogger(__name__)
settings = get_settings()

# Celery app
celery_app = Celery("ezitech", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Sync DB engine for Celery tasks (Celery doesn't support asyncio natively)
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite+aiosqlite"):
    _sync_url = _db_url.replace("sqlite+aiosqlite", "sqlite")
elif _db_url.startswith("postgresql+asyncpg"):
    _sync_url = _db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
else:
    _sync_url = _db_url.replace("postgresql://", "postgresql+psycopg2://")

_sync_kwargs = {"connect_args": {"check_same_thread": False}} if _sync_url.startswith("sqlite") else {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
_sync_engine = create_engine(_sync_url, **_sync_kwargs)
SyncSession = sessionmaker(bind=_sync_engine)


def _update_campaign(db: Session, campaign_id: str, status: str, progress: int, error: str = None):
    data = {"status": status, "progress": progress, "updated_at": datetime.now(timezone.utc)}
    if error: data["error"] = error
    if status == "running" and progress == 0: data["started_at"] = datetime.now(timezone.utc)
    if status == "completed": data["completed_at"] = datetime.now(timezone.utc)
    db.execute(update(Campaign).where(Campaign.id == campaign_id).values(**data))
    db.commit()


def _add_activity(db: Session, lead_id: str, type_: str, note: str, meta: dict = None):
    act = LeadActivity(
        id=new_id(), lead_id=lead_id, type=type_, note=note,
        metadata=json.dumps(meta) if meta else None,
    )
    db.add(act)
    db.commit()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60, name="pipeline.run_campaign")
def run_campaign_task(self, campaign_id: str):
    """Full 8-stage pipeline for a campaign."""
    from app.services.scraper.google_maps import _scrape_sync
    from app.services.ai.lead_intelligence import score_lead
    import asyncio

    db = SyncSession()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return

        if db.query(ScraperJob).filter(ScraperJob.campaign_id == campaign_id, ScraperJob.status == "running").first():
            logger.warning(f"Campaign {campaign_id} already running")
            return

        job = ScraperJob(id=new_id(), campaign_id=campaign_id, workspace_id=campaign.workspace_id,
                         status="running", data=json.dumps({"campaign_id": campaign_id}), attempts=1)
        db.merge(job)
        db.commit()

        _update_campaign(db, campaign_id, "running", 0)

        # ── STAGE 1: DISCOVER ────────────────────────────────────────────────
        logger.info(f"[{campaign_id}] STAGE 1: DISCOVER")
        queries = json.loads(campaign.search_queries or "[]")
        sources = json.loads(campaign.sources or '["google_maps"]')
        areas = [a.strip() for a in campaign.location.split(",") if a.strip()] or [campaign.location]
        if not areas: areas = [campaign.location]

        combos = [(f"{q} in {area}", area) for q in queries for area in areas]
        per_combo = max(5, campaign.max_results // max(len(combos), 1))

        raw_leads: list[dict] = []
        for i, (combo_query, _) in enumerate(combos):
            if "google_maps" in sources:
                try:
                    scraped = _scrape_sync(combo_query, per_combo)
                    raw_leads.extend(scraped)
                    logger.info(f"[{campaign_id}] Scraped {len(scraped)} from '{combo_query}'")
                except Exception as exc:
                    logger.warning(f"[{campaign_id}] Scrape failed for '{combo_query}': {exc}")
            pct = round((i + 1) / len(combos) * 25)
            _update_campaign(db, campaign_id, "running", pct)

        # Deduplicate
        seen = set()
        deduped = []
        for lead in raw_leads:
            key = f"{lead['name'].lower()}|{lead.get('address','').lower()}"
            if key not in seen:
                seen.add(key)
                deduped.append(lead)
        deduped = deduped[:campaign.max_results]

        if not deduped:
            _update_campaign(db, campaign_id, "failed", 0, "No leads found. Try different location/query.")
            db.execute(update(ScraperJob).where(ScraperJob.campaign_id == campaign_id).values(status="failed", error="No leads"))
            db.commit()
            return

        _update_campaign(db, campaign_id, "running", 30)

        # ── STAGE 2-3: RESEARCH + SCORE ─────────────────────────────────────
        logger.info(f"[{campaign_id}] STAGE 2-3: RESEARCH + SCORE ({len(deduped)} leads)")
        scored_leads = []
        for lead in deduped:
            s = score_lead(
                name=lead["name"], address=lead.get("address"), phone=lead.get("phone"),
                email=lead.get("email"), website=lead.get("website"), rating=lead.get("rating"),
                review_count=lead.get("review_count"), has_website=lead.get("has_website", False),
                source=lead.get("source"), industry=campaign.industry,
            )
            scored_leads.append({**lead, "score": s.score, "icp_fit_score": s.icp_fit_score,
                                  "intent_score": s.intent_score, "priority": s.priority,
                                  "factors": s.factors, "recommendation": s.recommendation})

        # Sort: demo data last, then by score desc
        scored_leads.sort(key=lambda l: (1 if l.get("source") == "demo_data" else 0, -l["score"]))
        _update_campaign(db, campaign_id, "running", 55)

        # ── STAGE 4-5: MATCH + PITCH (HIGH priority leads) ──────────────────
        logger.info(f"[{campaign_id}] STAGE 4-5: MATCH + PITCH")

        async def _enrich_high(lead: dict) -> dict:
            from app.services.ai.sales_research import research as do_research
            from app.services.ai.opportunity_finder import find_opportunities
            from app.services.ai.service_recommendation import recommend_services, match_case_study
            from app.services.ai.marketing_ai import generate as gen_pitch
            try:
                brief = await do_research(
                    name=lead["name"], industry=campaign.industry,
                    address=lead.get("address"), website=lead.get("website"),
                    rating=lead.get("rating"), review_count=lead.get("review_count"),
                    phone=lead.get("phone"), email=lead.get("email"), score=lead["score"],
                )
                opps = await find_opportunities(lead, brief)
                services = await recommend_services(opps, brief)
                cs = await match_case_study(opps, brief)
                pitch = await gen_pitch(
                    business_name=lead["name"], industry=campaign.industry,
                    address=lead.get("address"), rating=lead.get("rating"),
                    has_website=lead.get("has_website", False),
                    your_service=campaign.your_service,
                    content_style=campaign.content_style, language=campaign.language,
                    score=lead["score"], sales_brief=brief, case_study=cs,
                    top_service=services[0] if services else None,
                )
                import dataclasses
                return {
                    **lead,
                    "pipeline_stage": "PITCH",
                    "sales_brief": json.dumps(dataclasses.asdict(brief)),
                    "opportunities": json.dumps([dataclasses.asdict(o) for o in opps]),
                    "matched_services": json.dumps([dataclasses.asdict(s) for s in services]),
                    "matched_case_study": json.dumps(dataclasses.asdict(cs)) if cs else None,
                    "researched_at": datetime.now(timezone.utc).isoformat(),
                    "marketing_content": json.dumps({
                        "email": {"subject": pitch.email_subject, "body": pitch.email_body},
                        "whatsapp": pitch.whatsapp, "instagram": pitch.instagram,
                        "linkedin": {"connectionNote": pitch.linkedin_note},
                        "coldCall": {"opening": pitch.cold_call_opening},
                        "pitchAngle": pitch.pitch_angle, "proofPoint": pitch.proof_point,
                    }),
                    "pitch_generated_at": datetime.now(timezone.utc).isoformat(),
                    "ai_analysis": json.dumps({"factors": lead["factors"], "recommendation": lead["recommendation"]}),
                }
            except Exception as exc:
                logger.warning(f"Enrichment failed for {lead['name']}: {exc}")
                return lead

        high_priority = [l for l in scored_leads if l["priority"] == "HIGH"]
        other = [l for l in scored_leads if l["priority"] != "HIGH"]

        import asyncio as _asyncio
        loop = _asyncio.new_event_loop()
        enriched_high = loop.run_until_complete(_asyncio.gather(*[_enrich_high(l) for l in high_priority[:20]]))
        loop.close()

        final_leads = list(enriched_high) + other
        _update_campaign(db, campaign_id, "running", 85)

        # ── Save leads to DB ─────────────────────────────────────────────────
        logger.info(f"[{campaign_id}] Saving {len(final_leads)} leads to DB")
        saved = 0
        for lead in final_leads:
            try:
                db_lead = Lead(
                    id=new_id(),
                    name=lead["name"],
                    address=lead.get("address") or None,
                    phone=lead.get("phone") or None,
                    email=lead.get("email") or None,
                    website=lead.get("website") or None,
                    rating=lead.get("rating") or None,
                    review_count=lead.get("review_count"),
                    has_website=lead.get("has_website", False),
                    reference_url=lead.get("reference_link") or None,
                    lat=lead.get("lat"), lng=lead.get("lng"),
                    score=lead.get("score", 0),
                    icp_fit_score=lead.get("icp_fit_score", 0),
                    intent_score=lead.get("intent_score", 0),
                    priority=lead.get("priority", "LOW"),
                    source=lead.get("source", "google_maps"),
                    pipeline_stage=lead.get("pipeline_stage", "SCORE"),
                    sales_brief=lead.get("sales_brief"),
                    opportunities=lead.get("opportunities"),
                    matched_services=lead.get("matched_services"),
                    matched_case_study=lead.get("matched_case_study"),
                    researched_at=datetime.fromisoformat(lead["researched_at"]) if lead.get("researched_at") else None,
                    marketing_content=lead.get("marketing_content"),
                    pitch_generated_at=datetime.fromisoformat(lead["pitch_generated_at"]) if lead.get("pitch_generated_at") else None,
                    ai_analysis=lead.get("ai_analysis"),
                    campaign_id=campaign_id,
                    workspace_id=campaign.workspace_id,
                )
                db.add(db_lead)
                db.flush()
                saved += 1
            except Exception:
                db.rollback()
        db.commit()

        # Update campaign stats
        total = len(final_leads)
        high = sum(1 for l in final_leads if l.get("priority") == "HIGH")
        hq = sum(1 for l in final_leads if (l.get("score", 0) >= 70))
        avg = round(sum(l.get("score", 0) for l in final_leads) / max(total, 1))
        db.execute(update(Campaign).where(Campaign.id == campaign_id).values(
            total_leads=total, priority_leads=high, high_quality_leads=hq, average_score=avg,
        ))
        db.commit()

        _update_campaign(db, campaign_id, "completed", 100)
        db.execute(update(ScraperJob).where(ScraperJob.campaign_id == campaign_id).values(status="completed"))
        db.commit()
        logger.info(f"[{campaign_id}] COMPLETE: {total} leads, {high} HIGH priority, avg score {avg}")

    except Exception as exc:
        logger.error(f"[{campaign_id}] Pipeline failed: {exc}")
        try:
            _update_campaign(db, campaign_id, "failed", 0, str(exc))
            db.execute(update(ScraperJob).where(ScraperJob.campaign_id == campaign_id).values(status="failed", error=str(exc)))
            db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="pipeline.research_lead")
def research_lead_task(lead_id: str, workspace_id: str):
    """Run the full AI research pipeline on a single lead (RESEARCH→SCORE→MATCH→PITCH)."""
    import asyncio as _asyncio
    from app.services.ai.sales_research import research as do_research
    from app.services.ai.website_auditor import audit as do_audit
    from app.services.ai.opportunity_finder import find_opportunities
    from app.services.ai.service_recommendation import recommend_services, match_case_study
    from app.services.ai.marketing_ai import generate as gen_pitch
    import dataclasses

    db = SyncSession()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.workspace_id == workspace_id).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return

        campaign = db.query(Campaign).filter(Campaign.id == lead.campaign_id).first()
        if not campaign:
            return

        async def _run():
            audit = None
            if lead.website:
                try:
                    from app.services.ai.website_auditor import audit as do_audit_inner
                    audit = await do_audit_inner(lead.website)
                except Exception as exc:
                    logger.warning(f"Website audit failed for {lead.name}: {exc}")

            brief = await do_research(
                name=lead.name, industry=lead.category or campaign.industry,
                address=lead.address, website=lead.website, rating=lead.rating,
                review_count=lead.review_count, phone=lead.phone, email=lead.email,
                score=lead.score, website_audit=audit,
            )
            opps = await find_opportunities(
                {"name": lead.name, "website": lead.website, "rating": lead.rating, "review_count": lead.review_count, "email": lead.email},
                brief, audit,
            )
            services = await recommend_services(opps, brief)
            cs = await match_case_study(opps, brief)
            pitch = await gen_pitch(
                business_name=lead.name, industry=lead.category or campaign.industry,
                address=lead.address, rating=lead.rating, has_website=lead.has_website,
                your_service=campaign.your_service, content_style=campaign.content_style,
                language=campaign.language, score=lead.score,
                sales_brief=brief, case_study=cs, top_service=services[0] if services else None,
            )
            return audit, brief, opps, services, cs, pitch

        loop = _asyncio.new_event_loop()
        audit, brief, opps, services, cs, pitch = loop.run_until_complete(_run())
        loop.close()

        lead.sales_brief = json.dumps(dataclasses.asdict(brief))
        lead.website_audit = json.dumps(dataclasses.asdict(audit)) if audit else None
        lead.opportunities = json.dumps([dataclasses.asdict(o) for o in opps])
        lead.matched_services = json.dumps([dataclasses.asdict(s) for s in services])
        lead.matched_case_study = json.dumps(dataclasses.asdict(cs)) if cs else None
        lead.researched_at = datetime.now(timezone.utc)
        lead.marketing_content = json.dumps({
            "email": {"subject": pitch.email_subject, "body": pitch.email_body},
            "whatsapp": pitch.whatsapp, "instagram": pitch.instagram,
            "linkedin": {"connectionNote": pitch.linkedin_note},
            "coldCall": {"opening": pitch.cold_call_opening},
            "pitchAngle": pitch.pitch_angle, "proofPoint": pitch.proof_point,
        })
        lead.pitch_generated_at = datetime.now(timezone.utc)
        lead.pipeline_stage = "PITCH"
        db.commit()
        logger.info(f"Lead {lead_id} research complete. Stage: PITCH")

    except Exception as exc:
        logger.error(f"research_lead_task failed for {lead_id}: {exc}")
    finally:
        db.close()
