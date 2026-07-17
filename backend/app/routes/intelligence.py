from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.trip import Trip
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

class MoodCheckIn(BaseModel):
    trip_id: int
    mood: str # Energetic / Tired / Overwhelmed / Adventurous

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

    # Placeholder logic for dynamic replanning based on mood
    replanned_suggestion = ""
    if check_in.mood == "Tired":
        replanned_suggestion = "Swapped afternoon hike for a café visit."
    elif check_in.mood == "Energetic":
        replanned_suggestion = "Added an optional sunset walking tour."
    
    return {
        "message": "Mood recorded and itinerary adjusted.",
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

    # This would normally query flights, transit, and hotel types
    # For now, return a placeholder based on the DB field or default to an estimate.
    footprint = trip.carbon_footprint if trip.carbon_footprint else 1.2
    
    return {
        "trip_id": trip.id,
        "carbon_footprint_tonnes": footprint,
        "greener_option": "Take a train instead of the short-haul flight to save 0.7 tonnes."
    }
