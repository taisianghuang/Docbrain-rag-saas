from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document as DBDocument


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: str, chatbot_id: str, filename: str, file_url: str, status: str = "processing", metadata_map: dict = None) -> DBDocument:
        db_doc = DBDocument(
            tenant_id=tenant_id,
            chatbot_id=chatbot_id,
            filename=filename,
            file_url=file_url,
            status=status,
            metadata_map=metadata_map or {}
        )
        self.db.add(db_doc)
        await self.db.commit()
        await self.db.refresh(db_doc)
        return db_doc

    async def get_by_id(self, document_id: str) -> Optional[DBDocument]:
        return await self.db.get(DBDocument, document_id)

    async def update_status(self, document_id: str, status: str, metadata_map: dict = None, error_message: Optional[str] = None) -> Optional[DBDocument]:
        db_doc = await self.get_by_id(document_id)
        if not db_doc:
            return None
        db_doc.status = status
        if metadata_map is not None:
            db_doc.metadata_map = metadata_map
        if error_message is not None:
            db_doc.error_message = error_message
        await self.db.commit()
        await self.db.refresh(db_doc)
        return db_doc

    async def delete_by_id(self, document_id: str) -> None:
        db_doc = await self.get_by_id(document_id)
        if not db_doc:
            return
        await self.db.delete(db_doc)
        await self.db.commit()

    async def list_by_chatbot_id(self, chatbot_id: str) -> List[DBDocument]:
        q = await self.db.execute(select(DBDocument).where(DBDocument.chatbot_id == chatbot_id))
        return q.scalars().all()
