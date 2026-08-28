"""Run the golden set through the pipeline and score it."""

from __future__ import annotations

import re
import statistics
import time
from dataclasses import dataclass, field

from ..retrieval import format_context, retrieve
from .dataset import DATASET, EvalCase
from .metrics import (
    answer_correctness,
    context_recall,
    faithfulness,
    reciprocal_rank,
    route_exact_match,
)

_TRANSIENT = ("429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
_RETRY_DELAY_RE = re.compile(r"(?:retryDelay['\":\s]+|retry in )(\d+(?:\.\d+)?)s")


def _suggested_delay(error: Exception, fallback: float) -> float:
    """Honour the provider's own 'retry after N seconds' hint, capped at 60s."""
    match = _RETRY_DELAY_RE.search(str(error))
    return min(float(match.group(1)) + 1 if match else fallback, 60.0)


def _retry(fn, attempts: int = 4, base_delay: float = 3.0):
    """Retry on transient provider errors, waiting the delay the provider asks for."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if not any(c in str(e) for c in _TRANSIENT) or i == attempts - 1:
                raise
            time.sleep(_suggested_delay(e, base_delay * (i + 1)))


@dataclass
class CaseResult:
    case_id: str
    context_recall: float
    reciprocal_rank: float
    route_match: bool | None = None
    faithfulness: float | None = None
    correctness: float | None = None
    answer: str = ""
    notes: str = ""


@dataclass
class EvalReport:
    results: list[CaseResult] = field(default_factory=list)
    judged: bool = False

    def _avg(self, attr: str) -> float | None:
        vals = [getattr(r, attr) for r in self.results if getattr(r, attr) is not None]
        return round(statistics.fmean(vals), 3) if vals else None

    @property
    def aggregates(self) -> dict[str, float | None]:
        return {
            "context_recall": self._avg("context_recall"),
            "reciprocal_rank": self._avg("reciprocal_rank"),
            "route_accuracy": (
                round(
                    statistics.fmean(
                        [
                            1.0 if r.route_match else 0.0
                            for r in self.results
                            if r.route_match is not None
                        ]
                    ),
                    3,
                )
                if any(r.route_match is not None for r in self.results)
                else None
            ),
            "faithfulness": self._avg("faithfulness"),
            "correctness": self._avg("correctness"),
        }


def _retrieval_only(case: EvalCase) -> CaseResult:
    retrieved = retrieve(case.question)
    return CaseResult(
        case_id=case.id,
        context_recall=round(context_recall(retrieved, case.must_retrieve_sections), 3),
        reciprocal_rank=round(reciprocal_rank(retrieved, case.must_retrieve_sections), 3),
    )


def _full(case: EvalCase, judge_llm) -> CaseResult:
    from ..agents.graph import get_compiled_graph

    state = _retry(lambda: get_compiled_graph().invoke({"question": case.question}))
    retrieved = state.get("retrieved", []) or []
    answer = state.get("answer", "")

    result = CaseResult(
        case_id=case.id,
        context_recall=round(context_recall(retrieved, case.must_retrieve_sections), 3),
        reciprocal_rank=round(reciprocal_rank(retrieved, case.must_retrieve_sections), 3),
        route_match=route_exact_match(state.get("route", []), case.expected_route),
        answer=answer,
    )

    if judge_llm is not None and answer:
        # Faithfulness-vs-KB only makes sense for a pure knowledge-base answer;
        # a stats answer is grounded in tool output, not the retrieved context.
        if retrieved and state.get("route") == ["rules"]:
            result.faithfulness = round(
                _retry(
                    lambda: faithfulness(judge_llm, answer, format_context(retrieved)).score
                ),
                3,
            )
        result.correctness = round(
            _retry(lambda: answer_correctness(judge_llm, answer, case.expected_points).score), 3
        )
    return result


def run_eval(
    cases: list[EvalCase] | None = None,
    *,
    retrieval_only: bool = False,
    judge_llm=None,
    pace_seconds: float = 0.0,
) -> EvalReport:
    cases = cases or DATASET
    report = EvalReport(judged=judge_llm is not None and not retrieval_only)
    for n, case in enumerate(cases):
        if n and pace_seconds:
            time.sleep(pace_seconds)  # stay under per-minute provider quotas
        try:
            if retrieval_only:
                report.results.append(_retrieval_only(case))
            else:
                report.results.append(_full(case, judge_llm))
        except Exception as e:  # noqa: BLE001 - one bad case must not sink the run
            report.results.append(
                CaseResult(
                    case_id=case.id,
                    context_recall=0.0,
                    reciprocal_rank=0.0,
                    notes=f"{type(e).__name__}: {e}",
                )
            )
    return report


def render_markdown(report: EvalReport) -> str:
    agg = report.aggregates
    mode = "graph + LLM judge" if report.judged else "retrieval only"
    lines = [
        "# nba-scout evaluation",
        "",
        f"_{mode}. Judge scores are LLM-graded and vary between runs; treat them as a trend._",
        "",
        "| metric | score |",
    ]
    lines.append("| --- | --- |")
    for name, value in agg.items():
        lines.append(f"| {name} | {'—' if value is None else f'{value:.3f}'} |")
    lines += [
        "",
        "| case | ctx recall | RR | route | faithful | correct |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in report.results:
        lines.append(
            f"| {r.case_id} | {r.context_recall:.2f} | {r.reciprocal_rank:.2f} | "
            f"{'—' if r.route_match is None else ('✓' if r.route_match else '✗')} | "
            f"{'—' if r.faithfulness is None else f'{r.faithfulness:.2f}'} | "
            f"{'—' if r.correctness is None else f'{r.correctness:.2f}'} |"
        )

    failures = [r for r in report.results if r.notes]
    if failures:
        lines += ["", "## errors", ""]
        lines += [f"- **{r.case_id}**: {r.notes}" for r in failures]

    return "\n".join(lines) + "\n"
