# tests/test_rag_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.services.rag_service import RagOrchestrationService

@pytest.mark.asyncio
async def test_stream_appends_sources_at_the_end(mocker):
    """Verifies orchestration pipeline yields generation stream before appending sources."""
    mock_retrieval = MagicMock()
    mock_retrieval.get_context = AsyncMock(return_value=(
        "Mocked context text information data", True, ["Financial_Report.pdf"]
    ))
    
    # Intercept LangChain's internal stream execution
    async def mock_astream_sequence(*args, **kwargs):
        yield "AI text generation output stream contents."
        
    mocker.patch("langchain_core.runnables.RunnableSequence.astream", side_effect=mock_astream_sequence)
    
    # FIX: Mock the provider object so provider.get_strategy().get_model() doesn't crash
    mock_provider = MagicMock()
    
    service = RagOrchestrationService(provider=mock_provider, retrieval_service=mock_retrieval)
    
    # Safely assign dummy values to internal properties
    service._llm = MagicMock()
    service._parser = MagicMock()
    
    output_chunks = []
    async for chunk in service.answer_question_stream("Test question pipeline parameters"):
        output_chunks.append(chunk)
        
    assert len(output_chunks) >= 2
    assert "AI text generation" in output_chunks[0]
    assert "**Sources Gathered:**" in output_chunks[-1]
    assert "Financial_Report.pdf" in output_chunks[-1]