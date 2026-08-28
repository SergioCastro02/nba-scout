"""Evaluation harness tests. Metric functions are pure; the judge and graph are faked."""

from __future__ import annotations

from nba_scout.eval import DATASET, render_markdown, run_eval
from nba_scout.eval.metrics import (
    answer_correctness,
    context_recall,
    faithfulness,
    reciprocal_rank,
    route_exact_match,
)
from nba_scout.models import Chunk, RetrievedChunk


def _r(section: str, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(id=section, source="s", section=section, text="t"), score=score
    )


# --- retrieval metrics ---------------------------------------------------- #
def test_context_recall_full_and_partial():
    retrieved = [_r("A"), _r("B"), _r("C")]
    assert context_recall(retrieved, ["A", "B"]) == 1.0
    assert context_recall(retrieved, ["A", "Z"]) == 0.5
    assert context_recall(retrieved, []) == 1.0  # nothing required


def test_reciprocal_rank_uses_first_hit_position():
    retrieved = [_r("X"), _r("Y"), _r("target")]
    assert reciprocal_rank(retrieved, ["target"]) == 1 / 3
    assert reciprocal_rank(retrieved, ["missing"]) == 0.0


def test_route_exact_match_is_order_insensitive():
    assert route_exact_match(["stats", "rules"], ["rules", "stats"])
    assert not route_exact_match(["rules"], ["rules", "stats"])


# --- LLM-judged metrics (fake judge) ----------------------------------- #
class _FakeJudge:
    def __init__(self, payload: str):
        self.payload = payload

    def invoke(self, _prompt):
        from langchain_core.messages import AIMessage

        return AIMessage(content=self.payload)


def test_faithfulness_parses_judge_json():
    judge = _FakeJudge('Here is my grade: {"score": 0.9, "reason": "supported"}')
    result = faithfulness(judge, "answer", "context")
    assert result.score == 0.9
    assert "supported" in result.reason


def test_correctness_clamps_out_of_range_scores():
    assert answer_correctness(_FakeJudge('{"score": 1.7, "reason": "x"}'), "a", ["p"]).score == 1.0
    assert answer_correctness(_FakeJudge('{"score": -1, "reason": "x"}'), "a", ["p"]).score == 0.0


def test_judge_handles_missing_json():
    assert faithfulness(_FakeJudge("no json here"), "a", "c").score == 0.0


# --- runner ------------------------------------------------------------- #
def test_dataset_is_well_formed():
    ids = [c.id for c in DATASET]
    assert len(ids) == len(set(ids)) >= 10
    for c in DATASET:
        assert c.expected_points
        assert set(c.expected_route) <= {"rules", "stats"}


def test_run_eval_retrieval_only(fake_embedder, memory_store):
    from nba_scout.ingest import ingest

    ingest(reset=True)
    report = run_eval(DATASET[:3], retrieval_only=True)

    assert len(report.results) == 3
    assert not report.judged
    assert all(r.route_match is None for r in report.results)
    agg = report.aggregates
    assert agg["context_recall"] is not None
    assert agg["route_accuracy"] is None


def test_render_markdown_has_tables(fake_embedder, memory_store):
    from nba_scout.ingest import ingest

    ingest(reset=True)
    md = render_markdown(run_eval(DATASET[:2], retrieval_only=True))
    assert "# nba-scout evaluation" in md
    assert "| context_recall |" in md
    assert "| case |" in md
