"""nba-scout — a multi-agent NBA assistant.

A LangGraph-orchestrated assistant that answers NBA questions by combining:
- a RAG knowledge base over the NBA rulebook and Collective Bargaining Agreement
- live statistics tools (player/team stats, standings, box scores)

The LLM provider (AWS Bedrock or Anthropic) and the vector store (pgvector or an
in-memory store) are chosen by configuration, not hard-coded.
"""

__version__ = "0.1.0"
