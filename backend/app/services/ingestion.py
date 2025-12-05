import os
import shutil
import tempfile
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from llama_parse import LlamaParse
from llama_index.core import Document as LlamaDocument, StorageContext, VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore

from app.models import Document as DBDocument, Chatbot
from app.core.config import settings
from app.core.security import decrypt_value

from app.core.rag_factory import get_vector_store


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_file(self, chatbot: Chatbot, file: UploadFile) -> Dict[str, Any]:
        """
        SaaS 核心流程：上傳 -> LlamaParse -> 注入 Metadata -> PGVector

        Args:
            chatbot: 已預先載入 Tenant 資訊的 Chatbot 物件 (via ChatbotService)
            file: 上傳的檔案物件
        """

        # 1. 寫入業務資料庫 (DBDocument) - 狀態: processing
        # 這樣就算後續處理失敗，使用者也能看到 "Processing Failed" 的紀錄
        db_doc = DBDocument(
            tenant_id=chatbot.tenant_id,
            chatbot_id=chatbot.id,
            filename=file.filename,
            # MVP 暫時存本地，生產環境建議改傳 S3 並存 S3 URL
            file_url=f"local://{file.filename}",
            file_size=file.size,
            file_type=file.content_type or "application/octet-stream",
            status="processing",
            metadata_map={}
        )
        self.db.add(db_doc)
        await self.db.commit()
        await self.db.refresh(db_doc)

        tmp_path = None
        try:
            # 2. 準備檔案 (LlamaParse 需要實體路徑)
            # 將 UploadFile 寫入系統暫存區
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 3. 決定 API Key
            # 優先嘗試從 Tenant 取得加密 Key 並解密
            tenant_llama_key = None
            if chatbot.tenant and chatbot.tenant.encrypted_llama_cloud_key:
                tenant_llama_key = decrypt_value(
                    chatbot.tenant.encrypted_llama_cloud_key)

            if not tenant_llama_key:
                raise ValueError(
                    "No LlamaCloud API Key provided for tenant.")

            # 初始化 LlamaParse
            parser = LlamaParse(
                api_key=tenant_llama_key,
                result_type="markdown",  # Markdown 結構對 RAG 效果較好
                verbose=True,
                language="ch_tra"        # 繁體中文優化
            )

            # 執行解析 (這是最耗時的步驟)
            llama_docs: List[LlamaDocument] = await parser.aload_data(tmp_path)

            if not llama_docs:
                raise ValueError("LlamaParse returned no content.")

            # 4. Metadata Injection (SaaS 安全性關鍵!)
            # 我們要將 chatbot_id 與 document_id 打入每一個向量切片中
            # 這讓後續檢索時可以進行精確的 Metadata Filtering
            for doc in llama_docs:
                doc.metadata["chatbot_id"] = str(chatbot.id)
                doc.metadata["document_id"] = str(db_doc.id)
                doc.metadata["filename"] = file.filename
                doc.metadata["tenant_id"] = str(chatbot.tenant_id)

            # 5. 寫入向量資料庫 (PGVector)
            # 動態連接 PGVector，確保使用正確的 Table ("data_embeddings")
            # 取得 Vector Store
            vector_store = get_vector_store()
            # 注意: 這裡的 vector_store 已經在 rag_factory 處理好連線參數與 Table 名稱

            storage_context = StorageContext.from_defaults(
                vector_store=vector_store)

            # 建立 Index (這會觸發 Embedding API 並寫入 DB)
            VectorStoreIndex.from_documents(
                llama_docs,
                storage_context=storage_context,
                show_progress=True
            )

            # 6. 更新 DB 狀態為成功
            db_doc.status = "indexed"
            # 順便存解析後的結果摘要 (例如：解析出了幾頁、幾個區塊)
            db_doc.metadata_map = {"parsed_chunks": len(llama_docs)}
            await self.db.commit()

            return {
                "status": "success",
                "document_id": str(db_doc.id),
                "chunks": len(llama_docs)
            }

        except Exception as e:
            # 錯誤處理：更新 DB 狀態為 Error，並記錄錯誤訊息
            print(f"Ingestion Error: {e}")
            db_doc.status = "error"
            db_doc.error_message = str(e)
            await self.db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion failed: {str(e)}"
            )

        finally:
            # 清理暫存檔
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
