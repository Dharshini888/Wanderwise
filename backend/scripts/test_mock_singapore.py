import sys, os, json
sys.path.insert(0, os.path.abspath("backend"))

from app.ai.providers.mock_provider import MockProvider

mp = MockProvider()
prompt = """Destination: Singapore
Origin City: Coimbatore
Total Duration: EXACTLY 6 Days
Target Currency Code: INR
Traveler Composition: 2 Adults, 1 Children
Total Group Size: 3
Interests: Nature, Photography, Adventure, Shopping
Directives: Avoid overcrowded places, include family-friendly activities
Dietary: Vegetarian"""

resp = mp.generate(prompt)
data = json.loads(resp)
trip = data.get("trip", {})
days = trip.get("itinerary_days", [])
print(f"Total days from MockProvider: {len(days)}")
for d in days:
    acts = d.get("activities", [])
    print(f"Day {d.get('day_number')}: {len(acts)} activities")
    for a in acts:
        print(f"   - {a.get('title')} ({a.get('start_time')} - {a.get('end_time')}) | {a.get('formatted_cost')}")

