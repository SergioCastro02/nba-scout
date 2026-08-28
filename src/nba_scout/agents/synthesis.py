"""Synthesis node: merge the specialists' findings into one grounded answer."""

from __future__ import annotations

from ..llm import get_chat_model
from ._util import message_text
from .state import AssistantState

_SYSTEM = (
    "You write the final answer to an NBA question from the specialist findings below. "
    "Use only what the findings contain. Preserve rulebook/CBA citations like [1]. "
    "If the findings conflict or fall short, say so. Be concise."
)


def run_synthesis(state: AssistantState) -> AssistantState:
    parts = []
    if state.get("rules_findings"):
        parts.append(f"Rules/CBA findings:\n{state['rules_findings']}")
    if state.get("stats_findings"):
        parts.append(f"Stats findings:\n{state['stats_findings']}")
    findings = "\n\n".join(parts) or "(no findings were produced)"

    llm = get_chat_model()
    response = llm.invoke(
        [
            ("system", _SYSTEM),
            ("human", f"Question: {state['question']}\n\n{findings}"),
        ]
    )
    return {"answer": message_text(response)}
