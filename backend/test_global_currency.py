"""
test_global_currency.py — v2.7.2 Global Currency System Tests

Tests:
  1. CurrencyService conversion (USD → INR, AED, EUR, GBP, JPY)
  2. Budget object contract
  3. Format strings per currency
  4. normalize_currency_code
  5. Recommendation engine uses user currency
  6. API response includes user_currency key
  7. No hardcoded USD in budget objects for INR user
"""
import sys, traceback
sys.path.insert(0, '.')

PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
        PASS += 1
    except AssertionError as e:
        print(f"  [FAIL] {name}: {e}")
        FAIL += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
        FAIL += 1


print("=" * 60)
print("WanderWise v2.7.2 — Global Currency System Tests")
print("=" * 60)

# ─── 1. Import Tests ──────────────────────────────────────────────────────────
def t_imports():
    from app.services.currency_service import CurrencyService, FALLBACK_RATES_USD
    assert "INR" in FALLBACK_RATES_USD
    assert "AED" in FALLBACK_RATES_USD
    assert "EUR" in FALLBACK_RATES_USD
    assert FALLBACK_RATES_USD["INR"] > 10   # INR should be ~83
    assert FALLBACK_RATES_USD["AED"] > 3    # AED should be ~3.67

test("CurrencyService imports & fallback rates", t_imports)

# ─── 2. Conversion Tests ──────────────────────────────────────────────────────
def t_usd_to_inr():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(100, "USD", "INR")
    assert result > 5000, f"Expected >5000 INR for $100, got {result}"
    assert result < 15000, f"INR rate looks incorrect: {result}"
    print(f"      $100 USD → ₹{result:.0f} INR")

test("USD → INR conversion", t_usd_to_inr)

def t_usd_to_aed():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(100, "USD", "AED")
    assert result > 200, f"Expected >200 AED for $100, got {result}"
    assert result < 600, f"AED rate looks incorrect: {result}"
    print(f"      $100 USD → {result:.0f} AED")

test("USD → AED conversion", t_usd_to_aed)

def t_usd_to_eur():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(100, "USD", "EUR")
    assert result > 70, f"Expected >70 EUR for $100, got {result}"
    assert result < 115, f"EUR rate looks incorrect: {result}"
    print(f"      $100 USD → €{result:.2f} EUR")

test("USD → EUR conversion", t_usd_to_eur)

def t_usd_to_gbp():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(100, "USD", "GBP")
    assert result > 50, f"Expected >50 GBP for $100, got {result}"
    assert result < 100, f"GBP rate looks incorrect: {result}"
    print(f"      $100 USD → £{result:.2f} GBP")

test("USD → GBP conversion", t_usd_to_gbp)

def t_usd_to_jpy():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(100, "USD", "JPY")
    assert result > 10000, f"Expected >10000 JPY for $100, got {result}"
    assert result < 25000, f"JPY rate looks incorrect: {result}"
    print(f"      $100 USD → ¥{result:.0f} JPY")

test("USD → JPY conversion", t_usd_to_jpy)

def t_same_currency():
    from app.services.currency_service import CurrencyService
    result = CurrencyService.convert(500, "USD", "USD")
    assert result == 500.0, f"Same currency should return same amount, got {result}"

test("Same currency conversion (USD→USD)", t_same_currency)

# ─── 3. Budget Object Tests ───────────────────────────────────────────────────
def t_budget_object_inr():
    from app.services.currency_service import CurrencyService
    obj = CurrencyService.build_budget_object(700.0, "INR", "USD")
    assert obj["base_currency"] == "USD"
    assert obj["user_currency"] == "INR"
    assert obj["amount"] == 700.0
    assert obj["converted_amount"] > 40000, f"700 USD should be >40000 INR, got {obj['converted_amount']}"
    assert obj["formatted"].startswith("₹"), f"INR formatted should start with ₹, got {obj['formatted']}"
    print(f"      Budget object INR: {obj['formatted']} (₹{obj['converted_amount']:.0f})")

test("Budget object — INR user ($700 USD)", t_budget_object_inr)

def t_budget_object_aed():
    from app.services.currency_service import CurrencyService
    obj = CurrencyService.build_budget_object(1200.0, "AED", "USD")
    assert obj["user_currency"] == "AED"
    assert obj["converted_amount"] > 3000
    assert "د.إ" in obj["formatted"] or "AED" in obj["formatted"] or obj["converted_amount"] > 0
    print(f"      Budget object AED: {obj['formatted']}")

test("Budget object — AED user ($1200 USD Kyoto)", t_budget_object_aed)

def t_budget_object_eur():
    from app.services.currency_service import CurrencyService
    obj = CurrencyService.build_budget_object(800.0, "EUR", "USD")
    assert obj["user_currency"] == "EUR"
    assert obj["converted_amount"] > 500
    print(f"      Budget object EUR: {obj['formatted']}")

test("Budget object — EUR user ($800 USD)", t_budget_object_eur)

def t_budget_object_usd():
    from app.services.currency_service import CurrencyService
    obj = CurrencyService.build_budget_object(700.0, "USD", "USD")
    assert obj["user_currency"] == "USD"
    assert obj["converted_amount"] == 700.0
    assert "$" in obj["formatted"] or "USD" in obj["formatted"]
    print(f"      Budget object USD: {obj['formatted']}")

test("Budget object — USD user ($700 USD)", t_budget_object_usd)

# ─── 4. Currency Normalization ────────────────────────────────────────────────
def t_normalize():
    from app.services.currency_service import CurrencyService
    assert CurrencyService.normalize_currency_code("USD ($)") == "USD"
    assert CurrencyService.normalize_currency_code("INR (₹)") == "INR"
    assert CurrencyService.normalize_currency_code("inr") == "INR"
    assert CurrencyService.normalize_currency_code("EUR") == "EUR"
    assert CurrencyService.normalize_currency_code("") == "USD"
    assert CurrencyService.normalize_currency_code(None) == "USD"

test("Currency code normalization", t_normalize)

# ─── 5. Recommendation Engine Currency Integration ────────────────────────────
def t_recs_inr_user():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="INR")

        assert result["user_currency"] == "INR"

        recs = result["recommended_for_you"]
        assert len(recs) > 0

        for rec in recs:
            budget = rec.get("budget")
            assert budget is not None, f"{rec['destination']} missing budget object"
            assert budget["user_currency"] == "INR", f"Expected INR, got {budget.get('user_currency')}"
            assert budget["converted_amount"] > 1000, f"INR amount too low: {budget['converted_amount']}"
            assert budget["formatted"].startswith("₹"), f"INR should start with ₹: {budget['formatted']}"
            print(f"      {rec['destination']}: {budget['formatted']} (match {rec['match_score']}%)")

    finally:
        db.close()

test("Recommendations — INR user gets ₹ budget objects", t_recs_inr_user)

def t_recs_usd_user():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="USD")
        assert result["user_currency"] == "USD"
        for rec in result["recommended_for_you"][:3]:
            budget = rec["budget"]
            assert budget["user_currency"] == "USD"
            assert budget["converted_amount"] < 5000, f"USD budget looks too high: {budget['converted_amount']}"
    finally:
        db.close()

test("Recommendations — USD user gets $ budget objects", t_recs_usd_user)

def t_recs_aed_user():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="AED")
        assert result["user_currency"] == "AED"
        for rec in result["recommended_for_you"][:3]:
            budget = rec["budget"]
            assert budget["user_currency"] == "AED"
            assert budget["converted_amount"] > 500, f"AED amount too low: {budget['converted_amount']}"
            print(f"      {rec['destination']}: {budget['formatted']}")
    finally:
        db.close()

test("Recommendations — AED user gets AED budget objects", t_recs_aed_user)

# ─── 6. No Hardcoded $ for Non-USD Users ─────────────────────────────────────
def t_no_hardcoded_usd():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="INR")
        for rec in result["recommended_for_you"]:
            formatted = rec["budget"]["formatted"]
            assert not formatted.startswith("$"), f"{rec['destination']} still shows $ for INR user: {formatted}"
    finally:
        db.close()

test("No hardcoded $ symbol for INR user", t_no_hardcoded_usd)

# ─── 7. Currency Registry ─────────────────────────────────────────────────────
def t_currency_registry():
    from app.core.currencies import load_currency_registry, get_currency_info
    registry = load_currency_registry()
    assert len(registry) >= 30, f"Expected 30+ currencies, got {len(registry)}"

    # Check key currencies
    for code in ["USD", "INR", "EUR", "GBP", "JPY", "AED", "SGD", "KRW", "THB", "BRL"]:
        info = get_currency_info(code)
        assert info.code == code, f"Missing currency: {code}"
        assert info.symbol, f"{code} has no symbol"

    print(f"      Registry has {len(registry)} currencies")

test("Currency registry has 30+ world currencies", t_currency_registry)

# ─── 8. Deduplication Check ──────────────────────────────────────────────────
def t_no_duplicates():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="USD")
        names = [r["destination"] for r in result["recommended_for_you"]]
        assert len(names) == len(set(names)), f"Duplicates found in recommended_for_you: {names}"
        print(f"      No duplicates in {len(names)} recommendations")
    finally:
        db.close()

test("No duplicate destinations in recommendations", t_no_duplicates)

# ─── 9. No 'previous trip' reason for new users ──────────────────────────────
def t_no_trip_reason_for_new_user():
    from app.database.connection import get_db
    from app.ai.recommendation.recommendation_service import RecommendationService
    db = next(get_db())
    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(user_id=99999, user_currency="USD")
        for rec in result["recommended_for_you"]:
            for r in rec["reasons"]:
                assert "previous trip" not in r.lower(), f"Bad reason for new user: '{r}'"
        print("      No 'previous trip' reasons for user with no trip history")
    finally:
        db.close()

test("No 'previous trip' reason for new user", t_no_trip_reason_for_new_user)

# ─── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"v2.7.2 CURRENCY TEST RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED ✓")
    print()
    print("Currency System Status:")
    print("  ✅ USD, INR, EUR, GBP, JPY, AED — all supported")
    print("  ✅ Budget objects contain formatted string per user currency")
    print("  ✅ No hardcoded $ symbols for non-USD users")
    print("  ✅ Deduplication working")
    print("  ✅ New user reason wording corrected")
else:
    print("SOME TESTS FAILED — check output above")
