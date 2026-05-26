from fastapi import APIRouter, File, HTTPException, UploadFile, status, Request
from app.core.services.document_service import DocumentProcessingService
from app.utils.logging import LoggerFactory

from app.utils.exceptions import (
    UnsupportedFileTypeError,
    FileExtractionError,
    VectorStoreError,
    FileCannotBeDeleted,
)
from app.ingestion.ingestion_pipeline import RAGIngestionPipeline
from app.storage.factory_storage import get_storage_service
from app.api.schemas import DocumentResponse

logger = LoggerFactory.get_logger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):
    logger.info(f"File received: {file.filename}")

    if file.size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB.",
        )

    file_bytes = await file.read()

    pipeline = RAGIngestionPipeline(vector_store=request.app.state.vector_store)

    doc_service = DocumentProcessingService(
        ingestion_pipeline=pipeline, executor=request.app.state.thread_executor
    )

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

    except UnsupportedFileTypeError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid format: {str(val_err)}",
        )
    except FileExtractionError as ext_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read document contents: {str(ext_err)}",
        )
    except VectorStoreError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database ingestion subsystem failed: {str(db_err)}",
        )
    except Exception as sys_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled operational error occurred: {str(sys_err)}",
        )


@router.get(
    "/documents",
    status_code=status.HTTP_200_OK,
    response_model=list[DocumentResponse],
)
async def get_documents():
    try:
        logger.info("Getting documents from storage")
        storage_svc = get_storage_service()
        documents = await storage_svc.get_documents()
        logger.info(f"Found {len(documents)} documents")
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        logger.error(f"An error occurred while fetching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching documents: {str(e)}",
        )


@router.delete(
    "/documents/{file_name}",
    status_code=status.HTTP_200_OK,
)
async def delete_file(file_name: str, request: Request):
    logger.info(f"API request incoming to drop document resource: '{file_name}'")
    pipeline = RAGIngestionPipeline(vector_store=request.app.state.vector_store)

    doc_service = DocumentProcessingService(
        ingestion_pipeline=pipeline, executor=request.app.state.thread_executor
    )

    try:
        result = await doc_service.delete_document(
            file_name=file_name, vector_store=request.app.state.vector_store
        )

        return result
    except FileCannotBeDeleted as f_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(f_err))
    except Exception as e:
        logger.error(f"Global structural failure inside deletion router: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred while processing your request.",
        )
