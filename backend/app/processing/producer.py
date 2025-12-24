"""Queue producer scaffold for processing tasks."""

import logging
from typing import Optional

from app.adapters.base import QueueAdapter
from app.repositories.processing_task import ProcessingTaskRepository
from app.models.processing_task import ProcessingTask

logger = logging.getLogger(__name__)


class ProcessingProducer:
    """Creates processing tasks and publishes to the queue (if provided)."""

    def __init__(
        self,
        task_repo: ProcessingTaskRepository,
        queue_adapter: Optional[QueueAdapter] = None,
    ) -> None:
        self.task_repo = task_repo
        self.queue_adapter = queue_adapter

    async def enqueue_document(
        self,
        chatbot_id: str,
        document_id: Optional[str] = None,
        payload: Optional[dict] = None,
        priority: int = 5,
    ) -> ProcessingTask:
        """Persist task and enqueue message if adapter exists."""
        task = await self.task_repo.create_task(
            chatbot_id=chatbot_id,
            document_id=document_id,
            priority=priority,
            payload=payload,
        )

        if self.queue_adapter:
            await self.queue_adapter.enqueue(
                task_type="document_ingestion",
                payload={"task_id": str(task.id), **(payload or {})},
                priority=priority,
            )
        else:
            logger.info(
                "Queue adapter not configured; task persisted with status=queued")

        return task
