from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database.connection import Base, engine
from app.models import user, trip, expense, journal, wishlist
from app.routes import (
    auth, trips, expenses, chat,
    packing, transit, safety, weather,
    recommendations, journal as journal_router,
    wishlist as wishlist_router, analytics, companion, currency,
    consensus, intelligence, health_safety, ai_suggestions
)
from app.routes.recommendations import ai_rec_router

app = FastAPI(title="WanderWise API", version="2.0.0")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# v2 Routes
app.include_router(consensus.router)
app.include_router(intelligence.router)
app.include_router(health_safety.router)
app.include_router(ai_suggestions.router)

# v2.7 AI Recommendation Engine
app.include_router(ai_rec_router)


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
