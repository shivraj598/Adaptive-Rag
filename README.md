# Adaptive RAG

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5.4-orange.svg)](https://python.langchain.com/langgraph/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)

Intelligent Retrieval-Augmented Generation system that dynamically routes queries to indexed documents, general LLM knowledge, or web search. Built with LangGraph orchestration and a modern React frontend.

![Landing Page](src/api/pictures/landing1.png)
![Chat Interface](src/api/pictures/chating.png)

---

## How It Works

```
User Query -> query_analysis
  ├── "index"   -> retriever -> grade
  │                ^            ├── "yes" -> generate -> response
  │                └── rewrite -┘ "no"
  ├── "general" -> general_llm -> response
  └── "search"  -> web_search  -> generate -> response
```

The system classifies every query into one of three routes:
- **Index** — answered from your uploaded documents (FAISS vector search)
- **General** — answered from the LLM's own knowledge
- **Search** — answered via Tavily web search

If retrieved documents are irrelevant, the query is rewritten and re-retrieved (up to 3 attempts).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + Tailwind CSS v4 |
| Backend | FastAPI + Uvicorn |
| LLM Provider | OpenRouter (GPT-4o) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local — no API key needed) |
| Vector Store | FAISS (persisted to disk) |
| Orchestration | LangGraph |
| Chat History | MongoDB Atlas (via Motor) |
| Web Search | Tavily API |

---

## Quick Start

### Prerequisites

- Python 3.12
- Node.js 20+
- MongoDB Atlas connection string
- OpenRouter API key
- Tavily API key

### Setup

```bash
# Clone
git clone https://github.com/shivrajtimilsena/Adaptive-Rag.git
cd Adaptive-Rag

# Backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in your keys
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npx vite --host --port 5173
```

### Environment Variables (`.env`)

```
OPENROUTER_API_KEY=sk-or-v1-...
TAVILY_API_KEY=tvly-...
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=adaptive_rag
```

---

## API

**Query**
```
POST /rag/query
{ "query": "...", "session_id": "..." }
```

**Upload Document**
```
POST /rag/documents/upload
Header: X-Description: ...
Body: file (PDF or TXT)
```

---

## Project Structure

```
src/
├── main.py                  # FastAPI entrypoint
├── api/routes.py            # Query & upload endpoints
├── rag/
│   ├── graph_builder.py     # LangGraph workflow (7 nodes)
│   ├── retriever_setup.py   # FAISS vector store (persisted)
│   ├── document_upload.py   # PDF/TXT -> chunks -> FAISS
│   └── reAct_agent.py       # ReAct agent wrapping retriever
├── llms/openai.py           # ChatOpenAI via OpenRouter
├── tools/graph_tools.py     # Routing & conditional edges
├── models/                  # Pydantic state & schemas
├── memory/                  # MongoDB chat history
├── db/mongo_client.py       # Async MongoDB client
├── config/                  # YAML prompts, env settings
└── core/                    # Logger, config helpers

frontend/
└── src/App.jsx              # Chat UI with file upload + dark mode
```

---

## Author

**Shivraj Timilsena**

[![GitHub](https://img.shields.io/badge/GitHub-shivraj598-181717.svg)](https://github.com/shivraj598)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-shivrajtimilsena-0A66C2.svg)](https://linkedin.com/in/shivraj-timilsena)

---

## License

MIT
