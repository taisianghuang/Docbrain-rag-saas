"""Repository for ProcessingTask persistence."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_task import ProcessingTask


class ProcessingTaskRepository:
    """Provides CRUD operations for processing tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        chatbot_id: str,
        document_id: Optional[str] = None,
        priority: int = 5,
        payload: Optional[dict] = None,
    ) -> ProcessingTask:
        task = ProcessingTask(
            chatbot_id=UUID(str(chatbot_id)),
            document_id=UUID(str(document_id)) if document_id else None,
            priority=priority,
            payload=payload or {},
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        document_id: Optional[str] = None,
    ) -> Optional[ProcessingTask]:
        stmt = (
            update(ProcessingTask)
            .where(ProcessingTask.id == UUID(str(task_id)))
            .values(status=status, error_message=error_message)
            .returning(ProcessingTask)
        )
        if retry_count is not None:
            stmt = stmt.values(retry_count=retry_count)
        if document_id is not None:
            stmt = stmt.values(document_id=UUID(str(document_id)))

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def get(self, task_id: str) -> Optional[ProcessingTask]:
        stmt = select(ProcessingTask).where(
            ProcessingTask.id == UUID(str(task_id))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_chatbot(
        self, chatbot_id: str, limit: int = 50
    ) -> List[ProcessingTask]:
        stmt = (
            select(ProcessingTask)
            .where(ProcessingTask.chatbot_id == UUID(str(chatbot_id)))
            .order_by(ProcessingTask.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
