"""
journey_classifier.py — Geographic Scale Classifier for WanderWise Transit V11.1

Classifies origin and destination coordinate pairs into:
  - SAME_CITY
  - DOMESTIC
  - INTERNATIONAL
  - INTERCONTINENTAL

Uses ISO country codes returned by geocoders and an explicit COUNTRY_TO_CONTINENT lookup.
"""

import math
import logging
from typing import Dict, Any, Optional
from ..maps.nominatim_service import reverse_geocode, geocode_place

logger = logging.getLogger(__name__)

# Authoritative ISO 3166-1 Country -> Continent mapping
COUNTRY_TO_CONTINENT = {
    # Asia (ASIA)
    "IN": "ASIA", "JP": "ASIA", "KR": "ASIA", "CN": "ASIA", "TH": "ASIA", "SG": "ASIA",
    "MY": "ASIA", "ID": "ASIA", "VN": "ASIA", "AE": "ASIA", "SA": "ASIA", "QA": "ASIA",
    "PK": "ASIA", "BD": "ASIA", "LK": "ASIA", "NP": "ASIA", "PH": "ASIA", "TW": "ASIA",
    "HK": "ASIA", "MO": "ASIA", "IL": "ASIA", "JO": "ASIA", "LB": "ASIA", "KH": "ASIA",
    # Europe (EUROPE)
    "GB": "EUROPE", "FR": "EUROPE", "DE": "EUROPE", "IT": "EUROPE", "ES": "EUROPE", "NL": "EUROPE",
    "BE": "EUROPE", "AT": "EUROPE", "CH": "EUROPE", "PT": "EUROPE", "SE": "EUROPE", "NO": "EUROPE",
    "FI": "EUROPE", "DK": "EUROPE", "PL": "EUROPE", "CZ": "EUROPE", "HU": "EUROPE", "GR": "EUROPE",
    "IE": "EUROPE", "RO": "EUROPE", "BG": "EUROPE", "HR": "EUROPE", "UA": "EUROPE", "RU": "EUROPE",
    "TR": "EUROPE", "IS": "EUROPE", "LU": "EUROPE",
    # North America (NORTH_AMERICA)
    "US": "NORTH_AMERICA", "CA": "NORTH_AMERICA", "MX": "NORTH_AMERICA", "CU": "NORTH_AMERICA",
    "JM": "NORTH_AMERICA", "CR": "NORTH_AMERICA", "PA": "NORTH_AMERICA",
    # South America (SOUTH_AMERICA)
    "BR": "SOUTH_AMERICA", "AR": "SOUTH_AMERICA", "CL": "SOUTH_AMERICA", "CO": "SOUTH_AMERICA",
    "PE": "SOUTH_AMERICA", "VE": "SOUTH_AMERICA", "UY": "SOUTH_AMERICA",
    # Africa (AFRICA)
    "EG": "AFRICA", "ZA": "AFRICA", "MA": "AFRICA", "KE": "AFRICA", "NG": "AFRICA",
    "ET": "AFRICA", "GH": "AFRICA", "TN": "AFRICA",
    # Oceania (OCEANIA)
    "AU": "OCEANIA", "NZ": "OCEANIA", "FJ": "OCEANIA",
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in km between two coordinate points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _extract_country_code(lat: float, lon: float, display_name: str) -> str:
    """Extracts 2-letter ISO country code from display name heuristics or reverse geocoding."""
    dn = display_name.lower()
    if any(k in dn for k in ["united kingdom", "england", "scotland", "wales", "london", "manchester"]):
        return "GB"
    if any(k in dn for k in ["france", "paris", "lyon"]):
        return "FR"
    if any(k in dn for k in ["india", "coimbatore", "chennai", "mumbai", "delhi", "erode", "bangalore"]):
        return "IN"
    if any(k in dn for k in ["japan", "tokyo", "osaka", "東京都"]):
        return "JP"
    if any(k in dn for k in ["korea", "seoul", "서울특별시"]):
        return "KR"
    if any(k in dn for k in ["united states", "usa", "new york", "california"]):
        return "US"

    try:
        rev = reverse_geocode(lat, lon)
        cc = rev.get("country_code") or rev.get("address", {}).get("country_code")
        if cc:
            return cc.upper()
    except Exception:
        pass
    return "UNKNOWN"


class JourneyClassifier:
    @staticmethod
    def classify(
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        origin_name: str = "",
        dest_name: str = ""
    ) -> Dict[str, Any]:
        """
        Classifies geographic scale strictly by ISO country codes and continent mapping.
        """
        dist_km = round(_haversine_km(origin_lat, origin_lon, dest_lat, dest_lon), 1)

        c_orig = _extract_country_code(origin_lat, origin_lon, origin_name)
        c_dest = _extract_country_code(dest_lat, dest_lon, dest_name)

        cont_orig = COUNTRY_TO_CONTINENT.get(c_orig, "UNKNOWN_ORIG_CONT")
        cont_dest = COUNTRY_TO_CONTINENT.get(c_dest, "UNKNOWN_DEST_CONT")

        if c_orig != "UNKNOWN" and c_dest != "UNKNOWN" and c_orig == c_dest:
            scale = "SAME_CITY" if dist_km < 35 else "DOMESTIC"
        elif cont_orig != "UNKNOWN_ORIG_CONT" and cont_dest != "UNKNOWN_DEST_CONT" and cont_orig == cont_dest:
            scale = "INTERNATIONAL"
        elif c_orig != "UNKNOWN" and c_dest != "UNKNOWN" and c_orig != c_dest and cont_orig != cont_dest:
            scale = "INTERCONTINENTAL"
        else:
            # Distance fallback if country codes completely unknown
            if dist_km < 35:
                scale = "SAME_CITY"
            elif dist_km < 1500:
                scale = "DOMESTIC"
            elif dist_km < 3500:
                scale = "INTERNATIONAL"
            else:
                scale = "INTERCONTINENTAL"

        logger.info(f"[CLASSIFIER V11.1] Scale: {scale} (Dist: {dist_km} km, Country: {c_orig}[{cont_orig}] -> {c_dest}[{cont_dest}])")
        return {
            "scale": scale,
            "origin_country": c_orig,
            "destination_country": c_dest,
            "origin_continent": cont_orig,
            "destination_continent": cont_dest,
            "distance_km": dist_km,
        }
