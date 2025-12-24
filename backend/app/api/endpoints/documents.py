# backend/app/api/endpoints/documents.py
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Any
from app.api import deps
from app.services.ingestion import IngestionService
from app.services.chatbot import ChatbotService
from app.schemas import IngestResponse
from app.repositories.document import DocumentRepository
from app.processing.producer import ProcessingProducer

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    chatbot_id: str = Form(...),  # 前端 Dashboard 傳過來的 ID
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(deps.get_ingestion_service),
    chatbot_service: ChatbotService = Depends(
        deps.get_chatbot_service),  # 注入 ChatbotService
    processing_producer: ProcessingProducer = Depends(
        deps.get_processing_producer),
) -> Any:
    """
    SaaS 核心功能：上傳文件並進行 RAG 索引。
    """
    logger.info("Document ingest request received")
    # 1. 驗證 Chatbot 是否存在 (且預先載入 Tenant 供 Key 使用)
    chatbot = await chatbot_service.get_chatbot_by_id(chatbot_id)

    if not chatbot:
        logger.warning("Document ingest failed - Chatbot not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    logger.debug("Document ingest - Chatbot verified")

    # 2. 先建立 ProcessingTask（隊列抽象，實際隊列在 Spec2 定義）
    task = await processing_producer.enqueue_document(
        chatbot_id=chatbot_id,
        document_id=None,
        payload={"filename": file.filename},
        priority=5,
    )

    # 3. 呼叫 Service 進行處理 (目前仍同步，後續可由 Consumer 觸發)
    try:
        result = await ingestion_service.ingest_file(chatbot, file)
        await processing_producer.task_repo.update_status(
            task_id=str(task.id), status="completed", document_id=result["document_id"]
        )
        logger.info(f"Document ingest successful - chunks: {result['chunks']}")
        return IngestResponse(**result)
    except Exception:
        await processing_producer.task_repo.update_status(
            task_id=str(task.id), status="failed", error_message="ingestion_failed"
        )
        logger.error("Document ingest error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document ingestion failed"
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
