# backend/app/api/endpoints/documents.py
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Any
from app.api import deps
from app.services.ingestion import IngestionService
from app.services.chatbot import ChatbotService  # 改用 ChatbotService
from app.schemas import IngestResponse
from app.api import deps as deps_module
from app.repositories.document import DocumentRepository
from fastapi import Path

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    chatbot_id: str = Form(...),  # 前端 Dashboard 傳過來的 ID
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(deps.get_ingestion_service),
    chatbot_service: ChatbotService = Depends(
        deps.get_chatbot_service),  # 注入 ChatbotService
) -> Any:
    """
    SaaS 核心功能：上傳文件並進行 RAG 索引。
    """
    logger.info(
        f"Document ingest request - chatbot_id: {chatbot_id}, filename: {file.filename}, size: {file.size}")
    # 1. 驗證 Chatbot 是否存在 (且預先載入 Tenant 供 Key 使用)
    chatbot = await chatbot_service.get_chatbot_by_id(chatbot_id)

    if not chatbot:
        logger.warning(
            f"Document ingest failed - Chatbot not found: {chatbot_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    logger.debug(
        f"Document ingest - Chatbot verified: {chatbot_id}, tenant_id: {chatbot.tenant_id}")

    # 2. 呼叫 Service 進行處理 (IngestionService 已經寫好會處理 Key 和 Metadata)
    try:
        result = await ingestion_service.ingest_file(chatbot, file)
        logger.info(
            f"Document ingest successful - chatbot_id: {chatbot_id}, document_id: {result['document_id']}, chunks: {result['chunks']}")
        return IngestResponse(**result)
    except Exception as e:
        logger.error(
            f"Document ingest error - chatbot_id: {chatbot_id}, filename: {file.filename}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{chatbot_id}/documents")
async def list_documents_for_chatbot(
    chatbot_id: str,
    doc_repo: DocumentRepository = Depends(deps.get_document_repository),
):
    docs = await doc_repo.list_by_chatbot_id(chatbot_id)
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "created_at": d.created_at.isoformat() if getattr(d, "created_at", None) else None,
        }
        for d in docs
    ]


@router.delete("/document/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    doc_repo: DocumentRepository = Depends(deps.get_document_repository),
):
    await doc_repo.delete_by_id(document_id)
    return None
