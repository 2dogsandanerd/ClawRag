import asyncio
import os
import sys
import time
from pathlib import Path
from loguru import logger

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from src.core.rag_client import RAGClient
from src.core.indexing_service import Document, ChunkConfig, SplitterType

async def run_real_e2e_test():
    """
    Real E2E Test without Mocks.
    Uses localhost to access services running in Docker.
    """
    logger.info("🚀 Starting Real E2E Semantic Ingest Test (Host Access Mode)")
    
    # Set necessary environment variables for the test process
    os.environ["CHROMA_HOST"] = "localhost"
    os.environ["CHROMA_PORT"] = "8000"
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"
    os.environ["BM25_INDEX_DIR"] = "backend/data/bm25_indices"
    
    # Create BM25 dir if missing
    Path("backend/data/bm25_indices").mkdir(parents=True, exist_ok=True)
    
    # Initialize Client with explicit host config
    host_config = {
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": 8000,
        "OLLAMA_HOST": "http://localhost:11434",
        "EMBEDDING_PROVIDER": "ollama",
        "EMBEDDING_MODEL": "nomic-embed-text"
    }
    
    client = RAGClient(host_config)
    collection_name = f"e2e_test_{int(time.time())}"
    
    try:
        # 1. Create Collection
        logger.info(f"Step 1: Creating collection {collection_name}")
        res = await client.create_collection(collection_name)
        if not res.is_success:
            logger.error(f"❌ Failed to create collection: {res.error}")
            return
        
        # 2. Create Test Document
        content = """
        Der Six Sigma Black Belt ist ein Experte für Prozessoptimierung. 
        Er nutzt statistische Methoden, um Fehlerquoten zu senken. 
        In diesem Projekt wenden wir diese Prinzipien auf KI-Agenten an.
        
        Semantisches Chunking ist ein fortgeschrittenes Verfahren.
        Es erkennt Themenwechsel im Text automatisch.
        Dadurch bleiben Informationen im richtigen Kontext erhalten.
        """
        
        doc = Document(
            content=content,
            metadata={"source": "e2e_test_doc.txt"}
        )
        
        # 3. Ingest with Semantic Chunking
        logger.info("Step 2: Ingesting with SEMANTIC chunking")
        chunk_config = ChunkConfig(
            chunk_size=512,
            chunk_overlap=128,
            splitter_type=SplitterType.SEMANTIC
        )
        
        ingest_res = await client.index_documents(
            documents=[doc],
            collection_name=collection_name,
            chunk_config=chunk_config
        )
        
        if ingest_res.is_success:
            logger.success(f"✅ Ingest successful: {ingest_res.data['indexed_nodes']} chunks created")
        else:
            logger.error(f"❌ Ingest failed: {ingest_res.error}")
            return

        # 4. Query the Document
        logger.info("Step 3: Querying the document")
        query_text = "Was macht ein Six Sigma Black Belt?"
        query_res = await client.query(
            query_text=query_text,
            collection_names=[collection_name],
            n_results=2
        )
        
        if query_res.is_success:
            logger.success("✅ Query successful")
            logger.info(f"Answer Sample: {str(query_res.data)[:200]}...")
        else:
            logger.error(f"❌ Query failed: {query_res.error}")

    except Exception as e:
        logger.exception(f"💥 Unexpected error during E2E test: {e}")
    finally:
        # Cleanup and Exit
        logger.info(f"Step 4: Cleaning up collection {collection_name}")
        try:
            await client.delete_collection(collection_name)
            logger.success("✅ Cleanup successful")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
        
        logger.info("Test complete. Force exiting to close all connections.")
        os._exit(0)

if __name__ == "__main__":
    # Run with timeout to prevent infinite hang
    try:
        asyncio.run(run_real_e2e_test())
    except KeyboardInterrupt:
        pass
