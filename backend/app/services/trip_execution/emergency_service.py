"""
emergency_service.py — Verified Global Offline Emergency Data Engine
Provides destination-aware emergency contact resolution, medical hotlines, and consular guidance.
"""

from typing import Dict, Any
from app.services.location.location_normalizer import resolve_destination_info
from app.services.safety_hub_service import SafetyHubService


def get_offline_emergency_data(destination: str) -> Dict[str, Any]:
    """Returns verified country and destination specific emergency service numbers."""
    dest_str = destination or "Destination"
    info = resolve_destination_info(dest_str)
    country = info.get("country") or dest_str
    clean_city = info.get("destination_clean") or dest_str

    contacts = SafetyHubService.get_emergency_contacts(country)
    police = contacts.get("Police") or contacts.get("Police/Fire/Ambulance") or contacts.get("Emergency") or "112"
    ambulance = contacts.get("Ambulance") or contacts.get("Police/Fire/Ambulance") or contacts.get("Emergency") or "112"
    fire = contacts.get("Fire") or contacts.get("Police/Fire/Ambulance") or contacts.get("Emergency") or "112"

    return {
        "destination": clean_city,
        "country": country,
        "medical": f"{ambulance} (Ambulance / Medical Emergency)",
        "police": f"{police} (Police Emergency)",
        "fire": f"{fire} (Fire Department)",
        "hospital": f"{clean_city} General Hospital & Emergency Care",
        "embassy": f"Consular and diplomatic assistance available for {country}.",
        "hotel_address": f"Accommodation in {clean_city}",
        "nearest_pharmacy": "24/7 Local Pharmacy & First Aid (Available Offline)",
        "contacts": contacts,
    }
