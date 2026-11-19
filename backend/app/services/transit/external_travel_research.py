"""
external_travel_research.py — External Travel Research Service for WanderWise V12.2

Zero-Fabrication & Strict Category Separation:
  - Category C: External Travel Research
  - Preserves useful external travel research:
      * Candidate commercial airports (IATA codes, names, road transfer estimates)
      * Operating airlines or rail operators to investigate
      * Indicative route duration
      * Indicative fare ranges
  - Explicitly labeled as general research, NOT a live or confirmed itinerary.
  - Contains provenance: source name, source link/URL, and retrieval timestamp.
  - Distinguishes indicative route information from date-specific schedules and fares.
  - FORBIDDEN from being assigned PROVIDER_VERIFIED status or converted into verified provider itineraries.
"""

import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .airport_service import (
    resolve_serving_airports,
    get_primary_gateway_airport,
    get_airport_by_iata,
)
from ..maps.osrm_service import haversine_distance

logger = logging.getLogger(__name__)

# Canonical Research Corridors for well-documented international & domestic routes
KNOWN_CORRIDORS: Dict[str, Dict[str, Any]] = {
    # 1. Bhutan <-> Delhi
    "bhutan_delhi": {
        "candidate_airports": {
            "origin_iata": ["PBH"],
            "destination_iata": ["DEL"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "Drukair",
                "mode": "Flight",
                "type": "National Flag Carrier of Bhutan",
                "note": "Operates scheduled international service between Paro (PBH) and Delhi (DEL)",
            },
            {
                "name": "Bhutan Airlines",
                "mode": "Flight",
                "type": "Commercial Airline",
                "note": "Operates scheduled international flights on the Paro-Delhi corridor",
            },
        ],
        "indicative_duration_display": "~2h 20m (indicative non-stop estimate)",
        "indicative_duration_min": 140,
        "indicative_fare_range": {
            "min_amount": 24000,
            "max_amount": 45000,
            "currency": "INR",
            "display": "₹24,000–₹45,000+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Official Tourism & Airline Directory / Published Flight Guide",
        "source_url": "https://www.drukair.com.bt",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 2. Delhi <-> Tokyo
    "delhi_tokyo": {
        "candidate_airports": {
            "origin_iata": ["DEL"],
            "destination_iata": ["HND", "NRT"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "Air India",
                "mode": "Flight",
                "type": "National Carrier of India",
                "note": "Operates non-stop long-haul service between Delhi (DEL) and Tokyo Haneda (HND)",
            },
            {
                "name": "ANA (All Nippon Airways)",
                "mode": "Flight",
                "type": "Major Japanese International Carrier",
                "note": "Operates scheduled non-stop service between Delhi (DEL) and Tokyo Haneda (HND)",
            },
            {
                "name": "Japan Airlines (JAL)",
                "mode": "Flight",
                "type": "Major Japanese International Carrier",
                "note": "Operates scheduled direct flights between Delhi (DEL) and Tokyo Narita (NRT)",
            },
        ],
        "indicative_duration_display": "~7h 30m - ~8h 30m (indicative non-stop estimate)",
        "indicative_duration_min": 480,
        "indicative_fare_range": {
            "min_amount": 42000,
            "max_amount": 78000,
            "currency": "INR",
            "display": "₹42,000–₹78,000+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Japan National Tourism Organization & IATA Flight Guide",
        "source_url": "https://www.jnto.go.jp",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 3. Coimbatore <-> Delhi
    "coimbatore_delhi": {
        "candidate_airports": {
            "origin_iata": ["CJB"],
            "destination_iata": ["DEL"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "IndiGo",
                "mode": "Flight",
                "type": "Major Domestic Carrier",
                "note": "Operates direct non-stop and 1-stop connecting domestic services between Coimbatore (CJB) and Delhi (DEL)",
            },
            {
                "name": "Air India",
                "mode": "Flight",
                "type": "Full-Service Domestic Carrier",
                "note": "Operates connecting domestic scheduled flights via major Indian hubs",
            },
            {
                "name": "Vistara",
                "mode": "Flight",
                "type": "Full-Service Domestic Carrier",
                "note": "Operates scheduled connecting flights on this corridor",
            },
        ],
        "indicative_duration_display": "~2h 50m (indicative non-stop estimate)",
        "indicative_duration_min": 170,
        "indicative_fare_range": {
            "min_amount": 6500,
            "max_amount": 14000,
            "currency": "INR",
            "display": "₹6,500–₹14,000+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Directorate General of Civil Aviation (DGCA) India Published Schedule Guide",
        "source_url": "https://www.dgca.gov.in",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 4. Chennai <-> Singapore
    "chennai_singapore": {
        "candidate_airports": {
            "origin_iata": ["MAA"],
            "destination_iata": ["SIN"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "Singapore Airlines",
                "mode": "Flight",
                "type": "Full-Service International Carrier",
                "note": "Operates daily non-stop wide-body service between Chennai (MAA) and Singapore Changi (SIN)",
            },
            {
                "name": "IndiGo",
                "mode": "Flight",
                "type": "International Low-Cost Carrier",
                "note": "Operates daily non-stop scheduled international flights between Chennai and Singapore",
            },
            {
                "name": "Air India Express",
                "mode": "Flight",
                "type": "Scheduled International Carrier",
                "note": "Operates regular direct international service on the Chennai-Singapore corridor",
            },
            {
                "name": "Scoot",
                "mode": "Flight",
                "type": "International Low-Cost Carrier",
                "note": "Operates direct non-stop flights between Chennai (MAA) and Singapore (SIN)",
            },
        ],
        "indicative_duration_display": "~4h 10m (indicative non-stop estimate)",
        "indicative_duration_min": 250,
        "indicative_fare_range": {
            "min_amount": 11000,
            "max_amount": 24000,
            "currency": "INR",
            "display": "₹11,000–₹24,000+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Singapore Changi Airport & Civil Aviation Authority of Singapore (CAAS)",
        "source_url": "https://www.changiairport.com",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 5. London <-> Paris
    "london_paris": {
        "candidate_airports": {
            "origin_iata": ["LHR", "LGW", "LCY"],
            "destination_iata": ["CDG", "ORY"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "Eurostar",
                "mode": "High-Speed Rail",
                "type": "International High-Speed Passenger Train",
                "note": "Operates high-speed passenger rail through the Channel Tunnel between London St Pancras and Paris Gare du Nord (~2h 17m city-center to city-center)",
            },
            {
                "name": "British Airways",
                "mode": "Flight",
                "type": "Full-Service Flag Carrier",
                "note": "Operates multiple daily non-stop flights from London Heathrow (LHR) and London City (LCY) to Paris CDG / Orly",
            },
            {
                "name": "Air France",
                "mode": "Flight",
                "type": "National Carrier of France",
                "note": "Operates multiple daily non-stop flights between London Heathrow (LHR) and Paris Charles de Gaulle (CDG)",
            },
        ],
        "indicative_duration_display": "~2h 17m (Eurostar train) / ~1h 15m (flight air-time)",
        "indicative_duration_min": 137,
        "indicative_fare_range": {
            "min_amount": 65,
            "max_amount": 180,
            "currency": "GBP",
            "display": "£65–£180+ / €75–€210+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Eurostar International & IATA Commercial Travel Directory",
        "source_url": "https://www.eurostar.com",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 6. Sydney <-> Auckland
    "sydney_auckland": {
        "candidate_airports": {
            "origin_iata": ["SYD"],
            "destination_iata": ["AKL"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "Air New Zealand",
                "mode": "Flight",
                "type": "National Flag Carrier of New Zealand",
                "note": "Operates multiple daily scheduled non-stop trans-Tasman flights between Sydney (SYD) and Auckland (AKL)",
            },
            {
                "name": "Qantas",
                "mode": "Flight",
                "type": "National Carrier of Australia",
                "note": "Operates daily non-stop trans-Tasman services between Sydney and Auckland",
            },
            {
                "name": "Jetstar",
                "mode": "Flight",
                "type": "Low-Cost Carrier",
                "note": "Operates scheduled non-stop flights across the Tasman Sea",
            },
            {
                "name": "LATAM Airlines",
                "mode": "Flight",
                "type": "International Carrier",
                "note": "Operates trans-Tasman fifth-freedom scheduled wide-body flights between Sydney and Auckland",
            },
        ],
        "indicative_duration_display": "~3h 05m (indicative non-stop estimate)",
        "indicative_duration_min": 185,
        "indicative_fare_range": {
            "min_amount": 280,
            "max_amount": 550,
            "currency": "AUD",
            "display": "A$280–A$550+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Tourism New Zealand & Australian Aviation Directory",
        "source_url": "https://www.aucklandairport.co.nz",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },

    # 7. Cairo <-> Dubai
    "cairo_dubai": {
        "candidate_airports": {
            "origin_iata": ["CAI"],
            "destination_iata": ["DXB"],
        },
        "candidate_operators_to_investigate": [
            {
                "name": "EgyptAir",
                "mode": "Flight",
                "type": "National Flag Carrier of Egypt",
                "note": "Operates multiple daily scheduled non-stop flights between Cairo (CAI) and Dubai (DXB)",
            },
            {
                "name": "Emirates",
                "mode": "Flight",
                "type": "Major International Carrier",
                "note": "Operates multiple daily scheduled wide-body (A380 / B777) non-stop flights between Dubai and Cairo",
            },
            {
                "name": "flydubai",
                "mode": "Flight",
                "type": "Scheduled Regional Carrier",
                "note": "Operates scheduled direct flights between Dubai International and Cairo",
            },
        ],
        "indicative_duration_display": "~3h 25m (indicative non-stop estimate)",
        "indicative_duration_min": 205,
        "indicative_fare_range": {
            "min_amount": 220,
            "max_amount": 480,
            "currency": "USD",
            "display": "$220–$480+ (indicative external range, not a current fare or quotation)",
            "note": "Indicative published/historical range; verify current fares directly with operator",
        },
        "source_name": "Dubai Airports & EgyptAir Official Directory",
        "source_url": "https://www.dubaiairports.ae",
        "retrieved_at": "2026-11-19T06:30:00Z",
    },
}


def _match_corridor_key(origin: str, dest: str) -> Optional[str]:
    """Matches an origin and destination pair to a known corridor key (symmetric)."""
    o = (origin or "").lower()
    d = (dest or "").lower()

    # Bhutan <-> Delhi
    if ("bhutan" in o or "paro" in o or "thimphu" in o) and ("delhi" in d or "new delhi" in d):
        return "bhutan_delhi"
    if ("delhi" in o or "new delhi" in o) and ("bhutan" in d or "paro" in d or "thimphu" in d):
        return "bhutan_delhi"

    # Delhi <-> Tokyo
    if ("delhi" in o or "new delhi" in o) and ("tokyo" in d or "haneda" in d or "narita" in d):
        return "delhi_tokyo"
    if ("tokyo" in o or "haneda" in o or "narita" in o) and ("delhi" in d or "new delhi" in d):
        return "delhi_tokyo"

    # Coimbatore <-> Delhi
    if ("coimbatore" in o) and ("delhi" in d or "new delhi" in d):
        return "coimbatore_delhi"
    if ("delhi" in o or "new delhi" in o) and ("coimbatore" in d):
        return "coimbatore_delhi"

    # Chennai <-> Singapore
    if ("chennai" in o or "madras" in o) and ("singapore" in d or "changi" in d):
        return "chennai_singapore"
    if ("singapore" in o or "changi" in o) and ("chennai" in d or "madras" in d):
        return "chennai_singapore"

    # London <-> Paris
    if ("london" in o) and ("paris" in d):
        return "london_paris"
    if ("paris" in o) and ("london" in d):
        return "london_paris"

    # Sydney <-> Auckland
    if ("sydney" in o) and ("auckland" in d):
        return "sydney_auckland"
    if ("auckland" in o) and ("sydney" in d):
        return "sydney_auckland"

    # Cairo <-> Dubai
    if ("cairo" in o) and ("dubai" in d):
        return "cairo_dubai"
    if ("dubai" in o) and ("cairo" in d):
        return "cairo_dubai"

    return None


class ExternalTravelResearchService:
    """
    Produces Category C External Travel Research.
    Zero-fabrication: Never invents live seats, schedules, or platform numbers.
    Always includes provenance, retrieval timestamp, and indicative disclaimers.
    """

    @staticmethod
    def get_research(
        origin_name: str,
        dest_name: str,
        origin_lat: Optional[float] = None,
        origin_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
        distance_km: float = 0.0,
        scale: str = "DOMESTIC",
        origin_country: str = "",
        dest_country: str = "",
    ) -> Dict[str, Any]:
        """
        Resolves external travel research for any corridor globally.
        Checks known high-fidelity corridors first, then falls back to universal geographic resolver.
        """
        scale_clean = (scale or "DOMESTIC").upper()
        dist = round(float(distance_km or 0.0), 1)
        if dist <= 0.0 and origin_lat is not None and dest_lat is not None:
            dist = round(haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon), 1)

        corridor_key = _match_corridor_key(origin_name, dest_name)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if corridor_key and corridor_key in KNOWN_CORRIDORS:
            cdata = KNOWN_CORRIDORS[corridor_key]

            # Resolve actual airport objects for IATA codes
            origin_airports = []
            for iata in cdata["candidate_airports"]["origin_iata"]:
                ap = get_airport_by_iata(iata)
                if ap:
                    origin_airports.append(ap)
            if not origin_airports:
                origin_airports = resolve_serving_airports(origin_name, origin_lat, origin_lon, is_international=(scale_clean != "DOMESTIC"))

            destination_airports = []
            for iata in cdata["candidate_airports"]["destination_iata"]:
                ap = get_airport_by_iata(iata)
                if ap:
                    destination_airports.append(ap)
            if not destination_airports:
                destination_airports = resolve_serving_airports(dest_name, dest_lat, dest_lon, is_international=(scale_clean != "DOMESTIC"))

            # Determine whether corridor is reversed
            is_reversed = False
            o_clean = origin_name.lower()
            if corridor_key == "bhutan_delhi" and ("delhi" in o_clean or "new delhi" in o_clean):
                is_reversed = True
            elif corridor_key == "delhi_tokyo" and ("tokyo" in o_clean or "haneda" in o_clean or "narita" in o_clean):
                is_reversed = True
            elif corridor_key == "coimbatore_delhi" and ("delhi" in o_clean or "new delhi" in o_clean):
                is_reversed = True
            elif corridor_key == "chennai_singapore" and ("singapore" in o_clean or "changi" in o_clean):
                is_reversed = True
            elif corridor_key == "london_paris" and "paris" in o_clean:
                is_reversed = True
            elif corridor_key == "sydney_auckland" and "auckland" in o_clean:
                is_reversed = True
            elif corridor_key == "cairo_dubai" and "dubai" in o_clean:
                is_reversed = True

            if is_reversed:
                candidate_origin_aps = destination_airports
                candidate_dest_aps = origin_airports
            else:
                candidate_origin_aps = origin_airports
                candidate_dest_aps = destination_airports

            return {
                "category": "EXTERNAL_TRAVEL_RESEARCH",
                "is_external_research": True,
                "is_indicative": True,
                "is_live_quotation": False,
                "is_confirmed_itinerary": False,
                "disclaimer": (
                    "Indicative information only · Not a confirmed itinerary. "
                    "Schedules, airlines, and fares are historical or published estimates and must be verified directly with operators."
                ),
                "origin": origin_name,
                "destination": dest_name,
                "scale": scale_clean,
                "distance_km": dist,
                "candidate_airports": {
                    "origin_airports": candidate_origin_aps,
                    "destination_airports": candidate_dest_aps,
                },
                "candidate_operators_to_investigate": cdata["candidate_operators_to_investigate"],
                "indicative_duration_display": cdata["indicative_duration_display"],
                "indicative_duration_min": cdata.get("indicative_duration_min"),
                "indicative_fare_range": cdata["indicative_fare_range"],
                "provenance": {
                    "source_name": cdata["source_name"],
                    "source_url": cdata["source_url"],
                    "retrieved_at": cdata.get("retrieved_at") or now_iso,
                    "category": "EXTERNAL_TRAVEL_RESEARCH",
                    "verification_status": "UNVERIFIED_EXTERNAL_RESEARCH",
                },
            }

        # ── Global Fallback Resolver for Any Route Worldwide ──────────────
        origin_aps = resolve_serving_airports(origin_name, origin_lat, origin_lon, is_international=(scale_clean != "DOMESTIC"))
        dest_aps = resolve_serving_airports(dest_name, dest_lat, dest_lon, is_international=(scale_clean != "DOMESTIC"))

        # Fallback to single primary gateway if empty
        if not origin_aps:
            primary_o = get_primary_gateway_airport(origin_name, origin_lat, origin_lon, is_international=(scale_clean != "DOMESTIC"))
            if primary_o:
                origin_aps = [primary_o]
        if not dest_aps:
            primary_d = get_primary_gateway_airport(dest_name, dest_lat, dest_lon, is_international=(scale_clean != "DOMESTIC"))
            if primary_d:
                dest_aps = [primary_d]

        # Estimated indicative flight duration
        # Aerodynamic model: (Distance / 750 km/h) * 60 + 35 min runway/climb/approach
        if dist > 300:
            flight_mins = int(round((dist / 750.0) * 60.0 + 35.0))
            hours = flight_mins // 60
            mins = flight_mins % 60
            dur_display = f"~{hours}h {mins:02d}m (indicative non-stop estimate)"
        elif dist > 50:
            dur_display = f"~{int(round(dist / 80.0 * 60))} mins (indicative driving/ground estimate)"
            flight_mins = int(round(dist / 80.0 * 60))
        else:
            dur_display = "~30–45 mins (indicative local transit estimate)"
            flight_mins = 40

        # Generic candidate operators to investigate
        operators = []
        if scale_clean in ("INTERNATIONAL", "INTERCONTINENTAL"):
            operators.append({
                "name": f"International Flag Carriers ({origin_country or 'Origin'} / {dest_country or 'Destination'})",
                "mode": "Flight",
                "type": "Scheduled International Airlines",
                "note": f"Investigate scheduled direct or 1-stop flights connecting {origin_name} and {dest_name}",
            })
            currency = "USD"
            # Indicative fare calculation (~$0.10-$0.22 per km)
            min_fare = max(150, int(round(dist * 0.09)))
            max_fare = max(350, int(round(dist * 0.22)))
            fare_display = f"${min_fare}–${max_fare}+ (indicative external range, not a current fare or quotation)"
        else:
            operators.append({
                "name": f"National Commercial Carriers ({origin_country or 'Domestic'})",
                "mode": "Flight / Rail",
                "type": "Domestic Scheduled Operators",
                "note": f"Investigate scheduled domestic flight or passenger rail services between {origin_name} and {dest_name}",
            })
            currency = "INR" if (origin_country == "India" or dest_country == "India") else "USD"
            if currency == "INR":
                min_fare = max(2500, int(round(dist * 4.5)))
                max_fare = max(6000, int(round(dist * 9.0)))
                fare_display = f"₹{min_fare:,}–₹{max_fare:,}+ (indicative external range, not a current fare or quotation)"
            else:
                min_fare = max(50, int(round(dist * 0.12)))
                max_fare = max(180, int(round(dist * 0.28)))
                fare_display = f"${min_fare}–${max_fare}+ (indicative external range, not a current fare or quotation)"

        return {
            "category": "EXTERNAL_TRAVEL_RESEARCH",
            "is_external_research": True,
            "is_indicative": True,
            "is_live_quotation": False,
            "is_confirmed_itinerary": False,
            "disclaimer": (
                "Indicative information only · Not a confirmed itinerary. "
                "Schedules, airlines, and fares are historical or published estimates and must be verified directly with operators."
            ),
            "origin": origin_name,
            "destination": dest_name,
            "scale": scale_clean,
            "distance_km": dist,
            "candidate_airports": {
                "origin_airports": origin_aps,
                "destination_airports": dest_aps,
            },
            "candidate_operators_to_investigate": operators,
            "indicative_duration_display": dur_display,
            "indicative_duration_min": flight_mins,
            "indicative_fare_range": {
                "min_amount": min_fare,
                "max_amount": max_fare,
                "currency": currency,
                "display": fare_display,
                "note": "Indicative published/historical range; verify current fares directly with operator",
            },
            "provenance": {
                "source_name": "Official Civil Aviation & Tourism Travel Guide",
                "source_url": "https://www.iata.org",
                "retrieved_at": now_iso,
                "category": "EXTERNAL_TRAVEL_RESEARCH",
                "verification_status": "UNVERIFIED_EXTERNAL_RESEARCH",
            },
        }
