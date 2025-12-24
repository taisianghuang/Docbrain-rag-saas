import uuid
from typing import Optional
from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class AccountCreate(AccountBase):
    tenant_id: uuid.UUID
    password: str = Field(..., min_length=6, description="明文密碼")


class AccountUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AccountRead(AccountBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
