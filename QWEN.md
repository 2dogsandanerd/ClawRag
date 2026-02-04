# ClawRAG - The Brain for OpenClaw

## Projektübersicht

ClawRAG ist ein produktionsbereites, selbst gehostetes RAG-Engine (Retrieval Augmented Generation), das als langfristiges Gedächtnis ("The Brain") für autonome Agenten wie OpenClaw fungiert. Das Projekt extrahiert essentielle kognitive Funktionen aus dem Enterprise-Core und bietet eine robuste API für Dokumenten-Ingestion und Abfrage. Die Architektur trennt Intelligenz von Aktionen und ermöglicht skalierbare KI-Anwendungen.

### Hauptmerkmale

- **Modernes Dokumenten-Processing**: Nutzt Docling 2.13.0 für PDF, DOCX, PPTX, XLSX, HTML, Markdown
- **Hybride Suche**: Vektorähnlichkeit + BM25 Schlüsselwortsuche mit Reciprocal Rank Fusion
- **ChromaDB 0.5.23**: Vektorspeicher mit Verbindungspooling und Gesundheitsprüfungen
- **LlamaIndex 0.12.9**: Fortgeschrittene Abruf-Pipelines
- **Multi-LLM-Unterstützung**: Ollama (Standard), OpenAI, Anthropic, Gemini
- **Leichtgewichtige UI**: Einzelne HTML/JS-Dashboard-Datei mit Live-Systemprotokollen
- **Docker-first**: Produktionsbereite Bereitstellung mit Hot-Reload-Unterstützung
- **MCP-Integration**: Eingebauter Model Context Protocol-Server für OpenClaw
- **Ordner-Ingestion**: Massenverarbeitung von Dokumenten mit Echtzeit-Fortschrittsanzeige

## Technische Architektur

### Hauptkomponenten

- **Backend**: FastAPI-basierte API mit Endpunkten für Ingestion, Abfrage, Sammlungen und Dokumente
- **ChromaDB**: Vektordatenbank für semantische Speicherung und Abruf
- **Ollama**: Lokale LLM- und Embedding-Inferenz
- **Docling**: Modernes Dokumentenverarbeitungs-Framework
- **MCP-Server**: Model Context Protocol-Server für OpenClaw-Integration
- **nginx**: Reverse-Proxy-Gateway für alle Dienste

### Kernmuster

- **Singleton**: ChromaManager für einzelne Verbindungsinstanz
- **Resilienz**: Circuit-Breaker + Wiederholungslogik für ChromaDB
- **Lifespan**: Korrektes FastAPI-Startup/-Shutdown für saubere Verbindungen
- **Hot-Reload**: Quellcode als Volume eingehängt für Entwicklung

### Dateistruktur

```
.
├── backend/
│   ├── src/
│   │   ├── api/v1/rag/         # RAG-Endpunkte
│   │   │   ├── collections.py  # Sammlungs-CRUD
│   │   │   ├── documents/      # Upload, Verwaltung
│   │   │   ├── query.py        # RAG-Abfragen
│   │   │   ├── ingestion/      # Ordnerscan, Batch-Verarbeitung
│   │   │   └── cockpit.py      # Systemstatus
│   │   ├── core/
│   │   │   ├── chroma_manager.py      # ChromaDB-Singleton
│   │   │   ├── docling_loader.py      # Dokumentenparser
│   │   │   ├── query_engine.py        # Abfrageausführung
│   │   │   ├── retrievers/            # Hybrid, BM25, Re-Ranker
│   │   │   ├── config.py              # Multi-LLM-Konfiguration
│   │   │   └── feature_limits.py      # Editions-Tarife
│   │   └── services/
│   │       ├── docling_service.py     # Zentrale Dok-Verarbeitung
│   │       ├── classification.py      # Dok-Klassifikation
│   │       └── generators/            # Zusammenfassungen, Konfigurationen
│   ├── requirements.txt
│   └── Dockerfile
├── mcp-server/
│   ├── src/
│   │   ├── server.ts            # MCP-Server-Implementierung
│   │   ├── config.ts            # Konfigurationsmanagement
│   │   └── types.ts             # Typdefinitionen
│   ├── package.json
│   └── README.md                # MCP-Server-Dokumentation
├── frontend/
│   └── index.html              # Null-Build-Dashboard (Vanilla JS)
├── docker-compose.yml          # Vollständige Stack-Orchestrierung
├── CLAUDE.md                   # Entwicklerhandbuch
└── README.md
```

## Installation und Betrieb

### Schnellstart (5 Minuten)

#### Voraussetzungen

1. **Docker & Docker Compose** installiert
2. **Ollama** lokal laufend (für Embeddings)
   ```bash
   # Ollama installieren (falls noch nicht installiert)
   curl -fsSL https://ollama.com/install.sh | sh

   # Ollama-Server starten
   ollama serve

   # Embedding-Modell herunterladen (in einem anderen Terminal)
   ollama pull nomic-embed-text
   ```

#### Setup

```bash
# 1. Repository klonen
git clone https://github.com/2dogsandanerd/ClawRag.git
cd ClawRag

# 2. Konfigurieren & Starten
# Interaktives Setup-Skript ausführen, um Ihren Dokumentenordner zu setzen
./setup.sh

# (Alternativ) Manuelles Setup:
# cp .env.example .env
# docker compose up -d

# 4. Gesundheitsprüfung
curl http://localhost:8080/health
# Erwartet: {"status":"healthy","chromadb":"connected","collections_count":0}

# 5. Anwendung öffnen
open http://localhost:8080
```

### Dienste (alle über einziges nginx-Gateway):

- Frontend-UI: http://localhost:8080/
- API-Dokumentation: http://localhost:8080/docs
- Gesundheitsprüfung: http://localhost:8080/health
- API-Endpunkte: http://localhost:8080/api/v1/rag/*

## Konfiguration

Umgebungsvariablen werden in der `.env`-Datei konfiguriert:

| Variable | Standard | Beschreibung |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM-Anbieter (ollama, openai, anthropic, gemini) |
| `LLM_MODEL` | `llama3.1:8b-instruct-q4_k_m` | Modellname für gewählten Anbieter |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding-Anbieter (normalerweise identisch mit LLM) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding-Modellname |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama-Verbindungs-URL |
| `CHROMA_HOST` | `chroma_running` | ChromaDB-Container/Service-Name |
| `CHROMA_PORT` | `8000` | ChromaDB-Port |
| `DOCS_DIR` | `./data/docs` | Host-Verzeichnis, das als `/host_root` für Ordner-Ingestion eingehängt wird |
| `PORT` | `8080` | Externer Port für nginx-Gateway |
| `DEBUG` | `true` | Debug-Protokollierung aktivieren |

## API-Nutzung

### Python-Beispiel

```python
import requests

BASE_URL = "http://localhost:8080/api/v1/rag"

# 1. Eine Sammlung erstellen
response = requests.post(
    f"{BASE_URL}/collections",
    files={
        "collection_name": (None, "mein_wissen"),
        "embedding_provider": (None, "ollama"),
        "embedding_model": (None, "nomic-embed-text")
    }
)
print(f"Sammlung erstellt: {response.json()}")

# 2. Dokumente hochladen
with open("dokument.pdf", "rb") as f:
    response = requests.post(
    f"{BASE_URL}/documents/upload",
    files={"files": f},
    data={
        "collection_name": "mein_wissen",
        "chunk_size": 512,
        "chunk_overlap": 128
    }
)
print(f"Upload-Status: {response.json()}")

# 3. Das Wissensbasis abfragen
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "Was sind die Hauptthemen?",
        "collection": "mein_wissen",
        "k": 5
    }
)
result = response.json()
print(f"Antwort: {result.get('answer')}")
print(f"Quellen: {len(result.get('sources', []))}")
```

### cURL-Beispiele

```bash
# Gesundheitsprüfung
curl http://localhost:8080/health

# Sammlungen auflisten
curl http://localhost:8080/api/v1/rag/collections

# Sammlungsstatistik abrufen
curl http://localhost:8080/api/v1/rag/collections/meine_dokumente/stats

# Abfrage mit spezifischen Parametern
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Erkläre die Architektur",
    "collection": "meine_dokumente",
    "k": 10,
    "similarity_threshold": 0.5
  }'

# Eine Sammlung löschen
curl -X DELETE http://localhost:8080/api/v1/rag/collections/meine_dokumente
```

## OpenClaw-Integration via MCP

ClawRAG bietet native Unterstützung für OpenClaw-Integration über das Model Context Protocol (MCP), wodurch Sie direkt aus WhatsApp, Telegram, Discord und anderen OpenClaw-unterstützten Kanälen auf Ihre Wissensbasis zugreifen können.

### Installation

1. **ClawRAG starten**:
   ```bash
   docker compose up -d
   ```

2. **MCP-Server in OpenClaw installieren**:
   ```bash
   openclaw mcp add --transport stdio clawrag npx -y @clawrag/mcp-server
   ```

3. **(Optional) Benutzerdefinierten Endpunkt konfigurieren**:
   Falls ClawRAG nicht auf `http://localhost:8080` läuft, setzen Sie die Umgebungsvariable:
   ```bash
   export CLAWRAG_API_URL=http://your-clawrag-instance:8080
   ```

### Verfügbare MCP-Tools

#### `query_knowledge`
Abfrage Ihrer Wissensbasis aus OpenClaw-Kanälen:

```
Benutzer: "Suche in Wissensbasis nach: Vertragsbedingungen mit Siemens"
OpenClaw: [Ruft query_knowledge(query="Vertragsbedingungen mit Siemens") auf]
ClawRAG: "Laut Siemens_Vertrag_2024.pdf, Seite 12, Abschnitt 4.2: 'Die Haftung ist auf direkte Schäden bis zu 10% des Vertragswerts begrenzt.' [Zitat: chunk_id: siemens_vertrag_2024_p12_s42]"
```

#### `list_collections`
Entdecken Sie verfügbare Wissensbasen:

```
Benutzer: "Verfügbare Sammlungen auflisten"
OpenClaw: [Ruft list_collections() auf]
ClawRAG: "Verfügbare Sammlungen:
- vertraege (15 Dokumente)
- handbuecher (8 Dokumente)
- protokolle (23 Dokumente)"
```

## Editions-Vergleich

### Community Edition (Dieses Repository)

**Kostenlos & Open Source (Selbst-Hosting)**

- ✅ **Sammlungen: Unbegrenzt**
- ✅ **Dokumente: Unbegrenzt**
- ✅ **Multi-Sammlungssuche-Routing** (über automatisches Fallback)
- ✅ Formate: PDF, Markdown, TXT, DOCX (über Docling)
- ✅ Hybride Suche: Vektor + BM25 (RRF-Fusion)
- ✅ Grundlegende Klassifikation: Heuristik-basiert
- ✅ Vollständiger Zugriff auf Quellcode
- ✅ **MCP-Integration**: Native OpenClaw-Integration über Model Context Protocol
- ❌ Kein Solomon Consensus Engine
- ❌ Kein Mission Cartridge System
- ❌ Keine ML-basierte Missionsanalyse

**Perfekt für:**
- Persönliche Wissensbasen
- Interne Firmendokumentation
- Entwicklung und Testing
- Verständnis der RAG-Architektur
- WhatsApp/Telegram-gesteuerte KI-Assistenten

### Professionelle Edition

- 🚀 Sammlungen: 10, jeweils 5000 Dokumente
- 🚀 Formate: Erweitert (DOCX, HTML, PPTX, XLSX)
- 🚀 Fortgeschrittener Re-Ranking: Cross-Encoder-Modelle
- 🚀 Multi-Sammlungssuche: Intelligente Routing
- 🚀 ML-Klassifikation: Konfidenzberechnung
- 🚀 Analysen & Monitoring
- 🚀 Priorisierter Support

### Enterprise Edition

**Die auditierungssichere Wahrheitsschicht**

Während ClawRAG schnelles, effizientes Gedächtnis für Agenten bereitstellt, fügt die Enterprise Core (V4.0) folgendes hinzu:

- **Solomon Consensus Engine** (Multi-Lane-Validierung über parallele KI-Agenten)
- **Erweitertes Janus** (Mission-basiertes intelligentes Dokumenten-Routing)
- **Surgical HITL** (Visuelle Human-in-the-Loop-Verifizierung mit Bounding Boxes)
- **Citation Enforcer** (Deterministischer Halluzinations-Schutz)
- **Mercator Context Graph** (GraphRAG mit Neo4j-Entity-Extraktion)
- **Six Sigma Laboratory** (Automatische Qualitätsaudits mit LLM-as-a-Judge)
- **Mission Cartridge System** (Multi-Tenant-Isolation & adaptive Konfiguration)

## Entwicklung

### Lokale Entwicklung (ohne Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

**Hinweis:** Sie benötigen ChromaDB und Ollama separat laufend.

### Docker-Entwicklung (mit Hot-Reload)

Code-Änderungen werden automatisch erkannt (Quellcode als Volume eingehängt):

```bash
# Code in backend/src/ bearbeiten
# Änderungen werden sofort erkannt, kein Neubau erforderlich

# Protokolle anzeigen
docker compose logs -f backend

# Bei Bedarf neu starten
docker compose restart backend
```

## Lizenz

MIT-Lizenz - Freie Nutzung in kommerziellen und Open-Source-Projekten.

Copyright (c) 2025 2dogsandanerd (ClawRAG Community Edition)

Dieses Produkt enthält Software, die von IBM (Docling) und anderen Open-Source-Mitwirkenden entwickelt wurde.

Docling: https://github.com/DS4SD/docling (MIT-Lizenz)
Copyright (c) 2024 IBM Corp.