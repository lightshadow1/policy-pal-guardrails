import pytest
from conftest import row

from ppguard.definitions import ROUND1
from ppguard.labels import Decision
from ppguard.report import Run, decisions, evaluate_all, export_misses, render_markdown


def test_decisions_regex_ignores_cache():
    rows = [row("I want to sue the company over my review", "not_allowed", topic="legal", week=2)]
    assert decisions("regex", ROUND1, rows, {}, {})[rows[0].id] == Decision("not_allowed", "legal")


def test_decisions_missing_cache_row_names_it():
    rows = [row("x", "in_scope", week=2)]
    with pytest.raises(KeyError, match=rows[0].id):
        decisions("jev", ROUND1, rows, {}, {})


def test_decisions_round1_model_uses_scores_then_retrieval():
    rows = [row("Should I get a lawyer?", "not_allowed", topic="legal", week=2),
            row("What is the capital of France?", "irrelevant", week=2)]
    cache = {"Should I get a lawyer?": {"scores": {"legal": .9, "medical": .1, "investment": .1, "prompt_attack": .1}},
             "What is the capital of France?": {"scores": {"legal": .1, "medical": .1, "investment": .1,
                                                           "prompt_attack": .1}}}
    dec = decisions("jev", ROUND1, rows, cache, {})
    assert dec["Should I get a lawyer?"] == Decision("not_allowed", "legal")
    assert dec["What is the capital of France?"] == Decision("irrelevant")


def test_export_misses_only_week1_wrong(tmp_path):
    rows = [row("a", "in_scope", week=1), row("b", "in_scope", week=1), row("c", "in_scope", week=2)]
    dec = {"a": Decision("in_scope"), "b": Decision("irrelevant"), "c": Decision("irrelevant")}
    export_misses(rows, dec, tmp_path / "m.csv")
    lines = (tmp_path / "m.csv").read_text().splitlines()
    assert len(lines) == 2 and lines[1].endswith(",b")


def test_evaluate_all_reports_week2_per_source_and_mcnemar():
    rows = [row("a", "in_scope", covered=True, week=2), row("b", "irrelevant", week=2),
            row("c", "in_scope", covered=True, week=1)]
    good = {r.id: Decision(r.label) for r in rows}
    bad = {r.id: Decision("irrelevant") for r in rows}
    res = evaluate_all(rows, [Run("good", good, {}), Run("bad", bad, {"a": {"latency_s": .1, "cost_usd": 2e-5}})],
                       n_boot=20)
    assert res["week2"]["good"]["n"] == 2 and res["week2"]["bad"]["accuracy"] == 0.5
    assert res["week1"]["good"]["n"] == 1 and set(res["per_source"]["good"]) == {"test"}
    assert res["mcnemar"][0]["a"] == "good" and res["mcnemar"][0]["b"] == "bad"
    assert res["usage"]["bad"]["cost_per_1k"] == pytest.approx(2e-5 / 1 * 1000)


def test_render_markdown_has_headline_table():
    rows = [row("a", "in_scope", covered=True, week=2), row("b", "irrelevant", week=2)]
    res = evaluate_all(rows, [Run("regex", {r.id: Decision(r.label) for r in rows}, {})], n_boot=20)
    md = render_markdown(res, title="Round 1")
    assert "| guardrail |" in md and "false refusals" in md and "regex" in md


def test_decisions_scope_first_passes_through():
    from ppguard.definitions import Definitions
    r2 = Definitions(2, topics={"legal": "l"}, in_scope="s", ambiguous="a")
    rows = [row("q", "in_scope", covered=True, week=2)]
    cache = {"q": {"scores": {"legal": .1, "in_scope": .9, "ambiguous": .9}}}
    assert decisions("jev", r2, rows, cache, {})["q"] == Decision("ambiguous")
    assert decisions("jev", r2, rows, cache, {}, scope_first=True)["q"] == Decision("in_scope")


def test_round2_variants_include_untuned_2b():
    from ppguard.report import ROUND2_VARIANTS
    assert {(name, tuned, scope_first) for name, tuned, scope_first in ROUND2_VARIANTS} == {
        ("r2@0.5", False, False), ("r2-tuned", True, False), ("r2b@0.5", False, True), ("r2b-tuned", True, True)}
