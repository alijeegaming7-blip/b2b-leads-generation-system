"""
Health check endpoint for monitoring and load balancers.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint returning service status and dependencies.
    
    Returns 200 if healthy, 503 if unhealthy.
    """
    start_time = time.time()
    checks = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        checks["checks"]["database"] = {"status": "up", "latency_ms": round((time.time() - start_time) * 1000, 2)}
    except Exception as e:
        logger.error(f"Health check: database error: {e}")
        checks["status"] = "unhealthy"
        checks["checks"]["database"] = {"status": "down", "error": str(e)}
    
    # Check agent coordinator
    try:
        from app.routers.agents import _coordinator
        checks["checks"]["coordinator"] = {
            "status": _coordinator.status.value,
            "queue_depth": _coordinator._processing_queue.qsize(),
            "total_processed": _coordinator.total_verified
        }
    except Exception as e:
        logger.error(f"Health check: coordinator error: {e}")
        checks["checks"]["coordinator"] = {"status": "error", "error": str(e)}
    
    checks["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    if checks["status"] == "unhealthy":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=checks)
    
    return checks


@router.get("/health/liveness")
async def liveness():
    """Kubernetes liveness probe - always returns 200 if service is running."""
    return {"status": "alive"}


@router.get("/health/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe - returns 200 only if service can handle requests."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": str(e)})
