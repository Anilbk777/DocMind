from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

# 1. EMbedding model
logger.info("Loading local HuggingFace embedding model...")
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Text Chunker Component
text_chunker = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
)

# 3. Vector Store Component
logger.info("Configuring development ephemeral Vector Store...")
chroma_vector_store = Chroma(
    persist_directory="./dev_chroma_db",
    collection_name="dev_rag_collection",
    embedding_function=embedding_model,
)
