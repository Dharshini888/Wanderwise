"""
test_singapore_itinerary_and_global_planning_defects.py — Automated Regression Test Suite
Validates the global architecture upgrades addressing the Singapore test:
1. Discrete Unmerged POIs: Separation of combined POIs into standalone physical attractions (Chinatown Heritage Centre vs Buddha Tooth Relic Temple; Botanic Gardens vs Orchid Garden; Sentosa vs Siloso Beach).
2. Experience-Calibrated Durations: Duration scaling based on attraction scale (Gardens by the Bay 180m, Sentosa 180m, Botanic Gardens 120m, National Museum 105-120m, Jewel 90m, Siloso Beach 90m, viewpoints/temples 45m).
3. Dining Intelligence & Proximity Matching: Proximity-sorted authentic restaurants near attractions; clean 'Flexible meal break' fallback; no fake 'Free Entry' meals.
4. Public Transit & Rail Classification: Automatic assignment of 'Public Transit / MRT' in Singapore for journeys > 1.2 km; honest route verification labels.
5. Airport Gateway & Provisional Departure Buffer: Single canonical airport POI on departure day; explicit provisional 3-hour departure buffer.
6. Chronological Integrity: Strict non-overlapping schedule across all itinerary days.
7. Budget Accounting Consistency: Remaining Unallocated Balance = Budget - Estimated Total Trip Cost; single-counted emergency reserve.
"""

import os
import sys
import json
import pytest
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

from app.services.poi_service import (
    fetch_real_pois_for_destination,
    get_realistic_activity_duration,
    resolve_poi_coordinates
)
from app.services.route_optimizer import estimate_travel_transition, haversine_distance_km
from app.services.budget_allocation_service import BudgetAllocationService
from app.ai.providers.mock_provider import MockProvider
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator


# ==============================================================================
# 1. ATTRACTION SEPARATION AND IDENTITY TESTS
# ==============================================================================

class TestUnmergedAttractionIdentity:
    """Verifies that separate physical attractions are never combined into merged hybrid POIs."""

    def test_singapore_pois_are_unmerged_and_discrete(self):
        """Attractions in Singapore must be discrete POIs with distinct coordinates and metadata."""
        pois = fetch_real_pois_for_destination("Singapore")
        poi_names = [p["name"] for p in pois]

        # 1. Chinatown Heritage Centre and Buddha Tooth Relic Temple must be separate
        assert "Chinatown Heritage Centre" in poi_names
        assert "Buddha Tooth Relic Temple" in poi_names
        assert not any("chinatown heritage centre &" in n.lower() for n in poi_names)

        # 2. Singapore Botanic Gardens and National Orchid Garden must be separate
        assert "Singapore Botanic Gardens" in poi_names
        assert "National Orchid Garden" in poi_names
        assert not any("botanic gardens & national orchid" in n.lower() for n in poi_names)

        # 3. Sentosa Island and Siloso Beach must be separate
        assert any("sentosa" in n.lower() and "beach" not in n.lower() for n in poi_names)
        assert any("siloso beach" in n.lower() for n in poi_names)

        # 4. Marina Bay Sands SkyPark and Gardens by the Bay must be separate
        assert "Gardens by the Bay" in poi_names
        assert "Marina Bay Sands SkyPark" in poi_names

    def test_distinct_attractions_have_unique_coordinates(self):
        """Separate Singapore attractions must have distinct latitude and longitude coordinates."""
        pois = fetch_real_pois_for_destination("Singapore")
        coord_map = {}
        for p in pois:
            if p.get("latitude") and p.get("longitude"):
                key = (round(float(p["latitude"]), 4), round(float(p["longitude"]), 4))
                assert key not in coord_map, f"Duplicate coordinates detected between '{p['name']}' and '{coord_map[key]}'"
                coord_map[key] = p["name"]


# ==============================================================================
# 2. REALISTIC ACTIVITY DURATION SCALING TESTS
# ==============================================================================

class TestRealisticDurationScaling:
    """Verifies that durations scale according to physical venue scale and visitor experience requirements."""

    def test_large_scale_attractions_receive_adequate_duration(self):
        """Theme parks, resort islands, and mega-conservatories must receive at least 150-180 minutes."""
        assert get_realistic_activity_duration("Gardens by the Bay") >= 150
        assert get_realistic_activity_duration("Sentosa Island Resort & Boardwalk") >= 180
        assert get_realistic_activity_duration("Universal Studios Singapore") >= 180

    def test_sprawling_botanical_gardens_and_museums_scale(self):
        """Botanical gardens and flagship national museums must receive 105 to 120 minutes."""
        assert get_realistic_activity_duration("Singapore Botanic Gardens") >= 120
        assert get_realistic_activity_duration("National Museum of Singapore") >= 105

    def test_lifestyle_hubs_and_beaches(self):
        """Major lifestyle hubs like Jewel Changi and beaches must receive 90 minutes."""
        assert get_realistic_activity_duration("Jewel Changi Airport") >= 90
        assert get_realistic_activity_duration("Siloso Beach") >= 90

    def test_observation_wheels_and_viewpoints(self):
        """Observation wheels (Singapore Flyer) get 60m, viewpoints and temples get 45m."""
        assert get_realistic_activity_duration("Singapore Flyer") == 60
        assert get_realistic_activity_duration("Marina Bay Sands SkyPark") == 60
        assert get_realistic_activity_duration("Merlion Park") == 45
        assert get_realistic_activity_duration("Buddha Tooth Relic Temple") == 45
        assert get_realistic_activity_duration("Sri Veeramakaliamman Temple") == 45
        assert get_realistic_activity_duration("Sultan Mosque") == 45


# ==============================================================================
# 3. VERIFIED DINING INTELLIGENCE & FLEXIBLE MEAL BREAKS
# ==============================================================================

class TestDiningIntelligenceAndMealBreaks:
    """Verifies that dining venues are authentic, geographically paired, and never marked 'Free Entry'."""

    def test_verified_singapore_dining_in_cache(self):
        """Verified dining venues across Singapore districts must exist with dietary and cuisine tags."""
        pois = fetch_real_pois_for_destination("Singapore")
        dining_pois = [p for p in pois if p.get("category") == "Restaurant" or "dining" in str(p.get("dietary_tags", [])).lower()]
        dining_names = [p["name"] for p in dining_pois]

        assert len(dining_pois) >= 8
        assert "Lau Pa Sat Festival Market" in dining_names
        assert "Maxwell Food Centre" in dining_names
        assert "Satay by the Bay" in dining_names
        assert "Komala Vilas Pure Vegetarian Restaurant" in dining_names
        assert "Whole Earth Peranakan-Thai Vegetarian" in dining_names
        assert "Jumbo Seafood Riverside Point" in dining_names

    def test_dining_entries_never_have_free_entry_formatted_cost(self):
        """Meal activities must have positive meal costs and never be formatted as 'Free Entry'."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Selected Activity Interests: Food, adventure, culture/history, nature and shopping
        Travel Style: mid_range
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        for day in trip_data["itinerary_days"]:
            for act in day.get("activities", []):
                if act.get("activity_type") == "meal":
                    fmt = act.get("formatted_cost", "").lower()
                    assert "free" not in fmt, f"Meal activity '{act.get('title')}' displayed as '{fmt}'"
                    assert act.get("meal_cost", 0) > 0 or act.get("cost", {}).get("amount", 0) > 0

    def test_flexible_meal_break_has_honest_provenance(self):
        """When verified dining pool is exhausted, flexible break is labelled accurately with Estimated status."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        flexible_breaks = []
        for day in trip_data["itinerary_days"]:
            for act in day.get("activities", []):
                if act.get("is_flexible_meal_break"):
                    flexible_breaks.append(act)

        assert len(flexible_breaks) > 0, "Expected flexible meal breaks on later days"
        for fb in flexible_breaks:
            assert "flexible meal break" in fb["title"].lower()
            assert fb.get("provenance", {}).get("overall_status") in ["Estimated", "Flexible Meal Break"]


# ==============================================================================
# 4. TRANSPORT CLASSIFICATION AND METRO / MRT SELECTION
# ==============================================================================

class TestPublicTransitAndModeSelection:
    """Verifies that high-density transit cities like Singapore prioritize Public Transit / MRT."""

    def test_singapore_transit_mode_assignment(self):
        """Journeys in Singapore over 1.5 km must assign 'Public Transit / MRT'."""
        trans = estimate_travel_transition(1.2847, 103.8610, 1.2540, 103.8238, "Singapore")
        assert "MRT" in trans["travel_mode"] or "Public Transit" in trans["travel_mode"]

    def test_generated_itinerary_uses_mrt_in_singapore(self):
        """Generated Singapore activities must utilize 'Public Transit / MRT' as daytime mode."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        mrt_modes = []
        for day in trip_data["itinerary_days"]:
            for act in day.get("activities", []):
                if act.get("transport_mode") == "Public Transit / MRT":
                    mrt_modes.append(act)

        assert len(mrt_modes) >= 8, f"Expected at least 8 MRT journeys, found {len(mrt_modes)}"


# ==============================================================================
# 5. AIRPORT DEPARTURE BUFFER AND SINGLE POI CONSOLIDATION
# ==============================================================================

class TestAirportDepartureBufferAndConsolidation:
    """Verifies departure day airport transfer and provisional departure buffer."""

    def test_single_airport_poi_on_departure_day(self):
        """Transfer 3A and Buffer 3B must reference the exact same canonical airport POI name."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        dep_day = trip_data["itinerary_days"][-1]
        acts = dep_day["activities"]

        transfer_act = next(a for a in acts if a["id"].endswith("_03a"))
        buffer_act = next(a for a in acts if a["id"].endswith("_03b"))

        # Both reference Singapore Changi Airport (SIN)
        assert transfer_act["place"]["name"] == "Singapore Changi Airport (SIN)"
        assert buffer_act["place"]["name"] == "Singapore Changi Airport (SIN)"

        # Buffer is explicitly labelled provisional
        assert "provisional" in buffer_act["title"].lower() or "provisional" in buffer_act["description"].lower()
        assert buffer_act["duration_minutes"] == 180
        assert buffer_act.get("provenance", {}).get("overall_status") == "Estimated"

    def test_jewel_changi_scheduled_on_departure_day(self):
        """Jewel Changi Airport should be prioritized on departure day morning before departure."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        dep_day = trip_data["itinerary_days"][-1]
        morning_act = dep_day["activities"][0]
        assert "jewel changi" in morning_act["title"].lower()


# ==============================================================================
# 6. SCHEDULE INTEGRITY AND ZERO OVERLAPS
# ==============================================================================

class TestScheduleChronologicalIntegrity:
    """Verifies that activities never overlap and have positive chronological order."""

    def test_zero_schedule_overlaps_across_entire_trip(self):
        """Start time of every activity must be >= end time of the preceding activity."""
        provider = MockProvider()
        prompt = """
        Destination: Singapore
        Origin City: Coimbatore
        Total Duration: 7 Days
        Total Group Size: 2
        Adults: 2
        Budget: 400000 INR
        Target Currency Code: INR
        Start Date: 2027-04-15
        End Date: 2027-04-21
        """
        raw = provider.generate(prompt)
        trip_data = json.loads(raw)["trip"]

        def _to_mins(t_str):
            h, m = map(int, t_str.split(":"))
            return h * 60 + m

        for day in trip_data["itinerary_days"]:
            acts = day.get("activities", [])
            for i in range(len(acts) - 1):
                cur_end = _to_mins(acts[i]["end_time"])
                next_start = _to_mins(acts[i + 1]["start_time"])
                assert next_start >= cur_end, (
                    f"Day {day['day_number']} schedule overlap: "
                    f"'{acts[i]['title']}' ends at {acts[i]['end_time']} ({cur_end}m), "
                    f"but '{acts[i+1]['title']}' starts at {acts[i+1]['start_time']} ({next_start}m)"
                )


# ==============================================================================
# 7. BUDGET INTEGRITY AND ACCOUNTING CONSISTENCY
# ==============================================================================

class TestBudgetAccountingIntegrity:
    """Verifies mathematical consistency of trip budget allocations."""

    def test_budget_allocation_formula_and_emergency_reserve(self):
        """Remaining balance must equal Budget - Total Cost, with single-counted emergency reserve."""
        budget = 400000.0
        plan = BudgetAllocationService.calculate_plan(
            total_budget=budget,
            currency="INR",
            tier="mid_range",
            destination="Singapore",
            origin_city="Coimbatore",
            days=7,
            adults=2,
            children=0
        )

        assert plan["total_user_budget"] == budget
        cat_rec = plan["category_reconciliation"]
        est_total = cat_rec["estimated_total"]
        emergency_reserve = cat_rec["emergency_reserve"]
        unallocated = cat_rec["unallocated_balance"]

        # Emergency reserve is positive and protected
        assert emergency_reserve > 0
        assert cat_rec["is_emergency_reserve_protected"] is True

        # Arithmetic: unallocated = user_budget - estimated_total
        assert round(unallocated, 2) == round(budget - est_total, 2)

        # Ensure emergency reserve is NOT deducted a second time
        double_counted = round(budget - est_total - emergency_reserve, 2)
        assert unallocated != double_counted
