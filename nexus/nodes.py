"""
NEXUS Nodes — Each function is one step in the LangGraph pipeline.
Nodes read from NexusState and return partial state updates.
All agent classes (agents.py) and memory systems (memory.py) are unchanged;
these node functions simply call into them.
"""

import time
import logging

from nexus.state import NexusState
from nexus.config import (
    console, print_agent_action, print_confidence_card,
    print_sources, print_query_plan, print_answer,
    print_memory_update, print_parliament_verdict,
)
from nexus.agents import reciprocal_rank_fusion, apply_diversity_penalty
from nexus.memory import Episode

logger = logging.getLogger(__name__)


class NexusNodes:
    """
    Holds references to every agent and memory system.
    Each public method is a LangGraph node: takes NexusState, returns partial dict.
    """

    def __init__(self, *, config, llm_client, planner, vector_retriever,
                 keyword_retriever, web_retriever, advocate, prosecutor,
                 judge, synthesizer, confidence_agent, tool_smith,
                 episodic, semantic, procedural):
        self.config = config
        self.llm = llm_client
        self.planner = planner
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.web_retriever = web_retriever
        self.advocate = advocate
        self.prosecutor = prosecutor
        self.judge = judge
        self.synthesizer = synthesizer
        self.confidence_agent = confidence_agent
        self.tool_smith = tool_smith
        self.episodic = episodic
        self.semantic = semantic
        self.procedural = procedural

    # ─────────────────────────────────────────────────────────
    #  Step 1  ·  Check Episodic + Semantic Memory
    # ─────────────────────────────────────────────────────────

    def check_memory(self, state: NexusState) -> dict:
        """Recall similar past interactions and pull knowledge-graph context."""
        query = state["query"]
        print_agent_action("Orchestrator", "Checking memory for similar past queries...")

        similar_episodes = self.episodic.find_similar(query)
        memory_context = self.semantic.get_context_for_query(query)

        if similar_episodes:
            best = similar_episodes[0]
            print_agent_action(
                "Orchestrator",
                f"Found similar past query (confidence: {best.confidence_score:.0%})",
                f'Past query: "{best.query[:60]}..."',
            )

        return {
            "similar_episodes": similar_episodes,
            "memory_context": memory_context,
        }

    # ─────────────────────────────────────────────────────────
    #  Steps 2-3  ·  Planning (GoTQD) + Strategy (MLRO)
    # ─────────────────────────────────────────────────────────

    def plan_and_strategize(self, state: NexusState) -> dict:
        """Classify query, get MLRO strategy recommendation, and decompose if needed."""
        query = state["query"]
        memory_context = state.get("memory_context", "")

        # Run Planning Agent (GoTQD — Concept #4)
        plan = self.planner.execute(query, memory_context)
        query_type = plan.get("query_type", "factual")
        complexity = plan.get("complexity", "simple")

        # Consult Procedural Memory (MLRO — Concept #5)
        recommendation = self.procedural.recommend_strategy(query_type)
        print_agent_action(
            "Orchestrator",
            f"Query classified: {query_type} ({complexity})",
            f"Recommended strategy: {recommendation.get('strategy', 'direct')}",
        )

        # Display decomposition plan if applicable
        if plan.get("needs_decomposition", False):
            print_agent_action("Planner", "Decomposing query into sub-queries (GoTQD)...")
            print_query_plan(plan)
        else:
            print_agent_action("Planner", "Simple query — no decomposition needed")

        sub_queries = plan.get(
            "sub_queries",
            [{"id": "Q1", "query": query, "depends_on": [], "strategy": "vector+web"}],
        )

        return {
            "plan": plan,
            "query_type": query_type,
            "complexity": complexity,
            "strategy_recommendation": recommendation,
            "sub_queries": sub_queries,
        }

    # ─────────────────────────────────────────────────────────
    #  Step 4  ·  Speculative Parallel Retrieval Fusion (SPRF)
    # ─────────────────────────────────────────────────────────

    def retrieve(self, state: NexusState) -> dict:
        """Run vector + keyword + web retrieval, then fuse with RRF."""
        sub_queries = state["sub_queries"]
        print_agent_action("Orchestrator", "Launching parallel retrieval (SPRF)...")

        all_results = {"vector": [], "keyword": [], "web": []}

        for sq in sub_queries:
            strategy = sq.get("strategy", "vector+web")
            sq_query = sq.get("query", "")

            # Always run vector search
            print_agent_action("VectorRetriever", f'Searching: "{sq_query[:50]}..."')
            vec_result = self.vector_retriever.execute(sq_query)
            all_results["vector"].extend(vec_result.get("documents", []))

            # Keyword search if strategy calls for it
            if "keyword" in strategy:
                print_agent_action("KeywordRetriever", f'Searching: "{sq_query[:50]}..."')
                kw_result = self.keyword_retriever.execute(sq_query)
                all_results["keyword"].extend(kw_result.get("documents", []))

            # Web search if enabled and strategy calls for it
            if "web" in strategy and self.config.retrieval.enable_web_search:
                print_agent_action("WebRetriever", f'Searching: "{sq_query[:50]}..."')
                web_result = self.web_retriever.execute(sq_query)
                all_results["web"].extend(web_result.get("documents", []))

        # Reciprocal Rank Fusion (core of SPRF — Concept #3)
        result_lists = [v for v in all_results.values() if v]
        if not result_lists:
            return {"documents": []}

        fused = reciprocal_rank_fusion(result_lists)
        documents = apply_diversity_penalty(fused)

        console.print(f"  📄 Retrieved [bold]{len(documents)}[/bold] documents total\n")
        return {"documents": documents}

    # ─────────────────────────────────────────────────────────
    #  Fallback  ·  LLM-only answer when no documents found
    # ─────────────────────────────────────────────────────────

    def fallback_answer(self, state: NexusState) -> dict:
        """Generate an answer purely from LLM knowledge (no retrieved docs)."""
        query = state["query"]
        print_agent_action("Orchestrator", "⚠️  No documents — using LLM knowledge only")

        answer = self.llm.chat_with_system(
            "Answer the question to the best of your knowledge. "
            "Be clear about uncertainty.",
            query,
        )
        return {
            "answer": answer,
            "confidence": {
                "overall": 0.4,
                "factual_accuracy": 0.4,
                "source_agreement": 0.0,
                "temporal_relevance": 0.5,
                "coverage": 0.5,
                "flags": ["No documents retrieved — answer is from LLM knowledge only"],
                "unknowns": [],
                "suggestions": ["Try ingesting relevant documents for better results"],
            },
            "sources": [],
            "verdict": {"decision": "SKIP"},
        }

    # ─────────────────────────────────────────────────────────
    #  Step 5  ·  Adversarial Verification Parliament (AVP)
    # ─────────────────────────────────────────────────────────

    def parliament(self, state: NexusState) -> dict:
        """Three-agent debate: Advocate (FOR), Prosecutor (AGAINST), Judge (VERDICT)."""
        active_query = state.get("active_query", state["query"])
        documents = state["documents"]
        top_docs = documents[: self.config.retrieval.max_results]

        print_agent_action("Orchestrator", "Convening Verification Parliament...")

        # Advocate argues FOR relevance
        print_agent_action("Advocate", "Arguing FOR document relevance...")
        advocate_result = self.advocate.execute(active_query, top_docs)

        # Prosecutor argues AGAINST
        print_agent_action("Prosecutor", "Challenging document quality...")
        prosecutor_result = self.prosecutor.execute(active_query, top_docs)

        # Judge weighs evidence
        print_agent_action("Judge", "Rendering verdict...")
        verdict = self.judge.execute(active_query, advocate_result, prosecutor_result, top_docs)

        print_parliament_verdict(verdict)

        # Filter rejected documents if PARTIAL
        if verdict.get("decision") == "PARTIAL":
            rejected_ids = set(verdict.get("rejected_doc_ids", []))
            if rejected_ids:
                documents = [d for d in documents if d.get("id") not in rejected_ids]

        return {"verdict": verdict, "documents": documents}

    # ─────────────────────────────────────────────────────────
    #  REJECT loop  ·  Refine the query and re-retrieve
    # ─────────────────────────────────────────────────────────

    def refine_and_retry(self, state: NexusState) -> dict:
        """Build a refined sub-query from the Judge's suggestion and loop back to retrieve."""
        verdict = state["verdict"]
        retry_count = state.get("retry_count", 0)

        refined_query = verdict.get("refined_query", state["query"])
        console.print("\n  🔄 [yellow]Re-retrieving with refined query...[/yellow]")

        return {
            "active_query": refined_query,
            "sub_queries": [
                {"id": "R1", "query": refined_query, "depends_on": [], "strategy": "vector+web"},
            ],
            "retry_count": retry_count + 1,
        }

    # ─────────────────────────────────────────────────────────
    #  Step 6  ·  Self-Evolving Tool Synthesis (SETS)
    # ─────────────────────────────────────────────────────────

    def tool_smith_node(self, state: NexusState) -> dict:
        """Check if computation is needed and synthesize tools on-the-fly."""
        query = state["query"]
        documents = state["documents"]

        print_agent_action("ToolSmith", "Checking if computation is needed...")
        tool_result = self.tool_smith.execute(query, str(documents[:2])[:500])
        computation_results = tool_result.get("results", [])

        if tool_result.get("status") == "tool_created":
            print_agent_action(
                "ToolSmith", f"Created new tool: {tool_result.get('tool', 'unknown')}"
            )

        return {"tool_result": tool_result, "computation_results": computation_results}

    # ─────────────────────────────────────────────────────────
    #  Step 7  ·  Synthesis Agent
    # ─────────────────────────────────────────────────────────

    def synthesize(self, state: NexusState) -> dict:
        """Generate a comprehensive, cited answer from verified sources."""
        query = state["query"]  # Always use original query for synthesis
        documents = state["documents"]
        computation_results = state.get("computation_results", [])
        memory_context = state.get("memory_context", "")
        max_results = self.config.retrieval.max_results

        print_agent_action("Synthesizer", "Generating comprehensive answer...")
        synthesis = self.synthesizer.execute(
            query=query,
            documents=documents[:max_results],
            computation_results=computation_results,
            memory_context=memory_context,
        )

        return {
            "answer": synthesis.get("answer", "I was unable to generate an answer."),
            "sources": synthesis.get("sources", []),
        }

    # ─────────────────────────────────────────────────────────
    #  Step 8  ·  Epistemic Uncertainty Quantification (EUQ)
    # ─────────────────────────────────────────────────────────

    def score_confidence(self, state: NexusState) -> dict:
        """Multi-dimensional confidence scoring of the final answer."""
        print_agent_action("Confidence", "Scoring answer confidence...")
        confidence = self.confidence_agent.execute(
            query=state["query"],
            answer=state["answer"],
            sources=state["sources"],
            parliament_scores=state.get("verdict", {}).get("scores", {}),
        )
        return {"confidence": confidence}

    # ─────────────────────────────────────────────────────────
    #  Step 9  ·  Display Results (Rich terminal output)
    # ─────────────────────────────────────────────────────────

    def display_results(self, state: NexusState) -> dict:
        """Render the answer, confidence card, and sources to the terminal."""
        print_answer(state.get("answer", ""))
        print_confidence_card(state.get("confidence", {}))
        print_sources(state.get("sources", []))
        return {}  # No state mutation — display only

    # ─────────────────────────────────────────────────────────
    #  Step 10  ·  Update Cognitive Memory Fabric (CMF)
    # ─────────────────────────────────────────────────────────

    def update_memory(self, state: NexusState) -> dict:
        """Persist episode, update MLRO stats, and extract entities into the knowledge graph."""
        query = state["query"]
        query_type = state.get("query_type", "factual")
        complexity = state.get("complexity", "simple")
        recommendation = state.get("strategy_recommendation", {})
        strategy = recommendation.get("strategy", "direct")
        retrieval_methods = recommendation.get("retrieval_methods", "vector")
        verdict = state.get("verdict", {})
        confidence = state.get("confidence", {})
        answer = state.get("answer", "")
        start_time = state.get("start_time", time.time())
        trace_id = state.get("trace_id", "")

        duration_ms = (time.time() - start_time) * 1000

        # ── Episodic Memory — record what happened ──
        episode = Episode(
            query=query,
            query_type=query_type,
            complexity=complexity,
            strategy_used=strategy,
            retrieval_methods=(
                retrieval_methods.split("+")
                if isinstance(retrieval_methods, str)
                else retrieval_methods
            ),
            parliament_verdict=verdict.get("decision", "UNKNOWN"),
            confidence_score=confidence.get("overall", 0.0),
            answer_summary=answer[:200],
            duration_ms=duration_ms,
            trace_id=trace_id,
        )
        self.episodic.record(episode)

        # ── Procedural Memory — learn from outcome (MLRO) ──
        self.procedural.record_outcome(
            query_type=query_type,
            strategy=strategy,
            retrieval_methods=retrieval_methods,
            success=verdict.get("decision") in ("ACCEPT", "SKIP"),
            confidence=confidence.get("overall", 0.0),
            duration_ms=duration_ms,
            tokens_used=self.llm.total_tokens_used,
        )

        # ── Semantic Memory — extract entities into knowledge graph ──
        try:
            extraction = self.llm.chat_json(
                system_prompt=(
                    "Extract key entities and relationships from this text. "
                    'Respond in JSON: {"entities": [{"name": "x", "type": "concept"}], '
                    '"relations": [{"source": "x", "target": "y", "type": "related_to"}]}'
                ),
                user_message=answer[:1000],
            )
            for ent in extraction.get("entities", [])[:10]:
                self.semantic.add_entity(ent["name"], ent.get("type", "concept"))
            for rel in extraction.get("relations", [])[:10]:
                self.semantic.add_relation(
                    rel["source"], rel["target"], rel.get("type", "related_to")
                )
        except Exception as e:
            logger.debug(f"Semantic extraction failed (non-critical): {e}")

        print_memory_update()

        console.print(
            f"\n  ⏱️  [dim]Total time: {duration_ms:.0f}ms | "
            f"Tokens: {self.llm.total_tokens_used}[/dim]\n"
        )

        return {
            "duration_ms": duration_ms,
            "result": {
                "answer": answer,
                "confidence": confidence,
                "sources": state.get("sources", []),
                "verdict": verdict.get("decision"),
                "trace_id": trace_id,
                "duration_ms": duration_ms,
            },
        }
