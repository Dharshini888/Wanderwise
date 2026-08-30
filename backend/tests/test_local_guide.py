import os
import sys
import pytest

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from app.main import app
from app.services.local_guide_service import normalize_place_data, LocalGuideService


def get_async_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
def anyio_backend():
    return 'asyncio'


# ── TEST SUITE ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_categories():
    """Test category definitions list endpoint"""
    async with get_async_client() as client:
        res = await client.get("/api/guide/categories")
        assert res.status_code == 200
        data = res.json()
        assert "categories" in data
        cat_ids = [c["id"] for c in data["categories"]]
        assert "ALL" in cat_ids
        assert "ATTRACTIONS" in cat_ids
        assert "RESTAURANTS" in cat_ids
        assert "HOSPITALS" in cat_ids


@pytest.mark.anyio
async def test_destination_search():
    """Test destination search endpoint returns places & cultural guide"""
    async with get_async_client() as client:
        res = await client.get("/api/guide/search?destination=Coimbatore")
        assert res.status_code == 200
        data = res.json()
        assert data["destination"] == "Coimbatore"
        assert "latitude" in data
        assert "longitude" in data
        assert "places" in data
        assert "cultural_guide" in data


@pytest.mark.anyio
async def test_nearby_search_and_category_filter():
    """Test nearby POI query with category filter"""
    async with get_async_client() as client:
        res = await client.get("/api/guide/nearby?lat=13.0827&lon=80.2707&category=RESTAURANTS&radius=3000")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == "RESTAURANTS"
        assert "places" in data
        if len(data["places"]) > 0:
            p = data["places"][0]
            assert "id" in p
            assert "name" in p
            assert "verification_status" in p
            assert p["verification_status"] == "Provider Verified"


@pytest.mark.anyio
async def test_place_normalization_truth_first():
    """Test normalization preserves null for missing values and preserves node/way/relation element type in ID"""
    raw_node = {
        "type": "way",
        "id": 987654,
        "lat": 11.0168,
        "lon": 76.9558,
        "tags": {
            "name": "Sample Historic Fort",
            "historic": "fort",
        }
    }
    normalized = normalize_place_data(raw_node, 11.0, 76.9)
    assert normalized["id"] == "way/987654"
    assert normalized["name"] == "Sample Historic Fort"
    assert normalized["category"] == "ATTRACTIONS"
    assert normalized["rating"] is None
    assert normalized["price_level"] is None
    assert normalized["phone"] is None
    assert normalized["verification_status"] == "Provider Verified"


@pytest.mark.anyio
async def test_route_calculation():
    """Test OSRM route calculation returns 'Route Calculated' status"""
    async with get_async_client() as client:
        res = await client.get(
            "/api/guide/route?origin_lat=11.0168&origin_lon=76.9558&dest_lat=11.0264&dest_lon=76.9577&mode=walking"
        )
        assert res.status_code == 200
        data = res.json()
        assert "distance_km" in data
        assert "duration_minutes" in data
        assert data["verification_status"] == "Route Calculated"


@pytest.mark.anyio
async def test_place_details_by_id():
    """Test fetching place details by node/way ID"""
    async with get_async_client() as client:
        res = await client.get("/api/guide/place/node/123456?lat=13.0827&lon=80.2707")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "node/123456"
        assert "name" in data


@pytest.mark.anyio
async def test_empty_search_handling():
    """Test empty search parameters validation"""
    async with get_async_client() as client:
        res = await client.get("/api/guide/search?destination=")
        assert res.status_code == 422


@pytest.mark.anyio
async def test_destination_independence_regression():
    """Regression test: Ensure searching Tokyo or Seoul returns destination POIs and NEVER Coimbatore POIs."""
    from app.services.local_guide_service import LocalGuideService
    
    # 1. Tokyo Search
    tokyo_res = LocalGuideService.search_destination("Tokyo")
    assert "Tokyo" in tokyo_res["destination"]
    assert abs(tokyo_res["latitude"] - 35.68) < 1.0
    tokyo_names = [p["name"] for p in tokyo_res["places"]]
    assert not any("Monkey Falls" in n or "Rajaji Statue" in n for n in tokyo_names)

    # 2. Seoul Search
    seoul_res = LocalGuideService.search_destination("Seoul")
    assert "Seoul" in seoul_res["destination"]
    assert abs(seoul_res["latitude"] - 37.57) < 1.0
    seoul_names = [p["name"] for p in seoul_res["places"]]
    assert not any("Monkey Falls" in n or "Rajaji Statue" in n for n in seoul_names)

    # 3. Truth-First null rating & hours check on unverified Overpass items
    unverified_el = {"id": 99999, "type": "node", "lat": 35.68, "lon": 139.76, "tags": {"name": "Test Node"}}
    normalized = normalize_place_data(unverified_el, 35.68, 139.76)
    assert normalized["rating"] is None
    assert normalized["opening_hours"] is None
    assert normalized["price_level"] is None
