"""
Base adapter interfaces for external systems.

These abstract classes define the contracts that adapters must implement,
allowing different implementations to be swapped without changing core logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.schemas.rag_config import AdvancedRAGConfig


class VectorStoreAdapter(ABC):
    """
    Interface for vector store operations.

    Implementations might use PGVector, Pinecone, Weaviate, or in-memory storage.
    """

    @abstractmethod
    async def write_nodes(
        self,
        nodes: List[Any],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Write document nodes/chunks to the vector store.

        Args:
            nodes: List of document nodes (chunks with embeddings)
            metadata: Additional metadata to attach (tenant_id, chatbot_id, etc.)
        """
        pass

    @abstractmethod
    async def query(
        self,
        query_text: str,
        filters: Dict[str, Any],
        top_k: int = 5,
        **kwargs
    ) -> List[Any]:
        """
        Query the vector store with filters.

        Args:
            query_text: The query string
            filters: Metadata filters (e.g., chatbot_id)
            top_k: Number of results to return
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching nodes/documents
        """
        pass

    @abstractmethod
    async def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """
        Delete documents matching filters.

        Args:
            filters: Metadata filters to match documents for deletion

        Returns:
            Number of documents deleted
        """
        pass


class QueueAdapter(ABC):
    """
    Interface for message queue operations.

    Implementations might use Kafka, Redis Streams, RabbitMQ, or in-memory queues.
    """

    @abstractmethod
    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        Enqueue a processing task.

        Args:
            task_type: Type of task (e.g., 'document_ingestion')
            payload: Task data
            priority: Task priority (1=highest, 10=lowest)

        Returns:
            Task ID for status tracking
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status.

        Args:
            task_id: The task identifier

        Returns:
            Dict with status, progress, errors, etc.
        """
        pass

    @abstractmethod
    async def ack(self, task_id: str) -> bool:
        """Acknowledge successful task completion."""
        pass

    @abstractmethod
    async def nack(self, task_id: str, reason: str) -> bool:
        """Reject task and move to retry/dead-letter queue."""
        pass


class RAGConfigRepositoryInterface(ABC):
    """
    Interface for RAG configuration persistence.

    This allows RAGConfigManager to work with different storage backends
    (DB, in-memory, cache, etc.) without changing business logic.
    """

    @abstractmethod
    async def save(self, chatbot_id: str, config: AdvancedRAGConfig) -> bool:
        """Save RAG configuration for a chatbot."""
        pass

    @abstractmethod
    async def get(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        """Retrieve RAG configuration for a chatbot."""
        pass

    @abstractmethod
    async def delete(self, chatbot_id: str) -> bool:
        """Delete RAG configuration for a chatbot."""
        pass

    @abstractmethod
    async def list_all(self) -> List[tuple[str, AdvancedRAGConfig]]:
        """List all configurations (chatbot_id, config pairs)."""
        pass
