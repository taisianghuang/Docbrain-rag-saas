# backend/app/services/config_manager.py
"""
Advanced RAG Configuration Management Service
Handles validation, templating, and management of RAG configurations.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.rag_config import (
    AdvancedRAGConfig, ValidationResult, ValidationError, CostEstimate,
    ConfigTemplate, EmbeddingConfig, LLMConfig, ChunkingConfig, RetrievalConfig
)
from app.models import Chatbot
from app.core.security import decrypt_value

logger = logging.getLogger(__name__)


class RAGConfigManager:
    """Centralized management of RAG configurations with validation and templating"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = ConfigValidator()
        self.template_manager = ConfigTemplateManager()

    async def validate_config(self, config: AdvancedRAGConfig, tenant_id: str) -> ValidationResult:
        """Validate RAG configuration with comprehensive checks"""
        logger.info(f"Validating RAG configuration for tenant: {tenant_id}")

        try:
            # Basic schema validation is handled by Pydantic
            errors = []
            warnings = []

            # Model compatibility validation
            compatibility_errors = self.validator.validate_model_compatibility(
                config)
            errors.extend(compatibility_errors)

            # API key validation (if tenant has keys)
            api_key_errors = await self.validator.validate_api_keys(config, tenant_id, self.db)
            errors.extend(api_key_errors)

            # Resource constraint validation
            resource_errors = self.validator.validate_resource_constraints(
                config)
            errors.extend(resource_errors)

            # Performance impact assessment
            performance_warnings = self.validator.assess_performance_impact(
                config)
            warnings.extend(performance_warnings)

            # Cost estimation
            cost_estimate = self.validator.estimate_costs(config)

            is_valid = len([e for e in errors if e.severity == "error"]) == 0

            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                estimated_cost=cost_estimate.estimated_monthly_cost if cost_estimate else None,
                performance_impact=self._assess_performance_impact(config)
            )

            logger.info(
                f"Configuration validation completed - valid: {is_valid}, errors: {len(errors)}, warnings: {len(warnings)}")
            return result

        except Exception as e:
            logger.error(
                f"Error validating configuration: {str(e)}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="general",
                    message=f"Validation failed: {str(e)}",
                    code="VALIDATION_ERROR"
                )]
            )

    async def save_config(self, chatbot_id: str, config: AdvancedRAGConfig) -> bool:
        """Save validated RAG configuration to chatbot"""
        try:
            # Get chatbot
            chatbot = await self.db.get(Chatbot, chatbot_id)
            if not chatbot:
                logger.error(f"Chatbot not found: {chatbot_id}")
                return False

            # Validate configuration first
            validation_result = await self.validate_config(config, str(chatbot.tenant_id))
            if not validation_result.is_valid:
                logger.error(
                    f"Configuration validation failed for chatbot: {chatbot_id}")
                return False

            # Update timestamps
            config.updated_at = datetime.utcnow()
            if not config.created_at:
                config.created_at = datetime.utcnow()

            # Save to database
            chatbot.rag_config = config.model_dump()
            await self.db.commit()
            await self.db.refresh(chatbot)

            logger.info(
                f"RAG configuration saved successfully for chatbot: {chatbot_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error saving configuration for chatbot {chatbot_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False

    async def get_config(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        """Get RAG configuration for chatbot"""
        try:
            chatbot = await self.db.get(Chatbot, chatbot_id)
            if not chatbot:
                return None

            # Try to parse as advanced config first, fallback to legacy
            try:
                return AdvancedRAGConfig(**chatbot.rag_config)
            except Exception:
                # Migration from legacy config
                logger.info(
                    f"Migrating legacy config for chatbot: {chatbot_id}")
                return self._migrate_legacy_config(chatbot.rag_config)

        except Exception as e:
            logger.error(
                f"Error getting configuration for chatbot {chatbot_id}: {str(e)}", exc_info=True)
            return None

    async def apply_template(self, template_name: str) -> Optional[AdvancedRAGConfig]:
        """Apply configuration template"""
        template = self.template_manager.get_template(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None

        # Create a copy of the template config with current timestamp
        config = template.config.model_copy()
        config.created_at = datetime.utcnow()
        config.updated_at = datetime.utcnow()

        logger.info(f"Applied template: {template_name}")
        return config

    def _migrate_legacy_config(self, legacy_config: Dict[str, Any]) -> AdvancedRAGConfig:
        """Migrate legacy configuration to advanced format"""
        # Create default advanced config
        advanced_config = AdvancedRAGConfig()

        # Map legacy fields to new structure
        if "llm_model" in legacy_config:
            advanced_config.llm.model_name = legacy_config["llm_model"]

        if "temperature" in legacy_config:
            advanced_config.llm.temperature = legacy_config["temperature"]

        if "top_k" in legacy_config:
            advanced_config.retrieval.top_k_final = legacy_config["top_k"]

        if "chunking_strategy" in legacy_config:
            advanced_config.chunking.strategy = legacy_config["chunking_strategy"]

        if "mode" in legacy_config:
            mode_mapping = {
                "vector": "vector",
                "hybrid": "hybrid",
                "router": "vector",  # Fallback to vector
                "sentence_window": "vector",
                "parent_child": "vector"
            }
            advanced_config.retrieval.strategy = mode_mapping.get(
                legacy_config["mode"], "vector")

        advanced_config.version = "1.0"
        advanced_config.created_at = datetime.utcnow()
        advanced_config.updated_at = datetime.utcnow()

        return advanced_config

    def _assess_performance_impact(self, config: AdvancedRAGConfig) -> str:
        """Assess performance impact of configuration"""
        impact_factors = []

        if config.visual_processing and config.visual_processing.enable_colpali:
            impact_factors.append("high_visual_processing")

        if config.retrieval.enable_reranking:
            impact_factors.append("reranking_enabled")

        if config.chunking.strategy == "semantic":
            impact_factors.append("semantic_chunking")

        if config.performance_settings.parallel_workers > 8:
            impact_factors.append("high_parallelism")

        if len(impact_factors) >= 3:
            return "high"
        elif len(impact_factors) >= 1:
            return "medium"
        else:
            return "low"


class ConfigValidator:
    """Configuration validation logic"""

    def validate_model_compatibility(self, config: AdvancedRAGConfig) -> List[ValidationError]:
        """Validate model compatibility"""
        errors = []

        # Check embedding model compatibility
        if config.embedding.provider == "openai" and not config.embedding.model_name.startswith("text-embedding"):
            errors.append(ValidationError(
                field="embedding.model_name",
                message="OpenAI embedding models must start with 'text-embedding'",
                code="INVALID_EMBEDDING_MODEL"
            ))

        # Check LLM model compatibility
        if config.llm.provider == "openai" and config.llm.model_name not in [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"
        ]:
            errors.append(ValidationError(
                field="llm.model_name",
                message="Unsupported OpenAI model",
                code="INVALID_LLM_MODEL"
            ))

        # Check reranking model compatibility
        if config.retrieval.enable_reranking and not config.retrieval.reranker_model:
            errors.append(ValidationError(
                field="retrieval.reranker_model",
                message="Reranker model must be specified when reranking is enabled",
                code="MISSING_RERANKER_MODEL"
            ))

        return errors

    async def validate_api_keys(self, config: AdvancedRAGConfig, tenant_id: str, db: AsyncSession) -> List[ValidationError]:
        """Validate API keys for selected providers"""
        errors = []

        try:
            # Get tenant to check API keys
            from app.models import Tenant
            tenant = await db.get(Tenant, tenant_id)
            if not tenant:
                errors.append(ValidationError(
                    field="tenant",
                    message="Tenant not found",
                    code="TENANT_NOT_FOUND"
                ))
                return errors

            # Check OpenAI API key if using OpenAI models
            if (config.embedding.provider == "openai" or config.llm.provider == "openai"):
                if not tenant.encrypted_openai_key:
                    errors.append(ValidationError(
                        field="api_keys",
                        message="OpenAI API key is required for selected models",
                        code="MISSING_OPENAI_KEY"
                    ))

            # Add validation for other providers as needed

        except Exception as e:
            logger.error(f"Error validating API keys: {str(e)}", exc_info=True)
            errors.append(ValidationError(
                field="api_keys",
                message="Failed to validate API keys",
                code="API_KEY_VALIDATION_ERROR"
            ))

        return errors

    def validate_resource_constraints(self, config: AdvancedRAGConfig) -> List[ValidationError]:
        """Validate resource constraints"""
        errors = []

        # Check chunk size vs context window
        if config.chunking.chunk_size > config.retrieval.context_window:
            errors.append(ValidationError(
                field="chunking.chunk_size",
                message="Chunk size cannot exceed context window",
                code="CHUNK_SIZE_TOO_LARGE"
            ))

        # Check overlap vs chunk size
        if config.chunking.chunk_overlap >= config.chunking.chunk_size:
            errors.append(ValidationError(
                field="chunking.chunk_overlap",
                message="Chunk overlap must be less than chunk size",
                code="INVALID_CHUNK_OVERLAP"
            ))

        # Check retrieval top_k constraints
        if config.retrieval.top_k_initial < config.retrieval.top_k_final:
            errors.append(ValidationError(
                field="retrieval.top_k_initial",
                message="Initial top_k must be greater than or equal to final top_k",
                code="INVALID_TOP_K_RATIO"
            ))

        return errors

    def assess_performance_impact(self, config: AdvancedRAGConfig) -> List[ValidationError]:
        """Assess performance impact and generate warnings"""
        warnings = []

        # High memory usage warning
        if config.performance_settings.memory_limit_mb > 4096:
            warnings.append(ValidationError(
                field="performance_settings.memory_limit_mb",
                message="High memory limit may impact system performance",
                code="HIGH_MEMORY_USAGE",
                severity="warning"
            ))

        # Complex processing warning
        if config.chunking.strategy == "semantic" and config.retrieval.enable_reranking:
            warnings.append(ValidationError(
                field="general",
                message="Semantic chunking with reranking may significantly increase processing time",
                code="COMPLEX_PROCESSING",
                severity="warning"
            ))

        return warnings

    def estimate_costs(self, config: AdvancedRAGConfig) -> Optional[CostEstimate]:
        """Estimate costs for configuration"""
        try:
            # Simple cost estimation (would be more sophisticated in production)
            embedding_cost = 0.0001  # per 1k tokens
            llm_cost = 0.002  # per 1k tokens

            # Adjust based on model selection
            if config.llm.model_name == "gpt-4o":
                llm_cost = 0.03
            elif config.llm.model_name == "gpt-4-turbo":
                llm_cost = 0.01

            # Estimate monthly usage (simplified)
            estimated_monthly_tokens = 1000000  # 1M tokens per month
            monthly_cost = (embedding_cost + llm_cost) * \
                (estimated_monthly_tokens / 1000)

            return CostEstimate(
                embedding_cost_per_1k_tokens=embedding_cost,
                llm_cost_per_1k_tokens=llm_cost,
                estimated_monthly_cost=monthly_cost,
                cost_breakdown={
                    "embedding": embedding_cost * (estimated_monthly_tokens / 1000),
                    "llm": llm_cost * (estimated_monthly_tokens / 1000)
                }
            )
        except Exception as e:
            logger.error(f"Error estimating costs: {str(e)}", exc_info=True)
            return None


class ConfigTemplateManager:
    """Manages configuration templates for common use cases"""

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, ConfigTemplate]:
        """Initialize built-in configuration templates"""
        templates = {}

        # General purpose template
        general_config = AdvancedRAGConfig(
            embedding=EmbeddingConfig(
                model_name="text-embedding-3-small",
                provider="openai"
            ),
            llm=LLMConfig(
                model_name="gpt-4o-mini",
                provider="openai",
                temperature=0.1
            ),
            chunking=ChunkingConfig(
                strategy="standard",
                chunk_size=1024,
                chunk_overlap=200
            ),
            retrieval=RetrievalConfig(
                strategy="vector",
                top_k_final=5
            )
        )

        templates["general"] = ConfigTemplate(
            name="General Purpose",
            description="Balanced configuration for general document Q&A",
            config=general_config,
            use_case="general",
            recommended_for=["customer_support", "general_qa", "documentation"]
        )

        # Technical documentation template
        tech_config = AdvancedRAGConfig(
            embedding=EmbeddingConfig(
                model_name="text-embedding-3-large",
                provider="openai"
            ),
            llm=LLMConfig(
                model_name="gpt-4o",
                provider="openai",
                temperature=0.0
            ),
            chunking=ChunkingConfig(
                strategy="markdown",
                chunk_size=1536,
                chunk_overlap=300,
                respect_document_structure=True
            ),
            retrieval=RetrievalConfig(
                strategy="hybrid",
                top_k_initial=20,
                top_k_final=8,
                enable_reranking=True,
                reranker_model="BAAI/bge-reranker-base"
            )
        )

        templates["technical_docs"] = ConfigTemplate(
            name="Technical Documentation",
            description="Optimized for technical documentation with code and structured content",
            config=tech_config,
            use_case="technical_docs",
            recommended_for=["api_docs",
                             "code_documentation", "technical_manuals"]
        )

        # Add more templates as needed...

        return templates

    def get_template(self, name: str) -> Optional[ConfigTemplate]:
        """Get configuration template by name"""
        return self.templates.get(name)

    def list_templates(self) -> List[ConfigTemplate]:
        """List all available templates"""
        return list(self.templates.values())

    def get_templates_for_use_case(self, use_case: str) -> List[ConfigTemplate]:
        """Get templates suitable for specific use case"""
        return [t for t in self.templates.values() if use_case in t.recommended_for]
