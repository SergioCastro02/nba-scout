"""Request/response models for the HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000, examples=["What is the second apron?"])


class Source(BaseModel):
    citation: str
    score: float


class AskResponse(BaseModel):
    question: str
    route: list[str] = Field(description="which specialist agents ran")
    answer: str
    sources: list[Source] = Field(default_factory=list, description="knowledge-base passages used")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    llm_provider: str
    embedding_provider: str
    vector_store: str
    knowledge_base_chunks: int
