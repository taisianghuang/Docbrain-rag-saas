# backend/app/api/endpoints/conversation.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(deps.get_chat_service),
):
    """
    Widget 對話 API
    """
    try:
        result = await chat_service.chat(
            public_id=request.public_id,
            user_query=request.messages[-1].content,  # 取最後一則 User Message
            conversation_id=request.conversation_id,
            visitor_id=request.visitor_id
        )

        return ChatResponse(**result)

    except ValueError as e:
        # 通常是 Public ID 錯誤
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
