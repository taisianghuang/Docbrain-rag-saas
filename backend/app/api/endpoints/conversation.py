# backend/app/api/endpoints/conversation.py
from fastapi import APIRouter
from app.schemas import ChatResponse  # 確保 Schema 還在

router = APIRouter()

# TODO: 我們稍後會重寫這裡的 Chat 邏輯


@router.post("/chat")
async def chat():
    return {"message": "Chat endpoint is under construction for the new architecture"}
