"""Fit thresholds on week 1 only."""
from __future__ import annotations

from .combine import DEFAULT, Thresholds
from .definitions import Definitions, score_names
from .labels import TOPICS, Row
from .metrics import tune_threshold


def _target(name: str, r: Row, has_topic: bool) -> bool | None:
    """One-vs-rest target for a score name; None = row left out of that fit."""
    if name == "in_scope":
        return {"in_scope": True, "irrelevant": False}.get(r.label)
    if name == "ambiguous":
        return r.label == "ambiguous"
    if r.label != "not_allowed":
        return False
    if not has_topic:
        return True  # a topic the ground truth doesn't name: any not_allowed row is a positive
    return True if r.topic == name else None  # other not_allowed topics are neither


def tune_thresholds(rows: list[Row], scores: dict[str, dict[str, float]], d: Definitions) -> Thresholds:
    """`scores` maps row id -> {score name: probability}."""
    bad = [r.id for r in rows if r.week != 1]
    if bad:
        raise ValueError(f"thresholds are tuned on week 1 only; got rows from another week, e.g. {bad[:3]}")
    out: Thresholds = {}
    for name in score_names(d):
        ys, ps = [], []
        for r in rows:
            y = _target(name, r, name in TOPICS)
            if y is not None:
                ys.append(y)
                ps.append(scores[r.id][name])
        # No positives, no negatives, or scores that never vary (a collapsed model): a fitted cut would be noise,
        # or would fire on every question, so keep the day-one default.
        informative = any(ys) and not all(ys) and len(set(ps)) >= 2
        out[name] = tune_threshold(ys, ps) if informative else DEFAULT
    return out
