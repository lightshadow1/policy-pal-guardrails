"""Build the test set: dedupe, the label CSV for human review, and the two "weeks of traffic".

    uv run python -m ppguard.build candidates      # load every source, dedupe -> data/candidates.jsonl
    uv run python -m ppguard.build export-labels   # rows needing a human label + 10% spot-check -> data/labels.csv
    uv run python -m ppguard.build assemble        # reviewed labels + week split -> data/testset.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

from .labels import LABELS, TOPICS, Row, normalize

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CANDIDATES, LABELS_CSV, TESTSET = DATA / "candidates.jsonl", DATA / "labels.csv", DATA / "testset.jsonl"

CSV_COLUMNS = ["id", "source", "text", "expected", "spot_check", "draft_label", "draft_topic", "draft_covered",
               "draft_reason", "reviewed", "reviewer", "final_label", "final_topic", "final_covered", "note"]
USER_COLUMNS = ["id", "source", "text", "draft", "reviewer_note", "reviewed", "final_label", "final_topic",
                "final_covered"]
AGENT_REVIEW, FOR_USER = DATA / "review" / "opus_review.csv", DATA / "review" / "for_user.csv"
_TRUE, _FALSE = {"true", "yes", "y", "1"}, {"false", "no", "n", "0"}


def dedupe(rows: list[Row]) -> tuple[list[Row], list[dict]]:
    first: dict[str, Row] = {}
    kept, report = [], []
    for r in rows:
        key = normalize(r.text)
        if key in first:
            k = first[key]
            conflict = k.label is not None and r.label is not None and k.label != r.label
            report.append({"kept": k.id, "dropped": r.id, "conflict": conflict})
        else:
            first[key] = r
            kept.append(r)
    return kept, report


def spot_check_ids(rows: list[Row], frac: float = 0.10, seed: int = 42) -> set[str]:
    by_source: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if not r.needs_review:
            by_source[r.source].append(r.id)
    picked: set[str] = set()
    for source, ids in by_source.items():
        picked |= set(random.Random(f"{seed}:{source}").sample(sorted(ids), round(len(ids) * frac)))
    return picked


def _source_label(r: Row) -> str:
    parts = [r.label or ""]
    if r.topic:
        parts.append(r.topic)
    if r.covered is not None:
        parts.append(f"covered={'yes' if r.covered else 'no'}")
    return "/".join(parts)


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def export_label_csv(rows: list[Row], spot_ids: set[str], path: Path) -> None:
    if path.exists() and any(rec.get(c, "").strip() for rec in _read_csv(path)
                             for c in ("reviewed", "final_label", "final_topic", "final_covered")):
        raise FileExistsError(f"{path} already has review work in it; refusing to overwrite")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            if r.needs_review or r.id in spot_ids:
                w.writerow({"id": r.id, "source": r.source, "text": r.text,
                            "expected": r.note if r.needs_review else _source_label(r),
                            "spot_check": "y" if r.id in spot_ids else "", "note": ""})


def _norm(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _covered(value: str) -> bool | None:
    v = value.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    if v:
        raise ValueError(f"covered must be yes/no, got {value!r}")
    return None


def _resolve(r: Row, rec: dict) -> tuple[str, str | None, bool | None]:
    """The reviewed (label, topic, covered) for one CSV row. Raises ValueError with the reason."""
    if rec.get("final_label", "").strip():
        label, topic, covered = rec["final_label"], rec.get("final_topic", ""), rec.get("final_covered", "")
    else:
        pick = lambda f: rec.get(f"final_{f}", "").strip() or rec.get(f"draft_{f}", "").strip()  # noqa: E731
        label, topic, covered = pick("label"), pick("topic"), pick("covered")
        if not label:
            if r.label is None:
                raise ValueError("no draft or final label")
            if not topic and not covered:
                return r.label, r.topic, r.covered  # spot-check row accepted as the source labelled it
            # a partial correction (topic or covered only) applies on top of the source label
            label = r.label
            topic = topic or (r.topic or "")
            covered = covered or ("" if r.covered is None else ("yes" if r.covered else "no"))
    label, topic, cov = _norm(label), _norm(topic) or None, _covered(covered)
    if label not in LABELS:
        raise ValueError(f"unknown label {label!r}")
    if label == "not_allowed" and topic not in TOPICS:
        raise ValueError(f"not_allowed needs a topic from {TOPICS}, got {topic!r}")
    if label != "not_allowed" and topic:
        raise ValueError(f"topic must be blank for {label}")
    if label == "in_scope" and cov is None:
        raise ValueError("in_scope needs covered yes/no")
    if label != "in_scope" and cov is not None:
        raise ValueError(f"covered must be blank for {label}")
    return label, topic, cov


def apply_labels(rows: list[Row], records: list[dict]) -> list[Row]:
    recs = {}
    for rec in records:
        clean = {k.lstrip("﻿").strip(): (v or "") for k, v in rec.items()}
        recs[clean["id"].strip()] = clean
    errors = [f"{rid}: not reviewed" for rid, rec in recs.items() if rec.get("reviewed", "").strip().lower()
              not in {"y", "yes"}]
    errors += [f"{r.id}: needs review but is missing from the CSV" for r in rows if r.needs_review and r.id not in recs]
    out = []
    for r in rows:
        rec = recs.get(r.id)
        if rec is None:
            out.append(r)
            continue
        try:
            label, topic, covered = _resolve(r, rec)
        except ValueError as e:
            errors.append(f"{r.id}: {e}")
            continue
        rv = rec.get("reviewer", "").strip()
        if r.needs_review:
            draft = (_norm(rec.get("draft_label", "")), _norm(rec.get("draft_topic", "")) or None,
                     _covered(rec.get("draft_covered", "")))
            same = (label, topic, covered) == draft
            by = ("drafted+reviewed" if same else "human") if not rv else \
                (f"drafted+reviewed:{rv}" if same else f"corrected:{rv}")
        else:
            same = (label, topic, covered) == (r.label, r.topic, r.covered)
            by = "source" if same else ("human" if not rv else f"corrected:{rv}")
        out.append(replace(r, label=label, topic=topic, covered=covered, labelled_by=by, needs_review=False))
    if errors:
        raise ValueError("label CSV problems:\n" + "\n".join(errors))
    return out


def apply_agent_review(records: list[dict], review: list[dict], reviewer: str = "opus") -> list[dict]:
    """Apply a reviewer agent's verdicts: agree/change are applied and marked reviewed; unsure rows stay unreviewed
    with the agent's best guess pre-filled in final_* for the user to confirm or change."""
    by_id = {v["id"].strip(): v for v in review}
    missing = [rec["id"] for rec in records if rec["id"] not in by_id]
    if missing:
        raise ValueError(f"{len(missing)} rows have no {reviewer} verdict, e.g. {missing[:5]}")
    out = []
    for rec in records:
        v, rec = by_id[rec["id"]], dict(rec)
        verdict = v["verdict"].strip().lower()
        guess = {"final_label": v["label"].strip(), "final_topic": v["topic"].strip(),
                 "final_covered": v["covered"].strip()}
        if verdict == "agree":
            rec |= {"reviewed": "y", "reviewer": reviewer}
        elif verdict == "change":
            rec |= {"reviewed": "y", "reviewer": reviewer} | guess
        elif verdict == "unsure":
            rec |= {"reviewed": "", "reviewer": ""} | guess
            rec["note"] = f"{reviewer} unsure: {v['reason'].strip()} | alternative: {v['alternative'].strip()}"
        else:
            raise ValueError(f"{rec['id']}: unknown verdict {v['verdict']!r}")
        out.append(rec)
    return out


def apply_user_review(records: list[dict], user_records: list[dict]) -> list[dict]:
    """Merge the user's decisions on the rows the agent was unsure about."""
    decided = {u["id"].strip(): u for u in user_records}
    unreviewed = [i for i, u in decided.items() if u.get("reviewed", "").strip().lower() not in {"y", "yes"}]
    if unreviewed:
        raise ValueError(f"{len(unreviewed)} rows not marked reviewed=y: {unreviewed[:10]}")
    out = []
    for rec in records:
        u = decided.get(rec["id"])
        if u is not None:
            rec = dict(rec) | {"reviewed": "y", "reviewer": "user"} | \
                {f: u.get(f, "").strip() for f in ("final_label", "final_topic", "final_covered")}
        out.append(rec)
    return out


def _write_csv(records: list[dict], path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def assign_weeks(rows: list[Row], seed: int = 42, existing: dict[str, int] | None = None) -> list[Row]:
    """50/50 within each (source, label) stratum; matched pairs move as whole units in their own stratum.

    `existing` freezes weeks already assigned (id -> week): a relabel must never move a reviewed week 1 row into
    the test half. Only ids without a week are split.
    """
    existing = existing or {}
    units: dict[str, dict[str, list[Row]]] = defaultdict(dict)
    for r in rows:
        stratum, unit = ("pairs", r.pair_id) if r.pair_id else (f"{r.source}|{r.label}", r.id)
        units[stratum].setdefault(unit, []).append(r)
    week: dict[str, int] = {}
    for stratum, members in units.items():
        keys = sorted(k for k in members if not all(r.id in existing for r in members[k]))
        random.Random(f"{seed}:{stratum}").shuffle(keys)
        for i, k in enumerate(keys):
            for r in members[k]:
                week[r.id] = 1 if i < len(keys) // 2 else 2
    return [replace(r, week=existing.get(r.id, week.get(r.id))) for r in rows]


def _read_rows(path: Path) -> list[Row]:
    return [Row.from_dict(json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def _write_rows(rows: list[Row], path: Path) -> None:
    path.write_text("".join(json.dumps(r.to_dict()) + "\n" for r in rows))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m ppguard.build")
    ap.add_argument("step", choices=["candidates", "export-labels", "apply-review", "apply-user", "assemble"])
    step = ap.parse_args(argv).step
    if step == "candidates":
        from .sources import load_all
        rows, report = dedupe(load_all())
        _write_rows(rows, CANDIDATES)
        (DATA / "dedupe_report.json").write_text(json.dumps(report, indent=1))
        print(f"{len(rows)} rows ({sum(r.needs_review for r in rows)} need review); {len(report)} duplicates dropped,"
              f" {sum(d['conflict'] for d in report)} with conflicting labels")
    elif step == "export-labels":
        rows = _read_rows(CANDIDATES)
        spot = spot_check_ids(rows)
        export_label_csv(rows, spot, LABELS_CSV)
        print(f"{LABELS_CSV}: {sum(r.needs_review for r in rows)} need review + {len(spot)} spot-check rows")
    elif step == "apply-review":
        recs = apply_agent_review(_read_csv(LABELS_CSV), _read_csv(AGENT_REVIEW))
        _write_csv(recs, LABELS_CSV, CSV_COLUMNS)
        todo = [r | {"draft": "/".join(x for x in (r["draft_label"] or r["expected"], r["draft_topic"],
                                                    r["draft_covered"] and f"covered={r['draft_covered']}") if x),
                     "reviewer_note": r["note"]} for r in recs if not r["reviewed"]]
        _write_csv(todo, FOR_USER, USER_COLUMNS)
        print(f"{len(recs) - len(todo)} rows settled by the agent; {len(todo)} for the user in {FOR_USER}")
    elif step == "apply-user":
        recs = apply_user_review(_read_csv(LABELS_CSV), _read_csv(FOR_USER))
        _write_csv(recs, LABELS_CSV, CSV_COLUMNS)
        print(f"merged {FOR_USER}; {sum(not r['reviewed'] for r in recs)} rows still unreviewed")
    else:
        frozen = {r.id: r.week for r in _read_rows(TESTSET)} if TESTSET.exists() else {}
        rows = assign_weeks(apply_labels(_read_rows(CANDIDATES), _read_csv(LABELS_CSV)), existing=frozen)
        unlabelled = [r.id for r in rows if r.label is None]
        if unlabelled:
            raise SystemExit(f"{len(unlabelled)} rows still have no label, e.g. {unlabelled[:5]}")
        _write_rows(rows, TESTSET)
        counts = Counter((r.label, r.week) for r in rows)
        print(f"{TESTSET}: {len(rows)} rows")
        for label in LABELS:
            print(f"  {label:12} week1 {counts[(label, 1)]:4}  week2 {counts[(label, 2)]:4}")


if __name__ == "__main__":
    main()
