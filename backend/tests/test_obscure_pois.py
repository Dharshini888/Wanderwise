import pytest
from app.services.poi_service import is_valid_destination_poi, is_obscure_or_inappropriate_attraction, score_and_rank_pois

def test_obscure_pois_rejected():
    obscure_examples = [
        "Site of the Beach Pneumatic Subway",
        "\"The Sun",
        "Barthman's Sidewalk Clock",
        "Cortlandt Alley",
        "The Bartholomew Tree",
        "Anne Frank Tree",
        "Bloody Angle",
        "Wavertree"
    ]

    for item in obscure_examples:
        is_obs, reason = is_obscure_or_inappropriate_attraction(item)
        assert is_obs is True, f"Expected {item} to be marked obscure, but passed. Reason: {reason}"
        valid = is_valid_destination_poi({"name": item, "category": "Attraction"}, "New York")
        assert valid is False, f"Expected {item} to be invalid destination POI, but passed"

def test_iconic_landmarks_preserved():
    iconic_examples = [
        "Central Park",
        "Empire State Building",
        "The Metropolitan Museum of Art",
        "Brooklyn Bridge",
        "Statue of Liberty",
        "Top of the Rock",
        "The High Line",
        "Grand Central Terminal",
        "Eiffel Tower",
        "Louvre Museum",
        "Tokyo Metropolitan Government Building",
        "Hagia Sophia",
        "Blue Mosque"
    ]

    for item in iconic_examples:
        is_obs, reason = is_obscure_or_inappropriate_attraction(item)
        assert is_obs is False, f"Expected {item} to NOT be marked obscure, but was rejected. Reason: {reason}"
        valid = is_valid_destination_poi({"name": item, "category": "Museum"}, "New York")
        assert valid is True, f"Expected {item} to be valid destination POI"

def test_interest_ranking():
    pois = [
        {"name": "Local Small Park", "category": "Nature and viewpoint", "rating": 3.8},
        {"name": "Metropolitan Museum of Art", "category": "Art Museum", "rating": 4.8},
        {"name": "Empire State Building", "category": "Observation deck", "rating": 4.7},
        {"name": "Central Park", "category": "Nature and viewpoint", "rating": 4.8}
    ]

    # Test Architecture interest
    ranked_arch = score_and_rank_pois(pois, "New York", user_interests=["Architecture"])
    assert ranked_arch[0]["name"] == "Empire State Building"

    # Test Nature interest
    ranked_nat = score_and_rank_pois(pois, "New York", user_interests=["Nature"])
    assert ranked_nat[0]["name"] == "Central Park"
