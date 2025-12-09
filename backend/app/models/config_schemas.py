# backend/app/models/config_schemas.py
"""
Standardized config schemas for Chatbot JSONB fields.
All field names use snake_case convention.
References the actual strategy enums defined in core modules.
"""
from typing import Literal
from pydantic import BaseModel, Field


class RagConfigSchema(BaseModel):
    """Standard schema for rag_config JSONB field - RAG retrieval strategies"""
    mode: Literal["vector", "hybrid", "router",
                  "sentence_window", "parent_child"] = "vector"
    chunking_strategy: Literal["standard",
                               "markdown", "semantic", "window"] = "standard"
    llm_model: Literal["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] = Field(
        default="gpt-4o-mini",
        description="LLM model name for chat generation"
    )
    top_k: int = Field(default=5, ge=1, le=20)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class WidgetConfigSchema(BaseModel):
    """Standard schema for widget_config JSONB field"""
    title: str = "Chat Assistant"
    primary_color: str = "#2563eb"
    welcome_message: str = "Hi! How can I help you today?"
