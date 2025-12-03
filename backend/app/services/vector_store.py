import os
from typing import List
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from sqlalchemy.engine import make_url

from app.core.config import settings


class VectorStoreService:
    _instance = None
    _index = None

    @classmethod
    def get_instance(cls):
        """Singleton Pattern: 確保全域只有一個 Service 實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._initialize_index()

    def _initialize_index(self):
        """
        初始化 PGVectorStore 並建立/載入 Index。
        注意：這裡的 Table 是 LlamaIndex 專用的 'vector_store'，
        用來儲存切割後的 Chunks (Nodes)，跟我們的 models/db.py 的 Document (檔案層級) 是分開的。
        """
        # 1. 解析資料庫連線字串
        # LlamaIndex 的 PGVectorStore 通常需要同步的 psycopg2 driver 或者 asyncpg
        # 這裡我們使用 settings.DATABASE_URL
        # 如果遇到 asyncpg 問題，可能需要在此臨時轉為 psycopg2 字串，但新版 LlamaIndex 支援 async

        url = make_url(settings.DATABASE_URL)

        # 2. 初始化 PGVectorStore
        # 這會自動在 DB 建立一個名為 "pg_vector_store" (預設) 的 table
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="pg_vector_store_chunks",  # 區分：這是存 Chunks 的表
            embed_dim=1536,  # OpenAI text-embedding-3-small 維度
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
                "dist_type": "cosine",
            },
        )

        # 3. 建立 Storage Context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # 4. 初始化 Global Settings (確保使用 OpenAI)
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )

        # 5. 載入 Index (如果 DB 有資料會自動連結，沒有則為空)
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
        )

    @property
    def index(self):
        return self._index

    def get_query_engine(self, client_id: str, similarity_top_k: int = 5):
        """
        核心功能：取得帶有「多租戶過濾器」的查詢引擎
        """
        # 強制過濾：只檢索 metadata['client_id'] == client_id 的向量
        filters = MetadataFilters(
            filters=[
                ExactMatchFilter(key="client_id", value=client_id)
            ]
        )

        return self._index.as_query_engine(
            similarity_top_k=similarity_top_k,
            filters=filters,
            verbose=True
        )

# Helper function for Dependency Injection


def get_vector_service() -> VectorStoreService:
    return VectorStoreService.get_instance()
