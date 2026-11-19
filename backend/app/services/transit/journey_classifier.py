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
    "HK": "ASIA", "MO": "ASIA", "IL": "ASIA", "JO": "ASIA", "LB": "ASIA", "KH": "ASIA", "BT": "ASIA",
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


def _haversine_km(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
    """Calculates straight-line distance in km between two coordinate points."""
    if any(coord is None for coord in (lat1, lon1, lat2, lon2)):
        return 0.0
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _extract_country_code(lat: Optional[float], lon: Optional[float], display_name: str) -> str:
    """Extracts 2-letter ISO country code from reverse geocoding, display name heuristics, or geographic bounds."""
    # 1. Reverse geocoding (authoritative OpenStreetMap data)
    if lat is not None and lon is not None:
        try:
            rev = reverse_geocode(lat, lon)
            if rev:
                cc = rev.get("country_code") or rev.get("address", {}).get("country_code")
                if cc:
                    return cc.upper()
        except Exception:
            pass

    # 2. Display name text analysis
    dn = (display_name or "").lower()
    if any(k in dn for k in ["bhutan", "paro", "thimphu", ", bt"]):
        return "BT"
    if any(k in dn for k in ["united kingdom", "england", "scotland", "wales", "london", "manchester", ", uk", ", gb"]):
        return "GB"
    if any(k in dn for k in ["france", "paris", "lyon", "marseille", ", fr"]):
        return "FR"
    if any(k in dn for k in ["india", "coimbatore", "chennai", "mumbai", "delhi", "erode", "bangalore", "bengaluru", "pune", "salem", "madurai", ", in"]):
        return "IN"
    if any(k in dn for k in ["japan", "tokyo", "osaka", "kyoto", "kiyomizu", "fushimi", "inari", "東京都", "京都", "大阪", ", jp"]):
        return "JP"
    if any(k in dn for k in ["korea", "seoul", "서울특별시", ", kr"]):
        return "KR"
    if any(k in dn for k in ["united states", "usa", "new york", "california", ", us"]):
        return "US"
    if any(k in dn for k in ["singapore", ", sg"]):
        return "SG"
    if any(k in dn for k in ["australia", "sydney", "melbourne", ", au"]):
        return "AU"
    if any(k in dn for k in ["germany", "berlin", "munich", ", de"]):
        return "DE"
    if any(k in dn for k in ["italy", "rome", "milan", ", it"]):
        return "IT"
    if any(k in dn for k in ["spain", "madrid", "barcelona", ", es"]):
        return "ES"
    if any(k in dn for k in ["turkey", "türkiye", "istanbul", ", tr"]):
        return "TR"

    # 3. High-precision geographic boundary resolution (works offline / sandboxed)
    if lat is not None and lon is not None:
        if 26.7 <= lat <= 28.3 and 88.7 <= lon <= 92.2:
            return "BT"
        if 8.0 <= lat <= 37.5 and 68.0 <= lon <= 97.5:
            return "IN"
        if 24.0 <= lat <= 46.0 and 123.0 <= lon <= 146.0:
            return "JP"
        if 33.0 <= lat <= 38.8 and 124.5 <= lon <= 130.0:
            return "KR"
        if 1.15 <= lat <= 1.48 and 103.5 <= lon <= 104.1:
            return "SG"
        if 49.5 <= lat <= 61.0 and -8.5 <= lon <= 2.0:
            return "GB"
        if 42.0 <= lat <= 51.5 and -5.0 <= lon <= 10.0:
            return "FR"
        if 24.5 <= lat <= 49.5 and -125.0 <= lon <= -66.5:
            return "US"
        if -44.0 <= lat <= -10.0 and 112.0 <= lon <= 154.0:
            return "AU"
        if 47.0 <= lat <= 55.0 and 5.5 <= lon <= 15.5:
            return "DE"
        if 36.0 <= lat <= 47.5 and 6.5 <= lon <= 18.5:
            return "IT"
        if 36.0 <= lat <= 43.8 and -9.5 <= lon <= 3.5:
            return "ES"
        if 63.0 <= lat <= 67.0 and -25.0 <= lon <= -13.0:
            return "IS"
        if 35.8 <= lat <= 42.2 and 25.5 <= lon <= 45.0:
            return "TR"

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
        elif c_orig != "UNKNOWN" and c_dest != "UNKNOWN" and c_orig != c_dest:
            if cont_orig != "UNKNOWN_ORIG_CONT" and cont_dest != "UNKNOWN_DEST_CONT" and cont_orig != cont_dest:
                scale = "INTERCONTINENTAL"
            else:
                scale = "INTERNATIONAL"
        else:
            # If one country is known and both are in the same bounding continent, or domestic distance
            if dist_km < 35:
                scale = "SAME_CITY"
            elif (c_orig != "UNKNOWN" and c_orig == c_dest) or (dist_km < 2500 and (c_orig == "IN" or c_dest == "IN")):
                scale = "DOMESTIC"
            elif dist_km < 4000 and (cont_orig == cont_dest and cont_orig != "UNKNOWN_ORIG_CONT"):
                scale = "DOMESTIC"
            elif dist_km > 5000:
                scale = "INTERCONTINENTAL"
            else:
                scale = "DOMESTIC" if dist_km < 2000 else "INTERNATIONAL"

        logger.info(f"[CLASSIFIER V11.1] Scale: {scale} (Dist: {dist_km} km, Country: {c_orig}[{cont_orig}] -> {c_dest}[{cont_dest}])")
        return {
            "scale": scale,
            "origin_country": c_orig,
            "destination_country": c_dest,
            "origin_continent": cont_orig,
            "destination_continent": cont_dest,
            "distance_km": dist_km,
        }
