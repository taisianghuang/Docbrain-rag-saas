"""
Configuration validator with unified ValidationResult schema.

This module provides validation logic for RAG configurations.
ValidationResult uses 'is_valid' to match the schema definition.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rag_config import AdvancedRAGConfig


class ValidationError(BaseModel):
    """Single validation error with field, message, and severity."""
    field: str
    message: str
    code: str = "validation_error"
    severity: str = Field(default="error", pattern="^(error|warning|info)$")


class ValidationResult(BaseModel):
    """
    Unified validation result schema.

    Uses 'is_valid' (not 'valid') to match app.schemas.rag_config.ValidationResult.
    """
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    estimated_cost: Optional[float] = None
    performance_impact: Optional[str] = None


class ConfigValidator:
    """
    Configuration validator for RAG settings.

    Implements validation rules:
    - Model compatibility (provider consistency)
    - API key presence for external providers
    - Resource constraints (chunk size vs max tokens)
    - Cost estimation
    """

    @staticmethod
    def validate_model_compatibility(config: AdvancedRAGConfig) -> List[ValidationError]:
        """Check if model selections are compatible."""
        errors: List[ValidationError] = []

        # Rule: local LLM should use local embeddings for consistency
        if config.llm.provider == "local" and config.embedding.provider != "local":
            errors.append(ValidationError(
                field="embedding.provider",
                message="Embedding provider should be 'local' when using local LLMs for consistency",
                code="provider_mismatch"
            ))

        return errors

    @staticmethod
    def validate_api_keys(config: AdvancedRAGConfig) -> List[ValidationError]:
        """Validate that external providers have API key references."""
        errors: List[ValidationError] = []

        # Check embedding provider API key
        if config.embedding.provider in ("openai", "cohere", "huggingface") and not config.embedding.api_key_ref:
            errors.append(ValidationError(
                field="embedding.api_key_ref",
                message=f"API key reference required for {config.embedding.provider} embedding provider",
                code="missing_api_key"
            ))

        # Check LLM provider API key
        if config.llm.provider in ("openai", "anthropic", "cohere") and not config.llm.api_key_ref:
            errors.append(ValidationError(
                field="llm.api_key_ref",
                message=f"API key reference required for {config.llm.provider} LLM provider",
                code="missing_api_key"
            ))

        return errors

    @staticmethod
    def validate_resource_constraints(config: AdvancedRAGConfig) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate resource constraints and return (errors, warnings)."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Error: chunk_size exceeds LLM context window
        if config.chunking.chunk_size > config.llm.max_tokens:
            errors.append(ValidationError(
                field="chunking.chunk_size",
                message=f"Chunk size ({config.chunking.chunk_size}) exceeds LLM max_tokens ({config.llm.max_tokens})",
                code="chunk_size_exceeds_limit"
            ))

        # Warning: chunk_overlap is very high
        if config.chunking.chunk_overlap > config.chunking.chunk_size * 0.5:
            warnings.append(ValidationError(
                field="chunking.chunk_overlap",
                message="Chunk overlap exceeds 50% of chunk size, may cause redundant storage",
                code="high_overlap",
                severity="warning"
            ))

        # Warning: reranking without sufficient initial candidates
        if config.retrieval.enable_reranking and config.retrieval.top_k_initial < config.retrieval.top_k_final * 2:
            warnings.append(ValidationError(
                field="retrieval.top_k_initial",
                message="top_k_initial should be at least 2x top_k_final for effective reranking",
                code="insufficient_rerank_candidates",
                severity="warning"
            ))

        return errors, warnings

    @staticmethod
    def estimate_costs(config: AdvancedRAGConfig) -> float:
        """
        Estimate monthly cost based on configuration.

        Simplified calculation - in production would use actual pricing tables.
        """
        # Base embedding cost per 1k tokens
        embedding_cost = {
            "openai": 0.0001,
            "cohere": 0.0001,
            "huggingface": 0.0,
            "local": 0.0
        }.get(config.embedding.provider, 0.0001)

        # LLM cost per 1k tokens
        llm_cost = {
            "openai": 0.03,
            "anthropic": 0.025,
            "cohere": 0.02,
            "local": 0.0
        }.get(config.llm.provider, 0.02)

        # Rough estimate: 1M tokens per month
        estimated_monthly_cost = (embedding_cost * 1000) + (llm_cost * 1000)

        return round(estimated_monthly_cost, 2)

    def validate_config(self, config: AdvancedRAGConfig) -> ValidationResult:
        """
        Perform full configuration validation.

        Returns ValidationResult with is_valid, errors, warnings, and cost estimate.
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Run all validation checks
        errors.extend(self.validate_model_compatibility(config))
        errors.extend(self.validate_api_keys(config))

        constraint_errors, constraint_warnings = self.validate_resource_constraints(
            config)
        errors.extend(constraint_errors)
        warnings.extend(constraint_warnings)

        # Calculate estimated cost
        estimated_cost = self.estimate_costs(config)

        # Determine performance impact
        performance_impact = None
        if config.retrieval.enable_reranking:
            performance_impact = "Reranking enabled - expect 100-300ms additional latency"

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            estimated_cost=estimated_cost,
            performance_impact=performance_impact
        )
