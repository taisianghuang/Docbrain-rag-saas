import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Client(Base):
    __tablename__ = "client"

    # 使用 UUID 作為 Primary Key，與 Base 保持一致
    # Base 已經定義了 id, created_at, updated_at，這裡不需要重複定義 id 除非要覆蓋預設行為
    # 保留 Base 的 id 定義，這裡專注於業務欄位

    name = Column(String(length=255), nullable=False)

    # API Key 管理
    api_key = Column(String(length=1024), nullable=True, unique=True)

    # 網域白名單 (CORS Security) - 用於限制哪些網站可以嵌入 Widget
    allowed_domains = Column(JSON, default=list, nullable=True)

    # Widget 外觀設定 (JSONB)
    # 範例: {"title": "Help Bot", "primaryColor": "#2563eb", "welcomeMessage": "Hi!"}
    widget_config = Column(JSON, default=dict, nullable=True)

    # 是否啟用
    is_active = Column(Boolean, default=True)


__all__ = ["Client"]
