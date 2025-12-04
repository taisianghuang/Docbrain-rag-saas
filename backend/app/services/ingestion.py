# backend/app/services/ingestion.py
import os
import shutil
import tempfile
from typing import List
from fastapi import UploadFile, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from llama_parse import LlamaParse
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.models.db import Document as DBDocument
from app.services.vector_store import VectorStoreService, get_vector_service
from app.core.config import settings


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 取得全域 Vector Service
        self.vector_service = get_vector_service()

    async def ingest_file(self, client_id: str, file: UploadFile):
        """
        核心流程：
        1. DB: 建立 Document 紀錄 (Status: processing)
        2. LlamaParse: 解析檔案 -> Text
        3. Logic: 注入 Metadata (client_id, db_document_id)
        4. VectorStore: 寫入向量
        5. DB: 更新 Status (indexed / error)
        """

        # --- Step 1: 寫入業務資料庫 (PostgreSQL) ---
        # 這樣就算後續處理失敗，使用者也能看到 "Processing Failed" 的紀錄
        db_doc = DBDocument(
            client_id=client_id,
            name=file.filename,
            url=f"local://{file.filename}",  # MVP 暫時存本地，未來可改 S3 URL
            status="processing",
            metadata_map={}
        )
        self.db.add(db_doc)
        await self.db.commit()
        await self.db.refresh(db_doc)

        tmp_path = None
        try:
            # --- Step 2: 準備檔案與解析 (LlamaParse) ---
            # 將 UploadFile 寫入暫存檔，因為 LlamaParse 需要實體路徑
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 初始化 LlamaParse (需設定 LLAMA_CLOUD_API_KEY)
            parser = LlamaParse(
                api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
                result_type="markdown",  # Markdown 對 RAG 效果較好
                verbose=True,
                language="ch_tra"  # 繁體中文優化
            )

            # 執行解析 (這是最耗時的步驟)
            llama_docs: List[LlamaDocument] = await parser.aload_data(tmp_path)

            if not llama_docs:
                raise ValueError("LlamaParse returned no content.")

            # --- Step 3: Metadata Injection ---
            # 我們要將 PostgreSQL 的 document ID 與 client_id 打入每一個向量切片中
            for doc in llama_docs:
                doc.metadata["client_id"] = client_id
                doc.metadata["document_id"] = str(db_doc.id)  # 關聯回 DB 表
                doc.metadata["filename"] = file.filename

            # --- Step 4: 寫入向量資料庫 (PGVector) ---
            # 使用我們在 Step 3 建立的 index 來插入節點
            # 這裡會自動切塊 (Chunking) 並呼叫 OpenAI Embedding API
            self.vector_service.index.insert_documents(llama_docs)

            # --- Step 5: 更新 DB 狀態為成功 ---
            db_doc.status = "indexed"
            # 順便存解析後的結果摘要
            db_doc.metadata_map = {"parsed_chunks": len(llama_docs)}
            await self.db.commit()

            return {
                "status": "success",
                "document_id": str(db_doc.id),
                "chunks": len(llama_docs)
            }

        except Exception as e:
            # 錯誤處理：更新 DB 狀態為 Error
            print(f"Ingestion Error: {e}")
            db_doc.status = "error"
            # db_doc.error_message = str(e) # 如果 Model 有開這個欄位
            await self.db.commit()
            raise HTTPException(
                status_code=500, detail=f"Ingestion failed: {str(e)}")

        finally:
            # 清理暫存檔
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
