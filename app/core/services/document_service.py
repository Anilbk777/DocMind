# # document_service.py
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# from app.utils.logging import LoggerFactory

# from app.ingestion.ingestion_pipeline import RAGIngestionPipeline
# from app.utils.exceptions import (
#     FileExtractionError,
#     UnsupportedFileTypeError,
#     VectorStoreError,
# )

# logger = LoggerFactory.get_logger(__name__)


# class DocumentProcessingService:
#     def __init__(
#         self, ingestion_pipeline: RAGIngestionPipeline, executor: ThreadPoolExecutor
#     ):
#         """
#         Manages async background document execution windows in development.

#         :param ingestion_pipeline: The structural processing pipeline instance.
#         :param executor: A shared ThreadPoolExecutor instance to keep heavy CPU loads off the event loop.
#         """
#         self._pipeline = ingestion_pipeline
#         self._executor = executor

#     async def process_document_background(
#         self, filename: str, file_bytes: bytes
#     ) -> None:
#         """
#         Non-blocking entry point designed for FastAPI BackgroundTasks.
#         Safely shifts the heavy processing job onto an isolated worker thread.
#         """
#         logger.info(f"Background task queued for file execution pipeline: '{filename}'")
#         loop = asyncio.get_running_loop()

#         try:
#             # Shift the synchronous execution loop onto the thread pool executor
#             total_chunks = await loop.run_in_executor(
#                 self._executor, self._run_blocking_pipeline, filename, file_bytes
#             )
#             logger.info(
#                 f"Background execution complete. Indexed {total_chunks} chunks for '{filename}'"
#             )

#         except UnsupportedFileTypeError as e:
#             logger.error(f"Validation failure for '{filename}': {str(e)}")
#         except FileExtractionError as e:
#             logger.error(f"Extraction processing anomaly on '{filename}': {str(e)}")
#         except VectorStoreError as e:
#             logger.critical(f"Database writing failure for '{filename}': {str(e)}")
#         except Exception as e:
#             logger.error(
#                 f"Unexpected operational crash while processing '{filename}': {str(e)}",
#                 exc_info=True,
#             )

#     def _run_blocking_pipeline(self, filename: str, file_bytes: bytes) -> int:
#         """
#         Synchronous proxy execution worker block. Runs completely isolated within its
#         own thread assignment inside the pool framework.
#         """
#         # Call your original pipeline logic safely inside the thread boundaries
#         return self._pipeline.process_file(filename, file_bytes)

# ===========================================================================================================================


# app/services/document_service.py
import asyncio
from concurrent.futures import ProcessPoolExecutor

# Import the base pipeline exception wrappers
from app.utils.exceptions import (
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _isolated_worker_pipeline(filename: str, file_bytes: bytes) -> int:
    """
    PURE CPU WORKER: This function executes inside an isolated OS process.
    It has its own independent CPU core and memory bubble.
    """
    #  We import dependencies INSIDE the worker process to avoid serialization (pickling) bugs
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings  # Local embedding execution
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from app.ingestion.ingestion_pipeline import RAGIngestionPipeline

    # 1. EMbedding model
    logger.info("Loading local HuggingFace embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 2. Text Chunker Component
    text_chunker = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
    )

    # 3. Vector Store Component
    logger.info("Configuring development ephemeral Vector Store...")
    chroma_vector_store = Chroma(
        persist_directory="./dev_chroma_db",
        collection_name="dev_rag_collection",
        embedding_function=embedding_model,
    )

    # 4. Construct the pipeline and run the heavy compute work
    pipeline = RAGIngestionPipeline(
        text_splitter=text_chunker, vector_store=chroma_vector_store
    )

    # This runs the heavy extraction, chunking, and embedding generation
    return pipeline.process_file(filename, file_bytes)


class DocumentProcessingService:
    def __init__(self, process_executor: ProcessPoolExecutor):
        """
        Manages multiprocessing isolation layers for heavy local RAG tasks.
        """
        self._executor = process_executor

    async def process_document_background(
        self, filename: str, file_bytes: bytes
    ) -> int:
        """
        Asynchronous boundary method called by FastAPI.
        Releases the event loop instantly while the CPU maxes out elsewhere.
        """
        logger.info(f"Routing '{filename}' to an isolated ProcessPool worker core.")
        loop = asyncio.get_running_loop()

        try:
            # Shift processing completely out of the FastAPI application space
            total_chunks = await loop.run_in_executor(
                self._executor,
                _isolated_worker_pipeline,  # The pure function
                filename,
                file_bytes,
            )
            logger.info(
                f"Process worker finished successfully. Indexed {total_chunks} blocks for '{filename}'."
            )
            return total_chunks

        except (
            UnsupportedFileTypeError,
            FileExtractionError,
            VectorStoreError,
        ) as custom_err:
            logger.error(
                f"Ingestion pipeline error for '{filename}': {str(custom_err)}"
            )
            raise ValueError(str(custom_err))
        except Exception as e:
            logger.error(
                f"Unexpected process crash for '{filename}': {str(e)}", exc_info=True
            )
            raise RuntimeError(
                "An unexpected system failure occurred during document processing."
            )
