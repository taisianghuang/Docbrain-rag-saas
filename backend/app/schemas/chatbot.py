import uuid
from typing import Optional
from pydantic import BaseModel, Field


class ChatbotCreate(BaseModel):
    tenant_id: Optional[uuid.UUID] = None
    name: str = Field(..., description="機器人名稱")
    rag_config: Optional[dict] = None
    widget_config: Optional[dict] = None


class ChatbotRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    public_id: str
    rag_config: dict
    widget_config: dict
    is_active: bool


class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    rag_config: Optional[dict] = None
    widget_config: Optional[dict] = None
    is_active: Optional[bool] = None


ChatbotResponse = ChatbotRead
