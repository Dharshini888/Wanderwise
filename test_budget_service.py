import sys
import os
import io

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.budget_allocation_service import BudgetAllocationService

print("Testing BudgetAllocationService for Agra reproduction scenario:")
plan = BudgetAllocationService.calculate_plan(
    total_budget=200000.0,
    currency='INR',
    tier='Ultra Luxury',
    destination='Agra',
    origin_city='Coimbatore',
    days=8,
    adults=10,
    children=0,
    transport_mode='Mixed Transport',
    accommodation_preference='hotel'
)

print(f"Tier Name: {plan['tier_name']}")
print(f"Total User Budget: {plan['formatted_user_budget']}")
print(f"Total Estimated Cost: {plan['formatted_total_estimated_cost']}")
print(f"Is Feasible: {plan['is_feasible']}")
print(f"Feasibility Status: {plan['feasibility_status']}")
print(f"Feasibility Color: {plan['feasibility_color']}")
print(f"Shortfall: {plan['formatted_shortfall']} (+{plan['shortfall_percentage']}%)")
print(f"Categories Count: {len(plan['categories'])}")

cat_sum = sum(c['amount'] for c in plan['categories'])
print(f"Sum of Categories: {cat_sum} INR (Expected: 200000.0 INR)")
assert abs(cat_sum - 200000.0) < 0.01, f"Category sum {cat_sum} does not match budget 200000.0"

for c in plan['categories']:
    print(f"  {c['label']} ({c['percentage']}%): {c['formatted']}")

print(f"\nFeasibility Note: {plan['feasibility_notes'][0]}")
print("\n[SUCCESS] BudgetAllocationService Agra verification passed!")
