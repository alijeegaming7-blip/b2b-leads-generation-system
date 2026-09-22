"""
Ezitech B2B Sales Intelligence API
FastAPI application entry point.
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import get_settings
from app.core.rate_limit import rate_limit_middleware
from app.routers import auth, health, campaigns, leads, email, crm, knowledge_base, analytics, export, workspace, settings as settings_router, cv, agents, connectors
from app.routers import demo as demo_router

# Get settings instance
settings = get_settings()

# Structured JSON logging for production
if settings.ENV == "production":
    import json
    import sys
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Ezitech API starting — ENV={settings.ENV}")

    # Auto-create tables for SQLite dev mode
    if settings.DATABASE_URL.startswith("sqlite"):
        logger.info("SQLite mode — auto-creating tables...")
        from app.core.database import create_tables
        await create_tables()
        logger.info("Tables ready")

    # Initialize connectors
    from app.scrapers import init_connectors
    init_connectors()
    logger.info("Connectors initialized: Google Maps, Yelp, Yellow Pages, Facebook, LinkedIn, Apollo, Hunter, Clearbit, Crunchbase, Twitter, ZoomInfo")

    # Start agent event pumps
    from app.routers.agents import ensure_pumps_running
    ensure_pumps_running()
    logger.info("Agent event pumps started")

    # Install Playwright browsers if missing (non-blocking)
    try:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"], capture_output=True, timeout=120)
        logger.info("Playwright chromium ready")
    except Exception as e:
        logger.warning(f"Playwright install skipped: {e}")
    yield
    logger.info("Ezitech API shutting down")


app = FastAPI(
    title="Ezitech B2B Sales Intelligence API",
    description="Full 8-stage B2B sales pipeline: Discover → Research → Score → Match → Pitch → Outreach → Respond → Convert",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Open for demo — Railway handles security via HTTPS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_timing(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.monotonic() - t0) * 1000:.1f}ms"
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc) if settings.ENV == "development" else ""},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
API = "/api"
app.include_router(auth.router,          prefix=API)
app.include_router(campaigns.router,     prefix=API)
app.include_router(leads.router,         prefix=API)
app.include_router(email.router,         prefix=API)
app.include_router(crm.router,           prefix=API)
app.include_router(knowledge_base.router,prefix=API)
app.include_router(analytics.router,     prefix=API)
app.include_router(export.router,        prefix=API)
app.include_router(workspace.router,     prefix=API)
app.include_router(settings_router.router, prefix=API)
app.include_router(cv.router,            prefix=API)
app.include_router(agents.router,        prefix=API)
app.include_router(connectors.router,    prefix=API)
app.include_router(demo_router.router,   prefix=API)
app.include_router(health.router, prefix=API)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.ENV}


# ── Serve built React frontend (for Railway/production deployment) ────────────
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(_STATIC_DIR):
    # Serve static assets (JS/CSS/images)
    app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Catch-all: serve index.html for all non-API routes (React Router)."""
        index = os.path.join(_STATIC_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse({"message": "Frontend not built yet. Run: npm run build"}, status_code=200)
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Ezitech B2B Sales API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=settings.ENV == "development", log_level="info")





