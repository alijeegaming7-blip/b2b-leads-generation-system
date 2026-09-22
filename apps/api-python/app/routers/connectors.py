"""
Connectors API - Manage and configure data source connectors.

Connector state is persisted in the workspace settings so it survives
server restarts.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from ..scrapers import connector_manager
from ..core.security import get_current_user, CurrentUser
from ..core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connectors", tags=["connectors"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class ConnectorInfo(BaseModel):
    name: str
    display_name: str
    requires_api_key: bool
    is_enabled: bool
    is_configured: bool


class ConnectorConfig(BaseModel):
    enabled: bool
    api_key: Optional[str] = None


class TestSearchRequest(BaseModel):
    connector_name: str
    query: str
    location: str
    limit: int = 5


# ── Persistence helpers ────────────────────────────────────────────────────────

async def _load_connector_settings(workspace_id: str, db: AsyncSession) -> dict:
    """Load saved connector configs from the workspace integrations table."""
    try:
        from ..models.integration import Integration
        result = await db.execute(
            select(Integration).where(
                Integration.workspace_id == workspace_id,
                Integration.type == "connector_config",
            )
        )
        row = result.scalar_one_or_none()
        if row and row.config:
            try:
                return json.loads(row.config)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Could not load connector settings: {e}")
    return {}


async def _save_connector_settings(workspace_id: str, settings: dict, db: AsyncSession) -> None:
    """Persist connector configs to the workspace integrations table."""
    try:
        from ..models.integration import Integration
        from ..core.ids import new_id
        result = await db.execute(
            select(Integration).where(
                Integration.workspace_id == workspace_id,
                Integration.type == "connector_config",
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.config = json.dumps(settings)
        else:
            db.add(Integration(
                id=new_id(),
                name="Connector Config",
                type="connector_config",
                config=json.dumps(settings),
                workspace_id=workspace_id,
            ))
        await db.commit()
    except Exception as e:
        logger.warning(f"Could not save connector settings: {e}")


def _apply_settings_to_manager(settings: dict) -> None:
    """Apply saved settings dict to the live connector_manager."""
    for name, cfg in settings.items():
        c = connector_manager.get_connector(name)
        if not c:
            continue
        if cfg.get("enabled"):
            c.enable()
        else:
            c.disable()
        if cfg.get("api_key"):
            c.api_key = cfg["api_key"]


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ConnectorInfo])
async def list_connectors(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available connectors, applying any saved settings first."""
    # Re-apply saved settings on every list call
    settings = await _load_connector_settings(user.workspace_id, db)
    if settings:
        _apply_settings_to_manager(settings)

    # Demo mode: only Google Maps allowed
    from app.core.demo import is_demo
    demo_active = is_demo()

    result = []
    for c in connector_manager.list_connectors():
        connector = connector_manager.get_connector(c["name"])
        is_configured = True
        if connector and connector.requires_api_key:
            is_configured = bool(connector.api_key)
        
        # In demo mode, force-disable all except google_maps
        effective_enabled = c["is_enabled"]
        if demo_active and c["name"] != "google_maps":
            effective_enabled = False

        result.append(ConnectorInfo(
            name=c["name"],
            display_name=c["display_name"] + (" 🔒 Demo" if demo_active and c["name"] != "google_maps" else ""),
            requires_api_key=c["requires_api_key"],
            is_enabled=effective_enabled,
            is_configured=is_configured if not demo_active or c["name"] == "google_maps" else False,
        ))
    return result


@router.put("/{connector_name}/config")
async def update_connector_config(
    connector_name: str,
    config: ConnectorConfig,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a connector and optionally set its API key. Persists to DB."""
    connector = connector_manager.get_connector(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector '{connector_name}' not found")

    # Apply to live manager
    if config.enabled:
        connector.enable()
    else:
        connector.disable()

    if config.api_key is not None:
        connector.api_key = config.api_key.strip() if config.api_key else None

    # Validate
    if connector.is_enabled and connector.requires_api_key and not connector.api_key:
        # Don't fail — just return warning
        pass

    # Persist
    settings = await _load_connector_settings(user.workspace_id, db)
    settings[connector_name] = {
        "enabled": connector.is_enabled,
        "api_key": connector.api_key,
    }
    await _save_connector_settings(user.workspace_id, settings, db)

    return {
        "success": True,
        "connector": connector_name,
        "is_enabled": connector.is_enabled,
        "is_configured": bool(not connector.requires_api_key or connector.api_key),
    }


@router.post("/test")
async def test_connector(
    request: TestSearchRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a connector with a live search — returns up to `limit` results."""
    connector = connector_manager.get_connector(request.connector_name)
    if not connector:
        raise HTTPException(404, f"Connector '{request.connector_name}' not found")
    if not connector.is_enabled:
        raise HTTPException(400, f"Connector '{request.connector_name}' is disabled")
    if connector.requires_api_key and not connector.api_key:
        raise HTTPException(400, f"Connector '{request.connector_name}' needs an API key")

    try:
        results = await connector.search(
            query=request.query,
            location=request.location,
            limit=request.limit,
        )
        return {
            "success": True,
            "connector": request.connector_name,
            "results_count": len(results),
            "results": [
                {
                    "name":         r.name,
                    "phone":        r.phone,
                    "email":        r.email,
                    "website":      r.website,
                    "address":      r.address,
                    "rating":       r.rating,
                    "review_count": r.review_count,
                    "social_media": (r.raw_data or {}).get("social_media", {}),
                }
                for r in results
            ],
        }
    except Exception as e:
        logger.error(f"Connector test failed: {e}")
        raise HTTPException(500, f"Test failed: {e}")


@router.post("/search-all")
async def search_all_connectors(
    query: str,
    location: str,
    limit_per_connector: int = 10,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search all enabled+configured connectors in parallel."""
    # Reload saved settings
    settings = await _load_connector_settings(user.workspace_id, db)
    if settings:
        _apply_settings_to_manager(settings)

    try:
        raw = await connector_manager.search_all(
            query=query,
            location=location,
            limit_per_connector=limit_per_connector,
            only_enabled=True,
        )
        output = {}
        total = 0
        for cname, cresults in raw.items():
            output[cname] = [
                {
                    "name":         r.name,
                    "phone":        r.phone,
                    "email":        r.email,
                    "website":      r.website,
                    "address":      r.address,
                    "city":         r.city,
                    "rating":       r.rating,
                    "review_count": r.review_count,
                    "social_media": (r.raw_data or {}).get("social_media", {}),
                }
                for r in cresults
            ]
            total += len(cresults)
        return {
            "success": True,
            "query": query,
            "location": location,
            "total_results": total,
            "results_by_connector": output,
        }
    except Exception as e:
        logger.error(f"search-all failed: {e}")
        raise HTTPException(500, str(e))
