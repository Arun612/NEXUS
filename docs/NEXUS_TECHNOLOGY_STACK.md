# NEXUS — Technology Stack Deep Dive

> Every technology in NEXUS, what it does, why it was chosen, and what problem it solves.

---

## Stack Overview

| Layer | Technology | Category |
|-------|------------|----------|
| Language | Python 3.x | Core runtime |
| LLM Inference | Groq API + Llama 3.3 70B | Reasoning engine |
| LLM Client | OpenAI Python SDK | API abstraction |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Local semantic vectors |
| Vector DB | ChromaDB | Document similarity search |
| Keyword Search | rank-bm25 (BM25Okapi) | Lexical retrieval |
| Web Search | Tavily API | Real-time internet context |
| Knowledge Graph | NetworkX | Semantic memory |
| CLI / UI | Rich | Terminal formatting |
| Config | python-dotenv | Environment management |
| PDF Parsing | pypdf | Document ingestion |
| Math / Vectors | NumPy | Cosine similarity |
| Token Counting | tiktoken | Usage tracking |
| Async (available) | aiohttp | Future async support |

---

## Core Technologies (Detailed)

### 1. Python

**Why:** Primary language for AI/ML tooling; rich ecosystem for LLMs, embeddings, and data processing.

**Problem it solves:** Rapid prototyping of multi-agent systems with readable orchestration logic. The entire pipeline fits in ~1,500 lines across 5 modules.

**Interview line:** *"I chose Python because the LLM, embedding, vector DB, and graph libraries all have mature Python bindings, which let me focus on agent architecture rather than infrastructure."*

---

### 2. Groq API + Llama 3.3 70B Versatile

**File:** `nexus/config.py` → `LLMClient`

**Why Groq:**
- **Free tier** with generous rate limits — ideal for a portfolio/research project
- **Extremely fast inference** (custom LPU hardware) — multi-agent pipelines make many LLM calls; latency matters
- **OpenAI-compatible API** — swap providers without rewriting agent code

**Why Llama 3.3 70B:**
- Strong reasoning for JSON-structured agent outputs (planning, parliament, confidence)
- Good balance of quality vs. speed for a 11-agent pipeline

**Problem it solves:** Powers all 8 LLM-backed agents (Planner, Advocate, Prosecutor, Judge, Synthesizer, Confidence, ToolSmith, plus memory extraction). Without a fast, cost-effective LLM backend, the multi-agent design would be impractical.

**Configuration:**
```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

---

### 3. OpenAI Python SDK

**File:** `nexus/config.py`

**Why:** Groq exposes an OpenAI-compatible REST API. Using the official `openai` client means:
- Standard `chat.completions.create()` interface
- Easy migration to OpenAI, Azure OpenAI, or other compatible providers
- Built-in support for `response_format`, tools, and token usage tracking

**Problem it solves:** Provider-agnostic LLM abstraction. Change `base_url` and `api_key` to switch backends.

---

### 4. sentence-transformers (all-MiniLM-L6-v2)

**File:** `nexus/config.py` → `EmbeddingEngine`

**Why local embeddings:**
- **No API cost** for embedding millions of document chunks
- **Privacy** — document content never leaves the machine for embedding
- **Latency** — no network round-trip per query

**Why all-MiniLM-L6-v2 specifically:**
- 384-dimensional vectors — compact and fast
- Well-tested general-purpose model
- ~80MB model size — runs on CPU without GPU

**Problem it solves:** Converts text chunks and user queries into vectors for semantic similarity search. Enables "find documents about the same concept even if they use different words."

**How it's used:**
```python
query_embedding = embedding_engine.embed(query)
# ChromaDB compares via cosine similarity (HNSW index)
```

---

### 5. ChromaDB

**File:** `nexus/agents.py` → `VectorRetriever`

**Why ChromaDB:**
- **Embedded / persistent** — no separate database server to deploy
- **Simple Python API** — `collection.query()`, `collection.upsert()`
- **Built-in HNSW index** with cosine distance
- **Metadata filtering** support for future enhancements

**Problem it solves:** Stores document chunk embeddings and performs fast approximate nearest-neighbor search. This is the "semantic brain" of retrieval — finds conceptually related content.

**Storage:** `data/vectorstore/` (PersistentClient)

---

### 6. rank-bm25 (BM25Okapi)

**File:** `nexus/agents.py` → `KeywordRetriever`

**Why BM25:**
- Classic, proven lexical ranking algorithm (used by Elasticsearch, Lucene)
- **Complements vector search** — catches exact terminology, acronyms, product names that embeddings miss
- Lightweight — pure Python, JSON-backed index

**Problem it solves:** The "semantic mismatch" problem. Example: searching for "GPT-4o" or "ISO 27001" — vector search may return vaguely related docs, but BM25 finds exact matches.

**Storage:** `data/memory/bm25_index.json`

---

### 7. Tavily API (tavily-python)

**File:** `nexus/agents.py` → `WebRetriever`

**Why Tavily:**
- Purpose-built for **LLM/RAG applications** — returns clean, summarized content (not raw HTML)
- Simple API with relevance scores
- Optional — system works without it using local docs only

**Problem it solves:** Local document corpus may be stale or incomplete. Web search adds real-time context for temporal queries ("latest AI regulations 2025").

**When disabled:** If `TAVILY_API_KEY` is missing, web retriever returns empty results gracefully.

---

### 8. Reciprocal Rank Fusion (RRF) — Algorithm, Not a Library

**File:** `nexus/agents.py` → `reciprocal_rank_fusion()`

**Formula:**
```
For each document d across retriever lists:
    RRF_score(d) = Σ  1 / (k + rank_i(d))
where k = 60 (standard constant from Cormack et al.)
```

**Why RRF over simple score averaging:**
- Rank-based — no need to normalize incompatible scores (cosine distance vs BM25 vs Tavily relevance)
- **Cross-retriever confirmation** — docs appearing in multiple lists get naturally boosted
- Proven in hybrid search literature

**Problem it solves:** Intelligently merges three heterogeneous retrieval result sets into one ranked list.

---

### 9. NetworkX

**File:** `nexus/memory.py` → `SemanticMemory`

**Why NetworkX:**
- Mature graph library with shortest-path, degree, and serialization support
- **In-memory DiGraph** — no Neo4j server needed for a portfolio project
- JSON persistence for entities and edges

**Problem it solves:** Builds a growing knowledge graph from every interaction. Enables multi-hop reasoning (e.g., `lithium → batteries → EVs → carbon footprint`) and context injection into future queries.

---

### 10. Rich

**Files:** `nexus/config.py` (formatters), `nexus/main.py` (CLI)

**Why Rich:**
- Beautiful terminal output: panels, tables, trees, markdown rendering, spinners
- Zero frontend needed — full demo runs in terminal
- Great for live interview demos

**Problem it solves:** Makes the multi-agent pipeline **visible** — you see each agent's action, parliament verdict, confidence card, and source table in real time.

---

### 11. python-dotenv

**File:** `nexus/config.py`

**Why:** Keeps API keys out of source code. All configuration loaded from `.env` at startup.

**Problem it solves:** Security and portability — different keys for dev/demo/production without code changes.

---

### 12. pypdf

**File:** `nexus/main.py` → `ingest_file()`

**Why pypdf:**
- Pure Python PDF text extraction
- No external dependencies (unlike pdfplumber with heavier deps)
- Sufficient for text-heavy PDFs

**Problem it solves:** Users can ingest PDF research papers, reports, and documentation into the knowledge base.

---

### 13. NumPy

**File:** `nexus/config.py` → `EmbeddingEngine`

**Why:** Efficient cosine similarity computation between embedding vectors.

**Problem it solves:** Mathematical operations on 384-dim vectors without manual loops.

---

### 14. tiktoken

**File:** Listed in `requirements.txt`

**Why:** Token counting for cost estimation and usage tracking in `LLMClient.get_stats()`.

**Problem it solves:** Visibility into LLM cost and efficiency — important for MLRO's efficiency scoring.

---

## Architecture Pattern: Multi-Agent Orchestration

NEXUS does **not** use LangChain, LlamaIndex, or CrewAI. This is intentional:

| Decision | Rationale |
|----------|-----------|
| **Custom orchestrator** | Full control over the 10-step pipeline; no framework magic |
| **BaseAgent pattern** | Simple inheritance — each agent is a class with an `execute()` method |
| **MessageBus** | Lightweight tracing (trace IDs, message log) without heavy infra |
| **JSON-structured LLM outputs** | Each agent returns typed dicts for reliable pipeline routing |

**Interview line:** *"I built a custom orchestrator rather than using LangChain because I wanted explicit control over agent ordering, retry logic, and memory updates — and to demonstrate I understand the underlying patterns frameworks abstract away."*

---

## Data Flow by Technology

```
                    INGESTION                          QUERY TIME
                    ─────────                          ──────────

PDF/TXT ──► pypdf ──► chunker ──┬──► ChromaDB ◄── sentence-transformers
                                └──► BM25 JSON

User Query ──► Orchestrator
                  │
                  ├──► Episodic Memory (Jaccard, JSON)
                  ├──► Semantic Memory (NetworkX graph)
                  ├──► Procedural Memory (MLRO, JSON)
                  │
                  ├──► Groq/Llama (Planning Agent)
                  │
                  ├──► ChromaDB (vector search)
                  ├──► BM25 (keyword search)
                  ├──► Tavily (web search)
                  ├──► RRF fusion (pure Python)
                  │
                  ├──► Groq/Llama (Advocate, Prosecutor, Judge)
                  ├──► Groq/Llama (Synthesis, Confidence)
                  ├──► Groq/Llama (Tool Smith) + exec()
                  │
                  └──► Rich (display) + JSON memory updates
```

---

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | — | **Required.** Groq API authentication |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model selection |
| `TAVILY_API_KEY` | — | Optional web search |
| `ENABLE_WEB_SEARCH` | `true` | Toggle web retriever |
| `ENABLE_TOOL_SYNTHESIS` | `true` | Toggle SETS |
| `MAX_RETRIEVAL_RESULTS` | `5` | Top-k per retriever |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimum confidence |
| `EMBEDDING_PROVIDER` | `local` | Embedding backend |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## What Technologies Were Considered But Not Used

| Alternative | Why Not Chosen |
|-------------|----------------|
| **LangChain / LlamaIndex** | Wanted custom orchestration to demonstrate architecture skills |
| **Pinecone / Weaviate** | ChromaDB is simpler for local/portfolio deployment (no cloud DB) |
| **Neo4j** | NetworkX sufficient for in-memory knowledge graph at this scale |
| **OpenAI GPT-4** | Groq free tier + speed; OpenAI-compatible client allows easy swap |
| **Elasticsearch** | BM25 via rank-bm25 is lighter for single-machine deployment |
| **FastAPI / Web UI** | CLI-first for simplicity; Rich provides excellent demo UX |

---

## Resume-Ready Tech Keywords

`Python` · `Multi-Agent Systems` · `Agentic RAG` · `Retrieval-Augmented Generation` · `LLM Orchestration` · `Groq API` · `Llama 3.3` · `ChromaDB` · `sentence-transformers` · `BM25` · `Reciprocal Rank Fusion` · `Hybrid Search` · `NetworkX` · `Knowledge Graphs` · `Tavily` · `Epistemic Uncertainty` · `Meta-Learning` · `Rich CLI`
