# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure LangChain validators don't crash on missing environment keys."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")


@pytest.fixture
def mock_embeddings():
    """Mocks the SentenceTransformer / Embedding generation layer."""
    mock = MagicMock()
    mock.embed_query.return_value = [0.1] * 384  # Standard vector dimensions
    mock.embed_documents.return_value = [[0.1] * 384]
    return mock


@pytest.fixture
def mock_vector_store():
    """Mocks Chroma DB interactions."""
    mock = MagicMock()
    # Mock similarity search return values
    mock.similarity_search_with_relevance_scores.return_value = []
    return mock


@pytest.fixture
def mock_llm():
    """Mocks LangChain LLM generation outputs."""
    mock = MagicMock()
    return mock


@pytest.fixture
def client(mock_vector_store):
    """Provides a FastAPI TestClient with overridden application state."""
    # Force the app to use our mock store instead of trying to open real Chroma storage
    app.state.vector_store = mock_vector_store
    with TestClient(app) as test_client:
        yield test_client
