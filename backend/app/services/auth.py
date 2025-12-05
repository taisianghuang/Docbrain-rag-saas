# backend/app/services/auth.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Tenant, Account, Chatbot
from app.schemas import SignupRequest
from app.core.security import get_password_hash, encrypt_value


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

        # 1. 檢查 Email 是否已存在
        query = select(Account).where(Account.email == data.email)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        # 2. 準備資料
        # 如果沒填公司名，就用 Email 前綴 (例如 john@gmail.com -> john's Workspace)
        company_name = data.company_name or f"{data.email.split('@')[0]}'s Workspace"
        slug = str(uuid.uuid4().hex[:8])  # 簡單生成唯一 slug

        # 3. 開啟 Transaction (確保 Tenant 和 Account 同時成功或失敗)
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

        # 提交
        await self.db.commit()

        return {
            "account_id": new_account.id,
            "tenant_id": new_tenant.id,
            "email": new_account.email,
            "company_name": new_tenant.name
        }
