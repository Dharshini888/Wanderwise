from .emergency_service import get_offline_emergency_data
from .ai_memory_engine import track_travel_behavior
from .sustainability_service import get_green_travel_score
from .replanning_engine import replan_itinerary
import uuid

class TripExecutionService:
    @staticmethod
    def start_trip_session(user_id: int, trip_id: int, start_date: str):
        return {
            "session_id": f"TRIP_{uuid.uuid4().hex[:6].upper()}",
            "status": "ACTIVE",
            "current_stage": "Airport Transfer"
        }

    @staticmethod
    def monitor_trip_progress(trip_id: int):
        # Mocked progress for a live trip
        return {
            "current_location": "Coimbatore Airport",
            "next_action": "Board Flight AI 452",
            "time_remaining": "45 mins",
            "timeline": [
                {"status": "completed", "time": "7:00 AM", "action": "Leave Home"},
                {"status": "current", "time": "8:30 AM", "action": "Airport Transfer"},
                {"status": "upcoming", "time": "2:10 PM", "action": "Arrival at Destination"},
                {"status": "upcoming", "time": "4:30 PM", "action": "Uluwatu Sunset Trek"}
            ]
        }

    @staticmethod
    def get_trip_alerts():
        return [
            {
                "type": "WEATHER",
                "severity": "HIGH",
                "title": "Heavy Rain Expected",
                "action": "Carry rain protection"
            },
            {
                "type": "TRAFFIC",
                "severity": "MEDIUM",
                "title": "Airport Road Congestion",
                "action": "Start 30 minutes earlier"
            }
        ]

    @staticmethod
    def generate_offline_pack():
        return {
            "status": "Success",
            "package_name": "WanderWise Offline Pack",
            "contents": [
                "✓ Maps",
                "✓ Hotel Details",
                "✓ Emergency Contacts",
                "✓ Itinerary",
                "✓ Tickets",
                "✓ Language Phrases"
            ]
        }
