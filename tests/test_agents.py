"""Agent-graph wiring tests. LLM and the stats ReAct loop are faked (see conftest);
retrieval uses the fake embedder + non-persistent store."""

import pytest

from nba_scout.agents.graph import answer_question, build_graph
from nba_scout.agents.router import route
from nba_scout.agents.rules import run_rules_agent
from nba_scout.ingest import ingest


@pytest.fixture(autouse=True)
def _kb(fake_embedder, memory_store):
    ingest(reset=True)


def test_router_returns_requested_agents(fake_chat):
    fake_chat.route_agents = ("rules", "stats")
    assert set(route({"question": "flagrant 2 and who has the most?"})["route"]) == {
        "rules",
        "stats",
    }


def test_router_defaults_to_rules_when_empty(fake_chat):
    fake_chat.route_agents = ()
    assert route({"question": "hmm"})["route"] == ["rules"]


def test_rules_agent_retrieves_and_answers(fake_chat):
    out = run_rules_agent({"question": "how many fouls to foul out?"})
    assert out["rules_findings"] == "canned answer"
    assert len(out["retrieved"]) > 0
    # the LLM was handed a numbered context block
    human_msg = fake_chat.calls[-1][-1]
    assert "[1]" in human_msg[1]


def test_graph_rules_only_path(fake_chat):
    fake_chat.route_agents = ("rules",)
    state = answer_question("what is a clear-path foul?")
    assert state["route"] == ["rules"]
    assert state["answer"] == "canned answer"
    assert "stats_findings" not in state or state["stats_findings"] is None


def test_graph_runs_both_specialists(fake_chat):
    fake_chat.route_agents = ("rules", "stats")
    state = answer_question("is a flagrant 2 an ejection, and who leads the league?")
    assert set(state["route"]) == {"rules", "stats"}
    assert state["rules_findings"] == "canned answer"
    assert state["stats_findings"] == "stats: 27.1 ppg"
    assert state["answer"] == "canned answer"


def test_graph_is_acyclic_and_has_expected_nodes():
    nodes = set(build_graph().compile().get_graph().nodes)
    assert {"router", "rules", "stats", "synthesis"} <= nodes
