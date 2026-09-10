"""
Explainable AI module for the budget prediction model, using SHAP.

For a given prediction, this tells you WHICH factors pushed the estimated
budget up or down, and by how much — not just the final number.

Usage:

    from explain_budget import explain_budget_prediction

    result = explain_budget_prediction(
        province="Gilgit-Baltistan",
        category="mountains",
        recommended_days=2,
        activities=["hiking", "camping", "photography"],
    )
    # result = {
    #   "predicted_budget_per_day": 7000.0,
    #   "base_value": 4230.1,               <- average budget across all destinations
    #   "contributions": [
    #       {"feature": "province_Gilgit-Baltistan", "impact": 1450.2},
    #       {"feature": "category_mountains", "impact": 890.5},
    #       {"feature": "recommended_days", "impact": 320.1},
    #       ...
    #   ]
    # }

A positive impact means that factor pushed the budget UP for this
prediction; negative means it pushed the budget DOWN. Contributions are
sorted by absolute impact, largest first.
"""

import shap
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from functools import lru_cache

MODEL_PATH = Path(__file__).parent / "budget_model.joblib"


@lru_cache(maxsize=1)
def load_bundle():
    """Load the trained model bundle once and cache it in memory."""
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_explainer():
    """
    Build (and cache) a SHAP explainer for the underlying regressor.
    Uses TreeExplainer for tree-based models (fast, exact), falling back
    to the general-purpose Explainer with the saved training data as
    background for anything else (e.g. linear models).
    """
    bundle = load_bundle()
    model = bundle["pipeline"].named_steps["model"]

    try:
        return shap.TreeExplainer(model)
    except Exception:
        # Fallback path (non-tree models) needs background data — recompute it
        # from the pipeline if the saved bundle predates this field.
        background = bundle.get("X_transformed")
        if background is None:
            # No training data cached — approximate with the single-row input
            # at call time isn't possible here, so this is a best-effort fallback.
            background = np.zeros((1, len(bundle["categorical_features"]) + len(bundle["numeric_features"])))
        return shap.Explainer(model, background)


def explain_budget_prediction(
    province: str,
    category: str,
    recommended_days: int,
    activities: list[str] | None = None,
    top_n: int = 6,
) -> dict:
    """
    Explain a single budget prediction: which features pushed it up/down.

    Same inputs as predict_budget() in predict_budget.py, plus top_n to
    limit how many contributing factors are returned (most impactful first).
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

    # feature_names: prefer the saved bundle (faster), but fall back to computing
    # it fresh from the pipeline's preprocessor if the bundle predates this field
    # (e.g. a budget_model.joblib retrained before explainability was added).
    feature_names = bundle.get("feature_names")
    if feature_names is None:
        feature_names = pipeline.named_steps["preprocess"].get_feature_names_out().tolist()
    contributions = [
        {"feature": _clean_feature_name(name), "impact": round(float(val), 1)}
        for name, val in zip(feature_names, values)
        if abs(val) > 0.01  # skip near-zero / irrelevant one-hot columns
    ]
    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)
    contributions = contributions[:top_n]

    return {
        "predicted_budget_per_day": round(predicted, -2),
        "base_value": round(base_value, 1),
        "contributions": contributions,
    }


def _clean_feature_name(raw_name: str) -> str:
    """Turn sklearn's ColumnTransformer names into human-readable labels."""
    name = raw_name.replace("remainder__", "").replace("cat__", "")
    name = name.replace("province_", "province: ").replace("category_", "category: ")
    if name == "recommended_days":
        return "trip duration (days)"
    if name == "n_activities":
        return "number of activities"
    return name


if __name__ == "__main__":
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