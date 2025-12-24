# backend/app/db/rag_factory.py
"""
Vector store factory for RAG operations.

Creates PGVectorStore instances using database configuration and models.
"""
from sqlalchemy.engine import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from app.core.config import settings
from app.models import LlamaIndexStore


def get_vector_store() -> PGVectorStore:
    """
    Factory function: Create PGVectorStore instance.

    Uses LlamaIndexStore model's table name to ensure consistency
    between SQLAlchemy models and LlamaIndex vector store.

    Returns:
        Configured PGVectorStore instance
    """
    db_url = make_url(settings.DATABASE_URL)

    return PGVectorStore.from_params(
        database=db_url.database,
        host=db_url.host,
        password=db_url.password,
        port=db_url.port,
        user=db_url.username,
        table_name=LlamaIndexStore.__tablename__,
        embed_dim=1536,  # OpenAI text-embedding-3-small dimension
    )
