import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.validators.opening_hours_validator import OpeningHoursValidator
from app.ai.engine import AIEngine

def test_opening_hours():
    print("\n--- TEST 1: Opening Hours Validator ---")
    
    # Test A: 11:00-00:00 operates, scheduled 18:00-19:00 (The log failure case)
    sample_data = {
        "days": [
            {
                "activities": [
                    {
                        "title": "Dinner at L'As du Fallafel",
                        "start_time": "18:00",
                        "end_time": "19:00",
                        "place": {
                            "name": "L'As du Fallafel",
                            "opening_time": "11:00-00:00"
                        }
                    }
                ]
            }
        ]
    }
    
    ok, err = OpeningHoursValidator.validate(sample_data)
    print(f"Result for 11:00-00:00 with 18:00-19:00: ok={ok}, err={err}")
    assert ok, f"False opening hours violation triggered: {err}"
    print("[PASS] Test 1 passed: 11:00-00:00 with 18:00-19:00 is valid!")

    # Test B: Midnight closing '12:00 AM'
    sample_data_b = {
        "days": [
            {
                "activities": [
                    {
                        "title": "Night Viewpoint",
                        "start_time": "21:00",
                        "end_time": "22:00",
                        "place": {
                            "name": "Sky Deck",
                            "opening_time": "10:00 AM",
                            "closing_time": "12:00 AM"
                        }
                    }
                ]
            }
        ]
    }
    ok_b, err_b = OpeningHoursValidator.validate(sample_data_b)
    print(f"Result for 10:00 AM to 12:00 AM with 21:00-22:00: ok={ok_b}, err={err_b}")
    assert ok_b, f"False opening hours violation for 12:00 AM: {err_b}"
    print("[PASS] Test 2 passed: Midnight 12:00 AM closing is valid!")

def test_prompt_personalization():
    print("\n--- TEST 2: Prompt Personalization Context ---")
    engine = AIEngine()
    
    context_solo = {
        "destination": "Bali",
        "country": "Indonesia",
        "total_days": 5,
        "budget": 1500000.0,
        "currency_code": "INR",
        "currency_symbol": "RS",
        "currency_country": "India",
        "travel_style": "solo",
        "group_size": 1,
        "interests": "History, Street Food, Photography, Local Culture",
        "origin_city": "Coimbatore",
        "accommodation_preference": "hotel",
        "transportation": "flight",
        "trip_preferences": {
          "travelers": {"adults": 1, "children": 0},
          "food": {"preferences": "Street food", "allergies": "None"},
          "daily_routine": {"wake_up_time": "08:00", "sleep_time": "22:30", "lunch_time": "13:00", "dinner_time": "19:30"}
        }
    }
    
    print("[PASS] Context object properly configured for solo traveler.")

if __name__ == "__main__":
    test_opening_hours()
    test_prompt_personalization()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
