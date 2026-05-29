from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
    Depends,
    BackgroundTasks,
)
import uuid
from app.core.services.job_tracker import job_tracker
from app.core.services.document_service import DocumentProcessingService
from app.utils.logging import LoggerFactory
from app.utils.exceptions import FileCannotBeDeleted
from app.api.schemas import DocumentResponse
from app.api.dependencies import get_document_processing_service

logger = LoggerFactory.get_logger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_BATCH = 5

router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    logger.info("Files received")
    accepted_files = files[:MAX_FILES_PER_BATCH]
    discarded_count = len(files) - len(accepted_files)
    if discarded_count > 0:
        logger.warning(
            f"Received {len(files)} files — processing first {MAX_FILES_PER_BATCH}, "
            f"discarding {discarded_count}."
        )

    jobs = []
    for file in accepted_files:
        if file.size > MAX_FILE_SIZE:
            logger.error(f"File too large: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB.",
            )

        file_bytes = await file.read()

        job_id = str(uuid.uuid4())
        job_tracker.create_job(job_id, file.filename)
        jobs.append((job_id, file.filename, file_bytes))

    logger.info(f"Queuing {len(jobs)} file(s) for background processing.")
    background_tasks.add_task(
        doc_service.process_batch_background,
        jobs,
    )

    return {
        "status": "Accepted",
        "message": f"{len(jobs)} document(s) accepted and queued for processing.",
        "accepted": len(jobs),
        "discarded": discarded_count,
        "jobs": [
            {"job_id": job_id, "filename": filename} for job_id, filename, _ in jobs
        ],
    }


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


@router.get("/jobs", status_code=status.HTTP_200_OK)
async def get_all_jobs():
    """Returns all background jobs."""
    return job_tracker.get_all_jobs()


@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_job_status(job_id: str):
    """Returns the status of a specific background job."""
    job = job_tracker.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    return job
