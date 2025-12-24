from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chatbot


class ChatbotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str) -> Optional[Chatbot]:
        return await self.db.get(Chatbot, id)

    async def get_with_tenant(self, chatbot_id: str) -> Optional[Chatbot]:
        q = await self.db.execute(
            select(Chatbot)
            .options(selectinload(Chatbot.tenant))
            .where(Chatbot.id == chatbot_id)
        )
        return q.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> Optional[Chatbot]:
        q = await self.db.execute(select(Chatbot).where(Chatbot.public_id == public_id))
        return q.scalars().first()

    async def list_for_tenant(self, tenant_id: str) -> List[Chatbot]:
        q = await self.db.execute(select(Chatbot).where(Chatbot.tenant_id == tenant_id))
        return q.scalars().all()

    async def create(self, chatbot: Chatbot) -> Chatbot:
        self.db.add(chatbot)
        await self.db.commit()
        await self.db.refresh(chatbot)
        return chatbot

    async def update(self, chatbot: Chatbot) -> Chatbot:
        await self.db.commit()
        await self.db.refresh(chatbot)
        return chatbot

    async def delete(self, chatbot: Chatbot) -> None:
        await self.db.delete(chatbot)
        await self.db.commit()
