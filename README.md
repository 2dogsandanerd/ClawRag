# ClawRAG - The Brain for OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)

**The Cognitive Core for Autonomous Agents.**

ClawRAG is a production-ready, self-hosted RAG engine designed to serve as the long-term memory ("The Brain") for agents like **OpenClaw**. It decouples intelligence from action, providing a robust API for document ingestion and retrieval.

Extracted from our **Fortress Core V4 (Enterprise Manifest)**. This Community Edition provides the essential cognitive functions for autonomous agents while serving as a gateway to our high-performance enterprise ecosystem.

---

## 🎯 What You Get

- **🔥 Modern Document Processing**: Docling 2.13.0 (PDF, DOCX, PPTX, XLSX, HTML, Markdown)
- **🔍 Hybrid Search**: Vector similarity + BM25 keyword search with Reciprocal Rank Fusion
- **📦 ChromaDB 0.5.23**: Vector storage with connection pooling and health checks
- **🚀 LlamaIndex 0.12.9**: Advanced retrieval pipelines
- **🎛️ Multi-LLM Support**: Ollama (default), OpenAI, Anthropic, Gemini
- 🖥️ **Lightweight UI**: Zero-build, single-file HTML/JS dashboard with live system logs (600px scrollable, no auto-scroll)
- **🐳 Docker-First**: Production-ready deployment with hot-reload support
- **🤖 MCP Integration**: Built-in Model Context Protocol server for [OpenClaw](https://github.com/2dogsandanerd/openclaw)
- **Folder Ingestion**: Bulk document processing with real-time progress tracking

---

## ⚡ Quick Start (5 minutes)

### Prerequisites

1. **Docker & Docker Compose** installed
2. **Ollama** running locally (for embeddings)
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.com/install.sh | sh

   # Start Ollama server
   ollama serve

   # Pull embedding model (in another terminal)
   ollama pull nomic-embed-text
   ```

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/2dogsandanerd/ClawRag.git
cd ClawRag

# 2. Configure & Start
# Run the interactive setup script to set your document folder
./setup.sh

# (Alternative) Manual setup:
# cp .env.example .env
# docker compose up -d

# 4. Check health
curl http://localhost:8080/health
# Expected: {"status":"healthy","chromadb":"connected","collections_count":0}

# 5. Open the application
open http://localhost:8080
```

**Services (all through single nginx gateway):**
- Frontend UI: http://localhost:8080/
- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health
- API Endpoints: http://localhost:8080/api/v1/rag/*

**Port Configuration:**
The application exposes a single port (default: 8080) configured via the `PORT` variable in `.env`. This prevents port conflicts and follows production best practices with nginx as a reverse proxy.

---

## 🧠 Customizing the Brain 

This RAG engine is designed to be the "Brain" for autonomous agents like **OpenClaw (ClawBot)**. You can easily swap the underlying LLM to fit your hardware or intelligence requirements.

### 1. Local Models (Ollama) - Default
Perfect for privacy and offline usage.

**Configuration in `.env`:**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3:latest  # or any model you pulled
OLLAMA_HOST=http://host.docker.internal:11434
```

**⚠️ Hardware Warning (VRAM vs. Context):**
If you run on consumer hardware (e.g., Laptop with 8GB VRAM), massive context windows can crash your GPU.
- **Problem:** Llama 3.1 has a 128k context window. Loading this fully requires >10GB VRAM even for the 8B model.
- **Solution:** We explicitly limit the context window to **8192 tokens** in the code to ensure stability on 8GB cards (RTX 3060/4060).
- **Recommendation:** Use efficient models like `llama3.2:3b` or `llama3:latest` (8B).

**Setup Steps:**
1. Install Ollama on your host.
2. Pull your desired model: `ollama pull llama3`
3. Restart the backend: `docker compose restart backend`

### 2. Cloud Models (OpenAI, Anthropic, Gemini)
For maximum reasoning power (e.g., for complex legal analysis or coding tasks).

**Configuration in `.env`:**
```bash
# Example for OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-proj-...

# Example for Anthropic
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-5-sonnet-20240620
# ANTHROPIC_API_KEY=sk-ant-...
```

Add your API keys to `docker-compose.yml` or export them in your shell before starting.

### 3. Integration with OpenClaw / ClawBot
This system exposes a stateless REST API that serves as the long-term memory for your agents.

**MCP Integration (Recommended):**
The easiest way to connect OpenClaw to ClawRAG is via the Model Context Protocol (MCP):

```bash
# Install the MCP server in OpenClaw
openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
```

**Connector Strategy:**
- **Ingest:** Send crawled data (PDFs, HTML) to `POST /api/v1/rag/documents/upload` or use `POST /api/v1/rag/ingestion/ingest-text` for raw text content.
- **Retrieve:** The bot queries `POST /api/v1/rag/query` to recall information before acting.

---

## 🤖 OpenClaw Integration via MCP

ClawRAG provides native support for OpenClaw integration via the Model Context Protocol (MCP), allowing you to query your knowledge base directly from WhatsApp, Telegram, Discord, and other OpenClaw-supported channels.

### Installation

1. **Start ClawRAG**:
   ```bash
   docker compose up -d
   ```

2. **Install the MCP server in OpenClaw**:
   ```bash
   openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
   ```

3. **(Optional) Configure custom endpoint**:
   If ClawRAG is not running on `http://localhost:8080`, set the environment variable:
   ```bash
   export CLAWRAG_API_URL=http://your-clawrag-instance:8080
   ```

### Available MCP Tools

#### `query_knowledge`
Query your knowledge base from OpenClaw channels:

```
User: "Search knowledge base for: contract terms with Siemens"
OpenClaw: [Calls query_knowledge(query="contract terms with Siemens")]
ClawRAG: "According to Siemens_Contract_2024.pdf, page 12, section 4.2: 'Liability is limited to direct damages up to 10% of contract value.' [Citation: chunk_id: siemens_contract_2024_p12_s42]"
```

#### `list_collections`
Discover available knowledge bases:

```
User: "List available collections"
OpenClaw: [Calls list_collections()]
ClawRAG: "Available Collections:
- contracts (15 documents)
- handbooks (8 documents)
- protocols (23 documents)"
```

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenClaw      │    │   MCP Server     │    │   ClawRAG       │
│   (WhatsApp/    │◄──►│   (stdio)        │◄──►│   (REST API)    │
│   Telegram)     │    │   @clawrag/      │    │                 │
│                 │    │   mcp-server     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
                                            ┌─────────────────┐
                                            │   ChromaDB      │
                                            │   (Vector DB)   │
                                            └─────────────────┘
```

---

## 🚀 Using the API Without Frontend

The Web UI is great for quick testing, but you'll likely want to integrate this into your applications. Here's how to use the API directly:

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

### Folder Ingestion Example

**Important:** Folder ingestion requires configuring `DOCS_DIR` in `.env` to point to your documents directory. This directory is mounted as `/host_root` inside the container.

```bash
# Option 1: Run setup script (recommended)
./setup.sh
# Enter your documents path when prompted: /home/user/Documents

# Option 2: Manually edit .env
# Set: DOCS_DIR=/home/user/Documents
# Then restart: docker compose restart backend
```

```python
import requests
import time

BASE_URL = "http://localhost:8080/api/v1/rag"

# Start folder ingestion
# Use /host_root as the base path (your DOCS_DIR is mounted here)
response = requests.post(
    f"{BASE_URL}/ingest-folder",
    json={
        "folder_path": "/host_root",  # Points to DOCS_DIR from .env
        "collection_name": "my_docs",
        "profile": "documents",
        "recursive": True
    }
)

task_id = response.json()["task_id"]
print(f"Ingestion started: {task_id}")

# Poll for status
while True:
    status = requests.get(f"{BASE_URL}/ingest-status/{task_id}").json()

    if status["status"] == "success":
        progress = status["progress"]
        print(f"✅ Processed {progress['successful_files']}/{progress['total_files']} files")
        print(f"📦 Created {progress['total_chunks']} chunks")
        break
    elif status["status"] == "failed":
        print(f"❌ Failed: {status.get('error_message', 'Unknown error')}")
        break
    elif status["status"] == "processing":
        progress = status["progress"]
        print(f"⏳ Processing: {progress['processed_files']}/{progress['total_files']} files")
        time.sleep(2)
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

### JavaScript/TypeScript Example

```javascript
const BASE_URL = "http://localhost:8080/api/v1/rag";

async function queryKnowledgeBase(question, collection = "my_docs") {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: question,
      collection: collection,
      k: 5
    })
  });

  const result = await response.json();
  return {
    answer: result.answer,
    sources: result.sources
  };
}

// Usage
const result = await queryKnowledgeBase("What is RAG?");
console.log(result.answer);
```

### Full API Documentation

For complete API documentation including all endpoints, parameters, and response schemas:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

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
- **Hot-Reload**: Source code mounted as volume for development

**MCP Server (`mcp-server/`):**
- `@clawrag/mcp-server` - Model Context Protocol server
- `query_knowledge` - MCP tool for knowledge queries
- `list_collections` - MCP tool for collection discovery

---

## 🔧 Configuration

Environment variables configured in `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama, openai, anthropic, gemini) |
| `LLM_MODEL` | `llama3.1:8b-instruct-q4_k_m` | Model name for selected provider |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding provider (usually matches LLM) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama connection URL (set to your Ollama host IP if needed) |
| `CHROMA_HOST` | `chroma_running` | ChromaDB container/service name |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `DOCS_DIR` | `./data/docs` | Host directory to mount as `/host_root` for folder ingestion |
| `PORT` | `8080` | External port for nginx gateway |
| `DEBUG` | `true` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |

**Important Notes:**
- **OLLAMA_HOST**: If `host.docker.internal` doesn't work (rootless Docker), set this to your actual host IP (e.g., `http://192.168.1.100:11434`)
- **DOCS_DIR**: Must be set to an existing directory with your documents for folder ingestion to work
- **ChromaDB**: Expects ChromaDB running as a separate container (see docker-compose.yml for external ChromaDB setup)

**For OpenAI/Anthropic/Gemini:**
Add API keys to `docker-compose.yml`:
```yaml
environment:
  - LLM_PROVIDER=openai
  - OPENAI_API_KEY=sk-...
  - EMBEDDING_PROVIDER=openai
```

---

## 📦 What's Inside

```
.
├── backend/
│   ├── src/
│   │   ├── api/v1/rag/         # RAG endpoints
│   │   │   ├── collections.py  # Collection CRUD
│   │   │   ├── documents/      # Upload, management
│   │   │   ├── query.py        # RAG queries
│   │   │   ├── ingestion/      # Folder scanning, batch processing
│   │   │   └── cockpit.py      # System status
│   │   ├── core/
│   │   │   ├── chroma_manager.py      # ChromaDB singleton
│   │   │   ├── docling_loader.py      # Document parser
│   │   │   ├── query_engine.py        # Query execution
│   │   │   ├── retrievers/            # Hybrid, BM25, reranker
│   │   │   ├── config.py              # Multi-LLM config
│   │   │   └── feature_limits.py      # Edition tiers
│   │   └── services/
│   │       ├── docling_service.py     # Central doc processing
│   │       ├── classification.py      # Doc classification
│   │       └── generators/            # Summaries, configs
│   ├── requirements.txt
│   └── Dockerfile
├── mcp-server/
│   ├── src/
│   │   ├── server.ts            # MCP server implementation
│   │   ├── config.ts            # Configuration management
│   │   └── types.ts             # Type definitions
│   ├── package.json
│   └── README.md                # MCP server documentation
├── frontend/
│   └── index.html              # Zero-build dashboard (Vanilla JS)
├── docker-compose.yml          # Full stack orchestration
├── CLAUDE.md                   # Development guide
└── README.md
```

---

## 🎓 Development

### Local Development (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

**Note:** You'll need ChromaDB and Ollama running separately.

### Docker Development (with hot-reload)

Code changes are automatically detected (source mounted as volume):

```bash
# Edit code in backend/src/
# Changes reflect immediately, no rebuild needed

# View logs
docker compose logs -f backend

# Restart if needed
docker compose restart backend
```

### Rebuild (only when changing dependencies)

```bash
docker compose down
docker compose up -d --build
```

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

### "Failed to connect to Ollama"

```bash
# Ensure Ollama is running
ollama serve

# Pull embedding model
ollama pull nomic-embed-text

# Test Ollama locally
curl http://localhost:11434/api/tags

# If using rootless Docker or host.docker.internal doesn't work:
# 1. Find your host IP
ip addr show | grep "inet "

# 2. Update .env with your actual IP
# OLLAMA_HOST=http://YOUR_HOST_IP:11434

# 3. Restart backend
docker compose restart backend

# 4. Test from container
docker exec clawrag-backend curl http://YOUR_HOST_IP:11434/api/tags
```

### "ChromaDB client not available"

```bash
# Check ChromaDB service
docker compose logs chromadb

# Restart ChromaDB
docker compose restart chromadb
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

**How it works:**
1. Set `DOCS_DIR=/home/user/Documents` in `.env`
2. Docker mounts it as `/host_root` inside container
3. Use `/host_root` in the UI

### Import errors after code changes

```bash
# Restart backend to reload modules
docker compose restart backend
```

---

## 📚 API Endpoints

Full API documentation available at http://localhost:8081/docs

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

## 🏢 Edition Comparison

### Community Edition (This Repository)

**Free & Open Source (Self-Hosted)**

- ✅ **Collections: Unlimited**
- ✅ **Documents: Unlimited**
- ✅ **Multi-collection search routing** (via automatic fallback)
- ✅ Formats: PDF, Markdown, TXT, DOCX (via Docling)
- ✅ Hybrid Search: Vector + BM25 (RRF fusion)
- ✅ Basic Classification: Heuristic-based
- ✅ Full source code access
- ✅ **MCP Integration**: Native OpenClaw integration via Model Context Protocol
- ❌ No Solomon Consensus Engine
- ❌ No Mission Cartridge System
- ❌ No ML-powered Mission Analytics

**Perfect for:**
- Personal Knowledge Bases
- Internal Company Documentation
- Development and testing
- Understanding RAG architecture
- WhatsApp/Telegram-controlled AI assistants

### Professional Edition

- 🚀 Collections: 10, 5000 docs each
- 🚀 Formats: Extended (DOCX, HTML, PPTX, XLSX)
- 🚀 Advanced Reranking: Cross-encoder models
- 🚀 Multi-Collection Search: Intelligent routing
- 🚀 ML Classification: Confidence calibration
- 🚀 Analytics & Monitoring
- 🚀 Priority Support

### Enterprise Edition 

**The Audit-Proof Truth Layer**

While ClawRAG provides fast, efficient memory for agents, the Enterprise Core (V4.0) adds:

- **Solomon Consensus Engine** (Multi-Lane Validation via parallel AI Agents)
- **Enhanced Janus** (Mission-based intelligent document routing)
- **Surgical HITL** (Visual Human-in-the-Loop verification with bounding boxes)
- **Citation Enforcer** (Deterministic hallucination protection)
- **Mercator Context Graph** (GraphRAG with Neo4j entity extraction)
- **Six Sigma Laboratory** (Automated quality audits with LLM-as-a-Judge)
- **Mission Cartridge System** (Multi-tenant isolation & adaptive configuration)

[View the Enterprise Manifest](https://github.com/2dogsandanerd/RAG_enterprise_core)

---

## 🤝 Contributing

Contributions welcome! This is the Community Edition - we encourage:

- 🐛 Bug reports and fixes
- 📝 Documentation improvements
- 💡 Feature suggestions
- ⚡ Performance optimizations

**Please note:** Advanced features (ML classification, reranking, multi-collection) are part of paid editions. Community contributions focus on core RAG functionality.

---

## 📜 License

MIT License - Use freely in commercial and open-source projects.

Copyright (c) 2025 2dogsandanerd (ClawRAG Community Edition)

This product includes software developed by IBM (Docling) and other open source contributors.

Docling: https://github.com/DS4SD/docling (MIT License)
Copyright (c) 2024 IBM Corp.

---

## Citation

If you use this tool in research or production, please cite:

```bibtex
@software{clawrag_community_edition,
  title = {ClawRAG: The Cognitive Core for Autonomous Agents},
  author = {2dogsandanerd},
  year = {2025},
  url = {https://github.com/2dogsandanerd/ClawRag}
}
```


---

## 🙏 Acknowledgements

- **Docling** - Modern document processing
- **ChromaDB** - Vector storage
- **LlamaIndex** - Retrieval pipelines
- **FastAPI** - API framework
- **Ollama** - Local LLM inference

---

## 📞 Support

- **Community Edition**: GitHub Issues
- **Professional/Enterprise**: [Contact Sales](mailto:2dogsandanerd@gmail.com)
- **Reddit**: [https://www.reddit.com/r/ClawRAG](https://www.reddit.com/r/ClawRAG/) 

---

## 🎯 Roadmap

**Community Edition:**
- [ ] Simple authentication layer
- [ ] Query history tracking
- [ ] Export/import collections
- [ ] Improved error messages
- [ ] MCP-based ingestion tools

**Professional Features** (Available Now):
- Multi-collection intelligent search
- Advanced reranking with cross-encoders
- ML-powered classification
- Extended format support

---

**Built with ❤️ by developers who needed a solid RAG foundation.**

*If you find this useful, star ⭐ the repo and share with others!*
# ClawRag
