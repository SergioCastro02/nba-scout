"""Golden evaluation set.

Each case pins: the expected router decision, the knowledge-base sections that a
correct answer must draw on (retrieval check, no LLM needed), and the facts the
final answer must contain (judged by an LLM).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    question: str
    expected_route: list[str] = Field(description="which specialists should run")
    must_retrieve_sections: list[str] = Field(
        default_factory=list, description="KB section headings a correct answer relies on"
    )
    expected_points: list[str] = Field(description="facts the final answer must state (LLM-judged)")


DATASET: list[EvalCase] = [
    EvalCase(
        id="rules-foul-out",
        question="How many personal fouls before an NBA player is disqualified?",
        expected_route=["rules"],
        must_retrieve_sections=["Personal fouls and foul-out"],
        expected_points=["six personal fouls", "player is disqualified / must leave the game"],
    ),
    EvalCase(
        id="rules-flagrant-2",
        question="Is a flagrant 2 foul an automatic ejection?",
        expected_route=["rules"],
        must_retrieve_sections=["Flagrant fouls"],
        expected_points=["yes, a flagrant 2 is an automatic ejection"],
    ),
    EvalCase(
        id="rules-shot-clock-reset",
        question="What does the shot clock reset to after an offensive rebound?",
        expected_route=["rules"],
        must_retrieve_sections=["Shot clock"],
        expected_points=["it resets to 14 seconds"],
    ),
    EvalCase(
        id="rules-defensive-3s",
        question="What is the penalty for a defensive three-second violation?",
        expected_route=["rules"],
        must_retrieve_sections=["Defensive three seconds"],
        expected_points=[
            "it is a technical foul",
            "one free throw and the offense keeps possession",
        ],
    ),
    EvalCase(
        id="rules-coach-challenge",
        question="What can a coach challenge, and what happens if the challenge succeeds?",
        expected_route=["rules"],
        must_retrieve_sections=["Coach's challenge"],
        expected_points=[
            "a called foul, out-of-bounds, goaltending or basket interference",
            "the timeout is retained if the challenge succeeds",
        ],
    ),
    EvalCase(
        id="rules-play-in",
        question="Which seeds play in the play-in tournament?",
        expected_route=["rules"],
        must_retrieve_sections=["Play-In Tournament"],
        expected_points=["seeds 7 through 10 in each conference"],
    ),
    EvalCase(
        id="cba-second-apron",
        question="What restrictions apply to a team over the second apron?",
        expected_route=["rules"],
        must_retrieve_sections=["First and second aprons"],
        expected_points=[
            "cannot aggregate salaries in trades",
            "cannot use any mid-level exception",
            "first-round pick is frozen / moved to end of the first round",
        ],
    ),
    EvalCase(
        id="cba-max-salary",
        question="What is the maximum starting salary for a player with 7 years of service?",
        expected_route=["rules"],
        must_retrieve_sections=["Maximum player salary"],
        expected_points=["30% of the salary cap for 7-9 years of service"],
    ),
    EvalCase(
        id="cba-bird-rights",
        question="How many seasons does a team need to hold a player to earn full Bird rights?",
        expected_route=["rules"],
        must_retrieve_sections=["Bird rights"],
        expected_points=["three seasons for full Bird rights"],
    ),
    EvalCase(
        id="cba-65-game-rule",
        question="How many games must a player appear in to be eligible for MVP (2023 CBA)?",
        expected_route=["rules"],
        must_retrieve_sections=["Minimum roster and games-played rules"],
        expected_points=["at least 65 games"],
    ),
    EvalCase(
        id="stats-scoring-leader-2023-24",
        question="Who led the NBA in points per game in the 2023-24 regular season?",
        expected_route=["stats"],
        expected_points=[
            "Joel Embiid had the highest average (~34.7)",
            "Luka Doncic won the title (~33.9)",
        ],
    ),
    EvalCase(
        id="stats-jokic-playoffs",
        question="What are Nikola Jokic's career playoff scoring and rebounding averages?",
        expected_route=["stats"],
        expected_points=["around 27 points per game", "around 12 rebounds per game"],
    ),
    EvalCase(
        id="both-tech-and-draymond",
        question=(
            "How many technical fouls in a season trigger a suspension, and is Draymond "
            "Green known for technical fouls?"
        ),
        expected_route=["rules", "stats"],
        must_retrieve_sections=["Technical fouls"],
        expected_points=["16 technical fouls trigger a one-game suspension"],
    ),
]
