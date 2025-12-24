"""Reranker strategy.

Provides a placeholder interface for reranking; to be implemented when
model/provider choices are finalized.
"""

from typing import List, Dict


class Reranker:
    """Stub reranker."""

    async def rerank(self, candidates: List[Dict], query: str) -> List[Dict]:
        """Rerank candidate documents for a query."""
        raise NotImplementedError("Reranker not implemented")
