import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)



class AppBaseException(Exception):
    def __init__(self, user_message: str, internal_detail: str, status_code: int = 500):
        self.user_message = user_message  # shown to API consumer
        self.internal_detail = internal_detail  # only logged internally
        self.status_code = status_code
        super().__init__(internal_detail or user_message)


class RepositoryException(AppBaseException):
    """Raised when database/repository operations fail."""

    def __init__(self, internal_detail: str, status_code: int = 500):
        super().__init__(
            user_message="A data access error occurred. Please try again later.",
            internal_detail=internal_detail,
            status_code=status_code,
        )


class ServiceException(AppBaseException):
    """Raised when business logic fails unexpectedly."""

    def __init__(self, internal_detail: str, status_code: int = 500):
        super().__init__(
            user_message="An internal error occurred while processing your request.",
            internal_detail=internal_detail,
            status_code=status_code,
        )


class RAGPipelineException(AppBaseException):
    def __init__(
        self,
        internal_detail: str,
        status_code: int = 500,
        user_message: str = "An internal error occurred while processing your request.",
    ):
        super().__init__(
            user_message=user_message,
            internal_detail=internal_detail,
            status_code=status_code,
        )


class AuthenticationException(AppBaseException):
    def __init__(self, internal_detail: str):
        super().__init__(
            user_message="Authentication failed. Please check your credentials.",
            internal_detail=internal_detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class FileExtractionError(RAGPipelineException):
    """Raised when text cannot be extracted from a specific document file."""

    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
        )


class UnsupportedFileTypeError(RAGPipelineException):
    """Raised when an unmapped or dangerous extension is routed to the pipeline."""

    def __init__(self, extension: str, internal_detail: str):
        super().__init__(
            user_message=f"Unsupported type: {extension}, file must be (.pdf, .docx, or .txt)",
            internal_detail=internal_detail,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class VectorStoreError(RAGPipelineException):
    """Raised when embedding generation or database insertion fails."""
    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
        )


class RAGServiceException(ServiceException):
    """Custom wrapper exception for pipeline processing bugs."""
    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
        )


class FileCannotBeDeleted(ServiceException):
    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DocumentRetrievalError(RepositoryException):
    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationException(AppBaseException):
    def __init__(self, user_message: str, internal_detail: str):
        super().__init__(
            user_message=user_message,
            internal_detail=internal_detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class StorageError(ServiceException):
    def __init__(self, internal_detail: str):
        super().__init__(
            internal_detail=internal_detail,
        )


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AppBaseException)
    async def handle_app_exception(request: Request, exc: AppBaseException):
        """
        Catches all your custom exceptions.
        Logs the internal detail to terminal, sends only the safe message outward.
        """
        logger.error(
            f"[{exc.__class__.__name__}] {exc.internal_detail}\n"
            f"Path: {request.url.path}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # Only the user_message goes into the response — never internal_detail
        return JSONResponse(
            status_code=exc.status_code, content={"error": exc.user_message}
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        """
        Safety net for ANY exception you didn't anticipate.
        Logs everything, but sends a completely generic message to the client.
        """
        logger.critical(
            f"[UnhandledException] {str(exc)}\n"
            f"Path: {request.url.path}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred. Please wait for while and try again."
            },
        )

