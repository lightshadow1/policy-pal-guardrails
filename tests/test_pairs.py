import json
from collections import defaultdict
from pathlib import Path

from ppguard.sources import pair_rows

PAIRS = Path(__file__).resolve().parent.parent / "data" / "pairs.jsonl"


def test_pairs_file_is_well_formed():
    rows = [json.loads(line) for line in PAIRS.read_text().splitlines()]
    by_pair = defaultdict(list)
    for r in rows:
        by_pair[r["pair_id"]].append(r)
    assert len(by_pair) == 60 and all(len(v) == 2 for v in by_pair.values())
    for a, b in by_pair.values():
        assert sorted([a["label"] == "in_scope", b["label"] == "in_scope"]) == [False, True]
        assert all(r["trap"].lower() in r["text"].lower() for r in (a, b))
        assert 0.7 <= len(a["text"]) / len(b["text"]) <= 1 / 0.7
        assert next(r for r in (a, b) if r["label"] == "in_scope")["policy_ref"]


def test_pair_rows_need_review_and_keep_pair_id():
    rows = pair_rows(PAIRS)
    assert len(rows) == 120 and all(r.needs_review and r.label is None and r.pair_id for r in rows)
    assert rows[0].source == "pairs" and rows[0].note.startswith("expected: in_scope/")
