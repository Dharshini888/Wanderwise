import google.generativeai as genai
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Try models in order — fall back if quota/unavailable
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


def _groq(prompt: str, system: str = None) -> str:
    """Call Groq API using the official SDK."""
    if not GROQ_API_KEY:
        return "⚠️ AI quota exceeded and no Groq API key configured."
    client = Groq(api_key=GROQ_API_KEY)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )
    return completion.choices[0].message.content


def _ai(prompt: str, system: str = None) -> str:
    """Helper: call Gemini with automatic model fallback, then Groq."""
    for model_name in MODELS:
        try:
            kwargs = {"model_name": model_name}
            if system:
                kwargs["system_instruction"] = system
            model = genai.GenerativeModel(**kwargs)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err = str(e)
            # Fall through to next model on quota OR model-not-found errors
            if (
                "429" in err
                or "quota" in err.lower()
                or "ResourceExhausted" in err
                or "404" in err
                or "NotFound" in err
                or "not found" in err.lower()
                or "not supported" in err.lower()
            ):
                continue
            raise  # Re-raise unexpected errors

    # All Gemini models exhausted — try Groq
    try:
        return _groq(prompt, system)
    except Exception as e:
        return f"⚠️ All AI providers failed. Last error: {str(e)}"


# ──────────────────────────────────────────────
# ITINERARY
# ──────────────────────────────────────────────

def generate_itinerary(destination: str, days: int, budget: float,
                       interests: str, travel_type: str,
                       group_size: int = 1, currency: str = "USD") -> str:
    prompt = f"""
    Create a detailed {days}-day travel itinerary for {destination}.
    Budget: {budget} {currency}
    Interests: {interests}
    Travel type: {travel_type}
    Group size: {group_size} person(s)

    Format the itinerary as:
    Day 1:
    - Morning: ...
    - Afternoon: ...
    - Evening: ...
    - Estimated cost: {currency} ...

    (repeat for each day)

    End with a total estimated budget breakdown by category.
    """
    try:
        res = _ai(prompt)
        if "quota exceeded" in res.lower() or "⚠️" in res:
            return (
                f"⚠️ AI quota exceeded — here is a sample itinerary for {destination}.\n\n"
                + _fallback_itinerary(destination, days, budget)
            )
        return res
    except Exception as e:
        raise

def replan_itinerary(current_itinerary: str, modification_request: str) -> str:
    prompt = f"""
    You are an AI travel assistant. The user wants to modify their existing itinerary.
    
    Current Itinerary:
    {current_itinerary}
    
    User's modification request:
    {modification_request}
    
    Please provide the updated itinerary in the exact same format as the original, 
    incorporating the requested changes smoothly. Do not include conversational text outside the itinerary.
    """
    try:
        res = _ai(prompt)
        return res
    except Exception as e:
        raise


def _fallback_itinerary(destination: str, days: int, budget: float) -> str:
    daily = budget / max(days, 1)
    lines = []
    for d in range(1, days + 1):
        lines.append(f"Day {d}:")
        lines.append(f"  - Morning: Explore the local area of {destination}")
        lines.append(f"  - Afternoon: Visit top-rated attractions")
        lines.append(f"  - Evening: Enjoy local cuisine and nightlife")
        lines.append(f"  - Estimated cost: ${daily:.0f}\n")
    lines.append(
        f"Total budget breakdown:\n"
        f"  - Accommodation: ${budget*0.4:.0f}\n"
        f"  - Food: ${budget*0.3:.0f}\n"
        f"  - Activities: ${budget*0.2:.0f}\n"
        f"  - Transport: ${budget*0.1:.0f}"
    )
    return "\n".join(lines)


# ──────────────────────────────────────────────
# AI CHAT
# ──────────────────────────────────────────────

def chat_with_assistant(user_message: str, destination: str = "") -> str:
    system_prompt = """You are WanderWise, an AI travel assistant.
    Help users with travel planning, recommendations, local tips,
    transportation guidance, and any travel-related questions.
    Be friendly, concise, and practical."""

    context = f"User is traveling to: {destination}" if destination else ""
    full_prompt = f"{context}\n\n{user_message}".strip()
    return _ai(full_prompt, system=system_prompt)


# ──────────────────────────────────────────────
# PACKING LIST
# ──────────────────────────────────────────────

def generate_packing_list(destination: str, duration: int,
                          travel_type: str, weather: str = "") -> str:
    prompt = f"""
    Generate a smart AI packing checklist for a trip to {destination}.
    Duration: {duration} days
    Travel type: {travel_type}
    Expected weather: {weather if weather else 'unknown'}

    Format your response as a JSON object with these categories:
    {{
      "Clothing": ["item1", "item2", ...],
      "Documents": ["item1", ...],
      "Electronics": ["item1", ...],
      "Health & Hygiene": ["item1", ...],
      "Accessories": ["item1", ...],
      "Destination Specific": ["item1", ...]
    }}

    Only return the JSON. No extra text.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# SMART TRANSIT
# ──────────────────────────────────────────────

def transit_guide(from_location: str, to_location: str, city: str) -> str:
    prompt = f"""
    You are a smart public transport navigator for {city}.
    A traveler wants to go from "{from_location}" to "{to_location}".

    Provide a detailed step-by-step transit guide in this exact JSON format:
    {{
      "summary": "Brief route summary",
      "total_time": "Estimated time e.g. 45 minutes",
      "total_fare": "Estimated fare e.g. ₹40 or $2",
      "walking_distance": "Total walking distance e.g. 800m",
      "steps": [
        {{
          "type": "walk|bus|metro|train|auto",
          "instruction": "Walk to XYZ Bus Stop",
          "detail": "Head north on Main Street for 200m",
          "duration": "5 min",
          "fare": "Free"
        }}
      ],
      "tips": ["Tip 1", "Tip 2"],
      "alternatives": [
        {{"name": "Fastest Route", "time": "30 min", "cost": "$5", "mode": "Taxi"}},
        {{"name": "Cheapest Route", "time": "60 min", "cost": "$1", "mode": "Bus"}}
      ]
    }}

    Only return the JSON. No extra text.
    """
    res = _ai(prompt)
    if "quota exceeded" in res.lower() or "⚠️" in res:
        return f"""
        {{
          "summary": "⚠️ AI quota exceeded. Showing an estimated generic route for {city}.",
          "total_time": "30 mins",
          "total_fare": "Local standard fare",
          "walking_distance": "500m",
          "steps": [
            {{
              "type": "walk",
              "instruction": "Walk towards the nearest main transit hub",
              "detail": "Head straight for about 5 minutes",
              "duration": "5 min",
              "fare": "Free"
            }},
            {{
              "type": "taxi",
              "instruction": "Take a local taxi or transit to {to_location}",
              "detail": "Ask the driver or staff for the fastest route",
              "duration": "25 min",
              "fare": "Standard fare"
            }}
          ],
          "tips": ["Always carry small change", "Verify the destination before boarding"],
          "alternatives": []
        }}
        """
    return res


# ──────────────────────────────────────────────
# RISK ANALYZER
# ──────────────────────────────────────────────

def analyze_travel_risk(destination: str, travel_dates: str, budget: float) -> str:
    prompt = f"""
    You are a travel risk analyzer. Analyze travel risks for:
    Destination: {destination}
    Travel dates: {travel_dates}
    Budget: ${budget}

    Return a JSON object with scores out of 100 (where 100 = 100% risk / highest danger, 0 = 0% risk / totally safe).
    Format exactly like this:
    {{
      "overall_score": <integer 0-100>,
      "overall_label": "<Safe | Moderate Risk | High Risk>",
      "weather_risk": <integer 0-100>,
      "crowd_risk": <integer 0-100>,
      "safety_risk": <integer 0-100>,
      "top_recommendations": ["...", "...", "..."],
      "emergency_numbers": {{"police": "<local police number>", "ambulance": "<local ambulance number>", "fire": "<local fire number>", "tourist_helpline": "<if applicable>"}}
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# SCAM ALERTS
# ──────────────────────────────────────────────

def get_scam_alerts(destination: str) -> str:
    prompt = f"""
    List common tourist scams and safety alerts for travelers visiting {destination}.

    Return JSON:
    {{
      "destination": "{destination}",
      "safety_rating": "<Safe | Moderate | Caution>",
      "scams": [
        {{
          "name": "<Name of a specific local scam>",
          "severity": "<High | Medium | Low>",
          "description": "<How this specific scam works in {destination}>",
          "warning_signs": ["<sign 1>", "<sign 2>"],
          "how_to_avoid": "<Practical advice>"
        }}
      ],
      "general_safety_tips": ["<tip 1>", "<tip 2>"],
      "safe_areas": ["<area 1>", "<area 2>"],
      "avoid_areas": ["<area 1>"]
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# RECOMMENDATIONS
# ──────────────────────────────────────────────

def get_recommendations(destination: str, category: str,
                        budget_level: str = "mid-range",
                        interests: str = "") -> str:
    prompt = f"""
    Recommend the best {category} for travelers visiting {destination}.
    Budget level: {budget_level}
    Interests: {interests if interests else 'general'}

    Return JSON array of 6 items:
    [
      {{
        "name": "Place/Hotel/Restaurant name",
        "description": "2-3 sentence description",
        "rating": 4.5,
        "price_range": "$ | $$ | $$$",
        "highlight": "One key highlight",
        "location": "Area/neighborhood",
        "best_for": "couples | families | solo | groups",
        "tip": "Insider tip"
      }}
    ]

    Only return the JSON array.
    """
    return _ai(prompt)


def get_hidden_gems(destination: str, interests: str = "") -> str:
    prompt = f"""
    Discover hidden gems, offbeat attractions, and authentic local experiences in {destination}.
    Interests: {interests if interests else 'general'}

    These should be places most tourists don't know about — local favorites, lesser-known spots.

    Return JSON array of 6 items:
    [
      {{
        "name": "Place name",
        "type": "Nature | Market | Cultural | Food | Adventure",
        "description": "What makes this place special",
        "why_hidden": "Why tourists miss this",
        "best_time": "Best time to visit",
        "local_tip": "What locals recommend doing there",
        "crowd_level": "Very Low | Low | Moderate",
        "location": "Approximate area"
      }}
    ]

    Only return the JSON array.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# WEATHER ACTIVITY ADVISOR
# ──────────────────────────────────────────────

def weather_activity_advisor(destination: str, weather_desc: str,
                              temperature: float) -> str:
    prompt = f"""
    A traveler is in {destination}.
    Current weather: {weather_desc}, {temperature}°C

    Suggest smart activity recommendations based on this weather.

    Return JSON:
    {{
      "weather_summary": "Brief interpretation",
      "indoor_activities": [
        {{"name": "Activity", "reason": "Why good for this weather", "duration": "2 hours"}}
      ],
      "outdoor_activities": [
        {{"name": "Activity", "reason": "Why good for this weather", "duration": "3 hours"}}
      ],
      "what_to_wear": ["item1", "item2"],
      "ai_suggestion": "One proactive suggestion from WanderWise AI"
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# AI TRAVEL MEMORY GENERATOR
# ──────────────────────────────────────────────

def generate_trip_memory(destination: str, start_date: str, end_date: str,
                         journal_entries: list, total_spent: float,
                         attractions_count: int = 0) -> str:
    entries_text = "\n".join(
        [f"- {e.get('title', 'Entry')}: {e.get('content', '')[:200]}" for e in journal_entries[:10]]
    )
    prompt = f"""
    Generate a warm, poetic AI travel memory summary for a completed trip.

    Trip details:
    - Destination: {destination}
    - Dates: {start_date} to {end_date}
    - Total spent: ${total_spent:.0f}
    - Attractions visited: {attractions_count}
    - Journal entries:
    {entries_text if entries_text else "No journal entries recorded."}

    Write a 3-4 paragraph travel memory that:
    1. Highlights the journey and key moments
    2. References specific journal entries warmly
    3. Includes stats naturally in the narrative
    4. Ends with an inspiring closing line

    Make it personal, vivid, and emotionally resonant.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# AI COMPANION MODE
# ──────────────────────────────────────────────

def companion_suggestions(destination: str, current_day: int, total_days: int,
                          itinerary_snippet: str, weather: str = "") -> str:
    prompt = f"""
    You are WanderWise AI Companion — a proactive travel guide.
    
    Traveler info:
    - Destination: {destination}
    - Day {current_day} of {total_days}
    - Current weather: {weather if weather else 'not specified'}
    - Today's planned activities: {itinerary_snippet[:500] if itinerary_snippet else 'free day'}

    Generate proactive, real-time travel companion suggestions.

    Return JSON:
    {{
      "greeting": "Personalized good morning/afternoon message",
      "weather_alert": null or "Alert message if weather affects plans",
      "suggestions": [
        {{"type": "timing | safety | food | transport | activity", "message": "Suggestion", "priority": "high|medium|low"}}
      ],
      "reminders": ["Reminder 1", "Reminder 2"],
      "did_you_know": "An interesting local fact about the destination",
      "progress_message": "You're on day X of Y — keep exploring!"
    }}

    Only return JSON.
    """
    return _ai(prompt)

# ──────────────────────────────────────────────
# DASHBOARD WIDGETS AI
# ──────────────────────────────────────────────

def get_language_guide(destination: str) -> str:
    prompt = f"""
    Provide a brief language guide for {destination}.
    Return JSON:
    {{
      "primary_language": "Language Name",
      "hello": "Translation for hello",
      "thank_you": "Translation for thank you",
      "help": "Translation for help me",
      "how_much": "Translation for how much is this",
      "goodbye": "Translation for goodbye",
      "cultural_tip": "A brief 1-sentence cultural tip about communication"
    }}
    Only return JSON.
    """
    return _ai(prompt)

def personalized_destinations(past_destinations: list) -> str:
    past_str = ", ".join(past_destinations) if past_destinations else "None yet"
    prompt = f"""
    A traveler has previously visited: {past_str}.
    Recommend 3 new, unique destinations they might like.
    Return JSON array:
    [
      {{
        "destination": "Name of new destination",
        "reason": "Why they would like it based on past trips",
        "vibe": "E.g., Relaxing, Adventure, Historic"
      }}
    ]
    Only return JSON array.
    """
    return _ai(prompt)

def translate_text(text: str, destination: str) -> str:
    prompt = f"""
    You are a real-time translator for a traveler in {destination}.
    Translate the following text into the primary local language of {destination}.
    If the text is already in the local language, translate it to English.
    Text to translate: "{text}"
    
    Return JSON format exactly like this:
    {{
      "original": "{text}",
      "translated": "<The translation>",
      "target_language": "<The name of the language translated to>"
    }}
    
    Only return JSON.
    """
    return _ai(prompt)
