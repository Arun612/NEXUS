# NEXUS — Complete Project Explanation

> **NEXUS** = **N**euro-**E**pisodic e**X**pert **U**nified **S**ystem  
> A multi-agent Agentic RAG system that answers questions with verification, citations, confidence scores, and continuous learning.

---

## One-Sentence Summary (Elevator Pitch)

**NEXUS is a Python-based multi-agent RAG system where 11 specialized LLM agents collaborate through a 10-step pipeline — combining hybrid retrieval, adversarial document verification, uncertainty scoring, and a three-tier memory system — to produce trustworthy, cited answers that improve over time.**

---

## The Problem With Standard RAG

Most RAG systems follow a simple loop:

```
User Question → Embed Query → Retrieve Chunks → LLM Generates Answer
```

This works for basic Q&A but breaks down when you need:

| Limitation | What Goes Wrong |
|------------|-----------------|
| **Single retrieval method** | Vector search misses exact keywords; keyword search misses semantic meaning |
| **No verification** | LLM may hallucinate or cite irrelevant chunks |
| **No confidence signal** | User cannot tell if the answer is reliable |
| **No memory** | Every query starts from scratch; past mistakes repeat |
| **Complex queries** | "Compare X vs Y" or multi-hop questions fail on one-shot retrieval |
| **Stale knowledge** | Local docs may be outdated; no live web context |

NEXUS was built to address all of these by modeling how a **human expert** researches: remember past work, plan the search, consult multiple sources, debate evidence, quantify uncertainty, and learn from outcomes.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (CLI)                              │
│                    python -m nexus.main                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (core.py)                       │
│         Coordinates 10-step pipeline + 11 agents                │
└───┬─────────────┬──────────────┬──────────────┬─────────────────┘
    │             │              │              │
    ▼             ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐
│ Memory │  │ Planning │  │ Retrieval │  │ Parliament  │
│ Fabric │  │  (GoTQD) │  │  (SPRF)   │  │   (AVP)     │
└────────┘  └──────────┘  └───────────┘  └─────────────┘
    │             │              │              │
    └─────────────┴──────────────┴──────────────┘
                             │
                             ▼
              Synthesis → Confidence → Output → Learn
```

---

## Project Structure (6 Python Modules)

| File | Role | Lines of Responsibility |
|------|------|----------------------|
| `nexus/main.py` | CLI entry point | Document ingestion (PDF/text), user commands, feedback loop |
| `nexus/core.py` | Orchestrator + Message Bus | Runs the full 10-step pipeline |
| `nexus/agents.py` | 11 specialized agents | Planning, retrieval, fusion, parliament, synthesis, confidence, tools |
| `nexus/memory.py` | Cognitive Memory Fabric | Episodic, semantic (graph), procedural (MLRO) memory |
| `nexus/config.py` | Configuration layer | Groq LLM client, embeddings, Rich UI formatters |
| `nexus/__init__.py` | Package marker | — |

**Data directories** (created at runtime):

- `data/vectorstore/` — ChromaDB persistent vector index
- `data/memory/` — JSON files for episodic, semantic, procedural memory + BM25 index
- `data/documents/` — Optional document storage
- `nexus/tools/generated/` — Auto-generated Python tools (SETS)

---

## The 11 Agents

| # | Agent | Purpose |
|---|-------|---------|
| 1 | **PlanningAgent** | Classifies query type; decomposes complex queries into sub-queries (GoTQD) |
| 2 | **VectorRetriever** | Semantic search via ChromaDB + sentence-transformers embeddings |
| 3 | **KeywordRetriever** | BM25 lexical search for exact term matches |
| 4 | **WebRetriever** | Live web search via Tavily API |
| 5 | **AdvocateAgent** | Argues FOR document relevance (Parliament) |
| 6 | **ProsecutorAgent** | Argues AGAINST — finds gaps, outdated info (Parliament) |
| 7 | **JudgeAgent** | Renders ACCEPT / PARTIAL / REJECT verdict |
| 8 | **SynthesisAgent** | Writes final answer with inline citations |
| 9 | **ConfidenceAgent** | Scores answer across 4 dimensions (EUQ) |
| 10 | **ToolSmithAgent** | Generates Python tools for computation (SETS) |
| 11 | **Orchestrator** | Meta-coordinator (not an LLM agent, but the central brain) |

All LLM agents inherit from `BaseAgent`, which wraps Groq API calls via `_llm_call()` and `_llm_call_json()`.

---

## The 10-Step Query Lifecycle

When a user asks a question, the Orchestrator runs these steps in order:

### Step 1 — Recall (Episodic Memory)
- Search past interactions for similar queries using **Jaccard similarity** on word overlap
- If a match exists, surface prior confidence and strategy context

### Step 2 — Strategize (Procedural Memory / MLRO)
- Planning agent classifies query: `factual`, `comparison`, `multi-hop`, `temporal`, `creative`, `analytical`
- Procedural memory recommends the best retrieval strategy based on historical success rates

### Step 3 — Decompose (GoTQD)
- Simple queries → single sub-query
- Complex queries → DAG of sub-queries with dependencies
- Example: *"Compare lithium vs sodium-ion batteries"* → 3 sub-queries (two independent + one dependent comparison)

### Step 4 — Retrieve (SPRF)
- Run **Vector + Keyword + Web** retrieval in parallel (based on strategy)
- Merge results with **Reciprocal Rank Fusion (RRF)** — documents found by multiple retrievers rank higher
- Apply **diversity penalty** so one retriever cannot dominate

### Step 5 — Verify (Adversarial Verification Parliament)
- **Advocate** argues documents are relevant and accurate
- **Prosecutor** challenges quality, recency, completeness
- **Judge** decides: **ACCEPT**, **PARTIAL** (drop bad docs), or **REJECT** (re-retrieve with refined query)

### Step 6 — Compute (SETS)
- Tool Smith checks if math/data processing is needed
- If yes, generates Python functions, executes them, saves for reuse

### Step 7 — Synthesize
- Synthesis agent writes answer using **only verified sources**
- Includes markdown formatting and inline citations `[Source 1]`, `[Source 2]`

### Step 8 — Score Confidence (EUQ)
- Four dimensions: factual accuracy, source agreement, temporal relevance, coverage
- Surfaces **flags**, **known unknowns**, and **follow-up suggestions**

### Step 9 — Present
- Rich terminal UI: answer panel, confidence card, source table
- User can give 👍/👎 feedback

### Step 10 — Learn
- **Episodic**: log full interaction trace
- **Semantic**: extract entities/relations into NetworkX knowledge graph
- **Procedural**: update strategy success rates for MLRO

---

## The 7 Core Innovations

### 1. Cognitive Memory Fabric (CMF)
Three memory tiers inspired by neuroscience:

| Tier | Analogy | Storage | Function |
|------|---------|---------|----------|
| Episodic | Diary | `episodic.json` | Records every query lifecycle |
| Semantic | Textbook | NetworkX graph in `semantic.json` | Growing knowledge graph with multi-hop paths |
| Procedural | Muscle memory | `procedural.json` | Strategy performance matrix (MLRO) |

A **Memory Consolidator** can batch-compress episodic logs into semantic knowledge (like sleep consolidation).

### 2. Adversarial Verification Parliament (AVP)
Three-agent debate **before** answer generation — reduces hallucination by filtering bad context upstream.

### 3. Speculative Parallel Retrieval + Fusion (SPRF)
Hybrid retrieval with RRF fusion. Documents confirmed across vector, keyword, and web search get boosted confidence.

### 4. Graph-of-Thought Query Decomposition (GoTQD)
Complex queries become a directed acyclic graph (DAG) of sub-queries. Independent nodes can run in parallel.

### 5. Meta-Learning Retrieval Optimizer (MLRO)
Learns which strategies work per query type using:

```
score = 0.5 × success_rate + 0.3 × avg_confidence + 0.2 × efficiency
```

### 6. Epistemic Uncertainty Quantification (EUQ)
Multi-dimensional confidence instead of false LLM certainty. Explicitly lists what the system does **not** know.

### 7. Self-Evolving Tool Synthesis (SETS)
Dynamic Python tool generation for computation tasks LLMs handle poorly (math, data transforms).

---

## Document Ingestion Flow

```
PDF or TXT file
    │
    ▼
Extract text (pypdf for PDF)
    │
    ▼
Smart chunking (~1500 chars, 200 overlap, paragraph-aware)
    │
    ├──► ChromaDB (vector embeddings via all-MiniLM-L6-v2)
    └──► BM25 index (JSON-backed lexical index)
```

CLI command: `/ingest path/to/document.pdf`

---

## Example Walkthrough

**Query:** *"Compare lithium and sodium-ion batteries for grid storage"*

1. **Memory** — No similar past query
2. **Strategy** — MLRO recommends `gotqd` + `vector+web` for comparison queries
3. **GoTQD** — 3 sub-queries: lithium advantages, sodium-ion advantages, direct comparison
4. **SPRF** — Vector finds 3 docs, web finds 4 → RRF merges to 5 unique docs
5. **Parliament** — Advocate: 4/5 relevant | Prosecutor: one doc from 2019 | Judge: **PARTIAL**
6. **Tool Smith** — No computation needed
7. **Synthesis** — Structured comparison with citations
8. **Confidence** — Overall ~81% (temporal score lower due to older doc)
9. **Display** — Answer + confidence card + source table
10. **Memory** — Episode logged; entities (lithium, sodium-ion, grid storage) added to graph

---

## How to Run (For Demo / Interview)

```bash
# Install
pip install -r requirements.txt

# Configure .env
GROQ_API_KEY=your-key
TAVILY_API_KEY=your-key   # optional, for web search

# Run
python -m nexus.main

# Ingest documents
NEXUS> /ingest path/to/document.pdf

# Ask questions
NEXUS> What are the key concepts in agentic RAG?

# View learning stats
NEXUS> /stats
```

---

## Key Metrics You Can Mention on a Resume

- **11 specialized agents** orchestrated through a **10-step pipeline**
- **3 retrieval modalities** fused with Reciprocal Rank Fusion
- **3-tier memory system** with meta-learning strategy optimization
- **4-dimensional confidence scoring** with explicit uncertainty surfacing
- **Hybrid local + cloud stack**: local embeddings, Groq LLM API, optional Tavily web search

---

## Related Documentation

| File | Contents |
|------|----------|
| [NEXUS_TECHNOLOGY_STACK.md](./NEXUS_TECHNOLOGY_STACK.md) | Every technology, why it was chosen |
| [NEXUS_INTERVIEW_PREP.md](./NEXUS_INTERVIEW_PREP.md) | Resume bullets, Q&A, talking points |
| [NEXUS_COMPARISON_AND_IMPROVEMENTS.md](./NEXUS_COMPARISON_AND_IMPROVEMENTS.md) | vs standard RAG, future roadmap |
| `../walkthrough.md` | Detailed file-by-file code walkthrough |
| `../nexus_architecture.md` | Mermaid architecture diagram |
