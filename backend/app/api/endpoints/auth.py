# backend/app/api/endpoints/auth.py
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api import deps
from app.schemas import SignupRequest, SignupResponse, Token
from app.schemas import SignupRequest, SignupResponse
from app.services.auth import AuthService

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
    logger.info(f"Register attempt for email: {data.email}")
    try:
        result = await auth_service.register(data)
        logger.info(
            f"Registration successful for email: {data.email}, account_id: {result['account_id']}, tenant_id: {result['tenant_id']}")
        return SignupResponse(**result)
    except ValueError as e:
        logger.warning(
            f"Registration validation error for email {data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Registration error for email {data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(deps.get_auth_service)
) -> Any:
    """
    OAuth2 相容登入接口
    username: 請填入 email
    password: 密碼
    """
    # 注意: OAuth2 spec 規定欄位名稱是 username，但我們邏輯是傳 email
    logger.info(f"Login attempt for email: {form_data.username}")
    try:
        result = await auth_service.authenticate(
            email=form_data.username,
            password=form_data.password
        )

        if not result:
            logger.warning(
                f"Login failed for email: {form_data.username} - Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Login successful for email: {form_data.username}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Login error for email {form_data.username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )
