from .weather_service import get_route_weather, get_weather_warnings
from .traffic_service import get_traffic_and_delays
from .cost_service import get_budget_optimization, get_cost_breakdown
from .carbon_service import get_carbon_footprint
from .safety_service import get_safety_intelligence
from .nearby_service import get_nearby_essentials, get_dynamic_alerts
from .offline_package_service import generate_offline_package
from .route_optimizer import optimize_routes
import random

class SmartTransitService:
    @staticmethod
    def generate_smart_route(origin: str, destination: str, preferred_mode: str, budget: int):
        # Determine the best route based on preferred_mode
        routes = optimize_routes(origin, destination, preferred_mode, budget)
        best_route = routes[0]
        
        # Timeline generation based on best_route mode
        timeline = [
            {"time": "7:00 AM", "action": "Leave Home", "type": "departure"},
            {"time": "7:45 AM", "action": f"Reach {best_route['mode']} Terminal", "type": "transit"},
            {"time": "9:20 AM", "action": f"Board {best_route['mode']}", "type": "board"},
            {"time": "2:10 PM", "action": "Arrival", "type": "arrival"},
            {"time": "3:00 PM", "action": "Taxi to Hotel", "type": "transit"},
            {"time": "3:30 PM", "action": "Hotel Check-in", "type": "destination"}
        ]
        
        # Build comprehensive AI response
        return {
            "hero_card": {
                "recommended_mode": best_route["mode"] + (" + Taxi" if best_route["mode"] == "Flight" else ""),
                "confidence": best_route["score"],
                "travel_time": best_route["time_str"],
                "estimated_cost": best_route["cost_inr"],
                "carbon": best_route["carbon_rating"],
                "safety": "Very High",
                "weather": "Clear",
                "delay_risk": "Low",
                "reason": "Fastest route within your budget." if preferred_mode == "Fastest" else f"Optimized for {preferred_mode}."
            },
            "score_breakdown": {
                "overall": best_route["score"],
                "time": 30,
                "budget": 20,
                "safety": 20,
                "comfort": 10,
                "weather": 10,
                "carbon": 10
            },
            "timeline": timeline,
            "multimodal_comparison": routes
        }

    @staticmethod
    def get_full_transit_intelligence(origin: str, destination: str, cost: int):
        return {
            "weather": get_route_weather(origin, destination),
            "warnings": get_weather_warnings(origin, destination),
            "traffic": get_traffic_and_delays(origin, destination),
            "budget": get_budget_optimization(origin, destination, cost),
            "cost_breakdown": get_cost_breakdown(cost),
            "carbon": get_carbon_footprint(origin, destination),
            "safety": get_safety_intelligence(destination),
            "nearby": get_nearby_essentials(destination),
            "alerts": get_dynamic_alerts(destination),
            "offline": generate_offline_package(origin, destination)
        }
