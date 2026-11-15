import os
import pytest
from app.services.ai_service import generate_structured_itinerary
from app.services.transit.airport_service import get_primary_gateway_airport

def test_new_york_itinerary_generation(monkeypatch):
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "mock")
    trip_prefs = {
        "interests": ["Architecture", "Sightseeing"],
        "travel_style": "Couple",
        "adults": 2,
        "children": 0
    }
    plan = generate_structured_itinerary(
        destination="New York",
        days=4,
        budget=700000,
        currency="INR",
        origin_city="Coimbatore",
        interests="Architecture, Sightseeing",
        travel_style="Couple",
        group_size=2,
        start_date="2027-05-10",
        end_date="2027-05-14",
        trip_preferences=trip_prefs
    )

    assert "days" in plan
    assert len(plan["days"]) == 4

    day1 = plan["days"][0]
    acts1 = day1["activities"]

    # Check Day 1 Airport Arrival Transfer
    arrival_transfer = acts1[0]
    assert arrival_transfer["activity_type"] == "transit"
    assert "John F. Kennedy International Airport (JFK)" in arrival_transfer["place"]["name"]
    assert "Corridor" not in arrival_transfer["place"]["name"]
    assert arrival_transfer["place"]["latitude"] == pytest.approx(40.6413, abs=0.01)
    assert arrival_transfer["place"]["longitude"] == pytest.approx(-73.7781, abs=0.01)

    # Check Day 1 Orientation Attraction
    d1_attraction = acts1[2]  # after transfer and check-in
    assert d1_attraction["activity_type"] == "attraction"
    d1_name = d1_attraction["place"]["name"]
    obscure_names = [
        "Site of the Beach Pneumatic Subway",
        "\"The Sun",
        "Barthman's Sidewalk Clock",
        "Cortlandt Alley",
        "The Bartholomew Tree",
        "Anne Frank Tree",
        "Bloody Angle",
        "Wavertree"
    ]
    for obs in obscure_names:
        assert obs != d1_name

    # Check Day 4 Departure Day
    day4 = plan["days"][3]
    dep_transfer = next(a for a in day4["activities"] if a.get("activity_type") == "transit")
    assert "John F. Kennedy International Airport (JFK)" in dep_transfer["place"]["name"]
    assert "Corridor" not in dep_transfer["place"]["name"]

    dep_buffer = next(a for a in day4["activities"] if a.get("activity_type") == "departure_buffer")
    assert "John F. Kennedy International Airport (JFK)" in dep_buffer["place"]["name"]
    assert "Corridor" not in dep_buffer["place"]["name"]

def test_global_airports_resolution():
    destinations = [
        ("New York", "JFK", 40.6413, -73.7781),
        ("Paris", "CDG", 49.0097, 2.5479),
        ("Tokyo", "HND", 35.5494, 139.7798),
        ("Istanbul", "IST", 41.2753, 28.7519),
        ("Bali", "DPS", -8.7482, 115.1672),
        ("Reykjavik", "KEF", 63.9850, -22.6056),
        ("Singapore", "SIN", 1.3644, 103.9915),
        ("Cusco", "CUZ", -13.5357, -71.9388)
    ]

    for dest, expected_iata, expected_lat, expected_lon in destinations:
        ap = get_primary_gateway_airport(dest)
        assert ap["iata"] == expected_iata, f"Expected {expected_iata} for {dest}, got {ap['iata']}"
        assert ap["latitude"] == pytest.approx(expected_lat, abs=0.01)
        assert ap["longitude"] == pytest.approx(expected_lon, abs=0.01)
        assert "Corridor" not in ap["name"]
        assert ap["is_verified_commercial_airport"] is True

def test_multi_destination_itinerary_generation(monkeypatch):
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "mock")

    test_cases = [
        ("Paris", "CDG", "Charles de Gaulle Airport"),
        ("Tokyo", "HND", "Haneda Airport"),
        ("Bali", "DPS", "Ngurah Rai")
    ]

    for dest, expected_iata, airport_kw in test_cases:
        plan = generate_structured_itinerary(
            destination=dest,
            days=3,
            budget=500000,
            currency="INR",
            origin_city="Mumbai",
            interests="Culture, Food",
            travel_style="Balanced",
            group_size=2,
            start_date="2027-06-01",
            end_date="2027-06-04"
        )
        assert "days" in plan
        assert len(plan["days"]) == 3

        # Day 1 Arrival transfer
        d1 = plan["days"][0]
        arrival = d1["activities"][0]
        assert arrival["activity_type"] == "transit"
        assert airport_kw.lower() in arrival["place"]["name"].lower()
        assert "corridor" not in arrival["place"]["name"].lower()

        # Day 3 Departure transfer
        d3 = plan["days"][2]
        dep = next(a for a in d3["activities"] if a.get("activity_type") == "transit")
        assert airport_kw.lower() in dep["place"]["name"].lower()
        assert "corridor" not in dep["place"]["name"].lower()

        # Check budget summary reconciliation
        summary = plan.get("budget_summary") or plan.get("budget_breakdown")
        if summary and "categories" in summary:
            total_allocated = sum(c.get("allocated_amount", 0) for c in summary["categories"].values())
            assert total_allocated == pytest.approx(500000, abs=5.0)
