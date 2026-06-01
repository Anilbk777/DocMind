from typing import List, Tuple
from langchain_core.documents import Document
from app.utils.logging import LoggerFactory
from app.ingestion.rag_components import VectorStore
import uuid

logger = LoggerFactory.get_logger(__name__)


class RetrievalService:
    def __init__(
        self,
        similarity_threshold: float = 0.4,
        max_results: int = 5,
    ):
        self.vector_store = VectorStore.get_vector_store()
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results

    async def get_context(
        self, question: str, user_id: uuid.UUID
    ) -> Tuple[str, bool, List[str]]:
        """
        Retrieves context and maps metadata fields.
        Returns: (context_string, is_from_vector_store, list_of_sources)
        """
        # 1. Fetch raw matches from vector storage
        raw_docs_with_scores = await self._query_vector_store(question, user_id)

        # FIX: Filter out chunks individually based on the 0.4 threshold
        valid_docs_with_scores = [
            (doc, score)
            for doc, score in raw_docs_with_scores
            if score >= self.similarity_threshold
        ]

        # Check if ANY individual documents survived the filter
        if valid_docs_with_scores:
            logger.info(
                f"Filtered context: keeping {len(valid_docs_with_scores)} out of {len(raw_docs_with_scores)} chunks."
            )

            # This will now ONLY join the chunks that cleared 0.4 (just the resume!)
            context_str = "\n\n".join(
                [doc.page_content for doc, _ in valid_docs_with_scores]
            )

            # Extract unique sources dynamically from valid document metadata
            sources = []
            for doc, _ in valid_docs_with_scores:
                source_id = (
                    doc.metadata.get("source")
                    or doc.metadata.get("file_name")
                    or "Unknown Document"
                )
                if source_id not in sources:
                    sources.append(source_id)

            return context_str, True, sources

        logger.warning(
            "Vector context insufficient or missing. Using llm general response."
        )
        return "", False, []

    async def _query_vector_store(
        self,
        question: str,
        user_id: uuid.UUID,
    ) -> List[Tuple[Document, float]]:
        try:
            results = await self.vector_store.asimilarity_search_with_relevance_scores(
                question, k=self.max_results, filter={"user_id": str(user_id)}
            )
            logger.info(
                f"Vector search raw query execution returned {len(results)} total potential segments."
            )
            for idx, (doc, score) in enumerate(results):
                source = doc.metadata.get("source", "Unknown")
                logger.info(
                    f" -> Match [{idx + 1}] File: '{source}' | Normalized Relevance Score: {score:.4f}"
                )
            return results
        except Exception as e:
            logger.error(
                f"Vector database search failed unexpectedly: {str(e)}", exc_info=True
            )
            return []
