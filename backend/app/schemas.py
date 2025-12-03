# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from enum import Enum
import uuid

# --- Chat Schemas ---


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    client_id: str = Field(..., description="租戶 ID (UUID)")
    messages: List[Message] = Field(..., description="對話歷史紀錄")
    conversation_id: Optional[str] = Field(None, description="若為延續對話請帶入此 ID")


class ChatResponse(BaseModel):
    response: str
    source_nodes: List[str] = []
    conversation_id: str

# --- Ingestion Schemas ---


class IngestResponse(BaseModel):
    status: str
    document_id: str
    chunks: int
