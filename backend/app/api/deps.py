# backend/app/api/deps.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.services.client import ClientService
from app.services.ingestion import IngestionService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# 新增：Client Service 依賴


def get_client_service(db: AsyncSession = Depends(get_db)) -> ClientService:
    return ClientService(db)

# 新增：Ingestion Service 依賴


def get_ingestion_service(db: AsyncSession = Depends(get_db)) -> IngestionService:
    return IngestionService(db)
