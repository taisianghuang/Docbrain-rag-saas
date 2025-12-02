from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.client import Client


async def get_client(db: AsyncSession, client_id: str) -> Optional[Client]:
    q = select(Client).where(Client.id == client_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    return row


async def create_client(db: AsyncSession, name: str, api_key: str | None = None) -> Client:
    client = Client(name=name, api_key=api_key)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


__all__ = ["get_client", "create_client"]
