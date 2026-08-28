"""Shared state for the assistant graph."""

from __future__ import annotations

from typing import Annotated, TypedDict

from ..models import RetrievedChunk


def _keep_last(a: str | None, b: str | None) -> str | None:
    return b if b is not None else a


class AssistantState(TypedDict, total=False):
    question: str

    # set by the router: which specialist agents should run
    route: list[str]

    # rules agent output
    retrieved: list[RetrievedChunk]
    rules_findings: Annotated[str | None, _keep_last]

    # stats agent output
    stats_findings: Annotated[str | None, _keep_last]

    # synthesis output
    answer: str
