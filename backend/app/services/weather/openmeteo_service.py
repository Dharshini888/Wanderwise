import requests
from datetime import date, datetime
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

def get_seasonal_climate_standard(lat: Optional[float], lon: Optional[float], location_name: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns scientific regional climate standard when departure is > 14 days in the future,
    calibrated by destination latitude, hemisphere, and travel month.
    """
    month = 7
    if target_date:
        try:
            parts = str(target_date).split("-")
            if len(parts) >= 2:
                month = int(parts[1])
        except Exception:
            month = 7

    is_southern = (lat is not None and lat < 0)
    is_winter = (month in [12, 1, 2] and not is_southern) or (month in [6, 7, 8] and is_southern)
    is_summer = (month in [6, 7, 8] and not is_southern) or (month in [12, 1, 2] and is_southern)

    abs_lat = abs(lat) if lat is not None else 35.0

    if abs_lat > 60.0:  # Arctic / Sub-arctic (e.g. Reykjavik, Tromsø)
        if is_winter:
            temp_c = -2.0
            cond = "Crisp / Snow Showers"
            icon = "🌨️"
            rain_prob = 35
        elif month == 3:
            temp_c = 0.5
            cond = "Sub-Arctic Late Winter / Flurries"
            icon = "🌨️"
            rain_prob = 30
        elif is_summer:
            temp_c = 13.0
            cond = "Cool / Partly Cloudy"
            icon = "⛅"
            rain_prob = 20
        else:
            temp_c = 5.0
            cond = "Brisk / Overcast"
            icon = "☁️"
            rain_prob = 30
    elif abs_lat > 40.0:  # Temperate North/South (e.g. Paris, Tokyo, New York, Queenstown)
        if is_winter:
            temp_c = 6.0
            cond = "Chilly / Clear"
            icon = "⛅"
            rain_prob = 20
        elif is_summer:
            temp_c = 26.0
            cond = "Warm & Sunny"
            icon = "☀️"
            rain_prob = 15
        else:
            temp_c = 16.0
            cond = "Mild / Partly Cloudy"
            icon = "🌤️"
            rain_prob = 20
    elif abs_lat > 20.0:  # Subtropical (e.g. Istanbul, Delhi, Cairo, Dubai, Sydney)
        if is_winter:
            temp_c = 14.0
            cond = "Pleasant / Clear"
            icon = "☀️"
            rain_prob = 10
        elif is_summer:
            temp_c = 32.0
            cond = "Hot & Sunny"
            icon = "☀️"
            rain_prob = 5
        else:
            temp_c = 23.0
            cond = "Warm / Sunny"
            icon = "☀️"
            rain_prob = 10
    else:  # Tropical / Equatorial (e.g. Bali, Singapore, Bangkok, Coimbatore, Cusco)
        temp_c = 28.0 if abs_lat < 15.0 else 18.0
        if "cusco" in location_name.lower():
            temp_c = 16.0
            cond = "Mild Mountain Climate"
            icon = "⛅"
            rain_prob = 40 if month in [12, 1, 2, 3] else 10
        elif is_winter:
            cond = "Tropical / Gentle Breeze"
            icon = "🌴"
            rain_prob = 20
        else:
            cond = "Tropical / Warm"
            icon = "☀️"
            rain_prob = 30

    return {
        "location": location_name,
        "temp_c": temp_c,
        "condition": cond,
        "icon": icon,
        "rain_probability": rain_prob,
        "visibility_km": 10.0,
        "wind_kmh": 12.0,
        "source": "Historical Regional Climate Benchmark",
        "weather_confidence": "Seasonal Climate Standard"
    }

def get_openmeteo_weather(lat: Optional[float], lon: Optional[float], location_name: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches real-time weather from Open-Meteo API when departure date is within 14 days.
    If travel date is > 14 days in the future, returns historical regional Seasonal Climate Standard.
    """
    if target_date:
        try:
            t_dt = datetime.strptime(str(target_date)[:10], "%Y-%m-%d").date()
            days_diff = (t_dt - date.today()).days
            if days_diff > 14:
                return get_seasonal_climate_standard(lat, lon, location_name, target_date)
        except Exception:
            pass

    if lat is None or lon is None:
        return get_seasonal_climate_standard(lat, lon, location_name, target_date)

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
    
    return get_seasonal_climate_standard(lat, lon, location_name, target_date)
