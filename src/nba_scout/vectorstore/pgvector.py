"""Postgres + pgvector store — the deployed path.

Schema is a single table with an HNSW index on cosine distance. psycopg3 with the
pgvector adapter; connections are opened per operation (fine for ingest + a
low-QPS API; swap for a pool if traffic grows).
"""

from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

from ..models import Chunk, RetrievedChunk

_TABLE = "kb_chunks"


class PgVectorStore:
    def __init__(self, database_url: str, dim: int) -> None:
        self._url = database_url
        self._dim = dim

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._url, autocommit=True)
        register_vector(conn)
        return conn

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                    id        TEXT PRIMARY KEY,
                    source    TEXT NOT NULL,
                    section   TEXT,
                    text      TEXT NOT NULL,
                    embedding vector({self._dim}) NOT NULL
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS {_TABLE}_embedding_idx "
                f"ON {_TABLE} USING hnsw (embedding vector_cosine_ops)"
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute(f"TRUNCATE {_TABLE}")

    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        rows = [
            (c.id, c.source, c.section, c.text, vec)
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        with self._connect() as conn, conn.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {_TABLE} (id, source, section, text, embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                    SET text = EXCLUDED.text, embedding = EXCLUDED.embedding
                """,
                rows,
            )

    def search(self, query_vector: list[float], top_k: int) -> list[RetrievedChunk]:
        with self._connect() as conn:
            result = conn.execute(
                f"""
                SELECT id, source, section, text, 1 - (embedding <=> %s::vector) AS score
                FROM {_TABLE}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_vector, query_vector, top_k),
            ).fetchall()
        return [
            RetrievedChunk(
                chunk=Chunk(id=r[0], source=r[1], section=r[2], text=r[3]), score=float(r[4])
            )
            for r in result
        ]

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {_TABLE}").fetchone()[0]
