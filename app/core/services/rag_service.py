# # rag_service.py

# from langchain_core.output_parsers import StrOutputParser
# from app.core.llm_strategies import LLMProvider
# from app.core.services.retrieval_service import RetrievalService

# from app.core.prompt_builder import (
#     RAG_PROMPT_TEMPLATE,
#     GENERAL_PROMPT_TEMPLATE,
# )
# from app.utils.exceptions import RAGServiceException
# from app.utils.logging import LoggerFactory

# logger = LoggerFactory.get_logger(__name__)


# class RagOrchestrationService:
#     def __init__(
#         self,
#         provider: LLMProvider = LLMProvider.GROQ,
#         retrieval_service: RetrievalService = None,
#     ):
#         self.retrieval_service = (
#             retrieval_service if retrieval_service is not None else RetrievalService()
#         )
#         try:
#             self._llm = provider.get_strategy().get_model()
#             self._parser = StrOutputParser()
#         except Exception as e:
#             logger.error(
#                 f"Failed to extract LLM client from provider strategy: {str(e)}",
#                 exc_info=True,
#             )
#             raise RAGServiceException(
#                 "Generation dependency initialization failed."
#             ) from e

#     async def answer_question_stream(self, question: str) -> str:
#         if not question.strip():
#             yield "Please provide a valid, non-empty query string."
#             return

#         try:
#             # Destructure our updated tuple tracking sources
#             (
#                 context,
#                 is_internal_data,
#                 sources,
#             ) = await self.retrieval_service.get_context(question)

#             # if not context.strip():
#             #     yield "I cannot find any valid local documentation or online resources to answer that question."
#             #     return
#             if is_internal_data:
#                 prompt = RAG_PROMPT_TEMPLATE
#                 chain = prompt | self._llm | self._parser

#                 for chunk in chain.stream({"context": context, "question": question}):
#                     # Safely parse text whether chunk is a raw string or an AIMessageChunk object
#                     content = (
#                         chunk
#                         if isinstance(chunk, str)
#                         else getattr(chunk, "content", str(chunk))
#                     )
#                     yield content

#                 # Append citations only when document chunks were successfully found
#                 if sources:
#                     citation_block = "\n\n**Sources Gathered:**\n" + "\n".join(
#                         [f"- *{source}*" for source in sources if source]
#                     )
#                     yield citation_block
#             else:
#                 prompt = GENERAL_PROMPT_TEMPLATE
#                 chain = prompt | self._llm | self._parser

#                 for chunk in chain.stream({"question": question}):
#                     # Safely parse text whether chunk is a raw string or an AIMessageChunk object
#                     content = (
#                         chunk
#                         if isinstance(chunk, str)
#                         else getattr(chunk, "content", str(chunk))
#                     )
#                     yield content

#         except Exception as e:
#             logger.error(
#                 f"Unhandled operational failure inside generation sequence: {str(e)}",
#                 exc_info=True,
#             )

#             # Check if it looks like a temporary capacity issue
#             if "503" in str(e) or "demand" in str(e).lower():
#                 raise RAGServiceException(
#                     "The AI engine is currently overloaded with traffic. Please wait a moment and try again."
#                 )

#             raise RAGServiceException(
#                 "An error occurred while compiling your generative answer pipeline."
#             ) from e


# ================================================================================================
# rag_service.py

from typing import AsyncGenerator
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import BasePromptTemplate

from app.core.llm_strategies import LLMProvider
from app.core.services.retrieval_service import RetrievalService
from app.core.prompt_builder import RAG_PROMPT_TEMPLATE, GENERAL_PROMPT_TEMPLATE
from app.utils.exceptions import RAGServiceException
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RagOrchestrationService:
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GROQ,
        retrieval_service: RetrievalService = None,
    ):
        self.retrieval_service = retrieval_service
        try:
            self._llm = provider.get_strategy().get_model()
            self._parser = StrOutputParser()
        except Exception as e:
            logger.error(
                "Failed to extract LLM client from provider strategy.",
                exc_info=True,
            )
            raise RAGServiceException(
                "Generation dependency initialization failed."
            ) from e

    def _build_chain(self, prompt: BasePromptTemplate):
        """Encapsulates chain assembly. Single place to modify the pipeline."""
        return prompt | self._llm | self._parser

    async def _stream_chain(
        self,
        prompt: BasePromptTemplate,
        inputs: dict,
    ) -> AsyncGenerator[str, None]:
        """
        Core streaming engine. Uses astream() — LangChain's native async
        streaming — so the event loop is never blocked between chunks.
        """
        chain = self._build_chain(prompt)
        async for chunk in chain.astream(inputs):
            # astream on LCEL chains with StrOutputParser yields plain strings.
            # Guard kept for safety in case a custom parser yields AIMessageChunk.
            yield (
                chunk
                if isinstance(chunk, str)
                else getattr(chunk, "content", str(chunk))
            )

    async def answer_question_stream(self, question: str) -> AsyncGenerator[str, None]:
        """
        Public async generator. Yields text chunks suitable for StreamingResponse.

        Error contract:
          - Validation errors yield a single user-facing message and return early.
          - Operational failures are logged and re-raised as RAGServiceException
            BEFORE any yield, so FastAPI can still return a proper 4xx/5xx.
            Mid-stream errors yield a sentinel error chunk so the client knows
            the stream was cut short.
        """
        if not question.strip():
            yield "Please provide a valid, non-empty query string."
            return

        # --- Resolve context BEFORE first yield so we can still raise HTTP errors ---
        try:
            (
                context,
                is_internal_data,
                sources,
            ) = await self.retrieval_service.get_context(question)
        except Exception as e:
            logger.error("Retrieval stage failed.", exc_info=True)
            # No yield has happened yet — safe to raise; FastAPI will convert to HTTP error
            raise RAGServiceException(
                "Failed to retrieve context for your question."
            ) from e

        # --- Determine prompt + inputs once ---
        if is_internal_data:
            prompt = RAG_PROMPT_TEMPLATE
            inputs = {"context": context, "question": question}
        else:
            prompt = GENERAL_PROMPT_TEMPLATE
            inputs = {"question": question}

        # --- Stream generation — errors here are mid-stream ---
        try:
            async for chunk in self._stream_chain(prompt, inputs):
                yield chunk
        except Exception as e:
            logger.error("Generation stage failed mid-stream.", exc_info=True)
            # We've already started streaming — signal the client gracefully
            if "503" in str(e) or "demand" in str(e).lower():
                yield "\n\n[Error: The AI engine is overloaded. Please retry.]"
            else:
                yield "\n\n[Error: Stream interrupted unexpectedly.]"
            return  # Stop the generator cleanly

        # --- Append citations after successful stream ---
        if is_internal_data and sources:
            citation_block = "\n\n**Sources Gathered:**\n" + "\n".join(
                f"- *{source}*" for source in sources if source
            )
            yield citation_block
