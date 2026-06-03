from typing import Annotated
from fastapi import Request, Depends, HTTPException, status
from app.services.document_service import DocumentProcessingService
from app.core.auth import oauth2_scheme, verify_access_token
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import UserModel
from sqlalchemy import select
from concurrent.futures import ThreadPoolExecutor
from app.services.job_tracker import JobTracker


async def get_job_tracker():
    return JobTracker()


JobTrackerDep = Annotated[JobTracker, Depends(get_job_tracker)]


async def get_document_processing_service(
    request: Request, db=Depends(get_db), job_tracker: JobTracker = JobTrackerDep
) -> DocumentProcessingService:
    """Dependency to retrieve document processing service."""
    executor: ThreadPoolExecutor = request.app.state.thread_executor
    return DocumentProcessingService(executor, db, job_tracker)


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
