from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import threading

from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

text_chunker = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
)


class EmbeddingsModel:
    _embedding_model: HuggingFaceEmbeddings | None = None
    _embedding_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_embedding_model(cls) -> HuggingFaceEmbeddings:
        """Returns the shared embedding model, loading it only on first call."""
        if cls._embedding_model is not None:
            return cls._embedding_model

        with cls._embedding_lock:
            if cls._embedding_model is None:
                logger.info("Loading local HuggingFace embedding model...")
                cls._embedding_model = HuggingFaceEmbeddings(
                    model_name="all-MiniLM-L6-v2",
                    encode_kwargs={
                        "batch_size": 32,  # process 32 chunks at once instead of 1
                        "normalize_embeddings": True,
                    },
                    model_kwargs={"device": "cpu"},
                )
        return cls._embedding_model


class VectorStore:
    _chroma_vector_store: Chroma | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_vector_store(cls) -> Chroma:
        """Returns the shared Chroma vector store, loading it only on first call."""
        if cls._chroma_vector_store is not None:
            return cls._chroma_vector_store

        with cls._lock:
            if cls._chroma_vector_store is None:
                logger.info("Configuring development ephemeral Vector Store...")
                cls._chroma_vector_store = Chroma(
                    persist_directory="./dev_chroma_db",
                    collection_name="dev_rag_collection",
                    embedding_function=EmbeddingsModel.get_embedding_model(),
                    collection_metadata={"hnsw:space": "cosine"},
                )
        return cls._chroma_vector_store
