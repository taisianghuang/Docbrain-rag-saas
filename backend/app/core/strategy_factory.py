"""Factory stubs for RAG components.

These are intentionally lightweight and will be implemented once
model/provider wiring is defined (Spec2 for queue/model details).
"""

from app.schemas.rag_config import AdvancedRAGConfig
from app.core.strategies.retriever import HybridRetriever
from app.core.strategies.reranker import Reranker


def create_embedder(config: AdvancedRAGConfig):
    """Create embedder based on config. To be implemented."""
    raise NotImplementedError("Embedder factory not implemented")


def create_chunker(config: AdvancedRAGConfig):
    """Create chunker based on config.chunking_config (strategy module)."""
    # Placeholder: actual chunker selection is defined in strategies/chunking.py
    raise NotImplementedError("Chunker factory not implemented")


def create_retriever(config: AdvancedRAGConfig):
    """Create retriever (vector/bm25/hybrid) based on config.retrieval_config."""
    # Example wiring for hybrid retriever
    return HybridRetriever()


def create_reranker(config: AdvancedRAGConfig):
    """Create reranker if enabled in config.retrieval_config."""
    if getattr(config.retrieval_config, "enable_reranking", False):
        return Reranker()
    return None


def create_llm(config: AdvancedRAGConfig):
    """Create LLM client based on config.llm_config."""
    raise NotImplementedError("LLM factory not implemented")
