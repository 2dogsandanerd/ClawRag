import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.v1.rag.models.ingestion import ProcessOptions, ChunkingStrategy
from src.core.indexing_service import SplitterType

# Mock the entire application structure to test API logic without running full server
# However, for FastApi testing, we usually need the 'app' instance.
# Since we are modifying an existing app, let's test the routers in isolation or mock dependencies.

# Let's test the models first
def test_process_options_validation():
    # Valid options
    options = ProcessOptions(
        chunk_size=500,
        chunk_overlap=50,
        chunking_strategy=ChunkingStrategy.SEMANTIC
    )
    assert options.chunk_size == 500
    assert options.chunk_overlap == 50
    assert options.chunking_strategy == ChunkingStrategy.SEMANTIC

    # Invalid chunk size
    with pytest.raises(ValueError):
        ProcessOptions(chunk_size=50)  # Too small

    # Invalid overlap
    with pytest.raises(ValueError):
        ProcessOptions(chunk_size=500, chunk_overlap=500)  # Overlap >= size

# Test the Recommendations Logic (Unit test for the endpoint logic)
from src.api.v1.rag.chunking_strategies import recommend_strategy, StrategyRecommendationRequest

@pytest.mark.asyncio
async def test_recommend_strategy():
    # Small PDF -> Sentence (unless code/row)
    req = StrategyRecommendationRequest(document_type="pdf", document_size=5000)
    
    resp = await recommend_strategy(req)
    assert resp.recommended_strategy == ChunkingStrategy.SENTENCE
    assert resp.confidence == 0.8

    # Large PDF -> Semantic
    req = StrategyRecommendationRequest(document_type="pdf", document_size=15 * 1024 * 1024)
    resp = await recommend_strategy(req)
    assert resp.recommended_strategy == ChunkingStrategy.SEMANTIC
    assert resp.confidence == 0.9

    # Python file -> Code
    req = StrategyRecommendationRequest(document_type="py", document_size=5000)
    resp = await recommend_strategy(req)
    assert resp.recommended_strategy == ChunkingStrategy.CODE
    
    # CSV file -> Row
    req = StrategyRecommendationRequest(document_type="csv", document_size=5000)
    resp = await recommend_strategy(req)
    assert resp.recommended_strategy == ChunkingStrategy.ROW_BASED

# Test Ingestion Processor Logic manually (Unit test)
import sys
from unittest.mock import MagicMock, AsyncMock

# No need to mock src.database.database anymore as we created the file
# but we still need to patch AsyncSessionLocal in the test to avoid real DB connection during unit test

# Now we can import
from src.services.ingestion_processor import IngestionProcessor
from src.core.indexing_service import ChunkConfig

@pytest.mark.asyncio
async def test_ingestion_processor_options_extraction():
    processor = IngestionProcessor()
    
    # Mock parameters
    assignment = {
        "file_path": "/tmp/test.pdf",
        "filename": "test.pdf",
        "collection": "default",
        "process_options": {
            "chunk_size": 1234,
            "chunk_overlap": 123,
            "chunking_strategy": "semantic",
            "semantic_buffer_size": 2000
        }
    }
    
    # We want to test _process_single_file but it has many dependencies (DB, RAG Client).
    # We will mock them.
    
    mock_rag_client = MagicMock()
    mock_indexing_svc = MagicMock()
    mock_rag_client.indexing_service = mock_indexing_svc
    
    # Mocking async method index_documents
    mock_indexing_svc.index_documents = AsyncMock()
    
    # Use patch to mock AsyncSessionLocal and ExtractionService where they are defined
    with patch("src.database.database.AsyncSessionLocal") as mock_session_cls, \
         patch("src.services.extraction_service.ExtractionService") as mock_extraction_cls:
        
        # Configure mocks
        mock_db = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_db
        
        mock_extraction_svc = MagicMock()
        mock_extraction_cls.return_value = mock_extraction_svc
        
        # Mock extraction result
        mock_result = MagicMock()
        mock_result.extracted_text = "test content"
        mock_result.metadata = {}
        mock_result.file_hash = "abc"
        # Mock async extract_document
        mock_extraction_svc.extract_document = AsyncMock(return_value=mock_result)
        
        # Mock indexing response
        mock_idx_response = MagicMock()
        mock_idx_response.status = "SUCCESS"
        mock_idx_response.data = {"indexed_nodes": 5}
        mock_indexing_svc.index_documents.return_value = mock_idx_response
        
        # Run
        import asyncio
        semaphore = asyncio.Semaphore(1)
        result = await processor._process_single_file(assignment, "default", mock_rag_client, semaphore)
        
        assert result.success is True
        
        # Verify call to index_documents had correct ChunkConfig
        call_args = mock_indexing_svc.index_documents.call_args
        _, kwargs = call_args
        chunk_config = kwargs.get("chunk_config")
        
        assert isinstance(chunk_config, ChunkConfig)
        assert chunk_config.chunk_size == 1234
        assert chunk_config.chunk_overlap == 123
        assert chunk_config.splitter_type == SplitterType.SEMANTIC
        assert chunk_config.semantic_buffer_size == 2000
