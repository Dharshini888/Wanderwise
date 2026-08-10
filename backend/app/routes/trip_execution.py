from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.trip_execution import (
    TripExecutionService,
    get_offline_emergency_data,
    track_travel_behavior,
    get_green_travel_score,
    replan_itinerary
)

router = APIRouter(prefix="/api/trip/execute", tags=["Trip Execution"])

class StartSessionReq(BaseModel):
    user_id: int
    trip_id: int
    start_date: str

class ReplanReq(BaseModel):
    reason: str
    delay_hours: int

@router.post("/start")
def start_session(data: StartSessionReq):
    return TripExecutionService.start_trip_session(data.user_id, data.trip_id, data.start_date)

@router.get("/status")
def get_status(trip_id: int):
    return TripExecutionService.monitor_trip_progress(trip_id)

@router.get("/alerts")
def get_alerts():
    return TripExecutionService.get_trip_alerts()

@router.post("/replan")
def replan(data: ReplanReq):
    return replan_itinerary(data.reason, data.delay_hours, [])

@router.post("/offline-pack")
def offline_pack():
    return TripExecutionService.generate_offline_pack()

@router.get("/emergency")
def emergency_data(destination: str = "Erode"):
    return get_offline_emergency_data(destination)

@router.post("/memory-learn")
def memory_learn(user_id: int, trip_id: int):
    return track_travel_behavior(user_id, trip_id)

@router.get("/sustainability")
def sustainability(mode: str = "Flight"):
    return get_green_travel_score(mode)
