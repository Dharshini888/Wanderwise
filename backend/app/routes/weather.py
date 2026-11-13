from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
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


def _estimate_seasonal_climate(city: str, lat: Optional[float] = None, month: int = 3) -> dict:
    """Dynamic global seasonal climate estimation based on geography, latitude bands, and calendar month."""
    city_l = (city or "").lower()
    is_tropical = (lat is not None and abs(lat) <= 23.5) or any(t in city_l for t in ["bali", "phuket", "singapore", "bangkok", "maldives", "hawaii", "colombo", "varkala", "goa", "chennai"])
    is_mediterranean = (lat is not None and 35.0 < abs(lat) <= 45.0) or any(t in city_l for t in ["istanbul", "rome", "athens", "madrid", "barcelona"])
    is_subtropical = (lat is not None and 23.5 < abs(lat) <= 35.0) or any(t in city_l for t in ["cairo", "dubai", "jaipur", "delhi", "tokyo", "kyoto"])

    if is_tropical:
        temp = 28.0
        desc = "Tropical Climate (Historical Seasonal Standard)"
        precip = 25
    elif is_mediterranean:
        temp = 14.5 if month in [3, 4, 10, 11] else (26.0 if month in [6, 7, 8, 9] else 9.0)
        desc = "Mediterranean Seasonal Climate Standard"
        precip = 20
    elif is_subtropical:
        temp = 20.0
        desc = "Subtropical Seasonal Climate Standard"
        precip = 15
    else:
        temp = 18.0
        desc = "Temperate Seasonal Climate Standard"
        precip = 15

    return {
        "temperature": temp,
        "feels_like": round(temp + 1.0, 1),
        "description": desc,
        "precipitation_probability": precip
    }


def _get_fallback_weather(city: str, date_str: Optional[str] = None) -> dict:
    """Fallback weather response when Open-Meteo or geocoding is unavailable or encounters network errors."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_seasonal = bool(date_str)
    weather_status = "Forecast unavailable" if is_seasonal else "Weather Unavailable"
    weather_confidence = "Seasonal Climate Standard" if is_seasonal else "Weather Unavailable"

    clean_target = date_str.split("T")[0] if date_str else ""
    target_month = 3
    if clean_target:
        try:
            target_month = int(clean_target.split("-")[1])
        except Exception:
            pass

    climate_est = _estimate_seasonal_climate(city, month=target_month)

    selected_date_weather = None
    if date_str:
        selected_date_weather = {
            "temperature": climate_est["temperature"],
            "feels_like": climate_est["feels_like"],
            "description": climate_est["description"],
            "weather_code": 1,
            "precipitation_probability": climate_est["precipitation_probability"],
            "status_label": f"Forecast unavailable — Seasonal Climate Standard for {clean_target}",
            "weather_status": "Forecast unavailable",
            "weather_confidence": "Seasonal Climate Standard",
            "is_confirmed_forecast": False,
            "forecast_unavailable": True,
            "provenance_note": f"Live atmospheric forecast unavailable for distant dates ({clean_target}). Typical historical seasonal climate standard displayed."
        }

    return {
        "city": city.strip().title(),
        "country": "International Destination",
        "latitude": 0.0,
        "longitude": 0.0,
        "timezone": "UTC",
        "provider": "Open-Meteo Weather Service (Estimated Baseline)",
        "timestamp": now_utc,
        "forecast_type": "Seasonal Climate Estimate" if is_seasonal else "Estimated Baseline",
        "is_seasonal_estimate": is_seasonal,
        "weather_status": weather_status,
        "weather_confidence": weather_confidence,
        "provenance_note": (
            f"Forecast unavailable for distant travel dates ({clean_target}). Typical historical seasonal climate standard displayed."
            if is_seasonal else "Seasonal estimate baseline; live forecast available within 14 days of departure."
        ),
        "current": {
            "temperature": climate_est["temperature"],
            "feels_like": climate_est["feels_like"],
            "humidity": 65,
            "wind_speed": 10.0,
            "wind_direction": "N",
            "wind_degrees": 0,
            "precipitation": 0.0,
            "uv_index": 5.0,
            "visibility": 10000,
            "pressure": 1013,
            "is_day": 1,
            "description": climate_est["description"],
            "weather_code": 1,
        },
        "selected_date_weather": selected_date_weather,
        "forecast": [],
        "hourly": [],
        "source": "Estimated Fallback Weather"
    }


@router.get("/{city}")
def get_weather(city: str, date_str: Optional[str] = None):
    """
    Fetch weather for a destination on a specific date (or current date if omitted).
    Supports 7-day Open-Meteo forecast, current live weather, and future date seasonal estimates.
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
            # Step 1b: Fallback to Nominatim geocoding
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

        # Check date_str relative to current date and 14-day live forecast horizon
        selected_date_weather = None
        weather_status_label = "Live Weather"

        if date_str:
            clean_target = date_str.split("T")[0]
            try:
                target_date_obj = datetime.strptime(clean_target, "%Y-%m-%d").date()
                today_obj = datetime.now(timezone.utc).date()
                days_ahead = (target_date_obj - today_obj).days
            except Exception:
                days_ahead = 30

            matching_forecast = next((f for f in forecast if f["date"] == clean_target), None) if days_ahead <= 14 else None

            if matching_forecast:
                selected_date_weather = {
                    "temperature": matching_forecast.get("max_temp"),
                    "feels_like": matching_forecast.get("max_temp"),
                    "description": matching_forecast.get("description"),
                    "weather_code": matching_forecast.get("weather_code"),
                    "precipitation_probability": matching_forecast.get("precipitation_probability"),
                    "status_label": f"Confirmed Forecast for {clean_target}",
                    "weather_status": "Live Forecast",
                    "weather_confidence": "Live Forecast",
                    "is_confirmed_forecast": True,
                    "forecast_unavailable": False
                }
            else:
                target_month = 3
                if clean_target:
                    try:
                        target_month = int(clean_target.split("-")[1])
                    except Exception:
                        pass
                climate_est = _estimate_seasonal_climate(search_city, lat=lat, month=target_month)
                selected_date_weather = {
                    "temperature": climate_est["temperature"],
                    "feels_like": climate_est["feels_like"],
                    "description": climate_est["description"],
                    "weather_code": 1,
                    "precipitation_probability": climate_est["precipitation_probability"],
                    "status_label": f"Forecast unavailable — Seasonal Climate Standard for {clean_target}",
                    "weather_status": "Forecast unavailable",
                    "weather_confidence": "Seasonal Climate Standard",
                    "is_confirmed_forecast": False,
                    "forecast_unavailable": True,
                    "provenance_note": f"Live atmospheric forecast unavailable for distant dates ({clean_target}). Typical historical seasonal climate standard displayed."
                }

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

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        is_seasonal = selected_date_weather is not None and not selected_date_weather.get("is_confirmed_forecast", True)
        
        # Weather confidence labeling: Live Forecast (<= 14 days), Seasonal Climate Standard (> 14 days)
        weather_status = "Forecast unavailable" if is_seasonal else "Live Forecast"
        weather_confidence = "Seasonal Climate Standard" if is_seasonal else "Live Forecast"

        return {
            "city": name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "provider": "Open-Meteo Weather Service",
            "timestamp": now_utc,
            "forecast_type": "Seasonal Climate Estimate" if is_seasonal else "Live & 7-Day Forecast",
            "is_seasonal_estimate": is_seasonal,
            "weather_status": weather_status,
            "weather_confidence": weather_confidence,
            "provenance_note": (
                f"Seasonal climate projection for target date. Live atmospheric forecast updates within 14 days of trip."
                if is_seasonal else f"Live Open-Meteo observations and 7-day model forecast as of {now_utc}."
            ),
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
            "selected_date_weather": selected_date_weather,
            "forecast": forecast,
            "hourly": hourly_forecast,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Weather Error] Live weather lookup failed for '{city}': {e}. Returning robust seasonal fallback.")
        return _get_fallback_weather(city, date_str=date_str)


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
