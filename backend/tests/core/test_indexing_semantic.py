import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.indexing_service import IndexingService, ChunkConfig, SplitterType, Document, RAGOperationStatus, RAGResponse
from src.core.chroma_manager import ChromaManager
from src.core.collection_manager import CollectionManager
from src.core.embedding_manager import EmbeddingManager
from llama_index.core.schema import TextNode
from llama_index.core.base.embeddings.base import BaseEmbedding
import src.core.resource_manager # Ensure module is loaded for patching

@pytest.mark.asyncio
async def test_semantic_chunking_integration():
    """Test the integration of the semantic splitter"""
    # Setup mocks
    chroma_manager = AsyncMock(spec=ChromaManager)
    collection_manager = MagicMock(spec=CollectionManager)
    embedding_manager = MagicMock(spec=EmbeddingManager)
    
    # Mock embeddings
    # Mock embeddings
    mock_embeddings = MagicMock(spec=BaseEmbedding)
    embedding_manager.get_embeddings.return_value = mock_embeddings
    
    service = IndexingService(chroma_manager, collection_manager, embedding_manager)
    
    # Test Data
    test_document = Document(
        content="This is a test document with multiple paragraphs. "
                "The semantic splitter should be able to identify "
                "semantically related sections.",
        metadata={"source": "test"}
    )
    
    # Test with semantic chunking configuration
    chunk_config = ChunkConfig(
        chunk_size=512,
        chunk_overlap=128,
        splitter_type=SplitterType.SEMANTIC
    )
    
    # Mock chroma_collection
    mock_chroma_collection = MagicMock()
    mock_chroma_collection.name = "test_collection"
    
    # Mock BatchSemanticSplitter to avoid actual heavy lifting
    with patch("src.core.resource_manager.BatchSemanticSplitter") as MockSplitter:
        mock_splitter_instance = MockSplitter.return_value
        # Mock split_nodes to return some dummy nodes
        mock_splitter_instance.split_nodes = AsyncMock(return_value=[
            TextNode(text="Chunk 1", metadata={"source": "test"}),
            TextNode(text="Chunk 2", metadata={"source": "test"})
        ])
        
        # Mock IngestionPipeline
        with patch("src.core.indexing_service.IngestionPipeline") as MockPipeline:
            mock_pipeline_instance = MockPipeline.return_value
            mock_pipeline_instance.arun = AsyncMock(return_value=[
                TextNode(text="Chunk 1", metadata={"source": "test"}),
                TextNode(text="Chunk 2", metadata={"source": "test"})
            ])

            # Execution
            result = await service._index_with_simple_chunking(
                documents=[test_document],
                chroma_collection=mock_chroma_collection,
                chunk_config=chunk_config
            )
            
            # Assertions
            assert result.status == RAGOperationStatus.SUCCESS
            assert result.metadata["chunking_strategy"] == "semantic"
            
            # Verify BatchSemanticSplitter was initialized
            MockSplitter.assert_called_once()
            # Verify split_nodes was called
            mock_splitter_instance.split_nodes.assert_called_once()


@pytest.mark.asyncio
async def test_semantic_chunking_fallback():
    """Test the fallback mechanism when semantic splitter fails"""
    # Setup
    chroma_manager = AsyncMock(spec=ChromaManager)
    collection_manager = MagicMock(spec=CollectionManager)
    embedding_manager = MagicMock(spec=EmbeddingManager)
    
    mock_embeddings = MagicMock(spec=BaseEmbedding)
    embedding_manager.get_embeddings.return_value = mock_embeddings
    
    service = IndexingService(chroma_manager, collection_manager, embedding_manager)
    
    test_document = Document(
        content="Test content for fallback test",
        metadata={"source": "fallback_test"}
    )
    
    chunk_config = ChunkConfig(
        chunk_size=512,
        chunk_overlap=128,
        splitter_type=SplitterType.SEMANTIC
    )
    
    mock_chroma_collection = MagicMock()
    mock_chroma_collection.name = "fallback_test_collection"
    
    # Mock BatchSemanticSplitter to raise exception
    with patch("src.core.resource_manager.BatchSemanticSplitter") as MockSplitter:
        mock_splitter_instance = MockSplitter.return_value
        mock_splitter_instance.split_nodes = AsyncMock(side_effect=Exception("GPU OOM"))
        
        # Mock IngestionPipeline for fallback
        with patch("src.core.indexing_service.IngestionPipeline") as MockPipeline:
            mock_pipeline_instance = MockPipeline.return_value
            mock_pipeline_instance.arun = AsyncMock(return_value=[
                TextNode(text="Fallback Chunk", metadata={"source": "fallback_test"})
            ])
            
            # Execution
            result = await service._index_with_simple_chunking(
                documents=[test_document],
                chroma_collection=mock_chroma_collection,
                chunk_config=chunk_config
            )
            
            # Assertions
            assert result.status == RAGOperationStatus.SUCCESS
            # Should still report success but log error (which we can't easily assert here without log capture)
            # The metadata might still say "semantic" based on config, OR we might want to update it to "sentence" in fallback?
            # Current implementation does NOT update chunk_config in place, so metadata will say "semantic".
            # However, the important part is that it didn't crash.
            assert result.metadata["chunking_strategy"] == "semantic" 
            
            # Verify fallback pipeline called (SentenceSplitter)
            # We can check if SentenceSplitter was used in transformations list
            # But here we mocked IngestionPipeline, so we check if it was called (twice? once for semantic failure setup?? No)
            # It should be called after exception.
            assert MockPipeline.call_count >= 1

@pytest.mark.asyncio
async def test_heuristic_config_loading():
    """Test if correct config is loaded from heuristics"""
    chroma_manager = AsyncMock(spec=ChromaManager)
    collection_manager = MagicMock(spec=CollectionManager)
    embedding_manager = MagicMock(spec=EmbeddingManager)
    embedding_manager._load_config.return_value = {}
    embedding_manager.get_embeddings.return_value = MagicMock()
    
    service = IndexingService(chroma_manager, collection_manager, embedding_manager)
    
    # Mock chroma client to avoid actual DB calls
    chroma_manager.get_client_async.return_value = MagicMock()
    
    # Mock _index_with_simple_chunking to just return config
    with patch.object(service, '_index_with_simple_chunking', new_callable=AsyncMock) as mock_index:
         mock_index.return_value = RAGResponse(status=RAGOperationStatus.SUCCESS)
         
         # Test PDF (Semantic)
         pdf_doc = Document(content="test", metadata={"source": "file.pdf"})
         await service.index_documents([pdf_doc], "test_col")
         
         # Verify call arguments
         call_args = mock_index.call_args
         # chunk_config is 3rd arg (index 2) or kwarg
         config_used = call_args.kwargs.get('chunk_config') or call_args.args[2]
         
         assert config_used.splitter_type == SplitterType.SEMANTIC
