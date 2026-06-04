import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import DocumentModel

class DocumentRepository:
    @staticmethod
    async def save(db:AsyncSession, document:DocumentModel)->DocumentModel:
        """Persists a new document metadata record."""
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @staticmethod
    async def get_all_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[DocumentModel]:
        """Retrieves all document records for a given user ordered by creation date."""
        result = await db.execute(
            select(DocumentModel)
            .where(DocumentModel.user_id == user_id)
            .order_by(DocumentModel.created_at.desc())
        )
        return list(result.scalars().all())
        
    @staticmethod
    async def get_by_filename(db: AsyncSession, file_name: str, user_id: uuid.UUID) -> DocumentModel | None:
        """Finds a specific document by its unique combinations of filename and owner."""
        result = await db.execute(
            select(DocumentModel).where(
                DocumentModel.file_name == file_name, 
                DocumentModel.user_id == user_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def delete_by_id(db: AsyncSession, document_id: uuid.UUID) -> None:
        """Deletes a document record explicitly matching its primary ID index."""
        await db.execute(
            delete(DocumentModel).where(DocumentModel.id == document_id)
        )
        await db.commit()
    
