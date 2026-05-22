from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

text_chunker = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
)

_embedding_model: HuggingFaceEmbeddings | None = None
_chroma_vector_store: Chroma | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Returns the shared embedding model, loading it only on first call."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading local HuggingFace embedding model...")
        _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedding_model


def get_vector_store() -> Chroma:
    """Returns the shared Chroma vector store, loading it only on first call."""
    global _chroma_vector_store
    if _chroma_vector_store is None:
        logger.info("Configuring development ephemeral Vector Store...")
        _chroma_vector_store = Chroma(
            persist_directory="./dev_chroma_db",
            collection_name="dev_rag_collection",
            embedding_function=get_embedding_model(),
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _chroma_vector_store
