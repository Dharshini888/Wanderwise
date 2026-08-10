# Weather tracking service
import random

def get_route_weather(origin: str, destination: str):
    # Generates dynamic weather for multi-stop transit
    temp_origin = random.randint(20, 35)
    temp_dest = random.randint(15, 30)
    return [
        {"location": origin, "temp_c": temp_origin, "icon": "☀️"},
        {"location": "Layover (Simulated)", "temp_c": (temp_origin + temp_dest)//2, "icon": "⛅"},
        {"location": destination, "temp_c": temp_dest, "icon": "🌧️" if temp_dest < 20 else "☀️"}
    ]

def get_weather_warnings(origin: str, destination: str):
    # Determine risk based on name length just to be deterministic
    if len(destination) % 3 == 0:
        return [f"Heavy rain expected near {destination} at ETA."]
    return ["Carry umbrella.", "Flight delay probability 18%."]
