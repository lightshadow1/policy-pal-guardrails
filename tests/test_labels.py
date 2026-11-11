from ppguard.labels import LABELS, TOPICS, Row, make_id


def test_make_id_is_stable_and_whitespace_insensitive():
    assert make_id("clinc", "Where can I get my W2") == make_id("clinc", "  where can i  get my w2 ")
    assert make_id("clinc", "x") != make_id("aegis", "x")


def test_row_round_trips():
    r = Row(id="a:1", text="t", source="a", licence="CC-BY-4.0", label="not_allowed", topic="legal")
    assert Row.from_dict(r.to_dict()) == r


def test_label_and_topic_vocab():
    assert LABELS == ("in_scope", "irrelevant", "not_allowed", "ambiguous")
    assert set(TOPICS) == {"legal", "medical", "investment", "privacy", "harmful", "prompt_attack", "other"}
