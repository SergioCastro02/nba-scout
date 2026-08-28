"""Shared data types."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A retrievable passage from the knowledge base."""

    id: str = Field(description="stable id: '<source>#<ordinal>'")
    source: str = Field(description="document name, e.g. 'NBA Rulebook'")
    section: str | None = Field(default=None, description="section / rule heading")
    text: str

    def citation(self) -> str:
        return f"{self.source}" + (f" / {self.section}" if self.section else "")


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float = Field(description="cosine similarity, higher is closer")
