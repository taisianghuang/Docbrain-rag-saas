# backend/app/services/tenant.py
from typing import Optional
import uuid
from app.repositories.tenant import TenantRepository
from app.models import Tenant
from app.schemas import TenantCreate
from app.core.security import encrypt_value


class TenantService:
    def __init__(self, repo: TenantRepository):
        self.repo = repo

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        slug = data.slug or data.name.lower().replace(
            " ", "-") + "-" + uuid.uuid4().hex[:6]

        existing = await self.repo.get_by_slug(slug)
        if existing:
            raise ValueError("Tenant slug already exists")

        tenant = Tenant(
            name=data.name,
            slug=slug,
            encrypted_openai_key=encrypt_value(
                data.openai_key) if data.openai_key else None,
            encrypted_llama_cloud_key=encrypt_value(
                data.llama_cloud_key) if data.llama_cloud_key else None
        )
        return await self.repo.create(tenant)

    async def get_tenant(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        return await self.repo.get_by_id(str(tenant_id))

    async def update_tenant_settings(self, tenant_id: uuid.UUID, openai_key: Optional[str] = None, llama_cloud_key: Optional[str] = None) -> Optional[Tenant]:
        tenant = await self.repo.get_by_id(str(tenant_id))
        if not tenant:
            return None

        if openai_key is not None:
            tenant.encrypted_openai_key = encrypt_value(
                openai_key) if openai_key else None
        if llama_cloud_key is not None:
            tenant.encrypted_llama_cloud_key = encrypt_value(
                llama_cloud_key) if llama_cloud_key else None

        return await self.repo.update(tenant)
