# Architekturdiagramme für ClawRAG

## 1. Gesamtarchitektur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BENUTZERSCHNITTSTELLE                          │
├─────────────────────────────────────────────────────────────────────────┤
│  WhatsApp    │  Telegram    │  Discord    │  WebUI    │  API-Client   │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPENCLAW GATEWAY                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  MCP-CLIENT (stdio-Transport)                                  │   │
│  │  Verbindet zu @clawrag/mcp-server                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCP SERVER (@clawrag/mcp-server)                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Tool: query_knowledge                                        │   │
│  │  Tool: list_collections                                       │   │
│  │  Formatierung für OpenClaw                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │ HTTP REST API
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLAWRAG BACKEND                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI API Server                                           │   │
│  │  Endpoints: /api/v1/rag/*                                     │   │
│  │  Query, Upload, Collections, Ingestion                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Core Services:                                               │   │
│  │  - Docling Loader (PDF, DOCX, PPTX, XLSX, HTML, MD)         │   │
│  │  - ChromaManager (Vector DB Connection)                       │   │
│  │  - QueryEngine (Hybrid Search)                                │   │
│  │  - Retriever (Vector + BM25 + RRF)                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATENSPEICHERUNG                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────────┐   │
│  │   CHROMADB      │    │         OLLAMA / LLM PROVIDER         │   │
│  │   Vector Store  │    │   Embeddings & LLM Inference          │   │
│  │   (Docker)      │    │   (lokal oder remote)                 │   │
│  └─────────────────┘    └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. MCP-Integration Flow

```
Benutzer sendet Frage über WhatsApp/Telegram
         │
         ▼
   OpenClaw empfängt
         │
         ▼
   OpenClaw identifiziert Bedarf an Wissensabfrage
         │
         ▼
   OpenClaw ruft MCP-Tool auf: query_knowledge("Frage...")
         │
         ▼
   MCP-Server (@clawrag/mcp-server) empfängt Anfrage
         │
         ▼
   MCP-Server ruft ClawRAG API auf: POST /api/v1/rag/query
         │
         ▼
   ClawRAG führt Hybrid-Suche durch (Vector + BM25)
         │
         ▼
   Ergebnis wird aus ChromaDB abgerufen
         │
         ▼
   LLM generiert Antwort mit Quellen
         │
         ▼
   Antwort wird an MCP-Server zurückgegeben
         │
         ▼
   MCP-Server formatiert Antwort für OpenClaw
         │
         ▼
   Antwort wird an OpenClaw zurückgegeben
         │
         ▼
   OpenClaw sendet Antwort an Benutzer
```

## 3. Ingestion-Architektur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INGESTION METHODEN                              │
├─────────────────────────────────────────────────────────────────────────┤
│  WebUI Upload     │  REST API Direct   │  Folder Ingestion           │
│                   │                    │                              │
│  Drag & Drop      │  curl/requests     │  Batch Processing           │
│  Dateien          │  Skripte           │  rekursiv                   │
│                   │                    │                              │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐            │
│  │  Frontend   │  │  │  API Client │  │  │  Folder     │            │
│  │  Upload     │  │  │  Script     │  │  │  Scanner   │            │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘            │
└──────────────────┬─────────────────────┬──────────────────────────────┘
                   │                     │
                   ▼                     ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │                CLAWRAG INGESTION PIPELINE                       │
        │  ┌─────────────────────────────────────────────────────────┐   │
        │  │  Document Processing Pipeline                         │   │
        │  │  1. Format Detection (Docling)                        │   │
        │  │  2. Text Extraction (PDF, DOCX, etc.)                │   │
        │  │  3. Chunking (semantic + size-based)                 │   │
        │  │  4. Embedding Generation (Ollama)                    │   │
        │  │  5. Vector Storage (ChromaDB)                        │   │
        │  └─────────────────────────────────────────────────────────┘   │
        └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────────────────────┐
                    │              CHROMADB VECTORSPEICHER                │
                    │  ┌─────────────────────────────────────────────┐   │
                    │  │  Collections:                             │   │
                    │  │  - vertraege (120 Dokumente)              │   │
                    │  │  - handbuecher (45 Dokumente)             │   │
                    │  │  - protokolle (200 Dokumente)             │   │
                    │  └─────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────┘
```

## 4. Sicherheitsarchitektur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SICHERHEITSKONZEPT                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Netzwerkebene:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  nginx Reverse Proxy                                             │   │
│  │  - Einziger externer Zugangspunkt                              │   │
│  │  - Rate Limiting                                                 │   │
│  │  - SSL/TLS Terminierung                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  MCP-Ebene:                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  @clawrag/mcp-server                                             │   │
│  │  - Keine Datei-Uploads über MCP                                  │   │
│  │  - Nur Abfrage-Operationen                                       │   │
│  │  - Formatierung für sichere Ausgabe                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  API-Ebene:                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend                                                 │   │
│  │  - Keine Authentifizierung (lokaler Zugriff)                   │   │
│  │  - Input Validation                                              │   │
│  │  - Rate Limiting (geplant)                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```