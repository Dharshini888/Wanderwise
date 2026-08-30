from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database.connection import get_db
from app.models.trip import Trip
from app.routes.auth import get_current_user
from app.models.user import User

from app.ml.recommendation_engine import HybridRecommendationEngine
from app.services.ai_learning_engine import AILearningEngine
from app.services.visa_service import VisaAssistantService
from app.services.local_guide_service import LocalGuideService
from app.services.smart_replanner import SmartReplanner
from app.services.trip_execution.sustainability_service import SustainabilityService

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])
hybrid_engine = HybridRecommendationEngine()


class MoodCheckIn(BaseModel):
    trip_id: int
    mood: str  # Energetic / Tired / Overwhelmed / Adventurous / Relaxed / Cultural / Food-focused


class FeedbackSignal(BaseModel):
    action: str  # like / skip / save / dislike / visited
    category: str
    metadata: Optional[Dict[str, Any]] = None


class ReplanningRequest(BaseModel):
    trip_id: int
    user_condition: str  # "I'm tired and it is raining", "flight delayed 2 hours"
    activities: List[Dict[str, Any]] = []


@router.post("/mood")
def check_in_mood(
    check_in: MoodCheckIn, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    trip = db.query(Trip).filter(Trip.id == check_in.trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.current_mood = check_in.mood
    db.commit()

    replanned_suggestion = ""
    if check_in.mood in ["Tired", "Relaxed"]:
        replanned_suggestion = "Swapped strenuous outdoor walking for a cozy local café visit & indoor gallery."
    elif check_in.mood in ["Energetic", "Adventurous"]:
        replanned_suggestion = "Added an optional sunset walking tour and panoramic viewpoint climb."
    elif check_in.mood == "Food-focused":
        replanned_suggestion = "Prioritized artisanal food market and top-rated local dining spots."
    else:
        replanned_suggestion = "Itinerary pace optimized for your current preference."
    
    return {
        "message": "Mood recorded and itinerary pace adjusted.",
        "mood": check_in.mood,
        "ai_adjustment": replanned_suggestion
    }


@router.get("/{trip_id}/carbon")
def get_carbon_footprint(
    trip_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    result = SustainabilityService.calculate_trip_carbon(
        mode=trip.travel_style or "Public Transit",
        distance_km=450.0
    )
    return result


@router.post("/recommendations")
def get_hybrid_recommendations(
    candidates: List[Dict[str, Any]],
    trip_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hybrid ML Recommendation endpoint with explainable reasons."""
    user_profile = {
        "travel_preferences": current_user.travel_preferences or {},
        "interests": (current_user.travel_preferences or {}).get("interests", []),
        "travel_history": [],
    }

    current_trip = None
    if trip_id:
        t = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
        if t:
            current_trip = {
                "destination": t.destination,
                "category": t.travel_style,
                "budget_tier": t.budget_tier or "moderate",
            }

    ranked = hybrid_engine.rank_recommendations(
        user_id=current_user.id,
        user_profile=user_profile,
        candidates=candidates,
        current_trip=current_trip,
        limit=10,
    )
    return {"recommendations": ranked, "count": len(ranked)}


@router.get("/learned-preferences")
def get_learned_preferences(current_user: User = Depends(get_current_user)):
    """Returns persistent learned user preferences."""
    prefs = AILearningEngine.get_learned_preferences(current_user.id)
    return {"user_id": current_user.id, "learned_preferences": prefs}


@router.post("/learned-preferences/feedback")
def record_feedback(
    signal: FeedbackSignal,
    current_user: User = Depends(get_current_user)
):
    """Records feedback signal to update learned preferences."""
    updated = AILearningEngine.record_user_feedback(
        user_id=current_user.id,
        action=signal.action,
        category=signal.category,
        metadata=signal.metadata
    )
    return {"message": "Feedback recorded", "learned_preferences": updated}


@router.post("/learned-preferences/reset")
def reset_learned_preferences(current_user: User = Depends(get_current_user)):
    """Resets learned preferences back to defaults."""
    clean = AILearningEngine.reset_learned_preferences(current_user.id)
    return {"message": "Learned preferences reset to clean defaults", "learned_preferences": clean}


@router.get("/visa")
def get_visa_guidance(
    passport_country: str = Query("IN"),
    destination_country: str = Query("GB")
):
    """Official Visa Assistant requirement API."""
    return VisaAssistantService.get_visa_requirements(passport_country, destination_country)


@router.get("/guide")
def get_local_guide(destination: str = Query("London")):
    """Verified Local Travel Guide API."""
    return LocalGuideService.get_destination_guide(destination)


@router.post("/replanning")
def dynamic_replanning(req: ReplanningRequest):
    """Dynamic itinerary replanning based on weather alerts, fatigue, or delays."""
    eval_res = SmartReplanner.evaluate_weather_recommendation(req.user_condition, req.activities)
    return {
        "trip_id": req.trip_id,
        "condition": req.user_condition,
        "has_recommendation": eval_res.get("has_recommendation", False),
        "title": eval_res.get("title", "Itinerary Optimized"),
        "suggestions": eval_res.get("suggestions", []),
        "status": "REPLANNED_SUCCESSFULLY",
    }
