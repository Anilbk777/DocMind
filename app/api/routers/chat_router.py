from fastapi import APIRouter, HTTPException, status, Request

from app.api.schemas import ChatRequest
from fastapi.responses import StreamingResponse
from app.core.services.rag_service import RagOrchestrationService
from app.utils.exceptions import RAGServiceException
from app.core.services.retrieval_service import RetrievalService
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _build_rag_service(request: Request, payload) -> RagOrchestrationService:
    """
    Factory kept separate so it's easy to swap in a cached/singleton
    service per provider in the future without touching the endpoint logic.
    """
    retrieval_svc = RetrievalService(vector_store=request.app.state.vector_store)
    return RagOrchestrationService(
        provider=payload.provider,
        retrieval_service=retrieval_svc,
    )


router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(payload: ChatRequest, request: Request):
    logger.info(f"Chat streaming query received: {payload.query[:30]}...")

    try:
        rag_service = _build_rag_service(request, payload)
        stream = rag_service.answer_question_stream(question=payload.query)
    except RAGServiceException as e:
        logger.warning(f"RAG service init error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception:
        logger.error("Unhandled exception building RAG service.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An unexpected error occurred while processing your request.",
        )

    return StreamingResponse(
        stream,
        media_type="text/event-stream",  # ← SSE-compatible; clients can also treat as plain text
        headers={
            "X-Accel-Buffering": "no"
        },  # ← Disables nginx/proxy buffering in production
    )
