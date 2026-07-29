DESTINATION_RECOMMENDER_PROMPT = """
Use this prompt to generate destination recommendation card payloads.

OUTPUT ACTION FORMAT:
{
  "type": "recommend_destinations",
  "title": "Tailored Destination Ideas",
  "destinations": [
    {
      "name": "Kyoto, Japan 🇯🇵",
      "estimated_budget": 80000,
      "best_season": "Nov - Feb",
      "travel_style": "Culture & Heritage",
      "reason": "Matches your preference for historic temples & walking tours"
    },
    {
      "name": "Da Nang, Vietnam 🇻🇳",
      "estimated_budget": 45000,
      "best_season": "Oct - Mar",
      "travel_style": "Beach & Food",
      "reason": "Affordable coastal experience with world-class street food"
    }
  ]
}
"""
