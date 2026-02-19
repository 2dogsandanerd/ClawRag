"""Ingestion and upload models."""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from enum import Enum

class FilePreview(BaseModel):
    """Preview info for uploaded file before ingestion."""
    filename: str
    size_bytes: int
    mime_type: str
    preview_text: str = Field(..., max_length=500, description="First 500 chars of text")
    page_count: Optional[int] = None
    detected_language: Optional[str] = None


class AnalyzeFilesRequest(BaseModel):
    """Request to analyze files before ingestion."""
    files: List[str] = Field(..., description="List of file paths or base64-encoded content")


class AnalyzeFilesResponse(BaseModel):
    """Response with file analysis results."""
    previews: List[FilePreview]
    total_size_bytes: int
    estimated_chunks: int


class ChunkingStrategy(str, Enum):
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    CODE = "code"
    ROW_BASED = "row_based"

class ProcessOptions(BaseModel):
    """Options for document processing and chunking."""
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Size of text chunks in characters")
    chunk_overlap: int = Field(default=200, ge=0, description="Overlap between chunks in characters")
    chunking_strategy: ChunkingStrategy = Field(default=ChunkingStrategy.SENTENCE, description="Strategy for document chunking")
    # Specific parameters for semantic chunking
    semantic_buffer_size: Optional[int] = Field(default=1024, ge=100, le=2048, description="Minimum buffer size for semantic splitting")
    semantic_similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold for semantic splitting")
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, values) -> int:
        """Validate that chunk_overlap is less than chunk_size."""
        # Pydantic v2: values is a ValidationInfo object or dict depending on mode
        # In field_validator, we can use the 'values' dict if it's available
        if hasattr(values, 'data') and "chunk_size" in values.data:
            chunk_size = values.data["chunk_size"]
            if v >= chunk_size:
                raise ValueError("chunk_overlap must be less than chunk_size")
        return v

class FileAssignment(BaseModel):
    """Assignment of a file to a collection."""

    file: str = Field(
        ...,
        description="Full file path to process"
    )
    collection: str = Field(
        ...,
        description="Target ChromaDB collection name"
    )
    process_options: Optional[ProcessOptions] = Field(
        default_factory=ProcessOptions,
        description="Options for document processing and chunking"
    )

    @field_validator("file")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate that file path exists and is readable."""
        path = Path(v)

        if not path.exists():
            raise ValueError(f"File does not exist: {v}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")

        # Check file extension
        allowed_extensions = {
            '.pdf', '.docx', '.pptx', '.xlsx',
            '.html', '.md', '.csv', '.txt',
            '.eml', '.mbox', '.py', '.js', '.java', '.cs', '.cpp', '.h', '.hpp'
        }

        if path.suffix.lower() not in allowed_extensions:
            raise ValueError(
                f"Unsupported file type: {path.suffix}. "
                f"Allowed: {allowed_extensions}"
            )

        return v

class ScanFolderRequest(BaseModel):
    """Request to scan a folder for Docling-compatible files."""
    folder_path: str
    recursive: bool = Field(default=True, description="Scan subdirectories recursively")
    max_depth: int = Field(default=10, ge=1, le=20, description="Maximum recursion depth")


class ScanFolderResponse(BaseModel):
    """Response with list of files found in folder scan."""
    files: List[Dict[str, Any]]
    total_files: int
    total_size: int
    summary: Dict[str, int]  # Count by extension


class IngestBatchRequest(BaseModel):
    """Request to ingest multiple files with collection assignments."""

    assignments: List[FileAssignment] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="File-to-collection assignments with individual processing options"
    )
    async_mode: bool = Field(
        default=True,
        description="Process asynchronously in background"
    )
    # New option: global chunking strategy for all files in batch
    default_chunking_strategy: Optional[ChunkingStrategy] = Field(
        default=None,
        description="Default chunking strategy for all assignments (can be overridden per file)"
    )
    # Option for batch-optimized processing
    optimize_for_quality: bool = Field(
        default=False,
        description="Optimize processing for quality (may be slower) - enables semantic chunking by default"
    )

    @model_validator(mode='after')
    def apply_batch_options(self) -> 'IngestBatchRequest':
        """Apply global options to all assignments if they use default strategy."""
        
        target_strategy = self.default_chunking_strategy
        
        # Quality optimization overrides default strategy to semantic
        if self.optimize_for_quality:
            target_strategy = ChunkingStrategy.SEMANTIC
            
        if target_strategy:
            for assignment in self.assignments:
                # Only override if assignment is using default strategy (SENTENCE)
                # or if options were not explicitly provided
                if not assignment.process_options:
                    assignment.process_options = ProcessOptions(chunking_strategy=target_strategy)
                elif assignment.process_options.chunking_strategy == ChunkingStrategy.SENTENCE:
                    assignment.process_options.chunking_strategy = target_strategy
                    
        return self

class IngestionResponse(BaseModel):
    """Response for batch ingestion."""
    success: bool
    processed_files: int = 0
    failed_files: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None  # For async processing
