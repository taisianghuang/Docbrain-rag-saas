import uuid
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProcessingTask(Base):
    """Tracks asynchronous document processing tasks."""

    __tablename__ = "processing_tasks"

    chatbot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatbots.id"), nullable=False, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(32), default="queued", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    # created_at / updated_at / id provided by Base
