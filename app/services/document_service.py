from app.core.models import DocumentModel
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# from langchain_chroma import Chroma
from concurrent.futures import ThreadPoolExecutor
import uuid
from sqlalchemy import select, delete
from app.services.job_tracker import job_tracker
from app.services.websocket_manager import websocket_manager
from app.ingestion.ingestion_pipeline import RAGIngestionPipeline
from app.ingestion.rag_components import VectorStore
from app.storage.factory_storage import get_storage_service
from app.utils.exceptions import (
    DocumentRetrievalError,
    FileCannotBeDeleted,
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DocumentProcessingService:
    def __init__(self, executor: ThreadPoolExecutor, db: AsyncSession):
        """
        Manages async background document execution windows in development.

        :param executor: A shared ThreadPoolExecutor instance to keep heavy CPU loads off the event loop.
        """
        self._ingestion_pipeline = RAGIngestionPipeline()
        self.db = db
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
                self._executor,
                self._ingestion_pipeline.process_file,
                filename,
                file_bytes,
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

    async def process_and_store_document_background(
        self,
        user_id: uuid.UUID,
        job_id: str,
        file_name: str,
        file_bytes: bytes,
        file_size: int,
    ) -> None:
        """
        Orchestrates the atomic ingestion and storage of a document.
        Designed to be run as a FastAPI BackgroundTask.
        """

        logger.info(f"Starting background processing for job {job_id} ('{file_name}')")
        try:
            # Step 1: Ingest into Vector Store (heavy CPU task on ThreadPool)
            chunks_created = await self.process_document_background(
                file_name, file_bytes
            )
            logger.info(
                f"Successfully processed {chunks_created} chunks for '{file_name}'"
            )

            # Step 2: Save to Local Storage
            storage_svc = get_storage_service()
            try:
                saved_path = await storage_svc.upload_file_bytes(
                    file_name, file_bytes, folder="documents"
                )
                logger.info(f"Successfully saved '{file_name}' to storage.")

                document = DocumentModel(
                    user_id=user_id,
                    file_name=file_name,
                    storage_uri=saved_path,
                    file_size=file_size,
                )
                self.db.add(document)
                await self.db.commit()
                logger.info(f"Saved document metadata to database for '{file_name}'")
                # Mark job as success
                job_tracker.update_job_success(job_id, saved_path, chunks_created)
            except Exception as storage_err:
                logger.error(
                    f"Failed to save '{file_name}' to storage: {storage_err}. Rolling back vector store..."
                )
                # Rollback vector store insertion since disk storage failed
                await self.delete_document(file_name)
                await self.db.rollback()
                job_tracker.update_job_error(job_id, str(storage_err))
                raise storage_err

        except Exception as e:
            logger.error(
                f"Background processing failed for job {job_id} ('{file_name}'): {str(e)}"
            )
            job_tracker.update_job_error(job_id, str(e))

    async def process_batch_background(
        self,
        user_id: uuid.UUID,
        batch_id: str,
        jobs: list[tuple[str, str, bytes]],
    ) -> None:
        """
        Orchestrates the atomic ingestion and storage of a batch of documents.
        Designed to be run as a FastAPI BackgroundTask.
        """
        logger.info(f"Batch processing started for {len(jobs)} file(s).")
        total_jobs = len(jobs)
        completed_count = 0

        semaphore = asyncio.Semaphore(2)

        async def throttled_worker(job_id, filename, file_bytes, file_size):
            nonlocal completed_count
            async with semaphore:
                # This calls your underlying thread-pool offloaded method
                await self.process_and_store_document_background(
                    user_id,
                    job_id,
                    filename,
                    file_bytes,
                    file_size,
                )

                job = job_tracker.get_job(job_id)
                completed_count += 1
                is_last = completed_count == total_jobs
                if job and job["status"] == "completed":
                    await websocket_manager.notify(
                        batch_id,
                        {
                            "job_id": job_id,
                            "filename": filename,
                            "status": "completed",
                            "chunks_created": job.get("chunks_created"),
                        },
                        close=is_last,
                    )
                else:
                    await websocket_manager.notify(
                        batch_id,
                        {
                            "job_id": job_id,
                            "filename": filename,
                            "status": "failed",
                            "error": job.get("error") if job else "Unknown error",
                        },
                        close=is_last,
                    )

        # 1.list of raw coroutines
        coroutines = [
            throttled_worker(job_id, filename, file_bytes, file_size)
            for job_id, filename, file_bytes, file_size in jobs
        ]

        # 2. Gather them safely. It automatically converts coroutines to tasks.
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # 3. Process results
        for (job_id, filename, _), result in zip(jobs, results):
            if isinstance(result, BaseException):
                logger.error(f"Batch job {job_id} ('{filename}') failed: {result}")
            else:
                logger.info(
                    f"Batch job {job_id} ('{filename}') completed successfully."
                )
        logger.info("Batch processing complete.")

    async def get_documents(self, user_id: uuid.UUID) -> list[DocumentModel]:
        try:
            result = await self.db.execute(
                select(DocumentModel)
                .where(DocumentModel.user_id == user_id)
                .order_by(DocumentModel.created_at.desc())
            )
            documents = result.scalars().all()
            return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            raise DocumentRetrievalError(f"Failed to retrieve documents: {str(e)}")

    async def delete_document(self, file_name: str, user_id: uuid.UUID):
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
            try:
                await self.db.execute(
                    delete(DocumentModel)
                    .where(DocumentModel.file_name == file_name)
                    .where(DocumentModel.user_id == user_id)
                )
                await self.db.commit()
                logger.info(
                    f"Deleted document metadata for '{file_name}' from database."
                )
            except Exception as db_del_err:
                logger.error(
                    f"Failed to delete document metadata from database for '{file_name}': {str(db_del_err)}"
                )
                raise FileCannotBeDeleted(
                    "Failed to delete document metadata from database."
                ) from db_del_err
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
