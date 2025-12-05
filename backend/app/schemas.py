# backend/app/schemas.py
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    public_id: str = Field(..., description="Widget Public ID")
    messages: List[Message] = Field(..., description="對話歷史紀錄")
    visitor_id: Optional[str] = Field(None, description="訪客指紋 ID")
    conversation_id: Optional[str] = Field(None, description="若為延續對話請帶入此 ID")


class ChatResponse(BaseModel):
    response: str
    source_nodes: List[str] = []
    conversation_id: str


class IngestResponse(BaseModel):
    status: str
    document_id: str
    chunks: int


# --- Tenant Schemas (註冊租戶) ---
class TenantCreate(BaseModel):
    name: str = Field(..., description="公司/組織名稱")
    # Slug 用於 URL，若未填後端可自動生成
    slug: Optional[str] = Field(None, description="URL 識別碼 (如: my-company)")

    # 這些 Key 傳入後會被後端加密，不會明文存入 DB
    openai_key: Optional[str] = Field(None, description="OpenAI API Key")
    llama_cloud_key: Optional[str] = Field(
        None, description="LlamaCloud API Key")


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    # 注意：我們絕對不回傳 API Key，即使是加密過的也不回傳


# --- Chatbot Schemas (創建機器人) ---
class ChatbotCreate(BaseModel):
    tenant_id: uuid.UUID = Field(..., description="歸屬的租戶 ID")
    name: str = Field(..., description="機器人名稱")

    # UI 設定
    widget_title: str = "Chat Assistant"
    primary_color: str = "#2563eb"
    welcome_message: str = "Hi! How can I help you?"


class ChatbotRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    public_id: str  # <--- 這就是 Widget 要用的 ID
    widget_config: dict
    is_active: bool


# --- Account Schemas ---
class AccountBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class AccountCreate(AccountBase):
    tenant_id: uuid.UUID
    password: str = Field(..., min_length=6, description="明文密碼")


class AccountUpdate(BaseModel):
    # 支援部分更新
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AccountRead(AccountBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    # 絕對不回傳 password


# --- Authentication / Registration ---
class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="登入信箱")
    password: str = Field(..., min_length=6, description="登入密碼")
    company_name: Optional[str] = Field(
        None, description="公司名稱 (未填則預設使用 Email 前綴)")

    # 這裡可以選擇性讓用戶在註冊時就填 Key，或者註冊後去設定頁面填
    openai_key: Optional[str] = None
    llama_cloud_key: Optional[str] = None


class SignupResponse(BaseModel):
    account_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    company_name: str
    message: str = "Registration successful"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
