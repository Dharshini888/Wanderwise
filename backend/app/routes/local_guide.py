from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional, List, Dict, Any
from app.services.local_guide_service import LocalGuideService, CATEGORY_OVERPASS_QUERIES
from app.routes.weather import get_weather

router = APIRouter(prefix="/api/guide", tags=["Local Travel Guide"])

CATEGORIES_LIST = [
    {"id": "ALL", "label": "All", "icon": "Compass"},
    {"id": "ATTRACTIONS", "label": "Attractions", "icon": "Landmark"},
    {"id": "RESTAURANTS", "label": "Food & Dining", "icon": "Utensils"},
    {"id": "CAFES", "label": "Cafés", "icon": "Coffee"},
    {"id": "HOTELS", "label": "Hotels", "icon": "Hotel"},
    {"id": "TRANSPORT", "label": "Transit", "icon": "Bus"},
    {"id": "HOSPITALS", "label": "Hospitals", "icon": "Hospital"},
    {"id": "PHARMACIES", "label": "Pharmacies", "icon": "Pill"},
    {"id": "SHOPPING", "label": "Shopping", "icon": "ShoppingBag"},
    {"id": "ATMS", "label": "ATMs & Banks", "icon": "CreditCard"},
    {"id": "EMERGENCY", "label": "Emergency", "icon": "ShieldAlert"},
]


@router.get("/categories")
def get_guide_categories():
    """Returns list of supported categories for Local Travel Guide."""
    return {"categories": CATEGORIES_LIST}


@router.get("/search")
def search_guide_destination(
    destination: str = Query(..., min_length=1, description="City or destination name"),
):
    """
    Geocodes a destination and fetches real nearby POIs, weather, and cultural guidelines.
    """
    try:
        data = LocalGuideService.search_destination(destination)

        # Include destination weather if available
        weather_info = None
        try:
            weather_info = get_weather(destination)
        except Exception:
            weather_info = {"status": "Unavailable", "message": "Weather data unavailable"}

        data["weather"] = weather_info
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search destination guide for '{destination}': {str(e)}"
        )


@router.get("/nearby")
def get_nearby_guide_places(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: int = Query(3000, ge=100, le=10000, description="Search radius in meters"),
    category: str = Query("ALL", description="Category filter"),
    query: Optional[str] = Query(None, description="Optional search term"),
    destination: Optional[str] = Query(None, description="Optional destination name"),
):
    """
    Fetches real nearby places from OpenStreetMap within specified radius and category.
    """
    try:
        return LocalGuideService.get_nearby_places(
            lat=lat,
            lon=lon,
            radius=radius,
            category=category,
            query=query,
            destination=destination
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby guide places: {str(e)}"
        )


@router.get("/place/{place_id:path}")
def get_place_details(
    place_id: str,
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    """
    Fetches details for a single place by OSM ID (node/123, way/456, relation/789).
    """
    try:
        return LocalGuideService.get_place_by_id(place_id, lat=lat, lon=lon)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place details not found for '{place_id}': {str(e)}"
        )


@router.get("/route")
def get_place_route(
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lon: float = Query(..., description="Origin longitude"),
    dest_lat: float = Query(..., description="Destination latitude"),
    dest_lon: float = Query(..., description="Destination longitude"),
    mode: str = Query("walking", description="Travel mode: walking or driving"),
):
    """
    Calculates OSRM routing distance, estimated duration, and route geometry.
    Returns status 'Route Calculated'.
    """
    try:
        return LocalGuideService.calculate_directions(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            mode=mode
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route calculation failed: {str(e)}"
        )
