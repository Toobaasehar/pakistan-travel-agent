"""
Explainable AI module for the budget prediction model.

For a given prediction, this tells you WHICH factors pushed the estimated
budget up or down, and by how much -- not just the final number.

Two engines are supported (chosen automatically):

1. SHAP (if the `shap` package is installed, e.g. on your local machine).
2. A built-in exact Shapley-value calculator (used when `shap` is NOT
   installed, e.g. on Vercel, where shap/numba/llvmlite are too heavy).
   It needs only numpy + pandas + scikit-learn, and returns the same
   response format, so the API endpoint and the agent work either way.

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
    #       {"feature": "province: Gilgit-Baltistan", "impact": 1450.2},
    #       {"feature": "category: mountains", "impact": 890.5},
    #       {"feature": "trip duration (days)", "impact": 320.1},
    #       ...
    #   ]
    # }

A positive impact means that factor pushed the budget UP for this
prediction; negative means it pushed the budget DOWN. Contributions are
sorted by absolute impact, largest first.
"""

import itertools
import math

try:
    import shap
except ImportError:  # shap is optional -- a built-in fallback is used instead
    shap = None

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from functools import lru_cache
from typing import Optional, List
from ml.predict_budget import apply_price_floor

MODEL_PATH = Path(__file__).parent / "budget_model.joblib"

# Reference values used by the built-in (non-SHAP) explainer to represent
# "an average trip" for the numeric inputs.
_DAYS_GRID = [1, 2, 3, 4, 5, 7]
_ACTIVITIES_GRID = [1, 2, 3, 4, 5]
_BACKGROUND_SIZE = 200


@lru_cache(maxsize=1)
def load_bundle():
    """Load the trained model bundle once and cache it in memory."""
    return joblib.load(MODEL_PATH)


# --------------------------------------------------------------------------
# Engine 1: SHAP (only used if the package is installed)
# --------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_explainer():
    """
    Build (and cache) a SHAP explainer for the underlying regressor.
    Uses TreeExplainer for tree-based models (fast, exact), falling back
    to the general-purpose Explainer with the saved training data as
    background for anything else (e.g. linear models).
    """
    if shap is None:
        raise RuntimeError("shap is not installed")

    bundle = load_bundle()
    model = bundle["pipeline"].named_steps["model"]

    try:
        return shap.TreeExplainer(model)
    except Exception:
        background = bundle.get("X_transformed")
        if background is None:
            background = np.zeros(
                (1, len(bundle["categorical_features"]) + len(bundle["numeric_features"]))
            )
        return shap.Explainer(model, background)


def _explain_with_shap(bundle, pipeline, X_input):
    """Return (base_value, contributions_list) using the shap package."""
    explainer = get_explainer()

    X_transformed = pipeline.named_steps["preprocess"].transform(X_input)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()

    shap_values = explainer(X_transformed)
    values = np.asarray(shap_values.values)[0]
    base_value = float(np.asarray(shap_values.base_values).flatten()[0])

    feature_names = bundle.get("feature_names")
    if feature_names is None:
        feature_names = pipeline.named_steps["preprocess"].get_feature_names_out().tolist()

    contributions = [
        {"feature": _clean_feature_name(name), "impact": round(float(val), 1)}
        for name, val in zip(feature_names, values)
        if abs(val) > 0.01  # skip near-zero / irrelevant one-hot columns
    ]
    return base_value, contributions


# --------------------------------------------------------------------------
# Engine 2: built-in exact Shapley values (no shap / numba / llvmlite needed)
# --------------------------------------------------------------------------
def _get_known_categories(preprocess) -> dict:
    """Read the category lists (provinces, categories) out of the fitted encoder."""
    known = {}
    for name, transformer, columns in getattr(preprocess, "transformers_", []):
        if name == "remainder" or transformer in ("drop", "passthrough"):
            continue
        encoder = transformer
        if hasattr(encoder, "steps"):  # a Pipeline -- take its last step
            encoder = encoder.steps[-1][1]
        if hasattr(encoder, "categories_"):
            for col, cats in zip(columns, encoder.categories_):
                known[col] = list(cats)
    return known


def _build_background(preprocess, province: str, category: str) -> pd.DataFrame:
    """A small, deterministic set of 'typical trips' to compare against."""
    known = _get_known_categories(preprocess)
    provinces = known.get("province") or [province]
    categories = known.get("category") or [category]

    rows = [
        {
            "province": p,
            "category": c,
            "recommended_days": d,
            "n_activities": a,
        }
        for p, c, d, a in itertools.product(
            provinces, categories, _DAYS_GRID, _ACTIVITIES_GRID
        )
    ]
    background = pd.DataFrame(rows)
    if len(background) > _BACKGROUND_SIZE:
        background = background.sample(
            n=_BACKGROUND_SIZE, random_state=0
        ).reset_index(drop=True)
    return background


def _explain_without_shap(pipeline, X_input):
    """
    Exact Shapley values over the 4 raw input features.

    With only 4 features there are just 16 feature subsets, so we can compute
    the values exactly (no approximation) using plain predictions from the
    pipeline. Returns (base_value, contributions_list).
    """
    features = list(X_input.columns)
    n = len(features)

    background = _build_background(
        pipeline.named_steps["preprocess"],
        province=X_input.iloc[0]["province"],
        category=X_input.iloc[0]["category"],
    )
    n_bg = len(background)
    row = X_input.iloc[0]

    # Prediction for every subset of "known" features, averaged over background.
    masks = list(range(1 << n))
    blocks = []
    for mask in masks:
        block = background.copy()
        for i, feat in enumerate(features):
            if (mask >> i) & 1:
                block[feat] = row[feat]
        blocks.append(block)

    preds = np.asarray(pipeline.predict(pd.concat(blocks, ignore_index=True)), dtype=float)
    value = {
        mask: float(preds[k * n_bg:(k + 1) * n_bg].mean())
        for k, mask in enumerate(masks)
    }

    # Shapley value of each feature.
    contributions = []
    for i, feat in enumerate(features):
        phi = 0.0
        for mask in masks:
            if (mask >> i) & 1:
                continue
            s = bin(mask).count("1")
            weight = math.factorial(s) * math.factorial(n - s - 1) / math.factorial(n)
            phi += weight * (value[mask | (1 << i)] - value[mask])

        if abs(phi) > 0.01:
            contributions.append(
                {"feature": _readable_input_label(feat, row[feat]), "impact": round(phi, 1)}
            )

    return value[0], contributions


def _readable_input_label(feature: str, val) -> str:
    if feature == "province":
        return f"province: {val}"
    if feature == "category":
        return f"category: {val}"
    if feature == "recommended_days":
        return "trip duration (days)"
    if feature == "n_activities":
        return "number of activities"
    return feature


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def explain_budget_prediction(
    province: str,
    category: str,
    recommended_days: int,
    activities: Optional[List[str]] = None,
    top_n: int = 6,
) -> dict:
    """
    Explain a single budget prediction: which features pushed it up/down.

    Same inputs as predict_budget() in predict_budget.py, plus top_n to
    limit how many contributing factors are returned (most impactful first).
    """
    bundle = load_bundle()
    pipeline = bundle["pipeline"]

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

    base_value, contributions = None, None

    # Prefer SHAP when it's available; on any problem, use the built-in engine.
    if shap is not None:
        try:
            base_value, contributions = _explain_with_shap(bundle, pipeline, X_input)
        except Exception:
            base_value, contributions = None, None

    if contributions is None:
        base_value, contributions = _explain_without_shap(pipeline, X_input)

    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)
    contributions = contributions[:top_n]

    # Match predict_budget()'s headline number exactly (same floor/rounding
    # rule) so /predict-budget and /predict-budget/explain never disagree on
    # the number shown to the user for identical inputs. The base_value and
    # contributions below explain the raw model output -- only this one
    # reported field is floored to match.
    return {
        "predicted_budget_per_day": apply_price_floor(predicted),
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