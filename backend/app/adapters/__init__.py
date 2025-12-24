"""
Adapters package - External system integration interfaces.

This package contains adapter interfaces for external systems like
vector stores, message queues, and LLM providers. Using adapters allows us to:
- Swap implementations easily (e.g., PGVector for production)
- Test core logic without external dependencies
- Isolate infrastructure concerns from business logic
"""

from .base import VectorStoreAdapter, QueueAdapter, RAGConfigRepositoryInterface

__all__ = ["VectorStoreAdapter", "QueueAdapter",
           "RAGConfigRepositoryInterface"]
