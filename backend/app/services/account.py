# backend/app/services/account.py
from typing import Optional
import uuid
from app.repositories.account import AccountRepository
from app.models import Account
from app.schemas import AccountCreate, AccountUpdate
from app.core.security import get_password_hash


class AccountService:
    def __init__(self, repo: AccountRepository):
        self.repo = repo

    async def get_account_by_email(self, email: str) -> Optional[Account]:
        return await self.repo.get_by_email(email)

    async def get_account(self, account_id: uuid.UUID) -> Optional[Account]:
        return await self.repo.get_by_id(str(account_id))

    async def create_account(self, data: AccountCreate) -> Account:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        new_account = Account(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            tenant_id=data.tenant_id,
            is_active=data.is_active
        )
        return await self.repo.create(new_account)

    async def update_account(self, account_id: uuid.UUID, data: AccountUpdate) -> Optional[Account]:
        account = await self.repo.get_by_id(str(account_id))
        if not account:
            return None

        if data.email is not None:
            account.email = data.email
        if data.full_name is not None:
            account.full_name = data.full_name
        if data.is_active is not None:
            account.is_active = data.is_active
        if data.password is not None:
            account.hashed_password = get_password_hash(data.password)

        return await self.repo.update(account)

    async def delete_account(self, account_id: uuid.UUID) -> bool:
        return await self.repo.delete(str(account_id))
