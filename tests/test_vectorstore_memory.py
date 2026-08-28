import numpy as np

from nba_scout.models import Chunk
from nba_scout.vectorstore.memory import InMemoryVectorStore


def _chunk(i: int) -> Chunk:
    return Chunk(id=f"s#{i}", source="s", section=f"sec{i}", text=f"text {i}")


def test_search_ranks_by_cosine_similarity():
    store = InMemoryVectorStore(path=None)
    store.add([_chunk(0), _chunk(1), _chunk(2)], [[1, 0, 0], [0, 1, 0], [0.9, 0.1, 0]])

    results = store.search([1, 0, 0], top_k=2)

    assert [r.chunk.id for r in results] == ["s#0", "s#2"]
    assert results[0].score > results[1].score
    assert results[0].score == 1.0


def test_empty_store_returns_nothing():
    assert InMemoryVectorStore(path=None).search([1, 0, 0], top_k=5) == []


def test_clear_empties_store():
    store = InMemoryVectorStore(path=None)
    store.add([_chunk(0)], [[1, 0, 0]])
    store.clear()
    assert store.count() == 0


def test_persistence_round_trip(tmp_path):
    path = tmp_path / "kb.npz"
    store = InMemoryVectorStore(path=path)
    store.add([_chunk(0), _chunk(1)], [[1.0, 0.0], [0.0, 1.0]])

    reopened = InMemoryVectorStore(path=path)
    assert reopened.count() == 2
    top = reopened.search([1.0, 0.0], top_k=1)[0]
    assert top.chunk.id == "s#0"
    assert np.isclose(top.score, 1.0)
