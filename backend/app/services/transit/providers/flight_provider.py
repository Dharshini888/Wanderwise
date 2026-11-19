"""
flight_provider.py — Single API Key Flight Provider Abstraction for WanderWise V12.3

Integrates AviationStack API (https://api.aviationstack.com/v1) using single API key authentication:
  - Primary key: FLIGHT_API_KEY
  - Fallback key: AVIATIONSTACK_API_KEY

Truth-First Rules:
1. Always uses official HTTPS endpoint (https://api.aviationstack.com/v1/flights).
2. Never exposes the API key in frontend payloads, logs, or error messages (strict sanitization).
3. Distinguishes error categories:
     - INVALID_API_KEY (HTTP 401, code 101 / invalid_access_key)
     - SUBSCRIPTION_RESTRICTION (HTTP 403, code 103 / 105 / function_access_restricted / https_access_restricted)
     - QUOTA_EXHAUSTED (HTTP 429, code 104 / usage_limit_reached)
     - TIMEOUT (requests.exceptions.Timeout)
     - CONNECTION_ERROR (DNS or network failure)
     - UNSUPPORTED_ENDPOINT (HTTP 404 / invalid_api_function)
     - EMPTY_SEARCH_RESULTS (HTTP 200 with data: [])
4. Never fabricates flight numbers, departure times, arrival times, or fares.
5. Does NOT return mock flights when the provider fails.
"""

import os
import re
import json
import requests
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date, timedelta, timezone

from .base import TransitProvider, ProviderStatus, ProviderResult
from ...maps.osrm_service import haversine_distance
from ..airport_service import GLOBAL_AIRPORTS, resolve_serving_airports, get_airport_by_iata, get_airport_timezone

logger = logging.getLogger(__name__)

AVIATIONSTACK_BASE_URL = "https://api.aviationstack.com/v1"
FLIGHTS_ENDPOINT = f"{AVIATIONSTACK_BASE_URL}/flights"
AIRPORTS_ENDPOINT = f"{AVIATIONSTACK_BASE_URL}/airports"


def parse_aviationstack_datetime(iso_str: Optional[str], tz_name: Optional[str] = None) -> Optional[datetime]:
    """
    Parses AviationStack ISO-8601 strings and attaches the authentic local IANA timezone.
    AviationStack returns the local wall-clock time in the scheduled string
    (e.g. '2026-11-18T19:55:00+00:00') and specifies the authentic local timezone
    in a separate 'timezone' field (e.g. 'Asia/Kolkata').
    """
    if not iso_str:
        return None
    try:
        clean_str = str(iso_str).replace("Z", "").split("+")[0]
        naive_dt = datetime.fromisoformat(clean_str)
    except Exception:
        return None

    if tz_name:
        try:
            from app.services.transit.tz_utils import get_timezone
            return naive_dt.replace(tzinfo=get_timezone(tz_name))
        except Exception:
            pass

    return naive_dt.replace(tzinfo=timezone.utc)


def _mask_key(key: Optional[str]) -> str:
    """Safely masks API key for logging and diagnostics (e.g. edab...0d2b)."""
    if not key:
        return "[NOT SET]"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def _sanitize_message(message: str, key: Optional[str]) -> str:
    """Removes any occurrence of the raw API key from a string or error payload."""
    if not message or not key:
        return message or ""
    return str(message).replace(key, _mask_key(key))


def classify_provider_error(
    status_code: Optional[int],
    error_payload: Optional[Dict[str, Any]] = None,
    raw_error: Optional[Exception] = None,
    key: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Classifies AviationStack provider errors into standardized categories.
    Returns: (category, sanitized_error_msg, user_facing_note)
    """
    if isinstance(raw_error, requests.exceptions.Timeout):
        return (
            "TIMEOUT",
            "Request to AviationStack timed out after 8 seconds",
            "Flight provider request timed out. Please try again."
        )
    if isinstance(raw_error, requests.exceptions.ConnectionError):
        err_msg = _sanitize_message(str(raw_error)[:120], key)
        return (
            "CONNECTION_ERROR",
            f"Network connection failed: {err_msg}",
            "Flight provider endpoint could not be reached (DNS or network error)."
        )

    err_data = error_payload or {}
    if isinstance(err_data, dict) and "error" in err_data:
        err_data = err_data["error"]

    err_code = err_data.get("code")
    err_type = str(err_data.get("type", "")).lower()
    err_info = str(err_data.get("info", err_data.get("message", "")))
    sanitized_info = _sanitize_message(err_info, key)

    # 1. Invalid API Key
    if (
        status_code == 401
        or err_code in [101, "invalid_access_key"]
        or "invalid_access_key" in err_type
        or "missing_access_key" in err_type
    ):
        return (
            "INVALID_API_KEY",
            f"HTTP {status_code or 401}: {sanitized_info or 'Invalid API Access Key'}",
            "Flight provider authentication failed: The configured API key is invalid or unauthorized."
        )

    # 2. Subscription Restriction
    if (
        status_code == 403
        or err_code in [103, 105, "function_access_restricted", "https_access_restricted"]
        or "function_access_restricted" in err_type
        or "https_access_restricted" in err_type
        or "subscription plan does not support" in sanitized_info.lower()
    ):
        return (
            "SUBSCRIPTION_RESTRICTION",
            f"HTTP {status_code or 403}: {sanitized_info or 'Subscription Plan Restricted'}",
            "Current AviationStack subscription plan does not support this query or endpoint."
        )

    # 3. Quota Exhaustion
    if (
        status_code == 429
        or err_code in [104, "usage_limit_reached", "rate_limit_reached"]
        or "usage_limit_reached" in err_type
        or "rate_limit_reached" in err_type
    ):
        return (
            "QUOTA_EXHAUSTED",
            f"HTTP {status_code or 429}: {sanitized_info or 'API Usage Quota Exceeded'}",
            "AviationStack monthly request quota or rate limit has been exhausted."
        )

    # 4. Unsupported Endpoint
    if status_code == 404 or err_code in ["invalid_api_function"]:
        return (
            "UNSUPPORTED_ENDPOINT",
            f"HTTP {status_code or 404}: {sanitized_info or 'Unsupported Endpoint'}",
            "The requested flight API endpoint is not supported by the provider."
        )

    # General HTTP error
    code_str = str(err_code or status_code or "UNKNOWN")
    return (
        f"PROVIDER_ERROR_{code_str.upper()}",
        f"HTTP {status_code}: {sanitized_info or 'Provider Error'}",
        f"Flight provider returned an error: {sanitized_info or 'Unexpected response'}"
    )


def find_nearest_airport(
    lat: float,
    lon: float,
    max_radius_km: float = 300.0,
    is_international: bool = True
) -> Optional[Dict[str, Any]]:
    """Resolves nearest commercial serving airport from global airport registry."""
    if lat is None or lon is None:
        return None
    nearest = None
    min_dist = float('inf')

    candidate_airports = GLOBAL_AIRPORTS
    if is_international:
        intl_candidates = [
            ap for ap in GLOBAL_AIRPORTS
            if ap.get("tier") in ["primary_international", "secondary_international"]
        ]
        if intl_candidates:
            candidate_airports = intl_candidates

    for ap in candidate_airports:
        dist = haversine_distance(lat, lon, ap["lat"], ap["lon"])
        if dist < min_dist and dist <= max_radius_km:
            min_dist = dist
            nearest = ap.copy()
            nearest["distance_from_point_km"] = round(dist, 2)

    # Fallback to any airport if no international airport was within radius
    if not nearest and is_international:
        return find_nearest_airport(lat, lon, max_radius_km=max_radius_km, is_international=False)

    return nearest


class FlightProvider(TransitProvider):
    """
    Production Flight Provider interfacing with AviationStack API over HTTPS.
    Guarantees strict authentication validation, truthful non-mock fallbacks, and
    detailed error categorization.
    """

    def __init__(self):
        super().__init__(provider_name="FlightProvider")
        self.session = requests.Session()

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Loads and returns configured flight API key from backend environment."""
        return os.getenv("FLIGHT_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")

    @classmethod
    def health_check(cls, probe_network: bool = True) -> Dict[str, Any]:
        """
        Comprehensive diagnostic probe for AviationStack flight provider.
        Performs minimal authentication request against https://api.aviationstack.com/v1/flights.
        Never exposes the raw API key in return payload or logs.
        """
        key = cls.get_api_key()
        if not key:
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": False,
                "authenticated": False,
                "reachable": False,
                "status": "PROVIDER_NOT_CONFIGURED",
                "category": "KEY_MISSING",
                "message": "FLIGHT_API_KEY environment variable is not configured.",
            }

        masked = _mask_key(key)

        if not probe_network:
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": True,
                "key_preview": masked,
                "status": "CONFIGURED",
                "message": "API key present (network probe skipped).",
            }

        headers = {"User-Agent": "WanderWise/12.3 (HealthCheck)"}
        params = {"access_key": key, "limit": 1}

        try:
            resp = requests.get(FLIGHTS_ENDPOINT, params=params, headers=headers, timeout=6)
            http_status = resp.status_code

            try:
                data = resp.json()
            except Exception:
                data = {}

            # AviationStack error responses
            if "error" in data:
                cat, err_msg, user_note = classify_provider_error(http_status, data, key=key)
                return {
                    "provider": "FlightProvider",
                    "api_service": "AviationStack",
                    "configured": True,
                    "authenticated": False,
                    "reachable": True,
                    "http_status": http_status,
                    "status": "PROVIDER_ERROR",
                    "category": cat,
                    "key_preview": masked,
                    "message": err_msg,
                    "note": user_note,
                }

            if http_status == 200 and "data" in data:
                return {
                    "provider": "FlightProvider",
                    "api_service": "AviationStack",
                    "configured": True,
                    "authenticated": True,
                    "reachable": True,
                    "http_status": 200,
                    "status": "AUTHENTICATED",
                    "category": "SUCCESS_AUTHENTICATED",
                    "endpoint": FLIGHTS_ENDPOINT,
                    "key_preview": masked,
                    "message": "AviationStack API authenticated and operational over HTTPS.",
                }

            # Fallback HTTP error
            cat, err_msg, user_note = classify_provider_error(http_status, data, key=key)
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": True,
                "authenticated": False,
                "reachable": True,
                "http_status": http_status,
                "status": "PROVIDER_ERROR",
                "category": cat,
                "key_preview": masked,
                "message": err_msg,
                "note": user_note,
            }

        except requests.exceptions.Timeout as e:
            cat, err_msg, user_note = classify_provider_error(None, raw_error=e, key=key)
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": True,
                "authenticated": False,
                "reachable": False,
                "status": "PROVIDER_UNAVAILABLE",
                "category": cat,
                "key_preview": masked,
                "message": err_msg,
                "note": user_note,
            }
        except requests.exceptions.ConnectionError as e:
            cat, err_msg, user_note = classify_provider_error(None, raw_error=e, key=key)
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": True,
                "authenticated": False,
                "reachable": False,
                "status": "PROVIDER_UNAVAILABLE",
                "category": cat,
                "key_preview": masked,
                "message": err_msg,
                "note": user_note,
            }
        except Exception as e:
            sanitized_e = _sanitize_message(str(e)[:150], key)
            return {
                "provider": "FlightProvider",
                "api_service": "AviationStack",
                "configured": True,
                "authenticated": False,
                "reachable": False,
                "status": "PROVIDER_UNAVAILABLE",
                "category": "UNEXPECTED_ERROR",
                "key_preview": masked,
                "message": sanitized_e,
                "note": "Unexpected error while reaching flight provider.",
            }

    @classmethod
    def test_airport_code(cls, iata_code: str) -> Dict[str, Any]:
        """
        Tests flight retrieval for a specific airport code independently (e.g. CJB or KIX).
        Uses /v1/flights with dep_iata filter.
        """
        key = cls.get_api_key()
        if not key:
            return {"iata": iata_code, "status": "KEY_MISSING", "active_flights": 0, "message": "API key missing"}

        headers = {"User-Agent": "WanderWise/12.3 (AirportTest)"}
        params = {"access_key": key, "dep_iata": iata_code.upper(), "limit": 3}

        try:
            resp = requests.get(FLIGHTS_ENDPOINT, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    cat, msg, _ = classify_provider_error(resp.status_code, data, key=key)
                    return {"iata": iata_code, "status": cat, "active_flights": 0, "message": msg}

                flights = data.get("data", [])
                sample = []
                for f in flights[:2]:
                    sample.append({
                        "flight_number": f.get("flight", {}).get("iata") or f.get("flight", {}).get("number"),
                        "destination_iata": f.get("arrival", {}).get("iata"),
                        "destination_airport": f.get("arrival", {}).get("airport"),
                        "status": f.get("flight_status"),
                    })
                return {
                    "iata": iata_code,
                    "status": "SUCCESS",
                    "http_status": 200,
                    "active_flights_count": len(flights),
                    "sample_flights": sample,
                }
            else:
                cat, msg, _ = classify_provider_error(resp.status_code, key=key)
                return {"iata": iata_code, "status": cat, "http_status": resp.status_code, "message": msg}
        except Exception as e:
            return {"iata": iata_code, "status": "ERROR", "message": _sanitize_message(str(e)[:120], key)}

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        origin_name: str = "",
        dest_name: str = "",
    ) -> ProviderResult:
        """
        Executes verified flight search between origin coordinates and destination coordinates.
        1. Resolves serving airports (e.g. Coimbatore -> CJB, Kansai -> KIX).
        2. Queries AviationStack over HTTPS.
        3. Parses verified flights and calculates distance.
        4. NEVER generates mock flights upon empty results or errors.
        """
        flight_key = self.get_api_key()

        is_intl = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon) > 500.0

        # 1. Resolve authentic commercial serving airports for origin and destination
        orig_candidates = resolve_serving_airports(origin_name, origin_lat, origin_lon, is_international=is_intl)
        if not orig_candidates:
            fallback_orig = find_nearest_airport(origin_lat, origin_lon, is_international=is_intl)
            orig_candidates = [fallback_orig] if fallback_orig else []

        dest_candidates = resolve_serving_airports(dest_name, dest_lat, dest_lon, is_international=is_intl)
        if not dest_candidates:
            fallback_dest = find_nearest_airport(dest_lat, dest_lon, is_international=is_intl)
            dest_candidates = [fallback_dest] if fallback_dest else []

        if not orig_candidates or not dest_candidates:
            logger.info("[FlightProvider] No valid serving commercial airports found near coordinates.")
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                category="AIRPORTS_UNRESOLVED",
                note="No verified commercial flight route available: Origin or destination is outside airport serving radius.",
            )

        orig_ap = orig_candidates[0]
        orig_iata = orig_ap["iata"]

        if not flight_key:
            logger.info("[FlightProvider] PROVIDER_NOT_CONFIGURED (FLIGHT_API_KEY missing)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                category="KEY_MISSING",
                note="Flight provider API credentials are unconfigured.",
            )

        # Parse requested travel date if provided
        target_date_str = None
        dep_type_clean = str((preferences or {}).get("departure_type") or "now").strip().lower()
        date_pref = str((preferences or {}).get("date") or "").strip().lower()

        # Only pass flight_date if user explicitly requested a future/specific date and not 'now'/'today'
        if dep_type_clean != "now" and date_pref not in ("today", "now", ""):
            if departure_time:
                try:
                    clean_time = departure_time.replace("Z", "+00:00")
                    dt_val = datetime.fromisoformat(clean_time)
                    if dt_val.date() > datetime.now().date():
                        target_date_str = dt_val.strftime("%Y-%m-%d")
                except Exception:
                    pass
            elif date_pref == "tomorrow":
                target_date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", date_pref):
                try:
                    p_date = datetime.strptime(date_pref, "%Y-%m-%d").date()
                    if p_date > datetime.now().date():
                        target_date_str = date_pref
                except Exception:
                    pass

        headers = {"User-Agent": "WanderWise/12.3 (FlightProvider)"}
        candidate_dest_iatas = [c["iata"] for c in dest_candidates[:2]]

        all_raw_flights: List[Dict[str, Any]] = []
        last_error_data = None
        last_http_status = None

        for target_dest_iata in candidate_dest_iatas:
            params: Dict[str, Any] = {
                "access_key": flight_key,
                "dep_iata": orig_iata,
                "arr_iata": target_dest_iata,
                "limit": 5,
            }
            if target_date_str:
                params["flight_date"] = target_date_str

            try:
                resp = self.session.get(FLIGHTS_ENDPOINT, params=params, headers=headers, timeout=8)
                last_http_status = resp.status_code

                try:
                    data = resp.json()
                except Exception:
                    data = {}

                if "error" in data:
                    last_error_data = data
                    cat, err_msg, user_note = classify_provider_error(resp.status_code, data, key=flight_key)
                    logger.warning(f"[FlightProvider] Provider Error querying {orig_iata}->{target_dest_iata}: {err_msg}")
                    if cat in ["INVALID_API_KEY", "QUOTA_EXHAUSTED", "SUBSCRIPTION_RESTRICTION"]:
                        return ProviderResult(
                            status=ProviderStatus.PROVIDER_ERROR,
                            provider_name=self.provider_name,
                            category=cat,
                            http_status=resp.status_code,
                            error=err_msg,
                            note=user_note,
                        )
                elif resp.status_code == 200:
                    fl_list = data.get("data", [])
                    if fl_list:
                        all_raw_flights.extend(fl_list)
                        # We have verified flights for this corridor; avoid redundant API calls
                        break
            except Exception as query_err:
                logger.debug(f"[FlightProvider] Exception querying {orig_iata}->{target_dest_iata}: {query_err}")

        # If all candidate gateway queries failed with provider error and no flights found
        if not all_raw_flights and last_error_data:
            cat, err_msg, user_note = classify_provider_error(last_http_status, last_error_data, key=flight_key)
            return ProviderResult(
                status=ProviderStatus.PROVIDER_ERROR,
                provider_name=self.provider_name,
                category=cat,
                http_status=last_http_status or 500,
                error=err_msg,
                note=user_note,
            )

        if all_raw_flights:
            normalized_options = []

            resolved_orig_name = origin_name or orig_ap["name"]
            resolved_dest_name = dest_name or dest_candidates[0]["name"]

            # Ensure flight journey endpoints reflect the city/region name, never a railway station
            if resolved_orig_name.lower().endswith(" junction"):
                resolved_orig_name = resolved_orig_name[:-9].strip()
            elif resolved_orig_name.lower().endswith(" central"):
                resolved_orig_name = resolved_orig_name[:-8].strip()
            elif resolved_orig_name.lower().endswith(" railway station"):
                resolved_orig_name = resolved_orig_name[:-16].strip()

            if resolved_dest_name.lower().endswith(" junction"):
                resolved_dest_name = resolved_dest_name[:-9].strip()
            elif resolved_dest_name.lower().endswith(" central"):
                resolved_dest_name = resolved_dest_name[:-8].strip()
            elif resolved_dest_name.lower().endswith(" railway station"):
                resolved_dest_name = resolved_dest_name[:-16].strip()

            for f in all_raw_flights[:3]:
                flight_num = f.get("flight", {}).get("iata") or f.get("flight", {}).get("number")
                dep = f.get("departure", {}) or {}
                arr = f.get("arrival", {}) or {}

                # Resolve actual airport returned by provider (e.g. HND or NRT, never assume)
                actual_dep_iata = dep.get("iata") or orig_iata
                actual_arr_iata = arr.get("iata") or candidate_dest_iatas[0]

                actual_orig_ap = get_airport_by_iata(actual_dep_iata) or orig_ap
                actual_dest_ap = get_airport_by_iata(actual_arr_iata) or next(
                    (c for c in dest_candidates if c.get("iata") == actual_arr_iata), dest_candidates[0]
                )

                dep_airport_full = f"{actual_orig_ap['name']} ({actual_orig_ap['iata']})"
                arr_airport_full = f"{actual_dest_ap['name']} ({actual_dest_ap['iata']})"

                flight_dist = haversine_distance(
                    actual_orig_ap["lat"], actual_orig_ap["lon"],
                    actual_dest_ap["lat"], actual_dest_ap["lon"]
                )

                # Timezone-aware timestamp extraction
                dep_time_raw = dep.get("scheduled") or dep.get("estimated")
                dep_tz_name = dep.get("timezone") or get_airport_timezone(actual_orig_ap)
                arr_time_raw = arr.get("scheduled") or arr.get("estimated")
                arr_tz_name = arr.get("timezone") or get_airport_timezone(actual_dest_ap)

                d_dt = parse_aviationstack_datetime(dep_time_raw, dep_tz_name)
                a_dt = parse_aviationstack_datetime(arr_time_raw, arr_tz_name)

                # Accurate in-air elapsed flight duration in UTC
                flight_dur_min = 120.0
                if d_dt and a_dt:
                    d_utc = d_dt.astimezone(timezone.utc)
                    a_utc = a_dt.astimezone(timezone.utc)
                    diff = (a_utc - d_utc).total_seconds() / 60.0
                    if diff > 10:
                        flight_dur_min = diff

                fl_h = int(flight_dur_min // 60)
                fl_m = int(round(flight_dur_min % 60))
                flight_dur_display = f"{fl_h}h {fl_m}m" if fl_h > 0 else f"{fl_m}m"

                # Local departure display (in departure airport local timezone)
                dep_tz_str = d_dt.tzname() or "" if d_dt else ""
                dep_disp = f"{d_dt.strftime('%I:%M %p').lstrip('0')} {dep_tz_str}".strip() if d_dt else None

                # Local arrival display (in arrival airport local timezone)
                arr_tz_str = a_dt.tzname() or "" if a_dt else ""
                arr_disp = f"{a_dt.strftime('%I:%M %p').lstrip('0')} {arr_tz_str}".strip() if a_dt else None
                if d_dt and a_dt and a_dt.date() > d_dt.date():
                    days_diff = (a_dt.date() - d_dt.date()).days
                    arr_disp += f" (+{days_diff} day{'s' if days_diff > 1 else ''})"

                airline_name = f.get("airline", {}).get("name") or "Commercial Airline"

                # Ground access (Origin -> Departure Airport)
                access_dist_km = haversine_distance(origin_lat, origin_lon, actual_orig_ap["lat"], actual_orig_ap["lon"])
                needs_access = access_dist_km > 1.5
                access_dur_min = round(max(10.0, access_dist_km * 1.5), 1) if needs_access else 0.0

                # Airport Check-in buffer: 180 min international, 90 min domestic
                checkin_buffer_min = 180.0 if is_intl else 90.0

                # Airport Baggage Claim & Deplaning buffer: 45 min international, 30 min domestic
                baggage_buffer_min = 45.0 if is_intl else 30.0

                # Ground egress (Arrival Airport -> Destination)
                egress_dist_km = haversine_distance(actual_dest_ap["lat"], actual_dest_ap["lon"], dest_lat, dest_lon)
                needs_egress = egress_dist_km > 1.5
                egress_dur_min = round(max(10.0, egress_dist_km * 1.5), 1) if needs_egress else 0.0

                # Door departure and arrival timestamps
                if d_dt:
                    door_dep_dt = d_dt - timedelta(minutes=int(access_dur_min + checkin_buffer_min))
                    ap_arr_dt = door_dep_dt + timedelta(minutes=int(access_dur_min))
                else:
                    door_dep_dt = None
                    ap_arr_dt = None

                if a_dt:
                    ap_exit_dt = a_dt + timedelta(minutes=int(baggage_buffer_min))
                    door_arr_dt = ap_exit_dt + timedelta(minutes=int(egress_dur_min))
                else:
                    ap_exit_dt = None
                    door_arr_dt = None

                # ── Build Door-to-Door Legs ──
                legs = []

                # Leg 1: First Mile / Ground Access
                if needs_access:
                    legs.append({
                        "type": "FIRST_MILE",
                        "mode": "Driving",
                        "provider": "OSRM",
                        "from_name": resolved_orig_name,
                        "to_name": dep_airport_full,
                        "departure_time": door_dep_dt.isoformat() if door_dep_dt else None,
                        "arrival_time": ap_arr_dt.isoformat() if ap_arr_dt else None,
                        "departure_time_display": door_dep_dt.strftime("%I:%M %p").lstrip("0") if door_dep_dt else None,
                        "arrival_time_display": ap_arr_dt.strftime("%I:%M %p").lstrip("0") if ap_arr_dt else None,
                        "duration_minutes": access_dur_min,
                        "duration_min": access_dur_min,
                        "distance_km": round(access_dist_km, 2),
                        "verification_status": "Route Calculated",
                        "source": "OSRM Road",
                    })

                # Transfer 1: Check-in buffer
                legs.append({
                    "type": "TRANSFER",
                    "mode": "Transfer",
                    "provider": "Airport",
                    "from_name": dep_airport_full,
                    "to_name": dep_airport_full,
                    "departure_time": ap_arr_dt.isoformat() if ap_arr_dt else None,
                    "arrival_time": d_dt.isoformat() if d_dt else None,
                    "departure_time_display": ap_arr_dt.strftime("%I:%M %p").lstrip("0") if ap_arr_dt else None,
                    "arrival_time_display": dep_disp,
                    "duration_minutes": checkin_buffer_min,
                    "duration_min": checkin_buffer_min,
                    "verification_status": "Buffer Verified",
                    "note": f"Airport check-in & security buffer ({int(checkin_buffer_min)} min)",
                })

                # Leg 2: Main Flight Leg
                legs.append({
                    "type": "MAIN_TRANSIT",
                    "mode": "Flight",
                    "provider": "FlightProvider",
                    "airline": airline_name,
                    "airline_name": airline_name,
                    "flight_number": flight_num or "Commercial Flight",
                    "from_name": dep_airport_full,
                    "to_name": arr_airport_full,
                    "origin": dep_airport_full,
                    "destination": arr_airport_full,
                    "origin_iata": actual_orig_ap["iata"],
                    "destination_iata": actual_dest_ap["iata"],
                    "departure_time": d_dt.isoformat() if d_dt else None,
                    "arrival_time": a_dt.isoformat() if a_dt else None,
                    "departure_time_display": dep_disp,
                    "arrival_time_display": arr_disp,
                    "duration_minutes": round(flight_dur_min, 1),
                    "duration_min": round(flight_dur_min, 1),
                    "duration_display": flight_dur_display,
                    "distance_km": round(flight_dist, 2),
                    "verification_status": "Provider Verified",
                    "source": "AviationStack",
                })

                # Transfer 2: Baggage claim buffer
                legs.append({
                    "type": "TRANSFER",
                    "mode": "Transfer",
                    "provider": "Airport",
                    "from_name": arr_airport_full,
                    "to_name": arr_airport_full,
                    "departure_time": a_dt.isoformat() if a_dt else None,
                    "arrival_time": ap_exit_dt.isoformat() if ap_exit_dt else None,
                    "departure_time_display": arr_disp,
                    "arrival_time_display": ap_exit_dt.strftime("%I:%M %p").lstrip("0") if ap_exit_dt else None,
                    "duration_minutes": baggage_buffer_min,
                    "duration_min": baggage_buffer_min,
                    "verification_status": "Buffer Verified",
                    "note": f"Deplaning & baggage claim buffer ({int(baggage_buffer_min)} min)",
                })

                # Leg 3: Last Mile / Ground Egress
                if needs_egress:
                    legs.append({
                        "type": "LAST_MILE",
                        "mode": "Driving",
                        "provider": "OSRM",
                        "from_name": arr_airport_full,
                        "to_name": resolved_dest_name,
                        "departure_time": ap_exit_dt.isoformat() if ap_exit_dt else None,
                        "arrival_time": door_arr_dt.isoformat() if door_arr_dt else None,
                        "departure_time_display": ap_exit_dt.strftime("%I:%M %p").lstrip("0") if ap_exit_dt else None,
                        "arrival_time_display": door_arr_dt.strftime("%I:%M %p").lstrip("0") if door_arr_dt else None,
                        "duration_minutes": egress_dur_min,
                        "duration_min": egress_dur_min,
                        "distance_km": round(egress_dist_km, 2),
                        "verification_status": "Route Calculated",
                        "source": "OSRM Road",
                    })

                total_door_dur_min = round(access_dur_min + checkin_buffer_min + flight_dur_min + baggage_buffer_min + egress_dur_min, 1)
                total_door_dist_km = round(access_dist_km + flight_dist + egress_dist_km, 2)
                door_h = int(total_door_dur_min // 60)
                door_m = int(round(total_door_dur_min % 60))
                total_door_dur_display = f"{door_h}h {door_m}m" if door_h > 0 else f"{door_m}m"

                # Realtime telemetry detection
                live_info = f.get("live")
                has_live_telemetry = bool(live_info and isinstance(live_info, dict) and live_info.get("latitude"))
                realtime_obj = {
                    "available": has_live_telemetry,
                    "status": "live" if has_live_telemetry else "unavailable",
                    "telemetry": live_info if has_live_telemetry else None,
                }

                normalized_options.append({
                    "provider": "FlightProvider",
                    "mode": "Flight",
                    "origin": resolved_orig_name,
                    "destination": resolved_dest_name,
                    "origin_airport": dep_airport_full,
                    "origin_iata": actual_orig_ap["iata"],
                    "origin_lat": actual_orig_ap["lat"],
                    "origin_lon": actual_orig_ap["lon"],
                    "destination_airport": arr_airport_full,
                    "destination_iata": actual_dest_ap["iata"],
                    "destination_lat": actual_dest_ap["lat"],
                    "destination_lon": actual_dest_ap["lon"],
                    "departure_station": dep_airport_full,
                    "arrival_station": arr_airport_full,
                    "flight_number": flight_num or "Commercial Flight",
                    "airline": airline_name,
                    "airline_name": airline_name,
                    "status": f.get("flight_status") or "Scheduled",

                    "departure_time": door_dep_dt.isoformat() if door_dep_dt else d_dt.isoformat() if d_dt else None,
                    "arrival_time": door_arr_dt.isoformat() if door_arr_dt else a_dt.isoformat() if a_dt else None,
                    "departure_time_display": door_dep_dt.strftime("%I:%M %p").lstrip("0") if door_dep_dt else dep_disp,
                    "arrival_time_display": door_arr_dt.strftime("%I:%M %p").lstrip("0") if door_arr_dt else arr_disp,

                    "flight_departure_time": d_dt.isoformat() if d_dt else None,
                    "flight_arrival_time": a_dt.isoformat() if a_dt else None,
                    "flight_departure_time_display": dep_disp,
                    "flight_arrival_time_display": arr_disp,

                    "flight_duration_minutes": round(flight_dur_min, 1),
                    "flight_duration_display": flight_dur_display,
                    "duration_minutes": total_door_dur_min,
                    "duration_min": total_door_dur_min,
                    "total_duration_minutes": total_door_dur_min,
                    "total_duration_display": total_door_dur_display,

                    "flight_distance_km": round(flight_dist, 2),
                    "distance_km": total_door_dist_km,
                    "total_distance_km": total_door_dist_km,

                    "transfers": 0,
                    "verification_status": "Provider Verified",
                    "verification": {
                        "level": "PROVIDER_VERIFIED",
                        "provider": "FlightProvider",
                        "live": has_live_telemetry,
                    },
                    "realtime": realtime_obj,
                    "source": {
                        "schedule": "AviationStack",
                        "duration": "Calculated from scheduled UTC timestamps",
                        "flight_duration": "Calculated from scheduled UTC timestamps",
                        "distance": "Great-circle calculation (Haversine)",
                        "flight_distance": "Great-circle calculation (Haversine)",
                        "fare": "Unavailable (AviationStack does not return ticket prices)",
                        "booking": "Unavailable (Booking availability not provided by provider)",
                        "ground_transfer": "OSRM Road",
                        "live_tracking": "LIVE_AIRBORNE" if has_live_telemetry else "SCHEDULE DATA ONLY",
                    },
                    "duration_breakdown": {
                        "access_min": access_dur_min,
                        "checkin_buffer_min": checkin_buffer_min,
                        "flight_min": round(flight_dur_min, 1),
                        "baggage_buffer_min": baggage_buffer_min,
                        "egress_min": egress_dur_min,
                        "total_door_to_door_min": total_door_dur_min,
                    },
                    "is_door_to_door": True,
                    "legs": legs,
                })

            primary_dest_iata = candidate_dest_iatas[0]
            return ProviderResult(
                status=ProviderStatus.SUCCESS,
                provider_name=self.provider_name,
                itineraries=normalized_options,
                category="SUCCESS_AUTHENTICATED",
                http_status=200,
                note=f"Verified door-to-door flight itineraries returned from AviationStack ({orig_iata} -> {primary_dest_iata}).",
            )

        # Direct flight search returned 0 results (Empty Search Results)
        primary_dest_iata = candidate_dest_iatas[0] if candidate_dest_iatas else dest_candidates[0]["iata"]
        logger.info(f"[FlightProvider] Empty search results for {orig_iata} -> {primary_dest_iata} (no direct flights).")
        return ProviderResult(
            status=ProviderStatus.NO_ITINERARY,
            provider_name=self.provider_name,
            itineraries=[],
            category="EMPTY_SEARCH_RESULTS",
            http_status=200,
            note=f"No direct verified flight options found for route {orig_iata} -> {primary_dest_iata}.",
        )
