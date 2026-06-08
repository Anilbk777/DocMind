from langchain_chroma import Chroma

# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import threading
import chromadb
import os
from dotenv import load_dotenv
from app.utils.logging import LoggerFactory

load_dotenv()


logger = LoggerFactory.get_logger(__name__)

text_chunker = RecursiveCharacterTextSplitter(
    chunk_size=1200, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
)


class EmbeddingsModel:
    _embedding_model: GoogleGenerativeAIEmbeddings | None = None
    _embedding_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_embedding_model(cls) -> GoogleGenerativeAIEmbeddings:
        """Returns the shared Google embedding model, loading it only on first call."""
        if cls._embedding_model is not None:
            return cls._embedding_model

        with cls._embedding_lock:
            if cls._embedding_model is None:
                logger.info("Loading Google Generative AI embedding model...")
                cls._embedding_model = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-2-preview",
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    output_dimensionality=768,  # standard, matches chromadb default
                )
        return cls._embedding_model


# class EmbeddingsModel:
#     _embedding_model: HuggingFaceEmbeddings | None = None
#     _embedding_lock: threading.Lock = threading.Lock()

#     @classmethod
#     def get_embedding_model(cls) -> HuggingFaceEmbeddings:
#         """Returns the shared embedding model, loading it only on first call."""
#         if cls._embedding_model is not None:
#             return cls._embedding_model

#         with cls._embedding_lock:
#             if cls._embedding_model is None:
#                 logger.info("Loading local HuggingFace embedding model...")
#                 cls._embedding_model = HuggingFaceEmbeddings(
#                     model_name="all-MiniLM-L6-v2",
#                     encode_kwargs={
#                         "batch_size": 32,  # process 32 chunks at once instead of 1
#                         "normalize_embeddings": True,
#                     },
#                     model_kwargs={"device": "cpu"},
#                 )
#         return cls._embedding_model


class VectorStore:
    _chroma_vector_store: Chroma | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_vector_store(cls) -> Chroma:
        """Returns the shared cloud Chroma vector store."""
        if cls._chroma_vector_store is not None:
            return cls._chroma_vector_store

        with cls._lock:
            if cls._chroma_vector_store is None:
                logger.info("Configuring cloud Vector Store...")

                api_key = os.getenv("CHROMA_API_KEY")
                tenant = os.getenv("CHROMA_TENANT")
                database = os.getenv("CHROMA_DATABASE", "default")

                if not api_key or not tenant:
                    raise ValueError(
                        f"Chroma Cloud configuration missing from environment! "
                        f"CHROMA_API_KEY={'Found' if api_key else 'MISSING'}, "
                        f"CHROMA_TENANT={'Found' if tenant else 'MISSING'}"
                    )

                try:
                    chroma_client = chromadb.CloudClient(
                        cloud_host="europe-west1.gcp.trychroma.com",
                        cloud_port=443,
                        tenant=tenant,
                        database=database,
                        api_key=api_key,
                    )

                    cls._chroma_vector_store = Chroma(
                        client=chroma_client,
                        collection_name=os.getenv(
                            "CHROMA_COLLECTION_NAME", "default_collection"
                        ),
                        embedding_function=EmbeddingsModel.get_embedding_model(),
                        collection_metadata={"hnsw:space": "cosine"},
                    )

                    logger.info("Cloud Vector Store configured successfully.")

                except Exception as e:
                    logger.error(f"Failed to initialize Chroma Cloud Client: {str(e)}")
                    raise e

        return cls._chroma_vector_store
