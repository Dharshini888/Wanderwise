import requests
from typing import Dict, Any, Optional
from ..cache.transit_cache import TransitCache

WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "☀️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "⛈️"),
    80: ("Rain showers", "🌦️"),
    95: ("Thunderstorm", "⛈️")
}

def get_openmeteo_weather(lat: Optional[float], lon: Optional[float], location_name: str) -> Dict[str, Any]:
    """
    Fetches real-time weather from Open-Meteo API (100% free, no API key).
    Returns: {"temp_c": float, "condition": str, "icon": str, "rain_probability": int, "visibility_km": float, "wind_kmh": float, "source": str}
    """
    if lat is None or lon is None:
        return {
            "location": location_name,
            "temp_c": 25.0,
            "condition": "Pleasant",
            "icon": "🌤️",
            "rain_probability": 10,
            "visibility_km": 10.0,
            "wind_kmh": 12.0,
            "source": "Default Baseline",
            "weather_confidence": "Seasonal Climate Standard"
        }

    cache_key = f"weather_{lat:.2f}_{lon:.2f}"
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m,precipitation_probability,visibility,wind_speed_10m"
        resp = requests.get(url, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current_weather", {})
            temp = round(curr.get("temperature", 28.0), 1)
            code = curr.get("weathercode", 0)
            wind = round(curr.get("windspeed", 12.0), 1)
            
            cond, icon = WEATHER_CODES.get(code, ("Clear", "☀️"))
            
            # Extract rain probability and visibility from hourly if available
            hourly = data.get("hourly", {})
            rain_prob = hourly.get("precipitation_probability", [10])[0] if hourly.get("precipitation_probability") else 10
            vis_m = hourly.get("visibility", [10000])[0] if hourly.get("visibility") else 10000
            vis_km = round(vis_m / 1000.0, 1)

            result = {
                "location": location_name,
                "temp_c": temp,
                "condition": cond,
                "icon": icon,
                "rain_probability": rain_prob,
                "visibility_km": vis_km,
                "wind_kmh": wind,
                "source": "Live (Open-Meteo)",
                "weather_confidence": "Live Forecast"
            }
            TransitCache.set(cache_key, result)
            return result
    except Exception:
        pass
    
    return {
        "location": location_name,
        "temp_c": "--",
        "condition": "Unavailable",
        "icon": "❓",
        "rain_probability": 0,
        "visibility_km": 0,
        "wind_kmh": 0,
        "source": "Unavailable",
        "weather_confidence": "Weather Unavailable"
    }
