import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from .messages import Message


class ChatRequest(BaseModel):
    public_id: str = Field(..., description="Widget Public ID")
    messages: List[Message] = Field(..., description="對話歷史紀錄")
    visitor_id: Optional[str] = Field(None, description="訪客指紋 ID")
    conversation_id: Optional[str] = Field(None, description="若為延續對話請帶入此 ID")


class ChatResponse(BaseModel):
    response: str
    source_nodes: List[str] = []
    conversation_id: str


class IngestResponse(BaseModel):
    status: str
    document_id: str
    chunks: int
