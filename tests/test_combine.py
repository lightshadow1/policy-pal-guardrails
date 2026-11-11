import pytest

from ppguard.combine import decide
from ppguard.definitions import ROUND1, Definitions
from ppguard.labels import Decision

R2 = Definitions(2, topics={"legal": "l", "privacy": "p"}, in_scope="s", ambiguous="a")


@pytest.mark.parametrize("scores,hit,want", [
    ({"legal": .9, "privacy": .95, "ambiguous": .9, "in_scope": .9}, True, Decision("not_allowed", "privacy")),
    ({"legal": .1, "privacy": .1, "ambiguous": .9, "in_scope": .9}, True, Decision("ambiguous")),
    ({"legal": .1, "privacy": .1, "ambiguous": .1, "in_scope": .9}, False, Decision("in_scope")),
    ({"legal": .1, "privacy": .1, "ambiguous": .1, "in_scope": .2}, True, Decision("irrelevant")),
])
def test_decide_precedence_round2(scores, hit, want):
    assert decide(scores, R2, {}, hit) == want


def test_decide_round1_uses_retrieval():
    low = {n: .1 for n in ROUND1.topics}
    assert decide(low, ROUND1, {}, True) == Decision("in_scope")
    assert decide(low, ROUND1, {}, False) == Decision("irrelevant")


def test_decide_uses_per_score_thresholds():
    s = {"legal": .4, "privacy": .1, "ambiguous": .1, "in_scope": .6}
    assert decide(s, R2, {"legal": .3}, True) == Decision("not_allowed", "legal")
    assert decide(s, R2, {"in_scope": .7}, True) == Decision("irrelevant")


def test_decide_scope_first_answers_in_scope_before_asking_for_detail():
    s = {"legal": .1, "privacy": .1, "ambiguous": .9, "in_scope": .9}
    assert decide(s, R2, {}, True) == Decision("ambiguous")
    assert decide(s, R2, {}, True, scope_first=True) == Decision("in_scope")
    assert decide({**s, "in_scope": .1}, R2, {}, True, scope_first=True) == Decision("ambiguous")
    assert decide({**s, "privacy": .95}, R2, {}, True, scope_first=True) == Decision("not_allowed", "privacy")
