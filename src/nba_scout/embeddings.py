"""Embedding providers behind one small interface.

`fastembed` runs a quantized ONNX model locally (no API key, no torch) and is the
default so the project works out of the box. `bedrock` uses Amazon Titan v2 for
the AWS deployment. Swap with NBA_SCOUT_EMBEDDING_PROVIDER; remember to also set
NBA_SCOUT_EMBEDDING_DIM to match (384 for bge-small, 1024 for Titan v2).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from .config import get_settings


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    """Local ONNX embeddings via fastembed."""

    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed(text))).tolist()


class BedrockEmbedder:
    """Amazon Titan embeddings via langchain-aws."""

    def __init__(self, model_id: str, region: str) -> None:
        from langchain_aws import BedrockEmbeddings

        self._model = BedrockEmbeddings(model_id=model_id, region_name=region)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)


@lru_cache
def get_embedder() -> Embedder:
    s = get_settings()
    if s.embedding_provider == "bedrock":
        return BedrockEmbedder(s.bedrock_embedding_model, s.aws_region)
    return FastEmbedEmbedder(s.fastembed_model)
