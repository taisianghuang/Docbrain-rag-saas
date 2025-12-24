"""Document processing scaffold."""

from app.models.processing_task import ProcessingTask


class DocumentProcessor:
    """Processes a document given a processing task."""

    async def process(self, task: ProcessingTask) -> None:
        """Process the task. To be implemented when queue backend is decided."""
        raise NotImplementedError("Processing logic will be defined in Spec2")
