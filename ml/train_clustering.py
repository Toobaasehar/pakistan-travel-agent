"""
Train a KMeans clustering model to group similar destinations, and save
everything needed to power a "similar destinations" recommendation feature.

k=9 was chosen via silhouette score exploration (see explore_clusters.py) —
it gave the best cluster separation (0.415) with reasonably balanced group sizes.
"""

import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from pathlib import Path

DB_PATH = "travel.db"
MODEL_PATH = Path(__file__).parent / "clustering_model.joblib"
N_CLUSTERS = 9

CATEGORICAL_FEATURES = ["province", "category"]
NUMERIC_FEATURES = ["estimated_budget_per_day", "recommended_days", "n_activities"]


def load_data(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM destinations", conn)
    conn.close()
    df["n_activities"] = df["activities"].apply(
        lambda x: len(str(x).split(",")) if x else 0
    )
    return df


def main():
    df = load_data(DB_PATH)

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    X = preprocessor.fit_transform(df[CATEGORICAL_FEATURES + NUMERIC_FEATURES])
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    score = silhouette_score(X, labels)

    print(f"Trained KMeans with k={N_CLUSTERS}")
    print(f"Silhouette score: {score:.3f}")
    print(f"Cluster sizes: {sorted([list(labels).count(i) for i in set(labels)])}")

    df["cluster"] = labels

    # Save everything needed for inference:
    # - the fitted preprocessor + kmeans model (to cluster NEW destinations later)
    # - the full feature matrix X (dense) so we can compute distances between
    #   any two destinations already in the dataset, without refitting
    # - destination ids aligned with rows of X, for lookups
    joblib.dump(
        {
            "preprocessor": preprocessor,
            "kmeans": kmeans,
            "feature_matrix": X,
            "destination_ids": df["id"].tolist(),
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "n_clusters": N_CLUSTERS,
        },
        MODEL_PATH,
    )
    print(f"\nSaved clustering model to {MODEL_PATH}")

    # Quick sanity print: show cluster membership for a few known destinations
    print("\n--- Sample cluster assignments ---")
    print(df[["name", "province", "category", "estimated_budget_per_day", "cluster"]].head(10))


if __name__ == "__main__":
    main()
