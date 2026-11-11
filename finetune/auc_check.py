"""Threshold-free check of the GLiNER fine-tune: does it rank correctly even though 0.5 is the wrong cut-off?

Week 2 only (never trained or tuned on). Reads the saved scores in results/finetune/ and results/cache/jev/.
Run: python3 finetune/auc_check.py   (needs numpy only; writes results/finetune/auc_check.md)
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ["legal", "medical", "investment", "prompt_attack", "privacy", "harmful"]


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def auc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    s = np.concatenate([pos, neg])
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    avg = np.cumsum(counts) - (counts - 1) / 2
    ranks = avg[inv]
    u = ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2
    return u / (len(pos) * len(neg))


def tpr_at_fpr(pos, neg, fpr=0.05):
    thr = np.quantile(np.asarray(neg, float), 1 - fpr)
    return float((np.asarray(pos, float) > thr).mean())


def ft_scores(rec):
    s = dict(rec["topic"]); s["in_scope"] = rec["scope"]["in_scope"]; s["ambiguous"] = rec["clarity"]["ambiguous"]
    return s


test = {r["id"]: r for r in load_jsonl(ROOT / "data/testset.jsonl") if r["week"] == 2}
models = {}
for name, f in [("gliner zero-shot", "results/finetune/tasks_base.jsonl"),
                ("ft seed 42", "results/finetune/tasks_ft_s42.jsonl"),
                ("ft seed 43", "results/finetune/tasks_ft_s43.jsonl"),
                ("ft seed 44", "results/finetune/tasks_ft_s44.jsonl")]:
    models[name] = {r["id"]: ft_scores(r) for r in load_jsonl(ROOT / f)}
models["jev round 2 (ref)"] = {r["id"]: r["scores"] for r in load_jsonl(ROOT / "results/cache/jev/round2.jsonl")}

ids = sorted(test)
for n, m in models.items():
    missing = [i for i in ids if i not in m]
    assert not missing, f"{n}: {len(missing)} week 2 ids missing"
label = np.array([test[i]["label"] for i in ids])
topic = np.array([test[i]["topic"] or "" for i in ids])
print(f"week 2 rows: {len(ids)}  " + "  ".join(f"{l}={int((label == l).sum())}" for l in
      ["in_scope", "irrelevant", "not_allowed", "ambiguous"]))


def col(m, key):
    return np.array([m[i][key] for i in ids])


def maxtopic(m):
    return np.array([max(m[i][t] for t in TOPICS) for i in ids])


rng = np.random.default_rng(42)
rows = {}
for n, m in models.items():
    mx = maxtopic(m)
    na, rest = label == "not_allowed", label != "not_allowed"
    r = {}
    r["A"] = auc(mx[na], mx[rest])
    boots = []
    for _ in range(500):
        b = rng.integers(0, len(ids), len(ids))
        boots.append(auc(mx[b][na[b]], mx[b][rest[b]]))
    r["A_ci"] = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))
    r["B"] = auc(mx[na], mx[label == "in_scope"])
    r["tpr5"] = tpr_at_fpr(mx[na], mx[rest])
    r["med_pos"], r["med_neg"] = float(np.median(mx[na])), float(np.median(mx[rest]))
    r["gt05"] = float((mx[na] > 0.5).mean())
    for t in TOPICS:
        r[t] = auc(col(m, t)[(label == "not_allowed") & (topic == t)], col(m, t)[rest])
    sc = col(m, "in_scope")
    r["D"] = auc(sc[label == "in_scope"], sc[label == "irrelevant"])
    am = col(m, "ambiguous")
    r["E"] = auc(am[label == "ambiguous"], am[label != "ambiguous"])
    rows[n] = r

names = list(rows)
ft = [n for n in names if n.startswith("ft")]
L = []
L.append("# AUC check: ranking quality of the fine-tune, week 2 (threshold-free)\n")
L.append("AUC = chance a random positive outscores a random negative (0.5 = chance, 1.0 = perfect). "
         "Week 2 only, 1,055 questions. Script: `finetune/auc_check.py`.\n")
L.append("## Not-allowed detection (score = highest of the six topic scores)\n")
L.append("| model | AUC vs all others (95% CI) | AUC vs in-scope only | TPR at 5% FPR | median score: not-allowed / others | not-allowed above 0.5 |")
L.append("|---|---|---|---|---|---|")
for n in names:
    r = rows[n]
    L.append(f"| {n} | {r['A']:.3f} ({r['A_ci'][0]:.3f}–{r['A_ci'][1]:.3f}) | {r['B']:.3f} | {r['tpr5']:.1%} | "
             f"{r['med_pos']:.2g} / {r['med_neg']:.2g} | {r['gt05']:.1%} |")
L.append("\n## Per topic (AUC of that topic's score; positives = that topic, negatives = every question that is not 'not allowed')\n")
L.append("| model | " + " | ".join(TOPICS) + " |")
L.append("|---|" + "---|" * len(TOPICS))
for n in names:
    L.append(f"| {n} | " + " | ".join(f"{rows[n][t]:.3f}" for t in TOPICS) + " |")
L.append("\n## The other two decisions\n")
L.append("| model | in scope vs irrelevant (AUC) | ambiguous vs rest (AUC) |")
L.append("|---|---|---|")
for n in names:
    L.append(f"| {n} | {rows[n]['D']:.3f} | {rows[n]['E']:.3f} |")
out = "\n".join(L) + "\n"
(ROOT / "results/finetune/auc_check.md").write_text(out)
print(out)
