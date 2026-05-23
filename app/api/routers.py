from fastapi import APIRouter, File, HTTPException, UploadFile, status, Request
from app.core.services.document_service import DocumentProcessingService
from app.core.services.retrieval_service import RetrievalService
from app.utils.logging import LoggerFactory
from app.api.schemas import ChatRequest, ChatResponse

from app.core.services.rag_service import RagOrchestrationService
from app.utils.exceptions import RAGServiceException
from app.utils.exceptions import (
    UnsupportedFileTypeError,
    FileExtractionError,
    VectorStoreError,
)
from app.ingestion.ingestion_pipeline import RAGIngestionPipeline

logger = LoggerFactory.get_logger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):
    logger.info(f"File received: {file.filename}")

    if file.size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB.",
        )

    file_bytes = await file.read()

    # 1. Pull shared resources straight out of FastAPI's app state
    shared_executor = request.app.state.thread_executor
    vector_store = request.app.state.vector_store

    # 2. Safely initialize your ingestion components under a shared process loop
    # Pass your pre-warmed vector store to the pipeline if required by its constructor
    pipeline = RAGIngestionPipeline(vector_store=vector_store)

    doc_service = DocumentProcessingService(
        ingestion_pipeline=pipeline, executor=shared_executor
    )

    try:
        # 3. Process the file and await execution safely
        chunks_created = await doc_service.process_document_background(
            file.filename, file_bytes
        )
        logger.info(f"Chunks created successfully: {chunks_created}")

        return {
            "status": "Success",
            "filename": file.filename,
            "message": f"Successfully parsed document into {chunks_created} vector chunks.",
        }

    except UnsupportedFileTypeError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid format: {str(val_err)}",
        )
    except FileExtractionError as ext_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read document contents: {str(ext_err)}",
        )
    except VectorStoreError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database ingestion subsystem failed: {str(db_err)}",
        )
    except Exception as sys_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled operational error occurred: {str(sys_err)}",
        )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(payload: ChatRequest, request: Request):
    logger.info(f"Chat query received: {payload.query[:30]}...")
    try:
        # 1. Initialize retrieval service with the pre-warmed single-process vector store
        retrieval_svc = RetrievalService(vector_store=request.app.state.vector_store)

        logger.info(f"Provider: {payload.provider}")
        rag_service = RagOrchestrationService(
            provider=payload.provider,
            retrieval_service=retrieval_svc,
        )

        answer = await rag_service.answer_question(question=payload.query)
        return ChatResponse(answer=answer)

    except RAGServiceException as e:
        logger.warning(f"RAG service error on chat query: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unhandled exception in /chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An unexpected error occurred while processing your request.",
        )
