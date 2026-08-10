"""
transitous_service.py — WanderWise v7 Truth-First Transit Provider

Calls Transitous GTFS routing. Returns structured result with explicit
provider status so the orchestrator can distinguish:

  TRANSIT_AVAILABLE          — GTFS returned legs
  TRANSIT_NO_ROUTE           — GTFS reachable but no itineraries for this pair
  TRANSIT_NO_GTFS_COVERAGE   — GTFS reachable but no coverage (empty plan)
  TRANSIT_PROVIDER_ERROR     — Provider returned malformed / unexpected data
  TRANSIT_PROVIDER_UNAVAILABLE — DNS failure, connection error, timeout

RULE: Never return None silently. Always return a structured dict with a
'provider_status' key so callers can make truthful routing decisions.
"""

import requests
import logging
from datetime import datetime
from .models import Location, WalkLeg, TransitLeg

logger = logging.getLogger(__name__)

TRANSITOUS_URL = "https://routing.transitous.org/api"

# ─────────────────────────────────────────────
# Provider status constants
# ─────────────────────────────────────────────
TRANSIT_AVAILABLE           = "TRANSIT_AVAILABLE"
TRANSIT_NO_ROUTE            = "TRANSIT_NO_ROUTE"
TRANSIT_NO_GTFS_COVERAGE    = "TRANSIT_NO_GTFS_COVERAGE"
TRANSIT_PROVIDER_UNAVAILABLE = "TRANSIT_PROVIDER_UNAVAILABLE"
TRANSIT_PROVIDER_ERROR      = "TRANSIT_PROVIDER_ERROR"
TRANSIT_TIMEOUT             = "TRANSIT_TIMEOUT"


def _unavailable_result(status: str, error: str) -> dict:
    """Return a structured failure result — never None."""
    return {
        "provider": "Transitous",
        "provider_status": status,
        "error": error,
        "legs": [],
        "total_mins": None,
        "total_duration": None,
        "transfers": None,
        "walking_distance_km": None,
    }


def get_transitous_route(origin_lat: float, origin_lon: float,
                         dest_lat: float, dest_lon: float) -> dict:
    """
    Plan a GTFS transit journey via Transitous.

    Always returns a dict with 'provider_status'. Never raises.
    Never returns None.
    """
    try:
        resp = requests.get(
            f"{TRANSITOUS_URL}/v1/plan",
            params={
                "fromLat": origin_lat,
                "fromLon": origin_lon,
                "toLat": dest_lat,
                "toLon": dest_lon,
                "numItineraries": 3,
                "mode": "TRANSIT,WALK",
            },
            headers={"User-Agent": "WanderWise/7.0"},
            timeout=10,
        )
    except requests.exceptions.Timeout:
        logger.warning("[PROVIDER] Transitous: TIMEOUT")
        return _unavailable_result(TRANSIT_TIMEOUT, "Request timed out after 10s")
    except requests.exceptions.ConnectionError as e:
        # DNS failures, refused connections, etc.
        err_str = str(e)
        if "getaddrinfo" in err_str or "NameResolutionError" in err_str or "Failed to resolve" in err_str:
            logger.warning("[PROVIDER] Transitous: PROVIDER_UNAVAILABLE (DNS)")
            return _unavailable_result(TRANSIT_PROVIDER_UNAVAILABLE,
                                       "DNS resolution failed — provider unreachable")
        logger.warning(f"[PROVIDER] Transitous: PROVIDER_UNAVAILABLE ({err_str[:120]})")
        return _unavailable_result(TRANSIT_PROVIDER_UNAVAILABLE,
                                   f"Connection error: {err_str[:120]}")
    except Exception as e:
        logger.warning(f"[PROVIDER] Transitous: PROVIDER_ERROR ({e})")
        return _unavailable_result(TRANSIT_PROVIDER_ERROR, str(e)[:200])

    # ── HTTP error ──────────────────────────────────────
    if resp.status_code != 200:
        logger.warning(f"[PROVIDER] Transitous: HTTP {resp.status_code}")
        return _unavailable_result(TRANSIT_PROVIDER_ERROR,
                                   f"HTTP {resp.status_code}")

    # ── Parse JSON ──────────────────────────────────────
    try:
        data = resp.json()
    except Exception as e:
        logger.warning(f"[PROVIDER] Transitous: MALFORMED JSON ({e})")
        return _unavailable_result(TRANSIT_PROVIDER_ERROR, "Malformed JSON response")

    plan = data.get("plan", {})
    itineraries = plan.get("itineraries", [])

    if not itineraries:
        # Distinguish: plan key exists → provider answered, just no route
        if "plan" in data:
            logger.info("[PROVIDER] Transitous: NO_ROUTE (plan returned empty itineraries)")
            return _unavailable_result(TRANSIT_NO_ROUTE,
                                       "No transit route found between these points")
        else:
            logger.info("[PROVIDER] Transitous: NO_GTFS_COVERAGE (no plan in response)")
            return _unavailable_result(TRANSIT_NO_GTFS_COVERAGE,
                                       "No GTFS coverage for this region")

    # ── Parse best itinerary ────────────────────────────
    best = itineraries[0]
    legs = []

    for leg_data in best.get("legs", []):
        mode = leg_data.get("mode", "WALK")
        from_place = leg_data.get("from", {})
        to_place   = leg_data.get("to",   {})
        from_name  = from_place.get("name", "Unknown")
        to_name    = to_place.get("name",   "Unknown")
        duration_mins = round(leg_data.get("duration", 0) / 60)

        from_loc = Location(
            name=from_name,
            lat=from_place.get("lat"),
            lon=from_place.get("lon"),
        )
        to_loc = Location(
            name=to_name,
            lat=to_place.get("lat"),
            lon=to_place.get("lon"),
        )

        if mode == "WALK":
            legs.append(WalkLeg(
                from_loc=from_loc,
                to_loc=to_loc,
                distance_m=int(leg_data.get("distance", 0)),
                duration_minutes=duration_mins,
                provenance="GTFS/OSRM",
            ).model_dump())
        else:
            # Parse real timestamps (OTP epoch ms)
            departure_time = None
            arrival_time   = None
            time_status    = "UNAVAILABLE"

            if leg_data.get("startTime"):
                try:
                    departure_time = datetime.fromtimestamp(
                        leg_data["startTime"] / 1000.0
                    ).strftime("%H:%M")
                    time_status = "SCHEDULED"
                except Exception:
                    pass
            if leg_data.get("endTime"):
                try:
                    arrival_time = datetime.fromtimestamp(
                        leg_data["endTime"] / 1000.0
                    ).strftime("%H:%M")
                except Exception:
                    pass

            # Route identification
            route_short = ""
            route_long  = ""
            if leg_data.get("route"):
                route_short = leg_data["route"].get("shortName", "")
                route_long  = leg_data["route"].get("longName", "")
            route_name = route_short or route_long or None

            # Agency
            agency = None
            if leg_data.get("agency"):
                agency = leg_data["agency"].get("name")

            legs.append(TransitLeg(
                mode=mode,
                route_name=route_name,
                headsign=leg_data.get("headsign") or None,
                boarding_stop=from_loc,
                alighting_stop=to_loc,
                departure_time=departure_time,
                arrival_time=arrival_time,
                time_status=time_status,
                platform=None,
                platform_status="UNAVAILABLE",
                stops_count=len(leg_data.get("intermediateStops", []))
                    if leg_data.get("intermediateStops") else None,
                provenance="GTFS",
            ).model_dump() | {"agency": agency})

    total_mins = round(best.get("duration", 0) / 60)

    logger.info(
        f"[PROVIDER] Transitous: AVAILABLE — "
        f"{len(legs)} legs, {best.get('transfers', 0)} transfers, "
        f"{total_mins} min"
    )

    return {
        "provider": "Transitous",
        "provider_status": TRANSIT_AVAILABLE,
        "legs": legs,
        "total_mins": total_mins,
        "total_duration": _format_duration(best.get("duration", 0)),
        "transfers": best.get("transfers", 0),
        "walking_distance_km": round(best.get("walkDistance", 0) / 1000, 2),
        "error": None,
    }


def _format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m"
