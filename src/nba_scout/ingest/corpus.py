"""Load source documents into (source, section, text) records.

Two loaders:
- markdown files under `nba_scout/corpus/` — split on `##` headings; ships with
  the package so the RAG path works with no downloads
- PDFs under `data/` (populated by scripts/download_corpus.py) — one record per
  page, section left blank
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

_HEADING = re.compile(r"^##\s+(.*)$", re.MULTILINE)

# Human-readable source name per bundled file.
_BUNDLED = {
    "nba_rules_summary.md": "NBA Rules (summary)",
    "cba_summary.md": "NBA CBA (summary)",
}


@dataclass(frozen=True)
class Document:
    source: str
    section: str | None
    text: str


def load_bundled() -> list[Document]:
    docs: list[Document] = []
    corpus_dir = files("nba_scout.corpus")
    for filename, source in _BUNDLED.items():
        raw = (corpus_dir / filename).read_text(encoding="utf-8")
        docs.extend(_split_markdown(raw, source))
    return docs


def load_pdfs(data_dir: Path) -> list[Document]:
    from pypdf import PdfReader

    docs: list[Document] = []
    for pdf_path in sorted(data_dir.glob("*.pdf")):
        source = pdf_path.stem.replace("_", " ")
        reader = PdfReader(str(pdf_path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                docs.append(Document(source=source, section=f"p.{page_num}", text=text))
    return docs


def _split_markdown(raw: str, source: str) -> list[Document]:
    # Drop the leading title and any blockquote preamble before the first `##`.
    parts = _HEADING.split(raw)
    docs: list[Document] = []
    # parts = [preamble, heading1, body1, heading2, body2, ...]
    for i in range(1, len(parts), 2):
        section = parts[i].strip()
        body = parts[i + 1].strip()
        if body:
            docs.append(Document(source=source, section=section, text=body))
    return docs
