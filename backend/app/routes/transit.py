import os
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..services.transit.transit_orchestrator import TransitOrchestrator
from ..services.transit.providers.railradar_provider import RailRadarProvider

router = APIRouter(prefix="/api/transit", tags=["Transit"])


class TransitRequest(BaseModel):
    origin: str
    destination: str
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    gps_accuracy: Optional[float] = None
    preferred_mode: str = "fastest"
    budget: float = 5000.0
    budget_currency: str = "INR"
    date: str = "Tomorrow"
    request_id: Optional[str] = None


@router.post("/route")
def get_route(data: TransitRequest):
    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    return TransitOrchestrator.get_transit_plan(
        origin=data.origin,
        destination=data.destination,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        dest_lat=data.dest_lat,
        dest_lon=data.dest_lon,
        gps_accuracy=data.gps_accuracy,
        preferred_mode=data.preferred_mode,
        budget=data.budget,
        budget_currency=data.budget_currency,
        date=data.date,
        request_id=req_id,
    )


@router.post("/intelligence")
def get_intelligence(data: TransitRequest):
    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    return TransitOrchestrator.get_transit_plan(
        origin=data.origin,
        destination=data.destination,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        dest_lat=data.dest_lat,
        dest_lon=data.dest_lon,
        gps_accuracy=data.gps_accuracy,
        preferred_mode=data.preferred_mode,
        budget=data.budget,
        budget_currency=data.budget_currency,
        date=data.date,
        request_id=req_id,
    )


@router.get("/debug/providers")
def get_debug_providers():
    rr_health = RailRadarProvider.health_check()
    return {
        "transitous": {"configured": True},
        "navitia": {"configured": bool(os.getenv("NAVITIA_API_KEY"))},
        "railradar": rr_health,
        "flight_provider": {"configured": bool(os.getenv("FLIGHT_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY"))},
        "osrm": {"configured": True},
        "gemini": {"configured": bool(os.getenv("GEMINI_API_KEY"))},
    }


@router.get("/debug/railradar")
def get_debug_railradar():
    return RailRadarProvider.health_check()
