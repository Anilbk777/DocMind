import uuid
from typing import Sequence
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import ChatSessionModel, ChatMessageModel
from app.utils.exceptions import RepositoryException


class ChatRepository:
    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: uuid.UUID, title: str = "New Conversation"
    ) -> ChatSessionModel:
        """Initializes a new chat session for a user."""
        try:
            session = ChatSessionModel(user_id=user_id, title=title)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except Exception as e:
            await db.rollback()
            raise RepositoryException(
                internal_detail=f"Failed to create chat session: {str(e)}"
            ) from e

    @staticmethod
    async def get_sessions_by_user(
        db: AsyncSession, user_id: uuid.UUID
    ) -> Sequence[ChatSessionModel]:
        """Retrieves all chat sessions for a user, ordered by most recent."""
        try:
            result = await db.execute(
                select(ChatSessionModel)
                .where(ChatSessionModel.user_id == user_id)
                .order_by(desc(ChatSessionModel.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch sessions for user {user_id}: {str(e)}"
            ) from e

    @staticmethod
    async def save_message(
        db: AsyncSession, session_id: uuid.UUID, role: str, content: str
    ) -> ChatMessageModel:
        """Persists a single message within a chat session."""
        try:
            message = ChatMessageModel(
                session_id=session_id, role=role, content=content
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except Exception as e:
            await db.rollback()
            raise RepositoryException(
                internal_detail=f"Failed to save chat message: {str(e)}"
            ) from e

    @staticmethod
    async def get_messages_by_session(
        db: AsyncSession, session_id: uuid.UUID, limit: int = 10, offset: int = 0
    ) -> Sequence[ChatMessageModel]:
        """Retrieves historical messages for a session with pagination support."""
        try:
            result = await db.execute(
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_id)
                .order_by(desc(ChatMessageModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            # Reverse because we want them in chronological order for the UI
            messages = list(result.scalars().all())
            messages.reverse()
            return messages
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch messages for session {session_id}: {str(e)}"
            ) from e

    @staticmethod
    async def get_session(
        db: AsyncSession, session_id: uuid.UUID
    ) -> ChatSessionModel | None:
        """Retrieves a specific chat session by ID."""
        try:
            result = await db.execute(
                select(ChatSessionModel).where(ChatSessionModel.id == session_id)
            )
            return result.scalars().first()
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch session {session_id}: {str(e)}"
            ) from e

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """Deletes a chat session and all its messages (via cascade)."""
        try:
            result = await db.execute(
                delete(ChatSessionModel).where(ChatSessionModel.id == session_id)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            raise RepositoryException(
                internal_detail=f"Failed to delete session {session_id}: {str(e)}"
            ) from e

    @staticmethod
    async def get_recent_messages(
        db: AsyncSession, session_id: uuid.UUID, limit: int = 5
    ) -> Sequence[ChatMessageModel]:
        """Retrieves the most recent messages for a session."""
        try:
            result = await db.execute(
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_id)
                .order_by(ChatMessageModel.created_at.desc())
                .limit(limit)
            )
            messages = list(result.scalars().all())
            messages.reverse()
            return messages
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch recent messages for session {session_id}: {str(e)}"
            ) from e
