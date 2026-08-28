"""Application configuration.

Everything env-driven so the same image runs locally (in-memory store, local
embeddings) and in AWS (pgvector on RDS, Bedrock models) with no code change.
Prefix every var with NBA_SCOUT_, e.g. NBA_SCOUT_LLM_PROVIDER=bedrock.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["anthropic", "bedrock", "google"]
EmbeddingProvider = Literal["fastembed", "bedrock"]
VectorStoreKind = Literal["memory", "pgvector"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NBA_SCOUT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---------------------------------------------------------------- #
    llm_provider: LLMProvider = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    bedrock_model: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    aws_region: str = "us-east-1"
    # google — free tier at https://aistudio.google.com/apikey (no card)
    google_api_key: str | None = None
    google_model: str = "gemini-flash-latest"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024

    # --- Embeddings ------------------------------------------------------- #
    embedding_provider: EmbeddingProvider = "fastembed"
    fastembed_model: str = "BAAI/bge-small-en-v1.5"  # 384 dims, ONNX, no torch
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"  # 1024 dims
    embedding_dim: int = 384  # MUST match the active embedding model

    # --- Vector store --------------------------------------------------- #
    vector_store: VectorStoreKind = "memory"
    database_url: str = "postgresql://nba:nba@localhost:5432/nba_scout"

    # --- Retrieval ------------------------------------------------------ #
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_top_k: int = 5

    # --- Stats tools -------------------------------------------------- #
    # If set, the stats agent calls a running nba-mcp-server over HTTP.
    # If unset, it imports nba_api directly (dev convenience).
    mcp_server_url: str | None = None

    # --- Observability --------------------------------------------- #
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")


@lru_cache
def get_settings() -> Settings:
    return Settings()
