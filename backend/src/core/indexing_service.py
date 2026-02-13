import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import hashlib
from loguru import logger
from dataclasses import dataclass

from src.core.chroma_manager import ChromaManager
from src.core.collection_manager import CollectionManager
from src.core.embedding_manager import EmbeddingManager
from src.core.circuit_breaker import RAGResponse, RAGOperationStatus
from src.storage.document_store import DocumentStore
from src.services.progress_service import progress_manager

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.schema import TextNode, Document as LlamaDocument
from llama_index.vector_stores.chroma import ChromaVectorStore
from enum import Enum

class SplitterType(str, Enum):
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    CODE = "code"
    ROW_BASED = "row_based"

@dataclass
class ChunkConfig:
    """Configuration for document chunking"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = None
    splitter_type: SplitterType = SplitterType.SENTENCE
    # Specific parameters for semantic splitter
    semantic_buffer_size: int = 1024
    semantic_similarity_threshold: float = 0.7

    def __post_init__(self):
        if self.separators is None:
            self.separators = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Document:
    """Document with metadata"""
    content: str
    metadata: dict
    doc_id: Optional[str] = None

    def __post_init__(self):
        if self.doc_id is None:
            # Generate unique ID from content hash
            self.doc_id = hashlib.sha256(
                self.content.encode()
            ).hexdigest()[:16]


class IndexingService:
    """
    Handles document indexing with chunking, deduplication, and metadata.
    """

    def __init__(
        self,
        chroma_manager: ChromaManager,
        collection_manager: CollectionManager,
        embedding_manager: EmbeddingManager
    ):
        self.chroma = chroma_manager
        self.collections = collection_manager
        self.embeddings = embedding_manager
        self._indexed_hashes: Dict[str, datetime] = {}  # For dedup
        
        # Initialize DocumentStore for parent document storage
        self.document_store = DocumentStore()

    async def index_documents(
        self,
        documents: List[Document],
        collection_name: str,
        chunk_config: Optional[ChunkConfig] = None,
        use_parent_child: bool = False,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 200,
        child_chunk_overlap: int = 20,
        batch_size: int = 100
    ) -> RAGResponse:
        """
        Index documents into collection with chunking and deduplication.

        Args:
            documents: List of documents to index
            collection_name: Target collection
            chunk_config: Chunking configuration (for simple chunking when use_parent_child=False)
            use_parent_child: Whether to use parent-child chunking strategy (Phase 2)
            parent_chunk_size: Size of parent chunks for context (default 2000 chars)
            child_chunk_size: Size of child chunks for searching (default 200 chars)
            child_chunk_overlap: Overlap for child chunks (default 20 chars)
            batch_size: Batch size for indexing (not used in LlamaIndex pipeline)

        Returns:
            RAGResponse with indexing statistics
        """
        chunk_config = chunk_config or ChunkConfig()
        
        # If no chunk_config passed, try to load heuristics from ingest_config based on document type
        # We need a representative document type. Assuming homogeneous batch or taking the first one.
        if chunk_config == ChunkConfig() and documents:
            # Try to infer type from metadata of first doc
            first_doc = documents[0]
            # Map mimetype or extension to config key
            # This is a basic mapping, can be improved
            source = first_doc.metadata.get("source", "").lower()
            doc_type = "default"
            if source.endswith(".pdf"): doc_type = "pdf"
            elif source.endswith(".docx"): doc_type = "docx"
            elif source.endswith(".html"): doc_type = "html"
            elif source.endswith(".md"): doc_type = "markdown"
            elif source.endswith(".csv"): doc_type = "csv"
            elif source.endswith(".py") or source.endswith(".js"): doc_type = "code"
            
            from src.core.ingest_config import get_ingest_config
            config = get_ingest_config()
            heuristic = getattr(config.heuristics, doc_type, config.heuristics.default)
            
            try:
                chunk_config.chunk_size = heuristic.chunk_size
                chunk_config.chunk_overlap = heuristic.overlap
                chunk_config.splitter_type = SplitterType(heuristic.splitter_type)
            except Exception as e:
                logger.warning(f"Failed to apply heuristic for {doc_type}: {e}")

        try:
            # Get the chroma client through the chroma_manager (async)
            chroma_client = await self.chroma.get_client_async()
            if not chroma_client:
                raise ConnectionError("Failed to connect to ChromaDB")

            # Get or create collection using ChromaDB client
            logger.debug(f"Attempting to get or create collection '{collection_name}'")
            try:
                chroma_collection = await asyncio.to_thread(
                    chroma_client.get_collection,
                    collection_name
                )
                logger.debug(f"Successfully got existing collection '{collection_name}'")
            except Exception as e:
                logger.warning(f"Collection '{collection_name}' not found, attempting to create. Error: {e}")
                chroma_collection = await asyncio.to_thread(
                    chroma_client.create_collection,
                    collection_name
                )
                logger.debug(f"Successfully created new collection '{collection_name}'")

            # Handle parent-child indexing if requested
            if use_parent_child:
                return await self._index_with_parent_child(
                    documents=documents,
                    chroma_collection=chroma_collection,
                    parent_chunk_size=parent_chunk_size,
                    child_chunk_size=child_chunk_size,
                    child_chunk_overlap=child_chunk_overlap
                )
            else:
                # Use simple chunking approach
                return await self._index_with_simple_chunking(
                    documents=documents,
                    chroma_collection=chroma_collection,
                    chunk_config=chunk_config
                )

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return RAGResponse(
                status=RAGOperationStatus.FAILURE,
                error=str(e)
            )

    async def _deduplicate_documents(
        self,
        documents: List[Document],
        collection_name: str
    ) -> List[Document]:
        """
        Deduplicate documents based on content hash and age (Issue #5).
        """
        unique_docs = []

        for doc in documents:
            doc_hash = self._compute_document_hash(doc.content)

            # Check if already indexed recently
            if doc_hash in self._indexed_hashes:
                last_indexed = self._indexed_hashes[doc_hash]
                age_hours = (datetime.now() - last_indexed).total_seconds() / 3600

                # Only skip if indexed within last 24 hours
                if age_hours < 24:
                    logger.debug(f"Skipping duplicate document (indexed {age_hours:.1f}h ago)")
                    continue
                else:
                    logger.debug(f"Re-indexing old document (indexed {age_hours:.1f}h ago)")

            # Check if exists in collection
            if await self._document_exists_in_collection(doc_hash, collection_name):
                logger.debug(f"Document {doc_hash} already exists in collection")
                continue

            unique_docs.append(doc)
            self._indexed_hashes[doc_hash] = datetime.now()

        return unique_docs

    async def _index_with_simple_chunking(
        self,
        documents: List[Document],
        chroma_collection,
        chunk_config: ChunkConfig
    ) -> RAGResponse:
        """Index documents using simple chunking approach."""
        # Get system-wide defaults from embedding_manager
        manager_config = self.embeddings._load_config()
        embedding_provider = manager_config.get("EMBEDDING_PROVIDER", "ollama")
        embedding_model = manager_config.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
        
        embeddings = self.embeddings.get_embeddings(
            provider=embedding_provider,
            model=embedding_model,
            use_fallback=True
        )
        
        if not embeddings:
            return RAGResponse(
                status=RAGOperationStatus.FAILURE,
                error=f"Failed to initialize embeddings: {embedding_provider}:{embedding_model}"
            )

        # Convert our Document objects to LlamaIndex Document objects (not TextNode!)
        from llama_index.core.schema import Document as LlamaDocument
        import json
        
        llama_docs = []
        for doc in documents:
            # Sanitize metadata: ChromaDB only accepts str, int, float, None
            sanitized_metadata = {}
            for key, value in doc.metadata.items():
                if isinstance(value, (str, int, float, type(None))):
                    sanitized_metadata[key] = value
                elif isinstance(value, (dict, list)):
                    # Convert complex types to JSON string
                    sanitized_metadata[key] = json.dumps(value)
                else:
                    # Convert other types to string
                    sanitized_metadata[key] = str(value)
            
            llama_doc = LlamaDocument(
                text=doc.content,
                metadata=sanitized_metadata
            )
            llama_docs.append(llama_doc)

        # Create LlamaIndex ChromaVectorStore
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # Select splitter based on config
        transformations = []
        
        # We will construct the pipeline dynamically
        
        # Create Vector Store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        nodes_to_process = []
        
        if chunk_config.splitter_type == SplitterType.SEMANTIC:
             try:
                from src.core.resource_manager import BatchSemanticSplitter
                logger.info("Using Semantic Splitting...")
                splitter = BatchSemanticSplitter(
                    embed_model=embeddings,
                    buffer_size=chunk_config.semantic_buffer_size,
                    similarity_threshold=chunk_config.semantic_similarity_threshold
                )
                # Split manually first
                # We need to run this async
                nodes_to_process = await splitter.split_nodes(llama_docs)
                
                # Pipeline now only needs Embeddings + Storage
                pipeline = IngestionPipeline(
                    transformations=[embeddings],
                    vector_store=vector_store
                )
                
                progress_manager.set_status(f"Processing {len(nodes_to_process)} semantic chunks...")
                nodes = await pipeline.arun(nodes=nodes_to_process, show_progress=True)
                
             except Exception as e:
                logger.error(f"Semantic splitting failed: {e}. Falling back to SentenceSplitter.")
                # Fallback
                pipeline = IngestionPipeline(
                    transformations=[
                        SentenceSplitter(
                            chunk_size=chunk_config.chunk_size,
                            chunk_overlap=chunk_config.chunk_overlap
                        ),
                        embeddings
                    ],
                    vector_store=vector_store
                )
                nodes = await pipeline.arun(documents=llama_docs, show_progress=True)

        else:
            # Standard Sentence Splitter
            pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(
                        chunk_size=chunk_config.chunk_size,
                        chunk_overlap=chunk_config.chunk_overlap
                    ),
                    embeddings
                ],
                vector_store=vector_store
            )
            nodes = await pipeline.arun(documents=llama_docs, show_progress=True)
        
        logger.info(f"Successfully indexed {len(nodes)} chunks to ChromaDB using {chunk_config.splitter_type.value} strategy")

        # Update BM25 Index (Phase H.1.1)
        progress_manager.set_status(f"Generating BM25 Hybrid Search index for {len(nodes)} chunks...")
        # FIX ISSUE #3: Propagate BM25 failures as warnings to user
        bm25_failed = False
        bm25_error = None
        try:
            from src.core.bm25_index import BM25IndexManager
            bm25_manager = BM25IndexManager(chroma_collection.name)
            # Run in thread to avoid blocking
            await asyncio.to_thread(bm25_manager.add_nodes, nodes)

            # Synchronize BM25 index with actual ChromaDB content to ensure consistency
            await asyncio.to_thread(bm25_manager.update_with_chroma_results, chroma_collection)
        except Exception as e:
            logger.error(f"Failed to update BM25 index: {e}")
            bm25_failed = True
            bm25_error = str(e)

        # Return response with warning if BM25 failed
        response_data = {
            "collection": chroma_collection.name,
            "total_documents": len(documents),
            "indexed_nodes": len(nodes),
            "duplicates_removed": 0
        }

        if bm25_failed:
            response_data["warning"] = "BM25 index update failed - hybrid search degraded to vector-only mode"

        return RAGResponse(
            status=RAGOperationStatus.SUCCESS,
            data=response_data,
            metadata={
                "chunk_size": chunk_config.chunk_size,
                "chunk_overlap": chunk_config.chunk_overlap,
                "chunking_strategy": chunk_config.splitter_type.value,
                "indexing_type": "simple_chunking",
                "bm25_status": "failed" if bm25_failed else "success"
            },
            error=f"BM25 indexing failed: {bm25_error}" if bm25_failed else None
        )

    async def _index_with_parent_child(
        self,
        documents: List[Document],
        chroma_collection,
        parent_chunk_size: int,
        child_chunk_size: int,
        child_chunk_overlap: int
    ) -> RAGResponse:
        """
        Index documents using parent-child strategy (Phase 2).
        
        This implements the dual chunking approach:
        1. Store full parent documents in DocumentStore
        2. Create small child chunks for search precision
        3. Link child chunks to parent documents via metadata
        """
        from llama_index.core.node_parser import SentenceSplitter
        
        # Prepare data for parent document storage and child chunking
        parent_docs_to_store = []
        all_child_nodes = []
        
        for doc in documents:
            # 1. Create parent doc ID and store in DocumentStore
            parent_doc_id = f"parent_{hashlib.sha256(doc.content.encode()).hexdigest()[:16]}"
            
            # Create LlamaDocument for the entire content
            parent_llama_doc = LlamaDocument(
                text=doc.content,
                metadata=doc.metadata
            )
            parent_llama_doc.id_ = parent_doc_id  # Set the ID
            parent_docs_to_store.append((parent_doc_id, parent_llama_doc))
            
            # 2. Create child chunks from the document content
            # Use SentenceSplitter for child chunks
            child_splitter = SentenceSplitter(
                chunk_size=child_chunk_size,
                chunk_overlap=child_chunk_overlap
            )
            
            # Create a temporary document to split
            temp_doc = LlamaDocument(text=doc.content, metadata=doc.metadata)
            child_nodes = child_splitter.get_nodes_from_documents([temp_doc])
            
            # 3. Add parent_doc_id to each child node's metadata
            for node in child_nodes:
                node.metadata["parent_doc_id"] = parent_doc_id
                # Add other identifying metadata
                node.metadata["chunk_type"] = "child"
                node.metadata["source_doc_id"] = doc.doc_id
                
                # Add to collection for vector storage
                all_child_nodes.append(node)

        # 4. Store parent documents in DocumentStore
        if parent_docs_to_store:
            success = self.document_store.mset(parent_docs_to_store)
            if not success:
                logger.error("Failed to store parent documents in DocumentStore")
                return RAGResponse(
                    status=RAGOperationStatus.FAILURE,
                    error="Failed to store parent documents in DocumentStore"
                )

        # 5. Store child chunks in ChromaDB
        # Get system-wide defaults from embedding_manager
        manager_config = self.embeddings._load_config()
        embedding_provider = manager_config.get("EMBEDDING_PROVIDER", "ollama")
        embedding_model = manager_config.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
        
        embeddings = self.embeddings.get_embeddings(
            provider=embedding_provider,
            model=embedding_model,
            use_fallback=True
        )

        if not embeddings:
            return RAGResponse(
                status=RAGOperationStatus.FAILURE,
                error=f"Failed to initialize embeddings: {embedding_provider}:{embedding_model}"
            )

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        pipeline = IngestionPipeline(
            transformations=[embeddings],  # Embed the nodes
            vector_store=vector_store
        )
        
        # Run the pipeline with the child nodes that have parent links
        final_nodes = await pipeline.arun(documents=all_child_nodes, show_progress=True)

        # Update BM25 Index for parent-child indexing as well
        progress_manager.set_status(f"Generating BM25 Hybrid Search index for {len(final_nodes)} child chunks...")
        bm25_failed = False
        bm25_error = None
        try:
            from src.core.bm25_index import BM25IndexManager
            bm25_manager = BM25IndexManager(chroma_collection.name)
            # Run in thread to avoid blocking
            await asyncio.to_thread(bm25_manager.add_nodes, final_nodes)

            # Synchronize BM25 index with actual ChromaDB content to ensure consistency
            await asyncio.to_thread(bm25_manager.update_with_chroma_results, chroma_collection)
        except Exception as e:
            logger.error(f"Failed to update BM25 index for parent-child indexing: {e}")
            bm25_failed = True
            bm25_error = str(e)

        # Prepare response data
        response_data = {
            "collection": chroma_collection.name,
            "total_documents": len(documents),
            "parent_documents_stored": len(parent_docs_to_store),
            "child_chunks_indexed": len(final_nodes),
        }

        if bm25_failed:
            response_data["warning"] = "BM25 index update failed - hybrid search degraded to vector-only mode"

        # Return success response
        return RAGResponse(
            status=RAGOperationStatus.SUCCESS,
            data=response_data,
            metadata={
                "parent_chunk_size": parent_chunk_size,
                "child_chunk_size": child_chunk_size,
                "child_chunk_overlap": child_chunk_overlap,
                "indexing_type": "parent_child",
                "bm25_status": "failed" if bm25_failed else "success"
            },
            error=f"BM25 indexing failed: {bm25_error}" if bm25_failed else None
        )

    async def _document_exists_in_collection(
        self,
        doc_hash: str,
        collection_name: str
    ) -> bool:
        """Check if document hash exists in collection"""
        try:
            client = await self.chroma.get_client_async()
            if not client:
                logger.warning("ChromaDB client not available")
                return False

            collection = await asyncio.to_thread(
                client.get_collection,
                collection_name
            )

            # Query by metadata hash
            results = await asyncio.to_thread(
                collection.get,
                where={"doc_hash": doc_hash},
                limit=1
            )

            return len(results["ids"]) > 0

        except Exception as e:
            logger.warning(f"Failed to check document existence: {e}")
            return False

    def _compute_document_hash(self, content: str) -> str:
        """Compute stable hash for document content"""
        # Normalize content before hashing
        normalized = content.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _chunk_documents(
        self,
        documents: List[Document],
        config: ChunkConfig
    ) -> List[Dict[str, Any]]:
        """
        Split documents into chunks with overlap.
        """
        chunks = []

        for doc in documents:
            doc_chunks = self._chunk_text(doc.content, config)

            for i, chunk_text in enumerate(doc_chunks):
                chunk_metadata = {
                    **doc.metadata,
                    "doc_hash": self._compute_document_hash(doc.content),
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks),
                    "indexed_at": datetime.now().isoformat()
                }

                chunk_id = f"{doc.doc_id}_chunk_{i}"

                chunks.append({
                    "id": chunk_id,
                    "content": chunk_text,
                    "metadata": chunk_metadata
                })

        return chunks

    def _chunk_text(
        self,
        text: str,
        config: ChunkConfig
    ) -> List[str]:
        """
        Split text into chunks with separators.
        """
        chunks = []
        current_chunk = ""

        # Split by separators in order
        for separator in config.separators:
            if separator in text:
                splits = text.split(separator)

                for split in splits:
                    if len(current_chunk) + len(split) <= config.chunk_size:
                        current_chunk += split + separator
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())

                        # Start new chunk with overlap
                        if chunks and config.chunk_overlap > 0:
                            overlap_text = chunks[-1][-config.chunk_overlap:]
                            current_chunk = overlap_text + split + separator
                        else:
                            current_chunk = split + separator

                break

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    async def delete_document(
        self,
        doc_id: str,
        collection_name: str
    ) -> RAGResponse:
        """Delete all chunks of a document from collection"""
        try:
            client = await self.chroma.get_client_async()
            if not client:
                return RAGResponse(
                    status=RAGOperationStatus.FAILURE,
                    error="ChromaDB client not available"
                )

            collection = await asyncio.to_thread(
                client.get_collection,
                collection_name
            )

            # Find all chunks with this doc_id prefix
            results = await asyncio.to_thread(
                collection.get,
                where={"or": [
                    {"doc_hash": doc_id},
                    # Also match by ID prefix (legacy)
                ]},
                include=["metadatas"]
            )

            chunk_ids = results["ids"]

            if not chunk_ids:
                return RAGResponse(
                    status=RAGOperationStatus.FAILURE,
                    error=f"Document {doc_id} not found in collection"
                )

            # Delete chunks
            await asyncio.to_thread(
                collection.delete,
                ids=chunk_ids
            )

            logger.info(f"Deleted {len(chunk_ids)} chunks for document {doc_id}")

            return RAGResponse(
                status=RAGOperationStatus.SUCCESS,
                data={
                    "doc_id": doc_id,
                    "chunks_deleted": len(chunk_ids)
                }
            )

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return RAGResponse(
                status=RAGOperationStatus.FAILURE,
                error=str(e)
            )
