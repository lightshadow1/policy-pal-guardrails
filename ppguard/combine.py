"""Turn a guardrail's raw scores into one of the four labels.

not_allowed > ambiguous > in_scope > irrelevant. In round 1 nothing defines in scope, so Policy Pal's keyword
retrieval decides it, as in the shipped pipeline.
"""
from __future__ import annotations

from .definitions import Definitions
from .labels import Decision

Thresholds = dict[str, float]  # score name -> cut (p >= cut fires); a missing name means 0.5
DEFAULT = 0.5


def decide(scores: dict[str, float], d: Definitions, t: Thresholds, hit: bool, scope_first: bool = False) -> Decision:
    """`scope_first` (round 2b) checks in scope before ambiguous: a question the model is confident is in scope gets
    answered rather than asked for detail. Found on week 1, where the ambiguous check swallowed in-scope questions."""
    fired = [(scores[name], name) for name in d.topics if scores[name] >= t.get(name, DEFAULT)]
    if fired:
        return Decision("not_allowed", max(fired)[1])
    if scope_first and d.in_scope and scores["in_scope"] >= t.get("in_scope", DEFAULT):
        return Decision("in_scope")
    if d.ambiguous and scores["ambiguous"] >= t.get("ambiguous", DEFAULT):
        return Decision("ambiguous")
    if d.in_scope:
        return Decision("in_scope" if scores["in_scope"] >= t.get("in_scope", DEFAULT) else "irrelevant")
    return Decision("in_scope" if hit else "irrelevant")
