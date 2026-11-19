import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.database.connection import Base, engine
from app.models import user, trip, expense, journal, wishlist
from app.routes import (
    auth, trips, expenses, chat,
    packing, transit, safety, weather,
    recommendations, journal as journal_router,
    wishlist as wishlist_router, analytics, companion, currency,
    consensus, intelligence, health_safety, ai_suggestions,
    notifications, activity, documents, checklist, local_guide
)
from app.routes.recommendations import ai_rec_router

logger = logging.getLogger(__name__)

app = FastAPI(title="WanderWise API", version="2.0.0")

try:
    Base.metadata.create_all(bind=engine)
except Exception as db_init_err:
    logger.warning(f"[Startup] Error initializing database tables: {db_init_err}")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

env_cors = os.getenv("CORS_ORIGINS") or os.getenv("ALLOWED_ORIGINS")
if env_cors:
    for o in env_cors.split(","):
        cleaned = o.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routes
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(trips.activities_router)

app.include_router(expenses.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(checklist.router)
app.include_router(local_guide.router)

# New feature routes
app.include_router(packing.router)
app.include_router(transit.router)
app.include_router(safety.router)
app.include_router(weather.router)
app.include_router(recommendations.router)
app.include_router(journal_router.router)
app.include_router(wishlist_router.router)
app.include_router(analytics.router)
app.include_router(companion.router)
app.include_router(currency.router)
app.include_router(notifications.router)
app.include_router(activity.router)

# v2 Routes
app.include_router(consensus.router)
app.include_router(intelligence.router)
app.include_router(health_safety.router)
app.include_router(ai_suggestions.router)

# v2.7 AI Recommendation Engine
app.include_router(ai_rec_router)

# v3.2 Trip Execution
from app.routes import trip_execution
app.include_router(trip_execution.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure unhandled exceptions still return JSON with CORS headers intact."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.get("/")
def root():
    return {"message": "WanderWise API v2.0 is running ✅"}


@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Lightweight health diagnostics endpoint.
    Reports real-time application health, database connectivity, and transit module readiness.
    """
    transit_status = "available"
    try:
        from app.services.transit.transit_orchestrator import TransitOrchestrator
    except Exception as e:
        transit_status = f"unavailable: {str(e)}"

    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"degraded: {str(e)}"

    is_healthy = db_status == "connected" and transit_status == "available"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "WanderWise Backend",
        "transit_module": transit_status,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }
