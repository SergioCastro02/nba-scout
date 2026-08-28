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


@pytest.fixture
def memory_store(monkeypatch: pytest.MonkeyPatch):
    """A fresh, non-persistent in-memory store wired into pipeline + retrieval."""
    store = memory_mod.InMemoryVectorStore(path=None)
    for mod in (pipeline_mod, retrieval_mod):
        monkeypatch.setattr(mod, "get_vector_store", lambda: store, raising=False)
    return store
