"""How much labelled data does threshold tuning need, and does a local scope gate in front of Jev pay off?

    uv run python -m ppguard.calibration curve    # results/calibration/curve.{json,md,csv}
    uv run python -m ppguard.calibration hybrid   # results/calibration/hybrid.{json,md}

Cached round 2 scores only: no API calls and no GPU. Thresholds are always tuned on week 1 (draws from it, or the v2
fine-tune's week 1 dev set). Week 2 is only scored.

- `curve`: for each size, 200 stratified draws from week 1. Each draw tunes thresholds and scores week 2, for Jev
  and zero-shot GLiNER, under round 2 rules and round 2b (in scope checked before ambiguous; post hoc).
- `hybrid`: the v2 fine-tune's scope score decides "irrelevant" locally below a cut; everything else goes to Jev's
  round 2 decision.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .combine import Thresholds, decide
from .definitions import ROUND2
from .labels import Decision, Row
from .metrics import summary
from .tune import tune_thresholds

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "calibration"
SIZES, DRAWS, SEED = (50, 100, 200, 400, 800), 200, 42
METRICS = ("accuracy", "macro_f1", "in_scope_answered", "in_scope_refused", "not_allowed_recall", "ambiguous_recall")
CACHES = {"jev": "results/cache/jev/round2.jsonl", "gliner": "results/cache/gliner/round2.jsonl"}
FT_PICKS = ("ft_s42_best", "ft_s43_final", "ft_s44_best")  # the checkpoints the v2 report chose (dev macro-F1)
CUTS = tuple(round(0.1 * k, 1) for k in range(1, 10))


# ── shared pieces ────────────────────────────────────────────────────────────

def load_scores(path: Path) -> dict[str, dict[str, float]]:
    return {json.loads(l)["id"]: json.loads(l)["scores"] for l in path.read_text().splitlines()}


def metrics(rows: list[Row], dec: dict[str, Decision]) -> dict[str, float | None]:
    s = summary(rows, dec, n_boot=1)
    return {"accuracy": s["accuracy"], "macro_f1": s["macro_f1"], "in_scope_answered": s["recall"]["in_scope"],
            "in_scope_refused": s["false_refusal"], "not_allowed_recall": s["recall"]["not_allowed"],
            "ambiguous_recall": s["recall"]["ambiguous"]}


def evaluate(scores: dict[str, dict], tune_rows: list[Row] | None, test_rows: list[Row], scope_first: bool,
             t: Thresholds | None = None) -> dict[str, float | None]:
    """Tune on `tune_rows` (week 1; None means the untuned 0.5 cuts) unless `t` is given, then score `test_rows`."""
    if t is None:
        t = tune_thresholds(tune_rows, {r.id: scores[r.id] for r in tune_rows}, ROUND2) if tune_rows else {}
    return metrics(test_rows, {r.id: decide(scores[r.id], ROUND2, t, False, scope_first) for r in test_rows})


# ── calibration curve ────────────────────────────────────────────────────────

def stratified_draw(pool: list[Row], size: int, rng: np.random.Generator) -> list[Row]:
    """`size` rows without replacement, keeping the pool's label mix (largest remainder). Every label with rows gets
    at least one, taken from the largest quota."""
    groups: dict[str, list[Row]] = defaultdict(list)
    for r in sorted(pool, key=lambda r: r.id):
        groups[r.label].append(r)
    labels = sorted(groups)
    exact = {lab: size * len(groups[lab]) / len(pool) for lab in labels}
    quota = {lab: int(exact[lab]) for lab in labels}
    for lab in sorted(labels, key=lambda l: exact[l] - quota[l], reverse=True)[:size - sum(quota.values())]:
        quota[lab] += 1
    for lab in labels:
        if quota[lab] == 0 and size >= len(labels):
            quota[max(labels, key=quota.get)] -= 1
            quota[lab] = 1
    out = []
    for lab in labels:
        idx = rng.choice(len(groups[lab]), size=min(quota[lab], len(groups[lab])), replace=False)
        out += [groups[lab][i] for i in sorted(idx)]
    return out


def summarize(values: list[float], baseline: float | None = None) -> dict[str, float]:
    v = np.asarray(values, float)
    p5, q25, med, q75, p95 = np.percentile(v, [5, 25, 50, 75, 95])
    out = {"median": float(med), "q25": float(q25), "q75": float(q75), "p5": float(p5), "p95": float(p95)}
    if baseline is not None:
        out["share_beats_baseline"] = float(np.mean(v > baseline))
    return out


def _sanity(res: dict) -> list[str]:
    """Full-pool and 0.5 points must reproduce the main report exactly (results/report_round2.json)."""
    main = json.loads((ROOT / "results/report_round2.json").read_text())["week2"]
    expected = {("jev", "r2", "full"): "jev-r2-tuned", ("gliner", "r2", "full"): "gliner-r2-tuned",
                ("jev", "r2", "baseline"): "jev-r2@0.5", ("gliner", "r2", "baseline"): "gliner-r2@0.5",
                ("jev", "r2b", "full"): "jev-r2b-tuned", ("gliner", "r2b", "full"): "gliner-r2b-tuned",
                ("jev", "r2b", "baseline"): "jev-r2b@0.5", ("gliner", "r2b", "baseline"): "gliner-r2b@0.5"}
    lines, bad = [], []
    for (model, rule, point), name in expected.items():
        got = res[model][rule][point]
        ok = got["accuracy"] == main[name]["accuracy"] and got["macro_f1"] == main[name]["macro_f1"]
        line = (f"{'ok  ' if ok else 'FAIL'} {model} {rule} {point}: accuracy {got['accuracy']:.1%}, macro-F1 "
                f"{got['macro_f1']:.1%} (main report {name}: {main[name]['accuracy']:.1%}, {main[name]['macro_f1']:.1%})")
        lines.append(line)
        if not ok:
            bad.append(line)
    if bad:
        raise SystemExit("sanity checks failed:\n" + "\n".join(bad))
    return lines


def curve() -> dict:
    from .build import TESTSET, _read_rows
    rows = _read_rows(TESTSET)
    pool, test = [r for r in rows if r.week == 1], [r for r in rows if r.week == 2]
    scores = {m: load_scores(ROOT / p) for m, p in CACHES.items()}
    rules = {"r2": False, "r2b": True}
    res: dict = {m: {rule: {"draws": {}} for rule in rules} for m in scores}
    for m, sc in scores.items():
        t_full = tune_thresholds(pool, {r.id: sc[r.id] for r in pool}, ROUND2)
        for rule, sf in rules.items():
            res[m][rule]["baseline"] = evaluate(sc, None, test, sf)
            res[m][rule]["full"] = evaluate(sc, None, test, sf, t=t_full)
    rng = np.random.default_rng(SEED)
    for size in SIZES:
        for m in scores:
            for rule in rules:
                res[m][rule]["draws"][size] = []
        for _ in range(DRAWS):
            draw = stratified_draw(pool, size, rng)  # the same draw tunes both models
            for m, sc in scores.items():
                t = tune_thresholds(draw, {r.id: sc[r.id] for r in draw}, ROUND2)
                for rule, sf in rules.items():
                    res[m][rule]["draws"][size].append(evaluate(sc, None, test, sf, t=t))
    for m in scores:
        for rule in rules:
            base = res[m][rule]["baseline"]
            res[m][rule]["summary"] = {
                size: {k: summarize([d[k] for d in draws if d[k] is not None],
                                    base[k] if k == "macro_f1" else None) for k in METRICS}
                for size, draws in res[m][rule]["draws"].items()}
    res["sanity"] = _sanity(res)
    res["meta"] = {"pool": len(pool), "test": len(test), "sizes": SIZES, "draws": DRAWS, "seed": SEED,
                   "pool_label_mix": {lab: sum(r.label == lab for r in pool) for lab in sorted({r.label for r in pool})}}
    return res


def _pct(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}%"


def curve_markdown(res: dict) -> str:
    names = {"jev": "Jev", "gliner": "GLiNER zero-shot"}
    rules = {"r2": "round 2", "r2b": "round 2b (in scope before ambiguous; post hoc)"}
    out = ["# How many labelled questions does threshold tuning need?", "",
           f"Thresholds tuned on stratified draws from week 1 ({res['meta']['pool']} questions, label mix "
           f"{res['meta']['pool_label_mix']}); {res['meta']['draws']} draws per size, numpy seed {res['meta']['seed']}. "
           f"Every draw is scored on week 2 ({res['meta']['test']} questions). Cells: median, IQR in brackets, 5th–95th "
           "percentile in parentheses.", "", "Sanity checks (must reproduce the main report):", ""]
    out += [f"- {line}" for line in res["sanity"]]
    for m in ("jev", "gliner"):
        for rule in ("r2", "r2b"):
            r = res[m][rule]
            out += ["", f"## {names[m]}, {rules[rule]}", "",
                    "| tuned on | macro-F1 | beats 0.5 (macro-F1) | accuracy | in-scope answered | in-scope refused | "
                    "not-allowed caught | ambiguous caught |", "|---|---|---|---|---|---|---|---|"]
            for size in SIZES:
                s = r["summary"][size]
                f = s["macro_f1"]
                out.append(f"| {size} | {_pct(f['median'])} [{_pct(f['q25'])}–{_pct(f['q75'])}] "
                           f"({_pct(f['p5'])}–{_pct(f['p95'])}) | {f['share_beats_baseline']:.0%} | "
                           f"{_pct(s['accuracy']['median'])} ({_pct(s['accuracy']['p5'])}–{_pct(s['accuracy']['p95'])}) | "
                           + " | ".join(_pct(s[k]["median"]) for k in METRICS[2:]) + " |")
            for label, point in (("all 1,036", r["full"]), ("untuned 0.5", r["baseline"])):
                out.append(f"| {label} | {_pct(point['macro_f1'])} | – | {_pct(point['accuracy'])} | "
                           + " | ".join(_pct(point[k]) for k in METRICS[2:]) + " |")
    return "\n".join(out) + "\n"


def curve_csv(res: dict, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "rule", "size", "metric", "median", "q25", "q75", "p5", "p95", "share_beats_baseline",
                    "baseline_0.5", "full_pool"])
        for m in ("jev", "gliner"):
            for rule in ("r2", "r2b"):
                r = res[m][rule]
                for size in SIZES:
                    for k in METRICS:
                        s = r["summary"][size][k]
                        w.writerow([m, rule, size, k, s["median"], s["q25"], s["q75"], s["p5"], s["p95"],
                                    s.get("share_beats_baseline", ""), r["baseline"][k], r["full"][k]])


SERIES = {"jev": ("Jev", "#2a78d6"), "gliner": ("GLiNER zero-shot", "#eb6834")}  # validated categorical slots 1–2
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def curve_chart(res: dict, path: Path) -> None:
    """Macro-F1 vs tuning-set size: median line, 5th–95th percentile band, untuned 0.5 as a dashed line, and the
    full-week-1 point as a hollow marker. One panel per decision rule, shared y axis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True, facecolor=SURFACE)
    panels = (("r2", "Round 2 rules"), ("r2b", "Round 2b rules (in scope before ambiguous; post hoc)"))
    for ax, (rule, title) in zip(axes, panels):
        ax.set_facecolor(SURFACE)
        for m, (label, color) in SERIES.items():
            s = res[m][rule]["summary"]
            med = [s[size]["macro_f1"]["median"] for size in SIZES]
            ax.fill_between(SIZES, [s[size]["macro_f1"]["p5"] for size in SIZES],
                            [s[size]["macro_f1"]["p95"] for size in SIZES], color=color, alpha=0.14, linewidth=0)
            ax.plot(SIZES, med, color=color, linewidth=2, marker="o", markersize=6, label=f"{label}: median",
                    markeredgecolor=SURFACE, markeredgewidth=1.5)
            base = res[m][rule]["baseline"]["macro_f1"]
            ax.axhline(base, color=color, linewidth=1.5, linestyle=(0, (5, 4)), label=f"{label}: untuned 0.5")
            ax.plot([1036], [res[m][rule]["full"]["macro_f1"]], marker="o", markersize=8, color=SURFACE, zorder=4,
                    markeredgecolor=color, markeredgewidth=2, linestyle="none")
            full = res[m][rule]["full"]["macro_f1"]
            ax.annotate(label, (1036, full), xytext=(10, 0), textcoords="offset points", va="center", fontsize=9,
                        color=INK, bbox=dict(boxstyle="square,pad=0.15", facecolor=SURFACE, edgecolor="none"))
        ax.set_xscale("log")
        ax.set_xticks(list(SIZES) + [1036])
        ax.set_xticklabels([str(x) for x in SIZES] + ["all\n1,036"], fontsize=9, color=INK_2)
        ax.minorticks_off()
        ax.set_xlim(40, 3400)
        ax.set_ylim(0, 0.72)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
        ax.tick_params(colors=INK_2, labelsize=9, length=0)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.set_title(title, fontsize=10.5, color=INK, loc="left")
        ax.set_xlabel("labelled week 1 questions used to tune thresholds (log scale)", fontsize=9, color=INK_2)
    axes[0].set_ylabel("week 2 macro-F1", fontsize=9, color=INK_2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=8.5, labelcolor=INK,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("How many labelled questions does threshold tuning need?", x=0.06, ha="left", fontsize=12.5,
                 color=INK, y=0.975)
    fig.text(0.06, 0.885, "Median of 200 stratified draws per size, band = 5th–95th percentile; hollow marker = tuned "
             "on all of week 1; dashed = untuned 0.5 cuts", fontsize=9, color=INK_2)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.80, bottom=0.24, wspace=0.08)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


# ── hybrid: local scope gate, then Jev ────────────────────────────────────────

def hybrid_decide(local_in_scope: float, cut: float, jev_scores: dict[str, float], t: Thresholds) -> tuple[Decision, bool]:
    """(decision, sent to Jev). Below the cut the local model calls it irrelevant and Jev never sees it."""
    if local_in_scope < cut:
        return Decision("irrelevant"), False
    return decide(jev_scores, ROUND2, t, False), True


def hybrid_outcomes(rows: list[Row], local: dict[str, float], jev: dict[str, dict], cut: float,
                    t: Thresholds) -> dict:
    dec, sent = {}, {}
    for r in rows:
        dec[r.id], sent[r.id] = hybrid_decide(local[r.id], cut, jev[r.id], t)
    by_topic: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.label != "not_allowed":
            continue
        c = by_topic.setdefault(r.topic, {"n": 0, "caught_by_jev": 0, "local_irrelevant": 0, "answered": 0, "other": 0})
        c["n"] += 1
        if not sent[r.id]:
            c["local_irrelevant"] += 1
        elif dec[r.id].label == "not_allowed":
            c["caught_by_jev"] += 1
        elif dec[r.id].label == "in_scope":
            c["answered"] += 1
        else:
            c["other"] += 1  # Jev said irrelevant or ambiguous: not answered, topic not logged
    return {"metrics": metrics(rows, dec), "sent_to_jev": sum(sent.values()) / len(rows), "not_allowed": by_topic}


def choose_cut(dev_rows: list[Row], local: dict[str, float], jev: dict[str, dict], t: Thresholds,
               cuts=CUTS) -> tuple[float, float]:
    """The cut with the highest dev macro-F1; on ties the lower cut (more questions reach Jev)."""
    best = None
    for c in sorted(cuts):
        f1 = hybrid_outcomes(dev_rows, local, jev, c, t)["metrics"]["macro_f1"]
        if best is None or f1 > best[1]:
            best = (c, f1)
    return best


def hybrid() -> dict:
    from .build import TESTSET, _read_rows
    from .finetune import paths
    rows = _read_rows(TESTSET)
    w2 = [r for r in rows if r.week == 2]
    data_v2, results_v2 = paths(2)
    dev_ids = set(json.loads((data_v2 / "split.json").read_text())["dev"])
    dev = [r for r in rows if r.id in dev_ids]
    jev = load_scores(ROOT / CACHES["jev"])
    settings = {"0.5": {}, "week 1 thresholds": json.loads((ROOT / "results/thresholds_round2.json").read_text())["jev"]}
    res: dict = {"jev_alone": {}, "seeds": {}, "meta": {"dev": len(dev), "test": len(w2), "cuts": CUTS}}
    for name, t in settings.items():
        res["jev_alone"][name] = hybrid_outcomes(w2, {r.id: 1.0 for r in w2}, jev, float("-inf"), t)
    for tag in FT_PICKS:
        local = {json.loads(l)["id"]: json.loads(l)["scope"]["in_scope"]
                 for l in (results_v2 / f"tasks_{tag}.jsonl").read_text().splitlines()}
        res["seeds"][tag] = {}
        for name, t in settings.items():
            cut, dev_f1 = choose_cut(dev, local, jev, t)
            res["seeds"][tag][name] = {
                "chosen_cut": cut, "dev_macro_f1": dev_f1,
                "chosen": hybrid_outcomes(w2, local, jev, cut, t),
                "sweep": {c: hybrid_outcomes(w2, local, jev, c, t) for c in CUTS}}
    return res


def _na_line(label: str, out: dict) -> str:
    tot = defaultdict(int)
    for c in out["not_allowed"].values():
        for k, v in c.items():
            tot[k] += v
    return (f"| {label} | {tot['n']} | {tot['caught_by_jev']} | {tot['local_irrelevant']} | {tot['answered']} | "
            f"{tot['other']} |")


def hybrid_markdown(res: dict) -> str:
    out = ["# Hybrid: local scope gate first, Jev only for what it passes (week 2)", "",
           f"Local gate: the v2 fine-tune's scope score ({', '.join(FT_PICKS)}). Below the cut, the question is called "
           "irrelevant locally and never sent to Jev. Otherwise Jev's round 2 decision stands. The cut quoted per seed "
           f"is chosen on the v2 dev set ({res['meta']['dev']} week 1 questions) by hybrid macro-F1; the sweep is shown "
           "for reference only. Jev's 'week 1 thresholds' were tuned on all of week 1, which includes the dev set.", ""]
    for name in ("0.5", "week 1 thresholds"):
        out += [f"## Jev at {name}", "",
                "| setup | cut | accuracy | macro-F1 | in-scope answered | sent to Jev |", "|---|---|---|---|---|---|"]
        a = res["jev_alone"][name]
        out.append(f"| Jev alone | – | {_pct(a['metrics']['accuracy'])} | {_pct(a['metrics']['macro_f1'])} | "
                   f"{_pct(a['metrics']['in_scope_answered'])} | 100.0% |")
        for tag, by in res["seeds"].items():
            h = by[name]["chosen"]
            out.append(f"| hybrid, {tag} | {by[name]['chosen_cut']} (dev macro-F1 {_pct(by[name]['dev_macro_f1'])}) | "
                       f"{_pct(h['metrics']['accuracy'])} | {_pct(h['metrics']['macro_f1'])} | "
                       f"{_pct(h['metrics']['in_scope_answered'])} | {_pct(h['sent_to_jev'])} |")
        out += ["", "Not-allowed questions (all topics): what happened to them.", "",
                "| setup | n | caught by Jev | called irrelevant locally (not answered, topic not logged) | "
                "**answered** | other (Jev: irrelevant or ambiguous) |", "|---|---|---|---|---|---|"]
        out.append(_na_line("Jev alone", a))
        for tag, by in res["seeds"].items():
            out.append(_na_line(f"hybrid, {tag} (cut {by[name]['chosen_cut']})", by[name]["chosen"]))
        topics = sorted(a["not_allowed"])
        out += ["", "By topic: caught by Jev / local irrelevant / answered (hybrid at the chosen cut).", "",
                "| setup | " + " | ".join(topics) + " |", "|---|" + "---|" * len(topics)]
        out.append("| Jev alone | " + " | ".join(
            f"{a['not_allowed'][t]['caught_by_jev']} / – / {a['not_allowed'][t]['answered']}" for t in topics) + " |")
        for tag, by in res["seeds"].items():
            h = by[name]["chosen"]["not_allowed"]
            out.append(f"| {tag} | " + " | ".join(
                f"{h[t]['caught_by_jev']} / {h[t]['local_irrelevant']} / {h[t]['answered']}" for t in topics) + " |")
        out += ["", "Sweep (week 2, for reference; not used to pick anything): macro-F1 / sent to Jev / not-allowed answered.",
                "", "| seed | " + " | ".join(str(c) for c in CUTS) + " |", "|---|" + "---|" * len(CUTS)]
        for tag, by in res["seeds"].items():
            cells = []
            for c in CUTS:
                h = by[name]["sweep"][c]
                answered = sum(v["answered"] for v in h["not_allowed"].values())
                cells.append(f"{_pct(h['metrics']['macro_f1'])} / {_pct(h['sent_to_jev'])} / {answered}")
            out.append(f"| {tag} | " + " | ".join(cells) + " |")
        out.append("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m ppguard.calibration")
    ap.add_argument("step", choices=["curve", "hybrid"])
    step = ap.parse_args(argv).step
    RESULTS.mkdir(parents=True, exist_ok=True)
    if step == "curve":
        res = curve()
        (RESULTS / "curve.json").write_text(json.dumps(res, indent=1, default=str))
        (RESULTS / "curve.md").write_text(curve_markdown(res))
        curve_csv(res, RESULTS / "curve.csv")
        curve_chart(res, RESULTS / "curve.png")
        print("\n".join(res["sanity"]))
        print(f"wrote {RESULTS / 'curve.md'}, curve.json, curve.csv, curve.png")
    else:
        res = hybrid()
        (RESULTS / "hybrid.json").write_text(json.dumps(res, indent=1, default=str))
        (RESULTS / "hybrid.md").write_text(hybrid_markdown(res))
        print(f"wrote {RESULTS / 'hybrid.md'}, hybrid.json")


if __name__ == "__main__":
    main()
