"""
rag/rag_tool.py
===============
Exposes the RAG retriever as a callable tool function that can be:
  1. Registered in CLAUDE_TOOLS / GROQ_TOOLS in agent.py
  2. Called directly from the mock agent
  3. Called from the /rag/search FastAPI endpoint

The tool gracefully handles import errors so the app always starts,
even if the index hasn't been built yet or dependencies are missing.
"""

from typing import Optional


def search_knowledge_base(query: str, top_k: int = 5) -> dict:
    """
    Search the Pakistan travel knowledge base using semantic similarity.

    Retrieves relevant passages about attractions, weather, history,
    travel tips, food, transport, and accommodations for any city or
    region in Pakistan.

    Args:
        query:  Natural language question or topic to search for.
        top_k:  Number of results to return (default 5, max 10).

    Returns:
        dict with keys:
          - "results": list of {"text", "metadata", "score"} dicts
          - "count":   number of results returned
          - "engine":  "semantic" | "tfidf" | "error"
    """
    top_k = min(max(1, top_k), 10)

    try:
        from .retriever import get_retriever
        from .embedder import is_semantic

        retriever = get_retriever()
        results = retriever.retrieve(query, top_k=top_k)

        return {
            "results": results,
            "count": len(results),
            "engine": "semantic" if is_semantic() else "tfidf",
        }

    except Exception as e:
        print(f"[RAG Tool] Error during search: {e}")
        return {
            "results": [],
            "count": 0,
            "engine": "error",
            "error": str(e),
        }


def get_rag_context(query: str, top_k: int = 5) -> str:
    """
    Returns retrieved knowledge as a formatted string ready to prepend
    to an LLM system prompt or inject as a user message.

    Returns empty string if RAG fails (safe fallback).
    """
    try:
        from .retriever import get_retriever
        retriever = get_retriever()
        return retriever.retrieve_formatted(query, top_k=top_k)
    except Exception as e:
        print(f"[RAG] get_rag_context error: {e}")
        return ""
