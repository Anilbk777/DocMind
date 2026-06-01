# tests/test_retrieval_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.documents import Document
from app.services.retrieval_service import RetrievalService


@pytest.fixture
def mock_vector_store():
    """Provides a mocked vector store containing an async search method."""
    store = MagicMock()
    store.asimilarity_search_with_relevance_scores = AsyncMock()
    return store


@pytest.fixture
def service(mock_vector_store, mocker):
    """Initializes the RetrievalService with the mocked vector store and patches web search."""
    # Patch DuckDuckGoSearchRun to avoid hit-testing live internet connections
    mocker.patch("app.services.retrieval_service.DuckDuckGoSearchRun")
    retrieval_svc = RetrievalService(
        vector_store=mock_vector_store, similarity_threshold=0.4
    )
    retrieval_svc._web_search_tool.arun = AsyncMock()
    return retrieval_svc


# ============================================================================
# 1. HAPPY PATH CASES
# ============================================================================


@pytest.mark.asyncio
async def test_get_context_happy_path_internal_data(service, mock_vector_store):
    """
    Verifies that chunks clearing the 0.4 threshold are combined into the context
    string and unique source file names are extracted perfectly.
    """
    # Setup: 2 docs that clear the 0.4 threshold
    doc1 = Document(
        page_content="NEPSE index gained 10 points today.",
        metadata={"source": "finance_report.pdf"},
    )
    doc2 = Document(
        page_content="Commercial banking sectors show low volatility.",
        metadata={"source": "finance_report.pdf"},
    )  # Duplicate source
    doc3 = Document(
        page_content="Random text chunk.", metadata={"file_name": "backup_data.txt"}
    )  # Alternate metadata key

    mock_vector_store.asimilarity_search_with_relevance_scores.return_value = [
        (doc1, 0.85),
        (doc2, 0.60),
        (doc3, 0.41),
    ]

    context_str, is_internal, sources = await service.get_context("NEPSE performance")

    # Assertions
    assert is_internal is True
    assert "NEPSE index gained" in context_str
    assert "Commercial banking" in context_str
    assert "Random text chunk" in context_str

    # Check that sources are deduplicated and alternate keys ('file_name') are processed
    assert len(sources) == 2
    assert "finance_report.pdf" in sources
    assert "backup_data.txt" in sources


# ============================================================================
# 2. EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_get_context_edge_case_below_threshold_triggers_fallback(
    service, mock_vector_store
):
    """
    Verifies that if matches exist but fall below the 0.4 threshold, they are
    filtered out completely, triggering the Web Search fallback channel.
    """
    # Setup: Document exists but has a weak score
    weak_doc = Document(
        page_content="Outdated irrelevant information.",
        metadata={"source": "old_cv.txt"},
    )
    mock_vector_store.asimilarity_search_with_relevance_scores.return_value = [
        (weak_doc, 0.38)
    ]

    # Mock DuckDuckGo returning data
    service._web_search_tool.arun.return_value = (
        "Live web search summary snippet about Kathmandu."
    )

    context_str, is_internal, sources = await service.get_context(
        "Current Kathmandu weather"
    )

    # Assertions
    assert is_internal is False
    assert context_str == "Live web search summary snippet about Kathmandu."
    assert sources == ["Web Search Engine"]

    # Verify the vector store filtering logic dropped the weak doc completely
    assert "Outdated irrelevant information" not in context_str


@pytest.mark.asyncio
async def test_get_context_edge_case_missing_metadata_keys(service, mock_vector_store):
    """
    Verifies that missing source keys inside document metadata default safely
    to 'Unknown Document' without dropping a KeyError crash.
    """
    # Setup: Document with completely empty metadata dict
    naked_doc = Document(page_content="Valid text data content.", metadata={})
    mock_vector_store.asimilarity_search_with_relevance_scores.return_value = [
        (naked_doc, 0.90)
    ]

    _, _, sources = await service.get_context("Valid text data content.")

    assert sources == ["Unknown Document"]


# ============================================================================
# 3. FAILURE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_get_context_failure_cascading_infrastructure_breakdown(
    service, mock_vector_store
):
    """
    Verifies resilience: If ChromaDB throws an unexpected operational exception
    AND DuckDuckGo search times out, the service safely degrades to returning an empty
    string context rather than crashing the system backend.
    """
    # 1. Force Vector Store to crash completely
    mock_vector_store.asimilarity_search_with_relevance_scores.side_effect = Exception(
        "Chroma connection refused"
    )

    # 2. Force DuckDuckGo Search Engine to crash right after
    service._web_search_tool.arun.side_effect = Exception(
        "DuckDuckGo rate limit exceeded (429)"
    )

    # Execution should not raise an error due to your try/except block layouts
    context_str, is_internal, sources = await service.get_context(
        "Emergency test question"
    )

    # Assertions
    assert is_internal is False
    assert context_str == ""
    assert sources == ["Web Search Engine"]
