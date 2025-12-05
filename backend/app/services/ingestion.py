# backend/app/services/ingestion.py
import os
import shutil
import tempfile
import aiofiles
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from llama_parse import LlamaParse
from llama_index.core import Document as LlamaDocument, StorageContext, VectorStoreIndex

from app.models import Document as DBDocument, Chatbot
from app.core.rag_factory import get_vector_store
from app.core.security import decrypt_value
from app.core.chunking_strategies import get_nodes_from_strategy  # <--- 新增 import


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_file(self, chatbot: Chatbot, file: UploadFile):
        # 1. DB 寫入 (保持不變)
        db_doc = DBDocument(
            tenant_id=chatbot.tenant_id,
            chatbot_id=chatbot.id,
            filename=file.filename,
            file_url=f"local://{file.filename}",
            status="processing",
            metadata_map={}
        )
        self.db.add(db_doc)
        await self.db.commit()
        await self.db.refresh(db_doc)

        tmp_path = None
        try:
            # 2. 準備實體檔案 (Async I/O)
            # LlamaParse 需要讀取磁碟上的檔案路徑

            # 使用 mkstemp 安全地建立暫存檔路徑 (這是 OS 層級操作，極快，不會阻塞)
            suffix = os.path.splitext(file.filename)[1]
            fd, tmp_path = tempfile.mkstemp(suffix=suffix)

            # 立即關閉這個 file descriptor，因為我們要用 aiofiles 重新開啟它
            os.close(fd)

            # 使用 aiofiles 非同步寫入，避免阻塞 Event Loop
            async with aiofiles.open(tmp_path, 'wb') as out_file:
                # 分塊讀取與寫入 (1MB chunk)，避免大檔案吃光記憶體
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)

            # 重置檔案指標 (好習慣，以防後續還有其他邏輯要讀取 file)
            await file.seek(0)

            # 3. 準備 Key (需要 LlamaCloud Key 解析 PDF，也可能需要 OpenAI Key 做語意切分)
            tenant_llama_key = None
            tenant_openai_key = None  # <--- 新增：準備 OpenAI Key

            if chatbot.tenant:
                if chatbot.tenant.encrypted_llama_cloud_key:
                    tenant_llama_key = decrypt_value(
                        chatbot.tenant.encrypted_llama_cloud_key)
                if chatbot.tenant.encrypted_openai_key:
                    tenant_openai_key = decrypt_value(
                        chatbot.tenant.encrypted_openai_key)

            # Key Fallback 邏輯
            parse_api_key = tenant_llama_key
            embedding_api_key = tenant_openai_key

            if not parse_api_key:
                raise ValueError(
                    "Tenant LlamaCloud Key is missing. Please configure it in Tenant settings.")
            if not embedding_api_key:
                raise ValueError(
                    "Tenant OpenAI Key is missing. Please configure it in Tenant settings.")

            # 4. 準備檔案 (保持不變)
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 5. LlamaParse 解析 (PDF -> Markdown Docs)
            parser = LlamaParse(
                api_key=parse_api_key,
                result_type="markdown",
                verbose=True,
                language="ch_tra"
            )
            llama_docs: List[LlamaDocument] = await parser.aload_data(tmp_path)

            if not llama_docs:
                raise ValueError("LlamaParse returned no content.")

            # --- 6. 使用策略模組進行 Chunking ---
            rag_config = chatbot.rag_config or {}

            nodes = get_nodes_from_strategy(
                documents=llama_docs,
                rag_config=rag_config,
                openai_api_key=embedding_api_key  # 傳入 Key 以備語意切分使用
            )

            # 7. Metadata Injection (Node Level)
            # 這裡注入的是「業務邏輯」ID，所以還是在 Service 層做比較合適
            for node in nodes:
                node.metadata["chatbot_id"] = str(chatbot.id)
                node.metadata["document_id"] = str(db_doc.id)
                node.metadata["filename"] = file.filename

                # 排除不讓 LLM 看到這些內部 ID
                node.excluded_llm_metadata_keys = [
                    "chatbot_id", "document_id", "window", "original_text"]
                node.excluded_embed_metadata_keys = [
                    "chatbot_id", "document_id", "window", "original_text"]

            # 8. 寫入向量資料庫 (使用工廠)
            vector_store = get_vector_store()
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store)

            # 改用 Index(nodes) 直接建立索引
            VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                show_progress=True
            )

            # 9. 更新 DB 狀態
            db_doc.status = "indexed"
            db_doc.metadata_map = {
                "parsed_chunks": len(nodes),
                "strategy": rag_config.get("chunking_strategy", "standard")
            }
            await self.db.commit()

            return {
                "status": "success",
                "document_id": str(db_doc.id),
                "chunks": len(nodes)
            }

        except Exception as e:
            # Error Handling (保持不變)
            print(f"Ingestion Error: {e}")
            db_doc.status = "error"
            db_doc.error_message = str(e)
            await self.db.commit()
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
