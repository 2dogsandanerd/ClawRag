"""
RAG API Router Package.

This package combines all RAG-related endpoints:
- Query: RAG knowledge base queries
- Collections: Collection management (CRUD)
- Documents: Document upload, retrieval, deletion
- Ingestion: Advanced Docling-based ingestion (Phase 4)
"""

from fastapi import APIRouter

from .collections import router as collections_router
from .documents import router as documents_router
from .query import router as query_router
from .ingestion import router as ingestion_router
from .cockpit import router as cockpit_router # Import cockpit router
from .chunking_strategies import router as chunking_strategies_router
from .chunking_comparison import router as chunking_comparison_router

# Main RAG router that combines all sub-routers
router = APIRouter()

# Include all sub-routers
router.include_router(query_router, tags=["RAG Query"])
router.include_router(cockpit_router, tags=["RAG Cockpit"]) # Include cockpit router
router.include_router(collections_router, tags=["RAG Collections"])
router.include_router(documents_router, tags=["RAG Documents"])
router.include_router(ingestion_router, tags=["RAG Ingestion (Phase 4)"])
router.include_router(chunking_strategies_router)
router.include_router(chunking_comparison_router)

__all__ = ["router"]
