# 🧠 GraphRAG — Enterprise Knowledge Graph + RAG System

A production-ready **Agentic + Multimodal-ready RAG system** combining:
- **ChromaDB** — vector similarity search
- **Neo4j** — knowledge graph storage
- **Gemini API** — entity extraction + answer generation
- **Streamlit** — interactive UI
- **FastAPI** — REST backend

---

## Architecture

```
Documents (PDF, DOCX, TXT)
        │
        ▼
   Document Loader
        │
        ▼
    Text Chunker
        │
   ┌────┴────┐
   ▼         ▼
ChromaDB  Entity Extractor (Gemini)
(Vectors)         │
                  ▼
             Neo4j Graph

User Query
    │
    ▼
Query Agent
    │
  ┌─┴─────────┐
  ▼           ▼
Vector      Graph
Search      Search
  │           │
  └─────┬─────┘
        ▼
   Gemini LLM
        │
        ▼
   Cited Response
```

---

## Quick Start

### 1. Clone and configure
```bash
git clone <repo>
cd graphrag_system
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Get your Gemini API key
Go to https://aistudio.google.com/apikey and create a free key.
Paste it in `.env`:
```
GEMINI_API_KEY=AIza...your_key_here
```

### 3. Launch with Docker
```bash
docker-compose up --build
```

Wait ~60 seconds for Neo4j to initialise on first run.

### 4. Open the UI
| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| FastAPI docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| ChromaDB | http://localhost:8001 |

---

## Usage

### Upload documents
1. Go to **Upload Documents** tab
2. Drag and drop PDF, DOCX, or TXT files
3. Click **Process All Documents**
4. System chunks, embeds, and extracts entities automatically

### Query
1. Go to **Query** tab
2. Type any question about your documents
3. Agent searches both vectors and graph, returns cited answer

### Explore the graph
1. Go to **Knowledge Graph** tab
2. Click **Load Graph**
3. Interactive force-directed graph of all extracted entities

---

## Project Structure

```
graphrag_system/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── loader.py        # PDF/DOCX/TXT loader
│   ├── chunker.py       # Text splitter
│   ├── chroma_store.py  # Vector DB client
│   ├── neo4j_store.py   # Graph DB client
│   ├── extractor.py     # Gemini entity extractor
│   ├── agent.py         # Query coordinator
│   └── config.py        # Environment config
├── streamlit_app.py     # Streamlit UI
├── Dockerfile.api
├── Dockerfile.streamlit
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Stopping the system
```bash
docker-compose down          # stop containers
docker-compose down -v       # stop + delete all data
```
