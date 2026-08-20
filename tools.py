"""
Tool functions — the building blocks the AI agent will call in Phase 4.
===========================================================================
Each function here is PLAIN PYTHON, callable and testable on its own,
with no AI involved yet. This is deliberate: prove the logic works
before adding the complexity of an AI deciding when to call it.

In Phase 4, we describe these same functions to Claude so IT can
decide which one to call and with what arguments — but the functions
themselves don't change.
"""

from typing import Optional
from database import SessionLocal
from models import Destination


def search_destinations(
    province: Optional[str] = None,
    district: Optional[str] = None,
    max_budget_per_day: Optional[int] = None,
    category: Optional[str] = None,
):
    """
    Returns destinations matching optional filters.
    All filters are optional so the agent can call this loosely
    ("show me mountain places") or precisely ("KPK, Swat, under 7000/day").
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


def estimate_cost(destination_id: int, days: int, people: int = 1):
    """
    Formula-based cost estimate — NOT live pricing.
    Deliberately simple and transparent so every number is explainable,
    matching the project's rule: never present an estimate as an exact fact.
    """
    db = SessionLocal()
    try:
        d = db.query(Destination).filter(Destination.id == destination_id).first()
        if not d:
            return None

        per_day = d.estimated_budget_per_day or 5000
        days = max(1, days)
        people = max(1, people)

        accommodation = per_day * 0.4 * days * people
        food = per_day * 0.3 * days * people
        activities = per_day * 0.2 * days * people
        transport = per_day * 0.1 * days * people

        total = accommodation + food + activities + transport

        return {
            "destination": d.name,
            "days": days,
            "people": people,
            "breakdown_pkr": {
                "accommodation": round(accommodation),
                "food": round(food),
                "activities": round(activities),
                "transport": round(transport),
            },
            "estimated_total_pkr": round(total),
            "note": "Formula-based estimate, not live pricing.",
        }
    finally:
        db.close()


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
