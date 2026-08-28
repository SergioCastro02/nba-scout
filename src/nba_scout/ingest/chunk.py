"""Text chunking.

Paragraph-greedy: pack whole paragraphs into a chunk until it would exceed
`chunk_size`, then start a new chunk carrying `chunk_overlap` characters of tail
context. Keeps rule/section boundaries intact where possible.
"""

from __future__ import annotations

import re

_PARAGRAPH = re.compile(r"\n\s*\n")


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in _PARAGRAPH.split(text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= chunk_size or not current:
            current = candidate
        else:
            chunks.append(current)
            tail = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{tail}\n\n{para}".strip()

    if current:
        chunks.append(current)

    # A single giant paragraph still needs to be broken up.
    return [piece for c in chunks for piece in _hard_wrap(c, chunk_size, chunk_overlap)]


def _hard_wrap(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    step = max(chunk_size - chunk_overlap, 1)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]
