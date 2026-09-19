import json
import math
import urllib.parse
import urllib.request
import logging
from typing import Dict, Any, List

logger = logging.getLogger("wanderwise.safety")

# ─── Country Emergency Numbers Dataset ───────────────────────────────────────
COUNTRY_EMERGENCY = {
    "india":     {"Police": "100 / 112", "Ambulance": "108", "Fire": "101",
                  "Tourist Helpline": "1363", "Women Helpline": "1091",
                  "Disaster Mgmt": "1078", "Coast Guard": "1554"},
    "japan":     {"Emergency": "119", "Police": "110", "Ambulance": "119",
                  "Fire": "119", "Tourist Hotline": "050-3816-2787",
                  "Coast Guard": "118"},
    "france":    {"Police": "17", "Ambulance": "15", "Fire": "18",
                  "Emergency": "112", "Mountain Rescue": "112"},
    "germany":   {"Police": "110", "Ambulance": "112", "Fire": "112",
                  "Emergency": "112"},
    "usa":       {"Police/Fire/Ambulance": "911",
                  "Tourist Info": "1-800-424-8802"},
    "uk":        {"Police/Fire/Ambulance": "999",
                  "Non-Emergency Police": "101", "NHS": "111"},
    "australia": {"Police/Fire/Ambulance": "000",
                  "Police Info Line": "131 444"},
    "canada":    {"Police/Fire/Ambulance": "911"},
    "singapore": {"Police": "999", "Ambulance": "995", "Fire": "995",
                  "Non-Emergency": "1800-255-0000"},
    "thailand":  {"Police": "191", "Ambulance": "1669", "Fire": "199",
                  "Tourist Police": "1155"},
    "malaysia":  {"Police": "999", "Ambulance": "999", "Fire": "994",
                  "Tourist Police": "1800-88-5050"},
    "indonesia": {"Police": "110", "Ambulance": "118", "Fire": "113",
                  "SAR": "115"},
    "vietnam":   {"Police": "113", "Ambulance": "115", "Fire": "114"},
    "uae":       {"Police": "999", "Ambulance": "998", "Fire": "997",
                  "Emergency": "999"},
    "sri lanka": {"Police": "119", "Ambulance": "110", "Fire": "111"},
    "nepal":     {"Police": "100", "Ambulance": "102", "Fire": "101"},
    "china":     {"Police": "110", "Ambulance": "120", "Fire": "119"},
    "italy":     {"Police": "113", "Ambulance": "118", "Fire": "115",
                  "Emergency": "112"},
    "spain":     {"Emergency": "112", "Police": "091", "Ambulance": "061",
                  "Fire": "080"},
    "default":   {"Emergency": "112", "Police": "112", "Ambulance": "112",
                  "Fire": "112"},
}

# ─── Currency per Country ──────────────────────────────────────────────────────
COUNTRY_CURRENCY = {
    "india": ("₹", "INR", "₹3,000–₹5,000"),
    "japan": ("¥", "JPY", "¥5,000–¥10,000"),
    "france": ("€", "EUR", "€40–€60"),
    "germany": ("€", "EUR", "€40–€60"),
    "usa": ("$", "USD", "$50–$100"),
    "uk": ("£", "GBP", "£30–£50"),
    "australia": ("A$", "AUD", "A$80–A$120"),
    "canada": ("C$", "CAD", "C$60–C$80"),
    "singapore": ("S$", "SGD", "S$50–S$80"),
    "thailand": ("฿", "THB", "฿1,500–฿3,000"),
    "malaysia": ("RM", "MYR", "RM 100–RM 200"),
    "indonesia": ("Rp", "IDR", "Rp 200,000–Rp 400,000"),
    "vietnam": ("₫", "VND", "₫500,000–₫1,000,000"),
    "uae": ("د.إ", "AED", "AED 150–AED 250"),
    "china": ("¥", "CNY", "¥200–¥400"),
    "italy": ("€", "EUR", "€40–€60"),
    "spain": ("€", "EUR", "€40–€60"),
    "default": ("$", "USD", "$50–$100"),
}

# ─── Destination-specific safety context ──────────────────────────────────────
DESTINATION_CONTEXT = {
    "japan": {
        "crime": "Extremely Low",
        "crime_score": 95,
        "tourist_stars": 5,
        "tourist_details": ["English signage at major stations", "Excellent public transport", "Highly foreigner-friendly"],
        "tips": [
            "Use Suica or PASMO IC card for all train and bus travel.",
            "Avoid rush hour (7–9 AM and 5–8 PM) on JR and Tokyo Metro lines.",
            "Last metro trains run around midnight — plan your return accordingly.",
            "Convenience stores (7-Eleven, FamilyMart) are open 24/7 and accept cards.",
            "Carry cash — many smaller restaurants and shops are cash-only.",
            "Use the JR Yamanote Line for easy city-wide transit.",
            "Keep your hotel address in Japanese — show it to taxi drivers.",
            "Women-only train coaches are available on many lines during peak hours.",
        ],
        "avoid_areas": ["Kabukicho late night", "Ueno Park after midnight"],
        "safe_areas": ["Shinjuku (daytime)", "Ginza", "Shibuya (daytime)", "Asakusa"],
        "women_score": 91,
        "solo_score": 94,
        "medical_fact": "Excellent — World-class hospitals with advanced medical care.",
        "medical_tip": "Carry travel insurance — healthcare costs in Japan can be very high for uninsured visitors.",
        "transport_tip": "Use JR Pass for intercity travel. IC card for local metro and buses.",
        "entry": "Visa requirements vary by nationality. Verify at Japan Ministry of Foreign Affairs.",
        "entry_link": "https://www.mofa.go.jp/j_info/visit/visa/",
    },
    "india": {
        "crime": "Moderate",
        "crime_score": 70,
        "tourist_stars": 4,
        "tourist_details": ["Major cities have tourism infrastructure", "English widely spoken", "Rich cultural heritage"],
        "tips": [
            "Use Ola or Uber for safe, metered rides instead of auto-rickshaws at night.",
            "Carry a photocopy of your passport and keep the original in a hotel locker.",
            "Drink only bottled or filtered water — avoid tap water.",
            "Bargain at local markets but use fixed-price stores for electronics.",
            "Keep emergency contacts including hotel number saved offline.",
            "Avoid displaying expensive jewelry or electronics in crowded areas.",
        ],
        "avoid_areas": ["Isolated areas at night", "Crowded markets for pickpockets"],
        "safe_areas": ["MG Road", "Connaught Place", "Marine Drive", "Brigade Road"],
        "women_score": 74,
        "solo_score": 76,
        "medical_fact": "Variable — Good private hospitals in major cities. Rural areas may have limited facilities.",
        "medical_tip": "Comprehensive travel insurance with medical cover is strongly recommended.",
        "transport_tip": "Metro is safe and reliable. Use app-based taxis (Ola/Uber) at night.",
        "entry": "Visa requirements vary by nationality. Many nationalities require an e-Visa.",
        "entry_link": "https://indianvisaonline.gov.in/",
    },
    "france": {
        "crime": "Low–Moderate",
        "crime_score": 78,
        "tourist_stars": 5,
        "tourist_details": ["World's most visited country", "Extensive English support", "Excellent Metro and rail network"],
        "tips": [
            "Beware of pickpockets near the Eiffel Tower, Louvre, and on the Metro.",
            "Keep your bag in front of you in crowded areas.",
            "Most pharmacies (Pharmacie) are marked by a green cross and open on rotation.",
            "The SAMU (15) is the medical emergency number — remember it.",
            "RATP app is the best way to navigate Paris Metro.",
            "Validate your metro ticket every time — inspectors check frequently.",
        ],
        "avoid_areas": ["Barbès-Rochechouart at night", "Gare du Nord surroundings at night"],
        "safe_areas": ["Marais", "Saint-Germain-des-Prés", "Opéra district", "Île de la Cité"],
        "women_score": 82,
        "solo_score": 83,
        "medical_fact": "Excellent — World-class public healthcare system.",
        "medical_tip": "EU nationals can use European Health Insurance Card (EHIC). Non-EU travelers must carry travel insurance.",
        "transport_tip": "Buy Navigo weekly pass for unlimited Metro/Bus/RER travel in Paris.",
        "entry": "Visa requirements vary by nationality. EU/EEA citizens are visa-free. Others may require a Schengen visa.",
        "entry_link": "https://france-visas.gouv.fr/",
    },
    "thailand": {
        "crime": "Low–Moderate",
        "crime_score": 74,
        "tourist_stars": 5,
        "tourist_details": ["One of Asia's top tourist destinations", "Tourist Police available", "Excellent street food culture"],
        "tips": [
            "Only use official metered taxis from the airport — avoid touts.",
            "Avoid Tuk-Tuk rides in Bangkok unless you negotiate the price first.",
            "Dress modestly when visiting temples — shoulders and knees covered.",
            "Do not disrespect the monarchy — it is illegal and taken seriously.",
            "Street food is generally safe — look for busy, high-turnover stalls.",
            "BTS Skytrain and MRT Metro are fast and safe for getting around Bangkok.",
        ],
        "avoid_areas": ["Khao San Road late night", "Pattaya Walking Street"],
        "safe_areas": ["Sukhumvit", "Silom", "Siam area", "Chatuchak Market"],
        "women_score": 78,
        "solo_score": 80,
        "medical_fact": "Good — Several internationally accredited hospitals in Bangkok.",
        "medical_tip": "Bumrungrad and Bangkok Hospital are world-class but costly. Carry travel insurance.",
        "transport_tip": "Use BTS SkyTrain and MRT for safe city travel. Grab app for taxis.",
        "entry": "Visa requirements vary by nationality. Check official Thai immigration for current rules.",
        "entry_link": "https://www.immigration.go.th/",
    },
    "singapore": {
        "crime": "Very Low",
        "crime_score": 96,
        "tourist_stars": 5,
        "tourist_details": ["Exceptionally safe city-state", "English is an official language", "Award-winning public transport"],
        "tips": [
            "Singapore has extremely strict laws — fines for chewing gum, littering, jaywalking.",
            "MRT (Mass Rapid Transit) is the safest and fastest way around the city.",
            "Grab app is the standard ride-hailing service — very reliable.",
            "Tap water is safe to drink directly — among the best quality globally.",
            "Carry an umbrella — afternoon tropical showers are common year-round.",
        ],
        "avoid_areas": [],
        "safe_areas": ["Orchard Road", "Marina Bay", "Sentosa", "Little India"],
        "women_score": 95,
        "solo_score": 97,
        "medical_fact": "World-class public and private hospitals.",
        "medical_tip": "Healthcare is excellent but expensive. Comprehensive travel insurance is essential.",
        "transport_tip": "Use EZ-Link card for MRT and buses. No need for taxis in most areas.",
        "entry": "Visa requirements vary by nationality. Check with ICA Singapore for your passport.",
        "entry_link": "https://www.ica.gov.sg/",
    },
}


# ─── WMO Weather Code Descriptions ───────────────────────────────────────────
WMO_LABELS = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 61: ("Light rain", "🌧️"), 63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"), 71: ("Light snow", "🌨️"), 73: ("Moderate snow", "🌨️"),
    75: ("Heavy snow", "❄️"), 80: ("Rain showers", "🌦️"), 95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm + hail", "⛈️"), 99: ("Severe thunderstorm", "🌩️"),
}


def _haversine_km(lat1, lon1, lat2, lon2):
    """Accurate distance between two lat/lon points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


CITY_ALIASES = {
    # Japan cities
    "tokyo": "japan", "osaka": "japan", "kyoto": "japan", "hiroshima": "japan",
    "sapporo": "japan", "fukuoka": "japan", "yokohama": "japan", "nara": "japan",
    # India cities
    "mumbai": "india", "delhi": "india", "bangalore": "india", "bengaluru": "india",
    "chennai": "india", "kolkata": "india", "hyderabad": "india", "jaipur": "india",
    "goa": "india", "pune": "india", "ahmedabad": "india", "coimbatore": "india",
    "kochi": "india", "mysore": "india", "agra": "india", "varanasi": "india",
    # France cities
    "paris": "france", "lyon": "france", "marseille": "france", "nice": "france",
    "bordeaux": "france", "strasbourg": "france",
    # Germany cities
    "berlin": "germany", "munich": "germany", "frankfurt": "germany",
    "hamburg": "germany", "cologne": "germany",
    # USA cities
    "new york": "usa", "los angeles": "usa", "chicago": "usa", "san francisco": "usa",
    "miami": "usa", "las vegas": "usa", "washington": "usa", "boston": "usa",
    "seattle": "usa", "houston": "usa",
    # UK cities
    "london": "uk", "manchester": "uk", "edinburgh": "uk", "birmingham": "uk",
    "liverpool": "uk", "glasgow": "uk",
    # Australia cities
    "sydney": "australia", "melbourne": "australia", "brisbane": "australia",
    "perth": "australia", "adelaide": "australia",
    # Singapore
    "singapore": "singapore",
    # Thailand cities
    "bangkok": "thailand", "phuket": "thailand", "chiang mai": "thailand",
    "pattaya": "thailand", "koh samui": "thailand",
    # Malaysia cities
    "kuala lumpur": "malaysia", "penang": "malaysia", "johor": "malaysia",
    # Indonesia cities
    "bali": "indonesia", "jakarta": "indonesia", "yogyakarta": "indonesia",
    # Vietnam cities
    "hanoi": "vietnam", "ho chi minh": "vietnam", "saigon": "vietnam", "danang": "vietnam",
    # UAE cities
    "dubai": "uae", "abu dhabi": "uae", "sharjah": "uae",
}


def _get_dest_context(destination: str) -> Dict:

    """Return destination-specific context data, falling back to generic."""
    dest_lower = destination.lower()
    # 1. Check city aliases first (most specific)
    for city, ctx_key in CITY_ALIASES.items():
        if city in dest_lower:
            if ctx_key in DESTINATION_CONTEXT:
                return DESTINATION_CONTEXT[ctx_key]
    # 2. Direct country keyword match
    for key, ctx in DESTINATION_CONTEXT.items():
        if key in dest_lower:
            return ctx
    return {
        "crime": "Moderate", "crime_score": 72,
        "tips": [], "avoid_areas": [], "safe_areas": [],
        "women_score": 78, "solo_score": 80,
        "medical": "Carry travel insurance. Locate the nearest hospital on arrival.",
        "transport_tip": "Use verified, licensed transport providers.",
        "entry": "Check your country's official travel advisory for entry requirements.",
    }


def _get_currency(country_name: str):
    """Return (symbol, code, emergency_cash_range) for a country."""
    key = country_name.lower().strip()
    if key in COUNTRY_CURRENCY:
        return COUNTRY_CURRENCY[key]
    for k, v in COUNTRY_CURRENCY.items():
        if k in key or key in k:
            return v
    return COUNTRY_CURRENCY["default"]


class SafetyHubService:
    """Production service powering WanderWise v2.0 Safety Hub."""

    @staticmethod
    def geocode(location: str) -> Dict[str, Any]:
        """Resolve coordinates via nominatim_service provider chain."""
        logger.info(f"[SAFETY] Requested location: {location}")
        from app.services.maps.nominatim_service import geocode_place

        geo_res = geocode_place(location)
        if not geo_res or not geo_res.get("is_valid", True) or geo_res.get("lat") is None or geo_res.get("lon") is None:
            logger.error(f"[SAFETY] Geocoding failed for location: {location}")
            return {
                "is_valid": False,
                "lat": None,
                "lon": None,
                "latitude": None,
                "longitude": None,
                "city": location,
                "country": "Unknown",
                "country_code": "unknown",
                "display": location,
                "display_name": location,
                "error": f"Unable to resolve destination '{location}'"
            }

        lat = float(geo_res["lat"])
        lon = float(geo_res["lon"])
        display = geo_res.get("display_name", location)
        cc = (geo_res.get("country_code") or "in").lower()

        logger.info(f"[SAFETY] Resolved location: {display}")
        logger.info(f"[SAFETY] Resolved coordinates: {lat}, {lon}")

        CC_MAP = {
            "jp": "Japan", "in": "India", "fr": "France", "de": "Germany",
            "us": "USA", "gb": "UK", "au": "Australia", "ca": "Canada",
            "sg": "Singapore", "th": "Thailand", "my": "Malaysia",
            "id": "Indonesia", "vn": "Vietnam", "ae": "UAE",
            "lk": "Sri Lanka", "np": "Nepal", "cn": "China",
            "it": "Italy", "es": "Spain", "kr": "South Korea",
        }

        parts = [p.strip() for p in display.split(",")]
        city = parts[0] if parts else location

        return {
            "is_valid": True,
            "lat": lat,
            "lon": lon,
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "country": CC_MAP.get(cc, parts[-1] if len(parts) > 1 else "India"),
            "country_code": cc,
            "display": display,
            "display_name": display,
        }

    @staticmethod
    def get_live_weather(lat: float, lon: float) -> Dict[str, Any]:
        """Fetch live weather from Open-Meteo with safety-relevant fields."""
        result = {
            "temperature": 28.0, "feels_like": 30.0, "humidity": 65,
            "weather_code": 0, "description": "Clear sky", "icon": "☀️",
            "wind_speed": 12.0, "rain_probability": 10, "uv_index": 5.0,
            "visibility": 10.0, "warnings": [], "air_quality": "Good",
        }
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"weather_code,wind_speed_10m,precipitation_probability,uv_index,visibility"
                f"&hourly=precipitation_probability,temperature_2m,weather_code"
                f"&forecast_days=1&timezone=auto"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "WanderWise/7.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
                cur = data.get("current", {})
                code = cur.get("weather_code", 0)
                label, icon = WMO_LABELS.get(code, ("Unknown", "🌡️"))
                uv = float(cur.get("uv_index", 0) or 0)
                rain_prob = int(cur.get("precipitation_probability", 0) or 0)
                wind = float(cur.get("wind_speed_10m", 0) or 0)
                vis = float(cur.get("visibility", 10000) or 10000)
                temp = round(float(cur.get("temperature_2m", 28) or 28), 1)

                # Air quality estimation from humidity + temp
                humidity = int(cur.get("relative_humidity_2m", 65) or 65)
                if humidity > 85 and temp > 30:
                    aq = "Moderate"
                elif code in [45, 48]:
                    aq = "Poor"
                else:
                    aq = "Good"

                # Build hourly forecast mini-data for timeline
                hourly = data.get("hourly", {})
                hourly_rain = hourly.get("precipitation_probability", [])
                hourly_temps = hourly.get("temperature_2m", [])
                hourly_codes = hourly.get("weather_code", [])

                result.update({
                    "temperature": temp,
                    "feels_like": round(float(cur.get("apparent_temperature", 30) or 30), 1),
                    "humidity": humidity,
                    "weather_code": code,
                    "description": label,
                    "icon": icon,
                    "wind_speed": round(wind, 1),
                    "rain_probability": rain_prob,
                    "uv_index": round(uv, 1),
                    "visibility": round(vis / 1000, 1),
                    "air_quality": aq,
                    "hourly_rain": hourly_rain[:24],
                    "hourly_temps": hourly_temps[:24],
                    "hourly_codes": hourly_codes[:24],
                })

                # Contextual warnings
                warnings = []
                if rain_prob >= 60:
                    warnings.append({"level": "moderate", "message": f"High rain probability ({rain_prob}%). Carry rain gear.", "icon": "🌧️"})
                if wind > 50:
                    warnings.append({"level": "high", "message": f"Strong winds at {round(wind)} km/h. Avoid exposed outdoor areas.", "icon": "💨"})
                if uv >= 8:
                    warnings.append({"level": "moderate", "message": f"Very high UV index ({round(uv)}). Use SPF 50+ sunscreen and seek shade.", "icon": "☀️"})
                if vis < 2:
                    warnings.append({"level": "high", "message": f"Low visibility ({round(vis * 1000)}m). Drive with extra caution.", "icon": "🌫️"})
                if code in [95, 96, 99]:
                    warnings.append({"level": "high", "message": "Thunderstorm active. Seek indoor shelter immediately.", "icon": "⛈️"})
                if temp >= 40:
                    warnings.append({"level": "high", "message": f"Extreme heat ({temp}°C). Stay hydrated and avoid midday sun.", "icon": "🔥"})
                result["warnings"] = warnings
        except Exception:
            pass
        return result

    @staticmethod
    def get_nearby_services(lat: float, lon: float) -> Dict[str, List]:
        """Fetch real emergency POIs using Overpass API centered around lat, lon."""
        services = {
            "hospitals": [], "police": [], "pharmacies": [],
            "fire_stations": [], "atms": [], "metro_stations": [],
            "bus_stops": [], "fuel_stations": [],
        }

        if lat is None or lon is None:
            logger.error("[SAFETY] get_nearby_services called with null coordinates")
            return services

        # Cache key unique to coordinates
        cache_key = f"nearby_services:{lat:.4f}:{lon:.4f}"
        try:
            from app.services.cache.transit_cache import TransitCache
            cached = TransitCache.get(cache_key)
            if cached:
                logger.info(f"[SAFETY] Returning cached nearby services for {lat:.4f}, {lon:.4f}")
                return cached
        except Exception:
            pass

        logger.info(f"[SAFETY] Nearby services center: {lat}, {lon}")

        overpass_queries = {
            "hospitals":      f"[out:json][timeout:10];(node[amenity=hospital](around:3000,{lat},{lon});way[amenity=hospital](around:3000,{lat},{lon}););out center 5;",
            "police":         f"[out:json][timeout:8];node[amenity=police](around:3000,{lat},{lon});out 5;",
            "pharmacies":     f"[out:json][timeout:8];node[amenity=pharmacy](around:2000,{lat},{lon});out 6;",
            "fire_stations":  f"[out:json][timeout:8];node[amenity=fire_station](around:5000,{lat},{lon});out 3;",
            "atms":           f"[out:json][timeout:8];node[amenity=atm](around:1500,{lat},{lon});out 6;",
            "metro_stations": f"[out:json][timeout:8];node[station=subway](around:2000,{lat},{lon});out 5;",
            "bus_stops":      f"[out:json][timeout:8];node[highway=bus_stop](around:800,{lat},{lon});out 6;",
            "fuel_stations":  f"[out:json][timeout:8];node[amenity=fuel](around:3000,{lat},{lon});out 4;",
        }

        total_received = 0
        total_rejected = 0

        for key, query in overpass_queries.items():
            try:
                url = "https://overpass-api.de/api/interpreter"
                data_enc = urllib.parse.urlencode({"data": query}).encode()
                req = urllib.request.Request(url, data=data_enc, headers={"User-Agent": "WanderWise/7.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    result = json.loads(resp.read())
                    elements = result.get("elements", [])
                    total_received += len(elements)
                    for el in elements[:6]:
                        tags = el.get("tags", {})
                        name = (tags.get("name:en") or tags.get("name") or
                                f"Unnamed {key.replace('_', ' ').title()}")
                        # Handle way elements (center lat/lon)
                        if el.get("type") == "way":
                            elat = el.get("center", {}).get("lat", lat)
                            elon = el.get("center", {}).get("lon", lon)
                        else:
                            elat, elon = el.get("lat", lat), el.get("lon", lon)

                        dist_km = _haversine_km(lat, lon, elat, elon)

                        # Location consistency validation: reject POIs > 50km away from center
                        if dist_km > 50.0:
                            total_rejected += 1
                            logger.warning(f"[SAFETY] POI rejected by distance validation (>50km): '{name}' ({dist_km} km away from {lat},{lon})")
                            continue

                        walk_min = max(1, round(dist_km / 0.08))  # ~80m/min walking speed

                        services[key].append({
                            "name": name,
                            "lat": elat,
                            "lon": elon,
                            "distance_km": dist_km,
                            "walk_min": walk_min,
                            "phone": tags.get("phone") or tags.get("contact:phone") or "",
                            "opening_hours": tags.get("opening_hours") or "",
                            "website": tags.get("website") or "",
                            "operator": tags.get("operator") or "",
                        })
                    # Sort by distance
                    services[key].sort(key=lambda x: x["distance_km"])
            except Exception as e:
                logger.error(f"[SAFETY] Error fetching {key} for {lat},{lon}: {e}")

        total_returned = sum(len(v) for v in services.values())
        logger.info(f"[SAFETY] Overpass results received: {total_received}")
        logger.info(f"[SAFETY] POIs rejected by distance validation: {total_rejected}")
        logger.info(f"[SAFETY] Nearby services returned: {total_returned}")

        try:
            from app.services.cache.transit_cache import TransitCache
            TransitCache.set(cache_key, services)
        except Exception:
            pass

        return services

    @staticmethod
    def get_emergency_contacts(country_name: str) -> Dict[str, str]:
        """Return country-specific emergency numbers from verified dataset."""
        key = country_name.lower().strip()
        if key in COUNTRY_EMERGENCY:
            return COUNTRY_EMERGENCY[key]
        for k, v in COUNTRY_EMERGENCY.items():
            if k in key or key in k:
                return v
        return COUNTRY_EMERGENCY["default"]

    @staticmethod
    def compute_safety_timeline(weather: Dict) -> List[Dict]:
        """Generate 12-slot safety timeline with unique, varied, realistic events."""
        from datetime import datetime, timedelta
        now = datetime.now()
        rain_list = weather.get("hourly_rain", [])
        temp_list = weather.get("hourly_temps", [])
        code_list = weather.get("hourly_codes", [])
        base_uv = weather.get("uv_index", 5)

        current_hour = now.hour

        # Events attached to specific hours of day
        HOUR_EVENTS = {
            0:  ("🌙 Midnight", "low",      "Very quiet. Last metro may have ended."),
            1:  ("🌑 1 AM",     "low",      "Minimal activity. Use ride-hailing apps."),
            2:  ("🌑 2 AM",     "low",      "Limited transport. Plan ahead for late nights."),
            3:  ("🌑 3 AM",     "low",      "Quietest hours. 24-hr pharmacies available."),
            4:  ("🌅 4 AM",     "low",      "Pre-dawn. Early market workers begin."),
            5:  ("🌅 5 AM",     "low",      "First metro/bus services resume."),
            6:  ("🌅 6 AM",     "low",      "Public transport resumes. Morning walkers active."),
            7:  ("🚇 7 AM",     "moderate", "Rush hour begins. Expect crowded trains."),
            8:  ("🚇 8 AM",     "moderate", "Peak rush hour. Allow extra travel time."),
            9:  ("🏙 9 AM",     "low",      "Rush hour easing. Tourist sites open."),
            10: ("🏙 10 AM",    "low",      "Good time for sightseeing. Shops open."),
            11: ("☀️ 11 AM",   "low",      "Active tourist hours. UV starting to rise."),
            12: ("☀️ Noon",    "moderate", "Peak UV. Seek shade. Stay hydrated."),
            13: ("🌞 1 PM",    "low",      "Lunch hours. Popular restaurants crowded."),
            14: ("🌞 2 PM",    "low",      "Afternoon. Good for indoor attractions."),
            15: ("🌦 3 PM",    "moderate", "Possible afternoon showers in tropical areas."),
            16: ("🌧 4 PM",    "moderate", "Rain likely in many regions. Monitor weather."),
            17: ("🚇 5 PM",    "moderate", "Evening rush begins. Allow extra time."),
            18: ("🚇 6 PM",    "moderate", "Peak evening rush. Very crowded transport."),
            19: ("🌆 7 PM",    "low",      "Rush hour ending. Good time for dinner."),
            20: ("🌆 8 PM",    "moderate", "Heavy crowd around major stations & markets."),
            21: ("🌃 9 PM",    "low",      "Night life starts. Use licensed transport."),
            22: ("🌃 10 PM",   "moderate", "Crowds reducing. Late-night travel — stay alert."),
            23: ("🌙 11 PM",   "moderate", "Check last metro/bus time. Limited services."),
        }

        slots = []
        for i in range(8):
            hour_offset = i * 1 + (0 if i == 0 else i)
            target_hour = (current_hour + hour_offset) % 24
            h_rain = rain_list[target_hour] if target_hour < len(rain_list) else weather.get("rain_probability", 10)
            h_code = code_list[target_hour] if target_hour < len(code_list) else weather.get("weather_code", 0)
            h_temp = round(temp_list[target_hour], 1) if target_hour < len(temp_list) else weather.get("temperature", 28)

            event_label, event_risk, event_tip = HOUR_EVENTS.get(target_hour, ("🌐", "low", "Safe"))

            # Override with real weather data if significant
            if h_code in [95, 96, 99]:
                event_label, event_risk, event_tip = "⛈️ Thunderstorm", "high", "Stay indoors! Thunderstorm active."
            elif h_rain >= 70:
                event_risk = "high"
                event_tip = f"Heavy rain likely ({h_rain}%). Carry rain gear."
            elif h_rain >= 50:
                event_risk = "moderate"
                event_tip = f"Rain possible ({h_rain}%). Keep umbrella ready."

            future_time = now + timedelta(hours=hour_offset)
            slots.append({
                "time": future_time.strftime("%I:%M %p"),
                "label": event_label,
                "risk": event_risk,
                "tip": event_tip,
                "temperature": h_temp,
                "rain": h_rain,
            })
        return slots

    @staticmethod
    def build_safety_dashboard(destination: str, weather: Dict, country: str) -> Dict:
        """Compute a realistic safety score with factors and reasons."""
        rain = weather.get("rain_probability", 0)
        wind = weather.get("wind_speed", 0)
        uv = weather.get("uv_index", 0)
        code = weather.get("weather_code", 0)
        warnings = weather.get("warnings", [])
        temp = weather.get("temperature", 28)
        # Use destination string for context (more reliable than geocoded country name)
        ctx = _get_dest_context(destination + " " + country)

        # --- Factor decomposition ---
        factors = []
        deductions = 0

        # Crime
        crime_score = ctx.get("crime_score", 72)
        crime_label = ctx.get("crime", "Moderate")
        factors.append({"label": "Crime Level", "status": crime_label,
                         "icon": "✅" if crime_score >= 85 else "⚠️" if crime_score >= 70 else "❌",
                         "positive": crime_score >= 75})
        if crime_score < 70:
            deductions += 12
        elif crime_score < 80:
            deductions += 5

        # Weather
        if code in [95, 96, 99]:
            factors.append({"label": "Weather", "status": "Severe storm — stay indoors", "icon": "❌", "positive": False})
            deductions += 20
        elif rain >= 60:
            factors.append({"label": "Weather", "status": f"Rain likely ({rain}%)", "icon": "⚠️", "positive": False})
            deductions += 8
        elif temp >= 40:
            factors.append({"label": "Weather", "status": f"Extreme heat ({temp}°C)", "icon": "⚠️", "positive": False})
            deductions += 6
        else:
            factors.append({"label": "Weather", "status": weather.get("description", "Clear"), "icon": "✅", "positive": True})

        # Medical — fact separated from advice
        medical_fact = ctx.get("medical_fact", ctx.get("medical", "Healthcare available."))
        # Truncate at first sentence for the factor card
        medical_short = medical_fact.split(".")[0] + "." if "." in medical_fact else medical_fact
        medical_tip = ctx.get("medical_tip", "Carry comprehensive travel insurance before departure.")
        factors.append({"label": "Medical Facilities", "status": medical_short,
                        "tip": medical_tip, "icon": "✅", "positive": True})

        # UV
        if uv >= 8:
            factors.append({"label": "UV Index", "status": f"Very High ({round(uv)})", "icon": "⚠️", "positive": False})
            deductions += 4
        else:
            factors.append({"label": "UV Index", "status": f"Manageable ({round(uv)})", "icon": "✅", "positive": True})

        # Tourist Infrastructure — star rating
        t_stars = ctx.get("tourist_stars", 4)
        t_details = ctx.get("tourist_details", ["Tourist infrastructure available"])
        star_str = "★" * t_stars + "☆" * (5 - t_stars)
        factors.append({"label": "Tourist Friendly", "status": star_str,
                        "sub_details": t_details, "icon": "✅", "positive": True})

        # Warnings penalty
        deductions += len([w for w in warnings if w["level"] == "high"]) * 5

        # Compute score — never 100 (or below 35)
        base = 88 + (crime_score - 72) // 5
        overall = max(35, min(95, base - deductions))

        risk_label = "Low" if overall >= 78 else "Moderate" if overall >= 55 else "High"
        travel_status = "Safe to Travel" if overall >= 78 else "Caution Advised" if overall >= 55 else "Risk — Monitor Closely"

        # Women & Solo scores
        women_score = max(35, min(95, ctx.get("women_score", 78) - (deductions // 2)))
        solo_score = max(35, min(95, ctx.get("solo_score", 80) - (deductions // 2)))

        # Score breakdown sub-scores (out of 30/20/20/20/10 = 100)
        crime_sub = max(5, min(30, int(crime_score * 0.30)))
        weather_sub = max(3, min(20, 20 - int(min(100, rain * 0.3 + (30 if code in [95, 96, 99] else 0)) / 5)))
        medical_sub = 20 if crime_score >= 80 else 16 if crime_score >= 65 else 12
        transport_sub = 20 if t_stars >= 5 else 16 if t_stars >= 4 else 12
        tourist_sub = min(10, t_stars * 2)
        score_breakdown = [
            {"label": "Crime & Safety", "score": crime_sub, "max": 30},
            {"label": "Weather",         "score": weather_sub, "max": 20},
            {"label": "Medical",         "score": medical_sub, "max": 20},
            {"label": "Transport",       "score": transport_sub, "max": 20},
            {"label": "Tourist Friendly","score": tourist_sub, "max": 10},
        ]

        # Travel alerts — proactive banners
        alerts = []
        if code in [95, 96, 99]:
            alerts.append({"level": "high", "icon": "⛈️",
                           "message": "Thunderstorm active. Stay indoors. Avoid open areas and high ground."})
        if rain >= 70:
            alerts.append({"level": "moderate", "icon": "🌧️",
                           "message": f"Heavy rain expected ({rain}% probability). Carry umbrella. Metro recommended over walking."})
        elif rain >= 50:
            alerts.append({"level": "low", "icon": "🌦️",
                           "message": f"Rain possible ({rain}%). Keep a compact umbrella handy."})
        if temp >= 38:
            alerts.append({"level": "high", "icon": "🔥",
                           "message": f"Extreme heat ({temp}°C). Avoid outdoor activity 12 PM–3 PM. Stay hydrated."})
        elif temp >= 33:
            alerts.append({"level": "moderate", "icon": "☀️",
                           "message": f"High heat ({temp}°C). Avoid midday sun. Use sunscreen and carry water."})
        if uv >= 8:
            alerts.append({"level": "moderate", "icon": "🕶️",
                           "message": f"UV Index is Very High ({round(uv)}). Apply SPF 50+, wear hat and sunglasses."})

        return {
            "overall_score": overall,
            "risk_label": risk_label,
            "travel_status": travel_status,
            "weather_risk": min(100, int(rain * 0.4 + (40 if code in [95, 96, 99] else 0))),
            "health_advisory": "Normal — No active health alerts",
            "crime_awareness": crime_label,
            "emergency_readiness": "Available" if overall >= 55 else "Limited",
            "women_score": women_score,
            "solo_score": solo_score,
            "factors": factors,
            "score_breakdown": score_breakdown,
            "travel_alerts": alerts,
            "entry_info": ctx.get("entry", "Visa requirements vary by nationality. Verify with official immigration sources."),
            "entry_link": ctx.get("entry_link", ""),
            "transport_tip": ctx.get("transport_tip", "Use licensed transport providers."),
            "safe_areas": ctx.get("safe_areas", []),
            "avoid_areas": ctx.get("avoid_areas", []),
            "medical_fact": medical_short,
            "medical_tip": medical_tip,
            "tourist_stars": t_stars,
            "tourist_details": t_details,
        }

    @staticmethod
    def generate_ai_safety_tips(destination: str, weather: Dict, country: str) -> List[str]:
        """Generate destination-specific, currency-aware safety tips."""
        ctx = _get_dest_context(destination)
        sym, code_c, cash_range = _get_currency(country)

        # Start with destination-specific tips from context
        tips = list(ctx.get("tips", []))

        # Always-on contextual tips
        generic = [
            f"Always carry a printed copy of your hotel address in {destination.split(',')[0]}.",
            "Keep emergency contacts saved offline on your phone.",
            "Download offline maps before you need them — Wi-Fi isn't always available.",
            "Share your live itinerary with at least one trusted contact at home.",
            f"Keep {cash_range} ({code_c}) in emergency cash — not all places accept cards.",
            "Carry a photocopy of your passport. Keep the original in a hotel safe.",
        ]
        tips.extend(generic)

        # Live weather-based tips (priority inserts)
        rain = weather.get("rain_probability", 0)
        wind = weather.get("wind_speed", 0)
        uv = weather.get("uv_index", 0)
        code = weather.get("weather_code", 0)

        if code in [95, 96, 99]:
            tips.insert(0, "⛈️ Thunderstorm active. Stay indoors and avoid open areas.")
        if rain >= 50:
            tips.insert(0, f"🌧️ Rain probability is {rain}%. Carry a compact umbrella today.")
        if wind > 40:
            tips.insert(0, f"💨 Wind speed is {round(wind)} km/h. Secure loose items.")
        if uv >= 8:
            tips.insert(0, f"☀️ UV index is {round(uv)} (Very High). Apply SPF 50+ sunscreen and wear a hat.")

        # De-duplicate while preserving order
        seen, unique = set(), []
        for t in tips:
            if t not in seen:
                seen.add(t)
                unique.append(t)

        return unique[:10]

    @staticmethod
    def get_health_advisory(lat: float, lon: float, country: str) -> Dict:
        """Compute health advisory from weather data."""
        weather_result = SafetyHubService.get_live_weather(lat, lon)
        temp = weather_result.get("temperature", 28)
        humidity = weather_result.get("humidity", 65)
        uv = weather_result.get("uv_index", 5)
        code = weather_result.get("weather_code", 0)

        # Heat index estimation
        if temp >= 27 and humidity >= 40:
            hi = temp + 0.33 * (humidity / 100 * 6.105 * math.exp(17.27 * temp / (237.7 + temp))) - 4.00
            heat_label = "Extreme" if hi > 54 else "Very Hot" if hi > 40 else "Hot" if hi > 32 else "Comfortable"
        else:
            hi = temp
            heat_label = "Cold" if temp < 10 else "Cool" if temp < 18 else "Comfortable"

        # AQI estimation (simple proxy from humidity + code)
        if code in [45, 48]:
            aqi, aqi_label = 150, "Unhealthy"
        elif humidity > 85 and temp > 30:
            aqi, aqi_label = 80, "Moderate"
        else:
            aqi, aqi_label = 40, "Good"

        return {
            "heat_index": round(hi, 1),
            "heat_label": heat_label,
            "aqi": aqi,
            "aqi_label": aqi_label,
            "pollen": "Low" if code in [61, 63, 65, 80] else "Moderate",
            "mosquito_risk": "High" if (temp > 25 and humidity > 70) else "Low",
            "water_safety": "Safe (bottled water recommended)" if country.lower() in ["india", "thailand", "vietnam", "indonesia", "nepal"] else "Tap water generally safe",
            "vaccination_note": "Consult your doctor for destination-specific vaccines 4–6 weeks before travel.",
            "sun_protection": "SPF 50+ required" if uv >= 8 else "SPF 30 recommended" if uv >= 5 else "Minimal risk",
        }
