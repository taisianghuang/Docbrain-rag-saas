import uuid
from pydantic import BaseModel, Field
from typing import Optional


class TenantCreate(BaseModel):
    name: str = Field(..., description="公司/組織名稱")
    slug: Optional[str] = Field(None, description="URL 識別碼 (如: my-company)")
    openai_key: Optional[str] = Field(None, description="OpenAI API Key")
    llama_cloud_key: Optional[str] = Field(
        None, description="LlamaCloud API Key")


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
