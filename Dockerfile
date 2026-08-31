# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/models

WORKDIR /app

# --- dependencies (cached layer) --- #
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# --- pre-download the local embedding model so the image runs offline --- #
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')" \
    && chmod -R a+rX /opt/models

# --- non-root --- #
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

# `serve` by default; override the command with `ingest` for the one-shot job.
ENTRYPOINT ["nba-scout"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
