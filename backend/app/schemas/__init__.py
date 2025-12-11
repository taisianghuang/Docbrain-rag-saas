"""Schemas package for application-level Pydantic models.

Expose legacy/common schemas and RAG-specific schemas under `app.schemas`.
"""
"""`app.schemas` package exports.

This package re-exports the commonly used schema classes so callers can do:

	from app import schemas
	from app.schemas import ChatRequest

Or import more specifically from modules like `app.schemas.chat`.
"""

from .messages import Role, Message
from .chat import ChatRequest, ChatResponse, IngestResponse
from .tenant import TenantCreate, TenantRead
from .chatbot import (
    ChatbotCreate,
    ChatbotRead,
    ChatbotUpdate,
    ChatbotResponse,
)
from .account import AccountBase, AccountCreate, AccountUpdate, AccountRead
from .auth import SignupRequest, SignupResponse, LoginRequest, Token, TokenPayload
from .rag_config import *

__all__ = [
    "Role",
    "Message",
    "ChatRequest",
    "ChatResponse",
    "IngestResponse",
    "TenantCreate",
    "TenantRead",
    "ChatbotCreate",
    "ChatbotRead",
    "ChatbotUpdate",
    "ChatbotResponse",
    "AccountBase",
    "AccountCreate",
    "AccountUpdate",
    "AccountRead",
    "SignupRequest",
    "SignupResponse",
    "LoginRequest",
    "Token",
    "TokenPayload",
]

__all__ = []
__all__.extend(name for name in dir() if not name.startswith("_"))
