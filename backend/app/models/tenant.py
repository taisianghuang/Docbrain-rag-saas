from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CASCADE_ALL_DELETE

# 使用 TYPE_CHECKING 避免循環引用
if TYPE_CHECKING:
    from app.models.chatbot import Chatbot
    from app.models.document import Document
    from app.models.account import Account


class Tenant(Base):
    """
    SaaS 租戶層級 (Company/Organization)
    """
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # --- AI Configuration ---
    # Fernet-encrypted API keys are base64 strings; reserve ample space
    encrypted_openai_key: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True)
    encrypted_llama_cloud_key: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True)

    # 關聯：使用字串 "Chatbot" 而非類別物件，SQLAlchemy 會自動延遲解析
    chatbots: Mapped[List["Chatbot"]] = relationship(
        "Chatbot", back_populates="tenant", cascade=CASCADE_ALL_DELETE
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="tenant", cascade=CASCADE_ALL_DELETE
    )

    # 關聯：使用字串 "Account"
    accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="tenant", cascade=CASCADE_ALL_DELETE
    )
