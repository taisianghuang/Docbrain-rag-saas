# backend/app/api/deps.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
# --- 修改 Imports ---
from app.services.chatbot import ChatbotService
from app.services.ingestion import IngestionService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# --- 新增 ChatbotService 依賴 ---


def get_chatbot_service(db: AsyncSession = Depends(get_db)) -> ChatbotService:
    return ChatbotService(db)

# --- IngestionService 依賴 ---


def get_ingestion_service(db: AsyncSession = Depends(get_db)) -> IngestionService:
    return IngestionService(db)
