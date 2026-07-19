from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.audit import ensure_indexes as ensure_audit_indexes
from app.core.config import settings
from app.core.events import subscriber_loop
from app.core.jobs import ensure_indexes as ensure_agent_task_indexes
from app.core.mongo import seed_mongo
from app.core.notifications import ensure_indexes as ensure_notification_indexes
from app.core.regions_db import seed_and_refresh as seed_regions
from app.core.token_tracking import ensure_indexes as ensure_token_indexes
from app.core.documents import ensure_indexes as ensure_doc_indexes
from app.core.notes import ensure_indexes as ensure_notes_indexes
from app.routers import (
    agent_router,
    agent_tasks_router,
    audit_router,
    auth_router,
    chats_router,
    departments_router,
    google_router,
    health_router,
    notifications_router,
    settings_router,
    tasks_router,
    tools_router,
    ws_router,
    notifications_ws_router,
)

# RATE LIMITING
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# FASTAPI APP
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs" if settings.is_debug else None,
    redoc_url="/api/redoc" if settings.is_debug else None,
)

app.state.limiter = limiter


# EXCEPTION HANDLERS
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please try again later."})

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# MIDDLEWARE
app.add_middleware(SlowAPIMiddleware)

# CORS - Allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else [settings.FRONTEND_ORIGIN],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS if hasattr(settings, 'CORS_ALLOW_CREDENTIALS') else True,
    allow_methods=settings.CORS_ALLOW_METHODS if hasattr(settings, 'CORS_ALLOW_METHODS') else ["*"],
    allow_headers=settings.CORS_ALLOW_HEADERS if hasattr(settings, 'CORS_ALLOW_HEADERS') else ["*"],
)


# ROUTERS
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(agent_router, prefix=settings.API_PREFIX)
app.include_router(agent_tasks_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(chats_router, prefix=settings.API_PREFIX)
app.include_router(departments_router, prefix=settings.API_PREFIX)
app.include_router(google_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(notifications_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)
app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(tools_router, prefix=settings.API_PREFIX)
app.include_router(ws_router, prefix=settings.API_PREFIX)
app.include_router(notifications_ws_router, prefix=settings.API_PREFIX)


# STATIC FILES (Generated files:)
import os as _os
_gen_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "generated")
_os.makedirs(_gen_dir, exist_ok=True)
app.mount("/api/static", StaticFiles(directory=_gen_dir), name="generated-files")

# STARTUP EVENT
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize everything on startup"""
    import asyncio as _asyncio
    
    print("🚀 Starting Mitsumi AI Agent Platform...")
    print(f"📡 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.is_debug}")
    
    try:
        # Connect to MongoDB
        from app.core.mongo import mongo_manager
        await mongo_manager.connect()
        print(" MongoDB connected")
        
        # Seed MongoDB with initial data
        await seed_mongo()
        print("MongoDB seeded")
        
        # Seed regions
        await seed_regions()
        print(" Regions seeded")
        
        # Ensure all indexes exist
        await ensure_audit_indexes()
        print(" Audit indexes created")
        
        await ensure_agent_task_indexes()
        print(" Agent task indexes created")
        
        await ensure_notification_indexes()
        print("Notification indexes created")
        
        await ensure_token_indexes()
        print(" Token tracking indexes created")
        
        await ensure_doc_indexes()
        print(" Document indexes created")
        
        await ensure_notes_indexes()
        print("Notes indexes created")
        
        # Start Redis→WebSocket forwarder for cross-process task events
        _asyncio.create_task(subscriber_loop())
        print(" Redis subscriber started")
        
        # Start embedded arq worker
        _asyncio.create_task(_start_embedded_worker())
        print("Embedded worker started")
        
        print("Application started successfully!")
        
    except Exception as e:
        print(f" Startup error: {e}")
        raise


# EMBEDDED WORKER
async def _start_embedded_worker() -> None:
    """Run arq worker polling loop inside the FastAPI process."""
    import asyncio
    import logging
    log = logging.getLogger("embedded_worker")

    await asyncio.sleep(3)  # Let FastAPI finish startup

    while True:
        try:
            from arq.worker import Worker
            from app.core.jobs import redis_settings as _rs, run_task
            from app.core import handlers  # noqa: F401

            worker = Worker(
                functions=[run_task],
                redis_settings=_rs(),
                max_jobs=5,
                job_timeout=900,
                keep_result_forever=False,
                handle_signals=False,  # Don't interfere with FastAPI signals
            )
            log.info("Embedded arq worker started")
            await worker.main()
        except asyncio.CancelledError:
            log.info("Worker cancelled")
            break
        except Exception as exc:
            log.error(f"Worker error: {exc}")
            await asyncio.sleep(5)

# HEALTH CHECK ENDPOINT
@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}


# READINESS CHECK ENDPOINT
@app.get("/ready")
async def readiness_check() -> dict:
    """Readiness check for load balancer - verifies MongoDB connection"""
    try:
        from app.core.mongo import get_mongo_client
        client = get_mongo_client()
        await client.admin.command('ping')
        return {"status": "ready", "mongodb": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": f"MongoDB connection failed: {str(e)}"}
        )
# CI/CD Testing
@app.get("/test-cicd")
async def test_cicd():
    """Test endpoint for CI/CD pipeline verification"""
    return {
        "status": "CI/CD is working!",
        "timestamp": "2026-07-09",
        "environment": settings.ENVIRONMENT,
        "service": settings.APP_NAME
    }

# ROOT ENDPOINT
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "operational"
    }

# SHUTDOWN EVENT (Optional)
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down application...")
    
    try:
        # Close MongoDB connection
        from app.core.mongo import mongo_manager
        await mongo_manager.disconnect()
        print("✅ MongoDB connection closed")
        
    except Exception as e:
        print(f" Error closing MongoDB: {e}")
