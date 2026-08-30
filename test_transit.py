import sys
import os

# Ensure backend app is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.transit.transit_orchestrator import TransitOrchestrator

try:
    print("Testing get_transit_plan for Coimbatore -> Tiruppur...")
    result = TransitOrchestrator.get_transit_plan(
        origin="Coimbatore",
        destination="Tiruppur",
        origin_lat=11.0168,
        origin_lon=76.9558,
        dest_lat=11.1085,
        dest_lon=77.3411,
        preferred_mode="best overall",
        budget=5000,
        budget_currency="INR"
    )
    import json
    print(json.dumps(result, indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
