"""Command-line entrypoint: `nba-scout <command>`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import __version__
from .config import get_settings


def _cmd_ingest(args: argparse.Namespace) -> None:
    from .ingest import ingest

    report = ingest(data_dir=Path(args.data_dir), reset=not args.no_reset)
    print(
        f"ingested {report.documents} documents -> {report.chunks} chunks "
        f"-> {report.stored} in the '{get_settings().vector_store}' store"
    )


def _cmd_ask(args: argparse.Namespace) -> None:
    from .retrieval import format_context, retrieve

    results = retrieve(args.question, top_k=args.top_k)
    print(format_context(results))


def _cmd_chat(args: argparse.Namespace) -> None:
    from .agents import answer_question

    state = answer_question(args.question)
    print(f"route: {', '.join(state.get('route', []))}\n")
    print(state["answer"])
    sources = {r.chunk.citation() for r in state.get("retrieved", [])}
    if sources:
        print("\nknowledge-base sources:")
        for s in sorted(sources):
            print(f"  - {s}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="nba-scout", description=f"nba-scout {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="build the knowledge base", parents=[common])
    p_ingest.add_argument("--data-dir", default="data", help="dir with downloaded PDFs (optional)")
    p_ingest.add_argument("--no-reset", action="store_true", help="keep existing rows")
    p_ingest.set_defaults(func=_cmd_ingest)

    p_ask = sub.add_parser(
        "ask", help="retrieve passages for a question (no LLM yet)", parents=[common]
    )
    p_ask.add_argument("question")
    p_ask.add_argument("--top-k", type=int, default=None)
    p_ask.set_defaults(func=_cmd_ask)

    p_chat = sub.add_parser(
        "chat",
        help="answer a question with the full agent graph (needs an LLM key)",
        parents=[common],
    )
    p_chat.add_argument("question")
    p_chat.set_defaults(func=_cmd_chat)

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    args.func(args)


if __name__ == "__main__":
    main()
