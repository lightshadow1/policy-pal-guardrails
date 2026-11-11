"""GLiNER fine-tune on the four labels: training data out, scores back in, evaluation on week 2.

    uv run python -m ppguard.finetune build --version 2      # data/finetune_v2/: train, dev, schema, texts, split
    (train and score on the GPU box with finetune/run_all.sh, see docs/2026-11-04-finetune.md)
    uv run python -m ppguard.finetune evaluate --version 2   # results/finetune_v2/report.md from tasks_<tag>.jsonl

Version 1 (2026-11-04, kept reproducible): week 1 85% + the generated questions; held-out 15% of week 1 as dev;
all three tasks multi-label. Its topic part collapsed to near-zero scores (docs/2026-11-04-finetune.md).
Version 2 fixes the recipe:
- `topic` and `clarity` are single-choice, and `topic` has an explicit "none" label, so the model has to choose;
- not_allowed rows are oversampled ×2 and ambiguous rows ×3;
- dev is 25% of week 1;
- week 1 rows sharing 60% or more of their words with a week 2 question are dropped from train and dev;
- each seed's checkpoint (best dev loss vs final) is chosen by dev macro-F1.
Week 2 stays the test throughout. Texts are PII-scrubbed, as every guardrail sees them.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from .definitions import CLEAR, IRRELEVANT, ROUND2, Definitions
from .labels import Row, normalize

ROOT = Path(__file__).resolve().parent.parent
GENERATED = ("seed_questions", "hard_batch2", "messy_batch3")
NONE = "none of these: an ordinary question or request that asks for none of the above"
VERSIONS = {
    1: dict(dev_frac=0.15, single=False, oversample={}, drop_near_dups=False),
    2: dict(dev_frac=0.25, single=True, oversample={"not_allowed": 2, "ambiguous": 3}, drop_near_dups=True),
}


def paths(version: int) -> tuple[Path, Path]:
    suffix = "" if version == 1 else f"_v{version}"
    return ROOT / "data" / f"finetune{suffix}", ROOT / "results" / f"finetune{suffix}"


def ft_schema(d: Definitions, single: bool = False) -> dict:
    topic_labels = dict(d.topics) | ({"none": NONE} if single else {})
    return {
        "topic": {"labels": topic_labels, "multi_label": not single, "cls_threshold": 0.0},
        "scope": {"labels": {"in_scope": d.in_scope, "irrelevant": IRRELEVANT}, "multi_label": True,
                  "cls_threshold": 0.0},
        "clarity": {"labels": {"ambiguous": d.ambiguous, "clear": CLEAR}, "multi_label": not single,
                    "cls_threshold": 0.0},
    }


def to_record(text: str, label: str, topic: str | None, d: Definitions, single: bool = False) -> dict:
    """One gliner2 training example. `scope` is only taught where it's defined (in scope vs irrelevant)."""
    s = ft_schema(d, single)

    def task(name: str, true: list[str]) -> dict:
        labels = s[name]["labels"]
        return {"task": name, "labels": list(labels), "true_label": true, "multi_label": s[name]["multi_label"],
                "label_descriptions": dict(labels)}

    no_topic = ["none"] if single else []
    out = [task("topic", [topic] if label == "not_allowed" else no_topic),
           task("clarity", ["ambiguous" if label == "ambiguous" else "clear"])]
    if label in ("in_scope", "irrelevant"):
        out.append(task("scope", [label]))
    return {"input": text, "output": {"classifications": out}}


def split_week1(rows: list[Row], frac: float = 0.15, seed: int = 42) -> tuple[set[str], set[str]]:
    strata: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if r.week == 1:
            strata[f"{r.source}|{r.label}"].append(r.id)
    train, dev = set(), set()
    for key, ids in strata.items():
        ids = sorted(ids)
        random.Random(f"{seed}:{key}").shuffle(ids)
        k = round(len(ids) * frac)
        dev |= set(ids[:k])
        train |= set(ids[k:])
    return train, dev


def _toks(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def near_duplicate_ids(rows: list[Row], test: list[Row], cut: float = 0.6) -> set[str]:
    """Ids of `rows` sharing at least `cut` of their words (token Jaccard) with any `test` row."""
    test_toks = [t for t in (_toks(r.text) for r in test) if t]
    out = set()
    for r in rows:
        a = _toks(r.text)
        if a and any(len(a & b) / len(a | b) >= cut for b in test_toks):
            out.add(r.id)
    return out


def oversample(rows: list[Row], factors: dict[str, int]) -> list[Row]:
    return [r for r in rows for _ in range(factors.get(r.label, 1))]


def parse_scores(rec: dict, topics: list[str] | None = None) -> dict[str, float]:
    """Score names from predict_tasks output. Single-choice tasks return only the chosen label's confidence: a topic
    that wasn't chosen scores 0, and p(ambiguous) is 1 - confidence when "clear" was chosen."""
    topic_out = rec["topic"]
    names = topics if topics is not None else [k for k in topic_out if k != "none"]
    scores = {t: float(topic_out.get(t, 0.0)) for t in names}
    scores["in_scope"] = rec["scope"]["in_scope"]
    clarity = rec["clarity"]
    scores["ambiguous"] = clarity["ambiguous"] if "ambiguous" in clarity else 1.0 - clarity["clear"]
    return scores


def _generated() -> list[Row]:
    rows = []
    for f in GENERATED:
        for line in (ROOT / "data" / "train" / f"{f}.jsonl").read_text().splitlines():
            q = json.loads(line)
            rows.append(Row(id=q["id"], text=q["text"], source=f"gen:{f}", licence="generated", label=q["label"],
                            topic=q["topic"], covered=q["covered"]))
    return rows


def build(version: int = 1, seed: int = 42) -> None:
    from .build import TESTSET, _read_rows
    from .regex_guard import scrub_text
    cfg = VERSIONS[version]
    data_dir, _ = paths(version)
    rows, gen = _read_rows(TESTSET), _generated()
    week2 = [r for r in rows if r.week == 2]
    train_ids, dev_ids = split_week1(rows, frac=cfg["dev_frac"], seed=seed)
    dropped: set[str] = set()
    if cfg["drop_near_dups"]:
        dropped = near_duplicate_ids([r for r in rows if r.week == 1], week2)
        train_ids, dev_ids = train_ids - dropped, dev_ids - dropped
    week2_texts = {normalize(scrub_text(r.text)) for r in week2}
    train_rows = [r for r in rows if r.id in train_ids] + gen
    leaks = [r.id for r in train_rows if normalize(scrub_text(r.text)) in week2_texts]
    if leaks:
        raise SystemExit(f"training text identical to a week 2 text: {leaks[:5]}")
    train_rows = oversample(train_rows, cfg["oversample"])
    single = cfg["single"]
    train = [to_record(scrub_text(r.text), r.label, r.topic, ROUND2, single) for r in train_rows]
    random.Random(seed).shuffle(train)
    dev = [to_record(scrub_text(r.text), r.label, r.topic, ROUND2, single) for r in rows if r.id in dev_ids]
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, recs in (("train.jsonl", train), ("dev.jsonl", dev)):
        (data_dir / name).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs))
    (data_dir / "schema.json").write_text(json.dumps(ft_schema(ROUND2, single), indent=1))
    texts = [{"id": r.id, "text": scrub_text(r.text)} for r in rows + gen]
    (data_dir / "texts.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in texts))
    (data_dir / "split.json").write_text(json.dumps({"train": sorted(train_ids), "dev": sorted(dev_ids),
                                                     "dropped_near_dups": sorted(dropped)}))
    print(f"v{version}: train {len(train)} records ({len(train_ids)} week 1 + {len(gen)} generated, before oversampling), "
          f"dev {len(dev)} (week 1), dropped {len(dropped)} week 1 near-duplicates of week 2, texts {len(texts)}")


def evaluate(version: int = 1) -> None:
    import numpy as np

    from .build import TESTSET, _read_rows
    from .metrics import summary
    from .report import decisions
    from .tune import tune_thresholds
    data_dir, results = paths(version)
    rows = _read_rows(TESTSET)
    dev_ids = set(json.loads((data_dir / "split.json").read_text())["dev"])
    dev = [r for r in rows if r.id in dev_ids]
    w2 = [r for r in rows if r.week == 2]
    topics = list(ROUND2.topics)
    loaded = {path.stem.removeprefix("tasks_"): {json.loads(l)["id"]: {"scores": parse_scores(json.loads(l), topics)}
                                                  for l in path.read_text().splitlines()}
              for path in sorted(results.glob("tasks_*.jsonl"))}
    # one run per seed: of its checkpoints (ft_s42_best, ft_s42_final, ...), keep the higher dev macro-F1 at 0.5
    runs: dict[str, dict] = {}
    picks = []
    for tag, cache in loaded.items():
        if not tag.startswith("ft_") or tag.count("_") < 2:
            runs[f"gliner-{tag}"] = cache
            continue
        seed = tag.rsplit("_", 1)[0]
        f1 = summary(dev, decisions("gliner", ROUND2, dev, cache, {}, False), 200)["macro_f1"]
        if seed not in {p[0] for p in picks} or f1 > next(p for p in picks if p[0] == seed)[2]:
            picks = [p for p in picks if p[0] != seed] + [(seed, tag, f1)]
    for seed, tag, f1 in sorted(picks):
        runs[f"gliner-{tag}"] = loaded[tag]
    for name, path in (("jev-r2", "results/cache/jev/round2.jsonl"),
                       ("gliner-zeroshot (served schema)", "results/cache/gliner/round2.jsonl")):
        runs[name] = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / path).read_text().splitlines()}
    table = {}
    for name, cache in runs.items():
        tuned = tune_thresholds(dev, {r.id: cache[r.id]["scores"] for r in dev}, ROUND2)
        for regime, t in (("0.5", {}), ("dev-tuned", tuned)):
            table[(name, regime)] = summary(w2, decisions("gliner", ROUND2, w2, cache, t, False), 2000)
    lines = [f"# GLiNER fine-tune v{version} vs base and Jev (week 2)", "",
             f"Week 2: {len(w2)} questions. Thresholds either 0.5 (no labelled data) or tuned on the held-out dev set: "
             f"{len(dev)} week 1 questions, {sum(r.label == 'ambiguous' for r in dev)} of them ambiguous. Accuracy alone "
             "misleads here: a model that never refuses still scores high on week 2's mix, so read macro-F1 and the "
             "not-allowed column."]
    if picks:
        lines += ["", "Checkpoint per seed, chosen by dev macro-F1 at 0.5: " +
                  ", ".join(f"{tag} ({f1:.1%})" for _, tag, f1 in sorted(picks)) + "."]
    lines += ["", "| model | thresholds | accuracy (95% CI) | macro-F1 | in-scope answered | in-scope refused | irrelevant | "
              "not allowed | ambiguous |", "|---|---|---|---|---|---|---|---|---|"]
    for (name, regime), s in table.items():
        lo, hi = s["accuracy_ci"]
        rc = s["recall"]
        lines.append(f"| {name} | {regime} | {s['accuracy']:.1%} ({lo:.1%}–{hi:.1%}) | {s['macro_f1']:.1%} | "
                     f"{rc['in_scope']:.1%} | {s['false_refusal']:.1%} | {rc['irrelevant']:.1%} | "
                     f"{rc['not_allowed']:.1%} | {rc['ambiguous']:.1%} |")
    for regime in ("0.5", "dev-tuned"):
        ft = [s for (n, r), s in table.items() if n.startswith("gliner-ft") and r == regime]
        if ft:
            f1 = [s["macro_f1"] for s in ft]
            lines.append(f"\nFine-tune, {regime}: macro-F1 mean {np.mean(f1):.1%} (range {min(f1):.1%}–{max(f1):.1%}) "
                         f"over {len(ft)} seeds.")
    results.mkdir(parents=True, exist_ok=True)
    (results / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m ppguard.finetune")
    ap.add_argument("step", choices=["build", "evaluate"])
    ap.add_argument("--version", type=int, choices=sorted(VERSIONS), default=1)
    a = ap.parse_args(argv)
    build(a.version) if a.step == "build" else evaluate(a.version)


if __name__ == "__main__":
    main()
