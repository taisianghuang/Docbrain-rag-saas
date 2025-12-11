import uuid
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="登入信箱")
    password: str = Field(..., min_length=8, max_length=30, description="登入密碼")
    company_name: Optional[str] = Field(
        None, description="公司名稱 (未填則預設使用 Email 前綴)")
    openai_key: Optional[str] = None
    llama_cloud_key: Optional[str] = None


class SignupResponse(BaseModel):
    account_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    company_name: str
    message: str = "Registration successful"


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="登入信箱")
    password: str = Field(..., description="登入密碼")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
