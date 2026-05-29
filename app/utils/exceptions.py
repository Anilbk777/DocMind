class RAGPipelineException(Exception):
    """Base exception for all RAG pipeline anomalies."""

    pass


class FileExtractionError(RAGPipelineException):
    """Raised when text cannot be extracted from a specific document file."""

    pass


class UnsupportedFileTypeError(RAGPipelineException):
    """Raised when an unmapped or dangerous extension is routed to the pipeline."""

    pass


class VectorStoreError(RAGPipelineException):
    """Raised when embedding generation or database insertion fails."""

    pass


class RAGServiceException(Exception):
    """Custom wrapper exception for pipeline processing bugs."""

    pass

class FileCannotBeDeleted(Exception):
    pass

class DocumentRetrievalError(Exception):
    pass