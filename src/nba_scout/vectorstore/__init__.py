"""Vector store abstraction.

Two implementations behind one Protocol:
- `memory`   — numpy cosine similarity, zero infra, used for tests and quickstart
- `pgvector` — Postgres + pgvector, the deployed path (see docker-compose.yml)

Pick with NBA_SCOUT_VECTOR_STORE.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from ..config import get_settings
from ..models import Chunk, RetrievedChunk


class VectorStore(Protocol):
    def ensure_schema(self) -> None: ...
    def clear(self) -> None: ...
    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...
    def search(self, query_vector: list[float], top_k: int) -> list[RetrievedChunk]: ...
    def count(self) -> int: ...


@lru_cache
def get_vector_store() -> VectorStore:
    s = get_settings()
    if s.vector_store == "pgvector":
        from .pgvector import PgVectorStore

        return PgVectorStore(s.database_url, s.embedding_dim)

    from .memory import InMemoryVectorStore

    return InMemoryVectorStore()


__all__ = ["VectorStore", "get_vector_store", "Chunk", "RetrievedChunk"]
