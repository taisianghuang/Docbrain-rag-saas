# backend/app/services/chatbot.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Chatbot, Tenant
from app.schemas import ChatbotCreate


class ChatbotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chatbot_by_id(self, chatbot_id: str) -> Optional[Chatbot]:
        """
        透過內部 ID 取得機器人
        使用 selectinload 預先載入 Tenant，方便後續讀取 API Key
        """
        try:
            query = (
                select(Chatbot)
                .options(selectinload(Chatbot.tenant))
                .where(Chatbot.id == chatbot_id)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def get_chatbot_by_public_id(self, public_id: str) -> Optional[Chatbot]:
        """
        透過公開 ID 取得機器人 (Widget 用)
        """
        query = (
            select(Chatbot)
            .options(selectinload(Chatbot.tenant))
            .where(Chatbot.public_id == public_id)
        )
        result = await self.db.execute(query)
        chatbot = result.scalar_one_or_none()
        return chatbot

    async def create_chatbot(self, data: ChatbotCreate) -> Chatbot:
        """從 Pydantic Schema 建立機器人"""

        # 組合 Widget Config JSON
        widget_config_json = {
            "title": data.widget_title,
            "primaryColor": data.primary_color,
            "welcomeMessage": data.welcome_message
        }

        new_bot = Chatbot(
            tenant_id=data.tenant_id,
            name=data.name,
            widget_config=widget_config_json,
            rag_config={"mode": "vector", "top_k": 5},
            # public_id 由 Model 的 default function 自動生成
        )

        self.db.add(new_bot)
        await self.db.commit()
        await self.db.refresh(new_bot)
        return new_bot
