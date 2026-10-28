"""
NEXUS State — Shared LangGraph state definition.
This TypedDict flows through every node in the graph.
Each node reads what it needs and returns partial updates.
"""

from typing import TypedDict


class NexusState(TypedDict, total=False):
    """
    Complete state for the NEXUS query lifecycle graph.
    Using total=False so nodes can return partial updates.
    """

    # ── Input ──────────────────────────────────────────────
    query: str                    # Original user query (never mutated)
    active_query: str             # Current query for retrieval/parliament (refined on retry)

    # ── Tracing ────────────────────────────────────────────
    trace_id: str
    start_time: float

    # ── Step 1: Memory ─────────────────────────────────────
    similar_episodes: list        # Past episodes matching this query
    memory_context: str           # Knowledge-graph context string

    # ── Steps 2–3: Planning (GoTQD + MLRO) ─────────────────
    plan: dict                    # Full planner output
    query_type: str               # factual | comparison | multi-hop | ...
    complexity: str               # simple | moderate | complex
    strategy_recommendation: dict # MLRO recommendation
    sub_queries: list             # DAG of sub-queries

    # ── Step 4: Retrieval (SPRF) ───────────────────────────
    documents: list               # Fused & diversified document list

    # ── Step 5: Parliament (AVP) ───────────────────────────
    verdict: dict                 # Judge's verdict + scores
    retry_count: int              # Number of REJECT→re-retrieve cycles

    # ── Step 6: Tool Smith (SETS) ──────────────────────────
    tool_result: dict             # ToolSmith status
    computation_results: list     # Results from synthesized tools

    # ── Steps 7–8: Synthesis + Confidence (EUQ) ────────────
    answer: str                   # Final synthesized answer
    sources: list                 # Source metadata for citations
    confidence: dict              # Multi-dimensional confidence scores

    # ── Output ─────────────────────────────────────────────
    duration_ms: float
    result: dict                  # Final result dict returned to caller
