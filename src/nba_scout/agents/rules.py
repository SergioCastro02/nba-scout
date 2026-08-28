"""Rules agent: RAG over the rulebook / CBA knowledge base."""

from __future__ import annotations

from ..llm import get_chat_model
from ..retrieval import format_context, retrieve
from ._util import message_text
from .state import AssistantState

_SYSTEM = (
    "You answer NBA rulebook and CBA questions strictly from the numbered context "
    "passages provided. Cite the passages you use as [1], [2], etc. If the context "
    "does not contain the answer, say so plainly — do not use outside knowledge."
)


def run_rules_agent(state: AssistantState) -> AssistantState:
    question = state["question"]
    results = retrieve(question)
    context = format_context(results)

    llm = get_chat_model()
    response = llm.invoke(
        [
            ("system", _SYSTEM),
            ("human", f"Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    return {"retrieved": results, "rules_findings": message_text(response)}
