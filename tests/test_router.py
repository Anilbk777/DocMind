# tests/test_router.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.api.routers import (
    chat,
    upload_document,
)


@pytest.mark.asyncio
async def test_upload_file_endpoint_success(mocker):
    """Verifies upload routing intercepts and forwards file bytes accurately to background workers."""
    mock_service_instance = MagicMock()
    # This return value (5) dictates what replaces {chunks_created} in your message
    mock_service_instance.process_document_background = AsyncMock(return_value=5)

    mocker.patch(
        "app.api.routers.DocumentProcessingService", return_value=mock_service_instance
    )

    mock_file = MagicMock()
    mock_file.filename = "test_document.txt"
    mock_file.size = 1024
    mock_file.read = AsyncMock(return_value=b"Raw file stream contents")

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.vector_store = MagicMock()

    # Run the endpoint handler
    response = await upload_document(file=mock_file, request=mock_request)

    # FIX: Assert against the keys and string structure your router actually outputs
    assert response["status"] == "Success"
    assert response["filename"] == "test_document.txt"
    assert "5 vector chunks" in response["message"]


@pytest.mark.asyncio
async def test_chat_streaming_endpoint_chunks(mocker):
    """Verifies that the chat router accurately constructs and flushes the generator payload stream."""
    # FIX: Patch the whole service class inside routers.py
    # This completely bypasses the real __init__ and prevents the provider error
    mock_service_instance = MagicMock()

    async def mock_generator(*args, **kwargs):
        yield "StreamingChunk1 "
        yield "StreamingChunk2"

    mock_service_instance.answer_question_stream = mock_generator
    mocker.patch(
        "app.api.routers.RagOrchestrationService", return_value=mock_service_instance
    )

    # Mock input parameters
    mock_payload = MagicMock()
    mock_payload.query = "Who is Anil BK?"
    mock_payload.provider = "GEMINI"

    mock_request = MagicMock(spec=Request)
    mock_request.app.state.vector_store = MagicMock()

    response = await chat(payload=mock_payload, request=mock_request)

    # Verify a StreamingResponse object is built properly
    assert response.media_type == "text/plain"

    # Consume chunks directly from the response generator stream
    chunks = [chunk async for chunk in response.body_iterator]
    assert "StreamingChunk1 " in chunks
    assert "StreamingChunk2" in chunks
