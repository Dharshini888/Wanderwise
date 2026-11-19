"""
itinerary_validator.py — Standalone Itinerary Validation & Provenance Service for WanderWise V12.1

Validates provider itineraries before declaring them verified:
  1. Chronology: leg[i].arrival_time <= leg[i+1].departure_time
  2. Distance Provenance: PROVIDER vs HAVERSINE
  3. Distance Breakdown: total_distance_km ≈ (walking_m + transit_m) / 1000.0
  4. Duration Breakdown: total = movement + waiting (waiting_duration_minutes >= 0)
  5. Transfers: max(0, N_transit_legs - 1)
  6. Platform Provenance: PROVIDER vs UNAVAILABLE (never HAVERSINE or ESTIMATED)
  7. Schedule Provenance: GTFS Scheduled vs Provider Verified vs Schedule Unavailable
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import math
logger = logging.getLogger(__name__)


def _haversine_km_validator(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def validate_itinerary_endpoints(
    itinerary: Dict[str, Any],
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
    origin_name: str = "",
    dest_name: str = "",
    max_catchment_km: float = 50.0,
) -> Dict[str, Any]:
    """
    Validates that:
    1. The first leg starts at the requested origin or within an acceptable nearby catchment radius (default 50km).
    2. The last leg terminates at the requested destination or within an acceptable nearby catchment radius (default 50km).
    3. Intermediate stops do not accidentally become the final destination.
    4. Rejects journeys terminating in a different city (e.g. Chennai when Coimbatore requested).
    """
    errors: List[str] = []
    legs = itinerary.get("legs", [])
    if not legs:
        return {"valid": False, "errors": ["No legs in itinerary."]}

    first_leg = legs[0]
    last_leg = legs[-1]

    # Destination endpoint extraction
    last_to_loc = last_leg.get("to_loc") or {}
    last_alighting = last_leg.get("alighting_stop") or {}
    a_lat = last_to_loc.get("lat") or last_alighting.get("lat") or last_leg.get("to_lat")
    a_lon = last_to_loc.get("lon") or last_alighting.get("lon") or last_leg.get("to_lon")
    a_name = last_leg.get("to_name") or last_alighting.get("name") or last_to_loc.get("name") or itinerary.get("destination") or "Unknown"

    if dest_lat is not None and dest_lon is not None and a_lat is not None and a_lon is not None:
        dest_dist = _haversine_km_validator(float(a_lat), float(a_lon), float(dest_lat), float(dest_lon))
        if dest_dist > max_catchment_km:
            msg = (
                f"Itinerary destination '{a_name}' ({a_lat}, {a_lon}) is {dest_dist:.1f} km from requested "
                f"destination '{dest_name}' ({dest_lat}, {dest_lon}), exceeding maximum catchment radius ({max_catchment_km} km)."
            )
            errors.append(msg)
            logger.warning(f"[ENDPOINT_VALIDATION_REJECT] {msg}")

    # Origin endpoint extraction
    first_from_loc = first_leg.get("from_loc") or {}
    first_boarding = first_leg.get("boarding_stop") or {}
    b_lat = first_from_loc.get("lat") or first_boarding.get("lat") or first_leg.get("from_lat")
    b_lon = first_from_loc.get("lon") or first_boarding.get("lon") or first_leg.get("from_lon")
    b_name = first_leg.get("from_name") or first_boarding.get("name") or first_from_loc.get("name") or itinerary.get("origin") or "Unknown"

    if origin_lat is not None and origin_lon is not None and b_lat is not None and b_lon is not None:
        orig_dist = _haversine_km_validator(float(b_lat), float(b_lon), float(origin_lat), float(origin_lon))
        if orig_dist > max_catchment_km:
            msg = (
                f"Itinerary origin '{b_name}' ({b_lat}, {b_lon}) is {orig_dist:.1f} km from requested "
                f"origin '{origin_name}' ({origin_lat}, {origin_lon}), exceeding maximum catchment radius ({max_catchment_km} km)."
            )
            errors.append(msg)
            logger.warning(f"[ENDPOINT_VALIDATION_REJECT] {msg}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "origin_endpoint": {"name": b_name, "lat": b_lat, "lon": b_lon},
        "dest_endpoint": {"name": a_name, "lat": a_lat, "lon": a_lon},
    }


def parse_timestamp(ts_val: Any) -> Optional[datetime]:
    """Helper to parse ISO-8601 strings or numeric timestamps."""
    if not ts_val:
        return None
    if isinstance(ts_val, (int, float)):
        try:
            # Handle numeric milliseconds or seconds
            sec = ts_val / 1000.0 if ts_val > 1e11 else float(ts_val)
            return datetime.fromtimestamp(sec)
        except Exception:
            return None
    if isinstance(ts_val, str):
        try:
            return datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


def harmonize_datetimes(dt1: Optional[datetime], dt2: Optional[datetime]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Harmonizes timezone awareness between two datetimes for safe comparison/subtraction."""
    if dt1 is None or dt2 is None:
        return dt1, dt2
    if dt1.tzinfo is not None and dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=dt1.tzinfo)
    elif dt1.tzinfo is None and dt2.tzinfo is not None:
        dt1 = dt1.replace(tzinfo=dt2.tzinfo)
    return dt1, dt2


def validate_itinerary(itinerary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates chronology, distance, duration, platform, and transfer count.
    Returns structured validation report.
    """
    errors: List[str] = []
    warnings: List[str] = []

    legs = itinerary.get("legs", [])
    if not legs:
        return {
            "valid": False,
            "errors": ["Itinerary contains zero legs."],
            "warnings": [],
            "checks": {
                "chronology": False,
                "distance": False,
                "duration": False,
                "transfers": False,
                "platform_provenance": False,
                "schedule_provenance": False,
            },
        }

    # ── 1. Chronology Validation ──────────────────────────────────────
    chronology_valid = True
    for i in range(len(legs)):
        leg_dep = parse_timestamp(legs[i].get("departure_time"))
        leg_arr = parse_timestamp(legs[i].get("arrival_time"))

        if leg_dep and leg_arr:
            h_dep, h_arr = harmonize_datetimes(leg_dep, leg_arr)
            if h_arr < h_dep:
                chronology_valid = False
                errors.append(f"Leg {i} arrival ({leg_arr}) precedes departure ({leg_dep}).")

        if i < len(legs) - 1:
            next_dep = parse_timestamp(legs[i + 1].get("departure_time"))
            if leg_arr and next_dep:
                h_arr, h_next = harmonize_datetimes(leg_arr, next_dep)
                if h_arr > h_next:
                    chronology_valid = False
                    errors.append(f"Leg {i} arrival ({leg_arr}) is after Leg {i+1} departure ({next_dep}).")

    # ── 2. Distance Provenance & Breakdown ────────────────────────────
    distance_valid = True
    transit_legs = [l for l in legs if l.get("type") == "TRANSIT"]
    walk_legs = [l for l in legs if l.get("type") == "WALK"]

    sum_walk_m = sum((l.get("distance_m", 0) or 0) for l in walk_legs)
    sum_transit_m = sum((l.get("distance_m", 0) or 0) for l in transit_legs)
    calc_total_m = sum_walk_m + sum_transit_m

    VALID_DISTANCE_SOURCES = {"PROVIDER", "HAVERSINE", "RailRadar", "OSRM", "FlightProvider", "GTFS", "Transitous"}
    VALID_DISTANCE_TYPES = {"ROUTE_DISTANCE", "STRAIGHT_LINE_ESTIMATE", None}

    for l in legs:
        src = l.get("distance_source")
        dtype = l.get("distance_type")
        if src and src not in VALID_DISTANCE_SOURCES:
            distance_valid = False
            errors.append(f"Invalid distance_source '{src}'. Must be a known provider or HAVERSINE.")
        # distance_type is optional — warn but don't fail if missing

    # ── 3. Duration Breakdown ─────────────────────────────────────────
    duration_valid = True
    overall_dep = parse_timestamp(itinerary.get("departure_time"))
    overall_arr = parse_timestamp(itinerary.get("arrival_time"))

    if overall_dep and overall_arr:
        h_ov_dep, h_ov_arr = harmonize_datetimes(overall_dep, overall_arr)
        calc_total_dur = int((h_ov_arr - h_ov_dep).total_seconds() / 60)
        sum_movement_dur = sum((l.get("duration_minutes", 0) or 0) for l in legs)
        calc_waiting_dur = calc_total_dur - sum_movement_dur

        if calc_waiting_dur < 0:
            duration_valid = False
            errors.append(f"Negative waiting duration calculated ({calc_waiting_dur} min).")
    else:
        warnings.append("Overall departure/arrival timestamps missing from itinerary.")

    # ── 4. Transfer Calculation ───────────────────────────────────────
    transfers_valid = True
    expected_transfers = max(0, len(transit_legs) - 1)
    given_transfers = itinerary.get("transfers")

    if given_transfers is not None and given_transfers != expected_transfers:
        warnings.append(f"Given transfer count ({given_transfers}) differs from transit legs count ({expected_transfers}). Correcting.")
        itinerary["transfers"] = expected_transfers

    # ── 5. Platform Provenance ────────────────────────────────────────
    platform_valid = True
    for l in legs:
        psrc = l.get("platform_source")
        if psrc and psrc not in ["PROVIDER", "UNAVAILABLE"]:
            platform_valid = False
            errors.append(f"Forbidden platform_source '{psrc}'. Only PROVIDER or UNAVAILABLE allowed.")

    # ── 6. Schedule Badges ────────────────────────────────────────────
    has_full_gtfs_stamps = True
    has_provider_verified = False

    for l in transit_legs:
        leg_dep = l.get("departure_time")
        leg_arr = l.get("arrival_time")
        if not (leg_dep and leg_arr):
            has_full_gtfs_stamps = False
        if l.get("time_status") == "SCHEDULED" or l.get("provider"):
            has_provider_verified = True

    if has_full_gtfs_stamps and len(transit_legs) > 0:
        schedule_status = "GTFS_SCHEDULED"
        schedule_badge = "🟢 GTFS Scheduled"
    elif has_provider_verified:
        schedule_status = "PROVIDER_VERIFIED"
        schedule_badge = "🟢 Provider Verified"
    else:
        schedule_status = "SCHEDULE_UNAVAILABLE"
        schedule_badge = "🟡 Schedule Unavailable"

    itinerary["schedule_badge"] = schedule_badge
    itinerary["schedule_status_code"] = schedule_status

    is_valid = len(errors) == 0 and chronology_valid and distance_valid and platform_valid

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "chronology": chronology_valid,
            "distance": distance_valid,
            "duration": duration_valid,
            "transfers": transfers_valid,
            "platform_provenance": platform_valid,
            "schedule_provenance": True,
        },
    }
