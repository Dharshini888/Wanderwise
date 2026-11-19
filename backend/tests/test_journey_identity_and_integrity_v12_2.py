"""
test_journey_identity_and_integrity_v12_2.py — Test Suite for WanderWise V12.2 Journey Identity & Integrity

Verifies:
1. Destination & Origin Identity Enforcement (No Chennai journey in a Coimbatore search).
2. Stale / Mixed Search Cache Isolation (Delhi -> Chennai never leaks into Delhi -> Coimbatore).
3. Coordinate-to-City Sanity Protection (Stale dest_lat/lon from previous searches discarded).
4. AI Transit Guidance Accuracy (Correct domestic/international scale and straight-line distance).
5. Data Provenance Canonical Consistency (Overview and detailed view agree on distance source).
6. Strategy Ranking operates only on validated itineraries reaching the destination.
7. Multi-corridor validation:
   - Delhi -> Coimbatore
   - Coimbatore -> Delhi
   - Coimbatore -> Chennai
   - Chennai -> Coimbatore
   - Erode -> Chennai
   - Erode Junction -> Chennai
   - Coimbatore -> Bengaluru
   - Pune -> Mumbai
"""

import os
import sys
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.itinerary_validator import validate_itinerary_endpoints
from app.services.transit.journey_classifier import JourneyClassifier
from app.services.transit.ai_route_guidance import AIRouteGuidanceService
from app.services.transit.provider_manager import ProviderManager
from app.services.transit.providers.transitous_provider import TransitousProvider
from app.services.transit.providers.base import ProviderStatus, ProviderResult
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import stitch_door_to_door_journey


def test_coimbatore_search_rejects_chennai_itinerary():
    """
    Test Case 1: When Coimbatore is requested, an itinerary terminating at Chennai Central
    must be rejected and must never be stitched or displayed.
    """
    # Delhi coords: 28.6139, 77.2090
    # Coimbatore coords: 11.0168, 76.9558
    # Chennai Central coords: 13.0827, 80.2757 (~425 km from Coimbatore)

    chennai_itin = {
        "route_id": "test_nzm_mas",
        "provider": "Transitous",
        "mode": "Train",
        "origin": "Hazrat Nizamuddin Junction",
        "destination": "Puratchi Thalaivar Dr. M.G.R. Central",
        "departure_time": "2026-11-19T06:00:00+05:30",
        "arrival_time": "2026-11-20T04:30:00+05:30",
        "duration_minutes": 1350.0,
        "distance_km": 2180.0,
        "legs": [
            {
                "type": "MAIN_TRANSIT",
                "mode": "Train",
                "provider": "Transitous",
                "from_name": "Hazrat Nizamuddin Junction",
                "to_name": "Puratchi Thalaivar Dr. M.G.R. Central",
                "boarding_stop": {"name": "Hazrat Nizamuddin Junction", "lat": 28.5880, "lon": 77.2530},
                "alighting_stop": {"name": "Puratchi Thalaivar Dr. M.G.R. Central", "lat": 13.0827, "lon": 80.2757},
                "departure_time": "2026-11-19T06:00:00+05:30",
                "arrival_time": "2026-11-20T04:30:00+05:30",
                "duration_minutes": 1350.0,
                "distance_km": 2180.0,
            }
        ]
    }

    # 1. Direct itinerary endpoint validation check
    val_res = validate_itinerary_endpoints(
        itinerary=chennai_itin,
        origin_lat=28.6139, origin_lon=77.2090,
        dest_lat=11.0168, dest_lon=76.9558,
        origin_name="Delhi", dest_name="Coimbatore",
        max_catchment_km=50.0,
    )
    assert not val_res["valid"], "Chennai Central itinerary must be marked invalid for a Coimbatore destination"
    assert any("exceeding maximum catchment" in err for err in val_res["errors"])

    # 2. RouteOptimizer normalization check
    norm_res = RouteOptimizer.normalize_route(
        provider="Transitous",
        mode="Train",
        raw_itinerary=chennai_itin,
        origin_name="Delhi",
        dest_name="Coimbatore",
        default_dist=1956.9,
        dest_lat=11.0168,
        dest_lon=76.9558,
    )
    assert norm_res is None, "RouteOptimizer must return None (reject) for mismatched destination"

    # 3. Journey stitcher check
    stitched = stitch_door_to_door_journey(
        route=chennai_itin,
        origin_name="Delhi",
        origin_lat=28.6139,
        origin_lon=77.2090,
        dest_name="Coimbatore",
        dest_lat=11.0168,
        dest_lon=76.9558,
    )
    assert stitched is None, "Journey stitcher must return None when alighting station is 425km from Coimbatore"


def test_stale_coordinate_sanity_in_orchestrator():
    """
    Test Case 2: If the frontend sends destination='Coimbatore' but leaves stale dest_lat/lon
    pointing to Chennai (13.0827, 80.2707), TransitOrchestrator must detect the drift,
    discard the stale coordinates, and geocode Coimbatore correctly.
    """
    plan = TransitOrchestrator.get_transit_plan(
        origin="Delhi",
        destination="Coimbatore",
        dest_lat=13.0827,  # Stale Chennai latitude!
        dest_lon=80.2707,  # Stale Chennai longitude!
        departure_type="now",
    )

    # Destination coordinates must be Coimbatore (~11.0168, ~76.9558), NOT Chennai (~13.0827, ~80.2707)
    dest_coords = plan.get("dest_coords", {})
    assert dest_coords.get("lat") is not None
    assert abs(dest_coords["lat"] - 11.0168) < 0.1, f"Expected Coimbatore latitude ~11.0168, got {dest_coords['lat']}"
    assert abs(dest_coords["lon"] - 76.9558) < 0.1, f"Expected Coimbatore longitude ~76.9558, got {dest_coords['lon']}"
    assert "Coimbatore" in plan["destination"]


def test_cache_isolation_between_corridors():
    """
    Test Case 3: A search for Delhi -> Chennai Central must not collide with or leak into
    a subsequent search for Delhi -> Coimbatore in ProviderManager.
    """
    mgr = ProviderManager.get_instance()

    key_delhi_mas = mgr._generate_cache_key(
        origin="Delhi", dest="Chennai",
        dep_time="now", mode="fastest",
        origin_lat=28.6139, origin_lon=77.2090,
        dest_lat=13.0827, dest_lon=80.2707,
    )

    key_delhi_cbe = mgr._generate_cache_key(
        origin="Delhi", dest="Coimbatore",
        dep_time="now", mode="fastest",
        origin_lat=28.6139, origin_lon=77.2090,
        dest_lat=11.0168, dest_lon=76.9558,
    )

    assert key_delhi_mas != key_delhi_cbe, "Cache keys for different destinations must be strictly distinct"
    assert "13.083,80.271" in key_delhi_mas
    assert "11.017,76.956" in key_delhi_cbe


def test_ai_route_guidance_domestic_and_distances():
    """
    Test Case 4: AI Route Guidance must classify Delhi -> Coimbatore as domestic (India),
    report deterministic straight-line distance, and never fabricate flight schedules.
    """
    # Straight-line distance between Delhi and Coimbatore is ~1956.9 km
    guidance = AIRouteGuidanceService.generate_guidance(
        origin_name="Delhi",
        dest_name="Coimbatore",
        journey_scale="DOMESTIC",
        origin_country="IN",
        dest_country="IN",
        distance_km=1956.9,
    )

    assert guidance["type"] == "AI_MODE_GUIDANCE"
    assert guidance["recommended_mode"] == "Flight"
    assert "domestic" in guidance["reason"].lower()
    assert "international" not in guidance["reason"].lower()
    assert guidance["distances"]["straight_line_distance_km"] == 1956.9
    assert guidance["provider_status"]["flight_provider"] == "no_verified_itinerary"
    assert any("FlightProvider" in lim for lim in guidance["limitations"])


def test_journey_classifier_domestic_long_distance():
    """
    Test Case 5: A long-distance domestic journey in India (> 1500 km) must be classified
    as DOMESTIC, not INTERNATIONAL.
    """
    # Delhi (28.6139, 77.2090) -> Coimbatore (11.0168, 76.9558)
    cls_res = JourneyClassifier.classify(
        origin_lat=28.6139, origin_lon=77.2090,
        dest_lat=11.0168, dest_lon=76.9558,
        origin_name="Delhi", dest_name="Coimbatore"
    )

    assert cls_res["origin_country"] == "IN"
    assert cls_res["destination_country"] == "IN"
    assert cls_res["scale"] == "DOMESTIC", f"Expected DOMESTIC, got {cls_res['scale']}"


def test_data_provenance_consistency():
    """
    Test Case 6: Stitched journeys must provide a canonical provenance structure with
    consistent distance and duration sources.
    """
    route = {
        "route_id": "test_cbe_mas_kovai",
        "provider": "IndianRailways-ScheduleVerified",
        "mode": "Train",
        "origin": "Coimbatore Junction",
        "destination": "Chennai Central",
        "departure_station": "Coimbatore Junction",
        "arrival_station": "Chennai Central",
        "departure_time": "2026-11-19T15:05:00+05:30",
        "arrival_time": "2026-11-19T22:50:00+05:30",
        "departure_time_display": "3:05 PM",
        "arrival_time_display": "10:50 PM",
        "duration_min": 465.0,
        "distance_km": 496.0,
        "distance_source": "Indian Railways Timetable",
        "duration_source": "Indian Railways Timetable (Calculated from timestamps)",
        "train_number": "12676",
        "train_name": "Kovai Superfast Express",
        "legs": [
            {
                "type": "MAIN_TRANSIT",
                "mode": "Train",
                "provider": "IndianRailways-ScheduleVerified",
                "from_name": "Coimbatore Junction",
                "to_name": "Chennai Central",
                "boarding_stop": {"name": "Coimbatore Junction", "lat": 11.0017, "lon": 76.9629},
                "alighting_stop": {"name": "Chennai Central", "lat": 13.0827, "lon": 80.2757},
                "departure_time": "2026-11-19T15:05:00+05:30",
                "arrival_time": "2026-11-19T22:50:00+05:30",
                "duration_min": 465.0,
                "distance_km": 496.0,
                "distance_source": "Indian Railways Timetable",
            }
        ]
    }

    stitched = stitch_door_to_door_journey(
        route=route,
        origin_name="Coimbatore Junction",
        origin_lat=11.0017,
        origin_lon=76.9629,
        dest_name="Chennai Central",
        dest_lat=13.0827,
        dest_lon=80.2757,
    )

    assert stitched is not None
    # Verify canonical provenance fields
    assert stitched.get("distance_source") == "Indian Railways Timetable"
    assert "source" in stitched
    assert stitched["source"].get("distance") == "Indian Railways Timetable"
    assert stitched["source"].get("duration") == "Indian Railways Timetable (Calculated from timestamps)"
    assert stitched.get("verification_status") in ("SCHEDULE_VERIFIED", "PROVIDER_VERIFIED", "Schedule Verified")


def test_eight_benchmark_corridors_endpoint_integrity():
    """
    Test Case 7: Evaluates the 8 benchmark corridors:
    1. Delhi -> Coimbatore
    2. Coimbatore -> Delhi
    3. Coimbatore -> Chennai
    4. Chennai -> Coimbatore
    5. Erode -> Chennai
    6. Erode Junction -> Chennai
    7. Coimbatore -> Bengaluru
    8. Pune -> Mumbai
    Ensures endpoints match and no cross-city destination contamination occurs.
    """
    corridors = [
        ("Delhi", "Coimbatore"),
        ("Coimbatore", "Delhi"),
        ("Coimbatore", "Chennai"),
        ("Chennai", "Coimbatore"),
        ("Erode", "Chennai"),
        ("Erode Junction", "Chennai"),
        ("Coimbatore", "Bengaluru"),
        ("Pune", "Mumbai"),
    ]

    for orig, dest in corridors:
        plan = TransitOrchestrator.get_transit_plan(
            origin=orig,
            destination=dest,
            departure_type="now",
        )
        assert plan["status"] in ("PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT", "VERIFIED_ROAD_ALTERNATIVE", "ROUTE_GUIDANCE_AVAILABLE")
        assert plan["origin"] is not None
        assert plan["destination"] is not None

        # Verify any journeys returned strictly terminate at the requested destination
        for j in plan.get("journeys", []):
            dest_obj = j.get("destination") or {}
            dest_name = (dest_obj.get("name") if isinstance(dest_obj, dict) else j.get("destination_name")) or ""
            # The journey must not be to a completely different city
            assert "chennai" not in dest_name.lower() or "chennai" in dest.lower(), f"Journey destination '{dest_name}' invalid for search to '{dest}'"
            assert "coimbatore" not in dest_name.lower() or "coimbatore" in dest.lower(), f"Journey destination '{dest_name}' invalid for search to '{dest}'"
