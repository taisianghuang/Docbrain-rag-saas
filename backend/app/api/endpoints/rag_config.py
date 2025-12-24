# backend/app/api/endpoints/rag_config.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Optional

from app.api import deps
from app.schemas.rag_config import AdvancedRAGConfig, ValidationResult
from app.services.rag_config_manager import RAGConfigManager

router = APIRouter()


@router.post("/{chatbot_id}", status_code=status.HTTP_200_OK)
async def save_rag_config(
    chatbot_id: str,
    config: AdvancedRAGConfig,
    manager: RAGConfigManager = Depends(deps.get_rag_config_manager),
) -> Any:
    success, validation = await manager.save_config(chatbot_id, config)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid configuration",
                "validation": validation.model_dump() if isinstance(validation, ValidationResult) else None,
            },
        )
    return {"success": True}


@router.get("/{chatbot_id}", response_model=Optional[AdvancedRAGConfig])
async def get_rag_config(
    chatbot_id: str,
    manager: RAGConfigManager = Depends(deps.get_rag_config_manager),
) -> Optional[AdvancedRAGConfig]:
    return await manager.get_config(chatbot_id)
