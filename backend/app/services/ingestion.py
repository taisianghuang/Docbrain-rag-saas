# backend/app/services/ingestion.py
import logging
import os
import shutil
import tempfile
import uuid
import aiofiles
import anyio
from typing import List
from fastapi import UploadFile, HTTPException
from app.repositories.document import DocumentRepository
from llama_parse import LlamaParse
from llama_index.core import Document as LlamaDocument, StorageContext, VectorStoreIndex

from app.models import Document as DBDocument, Chatbot
from app.db.rag_factory import get_vector_store
from app.core.security import decrypt_value
from app.core.strategies import get_nodes_from_strategy

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo

    async def _write_file_async(self, tmp_path: str, file: UploadFile) -> None:
        """Write uploaded file content to temporary location asynchronously."""
        logger.debug("Writing file content to temporary location")
        async with anyio.open_file(tmp_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
        await file.seek(0)
        logger.debug("File writing completed")

    def _retrieve_tenant_keys(self, chatbot: Chatbot) -> tuple[str, str]:
        """Retrieve and validate required API keys from tenant."""
        logger.debug(f"Retrieving API keys for tenant_id: {chatbot.tenant_id}")

        tenant_llama_key = None
        tenant_openai_key = None

        if chatbot.tenant:
            if chatbot.tenant.encrypted_llama_cloud_key:
                tenant_llama_key = decrypt_value(
                    chatbot.tenant.encrypted_llama_cloud_key)
            if chatbot.tenant.encrypted_openai_key:
                tenant_openai_key = decrypt_value(
                    chatbot.tenant.encrypted_openai_key)

        if not tenant_llama_key:
            logger.error("Missing LlamaCloud key for tenant")
            raise ValueError(
                "Tenant LlamaCloud Key is missing. Please configure it in Tenant settings.")
        if not tenant_openai_key:
            logger.error("Missing OpenAI key for tenant")
            raise ValueError(
                "Tenant OpenAI Key is missing. Please configure it in Tenant settings.")

        logger.debug("API keys retrieved successfully")
        return tenant_llama_key, tenant_openai_key

    async def _parse_and_chunk_documents(
        self,
        tmp_path: str,
        parse_api_key: str,
        embedding_api_key: str,
        rag_config: dict,
    ) -> list:
        """Parse file and chunk documents using LlamaParse and strategy."""
        logger.info("Starting LlamaParse")
        parser = LlamaParse(
            api_key=parse_api_key,
            result_type="markdown",
            verbose=True,
            language="ch_tra"
        )
        llama_docs: List[LlamaDocument] = await parser.aload_data(tmp_path)

        if not llama_docs:
            logger.error("LlamaParse returned no documents")
            raise ValueError("LlamaParse returned no content.")
        logger.info(f"LlamaParse completed - documents: {len(llama_docs)}")

        # Chunking using strategy
        chunking_strategy = rag_config.get('chunking_strategy', 'standard')
        logger.info(f"Chunking documents - strategy: {chunking_strategy}")

        nodes = get_nodes_from_strategy(
            documents=llama_docs,
            rag_config=rag_config,
            openai_api_key=embedding_api_key
        )
        logger.info(f"Chunking completed - nodes created: {len(nodes)}")
        return nodes

    def _inject_node_metadata(self, nodes: list, chatbot: Chatbot, db_doc: DBDocument, filename: str) -> None:
        """Inject metadata into nodes and set exclusion keys."""
        logger.debug(f"Injecting metadata for {len(nodes)} nodes")
        for node in nodes:
            node.metadata["chatbot_id"] = str(chatbot.id)
            node.metadata["document_id"] = str(db_doc.id)
            node.metadata["filename"] = filename

            node.excluded_llm_metadata_keys = [
                "chatbot_id", "document_id", "window", "original_text"]
            node.excluded_embed_metadata_keys = [
                "chatbot_id", "document_id", "window", "original_text"]
        logger.debug("Metadata injection completed")

    async def _write_to_vector_store(self, nodes: list, rag_config: dict, db_doc: DBDocument) -> None:
        """Write nodes to vector store and update document status."""
        logger.info(f"Writing nodes to vector store - nodes: {len(nodes)}")
        vector_store = get_vector_store()
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store)

        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            show_progress=True
        )
        logger.info("Nodes successfully written to vector store")

        # Update document status
        await self.document_repo.update_status(
            document_id=str(db_doc.id),
            status="indexed",
            metadata_map={
                "parsed_chunks": len(nodes),
                "strategy": rag_config.get("chunking_strategy", "standard")
            }
        )

    async def ingest_file(self, chatbot: Chatbot, file: UploadFile):
        """Main ingestion workflow with reduced cognitive complexity."""
        logger.info(f"Starting ingest for chatbot_id: {chatbot.id}")
        db_doc = await self.document_repo.create(
            tenant_id=chatbot.tenant_id,
            chatbot_id=str(chatbot.id),
            filename=file.filename,
            file_url=f"local://{file.filename}",
            status="processing",
            metadata_map={}
        )
        logger.debug(f"Document record created - document_id: {db_doc.id}")

        tmp_path = None
        try:
            # Create temporary file path and write asynchronously
            suffix = os.path.splitext(file.filename)[1]
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(
                tmp_dir, f"doc_upload_{uuid.uuid4().hex}{suffix}")

            await self._write_file_async(tmp_path, file)

            # Retrieve API keys
            parse_api_key, embedding_api_key = await self._retrieve_tenant_keys(chatbot)

            # Parse and chunk documents
            rag_config = chatbot.rag_config or {}
            nodes = await self._parse_and_chunk_documents(
                tmp_path, parse_api_key, embedding_api_key, rag_config
            )

            # Process and store nodes
            self._inject_node_metadata(nodes, chatbot, db_doc, file.filename)
            await self._write_to_vector_store(nodes, rag_config, db_doc)

            logger.info(
                f"Ingest completed successfully - document_id: {db_doc.id}")
            return {
                "status": "success",
                "document_id": str(db_doc.id),
                "chunks": len(nodes)
            }

        except Exception:
            # Log error without user-controlled data
            logger.error("Ingestion error for document_id: %s",
                         str(db_doc.id), exc_info=True)

            # Update status and clean up
            try:
                await self.document_repo.update_status(
                    document_id=str(db_doc.id),
                    status="error",
                    error_message="Document processing failed. Please try again."
                )
            except Exception:
                logger.exception(
                    "Failed to update document status after error")

            raise HTTPException(
                status_code=500, detail="Document ingestion failed")

        finally:
            logger.debug("Cleaning up temporary files")
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
