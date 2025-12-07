# backend/app/services/chat.py
import logging
from typing import Optional
from sqlalchemy.engine import make_url

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore

from app.models import Conversation, Message, MessageRole, LlamaIndexStore
from app.core.config import settings
from app.core.security import decrypt_value
from app.services.chatbot import ChatbotService
from app.repositories.conversation import ConversationRepository
from app.core.rag_strategies import create_chat_engine

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, chatbot_service: ChatbotService, conversation_repo: ConversationRepository):
        self.chatbot_service = chatbot_service
        self.conversation_repo = conversation_repo

    async def chat(
        self,
        public_id: str,
        user_query: str,
        conversation_id: Optional[str] = None,
        visitor_id: Optional[str] = None
    ):
        logger.debug(
            f"Chat service: fetching chatbot with public_id: {public_id}")
        chatbot = await self.chatbot_service.get_chatbot_by_public_id(public_id)
        if not chatbot:
            logger.warning(
                f"Chat service: Invalid chatbot public_id: {public_id}")
            raise ValueError("Invalid Chatbot Public ID")
        logger.debug(
            f"Chat service: Chatbot found - id: {chatbot.id}, tenant_id: {chatbot.tenant_id}")

        tenant_openai_key = None
        if chatbot.tenant and chatbot.tenant.encrypted_openai_key:
            tenant_openai_key = decrypt_value(
                chatbot.tenant.encrypted_openai_key)

        if not tenant_openai_key:
            logger.error(
                f"Chat service: Missing OpenAI key for chatbot - id: {chatbot.id}, tenant_id: {chatbot.tenant_id}")
            raise ValueError(
                "Tenant OpenAI Key is missing. Please configure it in the dashboard.")

        logger.debug(
            f"Chat service: Processing conversation - conversation_id: {conversation_id}, visitor_id: {visitor_id}")
        conversation = None
        if conversation_id:
            conversation = await self.conversation_repo.get_by_id(conversation_id)

        if not conversation:
            logger.debug(
                f"Chat service: Creating new conversation for chatbot_id: {chatbot.id}")
            conversation = Conversation(
                chatbot_id=chatbot.id, visitor_id=visitor_id)
            conversation = await self.conversation_repo.create(conversation)

        logger.debug(
            f"Chat service: Saving user message - conversation_id: {conversation.id}, query length: {len(user_query)}")
        user_msg = Message(conversation_id=conversation.id,
                           role=MessageRole.USER, content=user_query)
        await self.conversation_repo.add_message(user_msg)

        logger.debug(
            f"Chat service: Setting up RAG environment for chatbot_id: {chatbot.id}")

        rag_config = chatbot.rag_config or {}
        temperature = float(rag_config.get("temperature", 0.1))
        logger.debug(
            f"Chat service: RAG config - mode: {rag_config.get('mode')}, temperature: {temperature}")

        llm = OpenAI(
            model=settings.OPENAI_CHAT_LLM_NAME or "gpt-4o-mini",
            api_key=tenant_openai_key,
            temperature=temperature
        )

        db_url = make_url(settings.DATABASE_URL)
        vector_store = PGVectorStore.from_params(
            database=db_url.database,
            host=db_url.host,
            password=db_url.password,
            port=db_url.port,
            user=db_url.username,
            table_name=LlamaIndexStore.__tablename__,
            embed_dim=1536,
        )

        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="chatbot_id", value=str(chatbot.id))]
        )

        system_prompt = chatbot.widget_config.get(
            "system_prompt") or "You are a helpful AI."

        logger.debug(f"Chat service: Creating chat engine with strategy")
        chat_engine = create_chat_engine(
            index=index,
            llm=llm,
            filters=filters,
            system_prompt=system_prompt,
            rag_config=rag_config
        )

        logger.debug(f"Chat service: Executing achat with user query")
        response = await chat_engine.achat(user_query)
        response_text = str(response)
        logger.debug(
            f"Chat service: Chat completed - response length: {len(response_text)}")

        source_nodes = []
        if response.source_nodes:
            logger.debug(
                f"Chat service: Found {len(response.source_nodes)} source nodes")
            for node in response.source_nodes:
                source_nodes.append({
                    "document_id": node.metadata.get("document_id"),
                    "filename": node.metadata.get("filename"),
                    "score": node.score,
                    "text": (node.get_content()[:200] + "...") if node.get_content() else ""
                })

        logger.debug(
            f"Chat service: Saving assistant message - conversation_id: {conversation.id}")
        ai_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            sources=source_nodes
        )
        await self.conversation_repo.add_message(ai_msg)
        logger.info(
            f"Chat service completed - conversation_id: {conversation.id}, source_nodes: {len(source_nodes)}")

        return {
            "response": response_text,
            "conversation_id": str(conversation.id),
            "source_nodes": [s['filename'] for s in source_nodes]
        }
