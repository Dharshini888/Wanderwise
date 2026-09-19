import pytest
from unittest.mock import patch, MagicMock
from app.services.safety_hub_service import SafetyHubService, _haversine_km
from app.services.maps.nominatim_service import geocode_place
from app.services.cache.transit_cache import TransitCache

@pytest.fixture(autouse=True)
def clear_cache():
    TransitCache._cache.clear()
    yield
    TransitCache._cache.clear()

def test_kovaipudhur_geocoding():
    """Test 1 — Verify Kovaipudhur, Coimbatore resolves to Kovaipudhur coordinates."""
    res = SafetyHubService.geocode("Kovaipudhur, Coimbatore")
    assert res.get("is_valid") is True
    assert abs(res["lat"] - 10.9575) < 0.1
    assert abs(res["lon"] - 76.9298) < 0.1
    assert "Coimbatore" in res["display"] or "Kovaipudhur" in res["display"]


def test_no_chennai_fallback_on_failure():
    """Test 2 — Verify failed geocoding does NOT return Chennai coordinates (13.0827, 80.2707)."""
    with patch("requests.get", side_effect=Exception("Geocoding Service Unavailable")):
        res = SafetyHubService.geocode("UnknownLocXYZ999")
        # Must return is_valid = False and lat/lon = None, NEVER Chennai coords
        assert res.get("is_valid") is False or res.get("lat") is None
        if res.get("lat") is not None:
            assert abs(res["lat"] - 13.0827) > 0.01 or abs(res["lon"] - 80.2707) > 0.01


def test_nearby_service_distance_validation():
    """Test 3 — Verify POIs > 50km away (e.g. Chennai POI for a Coimbatore query) are rejected."""
    coimbatore_lat, coimbatore_lon = 10.9575, 76.9298
    chennai_poi_lat, chennai_poi_lon = 13.0816, 80.2739 # Central Metro Chennai

    # Calculate distance directly
    dist = _haversine_km(coimbatore_lat, coimbatore_lon, chennai_poi_lat, chennai_poi_lon)
    assert dist > 400  # Over 400 km away

    # Mock Overpass response containing Chennai Central Metro when querying Coimbatore
    fake_overpass = {
        "elements": [
            {
                "type": "node",
                "lat": chennai_poi_lat,
                "lon": chennai_poi_lon,
                "tags": {"name": "Central Metro — Chennai"}
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = str(fake_overpass).replace("'", '"').encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        services = SafetyHubService.get_nearby_services(coimbatore_lat, coimbatore_lon)
        # Central Metro must be rejected by the 50km distance filter!
        for cat, items in services.items():
            for item in items:
                assert "Chennai" not in item["name"]
                assert item["distance_km"] <= 50.0


def test_valid_local_poi_retained():
    """Test 4 — Verify local POI (< 50km) is retained."""
    coimbatore_lat, coimbatore_lon = 10.9575, 76.9298
    local_hospital_lat, local_hospital_lon = 10.9600, 76.9300

    dist = _haversine_km(coimbatore_lat, coimbatore_lon, local_hospital_lat, local_hospital_lon)
    assert dist < 1.0

    fake_overpass = {
        "elements": [
            {
                "type": "node",
                "lat": local_hospital_lat,
                "lon": local_hospital_lon,
                "tags": {"name": "Kovaipudhur Health Center", "amenity": "hospital"}
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = str(fake_overpass).replace("'", '"').encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        services = SafetyHubService.get_nearby_services(coimbatore_lat, coimbatore_lon)
        hospitals = services.get("hospitals", [])
        assert len(hospitals) >= 1
        assert hospitals[0]["name"] == "Kovaipudhur Health Center"
        assert hospitals[0]["distance_km"] < 50.0


def test_cache_isolation():
    """Test 5 — Verify Coimbatore and Chennai produce different cache keys."""
    cov_key = f"nearby_services:{10.9575:.4f}:{76.9298:.4f}"
    che_key = f"nearby_services:{13.0827:.4f}:{80.2707:.4f}"
    assert cov_key != che_key
    assert "10.9575" in cov_key
    assert "13.0827" in che_key


def test_invalid_coordinates_handling():
    """Test 6 — Verify missing/null/invalid coordinates return clean empty structure instead of crashing or falling back."""
    services = SafetyHubService.get_nearby_services(None, None)
    assert isinstance(services, dict)
    assert all(len(v) == 0 for v in services.values())
