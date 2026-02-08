# ClawRAG - The Brain for OpenClaw

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/2dogsandanerd/ClawRag/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)

**The Cognitive Core for Autonomous Agents.**

ClawRAG is a production-ready, self-hosted RAG engine designed to serve as the long-term memory ("The Brain") for agents like **OpenClaw**. It decouples intelligence from action, providing a robust API for document ingestion and retrieval.

---

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** installed
2. No additional setup required - everything runs in containers!

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/2dogsandanerd/ClawRag.git
cd ClawRag

# 2. Copy the example environment file
cp .env.example .env

# 3. Start the services
docker compose up -d

# 4. Check health
curl http://localhost:8080/health

# 5. Open the application
open http://localhost:8080
```

### Services (all through single nginx gateway):
- Frontend UI: http://localhost:8080/
- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health
- API Endpoints: http://localhost:8080/api/v1/rag/*

---

## ⚙️ Configuration

All configuration is done through the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | External port for nginx gateway |
| `DOCS_DIR` | `./data/docs` | Host directory to mount as `/host_root` for folder ingestion |
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama, openai, anthropic, gemini, openai_compatible) |
| `LLM_MODEL` | `llama3:latest` | Model name for selected provider |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding provider (usually matches LLM) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `CHUNK_SIZE` | `512` | Size of text chunks for ingestion |
| `CHUNK_OVERLAP` | `128` | Overlap between chunks |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |

### LLM Provider Configuration

#### 1. Ollama (Default) - Container
Perfect for privacy and offline usage. Everything runs in containers.

**Configuration in `.env`:**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3:latest  # or any model you want to use
EMBEDDING_MODEL=nomic-embed-text
```

The system includes an Ollama container that shares models with the host if available.

#### 2. Cloud Models (OpenAI, Anthropic, Gemini)
For maximum reasoning power.

**Configuration in `.env`:**
```bash
# Example for OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-proj-...
```

#### 3. Local AI Servers (LM Studio, Llama.cpp, Koboldcpp, etc.)
For users who prefer local AI servers that offer an OpenAI-compatible API.

**Configuration in `.env`:**
```bash
# Example for LM Studio or similar OpenAI-compatible server
LLM_PROVIDER=openai_compatible
LLM_MODEL=your-local-model-name
OPENAI_BASE_URL=http://host.docker.internal:1234/v1  # Adjust to your server's address
```

---

## 📁 Document Ingestion

### Single File Upload
Upload documents directly through the web UI or API.

### Folder Ingestion
Bulk document processing with real-time progress tracking.

**Configuration:**
1. Set `DOCS_DIR=/path/to/your/documents` in `.env`
2. Restart: `docker compose restart backend`
3. Use `/host_root` in the UI (your DOCS_DIR is mounted here)

---

## 🔍 Search Capabilities

The system provides hybrid search combining:
- **Vector Search**: Semantic similarity using embeddings
- **BM25 Search**: Keyword-based search for exact term matching
- **Results are combined using Reciprocal Rank Fusion (RRF)**

---

## 🛠️ Using the API

### Python Example

```python
import requests

BASE_URL = "http://localhost:8080/api/v1/rag"

# 1. Create a collection
response = requests.post(
    f"{BASE_URL}/collections",
    files={
        "collection_name": (None, "my_knowledge"),
        "embedding_provider": (None, "ollama"),
        "embedding_model": (None, "nomic-embed-text")
    }
)
print(f"Collection created: {response.json()}")

# 2. Upload documents
with open("document.pdf", "rb") as f:
    response = requests.post(
    f"{BASE_URL}/documents/upload",
    files={"files": f},
    data={
        "collection_name": "my_knowledge",
        "chunk_size": 512,
        "chunk_overlap": 128
    }
)
print(f"Upload status: {response.json()}")

# 3. Query the knowledge base
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "What are the main topics?",
        "collection": "my_knowledge",
        "k": 5
    }
)
result = response.json()
print(f"Answer: {result.get('answer')}")
print(f"Sources: {len(result.get('sources', []))}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# List collections
curl http://localhost:8080/api/v1/rag/collections

# Get collection stats
curl http://localhost:8080/api/v1/rag/collections/my_docs/stats

# Query with specific parameters
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the architecture",
    "collection": "my_docs",
    "k": 10,
    "similarity_threshold": 0.5
  }'

# Delete a collection
curl -X DELETE http://localhost:8080/api/v1/rag/collections/my_docs
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│             FastAPI Backend (Port 8081)         │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ RAG API      │  │ Lifespan Management     │ │
│  │ - Query      │  │ - ChromaDB Connection   │ │
│  │ - Upload     │  │ - Singleton Patterns    │ │
│  └──────┬───────┘  └────────────┬────────────┘ │
└─────────┼──────────────────────┼───────────────┘
          │                      │
          ↓                      ↓
┌─────────────────┐    ┌──────────────────────┐
│  ChromaDB       │    │  Ollama / LLM        │
│  Vector Storage │    │  Embeddings & Chat   │
│  (Port 8001)    │    │  (Port 11434)        │
└─────────────────┘    └──────────────────────┘
```

### Key Components

**Backend (`backend/src/`):**
- `api/v1/rag/` - API endpoints (ingestion, query, collections, documents)
- `core/` - ChromaDB manager, Docling loader, retrievers, query engine
- `services/` - Document processing, classification, generators

**Core Patterns:**
- **Singleton**: ChromaManager for single connection instance
- **Resilience**: Circuit breaker + retry logic for ChromaDB
- **Lifespan**: Proper FastAPI startup/shutdown for clean connections
- **Docker-first**: Everything runs in containers for easy deployment

---

## 📦 What's Included

Everything runs in Docker containers:
- **Backend**: FastAPI application
- **ChromaDB**: Vector database
- **Ollama**: LLM and embedding service
- **Nginx**: Reverse proxy gateway

---

## 🚨 Troubleshooting

### App won't start

```bash
# Check all services
docker compose ps

# View backend logs
docker compose logs backend

# Check ChromaDB connection
docker compose logs chromadb
```

### Folder Ingestion finds no files

```bash
# 1. Check your DOCS_DIR setting in .env
cat .env | grep DOCS_DIR

# 2. Verify the directory exists and has files
ls -la /path/to/your/docs

# 3. Check what's mounted inside container
docker exec clawrag-backend ls -la /host_root/

# 4. If /host_root is empty, DOCS_DIR is wrong or not mounted
# Fix: Update .env DOCS_DIR=/path/to/your/docs
# Then: docker compose restart backend
```

### Folder Ingestion path errors in UI

The UI folder path input must start with `/host_root`. This is automatically pre-filled.

- ✅ Correct: `/host_root` or `/host_root/subfolder`
- ❌ Wrong: `/home/user/Documents` (this won't work - use DOCS_DIR in .env instead)

## ⚙️ Customization Options

### Model Configuration
- Change `LLM_MODEL` in `.env` to use different models
- Adjust `EMBEDDING_MODEL` for different embedding quality/speed trade-offs
- For 8GB VRAM systems, use smaller models like `llama3.2:3b`

### Ingestion Settings
- Modify `CHUNK_SIZE` and `CHUNK_OVERLAP` in `.env` for different chunking strategies
- Adjust `INGEST_BATCH_SIZE` for faster or more memory-efficient ingestion

### Performance Tuning
- Set `DEBUG=false` in production for better performance
- Adjust `LOG_LEVEL` to reduce logging overhead in production

For more detailed customization options, see the [configuration guide](docs/configuration.md) and [customization guide](docs/customization.md).

---

## 📚 API Endpoints

Full API documentation available at http://localhost:8080/docs

**Collections:**
- `POST /api/v1/rag/collections` - Create collection
- `GET /api/v1/rag/collections` - List collections
- `DELETE /api/v1/rag/collections/{name}` - Delete collection

**Documents:**
- `POST /api/v1/rag/documents/upload` - Upload documents
- `GET /api/v1/rag/documents` - List documents
- `DELETE /api/v1/rag/documents/{id}` - Delete document

**Query:**
- `POST /api/v1/rag/query` - Query knowledge base

**Ingestion:**
- `POST /api/v1/rag/ingestion/scan-folder` - Scan folder for documents
- `POST /api/v1/rag/ingestion/ingest-batch` - Batch ingestion
- `POST /api/v1/rag/ingestion/ingest-folder` - Ingest folder synchronously

---

## 🤝 Contributing

Contributions welcome! This is the Community Edition - we encourage:

- 🐛 Bug reports and fixes
- 📝 Documentation improvements
- 💡 Feature suggestions
- ⚡ Performance optimizations

---

## 📄 License

MIT License - Free use in commercial and open-source projects.

Copyright (c) 2025 2dogsandanerd (ClawRAG Community Edition)