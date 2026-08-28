# nba-scout

A multi-agent NBA assistant. It answers questions by combining a **RAG knowledge
base** over the NBA rulebook and Collective Bargaining Agreement with **live
statistics tools**, orchestrated as a **LangGraph** agent graph.

```
"Is a flagrant 2 an automatic ejection, and who's had the most this season?"
        │
        ▼  router
   ┌────────────┬─────────────┐
   │ rules agent│ stats agent │      rules agent  → RAG over rulebook/CBA (pgvector)
   └────────────┴─────────────┘      stats agent  → nba-mcp-server tools / nba_api
        │            │
        ▼            ▼
        └──► synthesis agent ──► grounded answer with citations
```

> **Status:** knowledge-base ingestion + retrieval working. Agent graph and API
> are the next milestones — see [Roadmap](#roadmap).

## Design

| Concern | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | explicit state machine, inspectable, matches the JD |
| LLM | AWS Bedrock **or** Anthropic, config-selected | one interface (`llm.get_chat_model`), deploy on Bedrock, dev on Anthropic |
| Embeddings | fastembed (local ONNX) **or** Bedrock Titan | works offline out of the box; Titan for AWS |
| Vector store | pgvector **or** in-memory, config-selected | `VectorStore` Protocol — prod path is Postgres, tests/quickstart use numpy |
| Stats | `nba-mcp-server` over HTTP, or `nba_api` direct | reuses the companion MCP project |

Provider and store are chosen by env vars (`NBA_SCOUT_*`), never by code changes —
the same container image runs locally and in AWS.

## Quickstart (no Docker, no API keys)

```bash
python -m venv .venv && . .venv/Scripts/activate
pip install -e ".[dev]"

nba-scout ingest -v                       # builds the in-memory KB from bundled summaries
nba-scout ask "how many fouls before a player fouls out?"
```

`ask` currently returns the retrieved passages; the LLM answer step lands with the
agent graph.

## With Postgres + pgvector

```bash
docker compose up -d
export NBA_SCOUT_VECTOR_STORE=pgvector
nba-scout ingest -v
```

## Real documents

The bundled corpus is short original summaries so the project runs immediately.
To index the actual rulebook and CBA:

```bash
python scripts/download_corpus.py        # downloads PDFs into data/
nba-scout ingest --data-dir data -v
```

## Configuration

See [`.env.example`](.env.example). Key vars:

| Var | Default | Notes |
|---|---|---|
| `NBA_SCOUT_LLM_PROVIDER` | `anthropic` | or `bedrock` |
| `NBA_SCOUT_EMBEDDING_PROVIDER` | `fastembed` | or `bedrock` (set `EMBEDDING_DIM=1024`) |
| `NBA_SCOUT_VECTOR_STORE` | `memory` | or `pgvector` |
| `NBA_SCOUT_MCP_SERVER_URL` | _unset_ | if set, stats agent calls nba-mcp-server here |

## Development

```bash
ruff check .
pytest
```

## Roadmap

- [x] Config-driven providers (LLM / embeddings / vector store)
- [x] Ingestion pipeline (bundled summaries + PDF loader) and retrieval
- [ ] LangGraph agent graph: router → rules / stats → synthesis
- [ ] FastAPI service with streaming + `/healthz`
- [ ] LangSmith / OpenTelemetry tracing
- [ ] RAG evaluation harness (faithfulness, context recall)
- [ ] Docker image + Terraform (ECS Fargate, RDS Postgres, Bedrock)

## License

MIT
