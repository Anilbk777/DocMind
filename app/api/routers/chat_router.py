from app.api.dependencies import CurrentUser, get_chat_service, get_db
from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.schemas import ChatRequest, ChatSessionResponse, ChatMessageResponse
from fastapi.responses import StreamingResponse
from app.services.chat_service import ChatService
from app.utils.logging import LoggerFactory
from app.utils.exceptions import AuthenticationException
from app.utils.exceptions import RepositoryException

logger = LoggerFactory.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Retrieves all chat sessions for the current user."""
    return await chat_service.get_user_sessions(db, current_user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Retrieves paginated messages for a specific session."""
    # Security check: Ensure session belongs to user
    session = await chat_service.repo.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise AuthenticationException(internal_detail="Unauthorized access to chat session.")
    
    return await chat_service.get_session_messages(db, session_id, limit, offset)


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(
    payload: ChatRequest, 
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Handles streaming chat with RAG. 
    Persists query and AI response to the database within a session.
    """
    logger.info(f"Chat request received from user {current_user.id}")

    session_id, stream_generator = await chat_service.handle_chat_session(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        session_id=payload.session_id
    )

    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "X-Chat-Session-ID": str(session_id) # Inform client of the session ID used
        },
    )
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Deletes a specific chat session."""
    # Security check: Ensure session belongs to user
    session = await chat_service.repo.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise AuthenticationException(internal_detail="Unauthorized access to chat session.")
    
    deleted = await chat_service.delete_session(db, session_id)
    if not deleted:
        raise RepositoryException(internal_detail="Session not found or already deleted.")
    
    return
