# backend/app/api/deps.py
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.core.config import settings
from app.models import Account

# Import Services
from app.services.auth import AuthService
from app.services.account import AccountService
from app.services.tenant import TenantService
from app.services.chatbot import ChatbotService
from app.services.ingestion import IngestionService
from app.services.chat import ChatService

# Import Repositories
from app.repositories.document import DocumentRepository
from app.repositories.chatbot import ChatbotRepository
from app.repositories.account import AccountRepository
from app.repositories.tenant import TenantRepository
from app.repositories.conversation import ConversationRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_account_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    repo = AccountRepository(db)
    return AccountService(repo)


def get_tenant_service(db: AsyncSession = Depends(get_db)) -> TenantService:
    repo = TenantRepository(db)
    return TenantService(repo)


def get_chatbot_service(db: AsyncSession = Depends(get_db)) -> ChatbotService:
    return ChatbotService(db)


def get_ingestion_service(db: AsyncSession = Depends(get_db)) -> IngestionService:
    # Provide a DocumentRepository to the IngestionService so services no longer operate on AsyncSession directly
    document_repo = DocumentRepository(db)
    return IngestionService(document_repo)


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    chatbot_repo = ChatbotRepository(db)
    chatbot_service = ChatbotService(chatbot_repo)
    conversation_repo = ConversationRepository(db)
    return ChatService(chatbot_service, conversation_repo)


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_chatbot_repository(db: AsyncSession = Depends(get_db)) -> ChatbotRepository:
    return ChatbotRepository(db)


def get_account_repository(db: AsyncSession = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db)


def get_tenant_repository(db: AsyncSession = Depends(get_db)) -> TenantRepository:
    return TenantRepository(db)


def get_conversation_repository(db: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db)


# --- Auth Dependency (現在只負責呼叫 Service 並轉換 Exception) ---
# OAuth2 Scheme
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(reusable_oauth2),
    auth_service: AuthService = Depends(get_auth_service)
) -> Account:
    try:
        # 將邏輯委託給 Service
        user = await auth_service.get_active_user_by_token(token)
        return user
    except ValueError as e:
        # Deps 層只負責決定要回傳什麼 HTTP 狀態碼
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
