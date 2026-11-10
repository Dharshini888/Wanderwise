import sys, os, time
sys.path.insert(0, os.path.abspath("backend"))
from dotenv import load_dotenv
load_dotenv("backend/.env")

print(f"[{time.strftime('%X')}] 1. Environment loaded. Gemini key: {bool(os.getenv('GEMINI_API_KEY'))}, Groq key: {bool(os.getenv('GROQ_API_KEY'))}")
from app.services.ai_service import generate_structured_itinerary
print(f"[{time.strftime('%X')}] 2. Calling generate_structured_itinerary...")
t0 = time.time()
res = generate_structured_itinerary(
    destination="Singapore",
    days=6,
    budget=200000.0,
    currency="INR",
    group_size=3,
    interests="Nature, Photography, Adventure, Shopping",
    travel_style="family",
    origin_city="Coimbatore",
    start_date="2026-12-10",
    end_date="2026-12-15",
    trip_preferences={"travelers": {"adults": 2, "children": 1, "child_ages": [10]}}
)
print(f"[{time.strftime('%X')}] 3. Done in {time.time()-t0:.2f}s! Days returned: {len(res.get('days', []))}")
for d in res.get("days", []):
    print(f"Day {d.get('day_number')}: {len(d.get('activities', []))} activities")

