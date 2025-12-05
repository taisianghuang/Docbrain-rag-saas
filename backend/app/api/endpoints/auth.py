# backend/app/api/endpoints/auth.py
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api import deps
from app.schemas import SignupRequest, SignupResponse, Token
from app.schemas import SignupRequest, SignupResponse
from app.services.auth import AuthService

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
    try:
        result = await auth_service.register(data)
        return SignupResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Register Error: {e}")
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
    result = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result
