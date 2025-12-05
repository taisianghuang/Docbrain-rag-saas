# backend/app/models/account.py
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Account(Base):
    """
    SaaS 使用者帳號 (User Account)
    歸屬於一個 Tenant，使用 Email/Password 登入
    """
    __tablename__ = "accounts"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)  # 系統管理員

    # 關聯 Tenant
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), nullable=False, index=True)
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="accounts")
