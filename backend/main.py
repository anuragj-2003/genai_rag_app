"""
main.py — FastAPI application entry point.

Features:
- All routes under /api/v1/
- CORS locked to frontend origin (env var)
- Generic error handler (debug=False)
- Sentry free-tier integration
- APScheduler: nightly backup + weekly data retention
- slowapi rate limit state attached to app
"""

import os
import sys
import json
import logging

# Ensure backend directory is in Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

# Sentry (non-fatal if not configured)
sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("APP_ENV", "development"),
    )

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from init_dbs import init_dbs
init_dbs()

from routers import auth, chat, documents, settings

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GenAI RAG API",
    version="2.0.0",
    debug=False,  # Never expose debug info in production
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
]
if frontend_origin not in allowed_origins:
    allowed_origins.append(frontend_origin)

# Add production domain if set separately
prod_domain = os.getenv("PRODUCTION_ORIGIN", "")
if prod_domain:
    allowed_origins.append(prod_domain)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings.router)

# ── Generic error handler ─────────────────────────────────────────────────────
logger = logging.getLogger("rag_app")


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(json.dumps({
        "event": "unhandled_exception",
        "path": str(request.url),
        "method": request.method,
        "error": str(exc),
        "type": type(exc).__name__,
    }))
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again."}
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "version": "2.0.0", "api": "/api/docs"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}


# ── APScheduler: nightly backup + weekly retention ────────────────────────────
def _setup_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(timezone="UTC")

        # Nightly 02:00 UTC: gzip DB + upload to S3 (if configured)
        @scheduler.scheduled_job("cron", hour=2, minute=0)
        def nightly_backup():
            import gzip
            import shutil
            from utils.app_db import DB_PATH
            backup_path = DB_PATH + ".gz"
            try:
                with open(DB_PATH, "rb") as f_in, gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                logger.info(json.dumps({"event": "backup_created", "path": backup_path}))

                s3_bucket = os.getenv("S3_BUCKET", "")
                if s3_bucket:
                    import boto3
                    s3 = boto3.client("s3")
                    from datetime import datetime
                    key = f"backups/app_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db.gz"
                    s3.upload_file(backup_path, s3_bucket, key)
                    logger.info(json.dumps({"event": "backup_uploaded", "s3_key": key}))
            except Exception as e:
                logger.error(json.dumps({"event": "backup_failed", "error": str(e)}))

        # Weekly Sunday 03:00 UTC: purge old interactions
        @scheduler.scheduled_job("cron", day_of_week="sun", hour=3, minute=0)
        def weekly_retention():
            try:
                from utils.app_db import purge_old_interactions
                purge_old_interactions(days=90)
                logger.info(json.dumps({"event": "retention_purge_complete"}))
            except Exception as e:
                logger.error(json.dumps({"event": "retention_failed", "error": str(e)}))

        scheduler.start()
        logger.info(json.dumps({"event": "scheduler_started"}))
    except Exception as e:
        logger.warning(json.dumps({"event": "scheduler_failed", "error": str(e)}))


_setup_scheduler()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,  # Use 1 worker in reload mode
    )
