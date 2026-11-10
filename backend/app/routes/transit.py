import os
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..services.transit.transit_orchestrator import TransitOrchestrator
from ..services.transit.providers.railradar_provider import RailRadarProvider

router = APIRouter(prefix="/api/transit", tags=["Transit"])


import logging

logger = logging.getLogger(__name__)

class TransitRequest(BaseModel):
    origin: str
    destination: str
    origin_source: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    gps_accuracy: Optional[float] = None
    origin_accuracy_m: Optional[float] = None
    preferred_mode: str = "fastest"
    budget: float = 5000.0
    budget_currency: str = "INR"
    date: str = "Today"
    departure_type: Optional[str] = "now"
    departure_time: Optional[str] = None
    request_id: Optional[str] = None


class StrategyRequest(BaseModel):
    origin: str
    destination: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    primary_mode: Optional[str] = None
    provider: Optional[str] = None
    verified: bool = True
    segments: list = []


@router.post("/route")
def get_route(data: TransitRequest):
    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    acc = data.origin_accuracy_m if data.origin_accuracy_m is not None else data.gps_accuracy
    d_lat = data.dest_lat if data.dest_lat is not None else data.destination_lat
    d_lon = data.dest_lon if data.dest_lon is not None else data.destination_lon

    logger.info(f"[TRANSIT] Route request received: {data.origin} -> {data.destination} (Coords: {data.origin_lat},{data.origin_lon} -> {d_lat},{d_lon}, Dep: {data.departure_type} / {data.departure_time})")

    return TransitOrchestrator.get_transit_plan(
        origin=data.origin,
        destination=data.destination,
        origin_source=data.origin_source,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        dest_lat=d_lat,
        dest_lon=d_lon,
        gps_accuracy=acc,
        origin_accuracy_m=acc,
        preferred_mode=data.preferred_mode,
        budget=data.budget,
        budget_currency=data.budget_currency,
        date=data.date,
        departure_type=data.departure_type or "now",
        departure_time=data.departure_time,
        request_id=req_id,
    )


@router.post("/intelligence")
def get_intelligence(data: TransitRequest):
    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    acc = data.origin_accuracy_m if data.origin_accuracy_m is not None else data.gps_accuracy
    d_lat = data.dest_lat if data.dest_lat is not None else data.destination_lat
    d_lon = data.dest_lon if data.dest_lon is not None else data.destination_lon

    return TransitOrchestrator.get_transit_plan(
        origin=data.origin,
        destination=data.destination,
        origin_source=data.origin_source,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        dest_lat=d_lat,
        dest_lon=d_lon,
        gps_accuracy=acc,
        origin_accuracy_m=acc,
        preferred_mode=data.preferred_mode,
        budget=data.budget,
        budget_currency=data.budget_currency,
        date=data.date,
        request_id=req_id,
    )


@router.post("/strategy")
def get_transit_strategy(data: StrategyRequest):
    from ..services.ai_service import _ai
    import json
    
    prompt = f"""
    Analyze the following verified transit route from {data.origin} to {data.destination}.
    Route details: Distance: {data.distance_km}km, Duration: {data.duration_minutes} minutes, Mode: {data.primary_mode}, Provider: {data.provider}.
    Segments: {json.dumps(data.segments)}
    
    Output a JSON object exactly matching this structure, strictly separating verified facts from your AI analysis:
    {{
      "verified_facts": ["string"],
      "ai_analysis": ["string"],
      "recommendations": ["string"],
      "limitations": ["string"]
    }}
    Do NOT invent fares, transit timings, station names, or distances.
    """
    
    system = "You are a transit strategy analyzer. Always return strictly valid JSON. Keep answers concise."
    
    try:
        response = _ai(prompt, system=system)
        
        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return json.loads(text.strip())
    except Exception as e:
        return {
            "verified_facts": [f"Route connects {data.origin} to {data.destination}."],
            "ai_analysis": ["Strategy analysis temporarily unavailable due to AI service load."],
            "recommendations": ["Follow the verified timeline."],
            "limitations": ["AI Analysis unavailable."]
        }


@router.get("/nearby")
def get_transit_nearby(lat: float, lon: float, radius: int = 5000):
    import urllib.request
    import json
    
    try:
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:5];
        (
          node["public_transport"="station"](around:{radius},{lat},{lon});
          node["amenity"="restaurant"](around:{radius},{lat},{lon});
          node["tourism"="hotel"](around:{radius},{lat},{lon});
        );
        out body 15;
        """
        
        req = urllib.request.Request(overpass_url, data=overpass_query.encode('utf-8'), headers={"User-Agent": "WanderWise/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            
        pois = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Location')
            if name == 'Unknown Location':
                continue
                
            cat = "Restaurant"
            if "public_transport" in tags:
                cat = "Station"
            elif "tourism" in tags:
                cat = "Hotel"
                
            pois.append({
                "name": name,
                "category": cat,
                "distance": "Nearby",
                "latitude": element.get("lat"),
                "longitude": element.get("lon")
            })
            
        if not pois:
            return {"pois": [], "message": f"No verified nearby POIs available within {radius/1000} km."}
            
        return {"pois": pois}
    except Exception as e:
        return {"pois": [], "message": f"No verified nearby POIs available within {radius/1000} km."}


@router.get("/debug/providers")
def get_debug_providers():
    rr_health = RailRadarProvider.health_check()
    return {
        "transitous": {"configured": True},
        "transitland": {"configured": bool(os.getenv("TRANSITLAND_API_KEY"))},
        "navitia": {"configured": bool(os.getenv("NAVITIA_API_KEY"))},
        "railradar": rr_health,
        "flight_provider": {"configured": bool(os.getenv("FLIGHT_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY"))},
        "osrm": {"configured": True},
        "gemini": {"configured": bool(os.getenv("GEMINI_API_KEY"))},
    }


@router.get("/debug/railradar")
def get_debug_railradar():
    return RailRadarProvider.health_check()


@router.get("/capabilities")
def get_capabilities():
    from ..services.transit.provider_registry import PROVIDER_CAPABILITIES, FALLBACK_CHAIN
    return {
        "providers": PROVIDER_CAPABILITIES,
        "fallback_chain": FALLBACK_CHAIN
    }


@router.get("/realtime/{route_id}")
def get_route_realtime(
    route_id: str,
    provider: Optional[str] = None,
    train_number: Optional[str] = None,
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
):
    from ..services.transit.live_transit_service import LiveTransitService
    return LiveTransitService.get_realtime_route_status(
        route_id=route_id,
        provider=provider,
        train_number=train_number,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
    )
