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
    DocumentRetrievalError,
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

    async def process_and_store_document_background(self, job_id: str, file_name: str, file_bytes: bytes) -> None:
        """
        Orchestrates the atomic ingestion and storage of a document.
        Designed to be run as a FastAPI BackgroundTask.
        """
        from app.core.services.job_tracker import job_tracker
        logger.info(f"Starting background processing for job {job_id} ('{file_name}')")
        try:
            # Step 1: Ingest into Vector Store (heavy CPU task on ThreadPool)
            chunks_created = await self.process_document_background(file_name, file_bytes)
            logger.info(f"Successfully processed {chunks_created} chunks for '{file_name}'")

            # Step 2: Save to Local Storage
            storage_svc = get_storage_service()
            try:
                saved_path = await storage_svc.upload_file_bytes(file_name, file_bytes, folder="documents")
                logger.info(f"Successfully saved '{file_name}' to storage.")
                # Mark job as success
                job_tracker.update_job_success(job_id, saved_path, chunks_created)
            except Exception as storage_err:
                logger.error(f"Failed to save '{file_name}' to storage: {storage_err}. Rolling back vector store...")
                # Rollback vector store insertion since disk storage failed
                await self.delete_document(file_name)
                raise storage_err

        except Exception as e:
            logger.error(f"Background processing failed for job {job_id} ('{file_name}'): {str(e)}")
            job_tracker.update_job_error(job_id, str(e))

    def _run_blocking_pipeline(self, filename: str, file_bytes: bytes) -> int:
        """
        Synchronous proxy execution worker block running inside a thread assignment.
        """
        return self._ingestion_pipeline.process_file(filename, file_bytes)

    async def get_documents(self):
        storage_svc = get_storage_service()
        try:
            documents = await storage_svc.get_documents()
            return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            raise DocumentRetrievalError(f"Failed to retrieve documents: {str(e)}")

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
