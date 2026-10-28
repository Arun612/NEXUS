# NEXUS — Interview Preparation Guide

> Resume bullets, talking points, common interview questions, and demo script.

---

## 30-Second Elevator Pitch

*"I built NEXUS — a multi-agent RAG system where 11 specialized AI agents work together to answer questions. Instead of the typical retrieve-and-generate pipeline, NEXUS uses hybrid retrieval across vector, keyword, and web search; an adversarial verification step where agents debate document quality before answering; multi-dimensional confidence scoring; and a three-tier memory system that learns which strategies work best over time. It's built in Python using Groq's Llama model, ChromaDB, and BM25, with about 1,500 lines of orchestration code."*

---

## 2-Minute Deep Pitch

*"Standard RAG systems retrieve documents once and generate an answer — they hallucinate, can't handle complex multi-part questions, and never learn from mistakes.*

*NEXUS fixes this with seven architectural innovations. First, a Cognitive Memory Fabric with episodic, semantic, and procedural memory — so the system remembers past queries and learns optimal retrieval strategies. Second, an Adversarial Verification Parliament where three agents debate whether retrieved documents are actually good before any answer is written. Third, Speculative Parallel Retrieval that runs vector search, BM25 keyword search, and web search simultaneously, then fuses results with Reciprocal Rank Fusion.*

*For complex queries, a Planning Agent decomposes them into a graph of sub-queries. Every answer gets scored across four confidence dimensions — factual accuracy, source agreement, temporal relevance, and coverage — with explicit 'known unknowns' surfaced to the user. And when computation is needed, a Tool Smith agent dynamically generates Python functions.*

*The whole system runs as a Python CLI with about 11 agents coordinated by a central Orchestrator through a 10-step pipeline. I chose Groq for fast free inference, ChromaDB for local vector storage, and built custom orchestration rather than using LangChain to have full control over the agent workflow."*

---

## Resume Bullet Points (Pick 2–4)

**Option A — Architecture focused:**
> Designed and implemented NEXUS, a multi-agent Agentic RAG system with 11 specialized LLM agents orchestrated through a 10-step pipeline featuring hybrid retrieval, adversarial document verification, and three-tier cognitive memory.

**Option B — Technical depth:**
> Built hybrid search pipeline combining ChromaDB vector search, BM25 lexical retrieval, and Tavily web search with Reciprocal Rank Fusion; reduced irrelevant context via 3-agent adversarial verification parliament before answer generation.

**Option C — ML / Learning:**
> Implemented meta-learning retrieval optimizer (MLRO) that tracks strategy performance per query type and automatically routes future queries through historically optimal retrieval pathways based on success rate, confidence, and token efficiency.

**Option D — Full stack:**
> Developed Python CLI application integrating Groq Llama 3.3 70B, sentence-transformers embeddings, ChromaDB, NetworkX knowledge graphs, and Rich terminal UI for document ingestion, Q&A, and real-time agent trace visualization.

**Option E — Problem-solving:**
> Addressed key RAG failure modes — hallucination, stale knowledge, complex query handling, and false confidence — through adversarial verification, multi-source fusion, query decomposition, and epistemic uncertainty quantification.

---

## STAR Story Template

**Situation:** *"I wanted to build a RAG system that went beyond simple retrieve-and-generate, because I noticed standard RAG hallucinates on complex questions and provides no confidence signal."*

**Task:** *"Design a system that verifies retrieved context before generating answers, handles multi-part queries, and improves its retrieval strategy over time."*

**Action:** *"I architected NEXUS with 7 innovations: a three-tier memory system, hybrid retrieval with RRF fusion, a three-agent verification parliament, query decomposition into DAGs, meta-learning strategy optimization, four-dimensional confidence scoring, and dynamic tool synthesis. I implemented 11 agents in Python with a custom Orchestrator, using Groq for inference and ChromaDB + BM25 for retrieval."*

**Result:** *"The system produces cited answers with confidence scores, filters outdated documents via adversarial verification, learns optimal strategies per query type through user feedback, and builds a growing knowledge graph from every interaction."*

---

## Common Interview Questions & Answers

### Q1: "What is NEXUS and what problem does it solve?"

**Answer:** NEXUS is a multi-agent RAG system. Standard RAG has four main problems: (1) single retrieval method misses relevant docs, (2) no verification leads to hallucination, (3) complex queries fail on one-shot retrieval, and (4) no learning across sessions. NEXUS solves these with hybrid retrieval + fusion, an adversarial verification parliament, query decomposition, and a three-tier memory system with meta-learning.

---

### Q2: "Why multi-agent instead of a single LLM call?"

**Answer:** Separation of concerns. Each agent has a focused role and a specialized system prompt — the Prosecutor is tuned to find flaws, the Synthesizer is tuned to cite sources, the Confidence agent is tuned to be skeptical. A single prompt trying to do all of this would be unreliable. Multi-agent also enables the verification parliament pattern — genuine adversarial debate requires separate agents with opposing objectives.

---

### Q3: "Explain your retrieval strategy."

**Answer:** I use three parallel retrievers — vector (ChromaDB + sentence-transformers for semantic similarity), keyword (BM25 for exact term matching), and web (Tavily for real-time info). Results are merged using Reciprocal Rank Fusion, which is rank-based so I don't need to normalize incompatible scores. Documents found by multiple retrievers get naturally boosted. A diversity penalty prevents any single retriever from dominating the top results.

---

### Q4: "What is the Verification Parliament?"

**Answer:** Before generating any answer, three agents debate the retrieved documents. The Advocate argues they're relevant and accurate. The Prosecutor challenges them — finding outdated info, irrelevant chunks, or gaps. The Judge weighs both arguments and renders ACCEPT (use all docs), PARTIAL (drop bad docs), or REJECT (re-retrieve with a refined query). This catches bad context upstream, before the LLM can hallucinate from it.

---

### Q5: "How does the memory system work?"

**Answer:** Three tiers inspired by human cognition:
- **Episodic** — logs every interaction (query, strategy, confidence, feedback) as JSON episodes
- **Semantic** — a NetworkX knowledge graph that grows with extracted entities and relationships from every answer
- **Procedural (MLRO)** — tracks which retrieval strategies succeed for each query type, using a weighted score of success rate, confidence, and token efficiency

After enough interactions, the system automatically routes comparison queries through GoTQD decomposition and factual queries through direct retrieval, based on what historically worked.

---

### Q6: "Why Groq instead of OpenAI?"

**Answer:** Three reasons: (1) free tier for development and demos, (2) extremely fast inference — critical when you're making 6–8 LLM calls per query, (3) OpenAI-compatible API so I can swap to GPT-4 or Azure OpenAI by changing two config values. Llama 3.3 70B handles structured JSON outputs well, which every agent relies on.

---

### Q7: "Why not use LangChain or LlamaIndex?"

**Answer:** I wanted to demonstrate I understand the underlying patterns — orchestration, retrieval fusion, agent communication — not just framework configuration. A custom Orchestrator gives me explicit control over step ordering, retry on REJECT verdicts, and memory updates. That said, the architecture maps cleanly to LangGraph nodes if I wanted to migrate later.

---

### Q8: "How do you handle hallucination?"

**Answer:** Three layers: (1) the Verification Parliament filters bad documents before synthesis, (2) the Synthesis agent is instructed to use ONLY provided documents with inline citations, (3) the Confidence agent scores factual accuracy and source agreement, surfacing flags and known unknowns. If no documents are retrieved at all, the system explicitly falls back to LLM knowledge with low confidence (40%).

---

### Q9: "What is GoTQD?"

**Answer:** Graph-of-Thought Query Decomposition. The Planning Agent breaks complex queries into sub-queries arranged as a DAG. For "Compare X and Y," it creates independent sub-queries for X and Y, plus a dependent comparison query. Independent sub-queries can be retrieved in parallel. This enables multi-hop reasoning that single-shot retrieval cannot handle.

---

### Q10: "What is EUQ — Epistemic Uncertainty Quantification?"

**Answer:** Instead of the LLM saying "I'm confident" (which LLMs always do), a dedicated Confidence Agent scores the answer on four dimensions: factual accuracy, source agreement, temporal relevance, and coverage. It also explicitly lists "unknowns" — things the system knows it doesn't know — and suggests follow-up questions. This gives the user an honest reliability signal.

---

### Q11: "Walk me through the code architecture."

**Answer:**
- `main.py` — CLI entry, document ingestion, user feedback
- `core.py` — Orchestrator runs the 10-step pipeline; MessageBus for tracing
- `agents.py` — All 11 agents + RRF fusion functions
- `memory.py` — Episodic, Semantic (NetworkX), Procedural (MLRO) memory
- `config.py` — Groq LLM client, embedding engine, Rich formatters, dataclass config

The Orchestrator initializes everything in `__init__` and `execute()` runs steps 1–10 sequentially, calling agent `.execute()` methods and updating memory at the end.

---

### Q12: "What was the hardest part?"

**Answer (pick what resonates):**
- *"Designing the Orchestrator to handle the REJECT → re-retrieve loop without infinite retries, while keeping the pipeline readable."*
- *"Getting RRF fusion to work well when retrievers return different numbers of results with incompatible score scales."*
- *"Balancing LLM call count (cost/latency) vs. verification quality — the parliament adds 3 extra calls but significantly reduces hallucination."*

---

### Q13: "How would you scale this?"

**Answer:** See [NEXUS_COMPARISON_AND_IMPROVEMENTS.md](./NEXUS_COMPARISON_AND_IMPROVEMENTS.md). Key points: async parallel agent calls, replace ChromaDB with Pinecone/Weaviate, add FastAPI + React frontend, use Redis for episodic memory, deploy Tool Smith in sandboxed containers, add evaluation benchmarks (RAGAS, DeepEval).

---

### Q14: "Show me a trade-off you made."

**Answer:** *"I use Jaccard similarity for episodic memory instead of embedding-based similarity. Jaccard is faster and requires no API calls, but it misses semantic similarity ('battery' vs 'energy storage'). I chose it for simplicity and speed in a portfolio project, but I'd upgrade to embedding similarity in production."*

---

## Demo Script (5 Minutes)

1. **Start the system:** `python -m nexus.main`
2. **Show empty state:** `/stats` — 0 documents, 0 episodes
3. **Ingest a document:** `/ingest sample.pdf` — show chunk count
4. **Ask a simple question:** Watch agents execute steps 1–10 in the terminal
5. **Point out:** Parliament verdict, confidence card, source table
6. **Ask a complex question:** *"Compare X and Y"* — show GoTQD decomposition
7. **Give feedback:** 👍 — explain MLRO learning
8. **Show learning:** `/stats` — performance matrix with strategy records

---

## Questions to Ask the Interviewer

- "How does your team handle RAG evaluation — automated benchmarks or human review?"
- "Do you use multi-agent patterns in production, or single-chain orchestration?"
- "What's your approach to confidence calibration in LLM outputs?"

---

## Red Flags to Avoid

| Don't Say | Say Instead |
|-----------|-------------|
| "It never hallucinates" | "It reduces hallucination through verification and citation constraints" |
| "11 agents means 11x better" | "Specialized agents with focused prompts improve reliability over monolithic prompts" |
| "It's production-ready" | "It's a research/portfolio system; here's what I'd add for production..." |
| "I invented RRF / BM25" | "I applied established techniques — RRF from Cormack et al., BM25 from information retrieval literature" |

---

## Quick Reference Numbers

| Metric | Value |
|--------|-------|
| Python modules | 5 (+ `__init__.py`) |
| Specialized agents | 11 |
| Pipeline steps | 10 |
| Core innovations | 7 |
| Retrieval methods | 3 (vector, keyword, web) |
| Memory tiers | 3 (episodic, semantic, procedural) |
| Confidence dimensions | 4 |
| LLM calls per query | ~6–8 |
| Embedding model | all-MiniLM-L6-v2 (384-dim) |
| Default LLM | Llama 3.3 70B via Groq |
| RRF constant k | 60 |
