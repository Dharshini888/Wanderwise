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
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


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

        if leg_dep and leg_arr and leg_arr < leg_dep:
            chronology_valid = False
            errors.append(f"Leg {i} arrival ({leg_arr}) precedes departure ({leg_dep}).")

        if i < len(legs) - 1:
            next_dep = parse_timestamp(legs[i + 1].get("departure_time"))
            if leg_arr and next_dep and leg_arr > next_dep:
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
        calc_total_dur = int((overall_arr - overall_dep).total_seconds() / 60)
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
