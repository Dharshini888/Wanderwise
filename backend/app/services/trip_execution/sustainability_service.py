"""
sustainability_service.py — WanderWise Sustainable Travel & Carbon Footprint Service

Calculates estimated CO2 emissions based on travel mode & distance (g CO2 / passenger-km):
- Rail: 35g / km
- Electric Bus: 45g / km
- Driving (Car): 170g / km
- Domestic Flight: 255g / km
"""

from typing import Dict, Any


def get_green_travel_score(mode: str):
    res = SustainabilityService.calculate_trip_carbon(mode, 450.0)
    return {
        "score_stars": res["sustainability_score"],
        "carbon_saved_kg": res["carbon_saved_vs_flight_kg"],
        "better_choice": res["greener_alternative"],
        "equivalent_trees": int(res["carbon_saved_vs_flight_kg"] / 20.0) if res["carbon_saved_vs_flight_kg"] > 0 else 0
    }


class SustainabilityService:
    EMISSIONS_FACTOR_G_PER_KM = {
        "rail": 35.0,
        "train": 35.0,
        "bus": 45.0,
        "car": 170.0,
        "drive": 170.0,
        "flight": 255.0,
        "air": 255.0,
        "walk": 0.0,
    }

    @classmethod
    def calculate_trip_carbon(cls, mode: str, distance_km: float) -> Dict[str, Any]:
        m_lower = (mode or "car").lower()

        factor = 120.0
        for key, val in cls.EMISSIONS_FACTOR_G_PER_KM.items():
            if key in m_lower:
                factor = val
                break

        total_kg = round((factor * distance_km) / 1000.0, 2)
        rail_kg = round((35.0 * distance_km) / 1000.0, 2)
        saved_kg = max(0.0, round(total_kg - rail_kg, 2))

        score_stars = "★★★★★" if factor <= 45.0 else ("★★★☆☆" if factor <= 170.0 else "★☆☆☆☆")

        return {
            "mode": mode,
            "distance_km": distance_km,
            "carbon_emitted_kg": total_kg,
            "carbon_saved_vs_flight_kg": max(0.0, round(((255.0 - factor) * distance_km) / 1000.0, 2)),
            "sustainability_score": score_stars,
            "greener_alternative": "High-Speed Rail or Electric Bus" if factor > 45.0 else "Optimal Green Transit Selected",
            "provenance": "Estimated CO2 calculation based on standard passenger transport emission factors (g CO2/km)",
        }
