"""
Similar-destinations inference module.

Usage in your FastAPI app / agent.py:

    from similar_destinations import get_similar_destinations

    result = get_similar_destinations(destination_id=1, top_n=5)
    # result = {"destination_id": 1, "similar": [{"id": 7, "distance": 0.42}, ...]}

Approach: destinations are grouped into 9 clusters (province, category, budget,
duration, activity-count). "Similar" destinations are the closest neighbors
by Euclidean distance in that same feature space — computed within the same
cluster first, and only falling back to the full dataset if the cluster is
too small to return enough results.
"""

import joblib
import numpy as np
from pathlib import Path
from functools import lru_cache

MODEL_PATH = Path(__file__).parent / "clustering_model.joblib"


@lru_cache(maxsize=1)
def load_model():
    """Load the trained clustering bundle once and cache it in memory."""
    return joblib.load(MODEL_PATH)


def get_similar_destinations(destination_id: int, top_n: int = 5) -> dict:
    """
    Find the top_n most similar destinations to the given destination_id.

    Args:
        destination_id: the destination's integer id (from the destinations table)
        top_n: how many similar destinations to return

    Returns:
        dict with the query id, its cluster, and a list of similar destinations
        (id + distance, sorted closest-first). Empty list if the id isn't found.
    """
    bundle = load_model()
    ids = bundle["destination_ids"]
    X = bundle["feature_matrix"]
    labels = bundle["kmeans"].labels_

    if destination_id not in ids:
        return {"destination_id": destination_id, "cluster": None, "similar": []}

    idx = ids.index(destination_id)
    query_vector = X[idx]
    query_cluster = int(labels[idx])

    # Prefer candidates from the same cluster
    same_cluster_idx = [i for i, lbl in enumerate(labels) if lbl == query_cluster and i != idx]

    # If the cluster is too small, widen to the full dataset
    if len(same_cluster_idx) < top_n:
        candidate_idx = [i for i in range(len(ids)) if i != idx]
    else:
        candidate_idx = same_cluster_idx

    distances = [
        (i, float(np.linalg.norm(X[i] - query_vector)))
        for i in candidate_idx
    ]
    distances.sort(key=lambda pair: pair[1])
    top = distances[:top_n]

    return {
        "destination_id": destination_id,
        "cluster": query_cluster,
        "similar": [
            {"id": ids[i], "distance": round(dist, 3)}
            for i, dist in top
        ],
    }


if __name__ == "__main__":
    # quick smoke test — id 1 is Hunza Valley
    result = get_similar_destinations(destination_id=1, top_n=5)
    print(result)
