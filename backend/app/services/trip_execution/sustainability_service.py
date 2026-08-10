# Sustainability Service

def get_green_travel_score(mode: str):
    return {
        "score_stars": "★★★★☆" if mode != "Flight" else "★★☆☆☆",
        "carbon_saved_kg": 42 if mode != "Flight" else 0,
        "better_choice": "Train instead of Flight" if mode == "Flight" else "You made a sustainable choice!",
        "equivalent_trees": 2 if mode != "Flight" else 0
    }
