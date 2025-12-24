"""
Database-backed RAG configuration repository.

Implements RAGConfigRepositoryInterface using SQLAlchemy and the RagConfig model.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.adapters.base import RAGConfigRepositoryInterface
from app.models.rag_config import RagConfig
from app.schemas.rag_config import AdvancedRAGConfig


class RAGConfigRepository(RAGConfigRepositoryInterface):
    """
    Database-backed repository for RAG configurations.

    Uses RagConfig model to persist configurations in PostgreSQL.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def save(self, chatbot_id: str, config: AdvancedRAGConfig) -> bool:
        """
        Save or update RAG configuration for a chatbot.

        Args:
            chatbot_id: The chatbot identifier
            config: The RAG configuration to save

        Returns:
            True if successful
        """
        try:
            # Check if config already exists for this chatbot
            stmt = select(RagConfig).where(RagConfig.chatbot_id == chatbot_id)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing config
                existing.config = config.model_dump()
                existing.name = f"Config for {chatbot_id}"
            else:
                # Create new config
                new_config = RagConfig(
                    chatbot_id=chatbot_id,
                    name=f"Config for {chatbot_id}",
                    description="Auto-generated configuration",
                    config=config.model_dump(),
                    is_public=False
                )
                self.db.add(new_config)

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            return False

    async def get(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        """
        Retrieve RAG configuration for a chatbot.

        Args:
            chatbot_id: The chatbot identifier

        Returns:
            The configuration if found, None otherwise
        """
        try:
            stmt = select(RagConfig).where(RagConfig.chatbot_id == chatbot_id)
            result = await self.db.execute(stmt)
            config_model = result.scalar_one_or_none()

            if config_model and config_model.config:
                return AdvancedRAGConfig(**config_model.config)

            return None

        except Exception:
            return None

    async def delete(self, chatbot_id: str) -> bool:
        """
        Delete RAG configuration for a chatbot.

        Args:
            chatbot_id: The chatbot identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(RagConfig).where(RagConfig.chatbot_id == chatbot_id)
            result = await self.db.execute(stmt)
            config_model = result.scalar_one_or_none()

            if config_model:
                await self.db.delete(config_model)
                await self.db.commit()
                return True

            return False

        except Exception:
            await self.db.rollback()
            return False

    async def list_all(self) -> List[tuple[str, AdvancedRAGConfig]]:
        """
        List all RAG configurations.

        Returns:
            List of (chatbot_id, config) tuples
        """
        try:
            stmt = select(RagConfig)
            result = await self.db.execute(stmt)
            configs = result.scalars().all()

            return [
                (str(cfg.chatbot_id), AdvancedRAGConfig(**cfg.config))
                for cfg in configs
                if cfg.config
            ]

        except Exception:
            return []
