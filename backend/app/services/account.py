# backend/app/services/account.py
from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Account
from app.schemas import AccountCreate, AccountUpdate
from app.core.security import get_password_hash


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account_by_email(self, email: str) -> Optional[Account]:
        query = select(Account).where(Account.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_account(self, account_id: uuid.UUID) -> Optional[Account]:
        query = select(Account).where(Account.id == account_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_account(self, data: AccountCreate) -> Account:
        # 檢查 Email 是否重複
        existing = await self.get_account_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        new_account = Account(
            email=data.email,
            hashed_password=get_password_hash(data.password),  # 雜湊密碼
            full_name=data.full_name,
            tenant_id=data.tenant_id,
            is_active=data.is_active
        )
        self.db.add(new_account)
        await self.db.commit()
        await self.db.refresh(new_account)
        return new_account

    async def update_account(self, account_id: uuid.UUID, data: AccountUpdate) -> Optional[Account]:
        account = await self.get_account(account_id)
        if not account:
            return None

        # 更新欄位
        if data.email is not None:
            # TODO: 這裡應檢查新 Email 是否與其他人重複
            account.email = data.email
        if data.full_name is not None:
            account.full_name = data.full_name
        if data.is_active is not None:
            account.is_active = data.is_active
        if data.password is not None:
            account.hashed_password = get_password_hash(data.password)

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete_account(self, account_id: uuid.UUID) -> bool:
        account = await self.get_account(account_id)
        if not account:
            return False

        await self.db.delete(account)
        await self.db.commit()
        return True
