# backend/app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
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
