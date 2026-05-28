from fastapi import APIRouter, File, HTTPException, UploadFile, status, Depends
from app.core.services.document_service import DocumentProcessingService
from app.utils.logging import LoggerFactory

from app.utils.exceptions import (
    UnsupportedFileTypeError,
    FileExtractionError,
    VectorStoreError,
    FileCannotBeDeleted,
)
from app.storage.factory_storage import get_storage_service
from app.api.schemas import DocumentResponse
from app.api.dependencies import get_document_processing_service

logger = LoggerFactory.get_logger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    logger.info(f"File received: {file.filename}")

    if file.size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB.",
        )

    file_bytes = await file.read()

    try:
        logger.info("Chunks creation process started")
        chunks_created = await doc_service.process_document_background(
            file.filename, file_bytes
        )
        logger.info("Chunk creation completed")

        logger.info("Storing document in storage")
        await file.seek(0)
        storage_svc = get_storage_service()
        saved_uri = await storage_svc.upload_file(file, folder="documents")
        logger.info("Document stored successfully")

        logger.info(
            f"Chunks created and document stored successfully: {chunks_created}"
        )
        return {
            "status": "Success",
            "filename": file.filename,
            "saved_path": saved_uri,
            "message": f"Successfully parsed document into {chunks_created} vector chunks.",
        }

    except UnsupportedFileTypeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid format: please select only one supported file type (.pdf, .docx, .txt)",
        )
    except FileExtractionError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not read document contents, File may be corrupted or damaged",
        )
    except VectorStoreError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write vector chunks to the database, Please try again later",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unhandled operational error occurred, Please try again later",
        )


@router.get(
    "/documents",
    status_code=status.HTTP_200_OK,
    response_model=list[DocumentResponse],
)
async def get_documents(
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    try:
        logger.info("Getting documents from storage")
        documents = await doc_service.get_documents()
        logger.info(f"Found {len(documents)} documents")
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception:
        logger.error("An error occurred while fetching documents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching documents",
        )


@router.delete(
    "/documents/{file_name}",
    status_code=status.HTTP_200_OK,
)
async def delete_file(
    file_name: str,
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    logger.info(f"API request incoming to drop document resource: '{file_name}'")

    try:
        result = await doc_service.delete_document(file_name=file_name)
        return result
    except FileCannotBeDeleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    except Exception:
        logger.error("An error occurred while deleting the file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred while processing your request.",
        )
