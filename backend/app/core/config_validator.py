from typing import List, Optional

from pydantic import BaseModel

from app.schemas.rag_config import AdvancedRAGConfig


class ValidationError(BaseModel):
    field: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: List[ValidationError] = []


class ConfigValidator:
    """Basic configuration validator.

    This validator implements lightweight checks required by the spec:
    - model compatibility (basic rules)
    - api key presence for providers that require keys
    - resource constraint sanity checks
    """

    @staticmethod
    def validate_model_compatibility(config: AdvancedRAGConfig) -> List[ValidationError]:
        errors: List[ValidationError] = []
        # Example rule: if provider is 'local' for LLM, embedding provider must be 'local'
        if config.llm.provider == "local" and config.embedding.provider != "local":
            errors.append(ValidationError(field="embedding.provider",
                          message="Embedding provider should be 'local' when using local LLMs"))
        return errors

    @staticmethod
    def validate_api_keys(config: AdvancedRAGConfig) -> List[ValidationError]:
        errors: List[ValidationError] = []
        # If provider is external and api_key_ref is missing -> error
        if config.embedding.provider in ("openai", "cohere") and not config.embedding.api_key_ref:
            errors.append(ValidationError(field="embedding.api_key_ref",
                          message="API key reference required for selected embedding provider"))
        if config.llm.provider in ("openai", "anthropic", "cohere") and not config.llm.api_key_ref:
            errors.append(ValidationError(field="llm.api_key_ref",
                          message="API key reference required for selected LLM provider"))
        return errors

    @staticmethod
    def estimate_costs(config: AdvancedRAGConfig) -> dict:
        # Lightweight estimator: cost per 1k tokens placeholder
        return {
            "embedding_cost_per_1k": 0.001 if config.embedding.provider == "openai" else 0.0005,
            "llm_cost_per_1k": 0.03 if config.llm.provider == "openai" else 0.01,
        }

    def validate_config(self, config: AdvancedRAGConfig) -> ValidationResult:
        errors = []
        errors.extend(self.validate_model_compatibility(config))
        errors.extend(self.validate_api_keys(config))

        # Resource constraint example: chunk_size should be less than LLM max tokens (approx)
        if config.chunking.chunk_size > config.llm.max_tokens:
            errors.append(ValidationError(field="chunking.chunk_size",
                          message="Chunk size exceeds LLM max_tokens"))

        return ValidationResult(valid=len(errors) == 0, errors=errors)
