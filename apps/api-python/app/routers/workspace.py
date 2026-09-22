from __future__ import annotations
import hashlib
import json
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.ids import new_id
from app.core.security import get_current_user, CurrentUser
from app.models.workspace import Workspace, WorkspaceMember
from app.models.integration import Integration, ApiKey

router = APIRouter(prefix="/workspace", tags=["Workspace"])


@router.get("")
async def get_workspace(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ws = await db.get(Workspace, current.workspace_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return {"id": ws.id, "name": ws.name, "slug": ws.slug, "plan": ws.plan, "logo": ws.logo}


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None


@router.patch("")
async def update_workspace(
    body: UpdateWorkspaceRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await db.get(Workspace, current.workspace_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if body.name is not None: ws.name = body.name
    if body.logo is not None: ws.logo = body.logo
    await db.commit()
    return {"id": ws.id, "name": ws.name, "slug": ws.slug, "plan": ws.plan, "logo": ws.logo}


@router.get("/members")
async def list_members(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == current.workspace_id)
        .options(selectinload(WorkspaceMember.user))
    )
    members = result.scalars().all()
    return [
        {
            "id": m.id, "role": m.role, "userId": m.user_id,
            "user": {"name": m.user.name, "email": m.user.email} if m.user else None,
        }
        for m in members
    ]


# ── Integrations ──────────────────────────────────────────────────────────────

class CreateIntegrationRequest(BaseModel):
    type: str
    name: str
    config: dict
    enabled: bool = True


@router.get("/integrations")
async def list_integrations(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Integration).where(Integration.workspace_id == current.workspace_id)
    )
    return [{"id": i.id, "type": i.int_type, "name": i.name, "enabled": i.enabled} for i in result.scalars().all()]


@router.post("/integrations", status_code=201)
async def create_integration(
    body: CreateIntegrationRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    integration = Integration(
        id=new_id(), int_type=body.type, name=body.name,
        config=json.dumps(body.config), enabled=body.enabled,
        workspace_id=current.workspace_id,
    )
    db.add(integration)
    await db.commit()
    return {"id": integration.id, "type": integration.int_type, "name": integration.name, "enabled": integration.enabled}


# ── API Keys ──────────────────────────────────────────────────────────────────

@router.post("/api-keys", status_code=201)
async def create_api_key(
    name: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    key = ApiKey(
        id=new_id(), name=name, key_hash=key_hash,
        key_prefix=key_prefix, workspace_id=current.workspace_id,
    )
    db.add(key)
    await db.commit()
    return {"id": key.id, "name": key.name, "key": raw_key, "prefix": key_prefix}


@router.get("/api-keys")
async def list_api_keys(current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiKey).where(ApiKey.workspace_id == current.workspace_id)
    )
    return [
        {"id": k.id, "name": k.name, "prefix": k.key_prefix,
         "lastUsedAt": k.last_used_at.isoformat() if k.last_used_at else None}
        for k in result.scalars().all()
    ]


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.workspace_id == current.workspace_id)
    )
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404, "API key not found")
    await db.delete(k)
    await db.commit()
