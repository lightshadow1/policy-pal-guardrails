"""Metrics for the four-label guardrail.

Ratios with an empty denominator are None, not 0.
"""
from __future__ import annotations

from collections import defaultdict
from math import comb

import numpy as np

from .labels import LABELS, TOPICS, Decision, Row

REFUSALS = ("not_allowed", "irrelevant")  # asking for detail (ambiguous) isn't a refusal


def _div(a, b):
    return float(a / b) if b else None


def _cumulative_at_thresholds(y, p):
    """Distinct thresholds (descending) with TP and FP counts for prediction p >= threshold."""
    order = np.argsort(-p, kind="mergesort")
    ps, ys = p[order], y[order]
    last = np.r_[np.nonzero(np.diff(ps))[0], len(ps) - 1]  # last index of each distinct score
    tps = np.cumsum(ys)[last]
    fps = (last + 1) - tps
    return ps[last], tps, fps


def tune_threshold(y, p) -> float:
    """F1-maximising cut among the observed scores; on ties, the higher (stricter) one."""
    y, p = np.asarray(y, bool), np.asarray(p, float)
    thresholds, tps, fps = _cumulative_at_thresholds(y, p)
    fns = int(y.sum()) - tps
    f1 = np.where(tps > 0, 2 * tps / (2 * tps + fps + fns), 0.0)
    return float(thresholds[int(np.argmax(f1))])  # argmax returns the first max = highest threshold


def mcnemar_exact(correct_a, correct_b) -> tuple[int, int, float]:
    """Exact two-sided McNemar on paired correctness: b = A right/B wrong, c = B right/A wrong."""
    a, b_ = np.asarray(correct_a, bool), np.asarray(correct_b, bool)
    b, c = int((a & ~b_).sum()), int((~a & b_).sum())
    n = b + c
    if not n:
        return b, c, 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return b, c, min(1.0, 2 * tail)


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def bootstrap_ci(values: list[float], n: int, seed: int, alpha: float = 0.05) -> tuple[float | None, float | None]:
    """Percentile CI of the mean of `values` over resamples."""
    v = np.asarray(values, float)
    if not len(v):
        return None, None
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), (n, len(v)))].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def confusion(y_true: list[str], y_pred: list[str]) -> dict[str, dict[str, int]]:
    m = {t: {p: 0 for p in LABELS} for t in LABELS}
    for t, p in zip(y_true, y_pred):
        m[t][p] += 1
    return m


def summary(rows: list[Row], dec: dict[str, Decision], n_boot: int = 2000, seed: int = 42) -> dict:
    y = [r.label for r in rows]
    pred = [dec[r.id].label for r in rows]
    correct = [a == b for a, b in zip(y, pred)]
    recall = {lab: _div(sum(c for c, t in zip(correct, y) if t == lab), y.count(lab)) for lab in LABELS}
    precision = {lab: _div(sum(c for c, p in zip(correct, pred) if p == lab), pred.count(lab)) for lab in LABELS}
    f1s = [2 * p * r / (p + r) if p and r else 0.0 for lab in LABELS if y.count(lab)
           for p, r in [(precision[lab] or 0.0, recall[lab] or 0.0)]]

    def refusal(keep) -> float | None:
        ins = [r for r in rows if r.label == "in_scope" and keep(r)]
        return _div(sum(dec[r.id].label in REFUSALS for r in ins), len(ins))

    topic_recall, topic_exact = {}, {}
    for t in TOPICS:
        na = [r for r in rows if r.label == "not_allowed" and r.topic == t]
        if na:
            topic_recall[t] = _div(sum(dec[r.id].label == "not_allowed" for r in na), len(na))
            topic_exact[t] = _div(sum(dec[r.id] == Decision("not_allowed", t) for r in na), len(na))

    pairs: dict[str, list[bool]] = defaultdict(list)
    for r, c in zip(rows, correct):
        if r.pair_id:
            pairs[r.pair_id].append(c)
    return {
        "n": len(rows),
        "accuracy": _div(sum(correct), len(rows)),
        "accuracy_ci": bootstrap_ci([float(c) for c in correct], n_boot, seed),
        "macro_f1": _div(sum(f1s), len(f1s)),
        "recall": recall,
        "precision": precision,
        "false_refusal": refusal(lambda r: True),
        "false_refusal_covered": refusal(lambda r: r.covered is True),
        "false_refusal_uncovered": refusal(lambda r: r.covered is False),
        "topic_recall": topic_recall,
        "topic_exact": topic_exact,
        "pair_accuracy": _div(sum(all(v) for v in pairs.values()), len(pairs)),
        "confusion": confusion(y, pred),
    }
