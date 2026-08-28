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

> **Status:** knowledge base + LangGraph agent graph + FastAPI service (streaming)
> all working. RAG eval and the AWS deploy are next — see [Roadmap](#roadmap).

## Design

| Concern | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | explicit state machine, inspectable, matches the JD |
| LLM | Bedrock / Anthropic / Google, config-selected | one interface (`llm.get_chat_model`); deploy on Bedrock, dev on Anthropic or a free Gemini key |
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

`ask` returns the raw retrieved passages. For a full answer through the agent
graph, set an LLM key and use `chat`:

```bash
# Google AI Studio gives a free API key with no credit card: https://aistudio.google.com/apikey
export NBA_SCOUT_LLM_PROVIDER=google
export NBA_SCOUT_GOOGLE_API_KEY=AIza...

nba-scout chat "is a flagrant 2 an automatic ejection, and who led the league in points in 2023-24?"
```

(Or `NBA_SCOUT_LLM_PROVIDER=anthropic` / `bedrock` with the matching credentials.)

The router sends the rules half to the RAG agent and the stats half to a ReAct
agent over the live-stats tools; the synthesis node merges them, keeping the
knowledge-base citations.

> One question makes ~3–5 LLM calls (router + each specialist + synthesis). On
> Gemini's free tier use a `*-flash-lite` model — the full `flash` models have a
> low daily request quota.

## HTTP API

```bash
nba-scout serve                 # http://127.0.0.1:8000  (docs at /docs)
```

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness + effective config (providers, store, KB size) |
| `POST /ask` | `{question}` → `{answer, route, sources}` |
| `POST /ask/stream` | Server-Sent Events: one `step` event per graph node, then a final `answer` event |
| `GET /docs` | OpenAPI UI |

```bash
curl -N -X POST localhost:8000/ask/stream \
  -H 'content-type: application/json' \
  -d '{"question":"is a flagrant 2 an ejection, and who led the league in blocks in 2023-24?"}'
```

```
event: step
data: {"node": "router", "keys": ["route"]}

event: step
data: {"node": "rules", "keys": ["retrieved", "rules_findings"]}

event: step
data: {"node": "stats", "keys": ["stats_findings"]}

event: step
data: {"node": "synthesis", "keys": ["answer"]}

event: answer
data: {"question": "...", "route": ["rules","stats"], "answer": "...", "sources": [...]}
```

Every response carries an `x-request-id` header and each request is logged as one
JSON line with method, path, status and latency.

### Tracing

Set these in the environment and every graph run is captured as a LangSmith trace
(one span per node, with latency and token counts):

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=lsv2_...
```

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
| `NBA_SCOUT_LLM_PROVIDER` | `anthropic` | or `bedrock`, or `google` (free tier) |
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
- [x] LangGraph agent graph: router → rules / stats → synthesis
- [x] FastAPI service: `/ask`, SSE `/ask/stream`, `/healthz`, request logging
- [x] LangSmith tracing (env-driven)
- [ ] Stats agent talks to `nba-mcp-server` over MCP when `MCP_SERVER_URL` is set
- [ ] OpenTelemetry export (spans + metrics)
- [ ] RAG evaluation harness (faithfulness, context recall)
- [ ] Multilingual embeddings (bge-m3) — cross-lingual recall is weak with bge-small-en
- [ ] Docker image + Terraform (ECS Fargate, RDS Postgres, Bedrock)

## License

MIT
