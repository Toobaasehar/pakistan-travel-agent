"""
Train a budget-per-day prediction model on the destinations table in travel.db.
Saves model directly to the ml folder.
"""

import sqlite3
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ✅ Sahi Paths jo har jagah se theek chalengy
ML_DIR = Path(__file__).parent
BASE_DIR = ML_DIR.parent
DB_PATH = BASE_DIR / "travel.db" if (BASE_DIR / "travel.db").exists() else Path("travel.db")
MODEL_PATH = ML_DIR / "budget_model.joblib"

CATEGORICAL_FEATURES = ["province", "category"]
NUMERIC_FEATURES = ["recommended_days", "n_activities"]
TARGET = "estimated_budget_per_day"


def load_data(db_path) -> pd.DataFrame:
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM destinations", conn)
    conn.close()
    df["n_activities"] = df["activities"].apply(
        lambda x: len(str(x).split(",")) if x else 0
    )
    return df


def build_pipeline(model) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def evaluate(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, name: str) -> float:
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    mae_scores = -cross_val_score(
        pipeline, X, y, cv=cv, scoring="neg_mean_absolute_error"
    )
    r2_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="r2")
    print(f"{name}:")
    print(f"  CV MAE : {mae_scores.mean():.0f} (+/- {mae_scores.std():.0f}) PKR/day")
    print(f"  CV R^2 : {r2_scores.mean():.3f} (+/- {r2_scores.std():.3f})")
    return mae_scores.mean()


def main():
    if not DB_PATH.exists():
        print(f"❌ Error: {DB_PATH} nahi mili! Pehle 'python seed.py' chalayein.")
        return

    df = load_data(DB_PATH)
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df[TARGET]

    print(f"Training on {len(df)} destinations\n")

    candidates = {
        "Ridge Regression": build_pipeline(Ridge(alpha=1.0)),
        "Random Forest": build_pipeline(
            RandomForestRegressor(
                n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=42
            )
        ),
    }

    scores = {}
    for name, pipeline in candidates.items():
        scores[name] = evaluate(pipeline, X, y, name)
        print()

    best_name = min(scores, key=scores.get)
    print(f"Best model: {best_name} (lowest CV MAE)")

    best_pipeline = candidates[best_name]
    best_pipeline.fit(X, y)

    preprocess_step = best_pipeline.named_steps["preprocess"]
    X_transformed = preprocess_step.transform(X)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()
    feature_names = preprocess_step.get_feature_names_out().tolist()

    # ✅ Saves directly into ml/budget_model.joblib
    joblib.dump(
        {
            "pipeline": best_pipeline,
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "model_name": best_name,
            "X_transformed": X_transformed,
            "feature_names": feature_names,
        },
        MODEL_PATH,
    )
    print(f"\n✅ Saved trained model successfully to {MODEL_PATH}")


if __name__ == "__main__":
    main()