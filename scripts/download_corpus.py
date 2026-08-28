"""Download the source documents listed in corpus_sources.json into data/.

These are public reference documents (the NBA CBA, the rulebook). They are stored
locally only — data/ is gitignored — and indexed by `nba-scout ingest --data-dir data`.

    python scripts/download_corpus.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SOURCES = Path(__file__).with_name("corpus_sources.json")
DATA_DIR = ROOT / "data"


def main() -> int:
    spec = json.loads(SOURCES.read_text(encoding="utf-8"))
    DATA_DIR.mkdir(exist_ok=True)

    exit_code = 0
    for doc in spec["documents"]:
        dest = DATA_DIR / doc["filename"]
        url = doc.get("url")

        if dest.exists():
            print(f"= {doc['filename']} (already present)")
            continue
        if not url:
            print(f"! {doc['filename']}: no automatic URL.")
            print(f"    {doc.get('note', '')}")
            print(f"    official source: {doc.get('official_source')}")
            exit_code = 1
            continue

        print(f"↓ {doc['filename']}")
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=60) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            print(f"  saved {dest.stat().st_size // 1024} KiB -> {dest}")
        except Exception as e:  # noqa: BLE001 - report and continue to the next doc
            print(f"  FAILED: {type(e).__name__}: {e}")
            print(f"  download manually from {doc.get('official_source')}")
            dest.unlink(missing_ok=True)
            exit_code = 1

    print("\nNext: nba-scout ingest --data-dir data -v")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
