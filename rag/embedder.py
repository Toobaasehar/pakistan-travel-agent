"""
rag/embedder.py
===============
Text embedding for RAG.

Primary:  sentence-transformers (all-MiniLM-L6-v2) — semantic vectors (loaded lazily on demand)
Fallback: TF-IDF vectorizer from scikit-learn — keyword-based, fast, no extra deps

The embedder is loaded lazily on first use to ensure instant server cold starts.
"""

import os
from typing import List
import numpy as np

# ─── Lazy sentence-transformers loader ───────────────────────────────────────
_sbert_model = None
_sbert_checked = False


def _get_sbert_model():
    """Lazily load SentenceTransformer only when first needed (never at import time)."""
    global _sbert_model, _sbert_checked
    if _sbert_checked:
        return _sbert_model
    _sbert_checked = True

    if os.environ.get("VERCEL"):
        # Always use fast TF-IDF fallback on Vercel to stay within serverless limits
        return None

    try:
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[RAG] Embedder: sentence-transformers (all-MiniLM-L6-v2) ✓")
    except Exception:
        print("[RAG] Embedder: sentence-transformers not available — using TF-IDF fallback")
        _sbert_model = None

    return _sbert_model


# ─── TF-IDF Fallback state ─────────────────────────────────────────────────────
_tfidf_vectorizer = None
_tfidf_matrix = None
_tfidf_corpus: List[str] = []


def fit_tfidf(texts: List[str]) -> None:
    """Fit the TF-IDF vectorizer on a corpus (called once during index build)."""
    global _tfidf_vectorizer, _tfidf_matrix, _tfidf_corpus
    from sklearn.feature_extraction.text import TfidfVectorizer
    _tfidf_corpus = texts
    _tfidf_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=8000,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(texts)
    print(f"[RAG] TF-IDF vectorizer fitted on {len(texts)} texts, vocab={len(_tfidf_vectorizer.vocabulary_)}")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Encode a list of text strings into a float32 numpy matrix.
    Shape: (len(texts), embedding_dim)

    Uses sentence-transformers if available, TF-IDF otherwise.
    """
    model = _get_sbert_model()
    if model is not None:
        vecs = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(vecs, dtype=np.float32)
    else:
        # TF-IDF path: fit if not yet fitted
        global _tfidf_vectorizer, _tfidf_matrix
        if _tfidf_vectorizer is None:
            fit_tfidf(texts)
        mat = _tfidf_vectorizer.transform(texts)
        # L2 normalize rows
        from sklearn.preprocessing import normalize
        mat = normalize(mat, norm="l2")
        return mat.toarray().astype(np.float32)


def embed_query(text: str) -> np.ndarray:
    """
    Encode a single query string into a 1D float32 vector.
    """
    model = _get_sbert_model()
    if model is not None:
        vec = model.encode([text], normalize_embeddings=True)
        return np.array(vec[0], dtype=np.float32)
    else:
        if _tfidf_vectorizer is None:
            raise RuntimeError("[RAG] TF-IDF vectorizer is not fitted yet. Call embed_texts() first.")
        mat = _tfidf_vectorizer.transform([text])
        from sklearn.preprocessing import normalize
        mat = normalize(mat, norm="l2")
        return mat.toarray()[0].astype(np.float32)


def is_semantic() -> bool:
    """Returns True if using sentence-transformers (semantic), False if TF-IDF."""
    return _get_sbert_model() is not None
