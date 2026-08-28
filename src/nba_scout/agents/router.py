"""Router node: decide which specialist agents should handle the question.

- rules  → NBA rulebook / CBA questions (answered from the knowledge base)
- stats  → player/team numbers, standings, leaders (answered from live tools)
A question can need both ("is a flagrant 2 an ejection, and who has the most?").
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..llm import get_chat_model
from .state import AssistantState

_VALID = {"rules", "stats"}


class _Route(BaseModel):
    agents: list[str] = Field(
        description="subset of ['rules', 'stats'] — which specialists to invoke"
    )
    reasoning: str = Field(description="one sentence explaining the choice")


_SYSTEM = (
    "You route NBA questions to specialist agents.\n"
    "- 'rules': questions about the rulebook or the Collective Bargaining Agreement "
    "(fouls, violations, salary cap, aprons, contracts, free agency, tax).\n"
    "- 'stats': questions needing player or team numbers, standings, leaders, scores.\n"
    "Return every agent that is needed; many questions need both."
)


def route(state: AssistantState) -> AssistantState:
    llm = get_chat_model().with_structured_output(_Route)
    result: _Route = llm.invoke(
        [("system", _SYSTEM), ("human", state["question"])]
    )  # type: ignore[assignment]
    agents = [a for a in result.agents if a in _VALID] or ["rules"]
    return {"route": agents}


def route_selector(state: AssistantState) -> list[str]:
    """Conditional-edge function: the parallel branches to run next."""
    return state.get("route") or ["rules"]
