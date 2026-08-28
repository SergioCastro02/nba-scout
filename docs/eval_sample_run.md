# nba-scout evaluation

_graph + LLM judge. Judge scores are LLM-graded and vary between runs; treat them as a trend._

| metric | score |
| --- | --- |
| context_recall | 0.846 |
| reciprocal_rank | 0.846 |
| route_accuracy | 0.917 |
| faithfulness | 1.000 |
| correctness | 0.958 |

| case | ctx recall | RR | route | faithful | correct |
| --- | --- | --- | --- | --- | --- |
| rules-foul-out | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| rules-flagrant-2 | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| rules-shot-clock-reset | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| rules-defensive-3s | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| rules-coach-challenge | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| rules-play-in | 0.00 | 0.00 | ✗ | — | 1.00 |
| cba-second-apron | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| cba-max-salary | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| cba-bird-rights | 0.00 | 0.00 | — | — | — |
| cba-65-game-rule | 1.00 | 1.00 | ✓ | 1.00 | 1.00 |
| stats-scoring-leader-2023-24 | 1.00 | 1.00 | ✓ | — | 0.50 |
| stats-jokic-playoffs | 1.00 | 1.00 | ✓ | — | 1.00 |
| both-tech-and-draymond | 1.00 | 1.00 | ✓ | — | 1.00 |

## errors

- **cba-bird-rights**: ReadTimeout: The read operation timed out
