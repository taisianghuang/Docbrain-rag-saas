from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    model_name: str = Field(..., description="Embedding model identifier")
    provider: Literal["openai", "cohere", "huggingface", "local"] = "openai"
    model_params: Dict[str, Any] = Field(default_factory=dict)
    api_key_ref: Optional[str] = None
    batch_size: int = Field(default=100, ge=1, le=1000)


class ChunkingConfig(BaseModel):
    strategy: Literal["standard", "semantic", "markdown",
                      "window", "hierarchical"] = "standard"
    chunk_size: int = Field(default=1024, ge=100, le=8192)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    semantic_threshold: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)
    window_size: Optional[int] = Field(default=3, ge=1, le=10)
    respect_document_structure: bool = True


class RetrievalConfig(BaseModel):
    strategy: Literal["vector", "bm25", "hybrid", "contextual"] = "vector"
    top_k_initial: int = Field(default=50, ge=1, le=200)
    top_k_final: int = Field(default=5, ge=1, le=50)
    hybrid_weights: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {"semantic": 0.7, "bm25": 0.3})
    enable_reranking: bool = False
    reranker_model: Optional[str] = None
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class LLMConfig(BaseModel):
    model_name: str = Field(..., description="LLM model identifier")
    provider: Literal["openai", "anthropic", "cohere", "local"] = "openai"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=8192)
    system_prompt: Optional[str] = None
    api_key_ref: Optional[str] = None


class VisualProcessingConfig(BaseModel):
    enable_ocr: bool = True
    enable_colpali: bool = False
    enable_vlm_summarization: bool = False
    ocr_provider: Literal["tesseract", "azure", "google"] = "tesseract"
    vlm_model: Optional[str] = None


class PerformanceConfig(BaseModel):
    cache_embeddings: bool = True
    batch_processing: bool = True
    parallel_workers: int = Field(default=4, ge=1, le=16)
    memory_limit_mb: int = Field(default=2048, ge=512, le=8192)


class AdvancedRAGConfig(BaseModel):
    embedding: EmbeddingConfig
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    llm: LLMConfig
    visual_processing: Optional[VisualProcessingConfig] = None
    performance_settings: PerformanceConfig = Field(
        default_factory=PerformanceConfig)


class ProcessingTaskSchema(BaseModel):
    task_id: str
    chatbot_id: str
    document_id: str
    priority: int = Field(default=5, ge=1, le=10)
    retry_count: int = 0
    max_retries: int = 3


# --- Legacy / additional schemas migrated from models/config_schemas.py ---
class RagConfigSchema(BaseModel):
    """Legacy schema for rag_config JSONB field - maintained for backward compatibility"""
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


class ConfigTemplate(BaseModel):
    """Configuration template for common use cases"""
    name: str
    description: str
    config: AdvancedRAGConfig
    use_case: Literal["general", "technical_docs",
                      "legal", "medical", "customer_support", "research"]
    recommended_for: list[str] = Field(default_factory=list)


class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    code: str
    severity: Literal["error", "warning", "info"] = "error"


class ValidationResult(BaseModel):
    """Configuration validation result"""
    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    estimated_cost: Optional[float] = None
    performance_impact: Optional[str] = None


class CostEstimate(BaseModel):
    """Cost estimation for configuration"""
    embedding_cost_per_1k_tokens: float
    llm_cost_per_1k_tokens: float
    estimated_monthly_cost: float
    cost_breakdown: Dict[str, float]
