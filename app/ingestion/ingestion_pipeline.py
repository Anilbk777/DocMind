# pipeline_service.py
import uuid

import numpy as np
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

from app.ingestion.file_extractor import EXTRACTOR_REGISTRY
from app.ingestion.rag_components import VectorStore, text_chunker
from app.utils.exceptions import (
    FileExtractionError,
    UnsupportedFileTypeError,
    VectorStoreError,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RAGIngestionPipeline:
    def __init__(self):
        self._splitter: TextSplitter = text_chunker
        self._vector_store: Chroma = VectorStore.get_vector_store()

    def process_file(self, filename: str, file_bytes: bytes, user_id: uuid.UUID) -> int:
        """
        Full ingestion pipeline for a single file.
        Returns:
            Number of chunks written to the vector store.
        """
        # Phase 1: Extract
        logger.info("[Phase 1] Extracting text content streams from: %s", filename)
        raw_text = self._extract(filename, file_bytes)

        # Phase 2: Chunk
        logger.info("[Phase 2] Chunking '%s'…", filename)
        chunks = self._chunk(filename, raw_text, user_id)
        logger.info("Segmented '%s' into %d fragments.", filename, len(chunks))

        # Phase 3: Embed
        logger.info("[Phase 3] Computing embeddings for '%s'…", filename)
        texts, metadatas, ids = self._prepare_vectors(chunks)
        embeddings = self._vector_store._embedding_function.embed_documents(texts)

        # Phase 4: Store
        logger.info(
            "[Phase 4] Storing embeddings, documents, and metadata for '%s'…",
            filename,
        )
        self._store(texts, embeddings, metadatas, ids, filename)

        # Timing report
        logger.info(
            "Successfully integrated embedded arrays for '%s' into storage.",
            filename,
        )
        return len(chunks)

    def _extract(self, filename: str, file_bytes: bytes) -> str:
        """Detect extension, pick the right extractor, return plain text."""
        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            raise UnsupportedFileTypeError(
                f"No file extension found in filename: '{filename}'"
            )

        extension = filename[dot_idx:].lower()
        extractor_cls = EXTRACTOR_REGISTRY.get(extension)
        if extractor_cls is None:
            raise UnsupportedFileTypeError(
                f"Extension '{extension}' has no registered extractor. "
                f"Supported: {sorted(EXTRACTOR_REGISTRY)}"
            )

        raw_text = extractor_cls().extract(file_bytes)

        if not raw_text.strip():
            raise FileExtractionError(
                f"No parseable text found in '{filename}'. "
                "File may be empty, image-only, or corrupted."
            )

        return raw_text

    def _chunk(
        self, filename: str, raw_text: str, user_id: uuid.UUID
    ) -> list[Document]:
        """Split raw text into overlapping LangChain Document chunks."""
        source_doc = Document(
            page_content=raw_text,
            metadata={"source": filename, "user_id": str(user_id)},
        )
        return self._splitter.split_documents([source_doc])

    def _prepare_vectors(
        self,
        chunks: list[Document],
    ) -> tuple[list[str], list[dict], list[str]]:
        """
        Extract text, metadata, and generate stable UUIDs from chunks.
        """
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]
        return texts, metadatas, ids

    def _store(
        self,
        texts: list[str],
        embeddings: np.ndarray,
        metadatas: list[dict],
        ids: list[str],
        filename: str,
    ) -> None:
        """
        Write pre-computed embeddings directly to the ChromaDB collection.
        """
        try:
            self._vector_store._collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"ChromaDB write failed for '{filename}': {exc}"
            ) from exc
