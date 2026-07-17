from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from app.database.connection import get_db
from app.models.trip import Trip
from app.services.ai_service import generate_itinerary, replan_itinerary

router = APIRouter(prefix="/api/trips", tags=["Trips"])


class TripCreate(BaseModel):
    user_id: int
    destination: str
    start_date: date
    end_date: date
    budget: float
    travel_type: str = "leisure"
    travel_style: str = "solo"
    interests: str = "sightseeing"
    group_size: int = 1
    currency: str = "USD"


@router.post("/create")
def create_trip(data: TripCreate, db: Session = Depends(get_db)):
    days = (data.end_date - data.start_date).days + 1

    itinerary = generate_itinerary(
        destination=data.destination,
        days=days,
        budget=data.budget,
        interests=data.interests,
        travel_type=data.travel_type,
        group_size=data.group_size,
        currency=data.currency,
    )

    trip = Trip(
        user_id=data.user_id,
        destination=data.destination,
        start_date=data.start_date,
        end_date=data.end_date,
        budget=data.budget,
        currency=data.currency,
        travel_type=data.travel_type,
        travel_style=data.travel_style,
        group_size=data.group_size,
        interests=data.interests,
        itinerary=itinerary,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/{trip_id}")
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/user/{user_id}")
def get_user_trips(user_id: int, db: Session = Depends(get_db)):
    return db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.id.desc()).all()


@router.delete("/{trip_id}")
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()
    return {"message": "Trip deleted"}

class ReplanRequest(BaseModel):
    modification_request: str

@router.post("/{trip_id}/replan")
def replan_trip(trip_id: int, data: ReplanRequest, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    new_itinerary = replan_itinerary(trip.itinerary, data.modification_request)
    trip.itinerary = new_itinerary
    db.commit()
    db.refresh(trip)
    return trip
