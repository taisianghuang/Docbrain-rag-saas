# backend/app/api/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.schemas import TenantCreate, TenantRead, ChatbotCreate, ChatbotRead
from app.services.tenant import TenantService
from app.services.chatbot import ChatbotService

router = APIRouter()


@router.post("/tenants", response_model=TenantRead)
async def register_tenant(
    data: TenantCreate,
    tenant_service: TenantService = Depends(deps.get_tenant_service)
):
    """
    [Admin] 註冊新租戶 
    """
    try:
        tenant = await tenant_service.create_tenant(data)
        return tenant
    except Exception as e:
        # 實際應處理 IntegrityError (如 Slug 重複)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chatbots", response_model=ChatbotRead)
async def create_chatbot(
    data: ChatbotCreate,
    chatbot_service: ChatbotService = Depends(deps.get_chatbot_service),
    tenant_service: TenantService = Depends(deps.get_tenant_service)
):
    """
    [Admin] 為租戶創建機器人 
    回傳的資料中會包含 public_id，這就是 Widget 要用的 ID。
    """
    # 1. 檢查 Tenant 是否存在
    tenant = await tenant_service.get_tenant(data.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 2. 建立機器人
    chatbot = await chatbot_service.create_chatbot(data)
    return chatbot
