"""Assemble the assistant graph.

    START → router ─┬─▶ rules ─┐
                    └─▶ stats ─┴─▶ synthesis → END

The router picks one or both specialists; when both run they run in the same
superstep and synthesis joins them.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .router import route, route_selector
from .rules import run_rules_agent
from .state import AssistantState
from .stats import run_stats_agent
from .synthesis import run_synthesis


def build_graph() -> StateGraph:
    g = StateGraph(AssistantState)
    g.add_node("router", route)
    g.add_node("rules", run_rules_agent)
    g.add_node("stats", run_stats_agent)
    g.add_node("synthesis", run_synthesis)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", route_selector, ["rules", "stats"])
    g.add_edge("rules", "synthesis")
    g.add_edge("stats", "synthesis")
    g.add_edge("synthesis", END)
    return g


@lru_cache
def get_compiled_graph():
    return build_graph().compile()


def answer_question(question: str) -> AssistantState:
    """Run the whole graph for one question and return the final state."""
    return get_compiled_graph().invoke({"question": question})  # type: ignore[return-value]
