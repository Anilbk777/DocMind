import uuid
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import DocumentModel
from app.utils.exceptions import RepositoryException


class DocumentRepository:
    @staticmethod
    async def save(db: AsyncSession, document: DocumentModel) -> DocumentModel:
        """Persists a new document metadata record."""
        try:
            db.add(document)
            await db.commit()
            await db.refresh(document)
            return document
        except Exception as e:
            await db.rollback()
            raise RepositoryException(
                internal_detail=f"Failed to save document metadata: {str(e)}"
            ) from e

    @staticmethod
    async def get_all_by_user(
        db: AsyncSession, user_id: uuid.UUID
    ) -> list[DocumentModel]:
        """Retrieves all document records for a given user ordered by creation date."""
        try:
            result = await db.execute(
                select(DocumentModel)
                .where(DocumentModel.user_id == user_id)
                .order_by(DocumentModel.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch documents for user {user_id}: {str(e)}"
            ) from e

    @staticmethod
    async def get_by_filename(
        db: AsyncSession, file_name: str, user_id: uuid.UUID
    ) -> DocumentModel | None:
        """Finds a specific document by its unique combinations of filename and owner."""
        try:
            result = await db.execute(
                select(DocumentModel).where(
                    DocumentModel.file_name == file_name,
                    DocumentModel.user_id == user_id,
                )
            )
            return result.scalars().first()
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to fetch document '{file_name}' for user {user_id}: {str(e)}"
            ) from e

    @staticmethod
    async def delete_by_id(db: AsyncSession, document_id: uuid.UUID) -> None:
        """Deletes a document record explicitly matching its primary ID index."""
        try:
            await db.execute(
                delete(DocumentModel).where(DocumentModel.id == document_id)
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise RepositoryException(
                internal_detail=f"Failed to delete document record {document_id}: {str(e)}"
            ) from e

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Counts the number of documents for a specific user."""
        try:
            stmt = (
                select(func.count())
                .select_from(DocumentModel)
                .where(DocumentModel.user_id == user_id)
            )
            result = await db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RepositoryException(
                internal_detail=f"Failed to count documents for user {user_id}: {str(e)}"
            ) from e
