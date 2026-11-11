import pytest
from conftest import row

from ppguard.definitions import Definitions
from ppguard.tune import tune_thresholds

R2 = Definitions(2, topics={"legal": "l", "privacy": "p"}, in_scope="s", ambiguous="a")


def test_tune_refuses_week2():
    with pytest.raises(ValueError, match="week"):
        tune_thresholds([row("x", week=2, label="in_scope")], {}, R2)


def test_tune_thresholds_finds_separating_cut():
    rows = [row("l1", "not_allowed", topic="legal", week=1), row("l2", "not_allowed", topic="legal", week=1),
            row("i1", "in_scope", covered=True, week=1), row("i2", "in_scope", covered=True, week=1),
            row("x1", "irrelevant", week=1), row("a1", "ambiguous", week=1)]
    sc = {"l1": .8, "l2": .7, "i1": .3, "i2": .2, "x1": .25, "a1": .1}
    scores = {r: {"legal": v, "privacy": .1, "in_scope": {"i1": .9, "i2": .8}.get(r, .2), "ambiguous":
                  .9 if r == "a1" else .2} for r, v in sc.items()}
    t = tune_thresholds(rows, scores, R2)
    assert t["legal"] == pytest.approx(.7) and t["in_scope"] == pytest.approx(.8) and t["ambiguous"] == pytest.approx(.9)
    assert t["privacy"] == 0.5  # no positives in week 1: keep the day-one default rather than fit noise


def test_tune_falls_back_when_scores_have_one_distinct_value():
    rows = [row("l1", "not_allowed", topic="legal", week=1), row("l2", "not_allowed", topic="legal", week=1),
            row("i1", "in_scope", covered=True, week=1), row("x1", "irrelevant", week=1)]
    flat = {r.id: {"legal": 0.0, "privacy": 0.0, "in_scope": .7 if r.label == "in_scope" else .2, "ambiguous": .1}
            for r in rows}
    t = tune_thresholds(rows, flat, R2)
    assert t["legal"] == 0.5  # every score 0: a fitted cut would fire on every question
    assert t["in_scope"] == pytest.approx(.7)  # informative scores still get a fitted cut
