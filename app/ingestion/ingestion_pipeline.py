# pipeline_service.py
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

from app.ingestion.file_extractor import EXTRACTOR_REGISTRY
from app.ingestion.rag_components import get_vector_store, text_chunker
from app.utils.exceptions import (
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RAGIngestionPipeline:
    def __init__(
        self,
        text_splitter: TextSplitter = text_chunker,
        vector_store: Chroma = None,
    ):
        self._splitter = text_splitter
        self._vector_store = (
            vector_store if vector_store is not None else get_vector_store()
        )

    def process_file(self, filename: str, file_bytes: bytes) -> int:
        """
        Processes a single incoming byte stream file into the vector store.
        """
        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            raise UnsupportedFileTypeError(
                f"Missing file type extension context for: {filename}"
            )

        extension = filename[dot_idx:].lower()

        if extension not in EXTRACTOR_REGISTRY:
            raise UnsupportedFileTypeError(
                f"Extension '{extension}' has no mapped parsing strategy."
            )

        extractor = EXTRACTOR_REGISTRY[extension]()

        logger.info(f"Extracting text content streams from: {filename}")
        raw_text = extractor.extract(file_bytes)

        if not raw_text.strip():
            raise FileExtractionError(
                f"No parseable character patterns found within: {filename}"
            )

        source_doc = Document(page_content=raw_text, metadata={"source": filename})

        chunks = self._splitter.split_documents([source_doc])
        logger.info(f"Segmented '{filename}' into {len(chunks)} fragments.")

        try:
            self._vector_store.add_documents(chunks)
            logger.info(
                f"Successfully integrated embedded arrays for '{filename}' into storage."
            )
            return len(chunks)
        except Exception as e:
            raise VectorStoreError(
                f"Failed loading vector embeddings into database: {str(e)}"
            )
