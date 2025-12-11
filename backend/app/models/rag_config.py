import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.schemas.rag_config import AdvancedRAGConfig

if TYPE_CHECKING:
    from app.models.chatbot import Chatbot


class RagConfig(Base):
    """Named RAG configuration stored as JSONB for reuse across chatbots.

    This provides a first-class DB-backed store for advanced RAG configs.
    """
    __tablename__ = "rag_configs"

    # Each RagConfig belongs to a single Chatbot (chatbot-scoped).
    # Enforce uniqueness to make it a one-to-one relationship if desired.
    chatbot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatbots.id"), nullable=False, index=True, unique=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)

    config: Mapped[dict] = mapped_column(
        JSONB, default=lambda: AdvancedRAGConfig().model_dump()
    )

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship (SQLAlchemy 2.0 typed style)
    chatbot: Mapped["Chatbot"] = relationship(back_populates="rag_configs")
