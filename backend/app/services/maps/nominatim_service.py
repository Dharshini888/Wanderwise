import requests
import urllib.parse
from typing import Dict, Any, Optional
from ..cache.transit_cache import TransitCache

STATIC_COORDS = {
    "coimbatore": {"lat": 11.0168, "lon": 76.9558, "display_name": "Coimbatore, Tamil Nadu, India", "country_code": "IN"},
    "erode": {"lat": 11.3410, "lon": 77.7172, "display_name": "Erode, Tamil Nadu, India", "country_code": "IN"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "display_name": "Chennai, Tamil Nadu, India", "country_code": "IN"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India", "country_code": "IN"},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India", "country_code": "IN"},
    "goa": {"lat": 15.2993, "lon": 74.1240, "display_name": "Goa, India", "country_code": "IN"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "display_name": "Mumbai, Maharashtra, India", "country_code": "IN"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "display_name": "Tokyo, Japan", "country_code": "JP"},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "display_name": "Seoul, South Korea", "country_code": "KR"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "display_name": "Paris, Île-de-France, France", "country_code": "FR"},
    "london": {"lat": 51.5074, "lon": -0.1278, "display_name": "London, England, United Kingdom", "country_code": "GB"},
    "manchester": {"lat": 53.4808, "lon": -2.2426, "display_name": "Manchester, England, United Kingdom", "country_code": "GB"}
}

def geocode_place(place_name: str) -> Dict[str, Any]:
    """
    Geocodes a place name using Nominatim -> Photon -> Cache -> Static Fallback.
    Returns: {"lat": float, "lon": float, "display_name": str, "country_code": str, "source": str}
    """
    clean_name = place_name.strip().lower()
    cache_key = f"geocode_{clean_name}"
    
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    # 1. Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place_name)}&format=json&limit=1&addressdetails=1"
        headers = {"User-Agent": "WanderWise-SmartTransit/4.1 (dhars@wanderwise.ai)"}
        resp = requests.get(url, headers=headers, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                address = data[0].get("address", {})
                cc = address.get("country_code", "").upper()
                result = {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", place_name),
                    "country_code": cc or "UNKNOWN",
                    "source": "Live (Nominatim)"
                }
                TransitCache.set(cache_key, result)
                return result
    except Exception:
        pass

    # 2. Photon
    try:
        url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(place_name)}&limit=1"
        resp = requests.get(url, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                props = features[0].get("properties", {})
                display_name = f"{props.get('name', place_name)}, {props.get('country', '')}".strip(", ")
                cc = props.get("countrycode", "").upper()
                result = {
                    "lat": coords[1],
                    "lon": coords[0],
                    "display_name": display_name,
                    "country_code": cc or "UNKNOWN",
                    "source": "Live (Photon)"
                }
                TransitCache.set(cache_key, result)
                return result
    except Exception:
        pass

    # 3. Fallback Static Coordinates lookup
    for key, static_val in STATIC_COORDS.items():
        if key in clean_name:
            result = {
                "lat": static_val["lat"],
                "lon": static_val["lon"],
                "display_name": static_val["display_name"],
                "country_code": static_val["country_code"],
                "source": "Static Pre-seeded Fallback"
            }
            return result

    return {
        "lat": 12.9716,
        "lon": 77.5946,
        "display_name": f"{place_name} (Estimated Location)",
        "country_code": "IN",
        "source": "Default Search Fallback"
    }


def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """Reverse geocodes coordinates to get display_name and address details."""
    cache_key = f"reverse_geocode_{lat:.4f}_{lon:.4f}"
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        headers = {"User-Agent": "WanderWise-SmartTransit/4.1 (dhars@wanderwise.ai)"}
        resp = requests.get(url, headers=headers, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                addr = data.get("address", {})
                data["country_code"] = addr.get("country_code", "").upper()
            TransitCache.set(cache_key, data)
            return data
    except Exception:
        pass
    return {}
