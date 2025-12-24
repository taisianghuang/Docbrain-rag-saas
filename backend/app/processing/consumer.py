"""Queue consumer scaffold for processing tasks."""

import logging
from typing import Callable, Awaitable, Optional

from app.repositories.processing_task import ProcessingTaskRepository
from app.models.processing_task import ProcessingTask
from app.adapters.base import QueueAdapter

logger = logging.getLogger(__name__)


class ProcessingConsumer:
    """Consumes processing tasks from the queue and dispatches to a processor."""

    def __init__(
        self,
        task_repo: ProcessingTaskRepository,
        queue_adapter: QueueAdapter,
        processor: Callable[[ProcessingTask], Awaitable[None]],
    ) -> None:
        self.task_repo = task_repo
        self.queue_adapter = queue_adapter
        self.processor = processor

    async def consume_once(self) -> Optional[ProcessingTask]:
        """Pull one task from the queue and process it (implemented in Spec2)."""
        raise NotImplementedError(
            "Queue consumer will be implemented in Spec2")
