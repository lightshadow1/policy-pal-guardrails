from conftest import row

from ppguard.definitions import ROUND2
from ppguard.finetune import ft_schema, parse_scores, split_week1, to_record


def _task(rec, name):
    return next((c for c in rec["output"]["classifications"] if c["task"] == name), None)


def test_schema_uses_round2_definitions_all_multi_label():
    s = ft_schema(ROUND2)
    assert s["topic"]["labels"] == ROUND2.topics
    assert set(s["scope"]["labels"]) == {"in_scope", "irrelevant"} and set(s["clarity"]["labels"]) == {"ambiguous", "clear"}
    assert all(t["multi_label"] and t["cls_threshold"] == 0.0 for t in s.values())


def test_to_record_in_scope_has_scope_and_no_topic():
    rec = to_record("How many vacation days?", "in_scope", None, ROUND2)
    assert _task(rec, "topic")["true_label"] == []
    assert _task(rec, "scope")["true_label"] == ["in_scope"]
    assert _task(rec, "clarity")["true_label"] == ["clear"]


def test_to_record_not_allowed_and_ambiguous_skip_scope():
    na = to_record("Should I sue?", "not_allowed", "legal", ROUND2)
    assert _task(na, "topic")["true_label"] == ["legal"] and _task(na, "scope") is None
    amb = to_record("what about it", "ambiguous", None, ROUND2)
    assert _task(amb, "clarity")["true_label"] == ["ambiguous"] and _task(amb, "scope") is None
    assert _task(amb, "topic")["label_descriptions"] == ROUND2.topics


def test_split_week1_is_stratified_disjoint_and_week1_only():
    rows = [row(f"c{i}", "irrelevant", source="clinc", week=1) for i in range(40)]
    rows += [row(f"a{i}", "not_allowed", topic="harmful", source="aegis", week=1) for i in range(20)]
    rows += [row(f"w{i}", "irrelevant", source="clinc", week=2) for i in range(10)]
    train, dev = split_week1(rows, frac=0.15, seed=42)
    assert not train & dev and not any(i.startswith("w") for i in train | dev)
    assert sum(i.startswith("c") for i in dev) == 6 and sum(i.startswith("a") for i in dev) == 3


def test_parse_scores_maps_tasks_to_score_names():
    rec = {"id": "x", "topic": {"legal": 0.7, "privacy": 0.1}, "scope": {"in_scope": 0.8, "irrelevant": 0.3},
           "clarity": {"ambiguous": 0.2, "clear": 0.9}}
    assert parse_scores(rec) == {"legal": 0.7, "privacy": 0.1, "in_scope": 0.8, "ambiguous": 0.2}


def test_v2_schema_topic_and_clarity_single_label_with_none():
    s = ft_schema(ROUND2, single=True)
    assert s["topic"]["multi_label"] is False and set(s["topic"]["labels"]) == set(ROUND2.topics) | {"none"}
    assert s["clarity"]["multi_label"] is False and s["scope"]["multi_label"] is True


def test_to_record_v2_targets_none_and_single_choice():
    rec = to_record("How many vacation days?", "in_scope", None, ROUND2, single=True)
    assert _task(rec, "topic")["true_label"] == ["none"] and _task(rec, "topic")["multi_label"] is False
    assert _task(rec, "clarity")["true_label"] == ["clear"] and _task(rec, "clarity")["multi_label"] is False
    na = to_record("Should I sue?", "not_allowed", "legal", ROUND2, single=True)
    assert _task(na, "topic")["true_label"] == ["legal"]


def test_parse_scores_reads_single_label_outputs():
    rec = {"id": "x", "topic": {"privacy": 0.8}, "scope": {"in_scope": 0.3, "irrelevant": 0.9}, "clarity": {"clear": 0.7}}
    s = parse_scores(rec, topics=["legal", "privacy"])
    assert s["privacy"] == 0.8 and s["legal"] == 0.0 and s["in_scope"] == 0.3
    assert abs(s["ambiguous"] - 0.3) < 1e-9
    none = parse_scores({"id": "y", "topic": {"none": 0.9}, "scope": {"in_scope": 0.8, "irrelevant": 0.1},
                         "clarity": {"ambiguous": 0.6}}, topics=["legal"])
    assert none["legal"] == 0.0 and none["ambiguous"] == 0.6


def test_near_duplicate_ids_flags_paraphrases_of_test_rows():
    from ppguard.finetune import near_duplicate_ids
    train = [row("what is the day off request status", week=1), row("how do i bake bread", week=1)]
    test = [row("what is the day off request status please", week=2)]
    assert near_duplicate_ids(train, test, cut=0.6) == {"what is the day off request status"}


def test_oversample_repeats_by_label():
    from ppguard.finetune import oversample
    rows = [row("a", "not_allowed", topic="legal"), row("b", "ambiguous"), row("c", "in_scope", covered=True)]
    out = oversample(rows, {"not_allowed": 2, "ambiguous": 3})
    assert [r.id for r in out].count("a") == 2 and [r.id for r in out].count("b") == 3 and [r.id for r in out].count("c") == 1
