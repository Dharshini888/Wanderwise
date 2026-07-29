ITINERARY_PLANNER_PROMPT = """
Use this system prompt when generating structured trip creation or itinerary modification action payloads.

OUTPUT ACTION FORMATS:

1. Create Trip Payload:
{
  "type": "create_itinerary",
  "title": "Create Trip to [Destination]",
  "destination": "[Destination]",
  "duration_days": 5,
  "travel_style": "adventure/solo/family/cultural",
  "estimated_budget": 50000,
  "currency": "USD"
}

2. Update Itinerary Payload:
{
  "type": "update_itinerary",
  "title": "Adjust Schedule for [Activity]",
  "changes": [
    {
      "activity": "[Activity Name]",
      "from_time": "10:00 AM",
      "to_time": "05:00 PM",
      "reason": "Better weather conditions / avoided rain"
    }
  ]
}
"""
