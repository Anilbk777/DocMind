from fastapi import APIRouter, File, HTTPException, UploadFile, status, Request

from app.core.services.document_service import DocumentProcessingService
from app.core.services.retrieval_service import RetrievalService
from app.utils.logging import LoggerFactory
from app.api.schemas import ChatRequest, ChatResponse
from app.core.services.rag_service import RagOrchestrationService
from app.utils.exceptions import RAGServiceException
from concurrent.futures import ProcessPoolExecutor

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

    # Lazily initialize the process pool on the first upload request.
    # This avoids spawning worker processes at server startup (slow on Windows).
    if request.app.state.process_pool is None:
        worker_cores = request.app.state.worker_cores
        logger.info(
            f"First upload received — spawning ProcessPoolExecutor with {worker_cores} worker cores..."
        )
        request.app.state.process_pool = ProcessPoolExecutor(max_workers=worker_cores)

    process_pool = request.app.state.process_pool
    doc_service = DocumentProcessingService(process_executor=process_pool)

    try:
        # Await the processing job directly.
        # The connection remains open so the user gets instant feedback if it passes or fails.
        chunks_created = await doc_service.process_document_background(
            file.filename, file_bytes
        )
        logger.info(f"Chunks created: {chunks_created}")

        return {
            "status": "Success",
            "filename": file.filename,
            "message": f"Successfully parsed document into {chunks_created} vector chunks.",
        }

    except ValueError as val_err:
        logger.error(
            f"Validation error for '{file.filename}': {str(val_err)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err)
        )
    except Exception as sys_err:
        logger.error(
            f"Unexpected pipeline crash for '{file.filename}': {str(sys_err)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(sys_err)
        )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(payload: ChatRequest, request: Request):
    logger.info(f"Chat query received: {payload.query[:30]}...")
    try:
        retrieval_svc = RetrievalService(
            vector_store=request.app.state.vector_store
        )
        rag_service = RagOrchestrationService(
            provider=payload.provider,
            retrieval_service=retrieval_svc,
        )

        answer = await rag_service.answer_question(question=payload.query)
        return ChatResponse(answer=answer)

    except RAGServiceException as e:
        logger.warning(f"RAG service error on chat query: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unhandled exception in /chat endpoint: {str(e)}",
            exc_info=True,  # logs full stack trace so you can see the real error
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
