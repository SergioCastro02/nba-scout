from nba_scout.ingest.corpus import load_bundled


def test_load_bundled_returns_sectioned_documents():
    docs = load_bundled()
    assert len(docs) >= 20

    sources = {d.source for d in docs}
    assert sources == {"NBA Rules (summary)", "NBA CBA (summary)"}

    # every bundled doc has a section heading and non-trivial body
    assert all(d.section for d in docs)
    assert all(len(d.text) > 40 for d in docs)


def test_known_rule_is_present():
    docs = load_bundled()
    foul_out = next(d for d in docs if d.section == "Personal fouls and foul-out")
    assert "six personal fouls" in foul_out.text
