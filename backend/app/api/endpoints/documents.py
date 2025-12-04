# backend/app/api/endpoints/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Any
from app.api import deps
from app.services.ingestion import IngestionService
from app.services.chatbot import ChatbotService  # 改用 ChatbotService
from app.schemas import IngestResponse

router = APIRouter()


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
    # 1. 驗證 Chatbot 是否存在 (且預先載入 Tenant 供 Key 使用)
    chatbot = await chatbot_service.get_chatbot_by_id(chatbot_id)

    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )

    # 2. 呼叫 Service 進行處理 (IngestionService 已經寫好會處理 Key 和 Metadata)
    try:
        result = await ingestion_service.ingest_file(chatbot, file)
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
