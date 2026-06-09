import uuid
from typing import AsyncGenerator, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.chat_repository import ChatRepository
from app.services.rag_service import RagOrchestrationService
from app.core.models import ChatSessionModel, ChatMessageModel
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class ChatService:
    def __init__(self, chat_repo: ChatRepository, rag_service: RagOrchestrationService):
        self.repo = chat_repo
        self.rag_service = rag_service

    async def get_user_sessions(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Sequence[ChatSessionModel]:
        return await self.repo.get_sessions_by_user(db, user_id)

    async def get_session_messages(
        self, db: AsyncSession, session_id: uuid.UUID, limit: int = 10, offset: int = 0
    ) -> Sequence[ChatMessageModel]:
        return await self.repo.get_messages_by_session(db, session_id, limit, offset)

    async def handle_chat_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        session_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, AsyncGenerator[str, None]]:
        """
        Orchestrates the chat flow:
        1. Ensures a session exists.
        2. Saves the user message.
        3. Generates and yields the AI response stream.
        4. Saves the full AI response once completed.
        """
        # 1. Ensure Session
        if not session_id:
            # Create a simple title from the first 50 chars of the query
            title = query[:50] + "..." if len(query) > 50 else query
            session = await self.repo.create_session(db, user_id, title)
            session_id = session.id

        history = await self._get_chat_history(db, session_id, limit=5)

        # 2. Save User Message
        await self.repo.save_message(db, session_id, role="user", content=query)

        # 3. Get RAG Stream
        raw_stream = self.rag_service.answer_question_stream(
            question=query, user_id=user_id, history=history
        )

        # 4. Wrap stream to capture for persistence
        async def persistence_wrapper() -> AsyncGenerator[str, None]:
            full_ai_response = []
            try:
                async for chunk in raw_stream:
                    full_ai_response.append(chunk)
                    yield chunk

                ai_content = "".join(full_ai_response)
                if ai_content:
                    logger.info(
                        f"Saving AI response for session {session_id} ({len(ai_content)} chars)"
                    )
                    await self.repo.save_message(
                        db, session_id, role="ai", content=ai_content
                    )
                    logger.info("AI response saved successfully.")
                else:
                    logger.warning(
                        f"AI response empty for session {session_id}, skipping save."
                    )
            except Exception as e:
                logger.error(f"Error during AI stream/persistence: {e}")
                # Try to save whatever we have if it's substantial
                if full_ai_response:
                    try:
                        ai_content = "".join(full_ai_response)
                        await self.repo.save_message(
                            db, session_id, role="ai", content=ai_content
                        )
                        logger.info("Saved partial AI response after error.")
                    except Exception as e:
                        logger.error(f"Error saving partial AI response: {e}")
                raise e

        return session_id, persistence_wrapper()

    async def delete_session(self, db: AsyncSession, session_id: uuid.UUID) -> bool:
        return await self.repo.delete_session(db, session_id)

    async def _get_chat_history(
        self, db: AsyncSession, session_id: uuid.UUID, limit: int = 5
    ) -> list[tuple[str, str]]:
        messages = await self.repo.get_recent_messages(db, session_id, limit)
        formatted_history = []
        for msg in messages:
            role_type = "human" if msg.role == "user" else "ai"
            formatted_history.append((role_type, msg.content))
        return formatted_history
