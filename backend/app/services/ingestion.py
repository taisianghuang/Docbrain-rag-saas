# backend/app/services/ingestion.py
import logging
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

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_file(self, chatbot: Chatbot, file: UploadFile):
        # 1. DB 寫入 (保持不變)
        logger.info(
            f"Starting ingest for filename: {file.filename}, chatbot_id: {chatbot.id}")
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
        logger.debug(f"Document record created - document_id: {db_doc.id}")

        tmp_path = None
        try:
            # 2. 準備實體檔案 (Async I/O)
            # LlamaParse 需要讀取磁碟上的檔案路徑
            logger.debug(f"Preparing temporary file for: {file.filename}")

            # 使用 mkstemp 安全地建立暫存檔路徑 (這是 OS 層級操作，極快，不會阻塞)
            suffix = os.path.splitext(file.filename)[1]
            fd, tmp_path = tempfile.mkstemp(suffix=suffix)

            # 立即關閉這個 file descriptor，因為我們要用 aiofiles 重新開啟它
            os.close(fd)

            # 使用 aiofiles 非同步寫入，避免阻塞 Event Loop
            logger.debug(f"Writing file content to temporary location")
            async with aiofiles.open(tmp_path, 'wb') as out_file:
                # 分塊讀取與寫入 (1MB chunk)，避免大檔案吃光記憶體
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)

            # 重置檔案指標 (好習慣，以防後續還有其他邏輯要讀取 file)
            await file.seek(0)
            logger.debug(f"File writing completed - tmp_path: {tmp_path}")

            # 3. 準備 Key (需要 LlamaCloud Key 解析 PDF，也可能需要 OpenAI Key 做語意切分)
            logger.debug(
                f"Retrieving API keys for tenant_id: {chatbot.tenant_id}")
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
                logger.error(
                    f"Missing LlamaCloud key for tenant_id: {chatbot.tenant_id}")
                raise ValueError(
                    "Tenant LlamaCloud Key is missing. Please configure it in Tenant settings.")
            if not embedding_api_key:
                logger.error(
                    f"Missing OpenAI key for tenant_id: {chatbot.tenant_id}")
                raise ValueError(
                    "Tenant OpenAI Key is missing. Please configure it in Tenant settings.")
            logger.debug(f"API keys retrieved successfully")

            # 4. 準備檔案 (保持不變)
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 5. LlamaParse 解析 (PDF -> Markdown Docs)
            logger.info(f"Starting LlamaParse for file: {file.filename}")
            parser = LlamaParse(
                api_key=parse_api_key,
                result_type="markdown",
                verbose=True,
                language="ch_tra"
            )
            llama_docs: List[LlamaDocument] = await parser.aload_data(tmp_path)

            if not llama_docs:
                logger.error(
                    f"LlamaParse returned no documents for file: {file.filename}")
                raise ValueError("LlamaParse returned no content.")
            logger.info(f"LlamaParse completed - documents: {len(llama_docs)}")

            # --- 6. 使用策略模組進行 Chunking ---
            rag_config = chatbot.rag_config or {}
            logger.info(
                f"Chunking documents - strategy: {rag_config.get('chunking_strategy', 'standard')}, documents: {len(llama_docs)}")

            nodes = get_nodes_from_strategy(
                documents=llama_docs,
                rag_config=rag_config,
                openai_api_key=embedding_api_key  # 傳入 Key 以備語意切分使用
            )
            logger.info(f"Chunking completed - nodes created: {len(nodes)}")

            # 7. Metadata Injection (Node Level)
            # 這裡注入的是「業務邏輯」ID，所以還是在 Service 層做比較合適
            logger.debug(f"Injecting metadata for {len(nodes)} nodes")
            for node in nodes:
                node.metadata["chatbot_id"] = str(chatbot.id)
                node.metadata["document_id"] = str(db_doc.id)
                node.metadata["filename"] = file.filename

                # 排除不讓 LLM 看到這些內部 ID
                node.excluded_llm_metadata_keys = [
                    "chatbot_id", "document_id", "window", "original_text"]
                node.excluded_embed_metadata_keys = [
                    "chatbot_id", "document_id", "window", "original_text"]
            logger.debug(f"Metadata injection completed")

            # 8. 寫入向量資料庫 (使用工廠)
            logger.info(f"Writing nodes to vector store - nodes: {len(nodes)}")
            vector_store = get_vector_store()
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store)

            # 改用 Index(nodes) 直接建立索引
            VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                show_progress=True
            )
            logger.info(f"Nodes successfully written to vector store")

            # 9. 更新 DB 狀態
            db_doc.status = "indexed"
            db_doc.metadata_map = {
                "parsed_chunks": len(nodes),
                "strategy": rag_config.get("chunking_strategy", "standard")
            }
            await self.db.commit()
            logger.info(
                f"Ingest completed successfully - document_id: {db_doc.id}, chunks: {len(nodes)}")

            return {
                "status": "success",
                "document_id": str(db_doc.id),
                "chunks": len(nodes)
            }

        except Exception as e:
            # Error Handling (保持不變)
            logger.error(
                f"Ingestion error for document_id: {db_doc.id}, filename: {file.filename}, error: {str(e)}", exc_info=True)
            db_doc.status = "error"
            db_doc.error_message = str(e)
            await self.db.commit()
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            logger.debug(f"Cleaning up temporary files")
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
