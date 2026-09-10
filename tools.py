"""
Tool functions & Tests — Unified File
=====================================
Contains the core database search, live pricing, and itinerary generation functions.
Includes self-testing when run directly:
    python tools.py
"""

import sys
from typing import Optional
from database import SessionLocal
from models import Destination
from live_pricing import calculate_live_pricing, convert_from_pkr, get_exchange_rates


def search_destinations(
    province: Optional[str] = None,
    district: Optional[str] = None,
    max_budget_per_day: Optional[int] = None,
    category: Optional[str] = None,
):
    """
    Returns destinations matching optional filters.
    All filters are optional so the agent can call this loosely or precisely.
    """
    db = SessionLocal()
    try:
        query = db.query(Destination)
        if province:
            query = query.filter(Destination.province.ilike(f"%{province}%"))
        if district:
            query = query.filter(Destination.district.ilike(f"%{district}%"))
        if max_budget_per_day:
            query = query.filter(Destination.estimated_budget_per_day <= max_budget_per_day)
        if category:
            query = query.filter(Destination.category.ilike(f"%{category}%"))
        results = query.all()
        return [
            {
                "id": d.id,
                "name": d.name,
                "province": d.province,
                "district": d.district,
                "category": d.category,
                "estimated_budget_per_day": d.estimated_budget_per_day,
                "recommended_days": d.recommended_days,
            }
            for d in results
        ]
    finally:
        db.close()


def get_destination_details(destination_id: int):
    """Returns the full record for one destination, or None if not found."""
    db = SessionLocal()
    try:
        d = db.query(Destination).filter(Destination.id == destination_id).first()
        if not d:
            return None
        return {
            "id": d.id,
            "name": d.name,
            "province": d.province,
            "district": d.district,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "description": d.description,
            "best_season": d.best_season,
            "recommended_days": d.recommended_days,
            "estimated_budget_per_day": d.estimated_budget_per_day,
            "activities": d.activities,
        }
    finally:
        db.close()


def estimate_cost(
    destination_id: int,
    days: int,
    people: int = 1,
    travel_style: str = "standard",
    transport_mode: Optional[str] = None,
    currency: str = "PKR",
    from_city: Optional[str] = None,
    include_hotel: bool = True,
):
    """
    Dynamic Live Market Pricing (2026 Rates) for a destination.
    Uses real hotel rates, route-based transport (when from_city is given),
    authentic dining costs, and multi-currency conversion.
    """
    db = SessionLocal()
    try:
        d = db.query(Destination).filter(Destination.id == destination_id).first()
        if not d:
            return None

        days = max(1, days)
        people = max(1, people)

        pricing = calculate_live_pricing(
            destination_name=d.name,
            province=d.province,
            district=d.district,
            category=d.category,
            best_season=d.best_season,
            days=days,
            people=people,
            travel_style=travel_style,
            transport_mode=transport_mode,
            currency=currency,
            from_city=from_city,
            include_hotel=include_hotel,
        )

        return {
            "destination": d.name,
            "days": days,
            "people": people,
            "travel_style": pricing["travel_style"],
            "travel_style_label": pricing["travel_style_label"],
            "transport_mode": pricing["transport_mode"],
            "transport_label": pricing["transport_label"],
            "from_city": pricing["from_city"],
            "distance_km": pricing["distance_km"],
            "route_note": pricing["route_note"],
            "include_hotel": pricing["include_hotel"],
            "dining_style": pricing["dining_style"],
            "breakdown_pkr": pricing["breakdown_pkr"],
            "breakdown_converted": pricing["breakdown_converted"],
            # total_pkr is the canonical field. estimated_total_pkr is kept as
            # an alias only because test_all.py and older callers already
            # depend on that name -- don't let the two values drift apart.
            "total_pkr": pricing["total_pkr"],
            "estimated_total_pkr": pricing["total_pkr"],
            "converted_total": pricing["converted_total"],
            "currency": pricing["currency"],
            "tier_comparisons": pricing["tier_comparisons"],
            "seasonal_multiplier": pricing["seasonal_multiplier"],
            "season_status": pricing["season_status"],
            "pricing_source": pricing["pricing_source"],
            "note": "⚡ Verified Live Market Pricing (2026 Rates).",
        }
    finally:
        db.close()


def get_live_trip_cost(
    destination_id: int,
    days: int,
    people: int = 1,
    travel_style: str = "standard",
    transport_mode: Optional[str] = None,
    currency: str = "PKR",
    from_city: Optional[str] = None,
    include_hotel: bool = True,
):
    """Alias for estimate_cost with live pricing parameters."""
    return estimate_cost(
        destination_id=destination_id,
        days=days,
        people=people,
        travel_style=travel_style,
        transport_mode=transport_mode,
        currency=currency,
        from_city=from_city,
        include_hotel=include_hotel,
    )


def generate_itinerary(destination_id: int, days: int):
    """
    Builds a structured day-by-day itinerary skeleton.
    Handles 1-day day trips and multi-day stays cleanly.
    """
    db = SessionLocal()
    try:
        d = db.query(Destination).filter(Destination.id == destination_id).first()
        if not d:
            return None

        days = max(1, days)
        raw_activities = [a.strip() for a in (d.activities or "").split(",") if a.strip()]
        activities_list = raw_activities if raw_activities else ["sightseeing & photography", "cultural exploration"]

        itinerary = []
        if days == 1:
            main_act = activities_list[0] if activities_list else "sightseeing"
            itinerary.append({
                "day": 1,
                "plan": f"Day trip in {d.name}: morning arrival, guided exploration ({main_act}), local cuisine, and evening departure."
            })
        else:
            for day_num in range(1, days + 1):
                if day_num == 1:
                    plan = f"Arrival in {d.name}, check-in, orientation and light exploration."
                elif day_num == days:
                    plan = f"Final morning in {d.name}, souvenir shopping / photography, and departure."
                else:
                    activity = activities_list[(day_num - 2) % len(activities_list)]
                    plan = f"Full day: dedicated {activity} around {d.name}."
                itinerary.append({"day": day_num, "plan": plan})

        return {"destination": d.name, "total_days": days, "itinerary": itinerary}
    finally:
        db.close()


# =====================================================================
# SELF-TESTING BLOCK (Yeh tabhi chalega jab direct run karogy)
# =====================================================================
if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("--- Running Tools Self-Tests ---")

    print("\n=== Test 1: search_destinations (all) ===")
    print(search_destinations()[:3])  # pehle 3 dikhayega taake screen clutter na ho

    print("\n=== Test 2: search_destinations (province=KPK) ===")
    print(search_destinations(province="KPK")[:3])

    print("\n=== Test 3: search_destinations (max_budget_per_day=5000) ===")
    print(search_destinations(max_budget_per_day=5000)[:3])

    print("\n=== Test 4: get_destination_details (id=1) ===")
    print(get_destination_details(1))

    print("\n=== Test 5: estimate_cost (id=1, days=4, people=2) ===")
    print(estimate_cost(1, days=4, people=2))

    print("\n=== Test 6: generate_itinerary (id=1, days=4) ===")
    print(generate_itinerary(1, days=4))

    print("\n--- All Tests Finished Successfully! ---")