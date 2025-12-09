import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.services.chatbot import ChatbotService
from app.schemas import ChatbotCreate, ChatbotResponse, ChatbotUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/chatbots", response_model=List[ChatbotResponse])
async def list_chatbots(
    current_user=Depends(deps.get_current_user),
    chatbot_service: ChatbotService = Depends(deps.get_chatbot_service),
):
    tenant_id = current_user.tenant_id
    logger.debug(f"Listing chatbots for tenant_id: {tenant_id}")
    chatbots = await chatbot_service.list_for_tenant(str(tenant_id))
    return [
        {
            "id": str(c.id),
            "tenant_id": str(c.tenant_id),
            "name": c.name,
            "public_id": c.public_id,
            "rag_config": c.rag_config or {},
            "widget_config": c.widget_config or {},
            "is_active": c.is_active,
        }
        for c in chatbots
    ]


@router.post("/chatbots", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    data: ChatbotCreate,
    current_user=Depends(deps.get_current_user),
    chatbot_service: ChatbotService = Depends(deps.get_chatbot_service),
):
    # Override tenant_id from current user
    data.tenant_id = current_user.tenant_id
    logger.info(
        f"Creating chatbot for tenant_id: {data.tenant_id}, name: {data.name}")
    bot = await chatbot_service.create_chatbot(data)
    return {
        "id": str(bot.id),
        "tenant_id": str(bot.tenant_id),
        "name": bot.name,
        "public_id": bot.public_id,
        "rag_config": bot.rag_config or {},
        "widget_config": bot.widget_config or {},
        "is_active": bot.is_active,
    }


@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(chatbot_id: str, chatbot_service: ChatbotService = Depends(deps.get_chatbot_service)) -> Any:
    bot = await chatbot_service.get_chatbot_by_id(chatbot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return {
        "id": str(bot.id),
        "tenant_id": str(bot.tenant_id),
        "name": bot.name,
        "public_id": bot.public_id,
        "rag_config": bot.rag_config or {},
        "widget_config": bot.widget_config or {},
        "is_active": bot.is_active,
    }


@router.patch("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(chatbot_id: str, data: ChatbotUpdate, chatbot_service: ChatbotService = Depends(deps.get_chatbot_service)) -> Any:
    updated = await chatbot_service.update_chatbot(chatbot_id, **{k: v for k, v in data.model_dump().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Chatbot not found or update failed")
    return {
        "id": str(updated.id),
        "tenant_id": str(updated.tenant_id),
        "name": updated.name,
        "public_id": updated.public_id,
        "rag_config": updated.rag_config or {},
        "widget_config": updated.widget_config or {},
        "is_active": updated.is_active,
    }


@router.delete("/chatbots/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(chatbot_id: str, chatbot_service: ChatbotService = Depends(deps.get_chatbot_service)) -> None:
    ok = await chatbot_service.delete_chatbot(chatbot_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Chatbot not found or delete failed")
    return None
