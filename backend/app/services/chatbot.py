# backend/app/services/chatbot.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Chatbot, Tenant
from app.schemas import ChatbotCreate

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chatbot_by_id(self, chatbot_id: str) -> Optional[Chatbot]:
        """
        透過內部 ID 取得機器人
        使用 selectinload 預先載入 Tenant，方便後續讀取 API Key
        """
        logger.debug(f"Fetching chatbot by id: {chatbot_id}")
        try:
            query = (
                select(Chatbot)
                .options(selectinload(Chatbot.tenant))
                .where(Chatbot.id == chatbot_id)
            )
            result = await self.db.execute(query)
            chatbot = result.scalar_one_or_none()
            if chatbot:
                logger.debug(
                    f"Chatbot found by id: {chatbot_id}, tenant_id: {chatbot.tenant_id}")
            else:
                logger.warning(f"Chatbot not found by id: {chatbot_id}")
            return chatbot
        except Exception:
            logger.error(
                f"Error fetching chatbot by id: {chatbot_id}", exc_info=True)
            return None

    async def get_chatbot_by_public_id(self, public_id: str) -> Optional[Chatbot]:
        """
        透過公開 ID 取得機器人 (Widget 用)
        """
        logger.debug(f"Fetching chatbot by public_id: {public_id}")
        query = (
            select(Chatbot)
            .options(selectinload(Chatbot.tenant))
            .where(Chatbot.public_id == public_id)
        )
        result = await self.db.execute(query)
        chatbot = result.scalar_one_or_none()
        if chatbot:
            logger.debug(
                f"Chatbot found by public_id: {public_id}, id: {chatbot.id}, tenant_id: {chatbot.tenant_id}")
        else:
            logger.warning(f"Chatbot not found by public_id: {public_id}")
        return chatbot

    async def create_chatbot(self, data: ChatbotCreate) -> Chatbot:
        """從 Pydantic Schema 建立機器人"""
        logger.info(
            f"Creating chatbot - name: {data.name}, tenant_id: {data.tenant_id}")

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
        logger.info(
            f"Chatbot created successfully - id: {new_bot.id}, public_id: {new_bot.public_id}, tenant_id: {data.tenant_id}")
        return new_bot

    async def list_for_tenant(self, tenant_id: str) -> list[Chatbot]:
        try:
            query = select(Chatbot).where(Chatbot.tenant_id == tenant_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception:
            logger.error(
                f"Error listing chatbots for tenant: {tenant_id}", exc_info=True)
            return []

    async def update_chatbot(self, chatbot_id: str, **fields) -> Optional[Chatbot]:
        """更新機器人設定（部分更新）。fields 可以包含 name, widget_config, rag_config 等。"""
        chatbot = await self.get_chatbot_by_id(chatbot_id)
        if not chatbot:
            return None

        for k, v in fields.items():
            if hasattr(chatbot, k) and v is not None:
                setattr(chatbot, k, v)

        try:
            await self.db.commit()
            await self.db.refresh(chatbot)
            logger.info(f"Chatbot updated - id: {chatbot.id}")
            return chatbot
        except Exception:
            logger.error(
                f"Error updating chatbot - id: {chatbot_id}", exc_info=True)
            return None

    async def delete_chatbot(self, chatbot_id: str) -> bool:
        chatbot = await self.get_chatbot_by_id(chatbot_id)
        if not chatbot:
            return False
        try:
            await self.db.delete(chatbot)
            await self.db.commit()
            logger.info(f"Chatbot deleted - id: {chatbot_id}")
            return True
        except Exception:
            logger.error(
                f"Error deleting chatbot - id: {chatbot_id}", exc_info=True)
            return False
