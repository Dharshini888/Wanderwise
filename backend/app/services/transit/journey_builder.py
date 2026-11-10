"""
journey_builder.py -- WanderWise Journey Builder

Converts a normalized flat route dict (output of RouteOptimizer.normalize_route)
into a structured Journey object with typed JourneyLegs and JourneyConnections.

Truth-First: No values are invented. Missing data becomes null.
Backward-compatible: wraps single-provider routes in a 1-leg journey.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional

from .journey_models import Journey, JourneyLeg, ConnectionStatus
from .connection_engine import compute_connections, has_impossible_connection

logger = logging.getLogger(__name__)

# Verification status labels
VERIFIED_STATUSES = {"Provider Verified", "Schedule Verified", "VERIFIED"}


def _map_mode_to_icon(mode: str) -> str:
    m = (mode or "").lower()
    if "train" in m or "rail" in m:
        return "🚆"
    if "bus" in m:
        return "🚌"
    if "walk" in m:
        return "🚶"
    if "metro" in m or "subway" in m:
        return "🚇"
    if "flight" in m or "air" in m:
        return "✈️"
    if "road" in m or "car" in m or "driv" in m:
        return "🚗"
    if "ferry" in m:
        return "⛴️"
    return "🚌"


def _overall_verification(legs: List[JourneyLeg]) -> str:
    """Determine journey-level verification from leg verifications."""
    if not legs:
        return "Estimated"
    statuses = [l.verification_status for l in legs]
    if all(s in VERIFIED_STATUSES for s in statuses):
        return "Provider Verified"
    if any(s in VERIFIED_STATUSES for s in statuses):
        return "Partially Verified"
    if any(s == "Provider Calculated" for s in statuses):
        return "Provider Calculated"
    return "Route Calculated"


def _build_legs_from_route(route: Dict[str, Any]) -> List[JourneyLeg]:
    """
    Builds a list of JourneyLeg objects from a normalized route dict.

    If the route already has a multi-leg structure (legs field), map each leg.
    Otherwise create a single leg from the route-level fields.
    """
    raw_legs = route.get("legs") or []
    provider = route.get("provider", "Unknown")
    verification = route.get("verification_status", "Estimated")

    if raw_legs:
        legs = []
        for i, raw in enumerate(raw_legs):
            leg = JourneyLeg(
                sequence=i,
                mode=raw.get("mode") or route.get("mode", "Transit"),
                provider=raw.get("provider") or provider,
                from_stop=raw.get("from_name") or raw.get("from_stop") or raw.get("boarding_stop", {}).get("name"),
                to_stop=raw.get("to_name") or raw.get("to_stop") or raw.get("alighting_stop", {}).get("name"),
                departure_time=raw.get("departure_time"),
                arrival_time=raw.get("arrival_time"),
                departure_time_display=raw.get("departure_time_display"),
                arrival_time_display=raw.get("arrival_time_display"),
                duration_min=raw.get("duration_minutes") or raw.get("duration_min"),
                distance_km=raw.get("distance_km"),
                route_number=raw.get("route_number") or raw.get("route_short_name"),
                route_name=raw.get("route_name") or raw.get("route_long_name"),
                train_number=raw.get("train_number"),
                train_name=raw.get("train_name"),
                boarding_point=raw.get("boarding_stop", {}).get("name") if isinstance(raw.get("boarding_stop"), dict) else None,
                alighting_point=raw.get("alighting_stop", {}).get("name") if isinstance(raw.get("alighting_stop"), dict) else None,
                intermediate_stops=raw.get("intermediate_stops") or [],
                verification_status=raw.get("verification_status") or verification,
                source=raw.get("source") or provider,
                geometry=raw.get("geometry") or [],
            )
            legs.append(leg)
        return legs

    # Single-leg route — wrap entire route as one leg
    mode = route.get("mode", "Transit")
    # For train routes, mode may be "Train"
    if route.get("train_number"):
        mode = "Train"

    single = JourneyLeg(
        sequence=0,
        mode=mode,
        provider=provider,
        from_stop=route.get("departure_station") or route.get("origin"),
        to_stop=route.get("arrival_station") or route.get("destination"),
        departure_time=route.get("departure_time"),
        arrival_time=route.get("arrival_time"),
        departure_time_display=route.get("departure_time_display"),
        arrival_time_display=route.get("arrival_time_display"),
        duration_min=route.get("duration_min"),
        distance_km=route.get("distance_km"),
        train_number=route.get("train_number"),
        train_name=route.get("train_name"),
        intermediate_stops=route.get("intermediate_stops") or [],
        verification_status=verification,
        source=provider,
        geometry=route.get("geometry") or [],
        is_overnight=route.get("is_overnight", False),
        operating_days=route.get("operating_days") or [],
        platform=route.get("platform"),
        live_status=route.get("live_status"),
        delay_min=route.get("delay_min"),
        current_station=route.get("current_station"),
        next_station=route.get("next_station"),
    )
    return [single]


def build_journey_from_route(route: Dict[str, Any]) -> Optional[Journey]:
    """
    Builds a Journey from a normalized flat route dict.
    Returns None if the journey would be invalid.
    """
    try:
        legs = _build_legs_from_route(route)
        if not legs:
            return None

        # Compute connections between legs
        legs_dicts = [{"departure_time": l.departure_time, "arrival_time": l.arrival_time} for l in legs]
        connections, total_waiting = compute_connections(legs_dicts)

        # Discard journeys with RED (impossible) connections
        if has_impossible_connection(connections):
            logger.warning(
                "[JourneyBuilder] Discarding journey with impossible connection: %s -> %s",
                route.get("origin"), route.get("destination")
            )
            return None

        # Compute total walking distance across all legs
        total_walking = route.get("walking_distance_m") or route.get("total_walking_distance_m")
        if total_walking is None:
            walk_sum = sum(
                (l.distance_km or 0) * 1000
                for l in legs if "walk" in (l.mode or "").lower()
            )
            total_walking = walk_sum if walk_sum > 0 else None

        # Transfers = number of connections that are not walking
        non_walk_legs = [l for l in legs if "walk" not in (l.mode or "").lower()]
        total_transfers = max(0, len(non_walk_legs) - 1)

        overall_vs = _overall_verification(legs)

        # Build optimization tags
        tags = []
        if route.get("optimization_tags"):
            tags = route["optimization_tags"]
        else:
            if route.get("provider") in ("RailRadar", "GTFS", "Transitous"):
                tags.append("Scheduled Service")
            if route.get("is_overnight"):
                tags.append("Overnight Journey")

        journey = Journey(
            journey_id=route.get("route_id") or f"journey_{uuid.uuid4().hex[:8]}",
            route_id=route.get("route_id"),
            origin=route.get("origin", ""),
            destination=route.get("destination", ""),
            legs=legs,
            connections=connections,
            departure_time=route.get("departure_time"),
            arrival_time=route.get("arrival_time"),
            departure_time_display=route.get("departure_time_display"),
            arrival_time_display=route.get("arrival_time_display"),
            total_duration_min=route.get("duration_min"),
            total_waiting_time_min=total_waiting if total_waiting > 0 else None,
            total_walking_distance_m=total_walking,
            total_transfers=total_transfers,
            fare=route.get("fare"),
            fare_source=route.get("fare_source"),
            verification_status=overall_vs,
            geometry=route.get("geometry") or [],
            optimization_tags=tags,
            why_this_route=route.get("why_this_route") or [],
            is_overnight=route.get("is_overnight", False),
            # backward-compat flat fields
            provider=route.get("provider"),
            mode=route.get("mode"),
            distance_km=route.get("distance_km"),
            distance_source=route.get("distance_source"),
            duration_source=route.get("duration_source"),
            train_number=route.get("train_number"),
            train_name=route.get("train_name"),
            departure_station=route.get("departure_station"),
            arrival_station=route.get("arrival_station"),
            operating_days=route.get("operating_days") or [],
            intermediate_stops=route.get("intermediate_stops") or [],
            platform=route.get("platform"),
            live_status=route.get("live_status"),
            delay_min=route.get("delay_min"),
            current_station=route.get("current_station"),
            next_station=route.get("next_station"),
            is_long_distance_fallback=route.get("is_long_distance_fallback", False),
        )
        return journey

    except Exception as e:
        logger.error("[JourneyBuilder] Failed to build journey: %s", e, exc_info=True)
        return None


def build_journeys_from_routes(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts a list of normalized route dicts into Journey dicts.
    Discards journeys with impossible connections.
    Returns list of Journey.to_dict() dicts.
    """
    journeys = []
    for route in routes:
        journey = build_journey_from_route(route)
        if journey:
            journeys.append(journey.to_dict())
    return journeys
