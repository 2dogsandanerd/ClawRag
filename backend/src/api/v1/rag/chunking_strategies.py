from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

from src.api.v1.rag.models.ingestion import ChunkingStrategy

router = APIRouter(prefix="/chunking", tags=["RAG Chunking Strategies"])

class StrategyRecommendationRequest(BaseModel):
    """Request for strategy recommendation based on document characteristics."""
    document_type: str = Field(description="Document type (pdf, docx, html, etc.)")
    document_size: int = Field(description="Document size in bytes")
    content_preview: Optional[str] = Field(default=None, max_length=1000, description="First 1000 chars of document")

class StrategyRecommendationResponse(BaseModel):
    """Response with recommended chunking strategy."""
    recommended_strategy: ChunkingStrategy
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation")
    reasoning: str = Field(description="Explanation for the recommendation")
    performance_impact: str = Field(description="Expected performance impact (fast, medium, slow)")

class StrategyCapabilitiesResponse(BaseModel):
    """Response with available chunking strategies and their capabilities."""
    strategies: List[Dict[str, Any]]
    
strategies_info = {
    ChunkingStrategy.SENTENCE: {
        "name": "Sentence-based Chunking",
        "description": "Traditional chunking based on sentence boundaries and fixed sizes",
        "speed": "fast",
        "quality": "medium",
        "best_for": ["structured documents", "short texts", "high volume processing"],
        "requires_embeddings": False
    },
    ChunkingStrategy.SEMANTIC: {
        "name": "Semantic Chunking",
        "description": "Intelligent chunking based on semantic similarity and meaning preservation",
        "speed": "slow",
        "quality": "high",
        "best_for": ["long documents", "technical content", "accuracy-critical applications"],
        "requires_embeddings": True
    },
    ChunkingStrategy.CODE: {
        "name": "Code-aware Chunking",
        "description": "Chunking optimized for source code with syntax awareness",
        "speed": "medium",
        "quality": "high",
        "best_for": ["source code", "scripts", "programming documentation"],
        "requires_embeddings": False
    },
    ChunkingStrategy.ROW_BASED: {
        "name": "Row-based Chunking",
        "description": "Chunking optimized for tabular data and structured text",
        "speed": "fast",
        "quality": "high",
        "best_for": ["CSV files", "spreadsheets", "tabular data"],
        "requires_embeddings": False
    }
}

@router.get("/strategies", response_model=StrategyCapabilitiesResponse)
async def get_available_strategies():
    """Get information about all available chunking strategies."""
    strategies_list = []
    for strategy, info in strategies_info.items():
        info_copy = info.copy()
        info_copy["value"] = strategy.value
        strategies_list.append(info_copy)
    
    return StrategyCapabilitiesResponse(strategies=strategies_list)

@router.post("/recommend", response_model=StrategyRecommendationResponse)
async def recommend_strategy(request: StrategyRecommendationRequest):
    """Get a recommended chunking strategy based on document characteristics."""
    # Basis-Empfehlung basierend auf Dokumententyp
    recommendations = {
        "pdf": ChunkingStrategy.SEMANTIC,
        "docx": ChunkingStrategy.SEMANTIC,
        "html": ChunkingStrategy.SEMANTIC,
        "md": ChunkingStrategy.SEMANTIC,
        "txt": ChunkingStrategy.SEMANTIC,
        "csv": ChunkingStrategy.ROW_BASED,
        "py": ChunkingStrategy.CODE,
        "js": ChunkingStrategy.CODE,
        "java": ChunkingStrategy.CODE,
        "cpp": ChunkingStrategy.CODE,
        "cs": ChunkingStrategy.CODE,
        "eml": ChunkingStrategy.SEMANTIC,
    }
    
    # Normalize doc type (remove dot if present)
    doc_type = request.document_type.lower().lstrip('.')
    
    strategy = recommendations.get(doc_type, ChunkingStrategy.SEMANTIC)
    
    # Verfeinere Empfehlung basierend auf Größe
    # < 10KB
    if request.document_size < 10 * 1024:
        # Für kleine Dokumente reicht Satz-basiert, es sei denn es ist Code
        if strategy != ChunkingStrategy.CODE and strategy != ChunkingStrategy.ROW_BASED:
             strategy = ChunkingStrategy.SENTENCE
             confidence = 0.8
             reasoning = "Small document (<10KB) - sentence chunking sufficient and faster"
        else:
             confidence = 0.9
             reasoning = f"Small {doc_type} document - {strategy.value} chunking recommended for structure"
             
    # > 10MB
    elif request.document_size > 10 * 1024 * 1024:
        # Für sehr große Dokumente empfehlen wir semantisch, da Qualität wichtiger ist
        # Aber Achtung: Performance!
        # Eigentlich Semantic Chunking auf 10MB ist SEHR teuer. 
        # Vielleicht warnen? Oder Semantic empfehlen weil es besser navigator ist?
        # Bleiben wir bei Semantic für Qualität
        strategy = ChunkingStrategy.SEMANTIC
        confidence = 0.9
        reasoning = "Large document (>10MB) - semantic chunking recommended for better context preservation"
    else:
        # Medium size
        confidence = 0.7
        if strategy == ChunkingStrategy.SEMANTIC:
            reasoning = "Medium-sized document - semantic chunking provides better quality"
        else:
            reasoning = f"Document type {doc_type} typically benefits from {strategy.value} chunking"
    
    # Leistungseinfluss bestimmen
    speed_rating = strategies_info.get(strategy, {}).get("speed", "medium")
    performance_map = {
        "fast": "minimal (under 2x slowdown)",
        "medium": "moderate (2-5x slowdown)", 
        "slow": "significant (5x+ slowdown)"
    }
    performance_impact = performance_map.get(speed_rating, "unknown")
    
    return StrategyRecommendationResponse(
        recommended_strategy=strategy,
        confidence=confidence,
        reasoning=reasoning,
        performance_impact=performance_impact
    )
