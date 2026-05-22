# retrieval_service.py
from typing import List, Tuple

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.documents import Document

from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RetrievalService:
    def __init__(
        self, vector_store, similarity_threshold: float = 0.4, max_results: int = 3
    ):
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self._web_search_tool = DuckDuckGoSearchRun()

    def get_context(self, question: str) -> Tuple[str, bool, List[str]]:
        """
        Retrieves context and maps metadata fields.
        Returns: (context_string, is_from_vector_store, list_of_sources)
        """
        # 1. Try vector store retrieval
        docs_with_scores = self._query_vector_store(question)

        if self._is_context_adequate(docs_with_scores):
            logger.info("Internal vector database match passed confidence threshold.")

            context_str = "\n\n".join([doc.page_content for doc, _ in docs_with_scores])

            # Extract unique sources dynamically from document metadata fields
            sources = []
            for doc, _ in docs_with_scores:
                # Fallback progression checking common source metadata naming variants
                source_id = (
                    doc.metadata.get("source")
                    or doc.metadata.get("file_name")
                    or "Unknown Document"
                )
                if source_id not in sources:
                    sources.append(source_id)

            return context_str, True, sources

        # 2. Fall back to Web Search
        logger.warning("Vector context insufficient or missing. Fetching web fallback.")
        web_snippets = self._query_web_fallback(question)

        # Web search results don't have structural local doc sources
        return web_snippets, False, ["Web Search Engine"]

    def _query_vector_store(self, question: str) -> List[Tuple[Document, float]]:
        try:
            return self.vector_store.similarity_search_with_score(
                question, k=self.max_results
            )
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

    def _query_web_fallback(self, question: str) -> str:
        try:
            snippets = self._web_search_tool.run(question)
            return (
                ""
                if not snippets
                or "No good DuckDuckGo Search Result available" in snippets
                else snippets
            )
        except Exception as e:
            logger.error(f"DuckDuckGo infrastructure failure: {str(e)}", exc_info=True)
            return ""
