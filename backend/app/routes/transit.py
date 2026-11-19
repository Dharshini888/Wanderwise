import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.transit.transit_orchestrator import TransitOrchestrator
from ..services.transit.providers.railradar_provider import RailRadarProvider
from ..services.transit.providers.flight_provider import FlightProvider

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
    if not data.origin or not data.origin.strip():
        raise HTTPException(status_code=400, detail="Origin location is required.")
    if not data.destination or not data.destination.strip():
        raise HTTPException(status_code=400, detail="Destination location is required.")

    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    acc = data.origin_accuracy_m if data.origin_accuracy_m is not None else data.gps_accuracy
    d_lat = data.dest_lat if data.dest_lat is not None else data.destination_lat
    d_lon = data.dest_lon if data.dest_lon is not None else data.destination_lon

    # Coordinate range validation
    if data.origin_lat is not None and not (-90.0 <= data.origin_lat <= 90.0):
        raise HTTPException(status_code=400, detail="Origin latitude must be between -90 and 90.")
    if data.origin_lon is not None and not (-180.0 <= data.origin_lon <= 180.0):
        raise HTTPException(status_code=400, detail="Origin longitude must be between -180 and 180.")
    if d_lat is not None and not (-90.0 <= d_lat <= 90.0):
        raise HTTPException(status_code=400, detail="Destination latitude must be between -90 and 90.")
    if d_lon is not None and not (-180.0 <= d_lon <= 180.0):
        raise HTTPException(status_code=400, detail="Destination longitude must be between -180 and 180.")

    logger.info(f"[TRANSIT] Route request received: {data.origin} -> {data.destination} (Coords: {data.origin_lat},{data.origin_lon} -> {d_lat},{d_lon}, Dep: {data.departure_type} / {data.departure_time})")

    try:
        plan = TransitOrchestrator.get_transit_plan(
            origin=data.origin.strip(),
            destination=data.destination.strip(),
            origin_source=data.origin_source,
            origin_lat=data.origin_lat,
            origin_lon=data.origin_lon,
            dest_lat=d_lat,
            dest_lon=d_lon,
            gps_accuracy=acc,
            origin_accuracy_m=acc,
            preferred_mode=data.preferred_mode or "fastest",
            budget=data.budget,
            budget_currency=data.budget_currency,
            date=data.date or "Today",
            departure_type=data.departure_type or "now",
            departure_time=data.departure_time,
            request_id=req_id,
        )

        if plan.get("status") == "LOCATION_UNRESOLVED":
            raise HTTPException(
                status_code=400,
                detail=plan.get("message") or f"Unable to resolve coordinates for '{data.origin}' or '{data.destination}'."
            )

        if plan.get("status") in ("ROUTING_ERROR", "ERROR"):
            raise HTTPException(
                status_code=502,
                detail=plan.get("message") or "Transit providers failed to calculate a verified route."
            )

        return plan
    except HTTPException:
        raise
    except TimeoutError as te:
        logger.error(f"[TRANSIT] Timeout: {te}")
        raise HTTPException(status_code=504, detail="Transit routing request timed out while contacting upstream providers.")
    except Exception as e:
        logger.exception(f"[TRANSIT] Routing pipeline error: {e}")
        err_str = str(e).lower()
        if "timeout" in err_str:
            raise HTTPException(status_code=504, detail="Transit routing request timed out.")
        if "connection" in err_str or "unreachable" in err_str:
            raise HTTPException(status_code=503, detail="Transit service temporarily unavailable due to network connectivity.")
        raise HTTPException(status_code=500, detail=f"Transit planning encountered an unexpected error: {str(e)}")


@router.post("/intelligence")
def get_intelligence(data: TransitRequest):
    if not data.origin or not data.origin.strip():
        raise HTTPException(status_code=400, detail="Origin location is required.")
    if not data.destination or not data.destination.strip():
        raise HTTPException(status_code=400, detail="Destination location is required.")

    req_id = data.request_id or f"req_{uuid.uuid4().hex[:12]}"
    acc = data.origin_accuracy_m if data.origin_accuracy_m is not None else data.gps_accuracy
    d_lat = data.dest_lat if data.dest_lat is not None else data.destination_lat
    d_lon = data.dest_lon if data.dest_lon is not None else data.destination_lon

    try:
        plan = TransitOrchestrator.get_transit_plan(
            origin=data.origin.strip(),
            destination=data.destination.strip(),
            origin_source=data.origin_source,
            origin_lat=data.origin_lat,
            origin_lon=data.origin_lon,
            dest_lat=d_lat,
            dest_lon=d_lon,
            gps_accuracy=acc,
            origin_accuracy_m=acc,
            preferred_mode=data.preferred_mode or "fastest",
            budget=data.budget,
            budget_currency=data.budget_currency,
            date=data.date or "Today",
            departure_type=data.departure_type or "now",
            departure_time=data.departure_time,
            request_id=req_id,
        )

        if plan.get("status") == "LOCATION_UNRESOLVED":
            raise HTTPException(
                status_code=400,
                detail=plan.get("message") or f"Unable to resolve coordinates for '{data.origin}' or '{data.destination}'."
            )

        return plan
    except HTTPException:
        raise
    except TimeoutError as te:
        logger.error(f"[TRANSIT] Timeout: {te}")
        raise HTTPException(status_code=504, detail="Transit intelligence request timed out.")
    except Exception as e:
        logger.exception(f"[TRANSIT] Intelligence pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Transit intelligence encountered an error: {str(e)}")


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
def get_debug_providers(probe: bool = True):
    rr_health = RailRadarProvider.health_check()
    flight_health = FlightProvider.health_check(probe_network=probe)
    return {
        "transitous": {"configured": True},
        "transitland": {"configured": bool(os.getenv("TRANSITLAND_API_KEY"))},
        "navitia": {"configured": bool(os.getenv("NAVITIA_API_KEY"))},
        "railradar": rr_health,
        "flight_provider": flight_health,
        "osrm": {"configured": True},
        "gemini": {"configured": bool(os.getenv("GEMINI_API_KEY"))},
    }


@router.get("/debug/flight")
def get_debug_flight(test_cjb: bool = False, test_kix: bool = False):
    health = FlightProvider.health_check(probe_network=True)
    res = {"health": health}
    if test_cjb:
        res["cjb_test"] = FlightProvider.test_airport_code("CJB")
    if test_kix:
        res["kix_test"] = FlightProvider.test_airport_code("KIX")
    return res


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
