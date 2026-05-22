import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.utils.logging import LoggerFactory

from app.ingestion.ingestion_pipeline import RAGIngestionPipeline
from app.utils.exceptions import (
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
)

logger = LoggerFactory.get_logger(__name__)


class DocumentProcessingService:
    def __init__(
        self, ingestion_pipeline: RAGIngestionPipeline, executor: ThreadPoolExecutor
    ):
        """
        Manages async background document execution windows in development.

        :param ingestion_pipeline: The structural processing pipeline instance.
        :param executor: A shared ThreadPoolExecutor instance to keep heavy CPU loads off the event loop.
        """
        self._pipeline = ingestion_pipeline
        self._executor = executor

    async def process_document_background(
        self, filename: str, file_bytes: bytes
    ) -> int:
        """
        Runs document execution safely inside an isolated worker thread.
        Propagates exceptions up to caller for clean API exception handling.
        """
        logger.info(f"Queuing file execution pipeline inside thread pool: '{filename}'")
        loop = asyncio.get_running_loop()

        try:
            # Shift the synchronous execution loop onto the thread pool executor
            total_chunks = await loop.run_in_executor(
                self._executor, self._run_blocking_pipeline, filename, file_bytes
            )
            logger.info(
                f"Thread execution complete. Indexed {total_chunks} chunks for '{filename}'"
            )
            return total_chunks

        except UnsupportedFileTypeError as e:
            logger.error(f"Validation failure for '{filename}': {str(e)}")
            raise
        except FileExtractionError as e:
            logger.error(f"Extraction processing anomaly on '{filename}': {str(e)}")
            raise
        except VectorStoreError as e:
            logger.critical(f"Database writing failure for '{filename}': {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected operational crash while processing '{filename}': {str(e)}",
                exc_info=True,
            )
            raise

    def _run_blocking_pipeline(self, filename: str, file_bytes: bytes) -> int:
        """
        Synchronous proxy execution worker block running inside a thread assignment.
        """
        return self._pipeline.process_file(filename, file_bytes)