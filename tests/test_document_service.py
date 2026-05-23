# tests/test_document_service.py
import pytest
from unittest.mock import MagicMock
from concurrent.futures import ThreadPoolExecutor
from app.core.services.document_service import DocumentProcessingService
from app.utils.exceptions import UnsupportedFileTypeError

@pytest.mark.asyncio
async def test_process_document_background_success():
    """Verifies that chunks are parsed and tracked accurately through the executor."""
    # 1. Mock the structural ingestion pipeline component
    mock_pipeline = MagicMock()
    mock_pipeline.process_file.return_value = 12  # Simulate 12 chunks generated
    
    # 2. Use a real local executor with 1 worker to let run_in_executor pass clean threads
    with ThreadPoolExecutor(max_workers=1) as executor:
        service = DocumentProcessingService(
            ingestion_pipeline=mock_pipeline, 
            executor=executor
        )
        
        # 3. Fire the async method execution path
        filename = "nepal_financial_report.pdf"
        file_bytes = b"Fake PDF document byte stream structure data"
        
        result_chunks = await service.process_document_background(filename, file_bytes)
        
        # 4. Assertions
        assert result_chunks == 12
        mock_pipeline.process_file.assert_called_once_with(filename, file_bytes)


@pytest.mark.asyncio
async def test_process_document_background_propagates_custom_exceptions():
    """Verifies that custom ingestion errors drop out of the thread cleanly to the caller."""
    mock_pipeline = MagicMock()
    # Force the underlying pipeline proxy worker to raise a handled validation error
    mock_pipeline.process_file.side_effect = UnsupportedFileTypeError("Invalid file extension format type.")
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        service = DocumentProcessingService(ingestion_pipeline=mock_pipeline, executor=executor)
        
        # Ensure our custom business exception propagates to the router block instead of vanishing
        with pytest.raises(UnsupportedFileTypeError):
            await service.process_document_background("malicious_virus.exe", b"0x001021")