# ClawRAG MCP Server

Connect your autonomous agents (like [OpenClaw](https://github.com/2dogsandanerd/openclaw)) to your self-hosted knowledge base using the Model Context Protocol (MCP).

## 🌟 Features

- **Semantic Search**: Ask questions in natural language.
- **Auto-Discovery**: Automatically search all collections if none are specified.
- **Citations**: Get sources and page numbers directly in your chat (WhatsApp/Telegram).
- **Collection Management**: List available knowledge bases.

## 🚀 Quick Start

Ensure your ClawRAG backend is running (typically on port 8080).

### 1. Install via OpenClaw
The easiest way to use this is with the `openclaw` CLI:

```bash
openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
```

### 2. Configuration
The server uses the following environment variables:
- `CLAWRAG_API_URL`: URL of your ClawRAG instance (default: `http://localhost:8080`)
- `CLAWRAG_TIMEOUT`: Timeout in milliseconds (default: `120000` for slow local LLMs)
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARN`, or `ERROR` (default: `INFO`)

## 🛠️ Included Tools

### `query_knowledge`
Ask a question to the knowledge base.
- **Parameters**: 
  - `query` (string): Your question.
  - `collections` (array, optional): Specific collections to search.
  - `k` (number, optional): Number of sources to retrieve.

### `list_collections`
List all available knowledge bases.

## 💻 Development

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Test as a standalone client
node build/test-client.js
```

---

*Part of the [Knowledge Base Self-Hosting Kit](https://github.com/2dogsandanerd/self-hosting-kit)*
