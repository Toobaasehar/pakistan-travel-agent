"""
Explainable AI module for the budget prediction model, using SHAP.

For a given prediction, this tells you WHICH factors pushed the estimated
budget up or down, and by how much — not just the final number.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from functools import lru_cache

# In imports ke neechay agar red line aye to Step 2 follow karein
import numpy as np
import pandas as pd
import joblib
import shap

MODEL_PATH = Path(__file__).parent / "budget_model.joblib"


@lru_cache(maxsize=1)
def load_bundle():
    """Load the trained model bundle once and cache it in memory."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}. Pehle model train karein.")
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_explainer():
    """Build (and cache) a SHAP explainer for the regressor."""
    bundle = load_bundle()
    model = bundle["pipeline"].named_steps["model"]

    try:
        return shap.TreeExplainer(model)
    except Exception:
        return shap.Explainer(model, bundle["X_transformed"])


def explain_budget_prediction(
    province: str,
    category: str,
    recommended_days: int,
    activities: Optional[List[str]] = None,
    top_n: int = 6,
) -> Dict[str, Any]:
    """
    Explain a single budget prediction: which features pushed it up/down.
    """
    bundle = load_bundle()
    pipeline = bundle["pipeline"]
    explainer = get_explainer()

    n_activities = len(activities) if activities else 1

    X_input = pd.DataFrame(
        [
            {
                "province": province,
                "category": category,
                "recommended_days": recommended_days,
                "n_activities": n_activities,
            }
        ]
    )

    predicted = float(pipeline.predict(X_input)[0])

    X_transformed = pipeline.named_steps["preprocess"].transform(X_input)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()

    shap_values = explainer(X_transformed)
    values = np.asarray(shap_values.values)[0]
    base_value = float(np.asarray(shap_values.base_values).flatten()[0])

    feature_names = bundle["feature_names"]
    contributions = [
        {"feature": _clean_feature_name(name), "impact": round(float(val), 1)}
        for name, val in zip(feature_names, values)
        if abs(val) > 0.01
    ]
    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)
    contributions = contributions[:top_n]

    return {
        "predicted_budget_per_day": round(predicted, -2),
        "base_value": round(base_value, 1),
        "contributions": contributions,
    }


def _clean_feature_name(raw_name: str) -> str:
    """Turn sklearn ColumnTransformer names into human-readable labels."""
    name = raw_name.replace("remainder__", "").replace("cat__", "")
    name = name.replace("province_", "province: ").replace("category_", "category: ")
    if name == "recommended_days":
        return "trip duration (days)"
    if name == "n_activities":
        return "number of activities"
    return name


if __name__ == "__main__":
    try:
        result = explain_budget_prediction(
            province="Gilgit-Baltistan",
            category="mountains",
            recommended_days=2,
            activities=["hiking", "camping", "photography"],
        )
        print(f"Predicted: {result['predicted_budget_per_day']} PKR/day")
        print(f"Base value (avg across all destinations): {result['base_value']}")
        print("Top contributing factors:")
        for c in result["contributions"]:
            sign = "+" if c["impact"] >= 0 else ""
            print(f"  {c['feature']:35s} {sign}{c['impact']}")
    except Exception as e:
        print(f"Error: {e}")