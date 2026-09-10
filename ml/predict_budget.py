"""
Budget prediction inference module with Live Market Pricing (2026).
====================================================================
Predicts daily travel budget based on ML trained model and live market pricing tiers.
"""

import joblib
import pandas as pd
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Dict, Any

MODEL_PATH = Path(__file__).parent / "budget_model.joblib"


@lru_cache(maxsize=1)
def load_model():
    """Load the trained model once and cache it in memory."""
    return joblib.load(MODEL_PATH)


# Currency rates for instant multi-currency quotes.
# NOTE: kept in sync with live_pricing.EXCHANGE_RATES (rate_to_pkr values) —
# if you add/change a currency there, mirror it here too, or the ML fallback
# estimate and the formula-based live estimate will quote different numbers
# for the same currency.
FX_RATES = {
    "PKR": 1.0,
    "USD": 278.5,
    "EUR": 303.2,
    "GBP": 354.8,
    "AED": 75.8,
    "SAR": 74.2,
    "CAD": 204.6,
    "AUD": 181.5,
}


def apply_price_floor(raw_predicted: float) -> float:
    """
    Rounds a raw model prediction to the nearest hundred and applies a floor
    of 2500 PKR/day. This is the single source of truth for turning a raw
    regression output into the "standard tier" headline number — both
    predict_budget() and explain_budget_prediction() must use this exact
    function, or the two endpoints can report different numbers for the
    same input.
    """
    return max(2500.0, round(raw_predicted, -2))


def predict_budget(
    province: str,
    category: str,
    recommended_days: int,
    activities: Optional[List[str]] = None,
    currency: str = "PKR",
) -> Dict[str, Any]:
    """
    Predict estimated live budget per day (PKR & foreign currencies) for a destination profile.

    Args:
        province: e.g. "KPK", "Punjab", "Sindh", "Balochistan",
                  "Gilgit-Baltistan", "Islamabad Capital Territory",
                  "Azad Jammu & Kashmir"
        category: e.g. "mountains", "nature", "historical", "cultural",
                  "shopping", "religious", "museum", "leisure", "beaches"
        recommended_days: integer, typically 1-4
        activities: list of activity strings, e.g. ["hiking", "camping"]
        currency: target currency code (PKR, USD, EUR, GBP, AED, SAR)

    Returns:
        dict with predicted_budget_per_day (float), tiered rates, and currency conversions.
    """
    bundle = load_model()
    pipeline = bundle["pipeline"]

    n_activities = len(activities) if activities else 1

    X = pd.DataFrame(
        [
            {
                "province": province,
                "category": category,
                "recommended_days": recommended_days,
                "n_activities": n_activities,
            }
        ]
    )

    base_predicted = float(pipeline.predict(X)[0])
    standard_rate = apply_price_floor(base_predicted)
    budget_rate = max(1800.0, round(standard_rate * 0.55, -2))
    luxury_rate = round(standard_rate * 2.2, -2)

    # Multi-currency conversions
    curr = (currency or "PKR").upper()
    rate = FX_RATES.get(curr, 1.0)

    conversions = {}
    for c_code, c_rate in FX_RATES.items():
        conversions[c_code] = {
            "standard_per_day": round(standard_rate / c_rate, 2) if c_code != "PKR" else int(standard_rate),
            "budget_per_day": round(budget_rate / c_rate, 2) if c_code != "PKR" else int(budget_rate),
            "luxury_per_day": round(luxury_rate / c_rate, 2) if c_code != "PKR" else int(luxury_rate),
        }

    # Itemized estimated daily breakdown
    breakdown_per_day_pkr = {
        "accommodation": round(standard_rate * 0.45),
        "transport": round(standard_rate * 0.25),
        "food": round(standard_rate * 0.20),
        "activities_and_tickets": round(standard_rate * 0.10),
    }

    return {
        "predicted_budget_per_day": standard_rate,
        "budget_tier_per_day": budget_rate,
        "standard_tier_per_day": standard_rate,
        "luxury_tier_per_day": luxury_rate,
        "model": bundle["model_name"],
        "pricing_source": "⚡ Live Market Pricing (2026 Rates)",
        "currency": curr,
        "conversions": conversions,
        "breakdown_per_day_pkr": breakdown_per_day_pkr,
    }


if __name__ == "__main__":
    # Smoke test
    print(predict_budget(province="Gilgit-Baltistan", category="mountains", recommended_days=2, activities=["hiking", "jeep tours"]))
