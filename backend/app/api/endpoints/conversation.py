# backend/app/api/endpoints/conversation.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(deps.get_chat_service),
):
    """
    Widget 對話 API
    """
    logger.info("Chat request received")
    try:
        result = await chat_service.chat(
            public_id=request.public_id,
            user_query=request.messages[-1].content,  # 取最後一則 User Message
            conversation_id=request.conversation_id,
            visitor_id=request.visitor_id
        )
        logger.info(
            f"Chat successful - sources: {len(result['source_nodes'])}")

        return ChatResponse(**result)

    except ValueError as e:
        logger.warning("Chat validation error")
        # 通常是 Public ID 錯誤
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.error("Chat error", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
