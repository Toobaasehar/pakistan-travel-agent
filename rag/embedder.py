"""
rag/embedder.py
===============
Text embedding for RAG.

Primary:  sentence-transformers (all-MiniLM-L6-v2) — semantic vectors
Fallback: TF-IDF vectorizer from scikit-learn — keyword-based, no extra deps

The embedder is selected automatically at import time.
"""

from typing import List
import numpy as np

# ─── Try to load sentence-transformers ────────────────────────────────────────
_SBERT_AVAILABLE = False
_sbert_model = None

try:
    from sentence_transformers import SentenceTransformer
    _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
    _SBERT_AVAILABLE = True
    print("[RAG] Embedder: sentence-transformers (all-MiniLM-L6-v2) ✓")
except Exception:
    print("[RAG] Embedder: sentence-transformers not available — using TF-IDF fallback")


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
    print(f"[RAG] TF-IDF vectorizer fitted on {len(texts)} texts, vocab={_tfidf_vectorizer.vocabulary_.__len__()}")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Encode a list of text strings into a float32 numpy matrix.
    Shape: (len(texts), embedding_dim)

    Uses sentence-transformers if available, TF-IDF otherwise.
    """
    if _SBERT_AVAILABLE:
        vecs = _sbert_model.encode(
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
    if _SBERT_AVAILABLE:
        vec = _sbert_model.encode([text], normalize_embeddings=True)
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
    return _SBERT_AVAILABLE
