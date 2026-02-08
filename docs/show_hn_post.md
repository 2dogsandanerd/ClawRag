# Show HN Post: ClawRAG

## Titelvorschläge
- "Show HN: ClawRAG – Query your PDFs via WhatsApp using Model Context Protocol"
- "Show HN: I built a RAG system that lets me query my contracts via WhatsApp"
- "Show HN: Self-hosted RAG with MCP support for OpenClaw (WhatsApp/Telegram)"

## The Hook
I've been using OpenClaw to control my home server via WhatsApp, but it couldn't access my documents. Instead of uploading my private contracts to OpenAI, I built ClawRAG – a self-hosted RAG engine that connects to OpenClaw via MCP (Model Context Protocol). Now I can ask "What did the contract say about liability?" and get cited answers, not hallucinations.

## Why I built this
Most RAG systems are either too complex for a solo dev's home setup or they rely on cloud-hosted vector stores. I needed something that runs in a single Docker container, understands messy PDFs (tables!), and integrates natively as a "tool" for agents rather than just another REST endpoint.

## Technical Deep Dive

### Why MCP instead of REST?
I chose the Model Context Protocol (MCP) because it provides structured schemas that LLMs understand natively. The MCP server exposes `query_knowledge` as a tool, allowing the agent to decide exactly when to pull from the knowledge base vs. when to use its built-in memory. It prevents "tool-drift" and ensures type-safe responses.

### The Stack
- **Parsing**: Docling 2.13.0 (The first parser I've found that doesn't choke on nested tables in legacy PDFs).
- **Storage**: ChromaDB (Lightweight, file-based, no Postgres/pgvector overhead needed for personal knowledge bases).
- **Search**: Hybrid (Vector similarity + BM25 keyword search) fused using Reciprocal Rank Fusion (RRF) for better retrieval on specific legal jargon.
- **Footprint**: Optimized to run under 2GB RAM (excluding the local LLM).

### The tricky part: Citation Preservation
Getting citations to work reliably over a WhatsApp round-trip was the biggest challenge. I had to ensure chunk IDs and source metadata survive the transformation from ChromaDB → LlamaIndex → LLM → OpenClaw → WhatsApp without getting "summarized away" or sanitized by the LLM's output formatting.

## Demo / Real World Use Case
Last week my landlord claimed I signed a clause about garden/snow maintenance. I pulled up my phone, wrote to my OpenClaw bot: *"Search my lease for gardening obligations"*.
It found the relevant paragraph in 3 seconds, cited the page/section, and provided the exact quote. Argument closed.

## Quick Start
The repo includes a `docker-compose.yml` that spins up everything including the vector store:

```bash
# 1. Start ClawRAG
docker compose up -d

# 2. Add your documents
curl -X POST http://localhost:8080/api/v1/rag/documents/upload \
  -F "files=@my_lease.pdf" \
  -F "collection_name=personal"

# 3. Connect to your agent
openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
```

## Community & Feedback
Code is MIT licensed. I'd love feedback on the MCP implementation – specifically if you see better ways to handle tool schemas for multi-collection search.

**Ask me anything about the architecture or how I handled the citation logic!**

---

### Hidden Technical Details (For the comments section)
- **Privacy**: Zero external data leaks. Everything stays on your metal.
- **LLM Agnostic**: Tested with Ollama (Llama 3.2) and Claude 3.5 via API.
- **Context Management**: Explicit context window limiting to prevent GPU crashes on 8GB VRAM cards.
