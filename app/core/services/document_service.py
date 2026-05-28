import asyncio

# from langchain_chroma import Chroma
from concurrent.futures import ThreadPoolExecutor
from app.utils.logging import LoggerFactory
from app.ingestion.rag_components import VectorStore
from app.ingestion.ingestion_pipeline import RAGIngestionPipeline
from app.utils.exceptions import (
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
    FileCannotBeDeleted,
)
from app.storage.factory_storage import get_storage_service

logger = LoggerFactory.get_logger(__name__)


class DocumentProcessingService:
    def __init__(self, executor: ThreadPoolExecutor):
        """
        Manages async background document execution windows in development.

        :param executor: A shared ThreadPoolExecutor instance to keep heavy CPU loads off the event loop.
        """
        self._ingestion_pipeline = RAGIngestionPipeline()
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
        return self._ingestion_pipeline.process_file(filename, file_bytes)

    async def get_documents(self):
        storage_svc = get_storage_service()
        documents = await storage_svc.get_documents()
        return documents

    async def delete_document(self, file_name: str):
        logger.info(f"Initiating the deletion of file: '{file_name}'")
        chroma_deleted = False
        disk_deleted = False
        vector_store = VectorStore.get_vector_store()

        try:
            await asyncio.to_thread(vector_store.delete, where={"source": file_name})
            chroma_deleted = True
            logger.info(
                f"Vector embeddings matching source '{file_name}' dropped from ChromaDB."
            )
        except Exception as db_err:
            logger.error(
                f"Vector store database purge failed for '{file_name}': {str(db_err)}"
            )
            raise FileCannotBeDeleted("Vector store database purge failed.") from db_err

        try:
            storage_svc = get_storage_service()
            disk_deleted = await storage_svc.delete_file(file_name)
        except Exception as disk_err:
            logger.error(
                f"Physical disk purge failed for '{file_name}': {str(disk_err)}"
            )
            raise FileCannotBeDeleted("Physical disk purge failed") from disk_err

        if not chroma_deleted or not disk_deleted:
            raise FileCannotBeDeleted(
                f"Could not drop asset references for '{file_name}' ."
            )

        return {"chroma_purged": chroma_deleted, "disk_removed": disk_deleted}
