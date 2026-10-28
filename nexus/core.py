"""
NEXUS Core — LangGraph-powered Orchestrator.
The Orchestrator initializes all components and delegates the full
10-step query lifecycle to a compiled LangGraph StateGraph.
"""

import time
import logging

from nexus.config import NexusConfig, LLMClient, console
from nexus.agents import (
    PlanningAgent, VectorRetriever, KeywordRetriever, WebRetriever,
    AdvocateAgent, ProsecutorAgent, JudgeAgent,
    SynthesisAgent, ConfidenceAgent, ToolSmithAgent,
)
from nexus.memory import EpisodicMemory, SemanticMemory, ProceduralMemory
from nexus.nodes import NexusNodes
from nexus.graph import build_graph

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Message Bus — trace-ID generator (kept for compatibility)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MessageBus:
    """Lightweight trace-ID generator and message counter."""

    def __init__(self):
        self._message_log = []
        self._trace_counter = 0

    def generate_trace_id(self):
        """Generate a unique trace ID for each query lifecycle."""
        self._trace_counter += 1
        return f"trace_{int(time.time())}_{self._trace_counter}"

    def get_stats(self):
        return {"total_messages": len(self._message_log)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Orchestrator — wraps the compiled LangGraph
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Orchestrator:
    """
    Coordinates the full NEXUS query lifecycle (10 steps)
    via a compiled LangGraph StateGraph.

    The public API is identical to the original imperative Orchestrator:
      • execute(query)         → run the full pipeline
      • ingest_documents(docs) → add docs to vector + keyword indexes
      • get_system_stats()     → return system-wide metrics
    """

    def __init__(self, config: NexusConfig):
        self.config = config
        self.llm_client = LLMClient(config.llm)
        self.message_bus = MessageBus()

        # ── Initialize all agents (unchanged) ───────────────
        self.planner = PlanningAgent(self.llm_client)
        self.vector_retriever = VectorRetriever(
            self.llm_client, config.retrieval, config.embedding,
            config.system.vectorstore_path,
        )
        self.keyword_retriever = KeywordRetriever(self.llm_client, config.retrieval)
        self.web_retriever = WebRetriever(self.llm_client, config.retrieval)
        self.advocate = AdvocateAgent(self.llm_client)
        self.prosecutor = ProsecutorAgent(self.llm_client)
        self.judge = JudgeAgent(self.llm_client)
        self.synthesizer = SynthesisAgent(self.llm_client)
        self.confidence_agent = ConfidenceAgent(self.llm_client)
        self.tool_smith = ToolSmithAgent(self.llm_client)

        # ── Initialize memory systems (unchanged) ──────────
        self.episodic = EpisodicMemory(
            config.memory.episodic_path, config.memory.max_episodic_entries,
        )
        self.semantic = SemanticMemory(config.memory.semantic_path)
        self.procedural = ProceduralMemory(config.memory.procedural_path)

        # ── Build LangGraph ─────────────────────────────────
        self._nodes = NexusNodes(
            config=config,
            llm_client=self.llm_client,
            planner=self.planner,
            vector_retriever=self.vector_retriever,
            keyword_retriever=self.keyword_retriever,
            web_retriever=self.web_retriever,
            advocate=self.advocate,
            prosecutor=self.prosecutor,
            judge=self.judge,
            synthesizer=self.synthesizer,
            confidence_agent=self.confidence_agent,
            tool_smith=self.tool_smith,
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
        )
        self._graph = build_graph(
            self._nodes,
            max_retries=config.retrieval.max_retries,
        )

    # ─────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────

    def execute(self, query):
        """Execute the full 10-step NEXUS pipeline via LangGraph."""
        console.print(f"\n  🔍 [bold]Processing query:[/bold] {query}\n")

        initial_state = {
            "query": query,
            "active_query": query,
            "trace_id": self.message_bus.generate_trace_id(),
            "start_time": time.time(),
            "retry_count": 0,
        }

        final_state = self._graph.invoke(initial_state)

        return final_state.get("result", {
            "answer": "No answer generated.",
            "confidence": {"overall": 0.0},
            "sources": [],
            "trace_id": initial_state["trace_id"],
            "duration_ms": 0,
        })

    def ingest_documents(self, documents):
        """Ingest documents into both vector and keyword indexes."""
        self.vector_retriever.ingest_documents(documents)
        self.keyword_retriever.ingest_documents(documents)
        console.print(f"  ✅ Ingested {len(documents)} documents into NEXUS")

    def get_system_stats(self):
        """Return comprehensive system statistics."""
        return {
            "llm": self.llm_client.get_stats(),
            "message_bus": self.message_bus.get_stats(),
            "memory": {
                "episodic_entries": len(self.episodic.episodes),
                "semantic_entities": len(self.semantic.entities),
                "procedural_records": len(self.procedural.records),
            },
            "vectorstore_docs": self.vector_retriever.get_document_count(),
            "performance_matrix": self.procedural.get_performance_matrix(),
        }
