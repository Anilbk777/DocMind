# rag_service.py

from langchain_core.output_parsers import StrOutputParser
from app.core.llm_strategies import LLMProvider
from app.core.services.retrieval_service import RetrievalService

from app.core.prompt_builder import RAG_PROMPT_TEMPLATE, WEB_FALLBACK_PROMPT_TEMPLATE
from app.utils.exceptions import RAGServiceException
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RagOrchestrationService:
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GROQ,
        retrieval_service: RetrievalService = None,
    ):
        self.retrieval_service = (
            retrieval_service if retrieval_service is not None else RetrievalService()
        )
        try:
            self._llm = provider.get_strategy().get_model()
            self._parser = StrOutputParser()
        except Exception as e:
            logger.error(
                f"Failed to extract LLM client from provider strategy: {str(e)}",
                exc_info=True,
            )
            raise RAGServiceException(
                "Generation dependency initialization failed."
            ) from e

    async def answer_question_stream(self, question: str) -> str:
        if not question.strip():
            yield "Please provide a valid, non-empty query string."
            return

        try:
            # Destructure our updated tuple tracking sources
            (
                context,
                is_internal_data,
                sources,
            ) = await self.retrieval_service.get_context(question)

            if not context.strip():
                yield "I cannot find any valid local documentation or online resources to answer that question."
                return

            prompt = (
                RAG_PROMPT_TEMPLATE
                if is_internal_data
                else WEB_FALLBACK_PROMPT_TEMPLATE
            )

            chain = prompt | self._llm | self._parser

            # llm_response = await chain.ainvoke(
            #     {"context": context, "question": question}
            # )
            async for chunk in chain.astream(
                {"context": context, "question": question}
            ):
                # Safely parse text whether chunk is a raw string or an AIMessageChunk object
                content = (
                    chunk
                    if isinstance(chunk, str)
                    else getattr(chunk, "content", str(chunk))
                )
                yield content

            # 4. TERMINAL INSERTION: The loop finished, meaning the LLM is done.
            # Append citations cleanly at the very bottom of the user's interface.
            if is_internal_data and sources:
                citation_block = "\n\n**Sources Gathered:**\n" + "\n".join(
                    [f"- *{source}*" for source in sources]
                )
                yield citation_block

        except Exception as e:
            logger.error(
                f"Unhandled operational failure inside generation sequence: {str(e)}",
                exc_info=True,
            )

            # Check if it looks like a temporary capacity issue
            if "503" in str(e) or "demand" in str(e).lower():
                raise RAGServiceException(
                    "The AI engine is currently overloaded with traffic. Please wait a moment and try again."
                )

            raise RAGServiceException(
                "An error occurred while compiling your generative answer pipeline."
            ) from e
