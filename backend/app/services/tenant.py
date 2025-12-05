# backend/app/services/tenant.py
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Tenant
from app.schemas import TenantCreate
from app.core.security import encrypt_value


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        # 1. 自動生成 slug (若未填)
        slug = data.slug or data.name.lower().replace(
            " ", "-") + "-" + uuid.uuid4().hex[:6]

        # 2. 檢查 slug 是否重複 (簡單做)
        # 實際專案可能需要 while loop retry
        query = select(Tenant).where(Tenant.slug == slug)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Tenant slug already exists")

        # 3. 建立 Tenant 物件 (執行加密)
        tenant = Tenant(
            name=data.name,
            slug=slug,
            encrypted_openai_key=encrypt_value(
                data.openai_key) if data.openai_key else None,
            encrypted_llama_cloud_key=encrypt_value(
                data.llama_cloud_key) if data.llama_cloud_key else None
        )

        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def get_tenant(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
