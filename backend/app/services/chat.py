# backend/app/services/chat.py
import os
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.llms.openai import OpenAI
from llama_index.core.postprocessor import SimilarityPostprocessor

from app.models import Conversation, Message, MessageRole
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

        # 2. 讀取 RAG Config (SaaS 核心邏輯)
        # 預設值: mode="vector", top_k=5, temperature=0.1
        rag_config = chatbot.rag_config or {}
        strategy_mode = rag_config.get("mode", "vector")
        top_k = int(rag_config.get("top_k", 5))
        temperature = float(rag_config.get("temperature", 0.1))

        # 系統提示詞 (Persona)
        system_prompt = (
            chatbot.widget_config.get("system_prompt") or
            "You are a helpful AI assistant. Answer based on the context provided."
        )

        # 3. 處理對話 Session (Conversation)
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

        # 4. 儲存 User Message 到 DB
        user_msg_record = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_query
        )
        self.db.add(user_msg_record)
        await self.db.commit()

        # 5. 準備 LLM 環境
        # 決定 API Key (Tenant)
        tenant_openai_key = None
        if chatbot.tenant and chatbot.tenant.encrypted_openai_key:
            tenant_openai_key = decrypt_value(
                chatbot.tenant.encrypted_openai_key)

        # 沒有設定 tenant_openai_key 報錯
        if not tenant_openai_key:
            raise ValueError("No OpenAI API key configured for tenant")

        # 設定 LLM (使用動態 Temperature)
        llm = OpenAI(
            model=settings.OPENAI_CHAT_LLM_NAME or "gpt-4o-mini",
            api_key=tenant_openai_key,
            temperature=temperature
        )

        # 6. 連接 Vector Store (使用工廠模式)
        vector_store = get_vector_store()

        # 建立 Index View
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        # 7. Metadata Filters (強制隔離)
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="chatbot_id", value=str(chatbot.id))]
        )

        # 8. 策略配置 (RAG Strategy Implementation)
        # 這裡根據 rag_config 的不同，配置不同的 Retriever 參數

        chat_engine_kwargs = {
            # 這是最適合 Chatbot 的模式 (會改寫 Query)
            "chat_mode": "condense_plus_context",
            "llm": llm,
            "filters": filters,
            "system_prompt": system_prompt,
            "verbose": True,
        }

        # --- Strategy Logic ---
        if strategy_mode == "fast":
            # 快速模式：減少檢索量，只取高信心分數的
            chat_engine_kwargs["similarity_top_k"] = 3
            chat_engine_kwargs["node_postprocessors"] = [
                SimilarityPostprocessor(similarity_cutoff=0.80)
            ]

        elif strategy_mode == "precise":
            # 精準模式：檢索更多內容，提供更豐富 Context
            # (未來可在這裡加入 Reranker)
            chat_engine_kwargs["similarity_top_k"] = 10
            chat_engine_kwargs["node_postprocessors"] = [
                SimilarityPostprocessor(similarity_cutoff=0.70)
            ]

        else:  # "balanced" or "vector" (Default)
            chat_engine_kwargs["similarity_top_k"] = top_k
            # 不特別設定 Postprocessor，直接使用原始 top_k
        # ----------------------

        # 9. 建構 Chat Engine
        chat_engine = index.as_chat_engine(**chat_engine_kwargs)

        # 10. 執行查詢
        response = await chat_engine.achat(user_query)
        response_text = str(response)

        # 11. 整理引用來源
        source_nodes = []
        if response.source_nodes:
            for node in response.source_nodes:
                source_nodes.append({
                    "document_id": node.metadata.get("document_id"),
                    "filename": node.metadata.get("filename"),
                    "score": node.score,
                    # 避免內容太長塞爆 DB
                    "text": (node.get_content()[:200] + "...") if node.get_content() else ""
                })

        # 12. 儲存 Assistant Message
        ai_msg_record = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            sources=source_nodes,
        )
        self.db.add(ai_msg_record)
        await self.db.commit()

        return {
            "response": response_text,
            "conversation_id": str(conversation.id),
            "source_nodes": [s['filename'] for s in source_nodes]
        }
