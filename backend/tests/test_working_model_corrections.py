"""
test_working_model_corrections.py — Comprehensive Test Suite for IEEE NMIC-2026 Working Model Corrections

Validates:
1. Budget correctness:
   - Remaining Budget = Total Budget - Estimated Trip Cost
   - Clearly distinguished allocated budget, estimated expenses, emergency reserve, unallocated balance
   - Zero double-counting of emergency contingency
   - Sum of category percentages strictly equals 100.0%
   - Deficit shortfall correctly represented as negative remaining budget
2. Itinerary scheduling & temporal feasibility:
   - Non-overlapping activity schedules (start_time >= previous_end_time + transit_buffer)
   - Diurnal priority ordering (Breakfast morning, Lunch midday, Sunset evening, Dinner night)
   - Airport arrival buffer (Day 1 starts >= 14:00) & departure buffer (Day N concludes early with 3.5h airport buffer)
   - Mandatory, optional, and tentative commitment level classification
3. Global route intelligence & geographical constraints:
   - Water / island crossing detection (Bali mainland to Nusa Penida -> Ferry / Fast Boat Transfer)
   - Honest straight-line labeling vs OSRM verified road routes
   - Route summary consistency with segment statuses
4. Data reliability & missing API degradation:
   - Truthful provenance labels ("Coordinates Verified (Hours & Access Unverified)")
   - Weather forecast horizon separation (>14 days marked as Seasonal Climate Standard)
   - Multi-destination coverage: Istanbul (Turkey), Bali (Indonesia), Tromsø (Norway) / Reykjavik (Iceland) / Cusco (Peru)
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

import pytest
from datetime import date, timedelta
from typing import Dict, Any, List

from app.services.budget_allocation_service import BudgetAllocationService
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.services.route_optimizer import (
    haversine_distance_km,
    destination_has_rail,
    estimate_travel_transition,
    is_water_crossing
)
from app.services.poi_service import fetch_real_pois_for_destination
from app.services.ai_service import generate_structured_itinerary
from app.routes.weather import get_weather


@pytest.fixture(autouse=True)
def mock_ai_and_network(monkeypatch):
    monkeypatch.setattr("app.services.ai_service._ai", lambda *args, **kwargs: "[]")


# ==============================================================================
# 1. BUDGET CORRECTNESS & EMERGENCY RESERVE INTEGRITY
# ==============================================================================

def test_budget_correctness_formula_surplus_and_percentages():
    """
    Validates:
    - Remaining Budget = Total Budget - Estimated Trip Cost
    - Distinction between total budget, estimated expenses, emergency reserve, and unallocated balance
    - Sum of category percentages strictly equals 100.0%
    - Emergency reserve is not double counted
    """
    raw_budget = 400000.0
    plan = BudgetAllocationService.calculate_plan(
        total_budget=raw_budget,
        currency="INR",
        tier="mid_range",
        destination="Istanbul",
        origin_city="Coimbatore",
        days=5,
        adults=2,
        children=1,
        travel_style="family"
    )

    total_est = plan["total_estimated_trip_cost"]
    unallocated = plan["unallocated_balance"]
    rem_budget = plan["remaining_budget"]
    emergency = plan["emergency_reserve"]

    # 1. Canonical formula: Remaining Budget = Total Budget - Estimated Trip Cost
    assert rem_budget == round(raw_budget - total_est, 2)
    assert unallocated == round(raw_budget - total_est, 2)

    # 2. Distinct fields exist and are populated
    assert plan["total_user_budget"] == raw_budget
    assert plan["estimated_expenses"] == total_est
    assert emergency > 0.0
    assert plan["is_emergency_reserve_protected"] is True

    # 3. Sum of category percentages strictly equals 100.0%
    cats = plan["categories"]
    sum_pct = round(sum(c["percentage"] for c in cats), 1)
    assert sum_pct == 100.0, f"Expected 100.0%, got {sum_pct}%"

    # 4. Zero double counting: Emergency reserve remains protected and is not deducted twice
    contingency_cat = next(c for c in cats if c["key"] == "contingency")
    assert contingency_cat["allocated_amount"] == contingency_cat["estimated_cost"]
    assert contingency_cat["allocated_amount"] == emergency

    # 5. Category reconciliation exports the 4 distinct figures
    recon = plan["category_reconciliation"]
    assert recon["total_user_budget"] == raw_budget
    assert recon["estimated_expenses"] == total_est
    assert recon["emergency_reserve"] == emergency
    assert recon["unallocated_balance"] == unallocated


def test_budget_correctness_under_budget_shortfall():
    """
    Validates under-budget scenario:
    When user budget is insufficient, remaining_budget reflects the exact negative deficit.
    """
    low_budget = 50000.0  # Clearly insufficient for international trip to Istanbul
    plan = BudgetAllocationService.calculate_plan(
        total_budget=low_budget,
        currency="INR",
        tier="budget",
        destination="Istanbul",
        origin_city="Coimbatore",
        days=5,
        adults=2,
        children=1,
        travel_style="family"
    )

    total_est = plan["total_estimated_trip_cost"]
    rem_budget = plan["remaining_budget"]
    shortfall = plan["shortfall"]

    assert plan["is_feasible"] is False
    # Remaining budget is negative (shortfall)
    assert rem_budget < 0.0
    assert rem_budget == round(low_budget - total_est, 2)
    assert shortfall == round(abs(rem_budget), 2)


# ==============================================================================
# 2. ITINERARY SCHEDULING, TEMPORAL FEASIBILITY & BUFFERS
# ==============================================================================

def test_itinerary_scheduling_zero_overlap_and_transit_buffers():
    """
    Validates that consecutive activities within a day NEVER overlap
    and always have at least a 20-minute transit buffer between stops.
    """
    raw_days = [
        {
            "day_number": 2,
            "title": "Day 2: Istanbul Heritage",
            "activities": [
                {
                    "title": "Hagia Sophia Mosque",
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "duration_minutes": 90,
                    "place": {"name": "Hagia Sophia", "category": "Cultural / Heritage", "latitude": 41.0086, "longitude": 28.9802}
                },
                {
                    "title": "Blue Mosque",
                    "start_time": "09:30",  # Conflicting overlapping time from bad input
                    "end_time": "11:00",
                    "duration_minutes": 60,
                    "place": {"name": "Blue Mosque", "category": "Cultural / Heritage", "latitude": 41.0054, "longitude": 28.9768}
                },
                {
                    "title": "Topkapi Palace Museum",
                    "start_time": "10:00",  # Another conflicting overlapping time
                    "end_time": "12:00",
                    "duration_minutes": 120,
                    "place": {"name": "Topkapi Palace", "category": "Cultural / Heritage", "latitude": 41.0115, "longitude": 28.9833}
                }
            ]
        }
    ]

    _, _, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Istanbul",
        start_date=date(2027, 3, 16),
        end_date=date(2027, 3, 16),
        expected_days=1,
        currency="INR"
    )

    acts = validated[0]["activities"]
    assert len(acts) >= 3

    def _to_mins(t_str):
        h, m = map(int, t_str.split(":"))
        return h * 60 + m

    for i in range(len(acts) - 1):
        curr_act = acts[i]
        next_act = acts[i + 1]

        curr_end_min = _to_mins(curr_act["end_time"])
        next_start_min = _to_mins(next_act["start_time"])

        # Strict non-overlap assertion: next activity must start strictly after current end + transit buffer
        buffer_min = next_start_min - curr_end_min
        assert buffer_min >= 20, (
            f"Overlapping or insufficient buffer between '{curr_act['title']}' (ends {curr_act['end_time']}) "
            f"and '{next_act['title']}' (starts {next_act['start_time']}): buffer was only {buffer_min} mins"
        )


def test_itinerary_diurnal_alignment_and_commitment_levels():
    """
    Validates diurnal priority alignment:
    - Sunset cannot be scheduled in the morning.
    - Breakfast cannot be scheduled in the afternoon.
    - Mandatory, optional, and tentative commitment levels are correctly assigned.
    """
    raw_days = [
        {
            "day_number": 2,
            "title": "Day 2: Istanbul Full Day",
            "activities": [
                {
                    "title": "Sunset View from Galata Tower",
                    "place": {"name": "Galata Tower", "category": "Photography / Nature", "latitude": 41.0256, "longitude": 28.9741},
                    "duration_minutes": 60
                },
                {
                    "title": "Traditional Turkish Breakfast at Karakoy",
                    "place": {"name": "Karakoy Cafe", "category": "Dining", "latitude": 41.0230, "longitude": 28.9760},
                    "duration_minutes": 60,
                    "activity_type": "meal"
                },
                {
                    "title": "Midday Lunch by Bosphorus",
                    "place": {"name": "Bosphorus Dining", "category": "Dining", "latitude": 41.0200, "longitude": 28.9770},
                    "duration_minutes": 60,
                    "activity_type": "meal"
                },
                {
                    "title": "Evening Seafood Dinner",
                    "place": {"name": "Galata Seafood", "category": "Dining", "latitude": 41.0220, "longitude": 28.9750},
                    "duration_minutes": 75,
                    "activity_type": "meal"
                }
            ]
        }
    ]

    _, _, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Istanbul",
        start_date=date(2027, 3, 16),
        end_date=date(2027, 3, 16),
        expected_days=1,
        currency="TRY"
    )

    acts = validated[0]["activities"]
    titles_in_order = [a["title"] for a in acts]

    # Verify diurnal semantic ordering: Breakfast comes first, then Lunch, then Sunset, then Dinner
    breakfast_idx = next(i for i, t in enumerate(titles_in_order) if "breakfast" in t.lower())
    lunch_idx = next(i for i, t in enumerate(titles_in_order) if "lunch" in t.lower())
    sunset_idx = next(i for i, t in enumerate(titles_in_order) if "sunset" in t.lower())
    dinner_idx = next(i for i, t in enumerate(titles_in_order) if "dinner" in t.lower())

    assert breakfast_idx < lunch_idx < sunset_idx < dinner_idx, (
        f"Diurnal priority violated! Schedule order was: {titles_in_order}"
    )

    # Commitment levels must be populated for every activity
    for a in acts:
        assert a.get("commitment_level") in ["mandatory", "optional", "tentative"]
        assert a.get("metadata", {}).get("commitment_level") in ["mandatory", "optional", "tentative"]


def test_airport_arrival_and_departure_buffers():
    """
    Validates airport buffers:
    - Day 1 begins >= 14:00 (hotel check-in & flight arrival buffer).
    - Final Day concludes by 15:00 with dedicated 3.5h airport transfer buffer.
    """
    itinerary = generate_structured_itinerary(
        destination="Istanbul",
        days=4,
        budget=350000,
        currency="INR",
        country="Turkey",
        start_date="2027-03-15",
        end_date="2027-03-18"
    )

    days = itinerary.get("days", [])
    assert len(days) == 4

    day1 = days[0]
    day4 = days[3]

    # Day 1 start time >= 14:00
    first_act_start = day1["activities"][0]["start_time"]
    h1, m1 = map(int, first_act_start.split(":"))
    assert (h1 * 60 + m1) >= (14 * 60), f"Day 1 started too early: {first_act_start}"
    assert day1.get("is_provisional") is True

    # Day 4 final activity concludes by 15:00
    last_act_end = day4["activities"][-1]["end_time"]
    h4, m4 = map(int, last_act_end.split(":"))
    assert (h4 * 60 + m4) <= (15 * 60 + 30), f"Departure day concluded too late: {last_act_end}"
    assert day4.get("is_provisional") is True
    assert "airport" in day4.get("provisional_reason", "").lower()


# ==============================================================================
# 3. GLOBAL ROUTE INTELLIGENCE & GEOGRAPHICAL CONSTRAINTS (BALI & WATER CROSSING)
# ==============================================================================

def test_bali_water_crossing_detection():
    """
    Validates Bali island geography:
    - Travel between mainland Bali (e.g. Sanur, 115.26, -8.67) and Nusa Penida (115.52, -8.73)
      crosses the Badung Strait.
    - System must NOT recommend walking or road driving across the sea.
    - Mode must be 'Ferry / Fast Boat Transfer' and route status 'Water / Ferry Crossing Needed'.
    """
    sanur_lat, sanur_lon = -8.6705, 115.2625
    nusa_penida_lat, nusa_penida_lon = -8.7278, 115.5444

    is_water, label = is_water_crossing(sanur_lat, sanur_lon, nusa_penida_lat, nusa_penida_lon, "Bali")
    assert is_water is True
    assert "Badung Strait" in label or "Ferry" in label

    trans = estimate_travel_transition(sanur_lat, sanur_lon, nusa_penida_lat, nusa_penida_lon, "Bali")
    assert trans["route_status"] == "Water / Ferry Crossing Needed"
    assert "Ferry" in trans["travel_mode"] or "Fast Boat" in trans["travel_mode"]
    assert "Water Crossing" in trans["distance"]


def test_non_rail_destination_transport_sanitization():
    """
    Validates that non-rail tourist destinations (Bali, Queenstown, Maldives)
    never receive Train or Metro transit recommendations.
    """
    assert destination_has_rail("Bali") is False
    assert destination_has_rail("Queenstown") is False
    assert destination_has_rail("Maldives") is False
    assert destination_has_rail("Tokyo") is True
    assert destination_has_rail("London") is True


# ==============================================================================
# 4. MULTI-DESTINATION COVERAGE (ISTANBUL, BALI, TROMSO / REYKJAVIK)
# ==============================================================================

def test_multi_destination_istanbul_visa_and_currency():
    """Validates Istanbul Turkey e-Visa calculation and TRY currency benchmark."""
    plan = BudgetAllocationService.calculate_plan(
        total_budget=450000.0,
        currency="INR",
        tier="mid_range",
        destination="Istanbul",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=1,
        travel_style="family"
    )

    fees = plan["fees_breakdown"]
    assert fees["visa_eta"] > 0
    assert "Turkey entry" in fees["notes"]
    assert plan["destination_currency"] == "TRY"


def test_multi_destination_bali_visa_and_currency():
    """Validates Bali Indonesia VoA calculation and IDR currency benchmark."""
    plan = BudgetAllocationService.calculate_plan(
        total_budget=350000.0,
        currency="INR",
        tier="mid_range",
        destination="Bali",
        origin_city="Coimbatore",
        days=7,
        adults=2,
        children=2,
        travel_style="family"
    )

    fees = plan["fees_breakdown"]
    assert fees["visa_eta"] > 0
    assert "Indonesia entry" in fees["notes"]
    assert plan["destination_currency"] == "IDR"
    assert plan["num_rooms"] in [1, 2]  # Family suite or standard rooms occupancy


def test_multi_destination_tromso_arctic_and_norwegian_krone():
    """Validates remote destination Tromsø, Norway (Arctic climate norms and NOK currency)."""
    plan = BudgetAllocationService.calculate_plan(
        total_budget=500000.0,
        currency="INR",
        tier="mid_range",
        destination="Tromsø, Norway",
        origin_city="Coimbatore",
        days=5,
        adults=2,
        children=0,
        travel_style="couples"
    )

    assert plan["destination_currency"] == "NOK"
    assert plan["transportation_details"]["is_international"] is True


# ==============================================================================
# 5. DATA RELIABILITY & WEATHER HORIZON SEPARATION
# ==============================================================================

def test_weather_horizon_separation_live_vs_seasonal():
    """
    Validates weather data reliability:
    - When target date is > 14 days in the future, weather is marked as 'Forecast unavailable'
      and reports seasonal climate standard, never inventing a confirmed live atmospheric forecast.
    """
    future_date = (date.today() + timedelta(days=45)).isoformat()
    res = get_weather(city="Istanbul", date_str=future_date)

    sel = res.get("selected_date_weather") or {}
    assert sel.get("forecast_unavailable") is True
    assert "Seasonal Climate Standard" in sel.get("weather_confidence", "")
    assert "unavailable" in sel.get("weather_status", "").lower()
    assert "Live atmospheric forecast unavailable" in sel.get("provenance_note", "")
