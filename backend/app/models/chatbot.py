import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.schemas.rag_config import WidgetConfigSchema

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.document import Document
    from app.models.conversation import Conversation
    from app.models.rag_config import RagConfig


class Chatbot(Base):
    """
    機器人實體 (The Bot Instance)
    """
    __tablename__ = "chatbots"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # --- Security ---
    public_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    allowed_domains: Mapped[List[str]] = mapped_column(
        ARRAY(String), default=list)

    # --- AI Configuration ---
    # Per-bot RAG configuration is now stored in the `rag_configs` table
    # (one-to-one / one-to-many as needed). The legacy JSONB field was removed.

    # --- UI Configuration ---
    widget_config: Mapped[dict] = mapped_column(
        JSONB, default=lambda: WidgetConfigSchema().model_dump())

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 關聯
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="chatbots")
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="chatbot", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="chatbot", cascade="all, delete-orphan"
    )
    # Named RAG configs that are explicitly scoped to this chatbot
    rag_configs: Mapped[List["RagConfig"]] = relationship(
        back_populates="chatbot", cascade="all, delete-orphan"
    )
