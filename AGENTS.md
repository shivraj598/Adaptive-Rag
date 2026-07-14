# Adaptive RAG — Project Memory & Patterns

## Overview

Adaptive RAG is an intelligent Retrieval-Augmented Generation system that dynamically routes queries to indexed documents, general LLM knowledge, or web search (Tavily). It uses LangGraph to orchestrate a stateful workflow and GPT-4o for all LLM calls.

## Architecture

```
React Frontend (frontend/)
  └── src/App.jsx      — Single-page chat UI + document upload (calls Python backend on :8000)

FastAPI Backend (src/)
  ├── main.py              — Entry point, creates FastAPI app
  ├── api/routes.py        — POST /rag/query, POST /rag/documents/upload
  ├── rag/graph_builder.py — Central LangGraph orchestrator (7 nodes)
  ├── rag/retriever_setup.py — FAISS vector store (global singleton)
  ├── rag/document_upload.py — PDF/TXT → chunks → FAISS
  ├── rag/reAct_agent.py  — ReAct agent wrapping the retriever tool
  ├── tools/graph_tools.py — Routing/conditional edge functions
  ├── models/             — Pydantic models for state, grades, routes
  ├── memory/             — MongoDB-backed chat history
  ├── config/             — YAML prompt loader
  ├── core/               — Env settings, logger
  ├── db/                 — MongoDB async client (motor)
  └── llms/               — ChatOpenAI(gpt-4o) singleton
```

## LangGraph Workflow

```
START → query_analysis
  ├── "index"   → retriever → grade
  │                ↑            ├── "yes" → generate → END
  │                └── rewrite ──┘ "no"
  ├── "general" → general_llm → END
  └── "search"  → web_search → generate → END
```

### Graph Nodes (`src/rag/graph_builder.py`)
| Node | What it does |
|------|-------------|
| `query_analysis` | Calls FAISS for context, then LLM classifies as "index"/"general"/"search" |
| `retriever` | ReAct agent that invokes the FAISS retriever tool |
| `grade` | LLM checks retrieved docs relevance → "yes"/"no" |
| `rewrite` | LLM rewrites query for better retrieval, loops back to retriever |
| `generate` | LLM produces final answer from context |
| `web_search` | Tavily web search, passes results to generate |
| `general_llm` | Direct LLM response (no retrieval) |

## Key Patterns

### State Management
- `State` is a `TypedDict` with `messages` (using `add_messages` reducer), `binary_score`, `route`, `latest_query` (`src/models/state.py`)
- Graph nodes accept and return partial state dictionaries

### Structured LLM Output
Use `llm.with_structured_output(PydanticModel)` for all classifier/grader/verifier nodes:
```python
llm_with_structured_output = llm.with_structured_output(RouteIdentifier)
chain = classify_prompt | llm_with_structured_output
result = chain.invoke({"question": question, "context": context})
```

### FAISS Vector Store (Global Singleton)
- `_faiss_vectorstore` module-level variable in `retriever_setup.py`
- `retriever_chain(chunks)` → stores docs, `get_retriever()` → returns LangChain retriever tool
- Falls back to a dummy document if none uploaded
- **No persistence** — FAISS index is lost on restart

### Document Upload Flow
1. Validate file is `.pdf` or `.txt`
2. Save to temp file, load with `PyPDFLoader`/`TextLoader`
3. Split with `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=150)
4. Enhance user description via LLM → write to `description.txt`
5. Store chunks in FAISS via `retriever_chain()`

### Chat History
- MongoDB via `motor` (async) — `MongoDBChatMessageHistory` in `src/memory/chat_history_mongo.py`
- Factory: `ChatHistory.get_session_history(session_id)`
- Per-request: load history → append user msg → invoke graph → save AI response
- In-memory fallback exists (`chathistory_in_memory.py`) but is commented out in routes

### Conditional Edges (`src/tools/graph_tools.py`)
- `routing_tool(state)` → routes based on `state["route"]` ("index"→retriever, "general"→general_llm, "search"→web_search)
- `doc_tool(state)` → routes based on `state["binary_score"]` ("yes"→generate, "no"→rewrite)
- `verify_answer(state)` → defined but **never wired into the graph**

### Dual Backend Architecture
- Rust backend (:8080) for auth (`/init`, `/create_user`, `/login`)
- Python backend (:8000) for RAG (`/rag/query`, `/rag/documents/upload`)
- Streamlit frontend talks to both

## Conventions

- **Module docstrings** at top of every Python file (Google-style)
- **Google-style function docstrings** with Args/Returns/Raises
- **snake_case** for variables/functions, **PascalCase** for classes, **UPPER_CASE** for constants
- **Import order**: stdlib → third-party → local (alphabetical groups)
- **Two blank lines** between top-level definitions, one between class methods
- **Comments explain WHY, not WHAT**
- **Type hints** on all function parameters and return types

## Important Gotchas

- `src/rag/nodes.py` is empty (placeholder) — all nodes defined inline in `graph_builder.py`
- `langchain_groq` and `beautifulsoup4` in requirements but **not used**
- Qdrant is fully commented out in `retriever_setup.py` in favor of FAISS
- `verify_answer` function is never connected to the graph
- No tests exist anywhere in the project
- `description.txt` is the runtime-created communication channel for retriever tool instructions
- `app.state.description_` in `main.py:11` is set but never read
- `chat.py:97` passes `jwt_token` as session_id to `query_backend` (not the actual session_id from `st.session_state["session_id"]`)

## Start Commands

```bash
# Backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
streamlit run streamlit_app/home.py
```

## Dependencies (key)

| Package | Purpose |
|---------|---------|
| langchain~0.3.27 | Core LLM framework |
| langgraph~0.5.4 | Stateful graph workflow |
| langchain_openai~0.3.28 | GPT-4o + embeddings |
| faiss-cpu | Local vector store |
| tavily-python | Web search API |
| motor | Async MongoDB driver |
| fastapi + uvicorn | Backend server |
| streamlit | Frontend UI |
