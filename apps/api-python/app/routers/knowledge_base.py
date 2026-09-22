from __future__ import annotations
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.knowledge import KnowledgeBaseItem, CaseStudy

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


def _kb_out(item: KnowledgeBaseItem) -> dict:
    return {
        "id": item.id,
        "type": item.item_type,
        "title": item.title,
        "description": item.description,
        "tags": _safe_json(item.tags),
        "metadata": _safe_json(item.extra),
        "active": item.active,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
    }


def _cs_out(cs: CaseStudy) -> dict:
    return {
        "id": cs.id,
        "title": cs.title,
        "clientIndustry": cs.client_industry,
        "problem": cs.problem,
        "solution": cs.solution,
        "outcome": cs.outcome,
        "techStack": _safe_json(cs.tech_stack),
        "tags": _safe_json(cs.tags),
        "featured": cs.featured,
        "createdAt": cs.created_at.isoformat() if cs.created_at else None,
    }


def _safe_json(val: object) -> object:
    if not val:
        return []
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return val


class CreateKBItemRequest(BaseModel):
    type: str
    title: str
    description: str
    tags: list[str] = []
    metadata: Optional[dict] = None


class CreateCaseStudyRequest(BaseModel):
    title: str
    client_industry: str
    problem: str
    solution: str
    outcome: str
    tech_stack: list[str] = []
    tags: list[str] = []
    featured: bool = False


# ── KB Items ──────────────────────────────────────────────────────────────────

@router.get("/items")
async def list_items(
    type: Optional[str] = None,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(KnowledgeBaseItem).where(
        KnowledgeBaseItem.workspace_id == current.workspace_id,
        KnowledgeBaseItem.active == True,
    )
    if type:
        stmt = stmt.where(KnowledgeBaseItem.item_type == type)
    stmt = stmt.order_by(KnowledgeBaseItem.item_type, KnowledgeBaseItem.title)
    result = await db.execute(stmt)
    return [_kb_out(i) for i in result.scalars().all()]


@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.id == item_id,
            KnowledgeBaseItem.workspace_id == current.workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    return _kb_out(item)


@router.post("/items", status_code=201)
async def create_item(
    body: CreateKBItemRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = KnowledgeBaseItem(
        id=new_id(),
        item_type=body.type,
        title=body.title,
        description=body.description,
        tags=json.dumps(body.tags),
        extra=json.dumps(body.metadata) if body.metadata else None,
        workspace_id=current.workspace_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _kb_out(item)


@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    body: dict,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.id == item_id,
            KnowledgeBaseItem.workspace_id == current.workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")

    for k, v in body.items():
        if k == "type":     item.item_type = v
        elif k == "tags":   item.tags = json.dumps(v)
        elif k == "metadata": item.extra = json.dumps(v)
        elif hasattr(item, k): setattr(item, k, v)

    await db.commit()
    await db.refresh(item)
    return _kb_out(item)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.id == item_id,
            KnowledgeBaseItem.workspace_id == current.workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    await db.delete(item)
    await db.commit()


@router.post("/seed")
async def seed_services(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.ai.service_recommendation import EZITECH_SERVICES
    result = await db.execute(
        select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.workspace_id == current.workspace_id,
            KnowledgeBaseItem.item_type == "service",
        ).limit(1)
    )
    if result.scalar_one_or_none():
        return {"seeded": 0, "message": "Services already exist"}

    items = [
        KnowledgeBaseItem(
            id=new_id(), item_type="service",
            title=svc["name"],
            description=f"Professional {svc['name']} service tailored to your business.",
            tags=json.dumps(svc["industries"]),
            workspace_id=current.workspace_id,
        )
        for svc in EZITECH_SERVICES
    ]
    db.add_all(items)
    await db.commit()
    return {"seeded": len(items)}


# ── Case Studies ─────────────────────────────────────────────────────────────

@router.get("/case-studies")
async def list_case_studies(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseStudy)
        .where(CaseStudy.workspace_id == current.workspace_id)
        .order_by(CaseStudy.featured.desc(), CaseStudy.created_at.desc())
    )
    return [_cs_out(cs) for cs in result.scalars().all()]


@router.post("/case-studies", status_code=201)
async def create_case_study(
    body: CreateCaseStudyRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cs = CaseStudy(
        id=new_id(), title=body.title, client_industry=body.client_industry,
        problem=body.problem, solution=body.solution, outcome=body.outcome,
        tech_stack=json.dumps(body.tech_stack), tags=json.dumps(body.tags),
        featured=body.featured, workspace_id=current.workspace_id,
    )
    db.add(cs)
    await db.commit()
    await db.refresh(cs)
    return _cs_out(cs)


@router.put("/case-studies/{cs_id}")
async def update_case_study(
    cs_id: str,
    body: dict,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseStudy).where(CaseStudy.id == cs_id, CaseStudy.workspace_id == current.workspace_id)
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise HTTPException(404, "Case study not found")
    for k, v in body.items():
        if k in ("tech_stack", "tags"): v = json.dumps(v)
        if hasattr(cs, k): setattr(cs, k, v)
    await db.commit()
    await db.refresh(cs)
    return _cs_out(cs)


@router.delete("/case-studies/{cs_id}", status_code=204)
async def delete_case_study(
    cs_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseStudy).where(CaseStudy.id == cs_id, CaseStudy.workspace_id == current.workspace_id)
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise HTTPException(404, "Case study not found")
    await db.delete(cs)
    await db.commit()


@router.get("/context")
async def context_bundle(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc_r = await db.execute(
        select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.workspace_id == current.workspace_id,
            KnowledgeBaseItem.item_type == "service",
            KnowledgeBaseItem.active == True,
        )
    )
    cs_r = await db.execute(
        select(CaseStudy)
        .where(CaseStudy.workspace_id == current.workspace_id)
        .order_by(CaseStudy.featured.desc())
        .limit(10)
    )
    return {
        "services": [_kb_out(i) for i in svc_r.scalars().all()],
        "caseStudies": [_cs_out(cs) for cs in cs_r.scalars().all()],
    }
