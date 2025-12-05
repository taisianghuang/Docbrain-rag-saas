# backend/app/api/deps.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.chatbot import ChatbotService
from app.services.ingestion import IngestionService
from app.services.chat import ChatService
from app.services.tenant import TenantService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_chatbot_service(db: AsyncSession = Depends(get_db)) -> ChatbotService:
    return ChatbotService(db)


def get_ingestion_service(db: AsyncSession = Depends(get_db)) -> IngestionService:
    return IngestionService(db)


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


def get_tenant_service(db: AsyncSession = Depends(get_db)) -> TenantService:
    return TenantService(db)
