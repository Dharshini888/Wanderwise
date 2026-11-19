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
from .station_normalizer import normalize_station_name, normalize_mode_name, get_mode_icon

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


_OSRM_LEG_CACHE: Dict[Tuple[float, float, float, float, str], Dict[str, Any]] = {}


def _get_cached_osrm_leg(
    from_name: str, from_lat: float, from_lon: float,
    to_name: str, to_lat: float, to_lon: float, is_walk: bool
) -> Dict[str, Any]:
    """In-memory cache for OSRM walking/road calculations to eliminate repetitive network calls."""
    key = (round(from_lat, 4), round(from_lon, 4), round(to_lat, 4), round(to_lon, 4), "walk" if is_walk else "road")
    if key in _OSRM_LEG_CACHE:
        return _OSRM_LEG_CACHE[key]
    try:
        if is_walk:
            res = OSRMRoadProvider.get_walking_leg(from_name, from_lat, from_lon, to_name, to_lat, to_lon)
        else:
            res = OSRMRoadProvider.get_road_alternative(from_name, from_lat, from_lon, to_name, to_lat, to_lon)
        _OSRM_LEG_CACHE[key] = res
        return res
    except Exception as e:
        logger.warning(f"[STITCHER] OSRM leg calculation error: {e}")
        return {"distance_km": round(_haversine_dist_km(from_lat, from_lon, to_lat, to_lon), 1), "duration_min": 5.0, "geometry": []}


from .tz_utils import KOLKATA_TZ, get_timezone


def _parse_iso(ts_str: Optional[str], default_tz=KOLKATA_TZ) -> Optional[datetime]:
    """Parse ISO 8601 timestamp. Normalizes to station timezone (default Asia/Kolkata)."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            return dt.astimezone(default_tz)
        return dt.replace(tzinfo=default_tz)
    except Exception:
        return None


def _format_time_display(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%I:%M %p").lstrip("0")


def evaluate_catchability(
    service_dep_dt: Optional[datetime],
    now: datetime,
    first_mile_dur_min: float = 0.0,
    boarding_buffer_min: float = 5.0,
    station_name: str = "station",
) -> Tuple[bool, str, str, float]:
    """
    Calculates date-aware catchability strictly without altering calendar dates:
      Returns (is_catchable, catchability_status, why_catchable_msg, waiting_min)
      catchability_status in ("CATCHABLE", "AVAILABLE_LATER", "CANNOT_CATCH", "ALREADY_DEPARTED", "SCHEDULE_UNAVAILABLE")
    """
    if not service_dep_dt:
        return True, "SCHEDULE_UNAVAILABLE", f"Schedule unverified for {station_name} departure.", 10.0

    s_dt = service_dep_dt
    n_dt = now

    # Harmonize timezone awareness
    if s_dt.tzinfo is not None and n_dt.tzinfo is None:
        n_dt = n_dt.replace(tzinfo=s_dt.tzinfo)
    elif s_dt.tzinfo is None and n_dt.tzinfo is not None:
        s_dt = s_dt.replace(tzinfo=n_dt.tzinfo)

    access_total_min = float(first_mile_dur_min) + float(boarding_buffer_min)
    earliest_boarding_time = n_dt + timedelta(minutes=access_total_min)
    earliest_station_arrival = n_dt + timedelta(minutes=float(first_mile_dur_min))

    rec_origin_dep = s_dt - timedelta(minutes=int(access_total_min))
    rec_station_arr = rec_origin_dep + timedelta(minutes=int(first_mile_dur_min))

    dep_disp = _format_time_display(s_dt)
    eb_disp = _format_time_display(earliest_boarding_time)
    arr_disp = _format_time_display(earliest_station_arrival)
    rec_dep_disp = _format_time_display(rec_origin_dep)
    rec_arr_disp = _format_time_display(rec_station_arr)

    # 1. ALREADY DEPARTED:
    # If departure date is before reference date, OR if today and more than 15 minutes in past
    is_past_day = s_dt.date() < n_dt.date()
    is_past_today_15m = (s_dt.date() == n_dt.date()) and (s_dt < (n_dt - timedelta(minutes=15)))

    if is_past_day or is_past_today_15m:
        is_catchable = False
        catchability_status = "ALREADY_DEPARTED"
        date_str = "today" if s_dt.date() == n_dt.date() else s_dt.strftime("%b %d")
        msg = f"Already departed — service departed at {dep_disp} {date_str}."
        waiting_min = 0.0
        return is_catchable, catchability_status, msg, waiting_min

    # 2. CANNOT CATCH: (Insufficient transfer time)
    # Service has not departed long ago, but departs before user can reach station + boarding buffer
    if s_dt < earliest_boarding_time:
        is_catchable = False
        catchability_status = "CANNOT_CATCH"
        if boarding_buffer_min >= 60.0 or "airport" in station_name.lower():
            buf_name = "airport check-in & security buffer"
        elif boarding_buffer_min >= 15.0:
            buf_name = "station junction buffer"
        else:
            buf_name = "buffer"
        msg = (
            f"Cannot catch — service departs at {dep_disp}, "
            f"but earliest boarding time is {eb_disp} "
            f"(arrival at {arr_disp} + {int(boarding_buffer_min)} min {buf_name})."
        )
        waiting_min = 0.0
        return is_catchable, catchability_status, msg, waiting_min

    # 3. CATCHABLE (within 2 hours) or AVAILABLE LATER (departing later)
    diff_from_earliest_min = (s_dt - earliest_boarding_time).total_seconds() / 60.0
    is_catchable = True
    is_at_station = float(first_mile_dur_min) <= 0.5

    buf_desc = "airport check-in buffer" if (boarding_buffer_min >= 60.0 or "airport" in station_name.lower()) else "buffer"
    if diff_from_earliest_min <= 120.0:
        catchability_status = "CATCHABLE"
        door_dep = max(n_dt, rec_origin_dep)
        actual_arr = door_dep + timedelta(minutes=int(first_mile_dur_min))
        waiting_min = max(0.0, (s_dt - earliest_station_arrival).total_seconds() / 60.0)
        if is_at_station:
            msg = (
                f"Catchable now — at station: arrive at platform by {_format_time_display(door_dep)} "
                f"({int(waiting_min)} min {buf_desc} before {dep_disp} departure)."
            )
        else:
            msg = (
                f"Catchable now — leave origin by {_format_time_display(door_dep)} "
                f"to reach {station_name} at {_format_time_display(actual_arr)} "
                f"({int(waiting_min)} min {buf_desc} before {dep_disp} departure)."
            )
    else:
        catchability_status = "AVAILABLE_LATER"
        waiting_min = max(float(boarding_buffer_min), (s_dt - earliest_station_arrival).total_seconds() / 60.0)
        date_suffix = ""
        if s_dt.date() > n_dt.date():
            days_ahead = (s_dt.date() - n_dt.date()).days
            date_suffix = " tomorrow" if days_ahead == 1 else f" on {s_dt.strftime('%b %d')}"
        buf_station_desc = f"{int(boarding_buffer_min)} min airport check-in buffer" if (boarding_buffer_min >= 60.0 or "airport" in station_name.lower()) else f"{int(boarding_buffer_min)} min station buffer"
        if is_at_station:
            msg = (
                f"Available later — scheduled departure at {dep_disp}{date_suffix}. "
                f"At station: arrive at platform by {rec_dep_disp} ({int(boarding_buffer_min)} min before {dep_disp} departure)."
            )
        else:
            msg = (
                f"Available later — scheduled departure at {dep_disp}{date_suffix}. "
                f"Leave origin by {rec_dep_disp} to reach {station_name} at {rec_arr_disp} "
                f"with {buf_station_desc}."
            )

    return is_catchable, catchability_status, msg, waiting_min


def _is_past_departure(dep_dt: datetime, now: datetime) -> bool:
    """
    Returns True ONLY when the departure is on today's calendar AND
    is more than 15 minutes in the past.
    A departure on any future calendar date is always valid.
    """
    if dep_dt.date() > now.date():
        return False
    if dep_dt.date() == now.date():
        return dep_dt < (now - timedelta(minutes=15))
    return True


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
    and stitches a complete door-to-door Journey dict containing departure-time aware legs:
      - origin: {"name": origin_name, "lat": origin_lat, "lon": origin_lon}
      - destination: {"name": dest_name, "lat": dest_lat, "lon": dest_lon}
      - legs: [FIRST_MILE, MAIN_TRANSIT, LAST_MILE]
      - connections: [FIRST_MILE -> MAIN_TRANSIT, MAIN_TRANSIT -> LAST_MILE]
      - catchable: bool & catchability_status: str & why_catchable: str
      - door_to_door_departure & door_to_door_arrival
    """
    import os
    if not route:
        return None

    provider = route.get("provider", "Unknown")
    route_id = route.get("route_id") or f"j_{uuid.uuid4().hex[:8]}"

    is_flight = (provider == "FlightProvider") or ((route.get("mode") or "").lower() in ("flight", "commercial flight"))

    if is_flight:
        origin_name = route.get("origin") or origin_name
        dest_name = route.get("destination") or dest_name
        # Never let railway station names (e.g. Coimbatore Junction, Chennai Central) serve as the city origin/destination of a flight
        if origin_name.lower().endswith(" junction"):
            origin_name = origin_name[:-9].strip()
        elif origin_name.lower().endswith(" central"):
            origin_name = origin_name[:-8].strip()
        if dest_name.lower().endswith(" junction"):
            dest_name = dest_name[:-9].strip()
        elif dest_name.lower().endswith(" central"):
            dest_name = dest_name[:-8].strip()
        boarding_station_name = route.get("origin_airport") or route.get("departure_station") or f"{origin_name} Airport"
        alighting_station_name = route.get("destination_airport") or route.get("arrival_station") or f"{dest_name} Airport"
    else:
        origin_name = normalize_station_name(origin_name)
        dest_name = normalize_station_name(dest_name)
        boarding_station_name = normalize_station_name(route.get("departure_station") or route.get("origin") or "Boarding Station")
        alighting_station_name = normalize_station_name(route.get("arrival_station") or route.get("destination") or "Alighting Station")

    is_same_orig_station = (origin_name.lower().strip() == boarding_station_name.lower().strip())
    is_same_dest_station = (dest_name.lower().strip() == alighting_station_name.lower().strip())

    is_rail = (route.get("provider") in ("RailRadar", "Indian Railways Timetable", "IndianRailways-ScheduleVerified")) or ((route.get("mode") or "").lower() in ("train", "rail"))
    if is_flight:
        is_intl_flight = (route.get("is_international") or _haversine_dist_km(origin_lat, origin_lon, dest_lat, dest_lon) > 500.0)
        boarding_buffer_min = 180.0 if is_intl_flight else 90.0
    elif is_same_orig_station:
        boarding_buffer_min = float(os.getenv("TRANSIT_BOARDING_BUFFER_MINUTES", "5.0"))
    elif is_rail:
        boarding_buffer_min = float(os.getenv("RAIL_BOARDING_BUFFER_MINUTES", "20.0"))
    else:
        boarding_buffer_min = float(os.getenv("TRANSIT_BOARDING_BUFFER_MINUTES", "5.0"))
    transfer_buffer_min = float(os.getenv("TRANSIT_TRANSFER_BUFFER_MINUTES", "5.0"))

    now = request_time or datetime.now(KOLKATA_TZ)
    if isinstance(now, str):
        now = _parse_iso(now) or datetime.now(KOLKATA_TZ)
    elif isinstance(now, datetime):
        now = now.astimezone(KOLKATA_TZ) if now.tzinfo else now.replace(tzinfo=KOLKATA_TZ)

    # Check departure time validity (truth-first: NEVER silently alter date)
    main_dep_str = route.get("departure_time")
    main_arr_str = route.get("arrival_time")
    main_dep_dt = _parse_iso(main_dep_str)
    main_arr_dt = _parse_iso(main_arr_str)

    # ── Flight Option (Door-to-Door Flight with verified AviationStack schedule) ──
    if is_flight and route.get("is_door_to_door") and route.get("legs"):
        raw_legs = route.get("legs", [])
        j_legs: List[JourneyLeg] = []
        j_conns: List[JourneyConnection] = []

        main_fl_dep_dt = _parse_iso(route.get("flight_departure_time") or route.get("departure_time"))
        main_fl_arr_dt = _parse_iso(route.get("flight_arrival_time") or route.get("arrival_time"))

        fm_dur = 0.0
        for rl in raw_legs:
            if rl.get("type") == "FIRST_MILE":
                fm_dur = float(rl.get("duration_min") or rl.get("duration_minutes") or 0.0)
                break

        is_c, c_status, c_msg, w_min = evaluate_catchability(
            service_dep_dt=main_fl_dep_dt,
            now=now,
            first_mile_dur_min=fm_dur,
            boarding_buffer_min=boarding_buffer_min,
            station_name=boarding_station_name,
        )

        seq = 1
        for rl in raw_legs:
            l_type = rl.get("type", "MAIN_TRANSIT")
            if l_type == "TRANSFER":
                if j_legs:
                    j_conns.append(JourneyConnection(
                        from_leg_sequence=j_legs[-1].sequence,
                        to_leg_sequence=j_legs[-1].sequence + 1,
                        transfer_time_min=float(rl.get("duration_min") or rl.get("duration_minutes") or 30.0),
                        status=ConnectionStatus.GREEN,
                        note=rl.get("note") or f"{rl.get('mode')} buffer",
                    ))
                continue

            from_name_val = rl.get("from_name") or rl.get("from_stop") or boarding_station_name
            to_name_val = rl.get("to_name") or rl.get("to_stop") or alighting_station_name
            if from_name_val.lower().endswith(" junction"):
                from_name_val = from_name_val[:-9].strip()
            elif from_name_val.lower().endswith(" central"):
                from_name_val = from_name_val[:-8].strip()
            if to_name_val.lower().endswith(" junction"):
                to_name_val = to_name_val[:-9].strip()
            elif to_name_val.lower().endswith(" central"):
                to_name_val = to_name_val[:-8].strip()

            j_leg = JourneyLeg(
                sequence=seq,
                mode=rl.get("mode", "Flight" if l_type == "MAIN_TRANSIT" else "Driving"),
                provider=rl.get("provider", "FlightProvider"),
                leg_type=l_type,
                from_stop=from_name_val,
                to_stop=to_name_val,
                departure_time=rl.get("departure_time"),
                arrival_time=rl.get("arrival_time"),
                departure_time_display=rl.get("departure_time_display"),
                arrival_time_display=rl.get("arrival_time_display"),
                duration_min=float(rl.get("duration_min") or rl.get("duration_minutes") or 60.0),
                distance_km=rl.get("distance_km"),
                route_number=rl.get("flight_number"),
                flight_number=rl.get("flight_number"),
                airline=rl.get("airline") or rl.get("airline_name"),
                airline_name=rl.get("airline_name") or rl.get("airline"),
                origin_iata=rl.get("origin_iata"),
                destination_iata=rl.get("destination_iata"),
                verification_status=rl.get("verification_status") or "Provider Verified",
                source=rl.get("source") or "AviationStack",
            )
            j_legs.append(j_leg)
            seq += 1

        flight_dep_disp = route.get("flight_departure_time_display") or route.get("departure_time_display")
        flight_arr_disp = route.get("flight_arrival_time_display") or route.get("arrival_time_display")

        journey = Journey(
            journey_id=route_id,
            origin={"name": origin_name, "lat": origin_lat, "lon": origin_lon},
            destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
            legs=j_legs,
            connections=j_conns,
            departure_time=route.get("departure_time"),
            arrival_time=route.get("arrival_time"),
            departure_time_display=route.get("departure_time_display"),
            arrival_time_display=route.get("arrival_time_display"),
            departure_date=main_fl_dep_dt.strftime("%Y-%m-%d") if main_fl_dep_dt else None,
            arrival_date=main_fl_arr_dt.strftime("%Y-%m-%d") if main_fl_arr_dt else None,
            departure_date_display=main_fl_dep_dt.strftime("%b %d, %Y") if main_fl_dep_dt else None,
            arrival_date_display=main_fl_arr_dt.strftime("%b %d, %Y") if main_fl_arr_dt else None,
            door_to_door_departure=route.get("departure_time"),
            door_to_door_arrival=route.get("arrival_time"),
            door_to_door_departure_display=route.get("departure_time_display"),
            door_to_door_arrival_display=route.get("arrival_time_display"),
            catchable=is_c,
            catchability_status=c_status,
            why_catchable=c_msg,
            catchability_reason=c_msg,
            duration_breakdown=route.get("duration_breakdown") or {},
            total_duration_min=float(route.get("total_duration_minutes") or route.get("duration_min") or 120.0),
            duration_min=float(route.get("total_duration_minutes") or route.get("duration_min") or 120.0),
            total_distance_km=float(route.get("total_distance_km") or route.get("distance_km") or 0.0),
            verification_status="Provider Verified",
            verification=route.get("verification") or {"level": "PROVIDER_VERIFIED", "provider": "FlightProvider"},
            source=route.get("source") or {},
            realtime=route.get("realtime") or {"available": False, "status": "unavailable"},
            optimization_tags=["Fastest Multimodal Option", "Verified Commercial Flight"],
            why_this_route=[
                f"Verified commercial flight via {route.get('airline', 'AviationStack')} ({route.get('flight_number', 'Flight')}) from {boarding_station_name} to {alighting_station_name}."
            ],
            is_overnight=route.get("is_overnight", False),
            provider="FlightProvider",
            mode="Flight",
            flight_number=route.get("flight_number"),
            airline=route.get("airline"),
            airline_name=route.get("airline_name"),
            origin_airport=boarding_station_name,
            destination_airport=alighting_station_name,
            origin_iata=route.get("origin_iata"),
            destination_iata=route.get("destination_iata"),
            flight_departure_time=route.get("flight_departure_time"),
            flight_arrival_time=route.get("flight_arrival_time"),
            flight_departure_time_display=flight_dep_disp,
            flight_arrival_time_display=flight_arr_disp,
            flight_duration_minutes=route.get("flight_duration_minutes"),
            flight_duration_display=route.get("flight_duration_display"),
            flight_distance_km=route.get("flight_distance_km"),
            total_duration_minutes=route.get("total_duration_minutes"),
            total_duration_display=route.get("total_duration_display"),
            departure_station=boarding_station_name,
            arrival_station=alighting_station_name,
        )
        return journey.to_dict()

    # OSRM Driving alternative (on-demand door-to-door road route)
    if provider == "OSRM" or (route.get("mode") or "").lower() in ("driving", "road"):
        road_dur_min = max(1.0, float(route.get("duration_min") or route.get("duration_minutes") or 60.0))
        dur_rounded_min = int(round(road_dur_min))
        dep_start_dt = (main_dep_dt or now).replace(second=0, microsecond=0)
        road_arr_dt = (dep_start_dt + timedelta(minutes=dur_rounded_min)).replace(second=0, microsecond=0)
        is_overnight = road_arr_dt.date() > dep_start_dt.date()

        road_dep_display = route.get("departure_time_display") or _format_time_display(dep_start_dt)
        road_arr_display = route.get("arrival_time_display") or _format_time_display(road_arr_dt)
        if is_overnight and "(+1 day)" not in road_arr_display:
            road_arr_display = f"{road_arr_display} (+1 day)"

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
            departure_time=dep_start_dt.isoformat(),
            arrival_time=road_arr_dt.isoformat(),
            departure_time_display=road_dep_display,
            arrival_time_display=road_arr_display,
            duration_min=float(dur_rounded_min),
            distance_km=route.get("distance_km"),
            verification_status="Route Calculated",
            source="OSRM",
            geometry=route.get("geometry") or [],
            is_overnight=is_overnight,
        )
        leg.leg_id = leg_id
        leg.connection_status = None

        why_txt = f"Direct road route leaving at {road_dep_display}, arriving at {road_arr_display}."

        journey = Journey(
            journey_id=route_id,
            origin={"name": origin_name, "lat": origin_lat, "lon": origin_lon},
            destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
            legs=[leg],
            connections=[],
            departure_time=leg.departure_time,
            arrival_time=leg.arrival_time,
            departure_time_display=road_dep_display,
            arrival_time_display=road_arr_display,
            departure_date=dep_start_dt.strftime("%Y-%m-%d"),
            arrival_date=road_arr_dt.strftime("%Y-%m-%d"),
            departure_date_display=dep_start_dt.strftime("%b %d, %Y"),
            arrival_date_display=road_arr_dt.strftime("%b %d, %Y"),
            door_to_door_departure=leg.departure_time,
            door_to_door_arrival=leg.arrival_time,
            door_to_door_departure_display=road_dep_display,
            door_to_door_arrival_display=road_arr_display,
            catchable=True,
            catchability_status="CATCHABLE",
            why_catchable=why_txt,
            catchability_reason=why_txt,
            duration_breakdown={
                "access_min": 0,
                "waiting_min": 0,
                "main_transit_min": float(dur_rounded_min),
                "egress_min": 0,
                "total_door_to_door_min": float(dur_rounded_min),
            },
            total_duration_min=float(dur_rounded_min),
            total_distance_km=route.get("distance_km"),
            verification_status="Route Calculated",
            geometry=route.get("geometry") or [],
            optimization_tags=["Road Alternative"],
            why_this_route=route.get("why_this_route") or [why_txt],
            provider="OSRM",
            mode="Driving",
            distance_source="OSRM",
            duration_source="OSRM",
            is_long_distance_fallback=route.get("is_long_distance_fallback", False),
        )
        return journey.to_dict()

    # Extract stations and coordinates from candidate main transit route
    raw_legs = route.get("legs") or []
    boarding_station_name = normalize_station_name(route.get("departure_station") or route.get("origin") or "Boarding Station")
    alighting_station_name = normalize_station_name(route.get("arrival_station") or route.get("destination") or "Alighting Station")

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

    if (b_lat is None or b_lon is None) and isinstance(route.get("origin"), dict):
        b_lat = route["origin"].get("lat")
        b_lon = route["origin"].get("lon")
    if (a_lat is None or a_lon is None) and isinstance(route.get("destination"), dict):
        a_lat = route["destination"].get("lat")
        a_lon = route["destination"].get("lon")

    # Measure distances from origin to boarding station, and alighting station to destination
    first_mile_dist_km = _haversine_dist_km(origin_lat, origin_lon, b_lat, b_lon) if b_lat and b_lon else 0.0
    last_mile_dist_km = _haversine_dist_km(a_lat, a_lon, dest_lat, dest_lon) if a_lat and a_lon else 0.0

    # Endpoint Catchment Validation (Truth-First):
    # Reject journeys where the transit service terminates far away from destination (e.g. Chennai Central when Coimbatore was requested)
    if provider != "OSRM" and not is_flight:
        if a_lat and a_lon and dest_lat and dest_lon and last_mile_dist_km > 50.0:
            logger.warning(
                f"[STITCHER REJECTED] Itinerary alighting station '{alighting_station_name}' ({a_lat}, {a_lon}) "
                f"is {last_mile_dist_km:.1f} km from requested destination ({dest_lat}, {dest_lon}). Exceeds 50km catchment."
            )
            return None
        if b_lat and b_lon and origin_lat and origin_lon and first_mile_dist_km > 50.0:
            logger.warning(
                f"[STITCHER REJECTED] Itinerary boarding station '{boarding_station_name}' ({b_lat}, {b_lon}) "
                f"is {first_mile_dist_km:.1f} km from requested origin ({origin_lat}, {origin_lon}). Exceeds 50km catchment."
            )
            return None

    is_same_orig_station = (origin_name.lower().strip() == boarding_station_name.lower().strip())
    is_same_dest_station = (dest_name.lower().strip() == alighting_station_name.lower().strip())

    needs_first_mile = (first_mile_dist_km > 2.0) if is_same_orig_station else (first_mile_dist_km > 0.5 or (first_mile_dist_km > 0.1 and not is_same_orig_station))
    needs_last_mile = (last_mile_dist_km > 2.0) if is_same_dest_station else (last_mile_dist_km > 0.5 or (last_mile_dist_km > 0.1 and not is_same_dest_station))

    legs: List[JourneyLeg] = []
    connections: List[JourneyConnection] = []

    # 1. FIRST MILE LEG (ACCESS)
    first_mile_dur_min = 0.0
    fm_dist_km = 0.0
    fm_mode = "WALK"
    fm_geom = []

    if needs_first_mile:
        if b_lat and b_lon and origin_lat and origin_lon:
            fm_osrm = _get_cached_osrm_leg(
                from_name=origin_name, from_lat=origin_lat, from_lon=origin_lon,
                to_name=boarding_station_name, to_lat=b_lat, to_lon=b_lon,
                is_walk=first_mile_dist_km <= 1.5,
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

    # CATCHABILITY & WAITING TIME CALCULATION
    is_catchable, catchability_status, why_catchable_msg, waiting_min = evaluate_catchability(
        service_dep_dt=main_dep_dt,
        now=now,
        first_mile_dur_min=first_mile_dur_min if needs_first_mile else 0.0,
        boarding_buffer_min=boarding_buffer_min,
        station_name=boarding_station_name,
    )

    # Backwards-scheduled door-to-door origin departure calculation
    # Recommended origin departure = Train departure minus access duration minus boarding buffer
    if main_dep_dt:
        access_total_needed = (first_mile_dur_min if needs_first_mile else 0.0) + boarding_buffer_min
        rec_origin_dep = (main_dep_dt - timedelta(minutes=int(access_total_needed))).replace(second=0, microsecond=0)
        rec_station_arr = (rec_origin_dep + timedelta(minutes=int(first_mile_dur_min))).replace(second=0, microsecond=0)

        # For catchable departures departing very soon (within buffer), leave immediately at now
        if catchability_status == "CATCHABLE" and rec_origin_dep < now:
            door_dep_dt = now
            fm_dep_dt = now
            fm_arr_dt = now + timedelta(minutes=int(first_mile_dur_min))
        else:
            door_dep_dt = rec_origin_dep
            fm_dep_dt = rec_origin_dep
            fm_arr_dt = rec_station_arr
    else:
        door_dep_dt = now
        fm_dep_dt = now
        fm_arr_dt = now + timedelta(minutes=int(first_mile_dur_min))

    if needs_first_mile:
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
            departure_time=fm_dep_dt.isoformat(),
            arrival_time=fm_arr_dt.isoformat(),
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
    raw_mode = route.get("mode") or ("Train" if provider == "RailRadar" else "Transit")
    main_mode = normalize_mode_name(raw_mode)
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
        conn_wait = max(0.0, (main_dep_dt - fm_arr_dt).total_seconds() / 60.0) if main_dep_dt else waiting_min
        connections.append(JourneyConnection(
            from_leg_sequence=1,
            to_leg_sequence=main_seq,
            transfer_time_min=round(conn_wait, 1),
            status=ConnectionStatus.GREEN if is_catchable else ConnectionStatus.RED,
            reason=why_catchable_msg,
        ))

    # 3. LAST MILE LEG (EGRESS)
    last_mile_dur_min = 0.0
    lm_dep_dt = None
    lm_arr_dt = None

    if needs_last_mile:
        if a_lat and a_lon and dest_lat and dest_lon:
            lm_osrm = _get_cached_osrm_leg(
                from_name=alighting_station_name, from_lat=a_lat, from_lon=a_lon,
                to_name=dest_name, to_lat=dest_lat, to_lon=dest_lon,
                is_walk=last_mile_dist_km <= 1.5,
            )
            lm_dist_km = lm_osrm.get("distance_km") or (lm_osrm.get("distance_m", 0) / 1000.0) or round(last_mile_dist_km, 1)
            lm_dur_min = float(lm_osrm.get("duration_minutes") or lm_osrm.get("duration_min") or max(5, int(last_mile_dist_km * 2)))
            lm_mode = "Walk" if last_mile_dist_km <= 1.5 else "Driving"
            lm_geom = lm_osrm.get("geometry") or []
        else:
            lm_dist_km = round(last_mile_dist_km, 1)
            lm_dur_min = max(5.0, round(last_mile_dist_km * 2.5, 1))
            lm_mode = "Walk" if last_mile_dist_km <= 1.5 else "Driving"
            lm_geom = []

        if main_arr_dt:
            lm_dep_dt = main_arr_dt + timedelta(minutes=int(transfer_buffer_min))
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
            transfer_time_min=round(transfer_buffer_min, 1),
            status=ConnectionStatus.GREEN,
            reason=f"{int(transfer_buffer_min)} min station alighting buffer",
        ))

    # Calculate overall door-to-door duration and arrival (strictly positive)
    main_dur = float(main_leg.duration_min or 0.0)
    station_wait = max(0.0, (main_dep_dt - fm_arr_dt).total_seconds() / 60.0) if (main_dep_dt and needs_first_mile) else waiting_min
    if main_arr_dt:
        door_arr_dt = lm_arr_dt if (needs_last_mile and lm_arr_dt) else main_arr_dt
        tot_dur = max(1.0, (door_arr_dt - door_dep_dt).total_seconds() / 60.0)
    else:
        tot_dur = first_mile_dur_min + station_wait + main_dur + (transfer_buffer_min if needs_last_mile else 0.0) + last_mile_dur_min
        tot_dur = max(1.0, float(tot_dur))
        door_arr_dt = door_dep_dt + timedelta(minutes=int(tot_dur))

    overall_dep_time = door_dep_dt.isoformat()
    overall_arr_time = door_arr_dt.isoformat()
    overall_dep_display = _format_time_display(door_dep_dt)
    overall_arr_display = _format_time_display(door_arr_dt)

    tot_dist = sum(l.distance_km or 0 for l in legs)

    # Verification status calculation
    VERIFIED_STATUSES = (
        "Provider Verified", "Schedule Verified", "VERIFIED",
        "SCHEDULE_VERIFIED", "LIVE_VERIFIED", "PROVIDER_VERIFIED"
    )
    if all(l.verification_status in VERIFIED_STATUSES for l in legs):
        overall_vs = "SCHEDULE_VERIFIED" if any(l.verification_status in ("SCHEDULE_VERIFIED", "Schedule Verified") for l in legs) else "PROVIDER_VERIFIED"
    elif any(l.verification_status in VERIFIED_STATUSES for l in legs):
        overall_vs = "SCHEDULE_VERIFIED" if main_leg.verification_status in ("SCHEDULE_VERIFIED", "LIVE_VERIFIED", "Schedule Verified", "Provider Verified", "PROVIDER_VERIFIED", "VERIFIED") else "PARTIALLY_VERIFIED"
    else:
        overall_vs = "ROUTE_CALCULATED"

    # Combine geometries for map rendering
    combined_geometry = []
    for l in legs:
        if l.geometry:
            combined_geometry.extend(l.geometry)
    if not combined_geometry and route.get("geometry"):
        combined_geometry = list(route.get("geometry"))

    duration_breakdown = {
        "access_min": round(first_mile_dur_min, 1),
        "waiting_min": round(station_wait, 1),
        "main_transit_min": round(main_dur, 1),
        "egress_min": round(last_mile_dur_min, 1),
        "total_door_to_door_min": round(tot_dur, 1),
    }

    # Scheduled service times (from provider schedule)
    sched_dep_time = main_dep_dt.isoformat() if main_dep_dt else (main_leg.departure_time or route.get("departure_time"))
    sched_arr_time = main_arr_dt.isoformat() if main_arr_dt else (main_leg.arrival_time or route.get("arrival_time"))
    sched_dep_display = _format_time_display(main_dep_dt) if main_dep_dt else (main_leg.departure_time_display or route.get("departure_time_display"))
    sched_arr_display = _format_time_display(main_arr_dt) if main_arr_dt else (main_leg.arrival_time_display or route.get("arrival_time_display"))
    if main_dep_dt and main_arr_dt and main_arr_dt.date() > main_dep_dt.date() and "(+1 day)" not in (sched_arr_display or ""):
        sched_arr_display = f"{sched_arr_display} (+1 day)"

    # Service duration calculated from actual timestamps
    if main_dep_dt and main_arr_dt:
        service_dur_min = max(1.0, round((main_arr_dt - main_dep_dt).total_seconds() / 60.0, 1))
    else:
        service_dur_min = round(main_dur, 1) if main_dur > 0 else round(tot_dur, 1)

    journey = Journey(
        journey_id=route_id,
        origin={"name": origin_name, "lat": origin_lat, "lon": origin_lon},
        destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
        legs=legs,
        connections=connections,
        departure_time=sched_dep_time or overall_dep_time,
        arrival_time=sched_arr_time or overall_arr_time,
        departure_time_display=sched_dep_display or overall_dep_display,
        arrival_time_display=sched_arr_display or overall_arr_display,
        departure_date=main_dep_dt.strftime("%Y-%m-%d") if main_dep_dt else None,
        arrival_date=main_arr_dt.strftime("%Y-%m-%d") if main_arr_dt else None,
        departure_date_display=main_dep_dt.strftime("%b %d, %Y") if main_dep_dt else None,
        arrival_date_display=main_arr_dt.strftime("%b %d, %Y") if main_arr_dt else None,
        door_to_door_departure=overall_dep_time,
        door_to_door_arrival=overall_arr_time,
        door_to_door_departure_display=overall_dep_display,
        door_to_door_arrival_display=overall_arr_display,
        catchable=is_catchable,
        catchability_status=catchability_status,
        why_catchable=why_catchable_msg,
        catchability_reason=why_catchable_msg,
        duration_breakdown=duration_breakdown,
        total_duration_min=service_dur_min,
        duration_min=service_dur_min,
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
        distance_source=route.get("distance_source") or ("Transitous (GTFS / MOTIS)" if provider == "Transitous" and route.get("distance_km") else f"{provider}"),
        duration_source=route.get("duration_source") or f"{provider} (Calculated from timestamps)",
        verification=route.get("verification") or {
            "level": overall_vs,
            "provider": provider,
            "live": bool((route.get("realtime") or {}).get("available")),
        },
        source=route.get("source") or {
            "schedule": provider if provider != "OSRM" else None,
            "duration": route.get("duration_source") or f"{provider} (Calculated from timestamps)",
            "distance": route.get("distance_source") or f"{provider}",
            "fare": route.get("fare_source") or "Fare unavailable",
            "departure": provider,
            "arrival": provider,
            "live_tracking": "SCHEDULE DATA ONLY" if provider in ("RailRadar", "GTFSLocal", "GTFS", "Transitous") else "UNAVAILABLE",
        },
        realtime=route.get("realtime") or {"available": False, "status": "unavailable"},
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
    Deduplicates journeys with identical service identifiers or schedules.
    Discards invalid or RED-connection journeys.
    """
    stitched_journeys = []
    seen_keys = set()
    for r in candidate_routes:
        try:
            # Deduplication key
            t_num = r.get("train_number")
            prov = r.get("provider")
            d_time = r.get("departure_time")
            a_time = r.get("arrival_time")
            if t_num and prov:
                dedup_key = f"{prov}_{t_num}"
            else:
                dedup_key = f"{prov}_{r.get('mode')}_{d_time}_{a_time}"

            if dedup_key in seen_keys:
                continue

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
                seen_keys.add(dedup_key)
                stitched_journeys.append(j)
        except Exception as err:
            logger.warning(f"[J_STITCHER] Error stitching route {r.get('route_id')}: {err}")

    return stitched_journeys
