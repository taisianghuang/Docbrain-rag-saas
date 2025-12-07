# backend/app/services/auth.py
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models import Tenant, Account, Chatbot
from app.schemas import TokenPayload, SignupRequest
from app.core.security import get_password_hash, encrypt_value
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.models import Account
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: SignupRequest) -> dict:
        """
        單一流程註冊：
        1. 檢查 Email 重複
        2. 建立 Tenant (公司)
        3. 建立 Account (管理員)
        4. (Optional) 建立預設 Chatbot
        """
        logger.debug(f"Starting registration process for email: {data.email}")
        # 1. 檢查 Email 是否已存在
        query = select(Account).where(Account.email == data.email)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            logger.warning(
                f"Registration failed - Email already registered: {data.email}")
            raise ValueError("Email already registered")

        # 2. 準備資料
        # 如果沒填公司名，就用 Email 前綴 (例如 john@gmail.com -> john's Workspace)
        company_name = data.company_name or f"{data.email.split('@')[0]}'s Workspace"
        slug = str(uuid.uuid4().hex[:8])  # 簡單生成唯一 slug
        logger.debug(
            f"Creating tenant with company_name: {company_name}, slug: {slug}")

        # 3. 開啟 Transaction (確保 Tenant 和 Account 同時成功或失敗)
        try:
            async with self.db.begin_nested():
                # A. 建立 Tenant
                new_tenant = Tenant(
                    name=company_name,
                    slug=slug,
                    encrypted_openai_key=encrypt_value(
                        data.openai_key) if data.openai_key else None,
                    encrypted_llama_cloud_key=encrypt_value(
                        data.llama_cloud_key) if data.llama_cloud_key else None
                )
                self.db.add(new_tenant)
                await self.db.flush()  # 為了拿到 new_tenant.id
                logger.debug(f"Tenant created with id: {new_tenant.id}")

                # B. 建立 Account (連結到上面的 Tenant)
                new_account = Account(
                    email=data.email,
                    hashed_password=get_password_hash(data.password),
                    tenant_id=new_tenant.id,
                    full_name=company_name,  # 預設名稱
                    is_superuser=True,      # 註冊者就是管理員
                    is_active=True
                )
                self.db.add(new_account)
                logger.debug(f"Account created with id: {new_account.id}")

                # C. (Optional) 自動建立一個預設 Chatbot，讓用戶一進來就有東西玩
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
                self.db.add(default_bot)
                logger.debug(
                    f"Default chatbot created with id: {default_bot.id}")

            # 提交
            await self.db.commit()
            logger.info(
                f"Registration transaction committed successfully for email: {data.email}")
        except Exception as e:
            logger.error(
                f"Registration transaction failed for email: {data.email}: {str(e)}", exc_info=True)
            raise

        return {
            "account_id": new_account.id,
            "tenant_id": new_tenant.id,
            "email": new_account.email,
            "company_name": new_tenant.name
        }


async def authenticate(self, email: str, password: str) -> Optional[dict]:
    """
    驗證使用者登入
    回傳 Token 物件或是 None
    """
    logger.debug(f"Authenticating user with email: {email}")
    # 1. 找帳號
    query = select(Account).where(Account.email == email)
    result = await self.db.execute(query)
    account = result.scalar_one_or_none()

    # 2. 驗證
    if not account:
        logger.warning(
            f"Authentication failed - Account not found for email: {email}")
        return None
    if not verify_password(password, account.hashed_password):
        logger.warning(
            f"Authentication failed - Invalid password for email: {email}")
        return None

    # 3. 登入成功，生成 Token
    # 我們將 Account ID 放入 Token 的 sub (Subject) 欄位
    access_token = create_access_token(subject=account.id)
    logger.info(
        f"Authentication successful for email: {email}, account_id: {account.id}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        # 可以順便回傳使用者基本資料給前端
        "user": {
            "email": account.email,
            "full_name": account.full_name,
            "tenant_id": account.tenant_id
        }
    }


async def get_active_user_by_token(self, token: str) -> Account:
    """
    解析 Token 並取得活躍用戶。
    若失敗則拋出具體的 ValueError，讓上層 (deps) 決定如何處理 HTTP 回應。
    """
    try:
        # 1. 解碼 JWT
        logger.debug("Decoding JWT token")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        logger.debug(
            f"Token decoded successfully, account_id: {token_data.sub}")
    except (JWTError, AttributeError) as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise ValueError("Could not validate credentials")

    # 2. 查詢 DB
    query = select(Account).where(Account.id == token_data.sub)
    result = await self.db.execute(query)
    user = result.scalar_one_or_none()

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
