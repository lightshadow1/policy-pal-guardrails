"""Evaluate the guardrails on the test set and write the markdown report.

    uv run python -m ppguard.report --round 1   # regex, jev-r1, gliner-r1 + the week 1 misses for review
    uv run python -m ppguard.report --round 2   # adds round 2 at 0.5 and at week-1-tuned thresholds

Headline numbers are week 2 only. Week 1 is where the misses are read and thresholds are tuned.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np

from .combine import Thresholds, decide
from .definitions import Definitions
from .labels import LABELS, TOPICS, Decision, Row
from .metrics import holm, mcnemar_exact, summary
from .regex_guard import regex_decide, retrieval_hit, scrub_text

ROOT = Path(__file__).resolve().parent.parent
# (name suffix, thresholds tuned on week 1?, check in scope before ambiguous?). 2b is post hoc: the ambiguous
# over-firing was first seen in the week 2 round-2 results, then confirmed on week 1.
ROUND2_VARIANTS = [("r2@0.5", False, False), ("r2-tuned", True, False), ("r2b@0.5", False, True), ("r2b-tuned", True, True)]
RESULTS = ROOT / "results"


@dataclass
class Run:
    name: str
    decisions: dict[str, Decision]
    cache: dict[str, dict] = field(default_factory=dict)  # id -> cache row (latency_s, cost_usd); empty for regex
    latencies: list[float] = field(default_factory=list)   # measured locally (regex)


def decisions(guard: str, d: Definitions, rows: list[Row], cache: dict[str, dict], t: Thresholds,
              scope_first: bool = False) -> dict[str, Decision]:
    if guard == "regex":
        return {r.id: regex_decide(r.text) for r in rows}
    out = {}
    for r in rows:
        if r.id not in cache:
            raise KeyError(f"no cached {guard} round {d.round} scores for {r.id}")
        hit = retrieval_hit(scrub_text(r.text)) if d.in_scope is None else False
        out[r.id] = decide(cache[r.id]["scores"], d, t, hit, scope_first)
    return out


def _source(r: Row) -> str:
    return r.source.replace(".stackexchange.com", "").replace(".com", "")


def _usage(run: Run, rows: list[Row]) -> dict:
    lat = run.latencies or [run.cache[r.id]["latency_s"] for r in rows if r.id in run.cache]
    costs = [run.cache[r.id].get("cost_usd") or 0.0 for r in rows if r.id in run.cache]
    return {"cost_per_1k": float(np.mean(costs)) * 1000 if costs else 0.0,
            "p50_ms": float(np.percentile(lat, 50)) * 1000 if lat else None,
            "p95_ms": float(np.percentile(lat, 95)) * 1000 if lat else None}


def evaluate_all(rows: list[Row], runs: list[Run], n_boot: int = 2000, seed: int = 42) -> dict:
    w1 = [r for r in rows if r.week == 1]
    w2 = [r for r in rows if r.week == 2]
    by_source: dict[str, list[Row]] = defaultdict(list)
    for r in w2:
        by_source[_source(r)].append(r)
    res = {"configs": [run.name for run in runs], "week1": {}, "week2": {}, "per_source": {}, "usage": {},
           "n_week1": len(w1), "n_week2": len(w2)}
    for run in runs:
        res["week2"][run.name] = summary(w2, run.decisions, n_boot, seed)
        res["week1"][run.name] = summary(w1, run.decisions, n_boot, seed)
        res["per_source"][run.name] = {s: summary(rs, run.decisions, n_boot, seed) for s, rs in sorted(by_source.items())}
        res["usage"][run.name] = _usage(run, rows)
    tests = []
    for a, b in combinations(runs, 2):
        ca = [a.decisions[r.id].label == r.label for r in w2]
        cb = [b.decisions[r.id].label == r.label for r in w2]
        n_ab, n_ba, p = mcnemar_exact(ca, cb)
        tests.append({"a": a.name, "b": b.name, "a_only": n_ab, "b_only": n_ba, "p": p})
    for t, adj in zip(tests, holm([t["p"] for t in tests])):
        t["p_holm"] = adj
    res["mcnemar"] = tests
    return res


def export_misses(rows: list[Row], dec: dict[str, Decision], path: Path) -> None:
    misses = [r for r in rows if r.week == 1 and dec[r.id].label != r.label]
    misses.sort(key=lambda r: (r.label, dec[r.id].label, r.source))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true_label", "true_topic", "pred_label", "pred_topic", "source", "text"])
        for r in misses:
            w.writerow([r.label, r.topic or "", dec[r.id].label, dec[r.id].topic or "", r.source, r.text])


def _pct(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}%"


def render_markdown(res: dict, title: str) -> str:
    names = res["configs"]
    w2 = res["week2"]
    out = [f"# {title}", "",
           f"Week 2 (test) only: {res['n_week2']} questions. Week 1 ({res['n_week1']}) is used for the review and for "
           "tuning; its numbers are in the last section.", "",
           "## Headline", "",
           "| guardrail | accuracy (95% CI) | macro-F1 | false refusals: all / covered / not covered | pairs both right "
           "| cost per 1k | p50 / p95 |",
           "|---|---|---|---|---|---|---|"]
    for n in names:
        s, u = w2[n], res["usage"][n]
        lo, hi = s["accuracy_ci"]
        lat = "–" if u["p50_ms"] is None else f"{u['p50_ms']:.0f} / {u['p95_ms']:.0f} ms"
        out.append(f"| {n} | {_pct(s['accuracy'])} ({_pct(lo)}–{_pct(hi)}) | {_pct(s['macro_f1'])} | "
                   f"{_pct(s['false_refusal'])} / {_pct(s['false_refusal_covered'])} / "
                   f"{_pct(s['false_refusal_uncovered'])} | {_pct(s['pair_accuracy'])} | ${u['cost_per_1k']:.4f} | {lat} |")
    out += ["", "False refusal = an in-scope question labelled not allowed or irrelevant. Asking for detail isn't "
            "counted as a refusal.", "", "## Recall per label", "",
            "| guardrail | " + " | ".join(LABELS) + " |", "|---|" + "---|" * len(LABELS)]
    out += [f"| {n} | " + " | ".join(_pct(w2[n]["recall"][lab]) for lab in LABELS) + " |" for n in names]
    topics = [t for t in TOPICS if any(t in w2[n]["topic_recall"] for n in names)]
    out += ["", "## Not allowed: caught (any topic) / right topic", "",
            "| guardrail | " + " | ".join(topics) + " |", "|---|" + "---|" * len(topics)]
    out += [f"| {n} | " + " | ".join(f"{_pct(w2[n]['topic_recall'].get(t))} / {_pct(w2[n]['topic_exact'].get(t))}"
                                      for t in topics) + " |" for n in names]
    sources = sorted({s for n in names for s in res["per_source"][n]})
    out += ["", "## Accuracy per source", "",
            "| source | n | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for s in sources:
        n_rows = res["per_source"][names[0]][s]["n"]
        out.append(f"| {s} | {n_rows} | " + " | ".join(_pct(res["per_source"][n][s]["accuracy"]) for n in names) + " |")
    if res["mcnemar"]:
        out += ["", "## Paired comparison (McNemar, Holm-adjusted)", "",
                "| A | B | only A right | only B right | p (Holm) |", "|---|---|---|---|---|"]
        out += [f"| {t['a']} | {t['b']} | {t['a_only']} | {t['b_only']} | {t['p_holm']:.3g} |" for t in res["mcnemar"]]
    out += ["", "## Confusion matrices (rows = true label, columns = predicted)", ""]
    for n in names:
        c = w2[n]["confusion"]
        out += [f"**{n}**", "", "| | " + " | ".join(LABELS) + " |", "|---|" + "---|" * len(LABELS)]
        out += [f"| {t} | " + " | ".join(str(c[t][p]) for p in LABELS) + " |" for t in LABELS]
        out.append("")
    w1 = res["week1"]
    out += ["## Week 1 (review and tuning set)", "", "| guardrail | accuracy | macro-F1 | false refusals |", "|---|---|---|---|"]
    out += [f"| {n} | {_pct(w1[n]['accuracy'])} | {_pct(w1[n]['macro_f1'])} | {_pct(w1[n]['false_refusal'])} |"
            for n in names]
    return "\n".join(out) + "\n"


def _model_run(cfg, name: str, guard: str, d: Definitions, rows: list[Row], t: Thresholds) -> Run | None:
    from .runner import cache_path, read_jsonl
    from .definitions import fingerprint
    fp = fingerprint(d, guard)
    cache = {r["id"]: r for r in read_jsonl(cache_path(cfg, guard, d)) if r.get("fingerprint") == fp}
    try:
        return Run(name, decisions(guard, d, rows, cache, t), cache)
    except KeyError as e:
        print(f"skipping {name}: {e.args[0]} (run `python -m ppguard.runner --guard {guard} --round {d.round}`)")
        return None


def _regex_run(rows: list[Row]) -> Run:
    dec, lat = {}, []
    for r in rows:
        t0 = time.perf_counter()
        dec[r.id] = regex_decide(r.text)
        lat.append(time.perf_counter() - t0)
    return Run("regex", dec, {}, lat)


def main(argv: list[str] | None = None) -> None:
    from . import definitions
    from .build import TESTSET, _read_rows
    from .config import Config
    from .tune import tune_thresholds
    ap = argparse.ArgumentParser(prog="python -m ppguard.report")
    ap.add_argument("--round", type=int, choices=[1, 2], required=True)
    args = ap.parse_args(argv)
    if not TESTSET.exists():
        raise SystemExit(f"{TESTSET} missing: finish the label review, then `python -m ppguard.build assemble`")
    cfg = Config.from_env()
    rows = _read_rows(TESTSET)
    runs = [_regex_run(rows)]
    for guard in ("jev", "gliner"):
        runs.append(_model_run(cfg, f"{guard}-r1", guard, definitions.ROUND1, rows, {}))
    if args.round == 2:
        r2 = definitions.ROUND2
        if r2 is None:
            raise SystemExit("ROUND2 is not defined yet")
        tuned = {}
        for guard in ("jev", "gliner"):
            base = _model_run(cfg, f"{guard}-r2@0.5", guard, r2, rows, {})
            if base is None:
                continue
            w1 = [r for r in rows if r.week == 1]
            tuned[guard] = tune_thresholds(w1, {r.id: base.cache[r.id]["scores"] for r in w1}, r2)
            for suffix, use_tuned, scope_first in ROUND2_VARIANTS:
                t = tuned[guard] if use_tuned else {}
                runs.append(Run(f"{guard}-{suffix}", decisions(guard, r2, rows, base.cache, t, scope_first), base.cache))
        (RESULTS / "thresholds_round2.json").write_text(json.dumps(tuned, indent=1))
    runs = [r for r in runs if r is not None]
    res = evaluate_all(rows, runs, cfg.n_bootstrap, cfg.seed)
    title = "Round 1: day one" if args.round == 1 else "Round 1 vs round 2 (and 2b: in scope checked before ambiguous)"
    md = render_markdown(res, title)
    if args.round == 2:
        md += _change_cost_section()
    out = RESULTS / ("report_round1.md" if args.round == 1 else "report.md")
    out.write_text(md)
    (RESULTS / f"report_round{args.round}.json").write_text(json.dumps(res, indent=1))
    if args.round == 1:
        for run in runs:
            export_misses(rows, run.decisions, RESULTS / "review" / f"week1_misses_{run.name.split('-')[0]}.csv")
    print(f"wrote {out}")


def _change_cost_section() -> str:
    from . import definitions
    if not hasattr(definitions, "change_cost") or definitions.ROUND2 is None:
        return ""
    c = definitions.change_cost(definitions.ROUND1, definitions.ROUND2, "jev")
    g = definitions.change_cost(definitions.ROUND1, definitions.ROUND2, "gliner")
    return ("\n## What adding the discovered topics cost\n\n"
            "| guardrail | change | labelled data | training |\n|---|---|---|---|\n"
            "| regex (as shipped) | a phrase list per topic (described, not done: the baseline stays unchanged) | "
            "no | no |\n"
            f"| Jev | {c['added_definitions']} new questions, {c['added_words']} words | none at 0.5; ~1,000 labelled "
            "week 1 questions to tune thresholds | no |\n"
            f"| GLiNER base, zero-shot | {g['added_definitions']} new label descriptions, {g['added_words']} words | "
            "none at 0.5; ~1,000 labelled week 1 questions to tune thresholds | no |\n"
            "| GLiNER fine-tune (measured later: docs/2026-11-04-finetune.md) | new labelled data and a "
            "retrain: 1,344 records, about 17 min per seed on a 1080 Ti | yes | yes |\n")


if __name__ == "__main__":
    main()
