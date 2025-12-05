# backend/app/services/chat.py
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.engine import make_url

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.llms import ChatMessage, MessageRole as LlamaRole
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.openai import OpenAI

from app.models import Chatbot, Conversation, Message, MessageRole
from app.core.config import settings
from app.core.security import decrypt_value
from app.services.chatbot import ChatbotService
from app.core.rag_factory import get_vector_store


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chatbot_service = ChatbotService(db)

    async def chat(
        self,
        public_id: str,
        user_query: str,
        conversation_id: Optional[str] = None,
        visitor_id: Optional[str] = None
    ):
        # 1. 安全驗證：透過 Public ID 取得 Chatbot (含 Tenant Key)
        chatbot = await self.chatbot_service.get_chatbot_by_public_id(public_id)
        if not chatbot:
            raise ValueError("Invalid Chatbot Public ID")

        # 2. 處理對話 Session (Conversation)
        # 如果前端沒傳 conversation_id，或是傳了但在 DB 找不到，就開一個新的
        conversation = None
        if conversation_id:
            query = select(Conversation).where(
                Conversation.id == conversation_id)
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                chatbot_id=chatbot.id,
                visitor_id=visitor_id
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

        # 3. 儲存 User Message 到 DB
        user_msg_record = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_query
        )
        self.db.add(user_msg_record)
        await self.db.commit()

        # 4. 準備 LlamaIndex 環境
        # 4.1 決定 API Key (Tenant > System)
        tenant_openai_key = None
        if chatbot.tenant and chatbot.tenant.encrypted_openai_key:
            tenant_openai_key = decrypt_value(
                chatbot.tenant.encrypted_openai_key)

        # 若 Tenant 沒設定，則返回錯誤
        if not tenant_openai_key:
            raise ValueError("Tenant OpenAI API Key is not configured.")

        # 設定 LLM (GPT-3.5/4)
        llm = OpenAI(
            model=settings.OPENAI_CHAT_LLM_NAME or "gpt-4o-mini",
            api_key=tenant_openai_key,
            temperature=0.1
        )

        # 4.2 連接 PGVector
        vector_store = get_vector_store()
        # 注意: 這裡的 vector_store 已經在 rag_factory 處理好連線參數與 Table 名稱

        # 4.3 建立 Index View
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            # 注意: 這裡不直接傳 embed_model，通常依賴全域 Settings 或在此處重新初始化 OpenAIEmbedding
        )

        # 5. RAG 核心：Metadata Filters (SaaS 隔離關鍵!)
        # 強制只檢索該 chatbot_id 的向量
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="chatbot_id", value=str(chatbot.id))]
        )

        # 6. 建構 Chat Engine
        # 使用 CondensePlusContext 模式：會先將對話歷史壓縮成一個獨立 Query，再檢索
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            llm=llm,
            filters=filters,
            verbose=True,
            # 這裡可以載入歷史訊息給 LLM 當 Context，目前我們先給空的，
            # 讓它專注於回答當前問題 (Stateless REST API pattern)，
            # 若需多輪對話記憶，需將 DB 中的 Messages 轉為 LlamaIndex ChatMessage 傳入
        )

        # 執行 RAG 查詢
        response = await chat_engine.achat(user_query)
        response_text = str(response)

        # 7. 整理引用來源 (Citations)
        source_nodes = []
        if response.source_nodes:
            for node in response.source_nodes:
                source_nodes.append({
                    "document_id": node.metadata.get("document_id"),
                    "filename": node.metadata.get("filename"),
                    "score": node.score,
                    "text": node.get_content()[:200] + "..."  # 摘要
                })

        # 8. 儲存 Assistant Message 到 DB
        ai_msg_record = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            sources=source_nodes,
            # tokens_used 可以從 response.raw 取得，暫時略過
        )
        self.db.add(ai_msg_record)
        await self.db.commit()

        return {
            "response": response_text,
            "conversation_id": str(conversation.id),
            "source_nodes": [s['filename'] for s in source_nodes]  # 簡單回傳檔名列表
        }
