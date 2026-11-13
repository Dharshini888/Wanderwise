"""
test_global_itinerary_validation_and_personalization.py

Comprehensive Regression Test Suite for WanderWise Global Itinerary Validation and Personalization Architecture:
1. Trip-Wide Duplicate Prevention: Zero duplicate attractions or dining venues across multi-day trips.
2. Strict Public-Place and POI Validation: Generic observation decks ("Смотровая площадка", "Observation Deck")
   and private residences ("Besteci Faik Canselen'in Evi", "Erbilgin Yalısı", "Akatlar Kültür Merkezi") strictly rejected.
3. 9 Independent Field-Level Verification Statuses & Honest Provenance: "Verified Coordinates Only (Access Unverified)"
   displayed when only coordinates are verified; "Public Access Verified" verified; private property rejected.
4. Interest-Based Personalization & Interest Coverage Report: Mandatory ranking by selected interests
   (History, Street Food, Photography, Shopping, Nature) with structured coverage report.
5. Correct Dining Classification & Dietary "No Preference" Handling: Restaurants categorized as Dining/Meal with
   ticket_price=0.0; "No Preference" is never treated as vegetarian.
6. Route & Transport Validation: Walking recommended for distances <= 1.5 km; straight-line vs road routing labeled;
   daily stops sequenced geographically.
7. Weather Accuracy & 14-Day Live Forecast Horizon: Distant dates return "Forecast unavailable" with "Seasonal Climate Standard".
8. Budget Transparency, Room Occupancy & Nationality-Aware Visa: 1 family room for 2 adults + 1 child;
   Indian passport Turkey e-Visa estimation; distinct contingency reserve (5-8%) and surplus buffer.
9. Arrival & Departure Handling: Day 1 starts >= 14:00 with check-in buffer; Final Day reserves 3.5-hour airport transfer buffer.
10. Global Scalability: Architecture operates dynamically worldwide without hardcoded destination hacks.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

import pytest
from datetime import date, timedelta
from typing import Dict, Any, List

from app.services.budget_allocation_service import BudgetAllocationService
from app.services.poi_service import (
    is_valid_destination_poi,
    is_generic_or_ambiguous_poi,
    is_private_or_non_tourist_venue,
    fetch_real_pois_for_destination,
    WORLD_POI_DATABASE
)
from app.services.route_optimizer import (
    estimate_travel_transition,
    optimize_daily_route,
    haversine_distance_km
)
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.services.ai_service import generate_structured_itinerary
from app.routes.weather import get_weather


# =====================================================================
# 1. Trip-Wide Duplicate Prevention
# =====================================================================
def test_trip_wide_duplicate_prevention_istanbul():
    """Verify that a 7-day trip to Istanbul has zero duplicate attractions across all days."""
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=7,
        budget=500000,
        interests="History, Street Food, Photography, Shopping, Nature",
        travel_style="family",
        group_size=3,
        currency="INR",
        country="Turkey",
        origin_city="Coimbatore",
        start_date="2027-03-15",
        end_date="2027-03-21",
        trip_preferences={
            "adults": 2,
            "children": 1,
            "dietary_preferences": "No Preference",
            "budget_type": "mid_range"
        }
    )

    days = itinerary.get("days", [])
    assert len(days) == 7, f"Expected 7 days, got {len(days)}"

    scheduled_venues = []
    seen_entity_keys = set()
    from app.services.pricing.canonical_pricing_registry import normalize_place_entity_key

    for d in days:
        acts = d.get("activities", [])
        assert len(acts) >= 2, f"Day {d.get('day_number')} must have at least 2 activities"
        for act in acts:
            p = act.get("place") if isinstance(act.get("place"), dict) else {}
            name = p.get("name") or act.get("title")
            act_type = act.get("activity_type")
            if act_type == "area_suggestion":
                continue
            key = normalize_place_entity_key(name)
            assert key not in seen_entity_keys, f"Duplicate venue '{name}' (key: '{key}') detected on Day {d.get('day_number')}!"
            seen_entity_keys.add(key)
            scheduled_venues.append(name)

    assert len(seen_entity_keys) >= 15, f"Expected at least 15 unique venues, got {len(seen_entity_keys)}"


# =====================================================================
# 2. Strict Public-Place and POI Validation
# =====================================================================
def test_generic_observation_deck_and_label_rejection():
    """Verify that generic observation decks, lookout points, and city centers are strictly rejected across languages."""
    generic_bad_names = [
        "Смотровая площадка",
        "Обзорная площадка",
        "Панорамный вид",
        "Observation Deck",
        "Viewing Platform",
        "Panoramic Viewpoint",
        "Mirador",
        "Seyir Terası",
        "Manzara Noktası",
        "Aussichtsplattform",
        "City Center",
        "Historic City Center",
        "Historic Center"
    ]
    for bad_name in generic_bad_names:
        is_gen, reason = is_generic_or_ambiguous_poi(bad_name)
        assert is_gen is True, f"Expected '{bad_name}' to be detected as generic/ambiguous POI"
        assert is_valid_destination_poi({"name": bad_name}, "Istanbul") is False, f"Expected '{bad_name}' to be rejected by is_valid_destination_poi"


def test_private_property_and_civic_holding_rejection():
    """Verify that private residences, apartments, mansions, and administrative civic centers are rejected."""
    private_bad_venues = [
        ("Besteci Faik Canselen'in Evi", ""),
        ("Erbilgin Yalısı", ""),
        ("Akatlar Kültür Merkezi", "Civic Center"),
        ("Seylanovs house", ""),
        ("Ahmet Bey Apartmanı", ""),
        ("Holding A.Ş.", "Business"),
        ("Private Villa", ""),
        ("Частный дом", "")
    ]
    for name, cat in private_bad_venues:
        is_priv, reason = is_private_or_non_tourist_venue(name, cat)
        assert is_priv is True, f"Expected '{name}' to be detected as private/non-tourist venue"
        assert is_valid_destination_poi({"name": name, "category": cat}, "Istanbul") is False

    # Famous public museums must NOT be rejected
    famous_public = [
        ("Anne Frank House", "Museum"),
        ("Casa Batlló", "Museum"),
        ("White House", "Historical site"),
        ("Hagia Sophia Grand Mosque", "Cultural / Heritage")
    ]
    for pub_name, pub_cat in famous_public:
        is_priv, _ = is_private_or_non_tourist_venue(pub_name, pub_cat)
        assert is_priv is False, f"Famous public landmark '{pub_name}' must NOT be flagged as private"


# =====================================================================
# 3. 9 Independent Field-Level Verification Statuses & Honest Provenance
# =====================================================================
def test_nine_field_level_verification_statuses():
    """Verify that all 9 independent verification fields exist, public accessibility is verified, and honest provenance is enforced."""
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=3,
        budget=300000,
        interests="History, Street Food, Photography",
        travel_style="family",
        currency="INR",
        country="Turkey"
    )

    days = itinerary.get("days", [])
    for d in days:
        for act in d.get("activities", []):
            prov = act.get("provenance") or {}
            # 1. identity_status
            assert "identity_status" in prov, "Missing identity_status"
            assert prov["identity_status"] in ["Verified Place", "Verified Dining", "Estimated", "Unavailable"]

            # 2. public_accessibility
            assert "public_accessibility" in prov, "Missing public_accessibility"
            assert prov["public_accessibility"] in ["Public Access Verified", "Public Access Unverified"]
            assert prov["public_accessibility"] != "Publicly Inaccessible / Private Property"

            # 3. location_status
            assert "location_status" in prov, "Missing location_status"

            # 4. coordinate_status
            assert "coordinate_status" in prov, "Missing coordinate_status"

            # 5. hours_status
            assert "hours_status" in prov, "Missing hours_status"

            # 6. price_status
            assert "price_status" in prov, "Missing price_status"

            # 7. route_status
            assert "route_status" in prov, "Missing route_status"

            # 8. rating_status
            assert "rating_status" in prov, "Missing rating_status"

            # 9. last_verified
            assert "last_verified" in prov, "Missing last_verified"

            # Honest Provenance Rule: If place_verification does not contain a recognized registry,
            # it must not claim "Verified Knowledge Base" or "Verified Attraction" on coordinates alone.
            pv = prov.get("place_verification", "")
            if "Coordinates Only" in pv:
                assert prov.get("overall_status") != "Verified", f"Coordinates-only venue '{act.get('title')}' must not be marked Verified"


# =====================================================================
# 4. Interest-Based Personalization & Interest Coverage Report
# =====================================================================
def test_interest_coverage_report():
    """Verify that selected interests (History, Street Food, Photography, Shopping, Nature) generate a complete coverage report."""
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=7,
        budget=500000,
        interests="History, Street Food, Photography, Shopping, Nature",
        travel_style="family",
        currency="INR",
        country="Turkey"
    )

    report = itinerary.get("interest_coverage_report") or (itinerary.get("days", [])[0].get("interest_coverage_report"))
    assert report is not None, "Missing interest_coverage_report in itinerary payload"

    selected = report.get("selected_interests", [])
    assert "History" in selected
    assert "Street Food" in selected
    assert "Photography" in selected
    assert "Shopping" in selected
    assert "Nature" in selected

    represented = report.get("interests_represented", [])
    assert len(represented) == 5, f"Expected all 5 interests to be represented, got: {represented}"
    assert report.get("coverage_percentage") == 100.0


# =====================================================================
# 5. Correct Dining Classification & Dietary Handling
# =====================================================================
def test_dining_classification_and_no_preference():
    """Verify restaurants are strictly classified as Dining with ticket_price=0, and 'No Preference' is not vegetarian."""
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=4,
        budget=400000,
        interests="History, Street Food",
        travel_style="family",
        currency="INR",
        country="Turkey",
        trip_preferences={
            "dietary_preferences": "No Preference",
            "food": "No Preference"
        }
    )

    found_dining = False
    for d in itinerary.get("days", []):
        for act in d.get("activities", []):
            if act.get("activity_type") == "meal":
                found_dining = True
                p = act.get("place") or {}
                assert p.get("category") == "Dining" or act.get("is_area_suggestion") is True
                assert act.get("ticket_price") == 0.0, "Dining activity ticket_price must be 0.0"
                # Must not falsely claim Vegetarian when user selected "No Preference"
                diet_tag = act.get("dietary_suitability")
                assert diet_tag != "Vegetarian", f"Dining '{act.get('title')}' falsely labeled Vegetarian for 'No Preference' user"

    assert found_dining is True, "Itinerary should contain at least one dining activity"


# =====================================================================
# 6. Route & Transport Validation
# =====================================================================
def test_short_distance_walking_recommendation():
    """Verify that transit legs <= 1.5 km are recommended as Walking and labeled with routing methodology."""
    # Hagia Sophia to Basilica Cistern is ~0.35 km
    trans = estimate_travel_transition(41.0086, 28.9802, 41.0084, 28.9779, "Istanbul")
    assert trans["travel_mode"] == "Walking"
    assert trans["distance_km"] <= 1.5
    assert "Straight-line" in trans["routing_methodology"] or "OSRM" in trans["routing_methodology"]


def test_daily_route_optimization_heuristic():
    """Verify that optimize_daily_route orders stops to minimize distance and avoid zigzagging."""
    stops = [
        {"name": "Taksim", "latitude": 41.0369, "longitude": 28.9850},
        {"name": "Sultanahmet", "latitude": 41.0086, "longitude": 28.9802},
        {"name": "Karaköy", "latitude": 41.0242, "longitude": 28.9779}
    ]
    ordered = optimize_daily_route(stops)
    # Starting at Taksim (41.0369), Karaköy (41.0242) is closer than Sultanahmet (41.0086)
    assert ordered[0]["name"] == "Taksim"
    assert ordered[1]["name"] == "Karaköy"
    assert ordered[2]["name"] == "Sultanahmet"


# =====================================================================
# 7. Weather Accuracy & 14-Day Live Forecast Horizon
# =====================================================================
def test_weather_distant_date_horizon_disclosure():
    """Verify that a travel date > 14 days in the future reports 'Forecast unavailable' with 'Seasonal Climate Standard'."""
    w = get_weather("Istanbul", date_str="2027-03-15")
    sd = w.get("selected_date_weather") or {}

    assert sd.get("weather_status") == "Forecast unavailable"
    assert sd.get("weather_confidence") == "Seasonal Climate Standard"
    assert sd.get("is_confirmed_forecast") is False
    assert sd.get("forecast_unavailable") is True
    assert "Forecast unavailable" in sd.get("status_label", "")
    assert "Live atmospheric forecast unavailable" in sd.get("provenance_note", "")


# =====================================================================
# 8. Budget Transparency, Room Occupancy & Nationality-Aware Visa
# =====================================================================
def test_budget_coimbatore_to_istanbul_family_plan():
    """Verify canonical budget calculation for Coimbatore -> Istanbul (2 adults + 1 child, 7 days, ₹5,00,000)."""
    plan = BudgetAllocationService.calculate_plan(
        total_budget=500000,
        currency="INR",
        tier="mid_range",
        destination="Istanbul",
        origin_city="Coimbatore",
        days=7,
        adults=2,
        children=1,
        travel_style="family",
        transport_mode="flight",
        accommodation_preference="hotel"
    )

    assert plan["is_feasible"] is True
    # 1 Family Room occupancy for 2 adults + 1 child
    assert plan["num_rooms"] == 1, f"Expected 1 family room, got {plan['num_rooms']}"

    # Indian passport Turkey e-Visa estimation (~$60 USD / ₹5,010 per person = ₹15,030 for 3)
    fees_b = plan["fees_breakdown"]
    assert fees_b["visa_eta"] > 14000.0, f"Expected Turkey e-Visa estimation, got: {fees_b['visa_eta']}"
    assert "Turkey entry" in fees_b["notes"]

    # Arithmetic consistency: Total Estimated Trip Cost = Subtotal Expenses + Contingency
    categories = plan["categories"]
    subtotal = sum(c["estimated_cost"] for c in categories if c.get("key") != "contingency")
    contingency = next(c["estimated_cost"] for c in categories if c.get("key") == "contingency")
    total_est = plan["total_estimated_trip_cost"]

    assert round(subtotal + contingency, 2) == round(total_est, 2)
    assert plan["remaining_surplus_buffer"] > 0
    assert plan["remaining_surplus_buffer"] == round(500000 - total_est, 2)


# =====================================================================
# 9. Arrival and Departure Buffers
# =====================================================================
def test_arrival_and_departure_day_buffers():
    """Verify Day 1 starts >= 14:00 with check-in buffer, and Final Day concludes with 3.5-hour airport transfer buffer."""
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=5,
        budget=350000,
        interests="History, Street Food, Photography",
        travel_style="family",
        currency="INR",
        country="Turkey",
        start_date="2027-03-15",
        end_date="2027-03-19"
    )

    days = itinerary.get("days", [])
    day1 = days[0]
    day5 = days[4]

    # Day 1
    assert day1.get("is_provisional") is True
    assert "arrival" in day1.get("provisional_reason", "").lower()
    d1_acts = day1.get("activities", [])
    assert len(d1_acts) >= 1
    d1_first_time = d1_acts[0].get("start_time")
    # First activity must start at 14:00 or later
    hr = int(d1_first_time.split(":")[0])
    assert hr >= 14, f"Day 1 must start >= 14:00, got {d1_first_time}"

    # Day 5 (Final Day)
    assert day5.get("is_provisional") is True
    assert "3.5-hour" in day5.get("provisional_reason", "").lower()
    d5_acts = day5.get("activities", [])
    d5_last_end = d5_acts[-1].get("end_time")
    d5_last_hr = int(d5_last_end.split(":")[0])
    # Schedule must conclude early afternoon to leave 3.5-hour buffer for evening international departure
    assert d5_last_hr <= 16, f"Final day activities must conclude by 16:00, got {d5_last_end}"


# =====================================================================
# 10. Global Destination Scalability
# =====================================================================
def test_global_scalability_cairo_and_rome():
    """Verify that non-Istanbul destinations (Cairo, Rome) execute successfully with the same pipeline."""
    for dest, country, curr in [("Cairo", "Egypt", "EGP"), ("Rome", "Italy", "EUR")]:
        itin = generate_structured_itinerary(
            destination=dest,
            days=3,
            budget=2000,
            interests="Culture, History, Photography",
            travel_style="solo",
            currency=curr,
            country=country,
            start_date="2027-04-01",
            end_date="2027-04-03"
        )
        assert len(itin.get("days", [])) == 3
        d1_acts = itin["days"][0].get("activities", [])
        assert len(d1_acts) >= 2
        for a in d1_acts:
            prov = a.get("provenance", {})
            assert "public_accessibility" in prov
            assert prov["public_accessibility"] != "Publicly Inaccessible / Private Property"
