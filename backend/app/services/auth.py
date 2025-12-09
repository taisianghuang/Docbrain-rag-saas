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
        logger.debug("Starting registration process")

        existing = await self.repo.get_account_by_email(data.email)
        if existing:
            logger.warning("Registration failed - Email already registered")
            raise ValueError("Email already registered")

        company_name = data.company_name or f"{data.email.split('@')[0]}'s Workspace"
        slug = str(uuid.uuid4().hex[:8])

        try:
            # Step 1: Create Tenant (flush to get ID, but don't commit yet)
            new_tenant = Tenant(
                name=company_name,
                slug=slug,
                encrypted_openai_key=encrypt_value(
                    data.openai_key) if data.openai_key else None,
                encrypted_llama_cloud_key=encrypt_value(
                    data.llama_cloud_key) if data.llama_cloud_key else None
            )
            await self.repo.create_tenant(new_tenant)
            await self.repo.flush()  # Get tenant.id without commit
            # Save ID before commit (attributes expire after commit)
            tenant_id = new_tenant.id
            logger.debug(f"Tenant created with id: {tenant_id}")

            # Step 2: Create Account (flush, don't commit)
            new_account = Account(
                email=data.email,
                hashed_password=get_password_hash(data.password),
                tenant_id=tenant_id,
                full_name=company_name,
                is_superuser=True,
                is_active=True
            )
            await self.repo.create_account(new_account)
            await self.repo.flush()  # Get account.id without commit
            account_id = new_account.id  # Save ID before commit
            logger.debug(f"Account created with id: {account_id}")

            # Step 3: Create default Chatbot (flush, don't commit)
            default_bot = Chatbot(
                tenant_id=tenant_id,
                name="My First Bot",
                rag_config={"mode": "vector", "top_k": 5},
                widget_config={
                    "title": "Welcome Bot",
                    "primaryColor": "#2563eb",
                    "welcomeMessage": "Hello! I am your AI assistant."
                }
            )
            await self.repo.create_chatbot(default_bot)
            await self.repo.flush()  # Get chatbot.id without commit
            chatbot_id = default_bot.id  # Save ID before commit
            logger.debug(f"Chatbot created with id: {chatbot_id}")

            # Step 4: Single commit for all three entities (atomic transaction)
            await self.repo.commit()
            logger.info(
                f"Registration committed (atomic) for email: {data.email}, tenant_id: {tenant_id}")

        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            raise

        return {
            "account_id": account_id,
            "tenant_id": tenant_id,
            "email": new_account.email,
            "company_name": company_name
        }

    async def authenticate(self, email: str, password: str) -> Optional[dict]:
        logger.debug("Authenticating user")
        account = await self.repo.get_account_by_email(email)
        if not account:
            logger.warning("Authentication failed - Account not found")
            return None
        if not verify_password(password, account.hashed_password):
            logger.warning("Authentication failed - Invalid password")
            return None

        access_token = create_access_token(subject=account.id)
        logger.info("Authentication successful")

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
