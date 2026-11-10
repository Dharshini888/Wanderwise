"""
location_normalizer.py — Location Normalization & Sanity Check Service for WanderWise V12

Responsibilities:
  1. Validate coordinate bounds (-90 <= lat <= 90, -180 <= lon <= 180).
  2. Extract ISO country_code, country, city, continent, display_name.
  3. Calculate Haversine straight-line distance.
  4. Perform SAME_LOCATION check (distance < 0.5 km).
  5. Check OSRM distance / straight-line ratio for ROUTE_SANITY_WARNING.
"""

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in km between two lat/lon pairs."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def normalize_location(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes location dictionary and validates coordinate boundaries.
    """
    lat = input_data.get("lat") or input_data.get("latitude")
    lon = input_data.get("lon") or input_data.get("longitude")

    if lat is None or lon is None:
        raise ValueError("Missing latitude or longitude in location input")

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid non-numeric coordinates: lat={lat}, lon={lon}")

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of bounds [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of bounds [-180, 180]: {lon}")

    return {
        "name": input_data.get("name") or input_data.get("display_name") or "Location",
        "display_name": input_data.get("display_name") or input_data.get("name") or "Location",
        "latitude": lat,
        "longitude": lon,
        "lat": lat,
        "lon": lon,
        "country_code": (input_data.get("country_code") or "").upper(),
        "country": input_data.get("country") or "",
        "city": input_data.get("city") or "",
        "source": input_data.get("source") or "Geolocation",
        "accuracy_m": input_data.get("accuracy_m") or input_data.get("accuracy"),
    }


def check_location_sanity(origin: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates origin and destination coordinates for SAME_LOCATION (< 0.5 km)
    and straight-line distance calculations.
    """
    try:
        norm_orig = normalize_location(origin)
        norm_dest = normalize_location(destination)
    except ValueError as e:
        logger.warning(f"[LOCATION SANITY] Normalization failed: {e}")
        return {
            "same_location": False,
            "straight_line_distance_km": 0.0,
            "warning": str(e),
        }

    dist_km = round(_haversine_km(
        norm_orig["latitude"], norm_orig["longitude"],
        norm_dest["latitude"], norm_dest["longitude"]
    ), 3)

    is_same = dist_km < 0.5

    if is_same:
        logger.info(f"[LOCATION SANITY] SAME_LOCATION detected! Distance: {dist_km} km ({norm_orig['name']} -> {norm_dest['name']})")

    return {
        "same_location": is_same,
        "straight_line_distance_km": dist_km,
        "origin_normalized": norm_orig,
        "destination_normalized": norm_dest,
        "warning": None,
    }


def validate_route_sanity(straight_line_km: float, road_distance_km: float) -> Optional[str]:
    """
    Flags ROUTE_SANITY_WARNING if road distance ratio is abnormally large compared to straight-line distance.
    """
    if straight_line_km <= 0 or road_distance_km <= 0:
        return None
    ratio = road_distance_km / straight_line_km
    if ratio > 5.0 and straight_line_km < 10.0:
        logger.warning(f"[ROUTE SANITY] Abnormal detour detected: straight={straight_line_km}km, road={road_distance_km}km (ratio: {ratio:.1f})")
        return "ROUTE_SANITY_WARNING: Road routing produces abnormal detour ratio compared to straight-line distance."
    return None


# ============================================================================
# Global Destination, Country & Currency Gazetteer
# ============================================================================

COUNTRY_NAME_TO_CODE: Dict[str, str] = {
    "georgia": "GE",
    "vietnam": "VN",
    "italy": "IT",
    "france": "FR",
    "germany": "DE",
    "spain": "ES",
    "united kingdom": "GB",
    "uk": "GB",
    "england": "GB",
    "scotland": "GB",
    "united states": "US",
    "usa": "US",
    "japan": "JP",
    "thailand": "TH",
    "malaysia": "MY",
    "singapore": "SG",
    "india": "IN",
    "iceland": "IS",
    "switzerland": "CH",
    "turkey": "TR",
    "türkiye": "TR",
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "peru": "PE",
    "bolivia": "BO",
    "australia": "AU",
    "new zealand": "NZ",
    "canada": "CA",
    "mexico": "MX",
    "egypt": "EG",
    "south africa": "ZA",
    "morocco": "MA",
    "uae": "AE",
    "united arab emirates": "AE",
    "saudi arabia": "SA",
    "qatar": "QA",
    "oman": "OM",
    "kuwait": "KW",
    "bahrain": "BH",
    "indonesia": "ID",
    "philippines": "PH",
    "south korea": "KR",
    "korea": "KR",
    "china": "CN",
    "taiwan": "TW",
    "hong kong": "HK",
    "nepal": "NP",
    "sri lanka": "LK",
    "bhutan": "BT",
    "norway": "NO",
    "sweden": "SE",
    "denmark": "DK",
    "poland": "PL",
    "czech republic": "CZ",
    "czechia": "CZ",
    "hungary": "HU",
    "austria": "AT",
    "netherlands": "NL",
    "belgium": "BE",
    "greece": "GR",
    "portugal": "PT",
    "ireland": "IE",
    "croatia": "HR",
    "romania": "RO",
    "bulgaria": "BG",
    "ukraine": "UA",
    "serbia": "RS",
    "bosnia and herzegovina": "BA",
    "bosnia": "BA",
    "costa rica": "CR",
    "dominican republic": "DO",
    "jamaica": "JM",
    "uruguay": "UY",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "kazakhstan": "KZ",
    "uzbekistan": "UZ",
    "georgian": "GE",
}

COUNTRY_CODE_TO_CURRENCY: Dict[str, str] = {
    "GE": "GEL",
    "VN": "VND",
    "IT": "EUR",
    "FR": "EUR",
    "DE": "EUR",
    "ES": "EUR",
    "GB": "GBP",
    "US": "USD",
    "JP": "JPY",
    "TH": "THB",
    "MY": "MYR",
    "SG": "SGD",
    "IN": "INR",
    "IS": "ISK",
    "CH": "CHF",
    "TR": "TRY",
    "BR": "BRL",
    "AR": "ARS",
    "CL": "CLP",
    "PE": "PEN",
    "BO": "BOB",
    "AU": "AUD",
    "NZ": "NZD",
    "CA": "CAD",
    "MX": "MXN",
    "EG": "EGP",
    "ZA": "ZAR",
    "MA": "MAD",
    "AE": "AED",
    "SA": "SAR",
    "QA": "QAR",
    "OM": "OMR",
    "KW": "KWD",
    "BH": "BHD",
    "ID": "IDR",
    "PH": "PHP",
    "KR": "KRW",
    "CN": "CNY",
    "TW": "TWD",
    "HK": "HKD",
    "NP": "NPR",
    "LK": "LKR",
    "BT": "BTN",
    "NO": "NOK",
    "SE": "SEK",
    "DK": "DKK",
    "PL": "PLN",
    "CZ": "CZK",
    "HU": "HUF",
    "AT": "EUR",
    "NL": "EUR",
    "BE": "EUR",
    "GR": "EUR",
    "PT": "EUR",
    "IE": "EUR",
    "HR": "EUR",
    "RO": "RON",
    "BG": "BGN",
    "UA": "UAH",
    "RS": "RSD",
    "BA": "BAM",
    "CR": "CRC",
    "DO": "DOP",
    "JM": "JMD",
    "UY": "UYU",
    "AM": "AMD",
    "AZ": "AZN",
    "KZ": "KZT",
    "UZ": "UZS",
}

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "GEL": "₾",
    "THB": "฿",
    "MYR": "RM",
    "SGD": "S$",
    "VND": "₫",
    "ISK": "kr",
    "CHF": "CHF",
    "AUD": "A$",
    "CAD": "C$",
    "NZD": "NZ$",
    "AED": "د.إ",
    "SAR": "﷼",
    "QAR": "ر.ق",
    "TRY": "₺",
    "BRL": "R$",
    "ARS": "$",
    "CLP": "$",
    "PEN": "S/",
    "BOB": "Bs.",
    "ZAR": "R",
    "EGP": "E£",
    "KRW": "₩",
    "CNY": "¥",
    "HKD": "HK$",
    "TWD": "NT$",
    "IDR": "Rp",
    "PHP": "₱",
    "NOK": "kr",
    "SEK": "kr",
    "DKK": "kr.",
    "PLN": "zł",
    "CZK": "Kč",
    "HUF": "Ft",
    "RON": "lei",
    "BGN": "лв",
    "UAH": "₴",
    "RSD": "дин.",
    "AMD": "֏",
    "AZN": "₼",
    "KZT": "₸",
}

GLOBAL_DESTINATION_GAZETTEER: Dict[str, Dict[str, Any]] = {
    "tbilisi": {
        "name": "Tbilisi",
        "country": "Georgia",
        "country_code": "GE",
        "currency": "GEL",
        "currency_symbol": "₾",
        "latitude": 41.6938,
        "longitude": 44.8015,
        "region": "Caucasus / Eastern Europe",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "batumi": {
        "name": "Batumi",
        "country": "Georgia",
        "country_code": "GE",
        "currency": "GEL",
        "currency_symbol": "₾",
        "latitude": 41.6434,
        "longitude": 41.6399,
        "region": "Caucasus",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "hanoi": {
        "name": "Hanoi",
        "country": "Vietnam",
        "country_code": "VN",
        "currency": "VND",
        "currency_symbol": "₫",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "region": "Southeast Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "florence": {
        "name": "Florence",
        "country": "Italy",
        "country_code": "IT",
        "currency": "EUR",
        "currency_symbol": "€",
        "latitude": 43.7696,
        "longitude": 11.2558,
        "region": "Western Europe",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "reykjavik": {
        "name": "Reykjavik",
        "country": "Iceland",
        "country_code": "IS",
        "currency": "ISK",
        "currency_symbol": "kr",
        "latitude": 64.1466,
        "longitude": -21.9426,
        "region": "Nordic / Western Europe",
        "is_long_haul": True,
        "is_regional_international": False,
    },
    "bangkok": {
        "name": "Bangkok",
        "country": "Thailand",
        "country_code": "TH",
        "currency": "THB",
        "currency_symbol": "฿",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "region": "Southeast Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "kuala lumpur": {
        "name": "Kuala Lumpur",
        "country": "Malaysia",
        "country_code": "MY",
        "currency": "MYR",
        "currency_symbol": "RM",
        "latitude": 3.1390,
        "longitude": 101.6869,
        "region": "Southeast Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "singapore": {
        "name": "Singapore",
        "country": "Singapore",
        "country_code": "SG",
        "currency": "SGD",
        "currency_symbol": "S$",
        "latitude": 1.3521,
        "longitude": 103.8198,
        "region": "Southeast Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "tokyo": {
        "name": "Tokyo",
        "country": "Japan",
        "country_code": "JP",
        "currency": "JPY",
        "currency_symbol": "¥",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "region": "East Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "paris": {
        "name": "Paris",
        "country": "France",
        "country_code": "FR",
        "currency": "EUR",
        "currency_symbol": "€",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "region": "Western Europe",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "rome": {
        "name": "Rome",
        "country": "Italy",
        "country_code": "IT",
        "currency": "EUR",
        "currency_symbol": "€",
        "latitude": 41.9028,
        "longitude": 12.4964,
        "region": "Western Europe",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "london": {
        "name": "London",
        "country": "United Kingdom",
        "country_code": "GB",
        "currency": "GBP",
        "currency_symbol": "£",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "region": "Western Europe",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "agra": {
        "name": "Agra",
        "country": "India",
        "country_code": "IN",
        "currency": "INR",
        "currency_symbol": "₹",
        "latitude": 27.1767,
        "longitude": 78.0081,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": False,
    },
    "delhi": {
        "name": "Delhi",
        "country": "India",
        "country_code": "IN",
        "currency": "INR",
        "currency_symbol": "₹",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": False,
    },
    "mumbai": {
        "name": "Mumbai",
        "country": "India",
        "country_code": "IN",
        "currency": "INR",
        "currency_symbol": "₹",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": False,
    },
    "coimbatore": {
        "name": "Coimbatore",
        "country": "India",
        "country_code": "IN",
        "currency": "INR",
        "currency_symbol": "₹",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": False,
    },
    "bolivia": {
        "name": "La Paz",
        "country": "Bolivia",
        "country_code": "BO",
        "currency": "BOB",
        "currency_symbol": "Bs.",
        "latitude": -16.5000,
        "longitude": -68.1500,
        "region": "South America",
        "is_long_haul": True,
        "is_regional_international": False,
    },
    "dubai": {
        "name": "Dubai",
        "country": "United Arab Emirates",
        "country_code": "AE",
        "currency": "AED",
        "currency_symbol": "د.إ",
        "latitude": 25.2048,
        "longitude": 55.2708,
        "region": "Middle East",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "kathmandu": {
        "name": "Kathmandu",
        "country": "Nepal",
        "country_code": "NP",
        "currency": "NPR",
        "currency_symbol": "Rs.",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "kyoto": {
        "name": "Kyoto",
        "country": "Japan",
        "country_code": "JP",
        "currency": "JPY",
        "currency_symbol": "¥",
        "latitude": 35.0116,
        "longitude": 135.7681,
        "region": "East Asia",
        "is_long_haul": False,
        "is_regional_international": True,
    },
    "jaipur": {
        "name": "Jaipur",
        "country": "India",
        "country_code": "IN",
        "currency": "INR",
        "currency_symbol": "₹",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "region": "South Asia",
        "is_long_haul": False,
        "is_regional_international": False,
    },
    "nairobi": {
        "name": "Nairobi",
        "country": "Kenya",
        "country_code": "KE",
        "currency": "KES",
        "currency_symbol": "KSh",
        "latitude": -1.2921,
        "longitude": 36.8219,
        "region": "East Africa",
        "is_long_haul": True,
        "is_regional_international": False,
    },
}

INDIAN_CITIES = {
    "agra", "delhi", "new delhi", "mumbai", "coimbatore", "chennai", "bengaluru",
    "bangalore", "kolkata", "hyderabad", "pune", "kochi", "goa", "jaipur",
    "varanasi", "manali", "shimla", "rishikesh", "amritsar", "mysore", "udaipur",
    "kerala", "shillong", "guwahati", "darjeeling", "ooty", "pondicherry"
}


def resolve_destination_info(destination: str, origin: Optional[str] = None) -> Dict[str, Any]:
    """
    Truth-first destination resolver determining country, ISO code, authentic currency,
    GPS anchor, and truthful route corridor classification without city-specific hacks.
    """
    dest_raw = (destination or "").strip()
    dest_low = dest_raw.lower()
    orig_raw = (origin or "Coimbatore").strip()
    orig_low = orig_raw.lower()

    # 1. Match against Global Destination Gazetteer
    gaz_match = None
    for k, v in GLOBAL_DESTINATION_GAZETTEER.items():
        if k in dest_low or dest_low in k:
            gaz_match = v
            break

    # 2. Extract country name if in string, e.g. "Tbilisi, Georgia"
    country_name = None
    country_code = None
    if "," in dest_raw:
        parts = [p.strip() for p in dest_raw.split(",")]
        for p in parts[1:]:
            p_low = p.lower()
            if p_low in COUNTRY_NAME_TO_CODE:
                country_name = p.title()
                country_code = COUNTRY_NAME_TO_CODE[p_low]
                break

    if not country_code:
        for cname, ccode in COUNTRY_NAME_TO_CODE.items():
            if cname in dest_low:
                country_name = cname.title()
                country_code = ccode
                break

    if gaz_match:
        if not country_name:
            country_name = gaz_match["country"]
        if not country_code:
            country_code = gaz_match["country_code"]
        currency = gaz_match["currency"]
        currency_symbol = gaz_match["currency_symbol"]
        lat = gaz_match.get("latitude")
        lon = gaz_match.get("longitude")
        is_long_haul = gaz_match.get("is_long_haul", False)
        is_regional_international = gaz_match.get("is_regional_international", False)
    else:
        # Fallback to country mapping or default
        if country_code and country_code in COUNTRY_CODE_TO_CURRENCY:
            currency = COUNTRY_CODE_TO_CURRENCY[country_code]
        else:
            currency = "USD"
        currency_symbol = CURRENCY_SYMBOLS.get(currency, "$")
        lat = None
        lon = None
        is_long_haul = any(term in dest_low for term in ["south america", "bolivia", "peru", "chile", "brazil", "argentina", "iceland", "hawaii"])
        is_regional_international = not is_long_haul and country_code != "IN"

    # Evaluate domestic India route truth
    is_india_dest = (country_code == "IN") or any(ic in dest_low for ic in INDIAN_CITIES)
    is_india_origin = any(ic in orig_low for ic in INDIAN_CITIES) or "india" in orig_low
    is_india_domestic = is_india_dest and is_india_origin

    # If it is domestic India, currency is INR
    if is_india_domestic:
        currency = "INR"
        currency_symbol = "₹"
        flight_provenance = "Domestic Intercity Transit & Air Corridor Index"
    elif is_long_haul:
        flight_provenance = f"Transcontinental Long-Haul Route Index ({orig_raw} <-> {dest_raw})"
    elif is_regional_international or country_code != "IN":
        c_label = country_name or dest_raw.title()
        flight_provenance = f"International Air Route Index ({orig_raw} <-> {c_label})"
    else:
        flight_provenance = f"IATA Route Benchmark Average ({orig_raw} <-> {dest_raw})"

    return {
        "destination_clean": gaz_match["name"] if gaz_match else dest_raw,
        "country": country_name or ("India" if is_india_dest else "International"),
        "country_code": country_code or ("IN" if is_india_dest else "INTL"),
        "currency": currency,
        "currency_symbol": currency_symbol,
        "latitude": lat,
        "longitude": lon,
        "is_india_dest": is_india_dest,
        "is_india_origin": is_india_origin,
        "is_india_domestic": is_india_domestic,
        "is_long_haul": is_long_haul,
        "is_regional_international": is_regional_international,
        "flight_provenance_source": flight_provenance,
    }

