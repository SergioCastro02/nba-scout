"""Stats agent: a small ReAct loop over the live-stats tools."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from ..llm import get_chat_model
from ..stats_tools import get_stats_tools
from ._util import message_text
from .state import AssistantState

_SYSTEM = (
    "You answer NBA statistics questions using the provided tools. "
    "Resolve player names with find_player before calling player_career_stats. "
    "Seasons are 'YYYY-YY'. Report the numbers you retrieved; do not guess. "
    "If a tool returns an error, say what failed."
)


def run_stats_agent(state: AssistantState) -> AssistantState:
    agent = create_react_agent(get_chat_model(), get_stats_tools())
    result = agent.invoke(
        {"messages": [SystemMessage(_SYSTEM), HumanMessage(state["question"])]}
    )
    return {"stats_findings": message_text(result["messages"][-1])}
