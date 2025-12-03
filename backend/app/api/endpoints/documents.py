# backend/app/api/endpoints/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Any
from app.api import deps
from app.services.ingestion import IngestionService
from app.services.client import ClientService
from app.schemas import IngestResponse

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    client_id: str = Form(...),
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(deps.get_ingestion_service),
    client_service: ClientService = Depends(deps.get_client_service),
) -> Any:
    """
    SaaS 核心功能：上傳文件並進行 RAG 索引。
    必須提供 client_id 以確保資料隔離。
    """
    # 1. 驗證租戶是否存在
    client = await client_service.get_client_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # 2. 呼叫 Service 進行處理 (LlamaParse + PGVector)
    try:
        result = await ingestion_service.ingest_file(client_id, file)
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
