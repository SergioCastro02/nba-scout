"""Shared fixtures. Keeps tests offline: no model downloads, no network, no DB."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from nba_scout import embeddings as embeddings_mod
from nba_scout import retrieval as retrieval_mod
from nba_scout.ingest import pipeline as pipeline_mod
from nba_scout.vectorstore import memory as memory_mod


class FakeEmbedder:
    """Deterministic hash-based embeddings — stable, fast, offline."""

    dim = 32

    def _vec(self, text: str) -> list[float]:
        rng = np.random.default_rng(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8]))
        return rng.standard_normal(self.dim).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


@pytest.fixture
def fake_embedder(monkeypatch: pytest.MonkeyPatch) -> FakeEmbedder:
    embedder = FakeEmbedder()
    for mod in (embeddings_mod, pipeline_mod, retrieval_mod):
        monkeypatch.setattr(mod, "get_embedder", lambda: embedder, raising=False)
    return embedder


class FakeChat:
    """Minimal stand-in for a LangChain chat model.

    `route_agents` drives `.with_structured_output(...)`; `reply` drives `.invoke`.
    """

    def __init__(self, reply: str = "canned answer", route_agents: tuple[str, ...] = ("rules",)):
        self.reply = reply
        self.route_agents = route_agents
        self.calls: list[list] = []

    def invoke(self, messages):
        from langchain_core.messages import AIMessage

        self.calls.append(messages)
        return AIMessage(content=self.reply)

    def with_structured_output(self, schema):
        agents = list(self.route_agents)

        class _Structured:
            def invoke(_self, _messages):
                return schema(agents=agents, reasoning="test")

        return _Structured()

    def bind_tools(self, _tools):
        return self


@pytest.fixture
def fake_chat(monkeypatch: pytest.MonkeyPatch) -> FakeChat:
    chat = FakeChat()
    from nba_scout import llm as llm_mod
    from nba_scout.agents import router, rules, stats, synthesis

    for mod in (llm_mod, router, rules, stats, synthesis):
        monkeypatch.setattr(mod, "get_chat_model", lambda: chat, raising=False)

    # The stats ReAct agent is heavy; replace it with a canned runnable.
    class _FakeReactAgent:
        def invoke(self, _inputs):
            from langchain_core.messages import AIMessage

            return {"messages": [AIMessage(content="stats: 27.1 ppg")]}

    monkeypatch.setattr(stats, "create_react_agent", lambda *_a, **_k: _FakeReactAgent())
    return chat


@pytest.fixture
def memory_store(monkeypatch: pytest.MonkeyPatch):
    """A fresh, non-persistent in-memory store wired into pipeline + retrieval."""
    store = memory_mod.InMemoryVectorStore(path=None)
    for mod in (pipeline_mod, retrieval_mod):
        monkeypatch.setattr(mod, "get_vector_store", lambda: store, raising=False)
    return store
