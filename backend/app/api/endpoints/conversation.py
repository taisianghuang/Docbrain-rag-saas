# backend/app/api/endpoints/conversation.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas import ChatRequest, ChatResponse
from app.services.vector_store import get_vector_service, VectorStoreService
from app.services.client import ClientService
from app.models.db import Conversation, Message, MessageRoleEnum
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(deps.get_db),
    vector_service: VectorStoreService = Depends(get_vector_service),
    client_service: ClientService = Depends(deps.get_client_service),
):
    """
    SaaS 核心功能：RAG 對話。
    強制使用 client_id 進行 Metadata Filtering。
    """
    # 1. 驗證租戶
    client = await client_service.get_client_by_id(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # 2. 處理 Conversation ID (若無則新建)
    conversation_id = request.conversation_id
    if not conversation_id:
        new_conv = Conversation(client_id=uuid.UUID(request.client_id))
        db.add(new_conv)
        await db.commit()
        await db.refresh(new_conv)
        conversation_id = str(new_conv.id)

    # 3. 取得 User 最後一句話
    user_query = request.messages[-1].content

    # 4. 儲存 User Message 到 DB
    user_msg_record = Message(
        conversation_id=uuid.UUID(conversation_id),
        content=user_query,
        role=MessageRoleEnum.user
    )
    db.add(user_msg_record)
    await db.commit()

    try:
        # 5. 核心 RAG 檢索 (帶有多租戶過濾)
        # 這裡會強制只搜尋該 client_id 的向量
        query_engine = vector_service.get_query_engine(
            client_id=request.client_id,
            similarity_top_k=5
        )

        # 執行查詢
        response = await query_engine.aquery(user_query)
        response_text = str(response)

        # 6. 儲存 Assistant Message 到 DB
        ai_msg_record = Message(
            conversation_id=uuid.UUID(conversation_id),
            content=response_text,
            role=MessageRoleEnum.assistant,
            status="SUCCESS"
        )
        db.add(ai_msg_record)
        await db.commit()

        # 7. 整理 Source Nodes (引用來源)
        sources = []
        if response.source_nodes:
            for node in response.source_nodes:
                # 這裡可以回傳檔案名稱或內容摘要
                filename = node.metadata.get("filename", "unknown")
                sources.append(f"{filename}: {node.get_content()[:50]}...")

        return ChatResponse(
            response=response_text,
            source_nodes=sources,
            conversation_id=conversation_id
        )

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"RAG generation failed: {str(e)}")
