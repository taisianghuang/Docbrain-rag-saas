from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant


class TenantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        return await self.db.get(Tenant, tenant_id)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        q = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        return q.scalars().first()

    async def create(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def update(self, tenant: Tenant) -> Tenant:
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
