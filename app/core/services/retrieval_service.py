# retrieval_service.py
from typing import List, Tuple

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.documents import Document

from app.utils.logging import LoggerFactory

from app.ingestion.rag_components import get_vector_store

logger = LoggerFactory.get_logger(__name__)


class RetrievalService:
    def __init__(
        self,
        vector_store=None,  # Lazy: loaded on first use, not at import time
        similarity_threshold: float = 0.4,
        max_results: int = 5,
    ):
        # Use the lazy getter so the model only loads when first needed
        self.vector_store = (
            vector_store if vector_store is not None else get_vector_store()
        )
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self._web_search_tool = DuckDuckGoSearchRun()

    # async def get_context(self, question: str) -> Tuple[str, bool, List[str]]:
    #     """
    #     Retrieves context and maps metadata fields.
    #     Returns: (context_string, is_from_vector_store, list_of_sources)
    #     """
    #     # 1. Try vector store retrieval
    #     docs_with_scores = await self._query_vector_store(question)

    #     if self._is_context_adequate(docs_with_scores):
    #         logger.info("Internal vector database match passed confidence threshold.")

    #         context_str = "\n\n".join([doc.page_content for doc, _ in docs_with_scores])

    #         # Extract unique sources dynamically from document metadata fields
    #         sources = []
    #         for doc, _ in docs_with_scores:
    #             # Fallback progression checking common source metadata naming variants
    #             source_id = (
    #                 doc.metadata.get("source")
    #                 or doc.metadata.get("file_name")
    #                 or "Unknown Document"
    #             )
    #             if source_id not in sources:
    #                 sources.append(source_id)

    #         return context_str, True, sources

    #     # 2. Fall back to Web Search
    #     logger.warning("Vector context insufficient or missing. Fetching web fallback.")
    #     web_snippets = await self._query_web_fallback(question)

    #     # Web search results don't have structural local doc sources
    #     return web_snippets, False, ["Web Search Engine"]

    async def get_context(self, question: str) -> Tuple[str, bool, List[str]]:
        """
        Retrieves context and maps metadata fields.
        Returns: (context_string, is_from_vector_store, list_of_sources)
        """
        # 1. Fetch raw matches from vector storage
        raw_docs_with_scores = await self._query_vector_store(question)

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

        # 2. Fall back to Web Search if zero chunks cleared 0.4
        logger.warning("Vector context insufficient or missing. Fetching web fallback.")
        web_snippets = await self._query_web_fallback(question)
        return web_snippets, False, ["Web Search Engine"]

    async def _query_vector_store(self, question: str) -> List[Tuple[Document, float]]:
        try:
            results = await self.vector_store.asimilarity_search_with_relevance_scores(
                question, k=self.max_results
            )
            # DIAGNOSTIC LOGGING: Essential for tracing vector alignment matching
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

    def _is_context_adequate(
        self, docs_with_scores: List[Tuple[Document, float]]
    ) -> bool:
        if not docs_with_scores:
            return False
        _, top_score = docs_with_scores[0]
        return top_score >= self.similarity_threshold

    async def _query_web_fallback(self, question: str) -> str:
        try:
            snippets = await self._web_search_tool.arun(question)
            return (
                ""
                if not snippets
                or "No good DuckDuckGo Search Result available" in snippets
                else snippets
            )
        except Exception as e:
            logger.error(f"DuckDuckGo infrastructure failure: {str(e)}", exc_info=True)
            return ""
