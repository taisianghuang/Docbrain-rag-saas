from typing import Optional

from app.schemas.rag_config import AdvancedRAGConfig
from app.core.config_validator import ConfigValidator, ValidationResult
from app.repositories.rag_config import InMemoryRAGConfigRepository


class RAGConfigManager:
    def __init__(self, repository: Optional[InMemoryRAGConfigRepository] = None) -> None:
        # For now use the in-memory repository; later inject DB-backed implementation
        self._repo = repository or InMemoryRAGConfigRepository()
        self._validator = ConfigValidator()

    async def validate_config(self, config: AdvancedRAGConfig) -> ValidationResult:
        return self._validator.validate_config(config)

    async def save_config(self, chatbot_id: str, config: AdvancedRAGConfig) -> bool:
        result = await self.validate_config(config)
        if not result.valid:
            return False
        await self._repo.save(chatbot_id, config)
        return True

    async def get_config(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        return await self._repo.get(chatbot_id)
