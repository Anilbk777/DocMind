from fastapi import Request
from concurrent.futures import ThreadPoolExecutor
from app.services.document_service import DocumentProcessingService


def get_document_processing_service(request: Request) -> DocumentProcessingService:
    """Dependency to retrieve document processing service."""
    executor: ThreadPoolExecutor = request.app.state.thread_executor
    return DocumentProcessingService(executor)