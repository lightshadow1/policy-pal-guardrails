import numpy as np
import pytest
from conftest import row

from ppguard.calibration import (choose_cut, evaluate, hybrid_decide, hybrid_outcomes, stratified_draw,
                                 summarize)
from ppguard.labels import Decision

TOPICS = ("legal", "medical", "investment", "prompt_attack", "privacy", "harmful")


def _scores(label: str, topic: str | None = None) -> dict:
    """Perfectly separable scores for one row."""
    s = {t: (0.9 if label == "not_allowed" and t == topic else 0.1) for t in TOPICS}
    s["in_scope"] = 0.9 if label == "in_scope" else 0.1
    s["ambiguous"] = 0.9 if label == "ambiguous" else 0.1
    return s


def test_stratified_draw_keeps_size_and_label_mix():
    pool = ([row(f"x{i}", "irrelevant", week=1) for i in range(60)] + [row(f"i{i}", "in_scope", covered=True, week=1)
            for i in range(30)] + [row(f"a{i}", "ambiguous", week=1) for i in range(10)])
    draw = stratified_draw(pool, 20, np.random.default_rng(42))
    labels = [r.label for r in draw]
    assert len(draw) == 20 and len({r.id for r in draw}) == 20
    assert (labels.count("irrelevant"), labels.count("in_scope"), labels.count("ambiguous")) == (12, 6, 2)
    again = stratified_draw(pool, 20, np.random.default_rng(42))
    assert [r.id for r in again] == [r.id for r in draw]


def test_stratified_draw_never_drops_a_label_with_rows():
    pool = [row(f"x{i}", "irrelevant", week=1) for i in range(98)] + [row("a0", "ambiguous", week=1),
                                                                       row("a1", "ambiguous", week=1)]
    draw = stratified_draw(pool, 10, np.random.default_rng(0))
    assert len(draw) == 10 and any(r.label == "ambiguous" for r in draw)


def test_summarize_percentiles_and_share_beating_baseline():
    s = summarize([0.1 * k for k in range(1, 11)], baseline=0.55)
    assert s["median"] == pytest.approx(0.55) and s["share_beats_baseline"] == pytest.approx(0.5)
    assert s["q25"] < s["median"] < s["q75"] and s["p5"] < s["q25"] and s["p95"] > s["q75"]


def test_evaluate_tunes_on_the_draw_and_scores_the_test_rows():
    tune = [row("t1", "in_scope", covered=True, week=1), row("t2", "irrelevant", week=1),
            row("t3", "not_allowed", topic="legal", week=1), row("t4", "ambiguous", week=1)]
    test = [row("w1", "in_scope", covered=True, week=2), row("w2", "irrelevant", week=2),
            row("w3", "not_allowed", topic="legal", week=2), row("w4", "ambiguous", week=2)]
    scores = {r.id: _scores(r.label, r.topic) for r in tune + test}
    m = evaluate(scores, tune, test, scope_first=False)
    assert m["accuracy"] == 1.0 and m["not_allowed_recall"] == 1.0 and m["in_scope_answered"] == 1.0
    untuned = evaluate(scores, None, test, scope_first=False)
    assert untuned["accuracy"] == 1.0  # 0.5 cuts also separate these scores


def test_hybrid_decide_gates_locally_then_defers_to_jev():
    jev = _scores("not_allowed", "legal")
    assert hybrid_decide(0.2, 0.5, jev, {}) == (Decision("irrelevant"), False)
    assert hybrid_decide(0.8, 0.5, jev, {}) == (Decision("not_allowed", "legal"), True)


def test_hybrid_outcomes_breaks_down_not_allowed_by_topic():
    rows = [row("caught", "not_allowed", topic="legal", week=2), row("local", "not_allowed", topic="legal", week=2),
            row("answered", "not_allowed", topic="legal", week=2), row("ok", "in_scope", covered=True, week=2)]
    local = {"caught": 0.9, "local": 0.1, "answered": 0.9, "ok": 0.9}
    jev = {"caught": _scores("not_allowed", "legal"), "local": _scores("not_allowed", "legal"),
           "answered": _scores("in_scope"), "ok": _scores("in_scope")}
    out = hybrid_outcomes(rows, local, jev, cut=0.5, t={})
    assert out["sent_to_jev"] == pytest.approx(0.75)
    assert out["not_allowed"]["legal"] == {"n": 3, "caught_by_jev": 1, "local_irrelevant": 1, "answered": 1,
                                           "other": 0}
    assert out["metrics"]["in_scope_answered"] == 1.0


def test_choose_cut_maximises_dev_macro_f1_and_prefers_the_lower_cut_on_ties():
    rows = [row("i", "in_scope", covered=True, week=1), row("x", "irrelevant", week=1)]
    local = {"i": 0.75, "x": 0.25}
    jev = {"i": _scores("in_scope"), "x": _scores("in_scope")}  # Jev alone would answer the off-topic one
    cut, f1 = choose_cut(rows, local, jev, {}, cuts=[0.1, 0.3, 0.5, 0.7, 0.9])
    assert cut == 0.3 and f1 == 1.0


def test_curve_chart_writes_a_png(tmp_path):
    from ppguard.calibration import SIZES, curve_chart
    s = {"median": .5, "q25": .45, "q75": .55, "p5": .4, "p95": .6}
    point = {"macro_f1": .5}
    res = {m: {rule: {"summary": {size: {"macro_f1": s} for size in SIZES}, "baseline": point, "full": point}
               for rule in ("r2", "r2b")} for m in ("jev", "gliner")}
    curve_chart(res, tmp_path / "curve.png")
    data = (tmp_path / "curve.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 10_000
