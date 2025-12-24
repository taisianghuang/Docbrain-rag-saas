"""
RAG Configuration Manager.

Manages RAG configuration lifecycle with validation and persistence.
Uses dependency injection for repository to allow different storage backends.
"""

from typing import Optional

from app.schemas.rag_config import AdvancedRAGConfig
from app.core.validation import ConfigValidator, ValidationResult
from app.adapters.base import RAGConfigRepositoryInterface


class RAGConfigManager:
    """
    Manages RAG configuration validation and persistence.

    This manager coordinates validation and storage operations,
    allowing different repository implementations to be injected.
    """

    def __init__(self, repository: RAGConfigRepositoryInterface) -> None:
        """
        Initialize RAG config manager.

        Args:
            repository: Config repository implementation (must be provided)
        """
        self._repo = repository
        self._validator = ConfigValidator()

    async def validate_config(self, config: AdvancedRAGConfig) -> ValidationResult:
        """
        Validate a RAG configuration.

        Args:
            config: The configuration to validate

        Returns:
            ValidationResult with is_valid, errors, warnings, and cost estimate
        """
        return self._validator.validate_config(config)

    async def save_config(self, chatbot_id: str, config: AdvancedRAGConfig) -> tuple[bool, Optional[ValidationResult]]:
        """
        Validate and save RAG configuration.

        Args:
            chatbot_id: The chatbot identifier
            config: The configuration to save

        Returns:
            Tuple of (success, validation_result)
        """
        result = await self.validate_config(config)
        if not result.is_valid:
            return False, result

        success = await self._repo.save(chatbot_id, config)
        return success, result

    async def get_config(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        """
        Retrieve RAG configuration for a chatbot.

        Args:
            chatbot_id: The chatbot identifier

        Returns:
            The configuration if found, None otherwise
        """
        return await self._repo.get(chatbot_id)

    async def delete_config(self, chatbot_id: str) -> bool:
        """
        Delete RAG configuration for a chatbot.

        Args:
            chatbot_id: The chatbot identifier

        Returns:
            True if deleted, False if not found
        """
        return await self._repo.delete(chatbot_id)
