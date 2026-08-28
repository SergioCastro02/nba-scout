"""Ingest the bundled corpus with a fake embedder + non-persistent store, then
check retrieval and context formatting."""

from nba_scout.ingest import ingest
from nba_scout.retrieval import format_context, retrieve


def test_ingest_builds_knowledge_base(fake_embedder, memory_store):
    report = ingest(reset=True)

    assert report.documents >= 20
    assert report.chunks >= report.documents
    assert report.stored == memory_store.count() == report.chunks


def test_retrieve_returns_top_k(fake_embedder, memory_store):
    ingest(reset=True)
    results = retrieve("anything", top_k=3)
    assert len(results) == 3
    assert results == sorted(results, key=lambda r: r.score, reverse=True)


def test_format_context_numbers_and_cites(fake_embedder, memory_store):
    ingest(reset=True)
    rendered = format_context(retrieve("foul out", top_k=2))
    assert rendered.startswith("[1] ")
    assert "[2] " in rendered
    assert "summary)" in rendered  # citation includes the source name


def test_format_context_handles_no_results():
    assert "no relevant passages" in format_context([])
