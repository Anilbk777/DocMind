import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.api.dependencies import get_document_processing_service
from app.api.schemas import UserDocumentResponse
from app.services.document_service import DocumentProcessingService
from app.services.job_tracker import job_tracker
from app.services.websocket_manager import websocket_manager
from app.utils.exceptions import FileCannotBeDeleted, DocumentRetrievalError
from app.utils.logging import LoggerFactory
from app.api.dependencies import CurrentUser

logger = LoggerFactory.get_logger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_BATCH = 5

router = APIRouter(prefix="/api/v1", tags=["RAG API"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    files: list[UploadFile] = File(...),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    user_id = current_user.id
    logger.info(f"User {user_id} uploading files")

    logger.info("Files received")
    accepted_files = files[:MAX_FILES_PER_BATCH]
    discarded_count = len(files) - len(accepted_files)
    if discarded_count > 0:
        logger.warning(
            f"Received {len(files)} files — processing first {MAX_FILES_PER_BATCH}, "
            f"discarding {discarded_count}."
        )

    batch_id = str(uuid.uuid4())
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
        job_tracker.create_job(job_id, file.filename, batch_id)
        jobs.append((job_id, file.filename, file_bytes, file.size))

    logger.info(f"Queuing {len(jobs)} file(s) for background processing.")
    background_tasks.add_task(
        doc_service.process_batch_background,
        user_id,
        batch_id,
        jobs,
    )

    return {
        "status": "Accepted",
        "batch_id": batch_id,
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
    response_model=list[UserDocumentResponse],
)
async def get_documents(
    current_user: CurrentUser,
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    try:
        logger.info("Getting documents from storage")
        documents = await doc_service.get_documents(current_user.id)
        logger.info(f"Found {len(documents)} documents")
        return documents
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
    current_user: CurrentUser,
    doc_service: DocumentProcessingService = Depends(get_document_processing_service),
):
    logger.info(f"API request incoming to drop document resource: '{file_name}'")

    try:
        result = await doc_service.delete_document(
            file_name=file_name, user_id=current_user.id
        )
        return result
    except FileCannotBeDeleted as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DocumentRetrievalError as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.error("An error occurred while deleting the file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred while processing your request.",
        )


@router.websocket("/ws/batch/{batch_id}")
async def batch_status_websocket(batch_id: str, websocket: WebSocket):

    await websocket_manager.connect(batch_id, websocket)
    batch_jobs = job_tracker.get_batch_jobs(batch_id)

    if batch_jobs:
        finished_jobs = [
            job for job in batch_jobs if job["status"] in ("completed", "failed")
        ]

        for job in finished_jobs:
            await websocket.send_json(
                {
                    "job_id": job["job_id"],
                    "filename": job["filename"],
                    "status": job["status"],
                    "chunks_created": job.get("chunks_created"),
                    "error": job.get("error"),
                }
            )

        if len(finished_jobs) == len(batch_jobs):
            websocket_manager.disconnect(batch_id)
            return

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(batch_id)
