# backend/app/services/auth.py
"""
AuthService refactored to depend on AuthRepository.
"""
import logging
import uuid
from typing import Optional
from jose import jwt, JWTError

from app.schemas import TokenPayload, SignupRequest
from app.core.security import get_password_hash, encrypt_value, verify_password, create_access_token
from app.core.config import settings
from app.repositories.auth import AuthRepository
from app.models import Tenant, Account, Chatbot

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register(self, data: SignupRequest) -> dict:
        logger.debug(f"Starting registration process for email: {data.email}")

        existing = await self.repo.get_account_by_email(data.email)
        if existing:
            logger.warning(
                f"Registration failed - Email already registered: {data.email}")
            raise ValueError("Email already registered")

        company_name = data.company_name or f"{data.email.split('@')[0]}'s Workspace"
        slug = str(uuid.uuid4().hex[:8])

        try:
            new_tenant = Tenant(
                name=company_name,
                slug=slug,
                encrypted_openai_key=encrypt_value(
                    data.openai_key) if data.openai_key else None,
                encrypted_llama_cloud_key=encrypt_value(
                    data.llama_cloud_key) if data.llama_cloud_key else None
            )
            await self.repo.create_tenant(new_tenant)
            await self.repo.commit()
            await self.repo.refresh(new_tenant)

            new_account = Account(
                email=data.email,
                hashed_password=get_password_hash(data.password),
                tenant_id=new_tenant.id,
                full_name=company_name,
                is_superuser=True,
                is_active=True
            )
            await self.repo.create_account(new_account)

            default_bot = Chatbot(
                tenant_id=new_tenant.id,
                name="My First Bot",
                rag_config={"mode": "vector", "top_k": 5},
                widget_config={
                    "title": "Welcome Bot",
                    "primaryColor": "#2563eb",
                    "welcomeMessage": "Hello! I am your AI assistant."
                }
            )
            await self.repo.create_chatbot(default_bot)

            await self.repo.commit()
            await self.repo.refresh(new_account)
            await self.repo.refresh(default_bot)

            logger.info(f"Registration committed for email: {data.email}")
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            raise

        return {
            "account_id": new_account.id,
            "tenant_id": new_tenant.id,
            "email": new_account.email,
            "company_name": new_tenant.name
        }

    async def authenticate(self, email: str, password: str) -> Optional[dict]:
        logger.debug(f"Authenticating user with email: {email}")
        account = await self.repo.get_account_by_email(email)
        if not account:
            logger.warning(
                f"Authentication failed - Account not found for email: {email}")
            return None
        if not verify_password(password, account.hashed_password):
            logger.warning(
                f"Authentication failed - Invalid password for email: {email}")
            return None

        access_token = create_access_token(subject=account.id)
        logger.info(
            f"Authentication successful for email: {email}, account_id: {account.id}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": account.email,
                "full_name": account.full_name,
                "tenant_id": account.tenant_id
            }
        }

    async def get_active_user_by_token(self, token: str) -> Account:
        try:
            logger.debug("Decoding JWT token")
            payload = jwt.decode(token, settings.SECRET_KEY,
                                 algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)
        except (JWTError, AttributeError) as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise ValueError("Could not validate credentials")

        user = await self.repo.get_account_by_id(token_data.sub)
        if not user:
            logger.warning(f"User not found for account_id: {token_data.sub}")
            raise ValueError("User not found")
        if not user.is_active:
            logger.warning(
                f"Inactive user attempted access, account_id: {token_data.sub}")
            raise ValueError("Inactive user")

        logger.info(
            f"Active user retrieved successfully, account_id: {token_data.sub}")
        return user
