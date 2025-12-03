from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.api import deps

router = APIRouter()


@router.get("/")
async def health(db: AsyncSession = Depends(deps.get_db)) -> Dict[str, str]:
    """
    Health check endpoint.
    用於檢查後端與資料庫連線是否正常 (K8s/Docker 會用到這個)
    """
    try:
        # 執行一個簡單的 SQL 查詢來確保 DB 活著
        await db.execute(text("SELECT 1"))
        return {"status": "alive"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
