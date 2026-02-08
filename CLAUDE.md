# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClawRAG is a production-ready RAG (Retrieval Augmented Generation) engine designed as the long-term memory for autonomous agents. It provides document ingestion, vector storage, and hybrid search capabilities via a FastAPI backend and ChromaDB vector database.

**Key Architecture**: Extracted from "Mail Modul Alpha" and simplified to focus exclusively on RAG functionality. No email, statistics, or analytics modules remain.

## Development Commands

### Docker (Recommended)

```bash
# Start all services (nginx gateway, backend, ChromaDB via systemd)
docker compose up -d

# View backend logs
docker compose logs -f backend

# Restart backend (after code changes - hot-reload enabled)
docker compose restart backend

# Stop all services
docker compose down

# Rebuild (only when dependencies change in requirements.txt)
docker compose down
docker compose up -d --build
```

### Local Development (without Docker)

```bash
cd backend
pip install -r requirements.txt

# Start backend directly
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

**Note**: Requires ChromaDB and Ollama running separately when not using Docker.

### Testing & Verification

```bash
# Health check
curl http://localhost:8080/health

# API documentation (Swagger UI)
open http://localhost:8080/docs

# Test Ollama connection from within container
docker exec self-hosting-kit-backend curl http://host.docker.internal:11434/api/tags
```

### MCP Server (Model Context Protocol)

```bash
cd mcp-server

# Build TypeScript
npm run build

# Development mode
npm run dev

# Production mode
npm start
```

## Critical Architecture Patterns

### Singleton Pattern: ChromaManager

**Location**: `backend/src/core/chroma_manager.py`

**Why**: Prevents multiple ChromaDB client instances which cause unclosed connections and port blocking during shutdown.

**Implementation**:
- Global `_chroma_manager_instance` accessed via `get_chroma_manager()`
- Single connection initialized during FastAPI lifespan startup
- Properly closed during FastAPI lifespan shutdown
- Includes circuit breaker and retry logic for resilience

**Usage**: Always use `get_chroma_manager()` - never instantiate `ChromaManager()` directly.

### FastAPI Lifespan Management

**Location**: `backend/src/main.py`

**Critical Sequence**:
1. **Startup**: Configure ChromaManager → Test connection → Start serving
2. **Shutdown**: Close ChromaManager → Clean up resources

**Why**: Prevents CLOSE_WAIT connections and ensures clean shutdown.

### Hot-Reload Development

**Setup**: Source code mounted as volume in `docker-compose.yml`:
```yaml
volumes:
  - ./backend/src:/app/src:ro  # Hot-reload enabled
```

**Behavior**: Code changes in `backend/src/` automatically trigger reload - no rebuild required.

**When to rebuild**:
- Changes to `requirements.txt`
- Changes to `Dockerfile`
- Changes outside `/src` directory

### Resilience Patterns

**Circuit Breaker**: Prevents cascading failures when ChromaDB is unavailable
- Location: `backend/src/core/circuit_breaker.py`
- Auto-recovers after timeout

**Retry Policy**: Exponential backoff with jitter for ChromaDB operations
- Location: `backend/src/core/retry_policy.py`

## Core Components & Data Flow

### Document Ingestion Flow

1. **API Entry**: `POST /api/v1/rag/documents/upload` (file upload) or `POST /api/v1/rag/ingestion/ingest-folder` (bulk)
2. **Document Processing**: `DoclingService` (`backend/src/services/docling_service.py`)
   - Converts PDF/DOCX/PPTX/XLSX/HTML/Markdown to text
   - Uses Docling 2.13.0 for advanced document parsing
3. **Chunking**: Text split into chunks (default: 512 tokens, 128 overlap)
4. **Embedding**: Generated via Ollama (`nomic-embed-text`) or cloud providers
5. **Storage**: ChromaDB collection via `ChromaManager`

### Query Flow

1. **API Entry**: `POST /api/v1/rag/query`
2. **Query Engine**: `backend/src/core/query_engine.py`
   - Generates query embedding
   - Executes hybrid search (vector + BM25)
3. **Retrievers**: `backend/src/core/retrievers/`
   - `hybrid_retriever.py`: Combines vector and keyword search
   - `bm25_retriever.py`: Keyword-based retrieval
   - `reranker.py`: Optional cross-encoder reranking (Professional Edition)
4. **LLM Generation**: Context + query → LLM → response with citations
5. **Response**: JSON with `answer` and `sources`

### Collection Management

**Registry**: `backend/src/core/collection_registry.py`
- Singleton tracking all collections
- Metadata storage in ChromaDB metadata tables

**Manager**: `backend/src/core/collection_manager.py`
- CRUD operations for collections
- Domain-based classification (uses `rag_domains.json`)

## Configuration

### Environment Variables (.env)

**Critical for rootless Docker**:
- `OLLAMA_HOST`: If `host.docker.internal` fails, use actual host IP (e.g., `http://192.168.1.100:11434`)
- `DOCS_DIR`: Absolute path on host, mounted as `/host_root` in container

**LLM Configuration**:
- `LLM_PROVIDER`: `ollama`, `openai`, `anthropic`, `gemini`
- `LLM_MODEL`: Model name (e.g., `llama3:latest`, `gpt-4o`)
- Context window limited to 8192 tokens in code to prevent OOM on 8GB VRAM GPUs

**Embedding Configuration**:
- `EMBEDDING_PROVIDER`: Usually matches `LLM_PROVIDER`
- `EMBEDDING_MODEL`: `nomic-embed-text` for Ollama

### Multi-LLM Support

**Location**: `backend/src/core/config.py`

Supports:
- **Ollama** (default): Local inference via `llama-index-llms-ollama`
- **OpenAI**: Set `OPENAI_API_KEY` in environment
- **Anthropic**: Set `ANTHROPIC_API_KEY` in environment
- **Gemini**: Set `GOOGLE_API_KEY` in environment

## Rootless Docker Constraints

**CRITICAL**: This system is designed for rootless Docker environments.

**Constraints**:
- `user: "0:0"` in `docker-compose.yml` is INCOMPATIBLE with rootless Docker
- Host socket mounts may fail due to user namespace mapping
- `host.docker.internal` may not work - use actual host IP if needed

**Verification**:
```bash
# From container, test Ollama connection
docker exec self-hosting-kit-backend curl http://YOUR_HOST_IP:11434/api/tags
```

## Debugging Common Issues

### "Failed to connect to ChromaDB"

**Check**:
1. ChromaDB systemd service running: `systemctl --user status chroma.service`
2. Container can reach ChromaDB: `docker exec self-hosting-kit-backend curl http://chroma_running:8000/api/v1/heartbeat`

**Fix**: Verify `CHROMA_HOST` and `CHROMA_PORT` in `.env` match systemd service configuration

### "Failed to connect to Ollama"

**Check**:
1. Ollama running: `curl http://localhost:11434/api/tags`
2. Container can reach host: `docker exec self-hosting-kit-backend curl http://host.docker.internal:11434/api/tags`

**Fix (rootless Docker)**:
```bash
# Find host IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Update .env
OLLAMA_HOST=http://YOUR_HOST_IP:11434

# Restart
docker compose restart backend
```

### Folder Ingestion Finds No Files

**Symptom**: `POST /api/v1/rag/ingestion/ingest-folder` with `folder_path: /host_root` returns 0 files

**Check**:
```bash
# Verify DOCS_DIR in .env points to existing directory
cat .env | grep DOCS_DIR

# Check what's mounted in container
docker exec self-hosting-kit-backend ls -la /host_root/
```

**Fix**:
1. Set `DOCS_DIR=/path/to/your/documents` in `.env`
2. Restart: `docker compose restart backend`
3. Use `/host_root` or `/host_root/subfolder` in API calls

### Import Errors After Code Changes

**Symptom**: Hot-reload fails with import errors

**Fix**:
```bash
# Restart backend to reload Python modules
docker compose restart backend
```

## Testing Strategy

**Unit Tests**: None currently - this is a self-hosting kit extraction
**Integration Testing**: Use Swagger UI at `/docs` for manual testing
**Health Check**: `/health` endpoint verifies ChromaDB connectivity

## Code Locations Reference

**API Endpoints**:
- `backend/src/api/v1/rag/collections.py` - Collection CRUD
- `backend/src/api/v1/rag/query.py` - RAG queries
- `backend/src/api/v1/rag/documents/*.py` - Document upload/management
- `backend/src/api/v1/rag/ingestion/*.py` - Folder scanning, batch ingestion

**Core Logic**:
- `backend/src/core/chroma_manager.py` - ChromaDB singleton (CRITICAL)
- `backend/src/core/query_engine.py` - Query execution with multi-collection support
- `backend/src/core/docling_loader.py` - Document parsing (Docling integration)
- `backend/src/core/retrievers/` - Hybrid, BM25, parent-document, reranker

**Services**:
- `backend/src/services/docling_service.py` - Central document processing
- `backend/src/services/ingest_v2/pipeline.py` - Ingestion pipeline
- `backend/src/services/classification.py` - Document classification (heuristic)

**Configuration**:
- `backend/src/core/config.py` - Multi-LLM configuration factory
- `backend/src/core/feature_limits.py` - Edition tiers (Community/Professional/Enterprise)
- `backend/src/core/rag_domains.json` - Domain classification rules

## Performance Considerations

**Context Window Limit**: 8192 tokens hardcoded in `config.py` to prevent OOM on 8GB VRAM GPUs (Llama 3.1's 128k context would require >10GB)

**Batch Size**: `INGEST_BATCH_SIZE` controls parallel document processing - adjust based on available RAM

**Caching**: Docling cache mounted as volume (`docling_cache`) - persists across container restarts

## Security Notes

**No Authentication**: Community Edition has no auth layer - add reverse proxy auth if exposing publicly

**API Keys**: Never commit `.env` - use `.env.example` as template

**CORS**: Disabled in production (nginx handles routing) - only enabled in DEBUG mode

## MCP Integration (OpenClaw)

**MCP Server**: `mcp-server/` directory contains TypeScript implementation

**Tools Exposed**:
- `query_knowledge`: Query RAG collections from WhatsApp/Telegram/Discord
- `list_collections`: Discover available knowledge bases

**Installation in OpenClaw**:
```bash
openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
```

**Configuration**: Set `CLAWRAG_API_URL` environment variable if not using default `http://localhost:8080`
