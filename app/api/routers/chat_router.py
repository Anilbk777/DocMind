from app.api.dependencies import CurrentUser
from fastapi import APIRouter, status

from app.api.schemas import ChatRequest
from fastapi.responses import StreamingResponse
from app.services.rag_service import RagOrchestrationService
from app.services.retrieval_service import RetrievalService
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _build_rag_service(payload) -> RagOrchestrationService:
    """
    Factory kept separate so it's easy to swap in a cached/singleton
    service per provider in the future without touching the endpoint logic.
    """
    retrieval_svc = RetrievalService()
    return RagOrchestrationService(
        provider=payload.provider, retrieval_service=retrieval_svc
    )


router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(payload: ChatRequest, current_user: CurrentUser):
    logger.info(f"Chat streaming query received: {payload.query[:30]}...")

    rag_service = _build_rag_service(payload)
    stream = rag_service.answer_question_stream(
        question=payload.query, user_id=current_user.id
    )

    return StreamingResponse(
        stream,
        media_type="text/event-stream",  # ← SSE-compatible; clients can also treat as plain text
        headers={
            "X-Accel-Buffering": "no"
        },  # ← Disables nginx/proxy buffering in production
    )
