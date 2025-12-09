# backend/app/api/endpoints/auth.py
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api import deps
from app.schemas import SignupRequest, SignupResponse, Token, LoginRequest
from app.schemas import SignupRequest, SignupResponse
from app.services.auth import AuthService
import re

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: SignupRequest,
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    """
    SaaS 公開註冊接口：
    輸入 Email/Password -> 自動建立 Tenant + Account + Default Bot
    """
    logger.info("Register attempt received")
    # Run additional sign-up validations that can produce multiple messages
    errors: list[str] = []

    # Password complexity rules
    pw = data.password or ""
    if len(pw) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", pw):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", pw):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", pw):
        errors.append("Password must contain at least one digit.")

    # Company name length (if provided)
    if data.company_name and len(data.company_name) > 100:
        errors.append("Company name must be 100 characters or fewer.")

    # Optionally validate API key formats (basic non-empty check)
    if data.openai_key is not None and data.openai_key.strip() == "":
        errors.append("OpenAI key, if provided, cannot be empty.")
    if data.llama_cloud_key is not None and data.llama_cloud_key.strip() == "":
        errors.append("LlamaCloud key, if provided, cannot be empty.")

    if errors:
        # Return all validation messages together so client can display guidance
        logger.warning("Registration validation errors")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors}
        )

    try:
        result = await auth_service.register(data)
        logger.info("Registration successful")
        return SignupResponse(**result)
    except ValueError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(deps.get_auth_service)
) -> Any:
    """
    JSON 登入接口
    body: {"email": "user@example.com", "password": "password"}
    """
    logger.info(f"Login attempt for email: {credentials.email}")
    try:
        result = await auth_service.authenticate(
            email=credentials.email,
            password=credentials.password
        )

        if not result:
            logger.warning(
                f"Login failed for email: {credentials.email} - Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Login successful for email: {credentials.email}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Login error for email {credentials.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )
