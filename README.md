# ClawRAG

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/2dogsandanerd/ClawRag/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Enterprise](https://img.shields.io/badge/Enterprise-Available-success)](https://github.com/2dogsandanerd/RAG_enterprise_core)

**Production-Ready RAG Engine. Self-Hosted. Data Sovereign. Enterprise-Grade.**

ClawRAG is a powerful, self-hosted Retrieval-Augmented Generation (RAG) system that gives you complete control over your AI document processing. Process documents locally with local LLMs or connect to cloud APIs—your data never leaves your infrastructure unless you want it to.

[🚀 Quick Start](#quick-start) • [📊 Editions](#editions) • [🏢 Enterprise](#enterprise-features) • [📖 Documentation](docs/)

---

## 🎯 Why ClawRAG?

### The Problem
Enterprise document processing forces you to choose:
- ❌ **Cloud solutions**: Send sensitive data to third parties
- ❌ **Simple tools**: Fail on complex PDFs, tables, mixed content
- ❌ **DIY approaches**: Months of integration, no production readiness

### Our Solution
ClawRAG provides **production-grade document intelligence** that runs entirely on your infrastructure:

✅ **Self-Hosted**: Complete data sovereignty  
✅ **Intelligent Processing**: Handles complex PDFs, tables, scanned documents  
✅ **Hybrid Search**: Combines semantic + keyword search for accuracy  
✅ **Production-Ready**: Docker-first, scalable, monitored  
✅ **Enterprise Path**: Seamless upgrade to advanced features  

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- 8GB+ RAM (16GB recommended)

### One-Command Setup

```bash
# 1. Clone and enter
git clone https://github.com/2dogsandanerd/ClawRag.git
cd ClawRag

# 2. Configure
cp .env.example .env

# 3. Start everything
docker compose up -d

# 4. Verify
curl http://localhost:8080/health
```

**Access your instance:**
- 🌐 **Web UI**: http://localhost:8080
- 📚 **API Docs**: http://localhost:8080/docs
- 🔍 **Health Check**: http://localhost:8080/health

---

## 📊 Editions

Choose the edition that fits your needs:

| Feature | Community Edition | Enterprise Edition |
|---------|------------------|-------------------|
| **Document Processing** | Single-engine (Docling) | Multi-engine consensus |
| **Supported Formats** | PDF, DOCX, MD, TXT, CSV | + Images, Email, Code, PPT, XLS |
| **Search** | Vector + BM25 Hybrid | + Graph RAG, Semantic Routing |
| **Data Validation** | Basic quality scoring | Consensus validation, 100% accuracy |
| **Human Verification** | Manual review | Surgical precision (only conflicts) |
| **Multi-Tenancy** | Single user | Mission-based isolation |
| **Quality Assurance** | Basic logging | Real-time dashboards, automated testing |
| **Support** | Community | SLA-backed, dedicated support |
| **Pricing** | Free (MIT License) | Custom enterprise licensing |

**[→ Compare full feature matrix](docs/editions.md)**

---

## 🏢 Enterprise Features

Need more? [ClawRAG Enterprise Core](https://github.com/2dogsandanerd/RAG_enterprise_core) provides advanced capabilities:

### 🧠 Adaptive Intelligence
- **Multi-Engine Processing**: 3+ specialized extractors work in parallel
- **Consensus Validation**: Automated comparison ensures 100% data integrity
- **Intelligent Routing**: Analyzes document type and selects optimal strategy

### 🔒 Zero Data Loss Architecture
- **Parallel Processing**: Multiple engines analyze each document independently
- **Conflict Detection**: Flags discrepancies for targeted human review
- **Visual Verification**: See exactly where conflicts occur on source documents

### 🌐 Advanced Knowledge Retrieval
- **Graph RAG**: Neo4j-powered relationship traversal between documents
- **Semantic + Graph Hybrid**: Combines concept search with factual relationships
- **Query Decomposition**: Complex queries automatically split into sub-tasks

### 📊 Mission-Based Multi-Tenancy
- **Customer Isolation**: Complete data separation per mission
- **Hot Configuration**: Update rules without system restart
- **Quality Gates**: Per-mission thresholds and processing rules

### 📈 Continuous Quality Assurance
- **Real-Time Observability**: Grafana dashboards for all processing stages
- **Automated Testing**: Continuous validation against reference datasets
- **Performance Monitoring**: Track accuracy, speed, and system health

**[→ View Enterprise Manifest](https://github.com/2dogsandanerd/RAG_enterprise_core/blob/main/manifest_v4.0.md)**

---

## 💼 Use Cases

### 📄 Legal & Compliance
Process contracts, court filings, and regulatory documents with:
- Citation extraction and validation
- Clause detection and comparison
- Audit-compliant processing trails
- PII detection and redaction

### 🏥 Healthcare & Research
Analyze medical literature and patient records:
- Medical entity extraction
- Cross-document concept linking
- Citation graph analysis
- HIPAA-compliant processing

### 💰 Financial Services
Process invoices, reports, and due diligence documents:
- Entity mapping and verification
- Anomaly detection in financial data
- Structured data extraction from tables
- Multi-document reconciliation

### 🔬 Technical Documentation
Ingest API docs, manuals, and technical specifications:
- Code block preservation
- Structured content extraction
- Semantic chunking for technical terms
- Cross-reference resolution

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Gateway (8080)                 │
│  ┌──────────────┐  ┌──────────────────────────────┐    │
│  │  Frontend UI │  │  FastAPI Backend (8081)      │    │
│  │  (Vue.js)    │  │  - RAG API                   │    │
│  └──────────────┘  │  - Document Processing       │    │
│                    │  - Hybrid Search             │    │
│                    └──────────────┬───────────────┘    │
└───────────────────────────────────┼─────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────┐
         │                          │                  │
         ▼                          ▼                  ▼
┌─────────────────┐  ┌──────────────────────┐  ┌──────────────┐
│  ChromaDB       │  │  Ollama / LLM        │  │  (Optional)  │
│  Vector Store   │  │  Embeddings & Chat   │  │  Enterprise  │
│  (Port 8001)    │  │  (Port 11434)        │  │  Extensions  │
└─────────────────┘  └──────────────────────┘  └──────────────┘
```

### Key Components

**Backend (`backend/src/`):**
- `api/v1/rag/` - REST API endpoints (ingestion, query, collections)
- `core/` - ChromaDB manager, document loaders, retrievers
- `services/` - Document processing, deduplication, task management

**Processing Pipeline:**
1. **Ingestion**: Multi-format support with intelligent parsing
2. **Chunking**: Configurable semantic and sentence-based strategies
3. **Embedding**: Multi-provider support (Ollama, OpenAI, Anthropic)
4. **Storage**: ChromaDB with metadata and hybrid search
5. **Retrieval**: Vector + BM25 with Reciprocal Rank Fusion

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | External port for nginx gateway |
| `DOCS_DIR` | `./data/docs` | Host directory for folder ingestion |
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama, openai, anthropic, gemini) |
| `LLM_MODEL` | `llama3:latest` | Model name for selected provider |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `CHUNK_SIZE` | `512` | Size of text chunks |
| `CHUNK_OVERLAP` | `128` | Overlap between chunks |
| `DEBUG` | `false` | Enable debug logging |

### LLM Configuration Examples

**Local (Ollama) - Privacy First:**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3:latest
EMBEDDING_MODEL=nomic-embed-text
```

**Cloud (OpenAI) - Maximum Performance:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-proj-...
```

**Local Server (LM Studio, etc.):**
```bash
LLM_PROVIDER=openai_compatible
LLM_MODEL=local-model
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
```

---

## 🛠️ Using the API

### Python Example

```python
import requests

BASE_URL = "http://localhost:8080/api/v1/rag"

# 1. Create a collection
requests.post(f"{BASE_URL}/collections", files={
    "collection_name": (None, "legal_docs"),
    "embedding_model": (None, "nomic-embed-text")
})

# 2. Upload documents
with open("contract.pdf", "rb") as f:
    requests.post(
        f"{BASE_URL}/documents/upload",
        files={"files": f},
        data={"collection_name": "legal_docs"}
    )

# 3. Query knowledge base
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "What are the termination clauses?",
        "collection": "legal_docs",
        "k": 5
    }
)
print(response.json()["answer"])
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# List collections
curl http://localhost:8080/api/v1/rag/collections

# Query with filters
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the architecture",
    "collection": "my_docs",
    "k": 10,
    "similarity_threshold": 0.5
  }'
```

---

## 📦 What's Included

### Community Edition
- ✅ FastAPI backend with comprehensive API
- ✅ Web UI for document management and querying
- ✅ ChromaDB vector database
- ✅ Ollama LLM/embedding service
- ✅ Nginx reverse proxy
- ✅ Multi-provider LLM support
- ✅ Hybrid search (vector + BM25)
- ✅ Document chunking strategies
- ✅ Folder batch ingestion

### Optional Enterprise Extensions
- 🔧 Multi-engine consensus processing
- 🔧 Graph database (Neo4j) integration
- 🔧 Real-time monitoring dashboards
- 🔧 Advanced quality assurance pipeline
- 🔧 Mission-based multi-tenancy
- 🔧 PII detection and compliance tools

---

## 🚨 Troubleshooting

### Common Issues

**LLM Connection Problems:**
```bash
# Check LLM initialization
docker compose logs backend | grep "LLM"

# For local servers, verify network
docker exec clawrag-backend curl http://host.docker.internal:11434
```

**Folder Ingestion Not Working:**
```bash
# Verify DOCS_DIR is set correctly
cat .env | grep DOCS_DIR

# Check mount inside container
docker exec clawrag-backend ls -la /host_root/
```

**Performance Issues:**
```bash
# Check resource usage
docker stats

# Review logs for bottlenecks
docker compose logs -f backend
```

**[→ Full troubleshooting guide](docs/troubleshooting.md)**

---

## 🤝 Community & Support

### Community Edition
- 🐛 [GitHub Issues](https://github.com/2dogsandanerd/ClawRag/issues) - Bug reports
- 💡 [Discussions](https://github.com/2dogsandanerd/ClawRag/discussions) - Feature requests
- 📖 [Documentation](docs/) - Setup and configuration
- 📝 [Contributing Guide](CONTRIBUTING.md) - How to contribute

### Enterprise Support
- 🎫 SLA-backed support with response time guarantees
- 📞 Direct engineering contact
- 🚀 Priority feature development
- 🏢 Custom integration assistance

**[→ Contact for Enterprise](mailto:2dogsandanerd@gmail.com)**

---

## 📄 License

**Community Edition**: MIT License - Free for commercial and personal use.

**Enterprise Edition**: Proprietary license with custom terms. Contact for details.

Copyright (c) 2025 2dogsandanerd

---

## 🎯 Roadmap

### Version 1.3 (Next)
- [ ] Multi-collection search
- [ ] Enhanced UI with query history
- [ ] Additional document format support

### Version 2.0 (Planned)
- [ ] Conversational memory
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom processors

### Enterprise Roadmap
- [ ] Kubernetes deployment
- [ ] Advanced graph reasoning
- [ ] Multi-modal search (text + images)
- [ ] ISO 27001 certification

---

<p align="center">
  <strong>Built with ❤️ for developers who value data sovereignty</strong><br>
  <a href="https://github.com/2dogsandanerd/ClawRag">GitHub</a> •
  <a href="https://github.com/2dogsandanerd/RAG_enterprise_core">Enterprise</a> •
  <a href="docs/">Documentation</a>
</p>
