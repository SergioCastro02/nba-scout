"""In-memory vector store: numpy cosine similarity over a normalized matrix.

Not for production — linear scan, single process — but it makes the whole RAG path
runnable and testable without Postgres. It persists to a small file on disk
(`platformdirs` cache dir, override with NBA_SCOUT_MEMORY_STORE_PATH) so that
`nba-scout ingest` and a later `nba-scout ask` share a knowledge base. Pass
`path=None` for a pure in-memory instance (tests).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from platformdirs import user_cache_dir

from ..models import Chunk, RetrievedChunk

_SENTINEL = object()


def _default_path() -> Path:
    override = os.environ.get("NBA_SCOUT_MEMORY_STORE_PATH")
    if override:
        return Path(override)
    return Path(user_cache_dir("nba-scout")) / "kb.npz"


class InMemoryVectorStore:
    def __init__(self, path: Path | None | object = _SENTINEL) -> None:
        self._path: Path | None = _default_path() if path is _SENTINEL else path  # type: ignore[assignment]
        self._chunks: list[Chunk] = []
        self._matrix: np.ndarray | None = None  # (n, dim), L2-normalized
        self._load()

    def ensure_schema(self) -> None:
        return

    def clear(self) -> None:
        self._chunks = []
        self._matrix = None
        self._save()

    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        new = _normalize(np.asarray(vectors, dtype=np.float32))
        self._matrix = new if self._matrix is None else np.vstack([self._matrix, new])
        self._chunks.extend(chunks)
        self._save()

    def search(self, query_vector: list[float], top_k: int) -> list[RetrievedChunk]:
        if self._matrix is None or not self._chunks:
            return []
        q = _normalize(np.asarray([query_vector], dtype=np.float32))[0]
        scores = self._matrix @ q
        top = np.argsort(-scores)[:top_k]
        return [RetrievedChunk(chunk=self._chunks[i], score=float(scores[i])) for i in top]

    def count(self) -> int:
        return len(self._chunks)

    # --- persistence ---------------------------------------------------- #
    def _load(self) -> None:
        if not self._path or not self._path.exists():
            return
        with np.load(self._path, allow_pickle=False) as data:
            self._matrix = data["matrix"] if data["matrix"].size else None
            meta = json.loads(str(data["meta"]))
        self._chunks = [Chunk(**c) for c in meta]

    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        matrix = self._matrix if self._matrix is not None else np.empty((0, 0), dtype=np.float32)
        meta = json.dumps([c.model_dump() for c in self._chunks])
        np.savez(self._path, matrix=matrix, meta=np.array(meta))


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-12, None)
