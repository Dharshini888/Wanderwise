"""
test_global_itinerary_intelligence_and_financial_accuracy.py
Automated Multi-Destination Regression Suite for WanderWise Global Quality Requirements:
A. Intelligent Attraction Selection (No cross-day duplicates, compound landmark resolution)
B. Venue Verification (5 independent verification dimensions, GPS coords decoupled from access)
C. Realistic Scheduling Engine (Durations reflect venue scale, queues, diurnal sequencing)
D. Complete Door-to-Door Travel Planning (8 explicit travel stages, no transport mixed into descriptions)
E. Consistent Route & Map Calculations (Authentic Haversine routing, daily reconciliation)
F. Financial Transparency (3 distinct totals, per-person/group breakdowns, contingency protection, uncertainty ranges)
G. Daily Travel Experience Completeness (Sightseeing, meals, transit, rest)
H. Final-Day & Departure Validation (Dedicated departure transfer, 3.5h airport buffer, checkout)
"""

import pytest
from datetime import date
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.poi_service import (
    identify_parent_landmark,
    is_compound_sub_section_of,
    assess_venue_verification,
    get_realistic_activity_duration,
    fetch_real_pois_for_destination,
    COMPOUND_LANDMARK_REGISTRY
)
from app.services.transit.route_engine import calculate_distance, calculate_route
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.services.pricing.canonical_pricing_registry import normalize_place_entity_key


# ==============================================================================
# SECTION A: Intelligent Attraction Selection & Compound Landmark Intelligence
# ==============================================================================

class TestIntelligentAttractionSelection:
    def test_compound_landmark_parent_identification(self):
        """Validates that internal sections of global landmark complexes correctly identify their parent."""
        assert identify_parent_landmark("Cloud Forest Conservatory") == "gardens by the bay"
        assert identify_parent_landmark("Flower Dome") == "gardens by the bay"
        assert identify_parent_landmark("Supertree Grove") == "gardens by the bay"
        assert identify_parent_landmark("Topkapi Palace Harem") == "topkapi palace"
        assert identify_parent_landmark("Louvre Pyramid") == "louvre"
        assert identify_parent_landmark("Colosseum Underground & Arena Floor") == "colosseum"
        assert identify_parent_landmark("Sistine Chapel") == "vatican"
        assert identify_parent_landmark("Hall of Mirrors") == "versailles"
        assert identify_parent_landmark("St. Vitus Cathedral") == "prague castle"
        assert identify_parent_landmark("Nasrid Palaces") == "alhambra"
        assert identify_parent_landmark("Dubai Aquarium & Underwater Zoo") == "dubai mall"
        assert identify_parent_landmark("At The Top Sky Observation Deck") == "burj khalifa"
        assert identify_parent_landmark("Universal Studios Singapore") == "sentosa"

    def test_compound_sub_section_detection_against_scheduled_landmarks(self):
        """Prevents scheduling a landmark sub-section when its parent complex is already scheduled."""
        scheduled = ["Gardens by the Bay", "Marina Bay Sands", "National Museum of Singapore"]
        
        # Proposed child section should be detected as compound subsection
        is_sub, parent, matched = is_compound_sub_section_of("Flower Dome Conservatory", scheduled)
        assert is_sub is True
        assert parent.lower() == "gardens by the bay"
        assert matched == "Gardens by the Bay"

        # Independent attraction should NOT be flagged
        is_sub, _, _ = is_compound_sub_section_of("Singapore Flyer", scheduled)
        assert is_sub is False

    def test_obscure_and_wall_section_filtering(self):
        """Ensures rampart fragments, minor wall sections, and generic photo spots are filtered out."""
        from app.services.poi_service import is_obscure_or_inappropriate_attraction
        
        is_obs, reason = is_obscure_or_inappropriate_attraction("Old City Wall Remnant Fragment", "historical")
        assert is_obs is True

        is_obs, reason = is_obscure_or_inappropriate_attraction("Instagram Photo Spot Corner", "sightseeing")
        assert is_obs is True

        # Major landmark is not obscure
        is_obs, _ = is_obscure_or_inappropriate_attraction("Senso-ji Temple", "temple")
        assert is_obs is False


# ==============================================================================
# SECTION B: Venue Verification (5 Independent Dimensions)
# ==============================================================================

class TestVenueVerificationDecoupling:
    def test_gps_coordinates_alone_never_verify_visitor_access(self):
        """
        CRITICAL TEST (Requirement B):
        Geographic coordinates must NEVER be treated as proof of public access or venue identity.
        """
        # A place with GPS coordinates but unknown identity or private nature
        unverified_place = {
            "name": "Private Residential Estate 44B",
            "category": "residential",
            "latitude": 35.6895,
            "longitude": 139.6917
        }
        res = assess_venue_verification(unverified_place, destination="Tokyo")
        
        assert res["geographic_coordinates_verified"] is True
        assert res["place_identity_verified"] is False
        assert res["visitor_access_verified"] is False
        assert "Unverified" in res["access_status"] or "Inaccessible" in res["access_status"]

    def test_five_independent_verification_dimensions_present(self):
        """Validates that all 5 required verification dimensions are returned with transparent disclosures."""
        verified_place = {
            "name": "Senso-ji Temple",
            "category": "Temple",
            "latitude": 35.7148,
            "longitude": 139.7967,
            "opening_time": "06:00",
            "ticket_price": 0.0
        }
        res = assess_venue_verification(verified_place, destination="Tokyo")
        
        assert "place_identity_verified" in res
        assert "geographic_coordinates_verified" in res
        assert "visitor_access_verified" in res
        assert "opening_hours_verified" in res
        assert "ticket_pricing_verified" in res
        assert "verification_disclosure" in res
        
        assert res["place_identity_verified"] is True
        assert res["geographic_coordinates_verified"] is True
        assert res["visitor_access_verified"] is True
        assert res["opening_hours_verified"] is True
        assert res["ticket_pricing_verified"] is True


# ==============================================================================
# SECTION C: Realistic Scheduling Engine
# ==============================================================================

class TestRealisticSchedulingEngine:
    def test_venue_scale_realistic_durations(self):
        """Validates that visit durations reflect venue type and visitor scale (not generic 90m)."""
        # Sprawling attractions require substantial time (>= 120-180 min)
        assert get_realistic_activity_duration("Louvre Museum", "museum") >= 120
        assert get_realistic_activity_duration("Universal Studios Singapore", "theme park") >= 180
        assert get_realistic_activity_duration("Gardens by the Bay", "park") >= 150
        assert get_realistic_activity_duration("Amber Fort", "palace") >= 90
        assert get_realistic_activity_duration("Tokyo National Museum", "museum") >= 90
        
        # Viewpoints and photo stops are appropriately shorter (30-60 min)
        assert get_realistic_activity_duration("Shibuya Sky", "viewpoint") <= 60
        assert get_realistic_activity_duration("Sun Voyager Waterfront Sculpture", "monument") <= 45
        assert get_realistic_activity_duration("Hawa Mahal", "monument") <= 45


# ==============================================================================
# SECTION D & H: Complete Door-to-Door Planning & Final-Day Departure Validation
# ==============================================================================

class TestDoorToDoorAndFinalDayValidation:
    def test_eight_stage_door_to_door_travel_stages(self):
        """Validates that BudgetAllocationService produces all 8 explicit travel stages."""
        plan = BudgetAllocationService.calculate_plan(
            total_budget=300000,
            currency="INR",
            tier="mid_range",
            destination="Tokyo",
            origin_city="Delhi",
            days=7,
            adults=2,
            children=1
        )
        stages = plan.get("door_to_door_stages", [])
        assert len(stages) == 8, f"Expected exactly 8 travel stages, got {len(stages)}"
        
        stage_names = [s["stage_name"] for s in stages]
        assert "Origin to Departure Terminal" in stage_names[0]
        assert "Outbound Corridor Journey" in stage_names[1]
        assert "Arrival Terminal to Accommodation" in stage_names[2]
        assert "Daily Local Destination Transportation" in stage_names[3]
        assert "Intercity or Regional Day-Trip Transit" in stage_names[4]
        assert "Accommodation to Departure Airport/Station" in stage_names[5]
        assert "Return Corridor Journey" in stage_names[6]
        assert "Arrival Terminal to Home" in stage_names[7]

        # Verify corridors are marked as estimates and not confirmed bookings
        assert stages[1]["booking_status"] == "Illustrative Estimate (Not confirmed reservation)"
        assert stages[6]["booking_status"] == "Illustrative Estimate (Not confirmed reservation)"

    def test_final_day_departure_buffer_and_no_mixed_transport_text(self):
        """
        Validates:
        1. Final day includes dedicated departure logistics activity with 3.5h buffer.
        2. Airport transfer instructions are NEVER mixed into tourist attraction descriptions.
        """
        raw_days = [
            {
                "day_number": 1,
                "title": "Day 1: Arrival & Historic Asakusa",
                "activities": [
                    {
                        "time_slot": "afternoon",
                        "start_time": "14:00",
                        "end_time": "16:00",
                        "title": "Senso-ji Temple",
                        "description": "Historic temple in Asakusa.",
                        "place": {"name": "Senso-ji", "category": "Temple", "latitude": 35.7148, "longitude": 139.7967}
                    }
                ]
            },
            {
                "day_number": 2,
                "title": "Day 2: Final Sightseeing & Departure",
                "activities": [
                    {
                        "time_slot": "morning",
                        "start_time": "09:30",
                        "end_time": "11:30",
                        "title": "Meiji Jingu Shrine",
                        "description": "Explore forested Meiji Jingu shrine grounds.",
                        "place": {"name": "Meiji Jingu", "category": "Shrine", "latitude": 35.6764, "longitude": 139.6993}
                    },
                    {
                        "time_slot": "afternoon",
                        "start_time": "12:00",
                        "end_time": "13:30",
                        "title": "Farewell Japanese Lunch",
                        "description": "Traditional lunch near Shibuya.",
                        "place": {"name": "Shibuya Dining", "category": "Dining", "latitude": 35.6580, "longitude": 139.7016}
                    }
                ]
            }
        ]

        is_valid, warnings, validated_days = FinalItineraryValidator.validate_itinerary_payload(
            days_data=raw_days,
            destination="Tokyo",
            start_date=date(2027, 4, 10),
            end_date=date(2027, 4, 11),
            expected_days=2,
            currency="INR",
            interests="culture, temples, food",
            transport_mode="Public Metro & Bus",
            accommodation_preference="hotel",
            travelers_count=2,
            adults_count=2,
            children_count=0
        )

        day2 = validated_days[1]
        acts = day2["activities"]
        
        # Dedicated departure transfer activity must be scheduled at the end of the final day
        last_act = acts[-1]
        assert "Departure" in last_act["title"] or "Airport Transfer" in last_act["title"]
        assert last_act["activity_type"] == "transit"
        assert last_act["duration_minutes"] >= 180  # 3.0 to 3.5 hours
        assert last_act["commitment_level"] == "mandatory"

        # Verify NO tourist attraction descriptions contain injected airport buffer strings
        for day in validated_days:
            for act in day["activities"]:
                if act["activity_type"] != "transit":
                    desc = act.get("description", "")
                    assert "dedicated 3.5-hour international airport transfer" not in desc.lower(), (
                        f"Found injected airport transfer text in tourist attraction '{act['title']}': {desc}"
                    )


# ==============================================================================
# SECTION E: Consistent Route & Map Calculations
# ==============================================================================

class TestRouteAndMapCalculations:
    def test_authentic_haversine_distance_calculation_without_md5(self):
        """Verifies that route_engine calculate_distance returns authentic Haversine distance without md5 mod."""
        # Delhi to Tokyo is approximately 5,800 km
        dist_tokyo = calculate_distance("Delhi", "Tokyo")
        assert 5000 <= dist_tokyo <= 6500, f"Expected ~5800 km for Delhi-Tokyo, got {dist_tokyo}"

        # Coimbatore to Singapore is approximately 3,200 km
        dist_sg = calculate_distance("Coimbatore", "Singapore")
        assert 2800 <= dist_sg <= 3600, f"Expected ~3200 km for Coimbatore-Singapore, got {dist_sg}"

        # Mumbai to London is approximately 7,200 km
        dist_lon = calculate_distance("Mumbai", "London")
        assert 6500 <= dist_lon <= 8000, f"Expected ~7200 km for Mumbai-London, got {dist_lon}"

    def test_calculate_route_labels_distance_provenance(self):
        """Verifies that calculate_route returns distance provenance and no pseudo-random values."""
        route = calculate_route("Delhi", "Tokyo", date="2027-05-01", budget=200000, preferred_mode="Flight")
        assert route["distance_km"] > 5000
        assert route["distance_provenance"] == "Haversine Distance (Gazetteer Coordinates)"
        assert route["distance_status"] == "Calculated"


# ==============================================================================
# SECTION F: Financial Transparency & Mathematical Consistency
# ==============================================================================

class TestFinancialTransparency:
    @pytest.mark.parametrize("dest,origin,curr,budget,days,tier", [
        ("Tokyo", "Delhi", "INR", 350000, 7, "mid_range"),
        ("Singapore", "Coimbatore", "SGD", 5000, 5, "mid_range"),
        ("Paris", "Mumbai", "EUR", 4500, 4, "luxury"),
        ("Jaipur", "Delhi", "INR", 60000, 3, "budget"),
        ("Reykjavik", "Delhi", "USD", 6000, 4, "mid_range"),
        ("London", "Mumbai", "GBP", 3800, 5, "mid_range"),
    ])
    def test_financial_transparency_and_reconciliation_multi_destination(self, dest, origin, curr, budget, days, tier):
        """Validates all financial transparency requirements across 6 global test destinations."""
        plan = BudgetAllocationService.calculate_plan(
            total_budget=budget,
            currency=curr,
            tier=tier,
            destination=dest,
            origin_city=origin,
            days=days,
            adults=2,
            children=1
        )

        # 1. Present all three financial totals clearly and distinctly
        allocated_budget = plan["allocated_budget"]
        estimated_cost = plan["total_estimated_trip_cost"]
        remaining_budget = plan["remaining_budget"]
        
        assert allocated_budget == budget
        assert estimated_cost > 0
        assert remaining_budget == round(allocated_budget - estimated_cost, 2)

        # 2. Display both group totals and per-person amounts for every category
        categories = plan["categories"]
        assert len(categories) == 8
        travellers = plan["total_travelers"]
        
        for cat in categories:
            assert "group_allocated" in cat
            assert "group_estimated" in cat
            assert "per_person_allocated" in cat
            assert "per_person_estimated" in cat
            assert cat["per_person_allocated"] == round(cat["group_allocated"] / travellers, 2)
            assert cat["per_person_estimated"] == round(cat["group_estimated"] / travellers, 2)

        # 3. Category allocations strictly reconcile to total user budget
        sum_allocated = round(sum(c["allocated_amount"] for c in categories), 2)
        assert abs(sum_allocated - allocated_budget) <= 0.05, f"Allocated sum ({sum_allocated}) != budget ({allocated_budget})"

        # 4. Category estimates strictly sum to total estimated trip cost
        sum_estimated = round(sum(c["estimated_cost"] for c in categories), 2)
        assert abs(sum_estimated - estimated_cost) <= 0.05, f"Estimated sum ({sum_estimated}) != total est ({estimated_cost})"

        # 5. Prevent double-counting the emergency reserve
        # Contingency is already inside estimated_cost and is not deducted twice
        contingency_cat = next(c for c in categories if c["key"] == "contingency")
        assert contingency_cat["estimated_cost"] > 0
        assert plan["emergency_reserve"] == contingency_cat["estimated_cost"]

        # 6. Itemized fees breakdown (visa/ETA, insurance, baggage)
        fees = plan["fees_breakdown"]
        assert "visa_eta" in fees
        assert "travel_insurance" in fees
        assert "checked_baggage" in fees
        assert fees["total"] == next(c["estimated_cost"] for c in categories if c["key"] == "other_fees")

        # 7. Uncertainty ranges clearly explained [-6%, +7%]
        unc = plan["uncertainty_range"]
        assert unc["percentage_down"] == -6.0
        assert unc["percentage_up"] == 7.0
        assert "explanation" in unc
        assert unc["min_cost"] == round(estimated_cost * 0.94, 2)
        assert unc["max_cost"] == round(estimated_cost * 1.07, 2)

        # 8. Corridor flight estimates marked as benchmark estimates (not live confirmed bookings)
        trans = plan["transportation_details"]
        assert trans["is_market_benchmark"] is True
        assert trans["is_live_quote"] is False


# ==============================================================================
# SECTION G: Multi-Destination Complete Itinerary Validation (Tokyo, Singapore, Paris, Jaipur, Reykjavik, London)
# ==============================================================================

class TestMultiDestinationCompletenessAndQuality:
    @pytest.mark.parametrize("destination,days_count", [
        ("Tokyo", 5),
        ("Singapore", 5),
        ("Paris", 4),
        ("Jaipur", 3),
        ("Reykjavik", 4),
        ("London", 5),
    ])
    def test_complete_destination_itinerary_generation_and_validation(self, destination, days_count):
        """
        Validates itinerary generation across 6 global destinations:
        - Discrete authentic POIs scheduled without cross-day duplicates
        - Reconciled daily distance and transit minutes
        - Mandatory departure logistics on the final travel day
        - 5-dimension venue verification attached to all activities
        """
        dest_pois = fetch_real_pois_for_destination(destination)
        assert len(dest_pois) >= 10, f"Expected at least 10 POIs for {destination}, found {len(dest_pois)}"

        raw_days = []
        p_idx = 0
        for d in range(1, days_count + 1):
            acts = []
            for slot in ["morning", "afternoon", "evening"]:
                poi = dest_pois[p_idx % len(dest_pois)]
                p_idx += 1
                acts.append({
                    "time_slot": slot,
                    "start_time": "09:00" if slot == "morning" else ("13:30" if slot == "afternoon" else "18:00"),
                    "end_time": "11:30" if slot == "morning" else ("16:00" if slot == "afternoon" else "20:00"),
                    "title": f"Visit {poi['name']}",
                    "description": poi.get("description", ""),
                    "place": poi,
                    "ticket_price": poi.get("ticket_price", 0.0),
                    "is_dining": poi.get("is_dining", False)
                })
            raw_days.append({
                "day_number": d,
                "title": f"Day {d}: Experience {destination}",
                "activities": acts
            })

        is_valid, warnings, validated_days = FinalItineraryValidator.validate_itinerary_payload(
            days_data=raw_days,
            destination=destination,
            start_date=date(2027, 5, 1),
            end_date=date(2027, 5, days_count),
            expected_days=days_count,
            currency="INR",
            interests="culture, sightseeing, food, history",
            transport_mode="Public Transit / Metro",
            accommodation_preference="hotel",
            travelers_count=2,
            adults_count=2,
            children_count=0
        )

        assert len(validated_days) == days_count
        
        # Verify cross-day uniqueness and 5-point verification dimensions
        seen_keys = set()
        for day in validated_days:
            assert "daily_distance_km" in day
            assert "daily_transit_minutes" in day
            assert day["daily_distance_km"] >= 0.0

            for act in day["activities"]:
                p_dict = act.get("place") or {}
                p_name = p_dict.get("name") or act.get("title")
                key = normalize_place_entity_key(p_name)
                
                # Exclude transit/departure activities from attraction uniqueness check
                if act.get("activity_type") not in ["transit", "departure_buffer"]:
                    assert key not in seen_keys, f"Found duplicate attraction '{p_name}' in {destination} itinerary"
                    seen_keys.add(key)

                # Check 5 independent verification dimensions
                prov = act.get("provenance", {})
                assert "place_identity_verified" in prov
                assert "geographic_coordinates_verified" in prov
                assert "visitor_access_verified" in prov
                assert "opening_hours_verified" in prov
                assert "ticket_pricing_verified" in prov

        # Verify final day includes departure buffer
        final_day = validated_days[-1]
        final_acts = final_day["activities"]
        last_act = final_acts[-1]
        assert "Departure" in last_act["title"] or "Airport Transfer" in last_act["title"]
        assert last_act["activity_type"] == "transit"
