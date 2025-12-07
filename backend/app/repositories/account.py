from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[Account]:
        q = await self.db.execute(select(Account).where(Account.email == email))
        return q.scalars().first()

    async def get_by_id(self, account_id: str) -> Optional[Account]:
        return await self.db.get(Account, account_id)

    async def create(self, account: Account) -> Account:
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update(self, account: Account) -> Account:
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete(self, account_id: str) -> bool:
        account = await self.get_by_id(account_id)
        if not account:
            return False
        await self.db.delete(account)
        await self.db.commit()
        return True
