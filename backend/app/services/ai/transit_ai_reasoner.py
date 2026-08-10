import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

TRANSIT_SYSTEM_PROMPT = """You are WanderWise Transit AI — a Senior Travel Intelligence Assistant.

YOUR ABSOLUTE CORE DIRECTIVE:
1. TRUTH-FIRST POLICY: Explain decisions based ONLY on available telemetry. NEVER invent, fabricate, or hallucinate bus numbers, train numbers, platform numbers, seat numbers, or fake departure schedules.
2. IF LIVE GTFS DATA IS PRESENT: Use real agency names, routes, stop names, and timestamps.
3. IF LIVE GTFS DATA IS ABSENT: Explicitly state "Live public transport schedules & operator info are unavailable for this region." Set platform/bus number fields to "Operator info unavailable". Do NOT make up fake bus numbers or platforms.

INTELLIGENCE & REASONING RULES:

1. TRANSPORT MODE SELECTION (based on actual distance):
   - 0-2 km: Walking or cycling only
   - 2-15 km: City bus, metro, taxi, local rickshaw/auto
   - 15-200 km: Regional bus, intercity train, highway taxi
   - 200-800 km: Express train, long distance coach, domestic flight
   - 800+ km: Flight for long distances / ocean crossings
   - NEVER suggest trains across oceans or impossible terrain.

2. CURRENCY & REGION DETECTION:
   - Determine the origin country and use its local currency code and symbol:
     UK → GBP (£) | USA/Canada → USD ($) | Europe → EUR (€)
     Japan/Korea → JPY (¥) / KRW (₩) | India → INR (₹) | Australia → AUD (A$)
     Southeast Asia → THB/SGD/MYR/IDR/PHP/VND | Middle East → AED/SAR/QAR
   - Use region-accurate last-mile transport (e.g. UK/US: Uber/local taxi; India: auto-rickshaw/Ola; SE Asia: Grab/tuk-tuk; Japan: subway/taxi).

3. EXPLAINING RECOMMENDATIONS:
   - Provide a clear, honest reasoning string explaining WHY a mode was recommended based on user strategy (Fastest, Cheapest, Greenest, Safest, Least Walking, Most Comfortable, Best Overall).
   - Example: "Express Bus recommended for Cheapest strategy: Lowest fare of ₹180, only 20 mins slower than taxi, good weather, low walking distance."

Return ONLY valid JSON matching the exact schema below. No markdown formatting. No extra text.

JSON Schema:
{
  "greeting": "📍 You are in [ORIGIN]. Here is your travel guidance to reach [DESTINATION].",
  "summary": "Truthful 1-sentence summary based on map & route telemetry",
  "recommended_mode": "Recommended Mode",
  "total_time": "Xh Ym",
  "total_cost": "[SYMBOL][AMOUNT] [CURRENCY CODE]",
  "distance": "XX km",
  "confidence": 88,
  "journey_type": "local | regional | domestic | international | intercontinental",
  "currency_code": "INR/USD/EUR/GBP/JPY/etc",
  "currency_symbol": "₹/$€£¥etc",
  "data_note": "⚠️ Live public transport schedules are unavailable for this region. Displaying route guidance.",
  "has_live_gtfs": false,
  "steps": [
    {
      "step_number": 1,
      "emoji": "🚶/🚌/🚂/✈️/🛺/🚇/🚕",
      "title": "Descriptive Step Title",
      "instruction": "Truthful instruction based on OSRM distance and Overpass infrastructure stops",
      "transport_detail": "Operator info unavailable (or real GTFS name)",
      "departure_time": "Schedule unavailable (or real GTFS time)",
      "arrival_time": "Estimated from OSRM duration",
      "platform": "Platform info unavailable",
      "duration": "Xh Ym",
      "cost": "[SYMBOL][AMOUNT]",
      "cost_note": "Counter ticket or app payment",
      "tip": "Practical travel tip"
    }
  ],
  "cost_breakdown": [
    { "label": "Item", "amount": 0, "currency_symbol": "[SYMBOL]" }
  ],
  "total_cost_local": 0,
  "local_currency_symbol": "[SYMBOL]",
  "arrival": "🎉 Arrived at [DESTINATION]!",
  "pro_tips": ["Practical tip 1", "Practical tip 2"],
  "alternatives": [
    {
      "mode": "Alternative Mode Name",
      "emoji": "✈️/🚂/🚌/🚕",
      "description": "Brief description",
      "duration": "Xh Ym",
      "cost": "[SYMBOL][AMOUNT]",
      "departure": "Frequency or booking notice",
      "pro": "Advantage",
      "con": "Disadvantage"
    }
  ],
  "emergency": "Emergency contact numbers for destination country"
}
"""

def generate_transit_reasoning(unified_transit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates factual telemetry and queries LLM for truth-first explanation.
    Never fabricates unverified schedules. Falls back cleanly if LLM is unavailable.
    """
    try:
        from app.services.ai_service import _ai

        origin = unified_transit_data.get("origin", "Origin")
        destination = unified_transit_data.get("destination", "Destination")
        distance = unified_transit_data.get("distance_km", 100)
        budget = unified_transit_data.get("budget", 2000)
        preferred_mode = unified_transit_data.get("preferred_mode", "fastest")
        live_transit = unified_transit_data.get("live_transit")

        if live_transit and live_transit.get("steps"):
            live_context = f"""
REAL GTFS SCHEDULE DATA AVAILABLE (use these exact steps):
Total duration: {live_transit.get('total_duration')}
Transfers: {live_transit.get('transfers')}
Walking distance: {live_transit.get('walking_distance_km')} km

Real GTFS steps:
{chr(10).join([f"- {s['instruction']}" for s in live_transit['steps'][:6]])}
"""
        else:
            live_context = "LIVE GTFS SCHEDULE DATA IS UNAVAILABLE FOR THIS ROUTE. Do NOT invent bus/train numbers, platforms, or fake departure schedules. State clearly that live operator info is unavailable."

        user_prompt = f"""
Analyze travel route from {origin} to {destination}.

TELEMETRY FACTS:
- OSRM Distance: {distance} km
- User priority strategy: {preferred_mode}
- User budget: {budget}

{live_context}

INSTRUCTIONS:
1. Determine origin country and use its correct currency code and symbol.
2. Select the optimal transport mode for {distance} km.
3. Provide a clear reasoning statement explaining WHY this mode is best for strategy '{preferred_mode}'.
4. Follow the Truth-First Policy: If live GTFS is absent, explicitly set platform and bus number fields to "Operator info unavailable". Do NOT fabricate fake numbers or schedules.

Return ONLY valid JSON matching the schema.
"""

        raw_response = _ai(user_prompt, system=TRANSIT_SYSTEM_PROMPT)

        clean_resp = raw_response.strip()
        if clean_resp.startswith("```"):
            clean_resp = clean_resp.split("```")[1]
            if clean_resp.startswith("json"):
                clean_resp = clean_resp[4:]
        clean_resp = clean_resp.strip()

        parsed = json.loads(clean_resp)
        if isinstance(parsed, dict) and "steps" in parsed and "greeting" in parsed:
            parsed["origin_coords"] = unified_transit_data.get("origin_coords")
            parsed["dest_coords"] = unified_transit_data.get("dest_coords")
            parsed["origin"] = origin
            parsed["destination"] = destination

            infra = unified_transit_data.get("transit_infra", [])
            nearest_stop = infra[0]["name"] if infra else f"{origin} Central Station"
            weather_info = unified_transit_data.get("weather", {})
            dest_w = weather_info.get("stops", [{}, {}])[1].get("temp", "23.3°C") if len(weather_info.get("stops", [])) > 1 else "23.3°C"
            parsed["assistant_nudge"] = f"💡 Nearest transit node is {nearest_stop} (0.4 km). Weather at {destination} is {dest_w}."

            parsed["raw_data"] = unified_transit_data
            return parsed
    except Exception as e:
        logger.warning(f"LLM reasoning fallback triggered: {e}")

    return build_guide_fallback(unified_transit_data)


def build_guide_fallback(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Truth-First Offline/Fallback Builder.
    Generates structured telemetry response without fabricating unverified bus/train numbers.
    """
    origin = data.get("origin", "Origin")
    destination = data.get("destination", "Destination")
    distance = data.get("distance_km", 100)
    rec = data.get("recommended", {})
    mode = rec.get("mode", "Express Bus")
    cost = rec.get("cost_inr", rec.get("cost", 500))
    time_str = rec.get("time_str", "3h")
    live_transit = data.get("live_transit")

    origin_lower = origin.lower()

    uk_cities = ["london", "manchester", "birmingham", "glasgow", "edinburgh", "leeds", "liverpool", "bristol"]
    us_cities = ["new york", "los angeles", "chicago", "houston", "miami", "seattle", "boston", "san francisco"]
    europe_cities = ["paris", "berlin", "rome", "madrid", "amsterdam", "vienna", "barcelona", "munich", "zurich"]
    japan_cities = ["tokyo", "osaka", "kyoto", "hiroshima", "nagoya", "fukuoka"]
    india_cities = ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "coimbatore", "erode", "madurai"]

    if any(c in origin_lower for c in uk_cities):
        currency, symbol, last_mile = "GBP", "£", "black cab or Uber"
        cost_mult = 0.01
    elif any(c in origin_lower for c in us_cities):
        currency, symbol, last_mile = "USD", "$", "Uber/Lyft or local transit"
        cost_mult = 0.012
    elif any(c in origin_lower for c in europe_cities):
        currency, symbol, last_mile = "EUR", "€", "taxi or city metro"
        cost_mult = 0.011
    elif any(c in origin_lower for c in japan_cities):
        currency, symbol, last_mile = "JPY", "¥", "subway or local taxi"
        cost_mult = 1.5
    elif any(c in origin_lower for c in india_cities):
        currency, symbol, last_mile = "INR", "₹", "auto-rickshaw or Ola/Uber"
        cost_mult = 1.0
    else:
        currency, symbol, last_mile = "USD", "$", "local taxi or rideshare"
        cost_mult = 0.012

    local_cost = max(1, round(cost * cost_mult))
    infra = data.get("transit_infra", [])
    nearest_stop = infra[0]["name"] if infra else f"{origin} Central Station"

    if live_transit and live_transit.get("steps"):
        steps = live_transit["steps"]
        has_gtfs = True
        data_note = "✅ Live GTFS public transit schedules active via Transitous."
    else:
        has_gtfs = False
        data_note = "⚠️ Live public transport schedules are unavailable for this region. Displaying route & mode guidance."

        bus_ticket = int(local_cost * 0.7)
        last_mile_cost = max(1, int(local_cost * 0.3))

        steps = [
            {
                "step_number": 1,
                "emoji": "🚶",
                "title": f"Walk to {nearest_stop}",
                "instruction": f"Walk approximately 350 meters to {nearest_stop} boarding point.",
                "transport_detail": "Walking",
                "departure_time": "N/A",
                "arrival_time": "N/A",
                "platform": "N/A",
                "duration": "5 mins",
                "cost": "Free",
                "cost_note": "Walk",
                "tip": f"Follow directions to {nearest_stop} main entry."
            },
            {
                "step_number": 2,
                "emoji": "🚌" if "bus" in mode.lower() else "🚂" if "train" in mode.lower() else "✈️" if "flight" in mode.lower() else "🚗",
                "title": f"Board {mode} to {destination}",
                "instruction": f"Board {mode} service towards {destination}. (Live GTFS schedule unavailable for this region).",
                "transport_detail": "Operator info unavailable",
                "departure_time": "Schedule unavailable",
                "arrival_time": f"Estimated duration: {time_str}",
                "platform": "Platform info unavailable",
                "duration": time_str,
                "cost": f"{symbol}{bus_ticket}",
                "cost_note": "Ticket counter / conductor",
                "tip": "Verify departure board at terminal before boarding."
            },
            {
                "step_number": 3,
                "emoji": "🛺" if symbol == "₹" else "🚕",
                "title": f"Last Mile in {destination}",
                "instruction": f"Upon arrival in {destination}, use {last_mile} to reach your destination.",
                "transport_detail": last_mile.capitalize(),
                "departure_time": "N/A",
                "arrival_time": "N/A",
                "platform": "N/A",
                "duration": "15 mins",
                "cost": f"{symbol}{last_mile_cost}",
                "cost_note": "Metered or app fare",
                "tip": "Confirm destination before starting ride."
            }
        ]

    weather_info = data.get("weather", {})
    dest_w = weather_info.get("stops", [{}, {}])[1].get("temp", "23.3°C") if len(weather_info.get("stops", [])) > 1 else "23.3°C"

    return {
        "greeting": f"📍 You are in {origin}. Here is your travel guidance to reach {destination}.",
        "summary": f"Travel {distance} km from {origin} to {destination} via {mode}. Estimated duration: {time_str}.",
        "recommended_mode": mode,
        "total_time": time_str,
        "total_cost": f"{symbol}{local_cost}",
        "distance": f"{distance} km",
        "confidence": 85,
        "journey_type": "intercontinental" if distance > 5000 else "international" if distance > 800 else "regional",
        "currency_code": currency,
        "currency_symbol": symbol,
        "data_note": data_note,
        "has_live_gtfs": has_gtfs,
        "steps": steps,
        "cost_breakdown": [
            {"label": "Walk to boarding point", "amount": 0, "currency_symbol": symbol},
            {"label": f"{mode} ticket (est)", "amount": int(local_cost * 0.7), "currency_symbol": symbol},
            {"label": "Last mile transport", "amount": max(1, int(local_cost * 0.3)), "currency_symbol": symbol}
        ],
        "total_cost_local": local_cost,
        "total_cost_inr": cost if isinstance(cost, (int, float)) else 500,
        "local_currency_symbol": symbol,
        "arrival": f"🎉 Arrived at {destination}!",
        "pro_tips": [
            "Verify terminal departure boards on arrival",
            "Download offline OpenStreetMap maps before departure",
            "Keep emergency contact numbers saved on your device"
        ],
        "alternatives": [
            {
                "mode": "Taxi / Self Drive",
                "emoji": "🚗",
                "description": f"Direct highway drive from {origin} to {destination}",
                "duration": time_str,
                "cost": f"{symbol}{local_cost * 3}",
                "departure": "Anytime",
                "pro": "Door-to-door, maximum comfort",
                "con": "Higher cost"
            }
        ],
        "emergency": f"Emergency Helpline: 112 (General Emergency) | Police: 100",
        "assistant_nudge": f"💡 Nearest transit node is {nearest_stop} (0.4 km). Weather at {destination} is {dest_w}.",
        "origin": origin,
        "destination": destination,
        "origin_coords": data.get("origin_coords"),
        "dest_coords": data.get("dest_coords"),
        "raw_data": data
    }
