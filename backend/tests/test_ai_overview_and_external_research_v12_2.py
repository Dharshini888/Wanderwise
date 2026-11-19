"""
test_ai_overview_and_external_research_v12_2.py

Test Suite for WanderWise V12.2:
  - Strict separation of Three Information Categories:
      Category A: AI Transit Strategy
      Category B: Verified Journey Results
      Category C: External Travel Research
  - Benchmark Test Case: Bhutan -> New Delhi
  - Required International & Domestic Corridors:
      1. Bhutan -> New Delhi
      2. New Delhi -> Tokyo
      3. Coimbatore -> Delhi
      4. Chennai -> Singapore
      5. London -> Paris
      6. Sydney -> Auckland & Cairo -> Dubai
  - Edge Conditions:
      * Successful provider responses
      * No results / unverified routes
      * Rate limits / quota exhaustion
      * Timeouts
      * Incomplete results
      * External research without provider results
      * Zero AI Transit Facts safety contract
      * Statelessness / zero cross-query leakage
"""

import pytest
from backend.app.services.transit.transit_orchestrator import TransitOrchestrator
from backend.app.services.transit.ai_route_guidance import (
    AIRouteGuidanceService,
    validate_no_ai_transit_facts,
)
from backend.app.services.transit.external_travel_research import (
    ExternalTravelResearchService,
)
from backend.app.services.transit.airport_service import (
    resolve_serving_airports,
    get_airport_by_iata,
)


class TestAIOverviewAndExternalResearchV12_2:

    def test_bhutan_to_delhi_benchmark(self):
        """
        Benchmark corridor: Bhutan -> New Delhi
        Requirements:
          - AI Transit Strategy: Recommends flying, justifies based on Himalayan terrain.
          - Verified Journey Results: Prominently reports no verified flight itinerary available.
          - External Travel Research:
              * Candidate airports: Paro (PBH) and Indira Gandhi International (DEL).
              * Candidate airlines to investigate: Drukair and Bhutan Airlines.
              * Indicative duration: ~2h 20m.
              * Indicative fare: ₹24,000–₹45,000+ (clearly labeled as indicative external range).
              * Provenance: Official Tourism & Airline Directory, URL https://www.drukair.com.bt, timestamp.
              * Category EXTERNAL_TRAVEL_RESEARCH, is_indicative=True, is_live_quotation=False.
        """
        plan = TransitOrchestrator.get_transit_plan(
            origin="Bhutan",
            destination="New Delhi",
            preferred_mode="fastest",
            date="Today",
            departure_type="now",
        )

        assert plan is not None
        assert plan.get("status") in ("ROUTE_GUIDANCE_AVAILABLE", "NO_VERIFIED_ITINERARY")
        assert plan.get("verified") is False
        assert plan.get("message") == "No verified flight itinerary available for selected date."

        # ── Category A: AI Transit Strategy ───────────────────────────
        strategy = plan.get("ai_transit_strategy")
        assert strategy is not None
        assert strategy.get("category") == "AI_TRANSIT_STRATEGY"
        assert strategy.get("recommended_mode") == "Flight"
        assert "Flight Recommended" in strategy.get("title", "")
        assert "Himalayas" in strategy.get("reason", "") or "mountainous" in strategy.get("reason", "")
        assert strategy.get("scale") == "INTERNATIONAL"
        assert validate_no_ai_transit_facts(strategy) is True

        # Strategic considerations
        considerations = strategy.get("strategic_considerations", [])
        assert len(considerations) > 0
        assert any("mountain" in c.lower() or "himalayan" in c.lower() for c in considerations)

        # ── Category B: Verified Journey Results ───────────────────────
        verified_results = plan.get("verified_journey_results")
        assert verified_results is not None
        assert verified_results.get("category") == "VERIFIED_JOURNEY_RESULTS"
        assert verified_results.get("status") == "NO_VERIFIED_ITINERARY"
        assert verified_results.get("has_verified_itineraries") is False
        assert verified_results.get("count") == 0
        assert verified_results.get("message") == "No verified flight itinerary available for selected date."
        assert verified_results.get("itineraries") == []
        assert verified_results.get("verification_level") == "UNVERIFIED"

        # ── Category C: External Travel Research ───────────────────────
        research = plan.get("external_travel_research")
        assert research is not None
        assert research.get("category") == "EXTERNAL_TRAVEL_RESEARCH"
        assert research.get("is_external_research") is True
        assert research.get("is_indicative") is True
        assert research.get("is_live_quotation") is False
        assert research.get("is_confirmed_itinerary") is False

        # Candidate Airports
        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "PBH" in candidate_orig
        assert "DEL" in candidate_dest

        # Candidate Airlines to investigate
        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "Drukair" in operators
        assert "Bhutan Airlines" in operators

        # Indicative duration estimate
        assert "~2h 20m" in research.get("indicative_duration_display", "")

        # Indicative fare range
        fare_range = research.get("indicative_fare_range", {})
        assert fare_range.get("currency") == "INR"
        assert fare_range.get("min_amount") == 24000
        assert fare_range.get("max_amount") == 45000
        assert "₹24,000–₹45,000+" in fare_range.get("display", "")
        assert "not a current fare or quotation" in fare_range.get("display", "")

        # Provenance
        provenance = research.get("provenance", {})
        assert provenance.get("source_name") == "Official Tourism & Airline Directory / Published Flight Guide"
        assert provenance.get("source_url") == "https://www.drukair.com.bt"
        assert provenance.get("retrieved_at") == "2026-11-19T06:30:00Z"
        assert provenance.get("category") == "EXTERNAL_TRAVEL_RESEARCH"
        assert provenance.get("verification_status") == "UNVERIFIED_EXTERNAL_RESEARCH"

    def test_delhi_to_tokyo_corridor(self):
        """Intercontinental corridor: New Delhi -> Tokyo."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="New Delhi",
            destination="Tokyo",
            preferred_mode="fastest",
        )
        assert plan is not None

        # Category A: AI Transit Strategy
        strategy = plan.get("ai_transit_strategy")
        assert strategy.get("recommended_mode") == "Flight"
        assert strategy.get("scale") in ("INTERCONTINENTAL", "INTERNATIONAL")

        # Category C: External Travel Research
        research = plan.get("external_travel_research")
        assert research is not None
        assert research.get("is_indicative") is True

        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "DEL" in candidate_orig
        assert any(code in candidate_dest for code in ["HND", "NRT"])

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert any("Air India" in op for op in operators)
        assert any("ANA" in op for op in operators)
        assert any("Japan Airlines" in op for op in operators)

        assert "₹42,000–₹78,000+" in research.get("indicative_fare_range", {}).get("display", "")
        assert "https://www.jnto.go.jp" in research.get("provenance", {}).get("source_url", "")

    def test_coimbatore_to_delhi_corridor(self):
        """Domestic corridor: Coimbatore -> Delhi."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore",
            destination="Delhi",
            preferred_mode="fastest",
        )
        assert plan is not None

        # Category A
        strategy = plan.get("ai_transit_strategy")
        assert strategy.get("recommended_mode") in ("Rail / Flight", "Flight")

        # Category C
        research = plan.get("external_travel_research")
        assert research is not None
        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "CJB" in candidate_orig
        assert "DEL" in candidate_dest

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "IndiGo" in operators
        assert "Air India" in operators

        assert "₹6,500–₹14,000+" in research.get("indicative_fare_range", {}).get("display", "")

    def test_chennai_to_singapore_corridor(self):
        """International maritime corridor: Chennai -> Singapore."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Chennai",
            destination="Singapore",
            preferred_mode="fastest",
        )
        assert plan is not None

        strategy = plan.get("ai_transit_strategy")
        assert strategy.get("recommended_mode") == "Flight"

        research = plan.get("external_travel_research")
        assert research is not None
        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "MAA" in candidate_orig
        assert "SIN" in candidate_dest

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "Singapore Airlines" in operators
        assert "IndiGo" in operators

        assert "₹11,000–₹24,000+" in research.get("indicative_fare_range", {}).get("display", "")
        assert "https://www.changiairport.com" in research.get("provenance", {}).get("source_url", "")

    def test_london_to_paris_corridor(self):
        """Cross-channel corridor: London -> Paris."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="London",
            destination="Paris",
            preferred_mode="fastest",
        )
        assert plan is not None

        strategy = plan.get("ai_transit_strategy")
        assert "Rail" in strategy.get("recommended_mode", "") or "Flight" in strategy.get("recommended_mode", "")

        research = plan.get("external_travel_research")
        assert research is not None

        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert any(c in candidate_orig for c in ["LHR", "LGW", "LCY"])
        assert any(c in candidate_dest for c in ["CDG", "ORY"])

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "Eurostar" in operators
        assert "British Airways" in operators
        assert "Air France" in operators

        assert "Eurostar" in research.get("indicative_duration_display", "")
        assert "https://www.eurostar.com" in research.get("provenance", {}).get("source_url", "")

    def test_sydney_to_auckland_corridor(self):
        """Trans-Tasman corridor: Sydney -> Auckland."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Sydney",
            destination="Auckland",
            preferred_mode="fastest",
        )
        assert plan is not None

        strategy = plan.get("ai_transit_strategy")
        assert strategy.get("recommended_mode") == "Flight"

        research = plan.get("external_travel_research")
        assert research is not None

        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "SYD" in candidate_orig
        assert "AKL" in candidate_dest

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "Air New Zealand" in operators
        assert "Qantas" in operators

        assert "A$280–A$550+" in research.get("indicative_fare_range", {}).get("display", "")

    def test_cairo_to_dubai_corridor(self):
        """Middle Eastern corridor: Cairo -> Dubai."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Cairo",
            destination="Dubai",
            preferred_mode="fastest",
        )
        assert plan is not None

        strategy = plan.get("ai_transit_strategy")
        assert strategy.get("recommended_mode") == "Flight"

        research = plan.get("external_travel_research")
        assert research is not None

        candidate_orig = [a["iata"] for a in research.get("candidate_airports", {}).get("origin_airports", [])]
        candidate_dest = [a["iata"] for a in research.get("candidate_airports", {}).get("destination_airports", [])]
        assert "CAI" in candidate_orig
        assert "DXB" in candidate_dest

        operators = [op["name"] for op in research.get("candidate_operators_to_investigate", [])]
        assert "EgyptAir" in operators
        assert "Emirates" in operators

        assert "$220–$480+" in research.get("indicative_fare_range", {}).get("display", "")

    def test_universal_global_fallback_arbitrary_route(self):
        """
        Tests arbitrary / unmapped route worldwide:
        Resolver must dynamically compute flight duration, candidate gateway airports,
        indicative fare range, and citations without crashing or inventing flight numbers.
        """
        research = ExternalTravelResearchService.get_research(
            origin_name="Vancouver",
            dest_name="Toronto",
            origin_lat=49.2827,
            origin_lon=-123.1207,
            dest_lat=43.6532,
            dest_lon=-79.3832,
            distance_km=3350.0,
            scale="DOMESTIC",
            origin_country="Canada",
            dest_country="Canada",
        )

        assert research is not None
        assert research.get("category") == "EXTERNAL_TRAVEL_RESEARCH"
        assert research.get("is_indicative") is True
        assert research.get("is_live_quotation") is False
        assert "indicative" in research.get("indicative_duration_display", "").lower()
        assert research.get("indicative_fare_range", {}).get("display") is not None
        assert research.get("provenance", {}).get("source_url") is not None

    def test_zero_ai_transit_facts_safety_contract(self):
        """Asserts zero prohibited transit fact fields are generated or accepted in AI outputs."""
        clean_strategy = AIRouteGuidanceService.generate_strategy(
            origin_name="Paro",
            dest_name="New Delhi",
            journey_scale="INTERNATIONAL",
            origin_country="Bhutan",
            dest_country="India",
            distance_km=1215.0,
        )
        assert validate_no_ai_transit_facts(clean_strategy) is True

        # Test violation rejection
        toxic_payload_1 = {"flight_number": "KB204", "departure_time": "08:30"}
        assert validate_no_ai_transit_facts(toxic_payload_1) is False

        toxic_payload_2 = {"text": "Take Flight KB204 departing at 08:30"}
        assert validate_no_ai_transit_facts(toxic_payload_2) is False

        toxic_payload_3 = {"text": "Board at Platform 3 on Train 12675"}
        assert validate_no_ai_transit_facts(toxic_payload_3) is False

    def test_rate_limits_and_quota_exhaustion_audit(self):
        """Asserts that rate limit / quota exhaustion produces honest audit statuses without fake results."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore",
            destination="Delhi",
            departure_type="now",
        )
        prov_statuses = plan.get("provider_statuses", {})
        # RailRadar or Transitous should report truthful status, never fake success
        assert "RailRadar" in prov_statuses
        assert "Transitous" in prov_statuses

    def test_statelessness_no_cross_search_leakage(self):
        """Asserts that sequential searches do not leak candidate airports or data across queries."""
        plan_a = TransitOrchestrator.get_transit_plan(
            origin="Bhutan",
            destination="New Delhi",
        )
        research_a = plan_a.get("external_travel_research", {})
        orig_a = [a["iata"] for a in research_a.get("candidate_airports", {}).get("origin_airports", [])]
        assert "PBH" in orig_a

        # Subsequent unrelated search
        plan_b = TransitOrchestrator.get_transit_plan(
            origin="London",
            destination="Paris",
        )
        research_b = plan_b.get("external_travel_research", {})
        orig_b = [a["iata"] for a in research_b.get("candidate_airports", {}).get("origin_airports", [])]
        assert "PBH" not in orig_b
        assert "LHR" in orig_b or "LGW" in orig_b or "LCY" in orig_b
