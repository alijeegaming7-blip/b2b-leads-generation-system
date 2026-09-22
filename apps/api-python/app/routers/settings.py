from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_current_user, CurrentUser
from app.core.database import get_db
from app.core.ids import new_id

router = APIRouter(prefix="/settings", tags=["Settings"])


# ── AI / config endpoints ─────────────────────────────────────────────────────

@router.get("/ai-status")
async def ai_status(current: CurrentUser = Depends(get_current_user)):
    try:
        from app.services.ai.provider import ping
        return await ping()
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.get("/config")
async def get_config(current: CurrentUser = Depends(get_current_user)):
    from app.core.config import get_settings
    s = get_settings()
    try:
        from app.services.ai.provider import AI_AVAILABLE, _MODEL
        ai_available = AI_AVAILABLE
        ai_model = _MODEL
    except Exception:
        ai_available = False
        ai_model = "none"
    return {
        "aiProvider": ai_model.split("/")[0] if ai_available else "none",
        "aiModel": ai_model if ai_available else "none",
        "aiAvailable": ai_available,
        "gmailConfigured": bool(s.GMAIL_USER and s.GMAIL_APP_PASSWORD),
        "gmailDailyLimit": s.GMAIL_DAILY_LIMIT,
        "gmailDelaySeconds": s.GMAIL_DELAY_SECONDS,
        "env": s.ENV,
        "databaseUrl": s.DATABASE_URL.split("@")[-1] if "@" in s.DATABASE_URL else s.DATABASE_URL.split("///")[-1],
    }


# ── Integrations CRUD ─────────────────────────────────────────────────────────

class IntegrationRequest(BaseModel):
    type: str          # openai | gmail | whatsapp | webhook
    name: str
    config: dict       # free-form key/value config


@router.get("/integrations")
async def list_integrations(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.integration import Integration
    result = await db.execute(
        select(Integration).where(Integration.workspace_id == current.workspace_id)
    )
    rows = result.scalars().all()
    return [{"id": r.id, "type": r.int_type, "name": r.name, "config": json.loads(r.config or "{}")} for r in rows]


@router.post("/integrations", status_code=201)
async def upsert_integration(
    body: IntegrationRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.integration import Integration
    result = await db.execute(
        select(Integration).where(
            Integration.workspace_id == current.workspace_id,
            Integration.int_type == body.type,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.name = body.name
        existing.config = json.dumps(body.config)
    else:
        existing = Integration(
            id=new_id(),
            int_type=body.type,
            name=body.name,
            config=json.dumps(body.config),
            workspace_id=current.workspace_id,
        )
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return {"id": existing.id, "type": existing.int_type, "name": existing.name, "config": json.loads(existing.config or "{}")}


@router.delete("/integrations/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.integration import Integration
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.workspace_id == current.workspace_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


# ── API Keys CRUD ─────────────────────────────────────────────────────────────

@router.get("/api-keys")
async def list_api_keys(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.integration import ApiKey
    result = await db.execute(
        select(ApiKey).where(ApiKey.workspace_id == current.workspace_id)
    )
    rows = result.scalars().all()
    return [{"id": r.id, "name": r.name, "lastUsedAt": r.last_used_at, "expiresAt": r.expires_at, "createdAt": r.created_at} for r in rows]


class CreateApiKeyRequest(BaseModel):
    name: str


@router.post("/api-keys", status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import secrets
    from app.models.integration import ApiKey
    raw_key = f"px_{secrets.token_urlsafe(32)}"
    ak = ApiKey(
        id=new_id(),
        name=body.name,
        key_hash=raw_key,
        key_prefix=raw_key[:8],
        workspace_id=current.workspace_id,
    )
    db.add(ak)
    await db.commit()
    await db.refresh(ak)
    return {"id": ak.id, "name": ak.name, "key": raw_key, "createdAt": ak.created_at}


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.integration import ApiKey
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.workspace_id == current.workspace_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
