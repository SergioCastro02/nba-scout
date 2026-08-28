"""Evaluation metrics.

Retrieval metrics are deterministic and LLM-free. Quality metrics (faithfulness,
correctness) use an LLM as judge and are only computed when a judge is supplied.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel

from ..models import RetrievedChunk


# --------------------------------------------------------------------------- #
# Retrieval metrics — no LLM                                                   #
# --------------------------------------------------------------------------- #
def context_recall(retrieved: list[RetrievedChunk], required_sections: list[str]) -> float:
    """Fraction of the required KB sections that appear among the retrieved chunks."""
    if not required_sections:
        return 1.0
    got = {r.chunk.section for r in retrieved if r.chunk.section}
    hits = sum(1 for s in required_sections if s in got)
    return hits / len(required_sections)


def reciprocal_rank(retrieved: list[RetrievedChunk], required_sections: list[str]) -> float:
    """1/rank of the first retrieved chunk that matches a required section (0 if none)."""
    if not required_sections:
        return 1.0
    wanted = set(required_sections)
    for i, r in enumerate(retrieved, start=1):
        if r.chunk.section in wanted:
            return 1.0 / i
    return 0.0


def route_exact_match(actual: list[str], expected: list[str]) -> bool:
    return set(actual or []) == set(expected or [])


# --------------------------------------------------------------------------- #
# Quality metrics — LLM as judge                                               #
# --------------------------------------------------------------------------- #
class _Judgement(BaseModel):
    score: float
    reason: str


_FAITHFULNESS_PROMPT = (
    "You are grading whether an ANSWER is faithful to its CONTEXT — i.e. every factual "
    "claim in the answer is supported by the context. Ignore stylistic differences. "
    "Return a score from 0.0 (claims contradict or aren't in the context) to 1.0 "
    "(fully supported), and a one-sentence reason. Respond as JSON: "
    '{{"score": <float>, "reason": "<text>"}}.\n\n'
    "CONTEXT:\n{context}\n\nANSWER:\n{answer}"
)

_CORRECTNESS_PROMPT = (
    "You are grading whether an ANSWER covers the EXPECTED POINTS. Score = fraction of "
    "expected points that the answer clearly states (0.0 to 1.0). Minor wording and "
    "extra correct detail are fine. Respond as JSON: "
    '{{"score": <float>, "reason": "<text>"}}.\n\n'
    "EXPECTED POINTS:\n{points}\n\nANSWER:\n{answer}"
)


def _judge(llm, prompt: str) -> _Judgement:
    raw = llm.invoke(prompt)
    text = getattr(raw, "content", raw)
    if isinstance(text, list):
        text = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in text)
    match = re.search(r"\{.*\}", str(text), re.DOTALL)
    if not match:
        return _Judgement(score=0.0, reason="judge returned no JSON")
    data = json.loads(match.group(0))
    return _Judgement(score=max(0.0, min(1.0, float(data["score"]))), reason=data.get("reason", ""))


def faithfulness(llm, answer: str, context: str) -> _Judgement:
    return _judge(llm, _FAITHFULNESS_PROMPT.format(context=context, answer=answer))


def answer_correctness(llm, answer: str, expected_points: list[str]) -> _Judgement:
    points = "\n".join(f"- {p}" for p in expected_points)
    return _judge(llm, _CORRECTNESS_PROMPT.format(points=points, answer=answer))
