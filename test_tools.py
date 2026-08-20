"""
Manual test script for Phase 3 tool functions.
==================================================
Run this to prove each function works correctly BEFORE we let an AI
call them. If something breaks here, it's a plain Python bug — much
easier to fix than debugging through an AI's tool-calling layer.

Run with:
    python test_tools.py
"""

from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary

print("=== Test 1: search_destinations (all) ===")
print(search_destinations())

print("\n=== Test 2: search_destinations (province=KPK) ===")
print(search_destinations(province="KPK"))

print("\n=== Test 3: search_destinations (max_budget_per_day=5000) ===")
print(search_destinations(max_budget_per_day=5000))

print("\n=== Test 4: get_destination_details (id=1) ===")
print(get_destination_details(1))

print("\n=== Test 5: estimate_cost (id=1, days=4, people=2) ===")
print(estimate_cost(1, days=4, people=2))

print("\n=== Test 6: generate_itinerary (id=1, days=4) ===")
print(generate_itinerary(1, days=4))
