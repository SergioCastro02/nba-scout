"""Ingestion: documents -> chunks -> embeddings -> vector store."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..config import get_settings
from ..embeddings import get_embedder
from ..models import Chunk
from ..vectorstore import get_vector_store
from .chunk import split_text
from .corpus import Document, load_bundled, load_pdfs

log = logging.getLogger(__name__)


@dataclass
class IngestReport:
    documents: int
    chunks: int
    stored: int


def build_chunks(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    per_source_ordinal: dict[str, int] = {}
    for doc in docs:
        for piece in split_text(doc.text, chunk_size, chunk_overlap):
            n = per_source_ordinal.get(doc.source, 0)
            per_source_ordinal[doc.source] = n + 1
            chunks.append(
                Chunk(
                    id=f"{doc.source}#{n}",
                    source=doc.source,
                    section=doc.section,
                    text=piece,
                )
            )
    return chunks


def ingest(
    data_dir: Path | None = None, *, reset: bool = True, batch_size: int = 64
) -> IngestReport:
    s = get_settings()
    store = get_vector_store()
    embedder = get_embedder()

    docs = load_bundled()
    if data_dir and data_dir.exists():
        pdf_docs = load_pdfs(data_dir)
        log.info("loaded %d pages from PDFs in %s", len(pdf_docs), data_dir)
        docs += pdf_docs

    chunks = build_chunks(docs, s.chunk_size, s.chunk_overlap)
    log.info("split %d documents into %d chunks", len(docs), len(chunks))

    store.ensure_schema()
    if reset:
        store.clear()

    stored = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embedder.embed_documents([c.text for c in batch])
        store.add(batch, vectors)
        stored += len(batch)
        log.info("embedded + stored %d/%d", stored, len(chunks))

    return IngestReport(documents=len(docs), chunks=len(chunks), stored=store.count())
