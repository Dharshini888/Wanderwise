"""
WanderWise Recommendation Engine (Phase 1: Deterministic Rule Engine)
Designed as a modular service that can be swapped with AIRecommendationService in Phase 2
without requiring UI redesign or breaking API contracts.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional


class RuleRecommendationService:
    """Modular rule-based travel assistant recommendation service."""

    @staticmethod
    def calculate_trip_day(start_date: Optional[date], end_date: Optional[date], current_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate current trip day dynamically.
        tripDay = (currentDate - startDate) + 1
        """
        if not current_date:
            current_date = date.today()

        if not start_date or not end_date:
            return {
                "status": "Upcoming",
                "current_trip_day": 1,
                "total_days": 1,
                "day_text": "Day 1 of 1"
            }

        total_days = max(1, (end_date - start_date).days + 1)

        if current_date < start_date:
            days_until = (start_date - current_date).days
            return {
                "status": "Upcoming",
                "current_trip_day": 0,
                "total_days": total_days,
                "days_until_start": days_until,
                "day_text": f"Starts in {days_until} day{'s' if days_until != 1 else ''}"
            }
        elif current_date > end_date:
            return {
                "status": "Completed",
                "current_trip_day": total_days,
                "total_days": total_days,
                "day_text": f"Completed ({total_days} Days)"
            }
        else:
            current_day_number = (current_date - start_date).days + 1
            return {
                "status": "Active",
                "current_trip_day": current_day_number,
                "total_days": total_days,
                "day_text": f"Day {current_day_number} of {total_days}"
            }

    @staticmethod
    def compute_activity_status(
        start_time: str,
        end_time: str,
        is_completed: bool,
        now_dt: Optional[datetime] = None,
        activity_date: Optional[date] = None,
        trip_start_date: Optional[date] = None,
        trip_end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Determine activity status from trip dates and current date/time:
        - If today < tripStartDate: status = 'upcoming' (🔵 Blue)
        - If today > tripEndDate: status = 'completed' if is_completed else 'missed' (🔴 Red)
        - Else (During trip):
            - If is_completed: 'completed' (🟢 Green)
            - Else if activity date/time > now: 'upcoming' (🔵 Blue)
            - Else: 'pending' (🟡 Yellow) if today, or 'missed' (🔴 Red) if past day
        """
        if not now_dt:
            now_dt = datetime.now()

        today = now_dt.date()

        # 1. Before Trip Starts
        if trip_start_date and today < trip_start_date:
            return {
                "status": "upcoming",
                "badge": "Upcoming",
                "color": "blue",
                "countdown": f"Starts on {trip_start_date.strftime('%d %b %Y')}"
            }

        # 2. After Trip Ends
        if trip_end_date and today > trip_end_date:
            if is_completed:
                return {
                    "status": "completed",
                    "badge": "Completed",
                    "color": "emerald",
                    "countdown": "Completed"
                }
            else:
                return {
                    "status": "missed",
                    "badge": "Missed",
                    "color": "rose",
                    "countdown": "Trip ended"
                }

        # 3. During Trip
        if is_completed:
            return {
                "status": "completed",
                "badge": "Completed",
                "color": "emerald",
                "countdown": "Completed"
            }

        cur_mins = now_dt.hour * 60 + now_dt.minute

        def parse_mins(t_str: str, default_val: int) -> int:
            if not t_str:
                return default_val
            try:
                parts = t_str.split(":")
                return int(parts[0]) * 60 + int(parts[1])
            except Exception:
                return default_val

        st_mins = parse_mins(start_time, 9 * 60)
        end_mins = parse_mins(end_time, st_mins + 90)

        if activity_date and activity_date > today:
            return {
                "status": "upcoming",
                "badge": "Upcoming",
                "color": "blue",
                "countdown": f"Scheduled for {activity_date.strftime('%d %b')}"
            }
        elif activity_date and activity_date < today:
            return {
                "status": "missed",
                "badge": "Missed",
                "color": "rose",
                "countdown": "Past day"
            }

        # Activity is for TODAY
        if st_mins <= cur_mins <= end_mins:
            mins_left = end_mins - cur_mins
            return {
                "status": "current",
                "badge": "In Progress",
                "color": "teal",
                "countdown": f"Ends in {mins_left} mins" if mins_left > 0 else "Ending now"
            }
        elif cur_mins < st_mins:
            mins_start = st_mins - cur_mins
            countdown_text = f"Starts in {mins_start} mins" if mins_start <= 60 else f"Starts at {start_time or '09:00'}"
            return {
                "status": "upcoming",
                "badge": "Upcoming",
                "color": "blue",
                "countdown": countdown_text
            }
        else:
            return {
                "status": "pending",
                "badge": "Pending",
                "color": "amber",
                "countdown": "Pending completion"
            }

    @staticmethod
    def get_weather_badge(activity_title: str, category: str, weather_suitability: str, weather_data: Dict[str, Any], start_time: str = "") -> str:
        """Derive weather badge per activity based on place category and live weather."""
        curr = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}
        forecast_0 = (weather_data.get("forecast", [{}]) or [{}])[0] if isinstance(weather_data, dict) else {}

        precip_prob = forecast_0.get("precipitation_probability", 0) or forecast_0.get("precipitation_probability_max", 0) or 0
        temp = curr.get("temperature", 25.0) or 25.0

        title_lower = (activity_title or "").lower()
        cat_lower = (category or "").lower()
        suitability = (weather_suitability or "").lower()

        is_indoor = any(k in title_lower or k in cat_lower for k in ["museum", "cafe", "restaurant", "shopping", "mall", "aquarium", "gallery", "indoor"]) or suitability == "indoor"

        if is_indoor:
            return "🌧️ Rain Friendly"

        if "sunset" in title_lower or "viewpoint" in title_lower or start_time.startswith("17") or start_time.startswith("18"):
            return "🌅 Best at Sunset"

        if precip_prob > 35:
            return "☔ High Rain Risk"

        if temp >= 32.0:
            return "🌡️ Hot Afternoon"

        return "☀️ Good Weather"

    @staticmethod
    def get_crowd_badge(rating: float = 4.5, time_slot: str = "", order_index: int = 1) -> str:
        """Derive crowd level estimation badge."""
        if order_index == 1 or "08:" in time_slot or "09:" in time_slot:
            return "Low"
        elif "12:" in time_slot or "13:" in time_slot or "18:" in time_slot:
            return "High"
        else:
            return "Medium"

    @classmethod
    def generate_weather_recommendations(cls, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured weather travel recommendation & category filters."""
        curr = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}
        forecast_0 = (weather_data.get("forecast", [{}]) or [{}])[0] if isinstance(weather_data, dict) else {}

        precip_prob = forecast_0.get("precipitation_probability", 0) or forecast_0.get("precipitation_probability_max", 0) or 0
        temp = curr.get("temperature", 25.0) or 25.0

        if precip_prob > 40:
            return {
                "headline": f"Heavy rain expected today ({precip_prob}% chance)",
                "summary": "Outdoor activities like cliff walks and beaches have high rain exposure.",
                "recommended": ["Museum", "Local Café", "Shopping Arcade", "Art Gallery"],
                "avoid": ["Beach Walk", "Cliff Viewpoint", "Outdoor Hiking", "Trekking"]
            }
        elif temp >= 32.0:
            return {
                "headline": f"High heat warning ({temp}°C)",
                "summary": "Peak afternoon sun can cause fatigue during outdoor tours.",
                "recommended": ["AC Museum", "Indoor Dining", "Shaded Shopping"],
                "avoid": ["Midday Beach Walk", "Unshaded Hiking"]
            }
        else:
            return {
                "headline": "Pleasant weather conditions for sightseeing",
                "summary": "Great conditions for walking tours, beaches, and scenic viewpoints.",
                "recommended": ["Heritage Walk", "Scenic Viewpoint", "Beach Sunset", "Local Dining"],
                "avoid": []
            }

    @classmethod
    def generate_smart_recommendations(cls, weather_data: Dict[str, Any], today_activities: List[Dict[str, Any]], active_trip: Any) -> Dict[str, Any]:
        """
        Generate actionable smart recommendation cards.
        Structured to allow seamless AI engine integration in Phase 2.
        """
        weather_rec = cls.generate_weather_recommendations(weather_data)
        dest = getattr(active_trip, "destination", "your destination") if active_trip else "destination"

        forecast_0 = (weather_data.get("forecast", [{}]) or [{}])[0] if isinstance(weather_data, dict) else {}
        precip_prob = forecast_0.get("precipitation_probability", 0) or forecast_0.get("precipitation_probability_max", 0) or 0

        if precip_prob > 40:
            return {
                "title": "Smart Rain Advisory",
                "trigger": f"High rain probability ({precip_prob}%) detected",
                "suggested_changes": [
                    "Move Museum & Indoor attractions to Morning (09:45 AM)",
                    "Move Cliff Walk & Viewpoint to Late Afternoon / Sunset",
                    "Lunch & Café stops remain on schedule"
                ],
                "estimated_travel_saved": "22 mins",
                "reasoning": f"Reordering indoor places to earlier morning minimizes rain disruption while preserving sunset views in {dest}."
            }
        else:
            return {
                "title": "Smart Itinerary Optimization",
                "trigger": "Optimal weather window identified",
                "suggested_changes": [
                    "Visit outdoor viewpoints before 11:30 AM for lowest crowd levels",
                    "Schedule indoor dining during peak afternoon heat (01:00 PM)",
                    "Catch sunset at 05:30 PM with clear sky visibility"
                ],
                "estimated_travel_saved": "15 mins",
                "reasoning": f"Sequential route planning reduces backtracking along {dest}."
            }
