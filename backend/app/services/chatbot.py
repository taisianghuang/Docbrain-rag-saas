# backend/app/services/chatbot.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Chatbot, Tenant
from app.models.config_schemas import RagConfigSchema, WidgetConfigSchema
from app.schemas import ChatbotCreate

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _normalize_widget_config(self, widget_config: dict) -> dict:
        """Normalize widget_config from camelCase to snake_case."""
        normalized = {}
        for key, value in widget_config.items():
            if key == "primaryColor":
                normalized["primary_color"] = value
            elif key == "welcomeMessage":
                normalized["welcome_message"] = value
            else:
                normalized[key] = value
        return WidgetConfigSchema(**normalized).model_dump()

    def _normalize_rag_config(self, rag_config: dict) -> dict:
        """Validate and normalize rag_config using schema."""
        return RagConfigSchema(**rag_config).model_dump()

    def _apply_field_update(self, chatbot: Chatbot, field_name: str, value: any) -> None:
        """Apply a single field update with normalization if needed."""
        if field_name == "rag_config":
            setattr(chatbot, field_name, self._normalize_rag_config(value))
        elif field_name == "widget_config":
            setattr(chatbot, field_name, self._normalize_widget_config(value))
        else:
            setattr(chatbot, field_name, value)

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

        # Normalize configs using helper methods
        rag_config_json = (
            self._normalize_rag_config(data.rag_config)
            if data.rag_config
            else RagConfigSchema().model_dump()
        )

        widget_config_json = (
            self._normalize_widget_config(data.widget_config)
            if data.widget_config
            else WidgetConfigSchema().model_dump()
        )

        new_bot = Chatbot(
            tenant_id=data.tenant_id,
            name=data.name,
            widget_config=widget_config_json,
            rag_config=rag_config_json,
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

        # Apply field updates using helper method
        for field_name, value in fields.items():
            if self._should_update_field(chatbot, field_name, value):
                self._apply_field_update(chatbot, field_name, value)

        return await self._commit_update(chatbot, chatbot_id)

    def _should_update_field(self, chatbot: Chatbot, field_name: str, value: any) -> bool:
        """Check if a field should be updated."""
        return hasattr(chatbot, field_name) and value is not None

    async def _commit_update(self, chatbot: Chatbot, chatbot_id: str) -> Optional[Chatbot]:
        """Commit chatbot update to database."""
        try:
            await self.db.commit()
            await self.db.refresh(chatbot)
            logger.info(f"Chatbot updated - id: {chatbot.id}")
            return chatbot
        except Exception:
            logger.error(
                f"Error updating chatbot - id: {chatbot_id}", exc_info=True)
            await self.db.rollback()
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
