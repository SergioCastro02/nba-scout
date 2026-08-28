"""FastAPI service wrapping the assistant graph.

Endpoints:
    GET  /healthz       liveness + effective configuration
    POST /ask           run the graph, return the final answer
    POST /ask/stream    Server-Sent Events: one event per graph node, then the answer
    GET  /              points at /docs

LangSmith tracing turns on automatically when LANGSMITH_TRACING=true and
LANGSMITH_API_KEY are set in the environment (LangChain reads them directly).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .. import __version__
from ..config import get_settings
from .schemas import AskRequest, AskResponse, HealthResponse, Source

log = logging.getLogger("nba_scout.api")

# Phrases that mean "the operator didn't give us LLM credentials" -> 503 not 500.
_AUTH_HINTS = ("api key", "api_key", "credential", "unauthenticated", "permission", "quota")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    )
    log.info("nba-scout api %s starting", __version__)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="nba-scout",
        version=__version__,
        summary="Multi-agent NBA assistant: rulebook/CBA knowledge base + live stats.",
        lifespan=_lifespan,
    )

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["x-request-id"] = request_id
        log.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                }
            )
        )
        return response

    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({"service": "nba-scout", "version": __version__, "docs": "/docs"})

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        s = get_settings()
        try:
            from ..vectorstore import get_vector_store

            chunks = get_vector_store().count()
        except Exception:  # noqa: BLE001 - health must never raise
            chunks = -1
        return HealthResponse(
            version=__version__,
            llm_provider=s.llm_provider,
            embedding_provider=s.embedding_provider,
            vector_store=s.vector_store,
            knowledge_base_chunks=chunks,
        )

    @app.post("/ask", response_model=AskResponse)
    async def ask(body: AskRequest):
        from ..agents.graph import get_compiled_graph

        try:
            state = await get_compiled_graph().ainvoke({"question": body.question})
        except Exception as e:  # noqa: BLE001 - map to a clean HTTP error
            return _error_response(e)
        return _to_response(body.question, state)

    @app.post("/ask/stream")
    async def ask_stream(body: AskRequest):
        from ..agents.graph import get_compiled_graph

        async def events() -> AsyncIterator[str]:
            graph = get_compiled_graph()
            final: dict = {}
            try:
                async for update in graph.astream(
                    {"question": body.question}, stream_mode="updates"
                ):
                    for node, delta in update.items():
                        final.update(delta or {})
                        yield _sse("step", {"node": node, "keys": list((delta or {}).keys())})
                payload = _to_response(body.question, final).model_dump()
                yield _sse("answer", payload)
            except Exception as e:  # noqa: BLE001
                yield _sse("error", {"detail": _classify(e)[1]})

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


# --------------------------------------------------------------------------- #
def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _to_response(question: str, state: dict) -> AskResponse:
    sources = [
        Source(citation=r.chunk.citation(), score=round(r.score, 3))
        for r in state.get("retrieved", []) or []
    ]
    return AskResponse(
        question=question,
        route=state.get("route", []),
        answer=state.get("answer") or "(no answer produced)",
        sources=sources,
    )


def _classify(e: Exception) -> tuple[int, str]:
    text = str(e).lower()
    if any(h in text for h in _AUTH_HINTS):
        return 503, (
            "LLM provider not configured or unavailable "
            f"({get_settings().llm_provider}): {e}"
        )
    return 500, f"{type(e).__name__}: {e}"


def _error_response(e: Exception) -> JSONResponse:
    status, detail = _classify(e)
    log.warning("request failed: %s", detail)
    return JSONResponse(status_code=status, content={"detail": detail})


app = create_app()
