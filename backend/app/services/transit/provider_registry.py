"""
provider_registry.py — WanderWise Provider Capability Registry & Fallback Chain

Truth-First Principles:
1. Defines capabilities of all integrated transport providers.
2. Prevents the application from making false claims about live availability.
"""

from typing import Dict, Any, List

PROVIDER_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "OSRM": {
        "provider_name": "OSRM",
        "routing": True,
        "schedule": False,
        "realtime": False,
        "vehicle_position": False,
        "fare": False,
        "traffic_aware": False,
        "default_verification": "PROVIDER_CALCULATED",
        "description": "Calculated road network driving & walking routes via OSRM engine."
    },
    "RailRadar": {
        "provider_name": "RailRadar",
        "routing": True,
        "schedule": True,
        "realtime": True,
        "vehicle_position": True,
        "fare": False,
        "traffic_aware": False,
        "default_verification": "SCHEDULE_VERIFIED",
        "description": "Indian Railways schedule database and live train tracking API."
    },
    "Transitous": {
        "provider_name": "Transitous",
        "routing": True,
        "schedule": True,
        "realtime": "feed_dependent",
        "vehicle_position": False,
        "fare": False,
        "traffic_aware": False,
        "default_verification": "SCHEDULE_VERIFIED",
        "description": "Community-run global public transport routing API."
    },
    "GTFSLocal": {
        "provider_name": "GTFS Local",
        "routing": True,
        "schedule": True,
        "realtime": "feed_dependent",
        "vehicle_position": True,
        "fare": False,
        "traffic_aware": False,
        "default_verification": "SCHEDULE_VERIFIED",
        "description": "Local GTFS static schedules and GTFS-Realtime feeds."
    },
    "FlightProvider": {
        "provider_name": "FlightProvider",
        "routing": True,
        "schedule": True,
        "realtime": False,
        "vehicle_position": False,
        "fare": True,
        "traffic_aware": False,
        "default_verification": "SCHEDULE_VERIFIED",
        "description": "Airline schedule and flight option provider."
    }
}

FALLBACK_CHAIN = [
    {"level": "REALTIME_VERIFIED", "condition": "Live provider telemetry available and fresh (age <= 300s)"},
    {"level": "STALE_REALTIME", "condition": "Live provider telemetry available but age > 300s"},
    {"level": "SCHEDULE_VERIFIED", "condition": "Verified static provider timetable available"},
    {"level": "PROVIDER_CALCULATED", "condition": "OSRM road routing duration/distance calculation"},
    {"level": "UNAVAILABLE", "condition": "No verified provider schedule or routing data available"}
]

def get_provider_capabilities(provider_name: str) -> Dict[str, Any]:
    return PROVIDER_CAPABILITIES.get(provider_name, {
        "provider_name": provider_name,
        "routing": False,
        "schedule": False,
        "realtime": False,
        "vehicle_position": False,
        "fare": False,
        "default_verification": "UNAVAILABLE"
    })
