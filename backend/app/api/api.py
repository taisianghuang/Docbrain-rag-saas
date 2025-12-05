# backend/app/api/api.py
from fastapi import APIRouter
from app.api.endpoints import conversation, documents, health, admin, auth

api_router = APIRouter()

# 註冊對話 API (POST /api/conversation/chat)
api_router.include_router(
    conversation.router,
    prefix="/conversation",
    tags=["conversation"]
)

# 註冊文件 API (POST /api/document/ingest)
api_router.include_router(
    documents.router,
    prefix="/document",
    tags=["document"]
)

# 註冊健康檢查
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# 註冊 Auth API
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)
