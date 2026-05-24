# from abc import ABC, abstractmethod
# from enum import Enum

# from langchain_core.language_models.chat_models import BaseChatModel
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq


# class ILLMStrategy(ABC):
#     """
#     Interface definition for all LLM Provider Strategies.
#     """

#     @abstractmethod
#     def get_model(self) -> BaseChatModel:
#         """Returns the configured underlying LangChain ChatModel client instance."""
#         pass


# class GeminiFlashStrategy(ILLMStrategy):
#     def __init__(self, model_name: str = "gemini-2.5-flash"):
#         self._llm = ChatGoogleGenerativeAI(
#             model=model_name,
#             temperature=0.2,
#             max_retries=2,
 
#         )

#     def get_model(self) -> BaseChatModel:
#         return self._llm


# class GroqLlamaStrategy(ILLMStrategy):
#     def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
#         self._llm = ChatGroq(model=model_name, temperature=0.2, max_retries=2)

#     def get_model(self) -> BaseChatModel:
#         return self._llm


# class LLMProvider(Enum):
#     GEMINI = "gemini"
#     GROQ = "groq"

#     def get_strategy(self) -> ILLMStrategy:

#         mapping = {
#             LLMProvider.GEMINI: GeminiFlashStrategy,
#             LLMProvider.GROQ: GroqLlamaStrategy,
#         }

#         strategy_class = mapping.get(self)
#         if not strategy_class:
#             raise NotImplementedError(
#                 f"No strategy class assigned for provider enum: {self.name}"
#             )

#         return strategy_class()


# =============================================================================================

# llm_strategies.py  (minor improvement: lazy-cached strategies per provider)

from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


class ILLMStrategy(ABC):
    """Interface for all LLM Provider Strategies."""

    @abstractmethod
    def get_model(self) -> BaseChatModel:
        """Returns the configured LangChain ChatModel instance."""
        ...


class GeminiFlashStrategy(ILLMStrategy):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self._model_name = model_name

    @cached_property  # instantiated once per strategy instance, not per call
    def _llm(self) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            model=self._model_name,
            temperature=0.2,
            max_retries=2,
        )

    def get_model(self) -> BaseChatModel:
        return self._llm


class GroqLlamaStrategy(ILLMStrategy):
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self._model_name = model_name

    @cached_property
    def _llm(self) -> BaseChatModel:
        return ChatGroq(model=self._model_name, temperature=0.2, max_retries=2)

    def get_model(self) -> BaseChatModel:
        return self._llm


class LLMProvider(Enum):
    GEMINI = "gemini"
    GROQ = "groq"

    def get_strategy(self) -> ILLMStrategy:
        mapping = {
            LLMProvider.GEMINI: GeminiFlashStrategy,
            LLMProvider.GROQ: GroqLlamaStrategy,
        }
        strategy_class = mapping.get(self)
        if not strategy_class:
            raise NotImplementedError(
                f"No strategy class assigned for provider enum: {self.name}"
            )
        return strategy_class()