"""
RAG (Retrieval-Augmented Generation) Module
============================================
Provides semantic knowledge base retrieval over Pakistan travel data.

Usage:
    from rag.retriever import RAGRetriever
    retriever = RAGRetriever()
    results = retriever.retrieve("best time to visit Hunza", top_k=5)
"""
from .retriever import RAGRetriever
from .rag_tool import search_knowledge_base

__all__ = ["RAGRetriever", "search_knowledge_base"]
