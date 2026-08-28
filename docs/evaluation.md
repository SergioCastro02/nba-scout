# Evaluation

`nba-scout eval` runs a golden set (`src/nba_scout/eval/dataset.py`) through the
pipeline and scores it. Retrieval metrics are deterministic; quality metrics use
an LLM as judge.

## Metrics

| Metric | LLM? | What it measures |
|---|---|---|
| **context recall** | no | fraction of the KB sections a correct answer needs that were retrieved (top-k) |
| **reciprocal rank** | no | 1/rank of the first correct section — rewards putting the right passage first |
| **route accuracy** | router only | did the router pick exactly the expected specialist(s)? |
| **faithfulness** | yes (judge) | are the answer's claims supported by the retrieved context? (0–1) |
| **correctness** | yes (judge) | fraction of the case's expected facts the answer states (0–1) |

Each golden case pins the expected route, the required KB sections, and the facts
the answer must contain.

## Running it

```bash
nba-scout ingest

# deterministic, no API cost — safe for CI
nba-scout eval --retrieval-only

# full: runs the graph + LLM judge (needs NBA_SCOUT_*_API_KEY)
# --pace keeps you under per-minute quotas (Gemini free tier is 15 req/min)
nba-scout eval --judge --pace 20 --report docs/eval_sample_run.md

# quick subset
nba-scout eval --judge --limit 4
```

A failed case (transient provider error, etc.) is recorded in an **errors**
section instead of aborting the run. Transient 429/503s are retried, waiting the
delay the provider reports (`retryDelay`), capped at 60s.

## Caveats

- The bundled corpus is short original summaries, so retrieval scores are high.
  The harness earns its keep as the corpus grows to the full rulebook + CBA
  (`scripts/download_corpus.py`) and as a **regression gate** — run it before and
  after a change to chunking, the embedding model, or a prompt.
- Judge scores vary run to run (LLM non-determinism) and depend on the judge
  model. Treat them as a trend, not an absolute.
- Judge and generator use the same configured provider here; for a stricter
  setup, point the judge at a different/stronger model.

## Sample run

[`eval_sample_run.md`](eval_sample_run.md) is a committed `--judge` baseline. What
it currently surfaces:

- **`rules-play-in`** — the router misclassifies "which seeds play in the play-in
  tournament?" and retrieval misses the *Play-In Tournament* section. A real
  routing + recall gap.
- **`stats-scoring-leader-2023-24`** — the answer names one scoring leader but
  doesn't distinguish "highest average" (Embiid) from "won the title" (Doncic).
- Faithfulness is 1.0 across the pure-rules answers — the RAG grounding holds.

That is the point of the harness: it turns "seems fine" into a number that moves
when something regresses.
