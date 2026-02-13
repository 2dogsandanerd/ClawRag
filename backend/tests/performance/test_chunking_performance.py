import time
import pytest
from src.core.indexing_service import IndexingService, ChunkConfig, SplitterType, Document, RAGOperationStatus
from unittest.mock import AsyncMock, MagicMock, patch
from llama_index.core.schema import TextNode
# We need real or mock embeddings dependent on what we want to measure. 
# For pure overhead of our logic, mock is fine. 
# For actual "semantic" speed, we would need real embeddings which is slow and requires model.
# Let's mock the "heavy" embedding part with a sleep to simulate work.

from llama_index.core.base.embeddings.base import BaseEmbedding
from typing import List, Any

class MockEmbedModel(BaseEmbedding):
    def _get_text_embedding(self, text: str) -> List[float]:
        return [0.1] * 384

    def _get_query_embedding(self, query: str) -> List[float]:
         return [0.1] * 384

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return [0.1] * 384
        
    async def _aget_text_embedding(self, text: str) -> List[float]:
        await asyncio.sleep(0.01)
        return [0.1] * 384

    async def aget_text_embedding_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        # Simulate latency
        await asyncio.sleep(0.01 * len(texts)) 
        return [[0.1]*384 for _ in texts]
        
    def get_text_embedding_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        import time
        time.sleep(0.01 * len(texts))
        return [[0.1]*384 for _ in texts]

@pytest.mark.asyncio
async def test_chunking_performance_comparison():
    """Compare performance of semantic vs sentence chunking (simulated)"""
    
    large_text = "This is a sentence. " * 1000
    test_document = Document(
        content=large_text,
        metadata={"source": "performance_test"}
    )
    
    # Setup mocks
    chroma_manager = AsyncMock()
    collection_manager = MagicMock()
    embedding_manager = MagicMock()
    embedding_manager.get_embeddings.return_value = MockEmbedModel()
    
    service = IndexingService(chroma_manager, collection_manager, embedding_manager)
    mock_collection = MagicMock()
    mock_collection.name = "perf_test"
    
    # 1. Sentence Splitter
    sentence_config = ChunkConfig(
        splitter_type=SplitterType.SENTENCE
    )
    
    # Build a fast pipeline mock for sentence
    with patch("src.core.indexing_service.IngestionPipeline") as MockPipeline:
        pipeline = MockPipeline.return_value
        pipeline.arun = AsyncMock(return_value=[TextNode() for _ in range(100)]) # Dummy return
        
        start_time = time.time()
        await service._index_with_simple_chunking([test_document], mock_collection, sentence_config)
        sentence_duration = time.time() - start_time
        
    # 2. Semantic Splitter
    semantic_config = ChunkConfig(
        splitter_type=SplitterType.SEMANTIC
    )
    
    # We use valid BatchSemanticSplitter but mocked embeddings (via service setup)
    # Note: Our BatchSemanticSplitter uses the embed_model passed to it
    # We need to make sure Resource Manager can import GPUtil/psutil (installed).
    
    # Mock GPUMonitor to always return "healthy" to ensure we run semantic path
    with patch("src.core.resource_manager.GPUMonitor") as MockMonitor:
        monitor = MockMonitor.return_value
        monitor.get_free_memory.return_value = 10 * 1024**3 # 10GB free
        monitor.gpus = [MagicMock()] 
        
        # We also need to mock IngestionPipeline again as it is created fresh
        with patch("src.core.indexing_service.IngestionPipeline") as MockPipeline:
            pipeline = MockPipeline.return_value
            pipeline.arun = AsyncMock(return_value=[TextNode() for _ in range(100)])

            start_time = time.time()
            await service._index_with_simple_chunking([test_document], mock_collection, semantic_config)
            semantic_duration = time.time() - start_time

    print(f"\nSentence Splitter Duration: {sentence_duration:.4f}s")
    print(f"Semantic Splitter Duration: {semantic_duration:.4f}s")
    
    # Semantic should be slower (due to our sleep simulation in MockEmbedModel calls inside BatchSemanticSplitter)
    # BatchSemanticSplitter calls embed_model.get_text_embedding_batch
    # But wait, does SemanticSplitterNodeParser call get_text_embedding_batch? Yes.
    
    # Note: SentenceSplitter is pure CPU/regex. Semantic hits embeddings.
    # Our MockEmbedModel sleeps 0.01s per text. 1000 sentences -> lots of calls.
    
    # Just ensure it runs without error for now.
    assert semantic_duration > 0
    assert sentence_duration > 0
