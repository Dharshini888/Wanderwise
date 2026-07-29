"""
v2.7.1 End-to-End API Verification Test
Tests the full recommendation pipeline including DB interaction
"""
import sys
import traceback
sys.path.insert(0, '.')

PASS = 0
FAIL = 0

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
        PASS += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        traceback.print_exc()
        FAIL += 1

# ── Import verification ────────────────────────────────────────────────────────
def t_imports():
    from app.ai.recommendation.recommendation_service import RecommendationService, DESTINATION_SEEDS
    from app.ai.recommendation.fallback_destinations import CURATED_FOR_NEW_USERS, FALLBACK_DESTINATIONS
    assert len(DESTINATION_SEEDS) >= 10
    assert len(CURATED_FOR_NEW_USERS) >= 4
    assert "nature" in FALLBACK_DESTINATIONS
    assert "beach" in FALLBACK_DESTINATIONS
    assert "culture" in FALLBACK_DESTINATIONS

test("All imports OK", t_imports)

# ── DB connection ──────────────────────────────────────────────────────────────
from app.database.connection import get_db
db = next(get_db())

def t_service_init():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    assert svc is not None

test("RecommendationService initializes without crash", t_service_init)

# ── Core pipeline with no user profile ────────────────────────────────────────
def t_no_profile():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999)  # Non-existent user
    assert isinstance(result, dict)
    assert "recommended_for_you" in result
    assert "because_you_loved" in result
    assert "budget_friendly" in result
    assert "seasonal_picks" in result
    assert "user_profile" in result
    assert len(result["recommended_for_you"]) > 0, "Should return fallback curated for new user"
    print(f"      -> recommended_for_you: {len(result['recommended_for_you'])} items")
    print(f"      -> budget_friendly: {len(result['budget_friendly'])} items")
    print(f"      -> seasonal_picks: {len(result['seasonal_picks'])} items")

test("Full recommendations for new user (no profile/history)", t_no_profile)

# ── Interest filter: nature ────────────────────────────────────────────────────
def t_interest_nature():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999, interest_filter="nature")
    assert "discover_by_interest" in result
    print(f"      -> discover_by_interest (nature): {len(result['discover_by_interest'])} items")

test("Interest filter: nature", t_interest_nature)

# ── Interest filter: beach ────────────────────────────────────────────────────
def t_interest_beach():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999, interest_filter="beach")
    assert "discover_by_interest" in result

test("Interest filter: beach", t_interest_beach)

# ── Interest filter: culture ──────────────────────────────────────────────────
def t_interest_culture():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999, interest_filter="culture")
    assert "discover_by_interest" in result

test("Interest filter: culture", t_interest_culture)

# ── NL Query ─────────────────────────────────────────────────────────────────
def t_nl_query():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999, query="I loved Meghalaya waterfalls, suggest similar nature places")
    assert "nl_query_results" in result
    print(f"      -> nl_query_results: {len(result['nl_query_results'])} items")

test("Natural language query", t_nl_query)

# ── Budget constraint ─────────────────────────────────────────────────────────
def t_budget():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999, max_budget=500.0)
    assert "budget_friendly" in result
    budget_dests = result["budget_friendly"]
    for d in budget_dests:
        assert d["average_budget"] <= 500.0, f"{d['destination']} budget {d['average_budget']} exceeds cap 500"
    print(f"      -> budget_friendly (max $500): {len(budget_dests)} items")

test("Budget constraint filter", t_budget)

# ── Response contract validation ──────────────────────────────────────────────
def t_contract():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999)
    
    required_keys = ["user_profile", "recommended_for_you", "because_you_loved", "budget_friendly", "seasonal_picks"]
    for k in required_keys:
        assert k in result, f"Missing key: {k}"
    
    # Check each rec has required fields
    for rec in result["recommended_for_you"]:
        assert "destination" in rec, "Missing destination field"
        assert "match_score" in rec, "Missing match_score field"
        assert "reasons" in rec, "Missing reasons field"
        assert isinstance(rec["reasons"], list), "reasons should be a list"

test("Response contract validation", t_contract)

# ── Score range validation ────────────────────────────────────────────────────
def t_scores():
    from app.ai.recommendation.recommendation_service import RecommendationService
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=99999)
    for rec in result["recommended_for_you"]:
        score = rec["match_score"]
        assert 0 <= score <= 100, f"{rec['destination']} score {score} out of range"
    print(f"      -> all {len(result['recommended_for_you'])} scores in valid range 0-100")

test("Match scores in valid range (0-100)", t_scores)

db.close()

print()
print("=" * 50)
print(f"v2.7.1 TEST RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED - API ready for 200 responses")
else:
    print("SOME TESTS FAILED - check output above")
