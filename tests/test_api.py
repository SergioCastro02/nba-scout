"""API tests. The graph is replaced with a fake so no LLM is called."""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from nba_scout.api import app as app_module
from nba_scout.models import Chunk, RetrievedChunk


class _FakeGraph:
    def __init__(self, state: dict):
        self._state = state

    async def ainvoke(self, _inputs):
        return self._state

    async def astream(self, _inputs, stream_mode="updates"):
        yield {"router": {"route": self._state["route"]}}
        if "rules_findings" in self._state:
            yield {"rules": {"rules_findings": self._state["rules_findings"],
                             "retrieved": self._state.get("retrieved", [])}}
        yield {"synthesis": {"answer": self._state["answer"]}}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    state = {
        "route": ["rules"],
        "answer": "A flagrant 2 is an automatic ejection [1].",
        "rules_findings": "...",
        "retrieved": [
            RetrievedChunk(
                chunk=Chunk(id="r#1", source="NBA Rules (summary)", section="Flagrant fouls",
                            text="..."),
                score=0.88,
            )
        ],
    }
    monkeypatch.setattr(app_module, "get_compiled_graph", lambda: _FakeGraph(state), raising=False)
    # patched symbol lives in agents.graph; the route imports it locally
    from nba_scout.agents import graph as graph_module

    monkeypatch.setattr(graph_module, "get_compiled_graph", lambda: _FakeGraph(state))
    return TestClient(app_module.create_app())


def test_healthz(client: TestClient):
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["llm_provider"] in {"anthropic", "bedrock", "google"}


def test_readyz_reports_empty_knowledge_base(client: TestClient, monkeypatch):
    class _Empty:
        def count(self):
            return 0

    monkeypatch.setattr("nba_scout.vectorstore.get_vector_store", lambda: _Empty())
    r = client.get("/readyz")
    assert r.status_code == 503
    assert r.json()["ready"] is False


def test_ask_returns_answer_and_sources(client: TestClient):
    r = client.post("/ask", json={"question": "is a flagrant 2 an ejection?"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"] == ["rules"]
    assert "[1]" in body["answer"]
    assert body["sources"][0]["citation"].startswith("NBA Rules")
    assert r.headers["x-request-id"]


def test_ask_validates_question_length(client: TestClient):
    assert client.post("/ask", json={"question": "x"}).status_code == 422


def test_ask_stream_emits_steps_then_answer(client: TestClient):
    with client.stream("POST", "/ask/stream", json={"question": "flagrant 2?"}) as s:
        lines = [ln for ln in s.iter_lines() if ln]

    # pair each "event:" line with the "data:" line that follows it
    pairs = [
        (lines[i].split(": ", 1)[1], json.loads(lines[i + 1].split("data: ", 1)[1]))
        for i in range(0, len(lines) - 1, 2)
    ]
    kinds = [k for k, _ in pairs]
    assert kinds[0] == "step"
    assert kinds[-1] == "answer"

    _, final = pairs[-1]
    assert final["answer"].endswith("[1].")
    assert final["route"] == ["rules"]


def test_ask_maps_auth_error_to_503(monkeypatch: pytest.MonkeyPatch):
    class _Boom:
        async def ainvoke(self, _):
            raise RuntimeError("400 API key not valid")

    from nba_scout.agents import graph as graph_module

    monkeypatch.setattr(graph_module, "get_compiled_graph", lambda: _Boom())
    r = TestClient(app_module.create_app()).post("/ask", json={"question": "hello there"})
    assert r.status_code == 503
