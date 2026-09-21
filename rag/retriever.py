"""
rag/retriever.py
================
Builds and queries a vector index over the Pakistan travel knowledge base.

Primary backend:  FAISS (flat cosine, no GPU required)
Fallback backend: sklearn cosine_similarity (pure Python, zero extra deps beyond numpy)

The index is built once on first use and cached to rag/index_cache/
for fast subsequent loads.
"""

import os
import json
import pickle
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional

from .knowledge_base import build_knowledge_base
from .embedder import embed_texts, embed_query, fit_tfidf, is_semantic

# Cache directory (rag/index_cache/)
CACHE_DIR = (
    "/tmp/index_cache"
    if os.environ.get("VERCEL")
    else os.path.join(os.path.dirname(__file__), "index_cache")
)
CHUNKS_CACHE = os.path.join(CACHE_DIR, "chunks.pkl")
VECTORS_CACHE = os.path.join(CACHE_DIR, "vectors.npy")
FAISS_INDEX_CACHE = os.path.join(CACHE_DIR, "faiss.index")
TFIDF_CACHE = os.path.join(CACHE_DIR, "tfidf.pkl")
META_CACHE = os.path.join(CACHE_DIR, "meta.json")

# Try to import FAISS
_FAISS_AVAILABLE = False
try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    pass


def _data_hash() -> str:
    """Simple content hash to detect when JSON data files change."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    h = hashlib.md5()
    for root, dirs, files in os.walk(data_dir):
        dirs.sort()
        for fn in sorted(files):
            if fn.endswith(".json"):
                fp = os.path.join(root, fn)
                h.update(fn.encode())
                h.update(str(os.path.getmtime(fp)).encode())
    return h.hexdigest()


class RAGRetriever:
    """
    Singleton-style retriever — builds the index once and holds it in memory.
    Usage:
        r = RAGRetriever()
        results = r.retrieve("best time to visit Skardu", top_k=5)
    """

    _instance: Optional["RAGRetriever"] = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._built = False
            cls._instance = obj
        return cls._instance

    def __init__(self):
        if not self._built:
            self._chunks: List[Dict[str, Any]] = []
            self._vectors: Optional[np.ndarray] = None
            self._faiss_index = None
            self._build_index()
            self._built = True

    # ── Index Building ────────────────────────────────────────────────────────

    def _build_index(self):
        """Load from cache if data hasn't changed, else rebuild."""
        os.makedirs(CACHE_DIR, exist_ok=True)
        current_hash = _data_hash()

        if self._cache_valid(current_hash):
            print("[RAG] Loading index from cache...")
            self._load_from_cache()
        else:
            print("[RAG] Building RAG index (first run or data changed)...")
            self._rebuild(current_hash)

    def _cache_valid(self, current_hash: str) -> bool:
        try:
            if not os.path.exists(META_CACHE):
                return False
            with open(META_CACHE, "r") as f:
                meta = json.load(f)
            if meta.get("data_hash") != current_hash:
                return False
            if meta.get("semantic") != is_semantic():
                return False
            required = [CHUNKS_CACHE, VECTORS_CACHE]
            if _FAISS_AVAILABLE:
                required.append(FAISS_INDEX_CACHE)
            else:
                required.append(TFIDF_CACHE)
            return all(os.path.exists(p) for p in required)
        except Exception:
            return False

    def _rebuild(self, data_hash: str):
        # 1. Build chunks
        self._chunks = build_knowledge_base()
        texts = [c["text"] for c in self._chunks]

        # 2. TF-IDF needs fitting before embed_texts() if SBERT not available
        if not is_semantic():
            fit_tfidf(texts)

        # 3. Embed
        print(f"[RAG] Embedding {len(texts)} chunks...")
        self._vectors = embed_texts(texts)
        print(f"[RAG] Embedding done. Shape: {self._vectors.shape}")

        # 4. Build FAISS or fallback index
        if _FAISS_AVAILABLE:
            dim = self._vectors.shape[1]
            index = faiss.IndexFlatIP(dim)  # Inner product on normalized vecs == cosine
            index.add(self._vectors)
            self._faiss_index = index
            faiss.write_index(index, FAISS_INDEX_CACHE)
            print(f"[RAG] FAISS index built: {index.ntotal} vectors, dim={dim}")
        else:
            print("[RAG] FAISS not available — using sklearn cosine similarity at query time")

        # 5. Save cache
        with open(CHUNKS_CACHE, "wb") as f:
            pickle.dump(self._chunks, f)
        np.save(VECTORS_CACHE, self._vectors)

        if not is_semantic() and _tfidf_state():
            with open(TFIDF_CACHE, "wb") as f:
                pickle.dump(_tfidf_state(), f)

        with open(META_CACHE, "w") as f:
            json.dump({
                "data_hash": data_hash,
                "semantic": is_semantic(),
                "num_chunks": len(self._chunks),
                "faiss": _FAISS_AVAILABLE,
            }, f)

        print(f"[RAG] Index cached to {CACHE_DIR}")

    def _load_from_cache(self):
        with open(CHUNKS_CACHE, "rb") as f:
            self._chunks = pickle.load(f)
        self._vectors = np.load(VECTORS_CACHE)

        if _FAISS_AVAILABLE and os.path.exists(FAISS_INDEX_CACHE):
            import faiss
            self._faiss_index = faiss.read_index(FAISS_INDEX_CACHE)
            print(f"[RAG] FAISS index loaded: {self._faiss_index.ntotal} vectors")
        elif not is_semantic() and os.path.exists(TFIDF_CACHE):
            # Restore TF-IDF vectorizer into embedder module
            import rag.embedder as emb
            with open(TFIDF_CACHE, "rb") as f:
                state = pickle.load(f)
            emb._tfidf_vectorizer = state["vectorizer"]
            emb._tfidf_matrix = state["matrix"]
            emb._tfidf_corpus = state["corpus"]

        print(f"[RAG] Cache loaded: {len(self._chunks)} chunks")

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_section: Optional[str] = None,
        filter_city: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Args:
            query:          Natural language question or keyword phrase
            top_k:          Number of chunks to return
            filter_section: Optional metadata filter (e.g. 'weather', 'tips', 'history')
            filter_city:    Optional city name filter

        Returns:
            List of dicts: {"text", "metadata", "score"}
        """
        if not self._chunks:
            return []

        try:
            q_vec = embed_query(query)
        except Exception as e:
            print(f"[RAG] embed_query error: {e}")
            return []

        # FAISS retrieval
        if _FAISS_AVAILABLE and self._faiss_index is not None:
            # Retrieve more than top_k so we can post-filter
            fetch_k = min(top_k * 5, len(self._chunks))
            q_vec_2d = q_vec.reshape(1, -1).astype(np.float32)
            scores, indices = self._faiss_index.search(q_vec_2d, fetch_k)
            candidates = [
                {"chunk": self._chunks[idx], "score": float(scores[0][i])}
                for i, idx in enumerate(indices[0])
                if idx >= 0
            ]
        else:
            # sklearn cosine fallback
            from sklearn.metrics.pairwise import cosine_similarity
            sim = cosine_similarity(q_vec.reshape(1, -1), self._vectors)[0]
            ranked = np.argsort(sim)[::-1]
            candidates = [
                {"chunk": self._chunks[idx], "score": float(sim[idx])}
                for idx in ranked[: top_k * 5]
            ]

        # Apply optional filters
        if filter_section:
            candidates = [
                c for c in candidates
                if c["chunk"]["metadata"].get("section") == filter_section
            ]
        if filter_city:
            city_lower = filter_city.lower()
            candidates = [
                c for c in candidates
                if city_lower in c["chunk"]["metadata"].get("city", "").lower()
                or city_lower in c["chunk"]["text"].lower()
            ]

        # Deduplicate by chunk id and take top_k
        seen = set()
        results = []
        for c in candidates:
            chunk_id = c["chunk"]["id"]
            if chunk_id not in seen:
                seen.add(chunk_id)
                results.append({
                    "text": c["chunk"]["text"],
                    "metadata": c["chunk"]["metadata"],
                    "score": round(c["score"], 4),
                })
            if len(results) >= top_k:
                break

        return results

    def retrieve_formatted(self, query: str, top_k: int = 5) -> str:
        """
        Returns retrieved chunks as a formatted string ready to inject
        into an LLM system prompt.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""
        lines = ["=== Relevant Pakistan Travel Knowledge ==="]
        for i, r in enumerate(results, 1):
            meta = r["metadata"]
            source = f"{meta.get('city', '')}, {meta.get('province', '')} [{meta.get('section', '')}]"
            lines.append(f"\n[Context {i} — {source}]")
            lines.append(r["text"])
        lines.append("=== End of Retrieved Context ===")
        return "\n".join(lines)


def _tfidf_state():
    """Helper: return TF-IDF state dict for caching."""
    import rag.embedder as emb
    if emb._tfidf_vectorizer is None:
        return None
    return {
        "vectorizer": emb._tfidf_vectorizer,
        "matrix": emb._tfidf_matrix,
        "corpus": emb._tfidf_corpus,
    }


# Convenience: module-level singleton accessor
_retriever_instance: Optional[RAGRetriever] = None


def get_retriever() -> RAGRetriever:
    """Returns the module-level RAGRetriever singleton (builds index if needed)."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance


if __name__ == "__main__":
    r = RAGRetriever()
    test_queries = [
        "best time to visit Hunza",
        "travel tips for Swat Valley",
        "history of Mohenjo-daro",
        "budget hotels in Islamabad",
        "transport from Lahore to Skardu",
    ]
    for q in test_queries:
        print(f"\n--- Query: {q} ---")
        results = r.retrieve(q, top_k=2)
        for res in results:
            print(f"  Score: {res['score']:.3f} | {res['metadata']}")
            print(f"  Text: {res['text'][:180]}...")
