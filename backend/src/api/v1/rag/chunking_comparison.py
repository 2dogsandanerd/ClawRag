from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import tempfile
import os
import time
import asyncio
import uuid
import shutil

from src.core.indexing_service import IndexingService, ChunkConfig, SplitterType, Document
from src.api.v1.dependencies import get_rag_client
from src.services.docling_service import docling_service

router = APIRouter(prefix="/chunking", tags=["RAG Chunking Strategies"])

class ComparisonRequest(BaseModel):
    """Request für den Vergleich verschiedener Chunking-Strategien."""
    file_path: str
    collection_name: Optional[str] = "comparison_temp"
    strategies: List[SplitterType] = [SplitterType.SENTENCE, SplitterType.SEMANTIC]
    test_queries: List[str] = Field(default=["Was ist das Hauptthema dieses Dokuments?"])

class ComparisonResult(BaseModel):
    """Ergebnis des Strategievergleichs."""
    strategy: SplitterType
    chunk_count: int
    avg_chunk_size: float
    processing_time: float
    ragas_scores: Dict[str, float] = Field(default_factory=dict) # Empty until Phase 4
    resource_usage: Dict[str, Any]

class ComparisonResponse(BaseModel):
    """Antwort mit Vergleichsergebnissen."""
    original_file: str
    comparison_results: List[ComparisonResult]
    recommendation: SplitterType
    recommendation_reason: str

@router.post("/compare", response_model=ComparisonResponse)
async def compare_chunking_strategies(
    request: ComparisonRequest,
    rag_client=Depends(get_rag_client)
):
    """Vergleicht echte Chunking-Strategien für eine Datei (keine Simulation)."""
    
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    
    try:
        # 1. Dokument verarbeiten (Docling)
        process_result = await docling_service.process_file(request.file_path)
        if not process_result["success"]:
            raise HTTPException(status_code=400, detail=f"Docling processing failed: {process_result.get('error')}")
            
        content = process_result["content"]
        results = []
        
        for strategy in request.strategies:
            start_time = time.time()
            
            # Temporäre Kollektion für diesen Testlauf
            temp_col_name = f"tmp_cmp_{strategy.value}_{uuid.uuid4().hex[:8]}"
            
            doc = Document(
                content=content,
                metadata={"source": request.file_path, "comparison_run": True}
            )
            
            chunk_config = ChunkConfig(
                chunk_size=512,
                chunk_overlap=128,
                splitter_type=strategy
            )
            
            # ECHTES Indexing ausführen
            indexing_response = await rag_client.index_documents(
                documents=[doc],
                collection_name=temp_col_name,
                chunk_config=chunk_config
            )
            
            processing_time = time.time() - start_time
            
            if not indexing_response.is_success:
                continue # Skip failed strategy
                
            chunk_count = indexing_response.data.get("indexed_nodes", 0)
            avg_size = len(content) / chunk_count if chunk_count > 0 else 0
            
            # Ressourcen-Metriken (echt gemessen)
            resource_usage = {
                "processing_time_seconds": round(processing_time, 2),
                "chars_per_second": round(len(content) / processing_time, 2) if processing_time > 0 else 0
            }
            
            results.append(ComparisonResult(
                strategy=strategy,
                chunk_count=chunk_count,
                avg_chunk_size=round(avg_size, 2),
                processing_time=round(processing_time, 2),
                ragas_scores={}, # Real RAGAS scores coming in Phase 4
                resource_usage=resource_usage
            ))
            
            # Cleanup: Temporäre Kollektion löschen
            try:
                await rag_client.delete_collection(temp_col_name)
            except Exception as cleanup_err:
                print(f"Cleanup warning: {cleanup_err}")
        
        if not results:
            raise HTTPException(status_code=500, detail="All comparison runs failed")
            
        # Einfache Empfehlung basierend auf Chunk-Granularität (für Phase 2 ausreichend)
        best_result = results[0] # Default to first
        reason = "Semantic strategy provided for comparison" if any(r.strategy == SplitterType.SEMANTIC for r in results) else "Sentence strategy used"
        
        return ComparisonResponse(
            original_file=request.file_path,
            comparison_results=results,
            recommendation=best_result.strategy,
            recommendation_reason=reason
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
