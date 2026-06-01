from typing import Annotated
from fastapi import Request, Depends, HTTPException, status
from concurrent.futures import ThreadPoolExecutor
from app.services.document_service import DocumentProcessingService
from app.core.auth import oauth2_scheme, verify_access_token
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import UserModel
from sqlalchemy import select


def get_document_processing_service(request: Request) -> DocumentProcessingService:
    """Dependency to retrieve document processing service."""
    executor: ThreadPoolExecutor = request.app.state.thread_executor
    return DocumentProcessingService(executor)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserModel:
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
