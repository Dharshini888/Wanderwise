import requests
import urllib.parse
from typing import Dict, Any, Optional
from ..cache.transit_cache import TransitCache

STATIC_COORDS = {
    "kovaipudhur": {"lat": 10.9575, "lon": 76.9298, "display_name": "Kovaipudhur, Coimbatore, Tamil Nadu, India", "country_code": "IN"},
    "coimbatore junction": {"lat": 11.0017, "lon": 76.9629, "display_name": "Coimbatore Junction, Tamil Nadu, India", "country_code": "IN"},
    "coimbatore jn": {"lat": 11.0017, "lon": 76.9629, "display_name": "Coimbatore Junction, Tamil Nadu, India", "country_code": "IN"},
    "cbe": {"lat": 11.0017, "lon": 76.9629, "display_name": "Coimbatore Junction, Tamil Nadu, India", "country_code": "IN"},
    "coimbatore": {"lat": 11.0168, "lon": 76.9558, "display_name": "Coimbatore, Tamil Nadu, India", "country_code": "IN"},
    "karur": {"lat": 10.9601, "lon": 78.0766, "display_name": "Karur, Tamil Nadu, India", "country_code": "IN"},
    "erode": {"lat": 11.3410, "lon": 77.7172, "display_name": "Erode, Tamil Nadu, India", "country_code": "IN"},
    "erode junction": {"lat": 11.3400, "lon": 77.7289, "display_name": "Erode Junction, Tamil Nadu, India", "country_code": "IN"},
    "erode jn": {"lat": 11.3400, "lon": 77.7289, "display_name": "Erode Junction, Tamil Nadu, India", "country_code": "IN"},
    "ed": {"lat": 11.3400, "lon": 77.7289, "display_name": "Erode Junction, Tamil Nadu, India", "country_code": "IN"},
    "chennai central": {"lat": 13.0827, "lon": 80.2757, "display_name": "Chennai Central, Tamil Nadu, India", "country_code": "IN"},
    "chennai egmore": {"lat": 13.0782, "lon": 80.2612, "display_name": "Chennai Egmore, Tamil Nadu, India", "country_code": "IN"},
    "mas": {"lat": 13.0827, "lon": 80.2757, "display_name": "Chennai Central, Tamil Nadu, India", "country_code": "IN"},
    "ms": {"lat": 13.0782, "lon": 80.2612, "display_name": "Chennai Egmore, Tamil Nadu, India", "country_code": "IN"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "display_name": "Chennai, Tamil Nadu, India", "country_code": "IN"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India", "country_code": "IN"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India", "country_code": "IN"},
    "sbc": {"lat": 12.9781, "lon": 77.5697, "display_name": "KSR Bengaluru, Karnataka, India", "country_code": "IN"},
    "ksr bengaluru": {"lat": 12.9781, "lon": 77.5697, "display_name": "KSR Bengaluru, Karnataka, India", "country_code": "IN"},
    "ksr bengaluru city": {"lat": 12.9781, "lon": 77.5697, "display_name": "KSR Bengaluru City, Karnataka, India", "country_code": "IN"},
    "bangalore city": {"lat": 12.9781, "lon": 77.5697, "display_name": "KSR Bengaluru, Karnataka, India", "country_code": "IN"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "display_name": "Pune, Maharashtra, India", "country_code": "IN"},
    "pune junction": {"lat": 18.5284, "lon": 73.8739, "display_name": "Pune Junction, Maharashtra, India", "country_code": "IN"},
    "pune jn": {"lat": 18.5284, "lon": 73.8739, "display_name": "Pune Junction, Maharashtra, India", "country_code": "IN"},
    "madurai": {"lat": 9.9252, "lon": 78.1198, "display_name": "Madurai, Tamil Nadu, India", "country_code": "IN"},
    "madurai junction": {"lat": 9.9195, "lon": 78.1193, "display_name": "Madurai Junction, Tamil Nadu, India", "country_code": "IN"},
    "madurai jn": {"lat": 9.9195, "lon": 78.1193, "display_name": "Madurai Junction, Tamil Nadu, India", "country_code": "IN"},
    "mdu": {"lat": 9.9195, "lon": 78.1193, "display_name": "Madurai Junction, Tamil Nadu, India", "country_code": "IN"},
    "salem": {"lat": 11.6643, "lon": 78.1460, "display_name": "Salem, Tamil Nadu, India", "country_code": "IN"},
    "salem junction": {"lat": 11.6643, "lon": 78.1189, "display_name": "Salem Junction, Tamil Nadu, India", "country_code": "IN"},
    "salem jn": {"lat": 11.6643, "lon": 78.1189, "display_name": "Salem Junction, Tamil Nadu, India", "country_code": "IN"},
    "sa": {"lat": 11.6643, "lon": 78.1189, "display_name": "Salem Junction, Tamil Nadu, India", "country_code": "IN"},
    "mysuru": {"lat": 12.2958, "lon": 76.6394, "display_name": "Mysuru, Karnataka, India", "country_code": "IN"},
    "mysore": {"lat": 12.2958, "lon": 76.6394, "display_name": "Mysuru, Karnataka, India", "country_code": "IN"},
    "mysuru junction": {"lat": 12.3164, "lon": 76.6453, "display_name": "Mysuru Junction, Karnataka, India", "country_code": "IN"},
    "mysore junction": {"lat": 12.3164, "lon": 76.6453, "display_name": "Mysuru Junction, Karnataka, India", "country_code": "IN"},
    "tiruppur": {"lat": 11.1085, "lon": 77.3411, "display_name": "Tiruppur, Tamil Nadu, India", "country_code": "IN"},
    "katpadi": {"lat": 12.9698, "lon": 79.1368, "display_name": "Katpadi Junction, Tamil Nadu, India", "country_code": "IN"},
    "jolarpettai": {"lat": 12.5564, "lon": 78.5775, "display_name": "Jolarpettai Junction, Tamil Nadu, India", "country_code": "IN"},
    "trichy": {"lat": 10.7905, "lon": 78.6924, "display_name": "Tiruchirappalli, Tamil Nadu, India", "country_code": "IN"},
    "tiruchirappalli": {"lat": 10.7905, "lon": 78.6924, "display_name": "Tiruchirappalli, Tamil Nadu, India", "country_code": "IN"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "display_name": "Mumbai, Maharashtra, India", "country_code": "IN"},
    "mumbai central": {"lat": 18.9696, "lon": 72.8193, "display_name": "Mumbai Central, Maharashtra, India", "country_code": "IN"},
    "mumbai csmt": {"lat": 18.9400, "lon": 72.8353, "display_name": "Chhatrapati Shivaji Maharaj Terminus, Mumbai, India", "country_code": "IN"},
    "csmt": {"lat": 18.9400, "lon": 72.8353, "display_name": "Chhatrapati Shivaji Maharaj Terminus, Mumbai, India", "country_code": "IN"},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India", "country_code": "IN"},
    "goa": {"lat": 15.2993, "lon": 74.1240, "display_name": "Goa, India", "country_code": "IN"},
    "kyoto station": {"lat": 34.9858, "lon": 135.7588, "display_name": "Kyoto Station, Kyoto, Japan", "country_code": "JP"},
    "kiyomizu-dera": {"lat": 34.9949, "lon": 135.7850, "display_name": "Kiyomizu-dera, Kyoto, Japan", "country_code": "JP"},
    "fushimi inari": {"lat": 34.9671, "lon": 135.7727, "display_name": "Fushimi Inari-taisha, Kyoto, Japan", "country_code": "JP"},
    "kyoto": {"lat": 35.0116, "lon": 135.7681, "display_name": "Kyoto, Japan", "country_code": "JP"},
    "kansai international airport": {"lat": 34.4347, "lon": 135.2442, "display_name": "Kansai International Airport, Osaka, Japan", "country_code": "JP"},
    "kansai airport": {"lat": 34.4347, "lon": 135.2442, "display_name": "Kansai International Airport, Osaka, Japan", "country_code": "JP"},
    "kansai": {"lat": 34.4347, "lon": 135.2442, "display_name": "Kansai International Airport, Osaka, Japan", "country_code": "JP"},
    "osaka": {"lat": 34.6937, "lon": 135.5023, "display_name": "Osaka, Japan", "country_code": "JP"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "display_name": "Tokyo, Japan", "country_code": "JP"},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "display_name": "Seoul, South Korea", "country_code": "KR"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "display_name": "Paris, Île-de-France, France", "country_code": "FR"},
    "london": {"lat": 51.5074, "lon": -0.1278, "display_name": "London, England, United Kingdom", "country_code": "GB"},
    "manchester": {"lat": 53.4808, "lon": -2.2426, "display_name": "Manchester, England, United Kingdom", "country_code": "GB"},
    "varkala": {"lat": 8.7379, "lon": 76.7163, "display_name": "Varkala, Kerala, India", "country_code": "IN"},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "display_name": "Dubai, United Arab Emirates", "country_code": "AE"},
    "bali": {"lat": -8.4095, "lon": 115.1889, "display_name": "Bali, Indonesia", "country_code": "ID"},
    "rome": {"lat": 41.9028, "lon": 12.4964, "display_name": "Rome, Italy", "country_code": "IT"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "display_name": "Singapore", "country_code": "SG"},
    "hawaii": {"lat": 21.3069, "lon": -157.8583, "display_name": "Hawaii, USA", "country_code": "US"},
    "switzerland": {"lat": 46.8182, "lon": 8.2275, "display_name": "Switzerland", "country_code": "CH"},
    "zurich": {"lat": 47.3769, "lon": 8.5417, "display_name": "Zurich, Switzerland", "country_code": "CH"},
    "lucerne": {"lat": 47.0502, "lon": 8.3093, "display_name": "Lucerne, Switzerland", "country_code": "CH"},
    "interlaken": {"lat": 46.6863, "lon": 7.8632, "display_name": "Interlaken, Switzerland", "country_code": "CH"},
    "geneva": {"lat": 46.2044, "lon": 6.1432, "display_name": "Geneva, Switzerland", "country_code": "CH"},
    "istanbul": {"lat": 41.0082, "lon": 28.9784, "display_name": "Istanbul, Turkey", "country_code": "TR"},
    "cairo": {"lat": 30.0444, "lon": 31.2357, "display_name": "Cairo, Egypt", "country_code": "EG"},
    "bern": {"lat": 46.9480, "lon": 7.4474, "display_name": "Bern, Switzerland", "country_code": "CH"},
    "zermatt": {"lat": 45.9763, "lon": 7.7491, "display_name": "Zermatt, Switzerland", "country_code": "CH"},
    "reykjavik": {"lat": 64.1466, "lon": -21.9426, "display_name": "Reykjavík, Iceland", "country_code": "IS"},
    "tromso": {"lat": 69.6492, "lon": 18.9553, "display_name": "Tromsø, Norway", "country_code": "NO"},
    "tromsø": {"lat": 69.6492, "lon": 18.9553, "display_name": "Tromsø, Norway", "country_code": "NO"},
    "cusco": {"lat": -13.5320, "lon": -71.9675, "display_name": "Cusco, Peru", "country_code": "PE"},
    "cuzco": {"lat": -13.5320, "lon": -71.9675, "display_name": "Cusco, Peru", "country_code": "PE"},
    "queenstown": {"lat": -45.0312, "lon": 168.6626, "display_name": "Queenstown, New Zealand", "country_code": "NZ"}
}

def reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Reverse geocodes coordinates to a place name using Nominatim.
    """
    cache_key = f"rev_geocode_{lat}_{lon}"
    
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        headers = {"User-Agent": "WanderWise-SmartTransit/4.1 (dhars@wanderwise.ai)"}
        resp = requests.get(url, headers=headers, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            if "display_name" in data:
                address = data.get("address", {})
                cc = address.get("country_code", "").upper()
                result = {
                    "lat": float(lat),
                    "lon": float(lon),
                    "display_name": data["display_name"],
                    "country_code": cc or "UNKNOWN",
                    "source": "Live (Nominatim Reverse)"
                }
                TransitCache.set(cache_key, result)
                return result
    except Exception:
        pass

    return None

def geocode_place(place_name: str) -> Dict[str, Any]:
    """
    Geocodes a place name using Cache -> Static Hubs -> Nominatim -> Photon -> Fallback.
    Returns: {"lat": float, "lon": float, "display_name": str, "country_code": str, "source": str}
    """
    clean_name = place_name.strip().lower()
    cache_key = f"geocode_{clean_name}"
    
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    # Pre-check exact match in STATIC_COORDS for fast and reliable resolution of known hubs
    if clean_name in STATIC_COORDS:
        static_val = STATIC_COORDS[clean_name]
        res = {
            "lat": static_val["lat"],
            "lon": static_val["lon"],
            "display_name": static_val["display_name"],
            "country_code": static_val["country_code"],
            "source": "Static Pre-seeded Fallback"
        }
        TransitCache.set(cache_key, res)
        return res

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

    # 4. Fallback Global Destination Gazetteer lookup
    try:
        from app.services.location.location_normalizer import GLOBAL_DESTINATION_GAZETTEER
        for g_key, g_val in GLOBAL_DESTINATION_GAZETTEER.items():
            if g_key in clean_name or clean_name in g_key:
                return {
                    "lat": g_val["latitude"],
                    "lon": g_val["longitude"],
                    "display_name": f"{g_val['name']}, {g_val['country']}",
                    "country_code": g_val.get("country_code", "UNKNOWN"),
                    "source": "Global Gazetteer Fallback"
                }
    except Exception:
        pass

    return {
        "lat": None,
        "lon": None,
        "display_name": place_name,
        "country_code": "UNKNOWN",
        "source": "Failed Resolution",
        "is_valid": False
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
