# backend/app/services/client.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.client import Client


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """透過 ID 取得租戶資料"""
        try:
            query = select(Client).where(Client.id == client_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def get_client_by_api_key(self, api_key: str) -> Optional[Client]:
        """透過 API Key 驗證租戶 (未來 API 驗證用)"""
        query = select(Client).where(Client.api_key == api_key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_client(self, name: str, widget_config: dict = None) -> Client:
        """註冊新租戶"""
        new_client = Client(
            name=name,
            widget_config=widget_config or {}
        )
        self.db.add(new_client)
        await self.db.commit()
        await self.db.refresh(new_client)
        return new_client
