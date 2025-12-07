import uuid
from typing import List, Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from sqlalchemy import String, ForeignKey, Integer, Boolean, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.chatbot import Chatbot


class MessageRole(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    對話 Session
    """
    __tablename__ = "conversations"

    chatbot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatbots.id"), nullable=False, index=True)
    visitor_id: Mapped[str] = mapped_column(
        String(255), index=True, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 關聯
    chatbot: Mapped["Chatbot"] = relationship(
        "Chatbot", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    """
    單則訊息
    """
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True)

    # 關聯
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages")
