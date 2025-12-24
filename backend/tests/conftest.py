import os
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator

import pytest

# CRITICAL: Set env vars BEFORE any app imports (settings loads on first import)
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Now safe to import (settings will use env vars set above)
from fastapi.testclient import TestClient  # noqa: E402

from app.adapters.base import RAGConfigRepositoryInterface  # noqa: E402
from app.api import deps  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.rag_config import AdvancedRAGConfig  # noqa: E402
from app.services.rag_config_manager import RAGConfigManager  # noqa: E402


class FakeRAGConfigRepo(RAGConfigRepositoryInterface):
    def __init__(self):
        self.store: dict[str, AdvancedRAGConfig] = {}

    async def save(self, chatbot_id: str, config: AdvancedRAGConfig) -> bool:
        self.store[chatbot_id] = config
        return True

    async def get(self, chatbot_id: str) -> Optional[AdvancedRAGConfig]:
        return self.store.get(chatbot_id)

    async def delete(self, chatbot_id: str) -> bool:
        return self.store.pop(chatbot_id, None) is not None

    async def list_all(self):
        return [(cid, cfg) for cid, cfg in self.store.items()]


@asynccontextmanager
async def _noop_lifespan(_app) -> AsyncIterator[None]:
    # Skip DB connectivity checks during tests
    yield


@pytest.fixture(scope="session")
def app_with_overrides() -> "FastAPI":
    # Disable real lifespan (DB wait) for tests
    app.router.lifespan_context = _noop_lifespan  # type: ignore[attr-defined]

    # Override RAGConfigManager to use an in-memory fake repo
    fake_repo = FakeRAGConfigRepo()

    def override_manager() -> RAGConfigManager:
        return RAGConfigManager(repository=fake_repo)

    app.dependency_overrides[deps.get_rag_config_manager] = override_manager
    return app


@pytest.fixture()
def client(app_with_overrides) -> TestClient:
    with TestClient(app_with_overrides) as c:
        yield c
