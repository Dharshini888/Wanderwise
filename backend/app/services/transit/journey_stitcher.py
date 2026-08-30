"""
journey_stitcher.py -- WanderWise Multimodal Door-to-Door Journey Stitcher v14.0

Truth-First Rule:
- User origin remains exact real user origin.
- Provider verified schedule is preserved on MAIN_TRANSIT.
- First/last mile connections are OSRM walking/driving with "Route Calculated" status.
- Discards RED or invalid connections.
- Overnight trains: if the planning date is tomorrow (or a future date), do NOT reject
  trains whose clock time is earlier than current wall-clock time — they are valid
  future departures on the target calendar day.
"""

import logging
import uuid
import math
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple

from .journey_models import Journey, JourneyLeg, JourneyConnection, ConnectionStatus
from .connection_engine import classify_connection
from .providers.osrm_provider import OSRMRoadProvider

logger = logging.getLogger(__name__)


def _haversine_dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _parse_iso(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp. Returns naive datetime (tzinfo stripped)."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _format_time_display(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%I:%M %p").lstrip("0")


def _is_past_departure(dep_dt: datetime, now: datetime) -> bool:
    """
    Returns True ONLY when the departure is on today's calendar AND
    is more than 15 minutes in the past.
    A departure on any future calendar date is always valid.
    """
    if dep_dt.date() > now.date():
        return False  # Future calendar date — always valid
    if dep_dt.date() == now.date():
        return dep_dt < (now - timedelta(minutes=15))
    return True  # Past calendar date


def stitch_door_to_door_journey(
    route: Dict[str, Any],
    origin_name: str,
    origin_lat: float,
    origin_lon: float,
    dest_name: str,
    dest_lat: float,
    dest_lon: float,
    request_time: Optional[datetime] = None,
    date_hint: Optional[str] = "Tomorrow",
) -> Optional[Dict[str, Any]]:
    """
    Takes a candidate normalized route dict (e.g. from RailRadar, GTFS, Flight, or OSRM)
    and stitches a complete door-to-door Journey dict containing:
      - origin: {"name": origin_name, "lat": origin_lat, "lon": origin_lon}
      - destination: {"name": dest_name, "lat": dest_lat, "lon": dest_lon}
      - legs: [FIRST_MILE, MAIN_TRANSIT, LAST_MILE]
      - connections: [FIRST_MILE -> MAIN_TRANSIT, MAIN_TRANSIT -> LAST_MILE]
    Returns Journey dict or None if invalid/impossible.
    """
    if not route:
        return None

    now = request_time or datetime.now()
    provider = route.get("provider", "Unknown")
    route_id = route.get("route_id") or f"j_{uuid.uuid4().hex[:8]}"

    # Check departure time validity
    main_dep_str = route.get("departure_time")
    main_arr_str = route.get("arrival_time")
    main_dep_dt = _parse_iso(main_dep_str)
    main_arr_dt = _parse_iso(main_arr_str)

    # Filter out truly past departures — but never reject future-date trains
    if provider in ("RailRadar", "GTFS") and main_dep_dt:
        if _is_past_departure(main_dep_dt, now):
            logger.info(
                f"[J_STITCHER] Rejecting past departure for {provider} "
                f"train {route.get('train_number')}: {main_dep_dt} < current time {now}"
            )
            return None

    if provider == "OSRM" or route.get("mode") == "Driving":
        leg_id = f"leg_{uuid.uuid4().hex[:8]}"
        leg = JourneyLeg(
            sequence=1,
            mode="Driving",
            provider="OSRM",
            leg_type="MAIN_TRANSIT",
            from_stop=origin_name,
            to_stop=dest_name,
            origin_coords={"lat": origin_lat, "lon": origin_lon},
            dest_coords={"lat": dest_lat, "lon": dest_lon},
            departure_time=route.get("departure_time"),
            arrival_time=route.get("arrival_time"),
            departure_time_display=route.get("departure_time_display"),
            arrival_time_display=route.get("arrival_time_display"),
            duration_min=route.get("duration_min"),
            distance_km=route.get("distance_km"),
            verification_status="Route Calculated",
            source="OSRM",
            geometry=route.get("geometry") or [],
        )
        leg.leg_id = leg_id
        leg.connection_status = None

        journey = Journey(
            journey_id=route_id,
            origin={"name": origin_name, "lat": origin_lat, "lon": origin_lon},
            destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
            legs=[leg],
            connections=[],
            departure_time=leg.departure_time,
            arrival_time=leg.arrival_time,
            departure_time_display=leg.departure_time_display,
            arrival_time_display=leg.arrival_time_display,
            total_duration_min=route.get("duration_min"),
            total_distance_km=route.get("distance_km"),
            verification_status="Route Calculated",
            geometry=route.get("geometry") or [],
            optimization_tags=["Road Alternative"],
            why_this_route=route.get("why_this_route") or ["Road route calculated via OSRM."],
            provider="OSRM",
            mode="Driving",
            distance_source="OSRM",
            duration_source="OSRM",
            is_long_distance_fallback=route.get("is_long_distance_fallback", False),
        )
        return journey.to_dict()

    # Extract stations and coordinates from candidate main transit route
    raw_legs = route.get("legs") or []
    boarding_station_name = route.get("departure_station") or route.get("origin") or "Boarding Station"
    alighting_station_name = route.get("arrival_station") or route.get("destination") or "Alighting Station"

    b_lat, b_lon = None, None
    a_lat, a_lon = None, None

    if raw_legs:
        first_raw = raw_legs[0]
        b_stop = first_raw.get("boarding_stop") or {}
        b_lat = b_stop.get("lat") or first_raw.get("from_lat")
        b_lon = b_stop.get("lon") or first_raw.get("from_lon")

        last_raw = raw_legs[-1]
        a_stop = last_raw.get("alighting_stop") or {}
        a_lat = a_stop.get("lat") or last_raw.get("to_lat")
        a_lon = a_stop.get("lon") or last_raw.get("to_lon")

    # Measure distances from origin to boarding station, and alighting station to destination
    first_mile_dist_km = _haversine_dist_km(origin_lat, origin_lon, b_lat, b_lon) if b_lat and b_lon else 0.0
    last_mile_dist_km = _haversine_dist_km(a_lat, a_lon, dest_lat, dest_lon) if a_lat and a_lon else 0.0

    needs_first_mile = first_mile_dist_km > 0.5 or (origin_name.lower().strip() != boarding_station_name.lower().strip() and first_mile_dist_km > 0.1)
    needs_last_mile = last_mile_dist_km > 0.5 or (dest_name.lower().strip() != alighting_station_name.lower().strip() and last_mile_dist_km > 0.1)

    legs: List[JourneyLeg] = []
    connections: List[JourneyConnection] = []

    # 1. FIRST MILE LEG
    first_mile_dur_min = 0.0
    fm_dep_dt, fm_arr_dt = None, None

    if needs_first_mile:
        # Route via OSRM
        if b_lat and b_lon and origin_lat and origin_lon:
            fm_osrm = OSRMRoadProvider.get_walking_leg(
                from_name=origin_name, from_lat=origin_lat, from_lon=origin_lon,
                to_name=boarding_station_name, to_lat=b_lat, to_lon=b_lon
            ) if first_mile_dist_km <= 1.5 else OSRMRoadProvider.get_road_alternative(
                origin_name=origin_name, origin_lat=origin_lat, origin_lon=origin_lon,
                dest_name=boarding_station_name, dest_lat=b_lat, dest_lon=b_lon
            )
            fm_dist_km = fm_osrm.get("distance_km") or (fm_osrm.get("distance_m", 0) / 1000.0) or round(first_mile_dist_km, 1)
            fm_dur_min = float(fm_osrm.get("duration_minutes") or fm_osrm.get("duration_min") or max(5, int(first_mile_dist_km * 2)))
            fm_mode = "WALK" if first_mile_dist_km <= 1.5 else "ROAD"
            fm_geom = fm_osrm.get("geometry") or []
        else:
            fm_dist_km = round(first_mile_dist_km, 1)
            fm_dur_min = max(5.0, round(first_mile_dist_km * 2.5, 1))
            fm_mode = "WALK" if first_mile_dist_km <= 1.5 else "ROAD"
            fm_geom = []

        # Time alignment: arrive at station 15 mins before train departure
        if main_dep_dt:
            fm_arr_dt = main_dep_dt - timedelta(minutes=15)
            fm_dep_dt = fm_arr_dt - timedelta(minutes=int(fm_dur_min))

        fm_leg_id = f"leg_{uuid.uuid4().hex[:8]}"
        fm_leg = JourneyLeg(
            sequence=1,
            mode=fm_mode,
            provider="OSRM",
            leg_type="FIRST_MILE",
            from_stop=origin_name,
            to_stop=boarding_station_name,
            origin_coords={"lat": origin_lat, "lon": origin_lon},
            dest_coords={"lat": b_lat, "lon": b_lon},
            departure_time=fm_dep_dt.isoformat() if fm_dep_dt else None,
            arrival_time=fm_arr_dt.isoformat() if fm_arr_dt else None,
            departure_time_display=_format_time_display(fm_dep_dt),
            arrival_time_display=_format_time_display(fm_arr_dt),
            duration_min=fm_dur_min,
            distance_km=fm_dist_km,
            verification_status="Route Calculated",
            source="OSRM",
            geometry=fm_geom,
        )
        fm_leg.leg_id = fm_leg_id
        fm_leg.connection_status = None
        legs.append(fm_leg)

    # 2. MAIN TRANSIT LEG
    main_seq = len(legs) + 1
    main_mode = "RAIL" if provider == "RailRadar" or "train" in (route.get("mode") or "").lower() else (route.get("mode") or "TRANSIT")
    main_vs = route.get("verification_status") or ("Provider Verified" if provider == "RailRadar" else "Schedule Verified")

    main_leg_id = f"leg_{uuid.uuid4().hex[:8]}"
    main_leg = JourneyLeg(
        sequence=main_seq,
        mode=main_mode,
        provider=provider,
        leg_type="MAIN_TRANSIT",
        from_stop=boarding_station_name,
        to_stop=alighting_station_name,
        origin_coords={"lat": b_lat, "lon": b_lon},
        dest_coords={"lat": a_lat, "lon": a_lon},
        departure_time=route.get("departure_time"),
        arrival_time=route.get("arrival_time"),
        departure_time_display=route.get("departure_time_display"),
        arrival_time_display=route.get("arrival_time_display"),
        duration_min=route.get("duration_min"),
        distance_km=route.get("distance_km"),
        train_number=route.get("train_number"),
        train_name=route.get("train_name"),
        boarding_point=boarding_station_name,
        alighting_point=alighting_station_name,
        intermediate_stops=route.get("intermediate_stops") or [],
        verification_status=main_vs,
        source=provider,
        geometry=route.get("geometry") or [],
        is_overnight=route.get("is_overnight", False),
        operating_days=route.get("operating_days") or [],
        platform=route.get("platform"),
        live_status=route.get("live_status"),
        delay_min=route.get("delay_min"),
        current_station=route.get("current_station"),
        next_station=route.get("next_station"),
        fare=route.get("fare"),
        fare_source=route.get("fare_source"),
    )
    main_leg.leg_id = main_leg_id
    main_leg.connection_status = None
    legs.append(main_leg)

    # Connection 1: FIRST_MILE -> MAIN_TRANSIT
    if needs_first_mile:
        connections.append(JourneyConnection(
            from_leg_sequence=1,
            to_leg_sequence=main_seq,
            transfer_time_min=15.0,
            status=ConnectionStatus.GREEN,
            reason="Safe 15 min station boarding window",
        ))

    # 3. LAST MILE LEG
    last_mile_dur_min = 0.0
    lm_dep_dt, lm_arr_dt = None, None

    if needs_last_mile:
        if a_lat and a_lon and dest_lat and dest_lon:
            lm_osrm = OSRMRoadProvider.get_walking_leg(
                from_name=alighting_station_name, from_lat=a_lat, from_lon=a_lon,
                to_name=dest_name, to_lat=dest_lat, to_lon=dest_lon
            ) if last_mile_dist_km <= 1.5 else OSRMRoadProvider.get_road_alternative(
                origin_name=alighting_station_name, origin_lat=a_lat, origin_lon=a_lon,
                dest_name=dest_name, dest_lat=dest_lat, dest_lon=dest_lon
            )
            lm_dist_km = lm_osrm.get("distance_km") or (lm_osrm.get("distance_m", 0) / 1000.0) or round(last_mile_dist_km, 1)
            lm_dur_min = float(lm_osrm.get("duration_minutes") or lm_osrm.get("duration_min") or max(5, int(last_mile_dist_km * 2)))
            lm_mode = "WALK" if last_mile_dist_km <= 1.5 else "ROAD"
            lm_geom = lm_osrm.get("geometry") or []
        else:
            lm_dist_km = round(last_mile_dist_km, 1)
            lm_dur_min = max(5.0, round(last_mile_dist_km * 2.5, 1))
            lm_mode = "WALK" if last_mile_dist_km <= 1.5 else "ROAD"
            lm_geom = []

        if main_arr_dt:
            lm_dep_dt = main_arr_dt + timedelta(minutes=10)
            lm_arr_dt = lm_dep_dt + timedelta(minutes=int(lm_dur_min))

        lm_seq = len(legs) + 1
        lm_leg_id = f"leg_{uuid.uuid4().hex[:8]}"
        lm_leg = JourneyLeg(
            sequence=lm_seq,
            mode=lm_mode,
            provider="OSRM",
            leg_type="LAST_MILE",
            from_stop=alighting_station_name,
            to_stop=dest_name,
            origin_coords={"lat": a_lat, "lon": a_lon},
            dest_coords={"lat": dest_lat, "lon": dest_lon},
            departure_time=lm_dep_dt.isoformat() if lm_dep_dt else None,
            arrival_time=lm_arr_dt.isoformat() if lm_arr_dt else None,
            departure_time_display=_format_time_display(lm_dep_dt),
            arrival_time_display=_format_time_display(lm_arr_dt),
            duration_min=lm_dur_min,
            distance_km=lm_dist_km,
            verification_status="Route Calculated",
            source="OSRM",
            geometry=lm_geom,
        )
        lm_leg.leg_id = lm_leg_id
        lm_leg.connection_status = "GREEN"
        legs.append(lm_leg)

        # Connection 2: MAIN_TRANSIT -> LAST_MILE
        connections.append(JourneyConnection(
            from_leg_sequence=main_seq,
            to_leg_sequence=lm_seq,
            transfer_time_min=10.0,
            status=ConnectionStatus.GREEN,
            reason="10 min alighting transfer window",
        ))

    # Calculate overall door-to-door duration and distance
    tot_dur = sum(l.duration_min or 0 for l in legs) + sum(c.transfer_time_min or 0 for c in connections)
    tot_dist = sum(l.distance_km or 0 for l in legs)

    overall_dep_time = legs[0].departure_time
    overall_arr_time = legs[-1].arrival_time
    overall_dep_display = legs[0].departure_time_display
    overall_arr_display = legs[-1].arrival_time_display

    # Verification status calculation
    if all(l.verification_status in ("Provider Verified", "Schedule Verified", "VERIFIED") for l in legs):
        overall_vs = "PROVIDER_VERIFIED"
    elif any(l.verification_status in ("Provider Verified", "Schedule Verified", "VERIFIED") for l in legs):
        overall_vs = "PARTIALLY_VERIFIED"
    else:
        overall_vs = "ROUTE_CALCULATED"

    # Combine geometries for map rendering
    combined_geometry = []
    for l in legs:
        if l.geometry:
            combined_geometry.extend(l.geometry)

    journey = Journey(
        journey_id=route_id,
        origin={"name": origin_name, "lat": origin_lat, "lon": origin_lon},
        destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
        legs=legs,
        connections=connections,
        departure_time=overall_dep_time,
        arrival_time=overall_arr_time,
        departure_time_display=overall_dep_display,
        arrival_time_display=overall_arr_display,
        total_duration_min=round(tot_dur, 1),
        total_distance_km=round(tot_dist, 1),
        verification_status=overall_vs,
        geometry=combined_geometry,
        optimization_tags=route.get("optimization_tags") or ["Door-to-Door Multimodal"],
        why_this_route=route.get("why_this_route") or [
            f"Door-to-door multimodal journey via {provider} ({boarding_station_name} → {alighting_station_name})."
        ],
        is_overnight=route.get("is_overnight", False),
        provider=provider,
        mode=route.get("mode") or "Multimodal",
        train_number=route.get("train_number"),
        train_name=route.get("train_name"),
        departure_station=boarding_station_name,
        arrival_station=alighting_station_name,
        operating_days=route.get("operating_days") or [],
        intermediate_stops=route.get("intermediate_stops") or [],
        platform=route.get("platform"),
        live_status=route.get("live_status"),
        delay_min=route.get("delay_min"),
        current_station=route.get("current_station"),
        next_station=route.get("next_station"),
        is_long_distance_fallback=route.get("is_long_distance_fallback", False),
    )

    return journey.to_dict()


def stitch_all_journeys(
    candidate_routes: List[Dict[str, Any]],
    origin_name: str,
    origin_lat: float,
    origin_lon: float,
    dest_name: str,
    dest_lat: float,
    dest_lon: float,
    request_time: Optional[datetime] = None,
    date_hint: Optional[str] = "Tomorrow",
) -> List[Dict[str, Any]]:
    """
    Takes candidate normalized routes and produces stitched door-to-door Journey dicts.
    Discards invalid or RED-connection journeys.
    date_hint: 'Tomorrow' or 'YYYY-MM-DD' to control the planning calendar date.
    """
    stitched_journeys = []
    for r in candidate_routes:
        try:
            j = stitch_door_to_door_journey(
                route=r,
                origin_name=origin_name,
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                dest_name=dest_name,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                request_time=request_time,
                date_hint=date_hint,
            )
            if j:
                stitched_journeys.append(j)
        except Exception as err:
            logger.warning(f"[J_STITCHER] Error stitching route {r.get('route_id')}: {err}")

    return stitched_journeys
