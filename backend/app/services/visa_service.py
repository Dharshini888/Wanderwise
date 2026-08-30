"""
visa_service.py — WanderWise Phase 2 Official Visa Assistant Service

Provides verified visa requirements, stay limits, document checklists, and official portal links
for international country pairs based on verified Timatic / embassy rules.
"""

from typing import Dict, Any, List


class VisaAssistantService:
    """Official Visa & Immigration Guidance Engine."""

    _VISA_DATABASE: Dict[str, Dict[str, Any]] = {
        "IN_GB": {
            "requirement": "Visa Required",
            "status": "VISA_REQUIRED",
            "max_stay_days": 180,
            "application_type": "Standard Visitor Visa (Online Application)",
            "official_portal": "https://www.gov.uk/standard-visitor-visa",
            "documents_required": [
                "Valid Passport (at least 6 months validity)",
                "Proof of sufficient funds (bank statements)",
                "Accommodation booking confirmation",
                "Return flight ticket itinerary",
                "Travel itinerary details",
            ],
            "processing_time": "3 - 6 weeks",
        },
        "IN_FR": {
            "requirement": "Visa Required",
            "status": "VISA_REQUIRED",
            "max_stay_days": 90,
            "application_type": "Schengen Short-Stay Visa",
            "official_portal": "https://france-visas.gouv.fr",
            "documents_required": [
                "Valid Passport & previous visas",
                "Schengen Travel Insurance (€30,000 min coverage)",
                "Flight reservation & hotel bookings",
                "Proof of employment / income",
            ],
            "processing_time": "15 calendar days",
        },
        "IN_JP": {
            "requirement": "eVisa / Visa Required",
            "status": "EVISA",
            "max_stay_days": 90,
            "application_type": "Japan Single-Entry eVisa for Tourism",
            "official_portal": "https://www.evisa.mofa.go.jp",
            "documents_required": [
                "Valid Passport",
                "Digital passport photo",
                "Flight itinerary & day-by-day travel plan",
                "Financial proof / tax returns",
            ],
            "processing_time": "5 working days",
        },
        "IN_TH": {
            "requirement": "Visa-Free / Visa on Arrival",
            "status": "VISA_FREE",
            "max_stay_days": 60,
            "application_type": "Visa Exemption / On Arrival",
            "official_portal": "https://www.immigration.go.th",
            "documents_required": [
                "Valid Passport (6 months validity)",
                "Confirmed return flight ticket within 60 days",
                "Proof of funds (10,000 THB per person)",
            ],
            "processing_time": "Immediate at port of entry",
        },
        "GB_FR": {
            "requirement": "Visa-Free",
            "status": "VISA_FREE",
            "max_stay_days": 90,
            "application_type": "Schengen Visa-Free Access (90 in 180 days)",
            "official_portal": "https://france-visas.gouv.fr",
            "documents_required": [
                "Valid UK Passport",
                "Return flight / ferry ticket",
                "Proof of accommodation",
            ],
            "processing_time": "Immediate at border control",
        },
        "US_JP": {
            "requirement": "Visa-Free",
            "status": "VISA_FREE",
            "max_stay_days": 90,
            "application_type": "Short-Term Tourist Stay",
            "official_portal": "https://www.mofa.go.jp",
            "documents_required": [
                "Valid US Passport",
                "Return flight ticket",
            ],
            "processing_time": "Immediate at immigration",
        },
    }

    @classmethod
    def get_visa_requirements(cls, passport_country: str, destination_country: str) -> Dict[str, Any]:
        """Returns verified visa requirement information for a passport/destination pair."""
        p_code = (passport_country or "IN").upper()[:2]
        d_code = (destination_country or "GB").upper()[:2]

        if p_code == d_code:
            return {
                "passport_country": p_code,
                "destination_country": d_code,
                "requirement": "Domestic Travel (No Visa Required)",
                "status": "DOMESTIC",
                "max_stay_days": 365,
                "application_type": "Domestic / Resident",
                "official_portal": "",
                "documents_required": ["Government issued photo ID / Passport"],
                "processing_time": "Instant",
            }

        pair_key = f"{p_code}_{d_code}"
        data = cls._VISA_DATABASE.get(pair_key)

        if not data:
            # Fallback for unlisted pairs: Mark verification required
            return {
                "passport_country": p_code,
                "destination_country": d_code,
                "requirement": "Verification Required",
                "status": "VERIFICATION_REQUIRED",
                "max_stay_days": 30,
                "application_type": "Standard Embassy Application",
                "official_portal": "https://www.embassy-worldwide.com",
                "documents_required": [
                    "Valid Passport (6 months validity)",
                    "Official Embassy visa application form",
                    "Proof of accommodation & return travel",
                ],
                "processing_time": "Check official embassy portal",
                "note": "Verify exact requirements directly with the destination country embassy before travel.",
            }

        res = dict(data)
        res["passport_country"] = p_code
        res["destination_country"] = d_code
        return res
