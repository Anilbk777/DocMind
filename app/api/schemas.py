from app.core.llm_strategies import LLMProvider
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        description="The question or prompt you want the RAG system to answer.",
        min_length=1,
    )
    provider: LLMProvider = Field(
        ..., description="The LLM strategy choice. ", include_in_schema=True
    )


class ChatResponse(BaseModel):
    answer: str = Field(
        ..., description="The generated response from the RAG pipeline."
    )
