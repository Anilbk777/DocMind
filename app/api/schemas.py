from pydantic import BaseModel, Field
from app.core.llm_strategies import LLMProvider

class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        description="The question or prompt you want the RAG system to answer.",
        min_length=1,
    )
    provider: LLMProvider = Field(
        ..., 
        description="Select your preferred LLM engine from the dropdown menu."
    )

class ChatResponse(BaseModel):
    answer: str = Field(
        ..., description="The generated response from the RAG pipeline."
    )