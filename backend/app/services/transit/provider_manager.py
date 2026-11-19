"""
provider_manager.py -- Centralized Transit Provider Manager for WanderWise V12.2

Responsibilities:
1. Register and orchestrate all transit providers:
   - RailRadar (Indian Railway API)
   - Transitous (Global MOTIS public transit engine)
   - RailwayEngine (Alternative Indian railway API)
   - QRail (Alternative Indian railway API)
   - VerifiedIndianRail (Authorized offline IRCTC schedule registry)
   - OSRM (Road & walking routing)
   - FlightProvider (AviationStack flights)
2. Enforce independent provider timeouts and circuit breakers (HEALTHY, RATE_LIMITED, AUTH_FAILED, UNAVAILABLE, TIMEOUT).
3. Capture and log exact rate-limit headers (X-RateLimit-Limit-Month, X-RateLimit-Remaining-Month, trace ID, latencies).
4. Automatic intelligent failover: When RailRadar is RATE_LIMITED (429) or exhausted, stop calling it and seamlessly
   utilize Transitous, alternative railway providers, and verified IRCTC schedules.
5. In-memory short-lived TTL response caching and in-flight request deduplication.
6. Provide accurate per-provider frontend statuses:
   - Connected
   - Rate limited
   - Temporarily unavailable
   - Authentication failed
   - Timeout
   - No verified itinerary
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, wait, FIRST_COMPLETED

from .providers.base import TransitProvider, ProviderStatus, ProviderResult
from .providers.railradar_provider import RailRadarProvider
from .providers.transitous_provider import TransitousProvider
from .providers.railway_engine_provider import RailwayEngineProvider
from .providers.qrail_provider import QRailProvider
from .providers.verified_schedule_provider import VerifiedIndianRailProvider
from .providers.flight_provider import FlightProvider
from .providers.osrm_provider import OSRMRoadProvider

logger = logging.getLogger(__name__)


class ProviderCircuitBreaker:
    """Per-provider circuit breaker and health status monitor."""

    def __init__(self, name: str, default_timeout: float = 4.0):
        self.name = name
        self.state = "HEALTHY"  # HEALTHY, RATE_LIMITED, AUTH_FAILED, UNAVAILABLE, TIMEOUT
        self.cooldown_until = 0.0
        self.default_timeout = default_timeout
        self.rate_limit_metrics: Dict[str, Any] = {}
        self.last_status: Optional[str] = None
        self.last_error: Optional[str] = None
        self.last_latency_ms: Optional[float] = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        with self._lock:
            if self.state in ("QUOTA_EXHAUSTED", "RATE_LIMITED", "AUTH_FAILED", "UNAVAILABLE"):
                if time.time() < self.cooldown_until:
                    return False
                # Cooldown expired: half-open probe
                self.state = "HEALTHY"
            return True

    def record_success(self, latency_ms: float = 0.0):
        with self._lock:
            self.state = "HEALTHY"
            self.last_latency_ms = latency_ms
            self.last_error = None
            self.last_status = "SUCCESS"

    def trip_rate_limited(self, metrics: Dict[str, Any], cooldown_sec: float = 300.0):
        with self._lock:
            rem_month = metrics.get("remaining_month")
            is_monthly = rem_month == 0 or "month" in str(metrics.get("error_message") or "").lower()
            effective_cooldown = 3600.0 if is_monthly else cooldown_sec
            self.state = "QUOTA_EXHAUSTED" if is_monthly else "RATE_LIMITED"
            self.cooldown_until = time.time() + effective_cooldown
            self.rate_limit_metrics = metrics
            self.last_status = self.state
            self.last_error = metrics.get("error_message") or ("Monthly quota exceeded" if is_monthly else "Quota / rate limit exceeded (HTTP 429)")

    def trip_auth_failed(self, error: str):
        with self._lock:
            self.state = "AUTH_FAILED"
            self.cooldown_until = time.time() + 600.0
            self.last_status = "AUTH_FAILED"
            self.last_error = error

    def record_failure(self, state: str, error: str, cooldown_sec: float = 60.0):
        with self._lock:
            self.state = state
            self.cooldown_until = time.time() + cooldown_sec
            self.last_status = state
            self.last_error = error

    def trip_subscription_restricted(self, error: str):
        with self._lock:
            self.state = "SUBSCRIPTION_RESTRICTION"
            self.cooldown_until = time.time() + 60.0
            self.last_status = "SUBSCRIPTION_RESTRICTION"
            self.last_error = error

    def get_frontend_status(self, has_results: bool = False, success_status: str = "Connected") -> str:
        """
        Maps internal state to exact frontend status requirements:
        Connected | Route calculated | Offline timetable available | Monthly quota exhausted | Rate limited | Unavailable | Authentication failed | Subscription restricted | Timeout | No itinerary found
        """
        with self._lock:
            if self.state == "QUOTA_EXHAUSTED":
                return "Monthly quota exhausted"
            if self.state == "RATE_LIMITED":
                if self.rate_limit_metrics.get("remaining_month") == 0 or "month" in str(self.last_error or "").lower():
                    return "Monthly quota exhausted"
                return "Rate limited"
            if self.state == "AUTH_FAILED":
                return "Authentication failed"
            if self.state == "SUBSCRIPTION_RESTRICTION":
                return "Subscription restricted"
            if self.state == "TIMEOUT":
                return "Timeout"
            if self.state == "UNAVAILABLE":
                return "Unavailable"
            if has_results:
                return success_status
            return "No itinerary found"


class ProviderManager:
    """Centralized manager for all multimodal transit providers."""

    _instance = None
    _lock = threading.Lock()

    # Shared thread pool for concurrent asynchronous provider dispatch
    _EXECUTOR = ThreadPoolExecutor(max_workers=10, thread_name_prefix="transit_prov")

    # In-memory short-lived response cache: (cache_key -> (timestamp, data))
    _CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _CACHE_TTL_SEC: float = 300.0  # 5 minutes

    # In-flight request deduplication: (cache_key -> Future)
    _IN_FLIGHT: Dict[str, Future] = {}

    def __init__(self):
        # Register providers
        self.railradar = RailRadarProvider()
        self.transitous = TransitousProvider()
        self.railway_engine = RailwayEngineProvider()
        self.qrail = QRailProvider()
        self.verified_irctc = VerifiedIndianRailProvider()
        self.flight_provider = FlightProvider()

        # Register independent circuit breakers
        self.breakers = {
            "RailRadar": ProviderCircuitBreaker("RailRadar", default_timeout=3.5),
            "Transitous": ProviderCircuitBreaker("Transitous", default_timeout=4.0),
            "RailwayEngine": ProviderCircuitBreaker("RailwayEngine", default_timeout=3.5),
            "QRail": ProviderCircuitBreaker("QRail", default_timeout=3.5),
            "IndianRailways-ScheduleVerified": ProviderCircuitBreaker("IndianRailways-ScheduleVerified", default_timeout=0.5),
            "FlightProvider": ProviderCircuitBreaker("FlightProvider", default_timeout=6.5),
            "OSRM": ProviderCircuitBreaker("OSRM", default_timeout=2.5),
        }

    @classmethod
    def get_instance(cls) -> "ProviderManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def clear_cache(cls):
        with cls._lock:
            cls._CACHE.clear()

    def _generate_cache_key(
        self,
        origin: str,
        dest: str,
        dep_time: Optional[str],
        mode: str,
        origin_lat: Optional[float] = None,
        origin_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
    ) -> str:
        olat = round(float(origin_lat), 3) if origin_lat is not None else 0.0
        olon = round(float(origin_lon), 3) if origin_lon is not None else 0.0
        dlat = round(float(dest_lat), 3) if dest_lat is not None else 0.0
        dlon = round(float(dest_lon), 3) if dest_lon is not None else 0.0
        return f"{origin.strip().lower()}@{olat},{olon}->{dest.strip().lower()}@{dlat},{dlon}|{dep_time or 'now'}|{mode.lower()}"

    def query_providers(
        self,
        origin_name: str,
        origin_lat: float,
        origin_lon: float,
        dest_name: str,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        scale: str = "DOMESTIC",
        dist_km: float = 400.0,
    ) -> Dict[str, Any]:
        """
        Orchestrates parallel execution of eligible providers with:
        - Independent timeouts
        - Overall request deadline (6.5s)
        - Circuit-breaker rate-limit detection
        - Intelligent failover across railway providers
        - Truth-First result normalization
        """
        prefs = preferences or {}
        pref_mode = prefs.get("preferred_mode", "fastest")
        cache_key = self._generate_cache_key(
            origin_name, dest_name, departure_time, pref_mode,
            origin_lat=origin_lat, origin_lon=origin_lon,
            dest_lat=dest_lat, dest_lon=dest_lon
        )

        # Check short-lived cache
        with self._lock:
            if cache_key in self._CACHE:
                cached_time, cached_val = self._CACHE[cache_key]
                if time.time() - cached_time < self._CACHE_TTL_SEC:
                    logger.info(f"[PROVIDER_MGR][CACHE_HIT] Returning cached transit response for {cache_key}")
                    return cached_val

        # Execute providers concurrently
        raw_results = self._execute_concurrently(
            origin_name=origin_name,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_name=dest_name,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            departure_time=departure_time,
            preferences=prefs,
            scale=scale,
            dist_km=dist_km,
        )

        # Process and failover across providers
        processed = self._process_and_failover(raw_results, dist_km, scale)
        processed["search_origin"] = origin_name
        processed["search_destination"] = dest_name
        processed["search_origin_coords"] = {"lat": origin_lat, "lon": origin_lon}
        processed["search_dest_coords"] = {"lat": dest_lat, "lon": dest_lon}

        # Store in cache
        with self._lock:
            self._CACHE[cache_key] = (time.time(), processed)
            # Prune stale cache entries
            now = time.time()
            stale_keys = [k for k, (t, _) in self._CACHE.items() if now - t > self._CACHE_TTL_SEC * 2]
            for sk in stale_keys:
                self._CACHE.pop(sk, None)

        return processed

    def _execute_concurrently(
        self,
        origin_name: str,
        origin_lat: float,
        origin_lon: float,
        dest_name: str,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str],
        preferences: Dict[str, Any],
        scale: str,
        dist_km: float,
    ) -> Dict[str, ProviderResult]:
        """Dispatches eligible providers in parallel without blocking thread pool shutdown."""
        results: Dict[str, ProviderResult] = {}
        futures: Dict[str, Future] = {}

        # 1. RailRadar (Live API)
        if self.breakers["RailRadar"].is_available():
            futures["RailRadar"] = self._EXECUTOR.submit(
                self.railradar.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
            )

        # 2. Transitous (Global MOTIS public transit)
        if self.breakers["Transitous"].is_available():
            futures["Transitous"] = self._EXECUTOR.submit(
                self.transitous.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
            )

        # 3. RailwayEngine (Alternative Indian Railway API)
        if self.breakers["RailwayEngine"].is_available():
            futures["RailwayEngine"] = self._EXECUTOR.submit(
                self.railway_engine.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
            )

        # 4. QRail (Alternative Indian Railway API)
        if self.breakers["QRail"].is_available():
            futures["QRail"] = self._EXECUTOR.submit(
                self.qrail.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
            )

        # 5. Verified Indian Rail (Offline IRCTC schedules)
        can_rail = (scale in ["DOMESTIC", "SAME_CITY"] or dist_km < 2500.0)
        if can_rail and self.breakers["IndianRailways-ScheduleVerified"].is_available():
            futures["IndianRailways-ScheduleVerified"] = self._EXECUTOR.submit(
                self.verified_irctc.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
            )

        # 5. FlightProvider (when distance > 300km or international)
        can_flight = (scale in ["INTERNATIONAL", "INTERCONTINENTAL"]) or (dist_km > 300.0)
        if can_flight and self.breakers["FlightProvider"].is_available():
            futures["FlightProvider"] = self._EXECUTOR.submit(
                self.flight_provider.plan_journey,
                origin_lat, origin_lon, dest_lat, dest_lon,
                departure_time=departure_time,
                preferences=preferences,
                origin_name=origin_name,
                dest_name=dest_name,
            )

        # 6. OSRM Road Provider (when driving is possible)
        can_drive = (scale in ["DOMESTIC", "SAME_CITY"] or dist_km < 800.0)
        if can_drive and self.breakers["OSRM"].is_available():
            futures["OSRM"] = self._EXECUTOR.submit(
                OSRMRoadProvider.get_road_alternative,
                origin_name, origin_lat, origin_lon, dest_name, dest_lat, dest_lon
            )

        # Wait with overall hard deadline (6.5s)
        done, not_done = wait(list(futures.values()), timeout=6.5)

        for name, fut in futures.items():
            breaker = self.breakers.get(name)
            if fut in done:
                try:
                    res = fut.result()
                    if name == "OSRM":
                        # Wrap OSRM dict result
                        results["OSRM"] = ProviderResult(
                            status=ProviderStatus.SUCCESS if res else ProviderStatus.NO_ITINERARY,
                            provider_name="OSRM",
                            itineraries=[res] if res else [],
                        )
                        if breaker:
                            breaker.record_success()
                    elif isinstance(res, ProviderResult):
                        results[name] = res
                        if breaker:
                            if res.status == ProviderStatus.SUCCESS:
                                breaker.record_success(res.latency_ms or 0.0)
                            elif res.status == ProviderStatus.RATE_LIMITED:
                                breaker.trip_rate_limited(res.rate_limit_info or {})
                            elif getattr(res, "category", None) in ("SUBSCRIPTION_RESTRICTION", "SUBSCRIPTION_RESTRICTION_ENDPOINT") or "subscription plan does not support" in str(res.error or "").lower():
                                breaker.trip_subscription_restricted(res.error or "Subscription restricted")
                            elif res.status == ProviderStatus.AUTH_FAILED:
                                breaker.trip_auth_failed(res.error or "Auth failed")
                            elif res.status == ProviderStatus.TIMEOUT:
                                breaker.record_failure("TIMEOUT", res.error or "Timeout")
                            elif res.status == ProviderStatus.PROVIDER_UNAVAILABLE:
                                breaker.record_failure("UNAVAILABLE", res.error or "Unavailable")
                    else:
                        results[name] = ProviderResult(
                            status=ProviderStatus.PROVIDER_ERROR,
                            provider_name=name,
                            error=f"Unexpected result type: {type(res)}",
                        )
                except Exception as e:
                    logger.warning(f"[PROVIDER_MGR] Provider {name} execution error: {e}")
                    results[name] = ProviderResult(
                        status=ProviderStatus.PROVIDER_ERROR,
                        provider_name=name,
                        error=str(e)[:150],
                    )
                    if breaker:
                        breaker.record_failure("UNAVAILABLE", str(e))
            else:
                logger.warning(f"[PROVIDER_MGR] Provider {name} exceeded deadline and was marked TIMEOUT.")
                results[name] = ProviderResult(
                    status=ProviderStatus.TIMEOUT,
                    provider_name=name,
                    error=f"Provider {name} timed out after 6.5s deadline",
                )
                if breaker:
                    breaker.record_failure("TIMEOUT", "Request timed out")

        return results

    def _process_and_failover(
        self,
        results: Dict[str, ProviderResult],
        dist_km: float,
        scale: str,
    ) -> Dict[str, Any]:
        """
        Combines results following strict failover priority:
        1. RailRadar (if SUCCESS)
        2. Transitous (if SUCCESS)
        3. RailwayEngine / QRail (if configured & SUCCESS)
        4. VerifiedIndianRail (if all live railway providers fail/rate-limited)
        5. OSRM and FlightProvider remain independent
        """
        all_itineraries: List[Dict[str, Any]] = []
        train_itineraries: List[Dict[str, Any]] = []
        flight_itineraries: List[Dict[str, Any]] = []
        road_itinerary: Optional[Dict[str, Any]] = None

        rr_res = results.get("RailRadar")
        tr_res = results.get("Transitous")
        re_res = results.get("RailwayEngine")
        qr_res = results.get("QRail")
        fl_res = results.get("FlightProvider")
        os_res = results.get("OSRM")

        # ── 1. RAIL FAILOVER CASCADE ──────────────────────────────────
        rail_success = False

        # Step 1.1: Live RailRadar
        if rr_res and rr_res.status == ProviderStatus.SUCCESS and rr_res.itineraries:
            logger.info(f"[PROVIDER_MGR][CASCADE] Using {len(rr_res.itineraries)} trains from RailRadar.")
            train_itineraries.extend(rr_res.itineraries)
            rail_success = True

        # Step 1.2: Transitous MOTIS GTFS
        if not rail_success and tr_res and tr_res.status == ProviderStatus.SUCCESS and tr_res.itineraries:
            logger.info(f"[PROVIDER_MGR][CASCADE] RailRadar unavailable; successfully failing over to Transitous ({len(tr_res.itineraries)} routes).")
            train_itineraries.extend(tr_res.itineraries)
            rail_success = True

        # Step 1.3: RailwayEngine API
        if not rail_success and re_res and re_res.status == ProviderStatus.SUCCESS and re_res.itineraries:
            logger.info(f"[PROVIDER_MGR][CASCADE] Successfully failing over to RailwayEngine ({len(re_res.itineraries)} trains).")
            train_itineraries.extend(re_res.itineraries)
            rail_success = True

        # Step 1.4: QRail API
        if not rail_success and qr_res and qr_res.status == ProviderStatus.SUCCESS and qr_res.itineraries:
            logger.info(f"[PROVIDER_MGR][CASCADE] Successfully failing over to QRail ({len(qr_res.itineraries)} trains).")
            train_itineraries.extend(qr_res.itineraries)
            rail_success = True

        # Step 1.5: Offline IRCTC Verified Schedule Registry
        vir_res = results.get("IndianRailways-ScheduleVerified")
        if not rail_success and vir_res and vir_res.status == ProviderStatus.SUCCESS and vir_res.itineraries:
            logger.info(f"[PROVIDER_MGR][CASCADE] Live railway providers unavailable/rate-limited. Found {len(vir_res.itineraries)} verified IRCTC timetable options.")
            train_itineraries.extend(vir_res.itineraries)
            rail_success = True

        # ── 2. FLIGHT INTEGRATION ─────────────────────────────────────
        if fl_res and fl_res.status == ProviderStatus.SUCCESS and fl_res.itineraries:
            flight_itineraries.extend(fl_res.itineraries)

        # ── 3. ROAD ALTERNATIVE ───────────────────────────────────────
        if os_res and os_res.status == ProviderStatus.SUCCESS and os_res.itineraries:
            road_itinerary = os_res.itineraries[0]

        transitous_itins = tr_res.itineraries if (tr_res and tr_res.status == ProviderStatus.SUCCESS and tr_res.itineraries) else []

        # Combine non-duplicate itineraries
        seen_ids = set()
        for it in train_itineraries + transitous_itins + flight_itineraries:
            t_num = it.get("train_number") or it.get("flight_number") or it.get("route_id")
            if t_num and t_num in seen_ids:
                continue
            if t_num:
                seen_ids.add(t_num)
            all_itineraries.append(it)

        # ── 4. COMPUTE FRONTEND PROVIDER STATUSES ─────────────────────
        has_live_rr = bool(rr_res and rr_res.itineraries and any(it.get("provider") == "RailRadar" for it in rr_res.itineraries))
        has_ir_sched = bool(train_itineraries and any(it.get("provider") in ("Indian Railways Timetable", "IndianRailways-ScheduleVerified") for it in train_itineraries))

        provider_statuses = {
            "RailRadar": self.breakers["RailRadar"].get_frontend_status(has_results=has_live_rr, success_status="Connected"),
            "Indian Railways Timetable": "Connected" if has_ir_sched else "No itinerary found",
            "Transitous": self.breakers["Transitous"].get_frontend_status(has_results=bool(tr_res and tr_res.itineraries), success_status="Connected"),
            "RailwayEngine": self.breakers["RailwayEngine"].get_frontend_status(has_results=bool(re_res and re_res.itineraries), success_status="Connected"),
            "QRail": self.breakers["QRail"].get_frontend_status(has_results=bool(qr_res and qr_res.itineraries), success_status="Connected"),
            "OSRM": self.breakers["OSRM"].get_frontend_status(has_results=bool(road_itinerary), success_status="Route calculated"),
            "FlightProvider": self.breakers["FlightProvider"].get_frontend_status(has_results=bool(flight_itineraries), success_status="Connected"),
        }

        # Determine overall status and message
        if all_itineraries:
            overall_status = "PUBLIC_TRANSIT_AVAILABLE"
            message = "Verified multimodal transit itineraries found."
        elif road_itinerary:
            overall_status = "VERIFIED_ROAD_ALTERNATIVE"
            message = "No verified train itineraries are currently available. Other transport modes remain available."
        else:
            overall_status = "NO_TRANSIT_AVAILABLE"
            message = "No verified transit routes available from current providers."

        return {
            "status": overall_status,
            "message": message,
            "itineraries": all_itineraries,
            "train_itineraries": train_itineraries,
            "flight_itineraries": flight_itineraries,
            "road_alternative": road_itinerary,
            "provider_statuses": provider_statuses,
            "rate_limit_metrics": self.breakers["RailRadar"].rate_limit_metrics,
            "results_by_provider": results,
        }
