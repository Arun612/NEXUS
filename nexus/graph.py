"""
NEXUS Graph — LangGraph StateGraph wiring.
Builds and compiles the 10-step query lifecycle as a directed graph
with one conditional loop (parliament REJECT → re-retrieve).
"""

from langgraph.graph import StateGraph, END, START

from nexus.state import NexusState
from nexus.nodes import NexusNodes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Routing Functions (conditional edges)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _route_after_retrieval(state: NexusState) -> str:
    """After SPRF retrieval: go to parliament if docs found, else fallback."""
    if not state.get("documents"):
        return "fallback_answer"
    return "parliament"


def _make_verdict_router(max_retries: int):
    """
    Factory: returns a routing function that checks the parliament verdict.
    REJECT (with retries remaining) → loop back to refine_and_retry.
    ACCEPT / PARTIAL / max retries hit → proceed to tool_smith.
    """

    def _route_after_verdict(state: NexusState) -> str:
        verdict = state.get("verdict", {})
        retry_count = state.get("retry_count", 0)

        if (
            verdict.get("decision") == "REJECT"
            and verdict.get("refined_query")
            and retry_count < max_retries
        ):
            return "refine_and_retry"
        return "tool_smith"

    return _route_after_verdict


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Graph Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_graph(nodes: NexusNodes, *, max_retries: int = 3):
    """
    Assemble the NEXUS pipeline as a compiled LangGraph StateGraph.

    Graph topology:

        START
          │
          ▼
        check_memory
          │
          ▼
        plan_and_strategize
          │
          ▼
        retrieve  ◄─────────────────┐
          │                         │
          ├── (no docs) ─▶ fallback │
          │                  │      │
          ▼                  │      │
        parliament           │      │
          │                  │      │
          ├── REJECT ────────┼──▶ refine_and_retry
          │                  │
          ▼                  │
        tool_smith           │
          │                  │
          ▼                  │
        synthesize           │
          │                  │
          ▼                  │
        score_confidence     │
          │                  │
          ▼                  │
        display_results  ◄───┘
          │
          ▼
        update_memory
          │
          ▼
         END
    """
    builder = StateGraph(NexusState)

    # ── Register nodes ──────────────────────────────────────
    builder.add_node("check_memory",        nodes.check_memory)
    builder.add_node("plan_and_strategize", nodes.plan_and_strategize)
    builder.add_node("retrieve",            nodes.retrieve)
    builder.add_node("fallback_answer",     nodes.fallback_answer)
    builder.add_node("parliament",          nodes.parliament)
    builder.add_node("refine_and_retry",    nodes.refine_and_retry)
    builder.add_node("tool_smith",          nodes.tool_smith_node)
    builder.add_node("synthesize",          nodes.synthesize)
    builder.add_node("score_confidence",    nodes.score_confidence)
    builder.add_node("display_results",     nodes.display_results)
    builder.add_node("update_memory",       nodes.update_memory)

    # ── Linear edges ────────────────────────────────────────
    builder.add_edge(START, "check_memory")
    builder.add_edge("check_memory",        "plan_and_strategize")
    builder.add_edge("plan_and_strategize", "retrieve")

    # ── Conditional: after retrieval ────────────────────────
    builder.add_conditional_edges(
        "retrieve",
        _route_after_retrieval,
        {
            "fallback_answer": "fallback_answer",
            "parliament":      "parliament",
        },
    )

    # Fallback path → display → memory → END
    builder.add_edge("fallback_answer", "display_results")

    # ── Conditional: after parliament verdict ───────────────
    builder.add_conditional_edges(
        "parliament",
        _make_verdict_router(max_retries),
        {
            "refine_and_retry": "refine_and_retry",
            "tool_smith":       "tool_smith",
        },
    )

    # REJECT loop: refine → re-retrieve
    builder.add_edge("refine_and_retry", "retrieve")

    # Happy path: tool_smith → synthesize → confidence → display → memory → END
    builder.add_edge("tool_smith",       "synthesize")
    builder.add_edge("synthesize",       "score_confidence")
    builder.add_edge("score_confidence", "display_results")
    builder.add_edge("display_results",  "update_memory")
    builder.add_edge("update_memory",    END)

    return builder.compile()
