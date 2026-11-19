"""
journey_models.py -- WanderWise Door-to-Door Journey Schema

Truth-First Rule: All nullable fields must stay null when data is unavailable.
Never fabricate transit facts.
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class ConnectionStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class JourneyLegType(str, Enum):
    FIRST_MILE = "FIRST_MILE"
    MAIN_TRANSIT = "MAIN_TRANSIT"
    LAST_MILE = "LAST_MILE"


class JourneyLeg:
    """One segment of a door-to-door journey."""

    def __init__(self, sequence, mode, provider, leg_type="MAIN_TRANSIT",
                 from_stop=None, to_stop=None,
                 origin_coords=None, dest_coords=None,
                 departure_time=None, arrival_time=None,
                 departure_time_display=None, arrival_time_display=None,
                 duration_min=None, distance_km=None,
                 route_number=None, route_name=None,
                 train_number=None, train_name=None,
                 flight_number=None, airline=None, airline_name=None,
                 origin_iata=None, destination_iata=None,
                 boarding_point=None, alighting_point=None,
                 intermediate_stops=None, waiting_time_before_leg_min=None,
                 walking_distance_m=None,
                 verification_status="Unavailable", source=None,
                 fare=None, fare_source=None,
                 geometry=None, geometry_source=None,
                 is_overnight=False, operating_days=None,
                 platform=None, live_status=None, delay_min=None,
                 current_station=None, next_station=None):
        self.leg_id = f"leg_{sequence}"  # Will be overwritten by stitcher with UUID
        self.sequence = sequence
        self.type = leg_type.value if hasattr(leg_type, "value") else str(leg_type)
        self.mode = mode
        self.provider = provider
        self.from_stop = from_stop
        self.to_stop = to_stop
        self.origin = from_stop
        self.destination = to_stop
        self.origin_coords = origin_coords
        self.dest_coords = dest_coords
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.departure_time_display = departure_time_display
        self.arrival_time_display = arrival_time_display
        self.duration_min = duration_min
        self.distance_km = distance_km
        self.route_number = route_number or train_number or flight_number
        self.route_name = route_name or train_name or airline_name or airline
        self.train_number = train_number
        self.train_name = train_name
        self.flight_number = flight_number
        self.airline = airline or airline_name
        self.airline_name = airline_name or airline
        self.origin_iata = origin_iata
        self.destination_iata = destination_iata
        self.boarding_point = boarding_point or (from_stop if self.type == "MAIN_TRANSIT" else None)
        self.alighting_point = alighting_point or (to_stop if self.type == "MAIN_TRANSIT" else None)
        self.boarding_station = self.boarding_point
        self.alighting_station = self.alighting_point
        self.intermediate_stops = intermediate_stops or []
        self.waiting_time_before_leg_min = waiting_time_before_leg_min
        self.walking_distance_m = walking_distance_m
        self.verification_status = verification_status
        self.source = source
        self.fare = fare
        self.fare_source = fare_source
        self.geometry = geometry or []
        self.geometry_source = geometry_source or ("Provider Geometry" if geometry else "Schematic")
        self.is_overnight = is_overnight
        self.operating_days = operating_days or []
        self.platform = platform
        self.live_status = live_status
        self.delay_min = delay_min
        self.current_station = current_station
        self.next_station = next_station
        self.connection_status = None  # GREEN/YELLOW/RED or None

    def to_dict(self):
        return {
            "leg_id": getattr(self, 'leg_id', f"leg_{self.sequence}"),
            "sequence": self.sequence,
            "type": self.type,
            "mode": self.mode,
            "provider": self.provider,
            "from": self.from_stop,
            "to": self.to_stop,
            "from_stop": self.from_stop,
            "to_stop": self.to_stop,
            "origin": self.from_stop,
            "destination": self.to_stop,
            "origin_coords": self.origin_coords,
            "dest_coords": self.dest_coords,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "departure_time_display": self.departure_time_display,
            "arrival_time_display": self.arrival_time_display,
            "duration_min": self.duration_min,
            "distance_km": self.distance_km,
            "route_number": self.route_number,
            "route_name": self.route_name,
            "train_number": self.train_number,
            "train_name": self.train_name,
            "flight_number": self.flight_number,
            "airline": self.airline,
            "airline_name": self.airline_name,
            "origin_iata": self.origin_iata,
            "destination_iata": self.destination_iata,
            "boarding_point": self.boarding_point,
            "alighting_point": self.alighting_point,
            "boarding_station": self.boarding_station,
            "alighting_station": self.alighting_station,
            "intermediate_stops": self.intermediate_stops,
            "walking_distance_m": self.walking_distance_m,
            "fare": self.fare,
            "fare_source": self.fare_source or ("Unavailable" if self.fare is None else self.provider),
            "geometry": self.geometry,
            "geometry_source": self.geometry_source,
            "verification_status": self.verification_status,
            "operating_days": self.operating_days,
            "live_status": self.live_status,
            "delay_min": self.delay_min,
            "platform": self.platform,
            "current_station": self.current_station,
            "next_station": self.next_station,
            "is_overnight": self.is_overnight,
            "connection_status": getattr(self, 'connection_status', None),
            "waiting_time_before_leg_min": self.waiting_time_before_leg_min,
        }


class JourneyConnection:
    """The connection gap between two consecutive legs."""

    def __init__(self, from_leg_sequence, to_leg_sequence, transfer_time_min, status, note=None, reason=None):
        self.from_leg_sequence = from_leg_sequence
        self.to_leg_sequence = to_leg_sequence
        self.from_leg = from_leg_sequence
        self.to_leg = to_leg_sequence
        self.transfer_time_min = transfer_time_min
        self.status = status
        self.reason = reason or note or "Connection"

    def to_dict(self):
        st_val = self.status.value if hasattr(self.status, "value") else str(self.status)
        return {
            "from_leg": self.from_leg,
            "to_leg": self.to_leg,
            "from_leg_sequence": self.from_leg_sequence,
            "to_leg_sequence": self.to_leg_sequence,
            "transfer_time_min": self.transfer_time_min,
            "status": st_val,
            "reason": self.reason,
            "note": self.reason,
        }


class Journey:
    """
    A complete door-to-door journey consisting of one or more JourneyLegs.
    Fully backward-compatible with existing frontend schemas while adhering to the door-to-door contract.
    """

    def __init__(self, journey_id, origin, destination, legs, connections=None,
                 departure_time=None, arrival_time=None,
                 departure_time_display=None, arrival_time_display=None,
                 departure_date=None, arrival_date=None,
                 departure_date_display=None, arrival_date_display=None,
                 total_duration_min=None, duration_min=None, total_distance_km=None,
                 total_waiting_time_min=None, total_walking_distance_m=None,
                 total_transfers=0, fare=None, fare_source=None,
                 verification_status="PARTIALLY_VERIFIED",
                 geometry=None, optimization_tags=None, why_this_route=None,
                 is_overnight=False, provider=None, mode=None,
                 distance_km=None, distance_source=None, duration_source=None,
                 train_number=None, train_name=None,
                 flight_number=None, airline=None, airline_name=None,
                 origin_airport=None, destination_airport=None,
                 origin_iata=None, destination_iata=None,
                 flight_departure_time=None, flight_arrival_time=None,
                 flight_departure_time_display=None, flight_arrival_time_display=None,
                 flight_duration_minutes=None, flight_duration_display=None,
                 flight_distance_km=None, total_duration_minutes=None, total_duration_display=None,
                 verification=None, source=None, realtime=None,
                 departure_station=None, arrival_station=None,
                 operating_days=None, intermediate_stops=None,
                 platform=None, live_status=None, delay_min=None,
                 current_station=None, next_station=None,
                 route_id=None, is_long_distance_fallback=False,
                 catchable=True, catchability_status="CATCHABLE",
                 why_catchable=None, catchability_reason=None,
                 door_to_door_departure=None, door_to_door_arrival=None,
                 door_to_door_departure_display=None, door_to_door_arrival_display=None,
                 duration_breakdown=None):
        self.journey_id = journey_id
        self.route_id = route_id or journey_id

        # Accept dict or string for origin/destination
        if isinstance(origin, dict):
            self.origin_obj = origin
            self.origin_name = origin.get("name", "Origin")
        else:
            self.origin_name = str(origin) if origin else "Origin"
            self.origin_obj = {"name": self.origin_name, "lat": None, "lon": None}

        if isinstance(destination, dict):
            self.dest_obj = destination
            self.dest_name = destination.get("name", "Destination")
        else:
            self.dest_name = str(destination) if destination else "Destination"
            self.dest_obj = {"name": self.dest_name, "lat": None, "lon": None}

        self.legs = legs
        self.connections = connections or []
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.departure_time_display = departure_time_display
        self.arrival_time_display = arrival_time_display
        self.departure_date = departure_date
        self.arrival_date = arrival_date
        self.departure_date_display = departure_date_display
        self.arrival_date_display = arrival_date_display
        self.total_duration_min = total_duration_min if total_duration_min is not None else duration_min
        self.duration_min = self.total_duration_min
        self.total_distance_km = total_distance_km or distance_km
        self.total_waiting_time_min = total_waiting_time_min
        self.total_walking_distance_m = total_walking_distance_m
        self.total_transfers = total_transfers
        self.fare = fare
        self.fare_source = fare_source
        self.verification_status = verification_status
        self.geometry = geometry or []
        self.optimization_tags = optimization_tags or []
        self.why_this_route = why_this_route or []
        self.is_overnight = is_overnight

        # Door-to-door & catchability extension
        self.catchable = catchable
        self.catchability_status = catchability_status
        self.why_catchable = why_catchable or (why_this_route[0] if why_this_route else None)
        self.catchability_reason = catchability_reason or self.why_catchable
        self.door_to_door_departure = door_to_door_departure or departure_time
        self.door_to_door_arrival = door_to_door_arrival or arrival_time
        self.door_to_door_departure_display = door_to_door_departure_display or departure_time_display
        self.door_to_door_arrival_display = door_to_door_arrival_display or arrival_time_display
        self.duration_breakdown = duration_breakdown or {}

        # legacy compat
        self.provider = provider
        self.mode = mode
        self.distance_km = self.total_distance_km
        self.distance_source = distance_source
        self.duration_source = duration_source
        self.train_number = train_number
        self.train_name = train_name
        self.flight_number = flight_number
        self.airline = airline or airline_name
        self.airline_name = airline_name or airline
        self.origin_airport = origin_airport
        self.destination_airport = destination_airport
        self.origin_iata = origin_iata
        self.destination_iata = destination_iata
        self.flight_departure_time = flight_departure_time
        self.flight_arrival_time = flight_arrival_time
        self.flight_departure_time_display = flight_departure_time_display
        self.flight_arrival_time_display = flight_arrival_time_display
        self.flight_duration_minutes = flight_duration_minutes
        self.flight_duration_display = flight_duration_display
        self.flight_distance_km = flight_distance_km
        self.total_duration_minutes = total_duration_minutes or self.total_duration_min
        self.total_duration_display = total_duration_display
        self.verification = verification
        self.source = source
        self.realtime = realtime
        self.departure_station = departure_station
        self.arrival_station = arrival_station
        self.operating_days = operating_days or []
        self.intermediate_stops = intermediate_stops or []
        self.platform = platform
        self.live_status = live_status
        self.delay_min = delay_min
        self.current_station = current_station
        self.next_station = next_station
        self.is_long_distance_fallback = is_long_distance_fallback

    def to_dict(self):
        return {
            "journey_id": self.journey_id,
            "route_id": self.route_id,
            "origin": self.origin_obj,
            "destination": self.dest_obj,
            "origin_name": self.origin_name,
            "dest_name": self.dest_name,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "departure_time_display": self.departure_time_display,
            "arrival_time_display": self.arrival_time_display,
            "departure_date": self.departure_date,
            "arrival_date": self.arrival_date,
            "departure_date_display": self.departure_date_display,
            "arrival_date_display": self.arrival_date_display,
            "door_to_door_departure": self.door_to_door_departure,
            "door_to_door_arrival": self.door_to_door_arrival,
            "door_to_door_departure_display": self.door_to_door_departure_display,
            "door_to_door_arrival_display": self.door_to_door_arrival_display,
            "catchable": self.catchable,
            "catchability_status": self.catchability_status,
            "why_catchable": self.why_catchable,
            "catchability_reason": self.catchability_reason,
            "duration_breakdown": self.duration_breakdown,
            "total_duration_min": self.total_duration_min,
            "duration_min": self.total_duration_min,
            "total_distance_km": self.total_distance_km,
            "distance_km": self.total_distance_km,
            "total_waiting_time_min": self.total_waiting_time_min,
            "total_walking_distance_m": self.total_walking_distance_m,
            "walking_distance_m": self.total_walking_distance_m,
            "total_transfers": self.total_transfers,
            "transfers": self.total_transfers,
            "fare": self.fare,
            "fare_source": self.fare_source,
            "verification_status": self.verification_status,
            "verification": self.verification or {"level": self.verification_status, "provider": self.provider, "live": bool((self.realtime or {}).get("available"))},
            "source": self.source or {},
            "realtime": self.realtime or {"available": False, "status": "unavailable"},
            "geometry": self.geometry,
            "optimization_tags": self.optimization_tags,
            "why_this_route": self.why_this_route,
            "is_overnight": self.is_overnight,
            "provider": self.provider,
            "mode": self.mode,
            "distance_source": self.distance_source,
            "duration_source": self.duration_source,
            "train_number": self.train_number,
            "train_name": self.train_name,
            "flight_number": self.flight_number,
            "airline": self.airline,
            "airline_name": self.airline_name,
            "origin_airport": self.origin_airport,
            "destination_airport": self.destination_airport,
            "origin_iata": self.origin_iata,
            "destination_iata": self.destination_iata,
            "flight_departure_time": self.flight_departure_time,
            "flight_arrival_time": self.flight_arrival_time,
            "flight_departure_time_display": self.flight_departure_time_display,
            "flight_arrival_time_display": self.flight_arrival_time_display,
            "flight_duration_minutes": self.flight_duration_minutes,
            "flight_duration_display": self.flight_duration_display,
            "flight_distance_km": self.flight_distance_km,
            "total_duration_minutes": self.total_duration_minutes,
            "total_duration_display": self.total_duration_display,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "operating_days": self.operating_days,
            "intermediate_stops": self.intermediate_stops,
            "platform": self.platform,
            "live_status": self.live_status,
            "delay_min": self.delay_min,
            "current_station": self.current_station,
            "next_station": self.next_station,
            "is_long_distance_fallback": self.is_long_distance_fallback,
            "legs": [l.to_dict() for l in self.legs],
            "connections": [c.to_dict() for c in self.connections],
        }
