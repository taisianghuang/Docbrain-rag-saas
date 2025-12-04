import uuid
from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.chatbot import Chatbot


class Document(Base):
    """
    業務文件紀錄 (File Record)
    """
    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), nullable=False)
    chatbot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatbots.id"), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_type: Mapped[str] = mapped_column(
        String(50), default="application/pdf")

    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_map: Mapped[dict] = mapped_column(JSONB, default=dict)

    # 關聯
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="documents")
    chatbot: Mapped["Chatbot"] = relationship(
        "Chatbot", back_populates="documents")


class LlamaIndexStore(Base):
    """
    LlamaIndex 預設的 PGVectorStore Schema
    """
    __tablename__ = "data_embeddings"

    # LlamaIndex 預設使用 varchar 作為 id
    id: Mapped[str] = mapped_column(String, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=True)
    node_id: Mapped[str] = mapped_column(String, nullable=True)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536))
