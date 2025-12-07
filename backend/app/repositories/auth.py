from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, Tenant, Chatbot


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account_by_email(self, email: str) -> Optional[Account]:
        q = await self.db.execute(select(Account).where(Account.email == email))
        return q.scalars().first()

    async def get_account_by_id(self, account_id: str) -> Optional[Account]:
        return await self.db.get(Account, account_id)

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        await self.db.flush()
        return tenant

    async def create_account(self, account: Account) -> Account:
        self.db.add(account)
        return account

    async def create_chatbot(self, chatbot: Chatbot) -> Chatbot:
        self.db.add(chatbot)
        return chatbot

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        """Flush pending changes to DB without committing (get IDs for FK relationships)"""
        await self.db.flush()

    async def refresh(self, instance):
        await self.db.refresh(instance)
