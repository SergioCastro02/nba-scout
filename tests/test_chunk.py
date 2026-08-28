from nba_scout.ingest.chunk import split_text


def test_short_text_is_one_chunk():
    assert split_text("one paragraph only", chunk_size=900, chunk_overlap=100) == [
        "one paragraph only"
    ]


def test_packs_paragraphs_up_to_size():
    text = "\n\n".join(f"paragraph number {i} with some words" for i in range(20))
    chunks = split_text(text, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 120 + 40 for c in chunks)  # size + overlap slack


def test_overlap_carries_context():
    text = "AAAA BBBB CCCC.\n\n" + "D" * 200 + "\n\n" + "EEEE FFFF."
    chunks = split_text(text, chunk_size=100, chunk_overlap=30)
    # the giant middle paragraph must be hard-wrapped
    assert len(chunks) >= 3


def test_giant_single_paragraph_is_wrapped():
    chunks = split_text("Z" * 5000, chunk_size=1000, chunk_overlap=100)
    assert len(chunks) == 6
    assert all(len(c) <= 1000 for c in chunks)
