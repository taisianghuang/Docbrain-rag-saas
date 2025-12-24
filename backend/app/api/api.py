# backend/app/api/api.py
from fastapi import APIRouter
from app.api.endpoints import conversation, documents, health, auth, chatbots, settings, rag_config

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

# 註冊 Chatbots API
api_router.include_router(
    chatbots.router,
    tags=["chatbots"]
)

# 註冊 Settings API
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"]
)

# 註冊 RAG Config API
api_router.include_router(
    rag_config.router,
    prefix="/rag-config",
    tags=["rag-config"]
)
