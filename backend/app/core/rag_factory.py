# backend/app/core/rag_factory.py
from sqlalchemy.engine import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from app.core.config import settings
from app.models import LlamaIndexStore  # <--- 這裡就是 Source of Truth


def get_vector_store() -> PGVectorStore:
    """
    工廠函式：統一產出 PGVectorStore 實例
    解決了 Table Name 散落與 DB 連線參數重複的問題。
    """
    db_url = make_url(settings.DATABASE_URL)

    return PGVectorStore.from_params(
        database=db_url.database,
        host=db_url.host,
        password=db_url.password,
        port=db_url.port,
        user=db_url.username,
        # 關鍵：直接使用 Model 定義的表名，確保絕對連動
        table_name=LlamaIndexStore.__tablename__,
        embed_dim=1536,  # 如果未來換模型，也可考慮提取為參數
    )
