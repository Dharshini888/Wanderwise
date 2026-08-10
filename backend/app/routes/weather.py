from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import weather_activity_advisor
import urllib.request
import urllib.parse
import json

router = APIRouter(prefix="/api/weather", tags=["Weather"])


class ActivityRequest(BaseModel):
    destination: str
    weather_desc: str
    temperature: float


def _parse_json(raw: str):
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"raw": raw}


# Full WMO weather code descriptions
WMO_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail",
}


def _safe_get(lst, i, default=None):
    try:
        return lst[i] if lst and i < len(lst) else default
    except Exception:
        return default


CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "saigon": "Ho Chi Minh City",
}


def _get_fallback_weather(city: str) -> dict:
    """Fallback weather response when Open-Meteo or geocoding is unavailable or encounters errors."""
    raise HTTPException(status_code=404, detail=f"No weather data available for {city}")


@router.get("/{city}")
def get_weather(city: str):
    """
    Fetch live weather from Open-Meteo (free, no API key needed).
    Returns current conditions, 7-day forecast, and 24h hourly data.
    """
    search_city = city.strip()
    if search_city.lower() in CITY_ALIASES:
        search_city = CITY_ALIASES[search_city.lower()]

    try:
        # Step 1: Geocode city name
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={urllib.parse.quote(search_city)}&count=1&language=en&format=json"
        )
        req = urllib.request.Request(geo_url, headers={"User-Agent": "WanderWise/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read())

        lat = None
        lon = None
        name = city
        country = ""
        timezone = "auto"

        if geo_data.get("results"):
            loc = geo_data["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            name = loc.get("name", city)
            country = loc.get("country", "")
            timezone = loc.get("timezone", "auto")
        else:
            # Step 1b: Fallback to Nominatim / Photon geocoding for regions, states, islands, etc.
            try:
                from app.services.maps.nominatim_service import geocode_place
                fallback_geo = geocode_place(search_city)
                if fallback_geo and fallback_geo.get("source") != "Estimated Coordinates" and "lat" in fallback_geo and "lon" in fallback_geo:
                    lat = fallback_geo["lat"]
                    lon = fallback_geo["lon"]
                    parts = fallback_geo.get("display_name", city).split(",")
                    name = parts[0].strip()
                    country = parts[-1].strip() if len(parts) > 1 else ""
            except Exception:
                pass

        if lat is None or lon is None:
            return _get_fallback_weather(city)

        # Step 2: Fetch current + daily + hourly weather from Open-Meteo
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"weather_code,wind_speed_10m,wind_direction_10m,precipitation,"
            f"uv_index,visibility,surface_pressure,is_day"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,uv_index_max,sunrise,sunset,wind_speed_10m_max,"
            f"precipitation_probability_max"
            f"&hourly=temperature_2m,precipitation_probability,weather_code"
            f"&forecast_days=7&timezone={urllib.parse.quote(timezone)}"
        )
        w_req = urllib.request.Request(weather_url, headers={"User-Agent": "WanderWise/1.0"})
        with urllib.request.urlopen(w_req, timeout=5) as resp:
            w = json.loads(resp.read())

        current = w.get("current", {})
        daily = w.get("daily", {})
        hourly = w.get("hourly", {})

        code = current.get("weather_code", 0)

        # Build 7-day forecast
        forecast = []
        dates = daily.get("time", []) or []
        d_codes = daily.get("weather_code", []) or []
        d_max = daily.get("temperature_2m_max", []) or []
        d_min = daily.get("temperature_2m_min", []) or []
        d_precip = daily.get("precipitation_sum", []) or []
        d_precip_prob = daily.get("precipitation_probability_max", []) or []
        d_uv = daily.get("uv_index_max", []) or []
        d_wind = daily.get("wind_speed_10m_max", []) or []
        d_sunrise = daily.get("sunrise", []) or []
        d_sunset = daily.get("sunset", []) or []

        for i in range(len(dates)):
            day_code = _safe_get(d_codes, i, 0)
            forecast.append({
                "date": dates[i],
                "weather_code": day_code,
                "description": WMO_MAP.get(day_code, "Unknown"),
                "max_temp": _safe_get(d_max, i),
                "min_temp": _safe_get(d_min, i),
                "precipitation": _safe_get(d_precip, i, 0),
                "precipitation_probability": _safe_get(d_precip_prob, i),
                "uv_index_max": _safe_get(d_uv, i),
                "wind_speed_max": _safe_get(d_wind, i),
                "sunrise": _safe_get(d_sunrise, i),
                "sunset": _safe_get(d_sunset, i),
            })

        # Build next 24h hourly forecast starting from current hour
        current_time = current.get("time", "") or ""
        hourly_times = hourly.get("time", []) or []
        h_temps = hourly.get("temperature_2m", []) or []
        h_precip_prob = hourly.get("precipitation_probability", []) or []
        h_codes = hourly.get("weather_code", []) or []

        hourly_forecast = []
        started = False
        count = 0
        for i, t in enumerate(hourly_times):
            if not started and t[:13] >= current_time[:13]:
                started = True
            if started and count < 24:
                h_code = _safe_get(h_codes, i, 0)
                hourly_forecast.append({
                    "time": t,
                    "temperature": _safe_get(h_temps, i),
                    "precipitation_probability": _safe_get(h_precip_prob, i),
                    "weather_code": h_code,
                    "description": WMO_MAP.get(h_code, "Unknown"),
                })
                count += 1

        # Wind direction degrees -> compass
        wind_deg = current.get("wind_direction_10m", 0) or 0
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        wind_dir = directions[round(wind_deg / 45) % 8]

        return {
            "city": name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": wind_dir,
                "wind_degrees": wind_deg,
                "precipitation": current.get("precipitation"),
                "uv_index": current.get("uv_index"),
                "visibility": current.get("visibility"),
                "pressure": current.get("surface_pressure"),
                "is_day": current.get("is_day", 1),
                "description": WMO_MAP.get(code, "Unknown"),
                "weather_code": code,
            },
            "forecast": forecast,
            "hourly": hourly_forecast,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Weather Error] Live weather lookup failed for '{city}': {e}.")
        raise HTTPException(status_code=503, detail=f"Weather service unavailable for {city}")


@router.post("/activities")
def activity_recommendations(data: ActivityRequest):
    try:
        raw = weather_activity_advisor(
            destination=data.destination,
            weather_desc=data.weather_desc,
            temperature=data.temperature,
        )
        return _parse_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
