import sys, os, json
sys.path.insert(0, os.path.abspath("backend"))

from app.services.ai_service import schedule_unique_multiday_itinerary
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from datetime import date

sched = schedule_unique_multiday_itinerary("Singapore", 6)
fallback_days = []
time_slots = [
    ("08:30", "09:30", "morning", 60),
    ("09:45", "11:45", "morning", 120),
    ("12:00", "13:15", "afternoon", 75),
    ("13:30", "16:00", "afternoon", 150),
    ("16:30", "18:30", "evening", 120)
]
for d in range(1, 7):
    day_info = sched[d]
    acts = []
    for p_idx, poi in enumerate(day_info["pois"]):
        st, et, slot, dur_m = time_slots[min(p_idx, len(time_slots) - 1)]
        acts.append({
            "start_time": st, "end_time": et, "duration_minutes": dur_m, "time_slot": slot,
            "title": f"Explore {poi['name']}",
            "description": poi.get("desc") or f"Experience {poi['name']} in Singapore.",
            "place": {"name": poi['name'], "category": poi.get('category')},
            "cost": {"amount": 0.0, "currency": "INR", "symbol": "Rs", "estimated": False},
            "ticket_price": 0.0,
            "transport_mode": "walking", "transport_duration": "15 mins", "distance": "1.2 km",
            "weather_suitability": "all-weather", "crowd_level": "moderate",
            "ai_reason": f"System selected verified POI matching travel style",
            "confidence_score": 0.98,
            "metadata": {"tips": [f"Enjoy {poi['name']} at your own pace."], "nearby": []}
        })
    fallback_days.append({
        "day_number": d,
        "title": f"Day {d}: Singapore Exploration",
        "theme_note": "Explore unique top attractions",
        "activities": acts
    })

print(f"Fallback days count: {len(fallback_days)}")
for fd in fallback_days:
    print(f"  Day {fd['day_number']}: {len(fd['activities'])} activities")
    for a in fd['activities']:
        print(f"     - {a['title']}")

print("\n--- Validating fallback days with FinalItineraryValidator ---")
is_valid, warnings, validated_days = FinalItineraryValidator.validate_itinerary_payload(
    days_data=fallback_days,
    destination="Singapore",
    start_date=date(2026, 12, 10),
    end_date=date(2026, 12, 15),
    expected_days=6,
    currency="INR"
)
print("Is valid:", is_valid)
print("Warnings:", warnings)
print(f"Validated days: {len(validated_days)}")
for vd in validated_days:
    print(f"  Day {vd['day_number']}: {len(vd['activities'])} activities")
