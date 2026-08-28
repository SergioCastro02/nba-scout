"""Query-time retrieval over the knowledge base."""

from __future__ import annotations

from .config import get_settings
from .embeddings import get_embedder
from .models import RetrievedChunk
from .vectorstore import get_vector_store


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    s = get_settings()
    embedder = get_embedder()
    store = get_vector_store()
    query_vector = embedder.embed_query(query)
    return store.search(query_vector, top_k or s.retrieval_top_k)


def format_context(results: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as a numbered, citable context block for the LLM."""
    if not results:
        return "(no relevant passages found in the knowledge base)"
    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(f"[{i}] {r.chunk.citation()}\n{r.chunk.text}")
    return "\n\n".join(blocks)
