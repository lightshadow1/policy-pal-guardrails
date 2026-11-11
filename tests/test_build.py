import csv
from collections import defaultdict
from dataclasses import replace

import pytest

from ppguard.build import apply_labels, assign_weeks, dedupe, export_label_csv, spot_check_ids
from ppguard.labels import Row


def test_dedupe_keeps_first_and_reports_conflict():
    a = Row(id="xstest:1", text="How do I kill a process?", source="xstest", licence="x", label="irrelevant")
    b = Row(id="aegis:1", text="how do I kill a  process?", source="aegis", licence="x", label="not_allowed",
            topic="harmful")
    kept, report = dedupe([a, b])
    assert kept == [a] and report == [{"kept": "xstest:1", "dropped": "aegis:1", "conflict": True}]


def test_apply_labels_normalises_and_rejects():
    r = Row(id="p:1", text="t", source="policypal", licence="x", label=None, needs_review=True)
    ok = {"id": "p:1", "reviewed": "y", "draft_label": "not_allowed", "draft_topic": "legal",
          "draft_covered": "", "final_label": " In Scope ", "final_topic": "", "final_covered": "false"}
    assert apply_labels([r], [ok])[0] == replace(r, label="in_scope", covered=False, labelled_by="human",
                                                 needs_review=False)
    with pytest.raises(ValueError, match="p:1"):
        apply_labels([r], [{**ok, "final_label": "inscope"}])
    with pytest.raises(ValueError, match="p:1"):
        apply_labels([r], [{**ok, "final_label": "not_allowed", "final_topic": ""}])
    with pytest.raises(ValueError, match="p:1"):
        apply_labels([r], [{**ok, "reviewed": ""}])


def test_apply_labels_accepts_draft_and_strips_bom():
    r = Row(id="p:2", text="t", source="pairs", licence="x", label=None, needs_review=True)
    rec = {"﻿id": "p:2", "reviewed": "Y", "draft_label": "not_allowed", "draft_topic": "medical",
           "draft_covered": "", "final_label": "", "final_topic": "", "final_covered": ""}
    out = apply_labels([r], [rec])[0]
    assert (out.label, out.topic, out.labelled_by, out.needs_review) == ("not_allowed", "medical",
                                                                         "drafted+reviewed", False)


def test_apply_labels_requires_every_needs_review_row():
    r = Row(id="p:3", text="t", source="pairs", licence="x", label=None, needs_review=True)
    with pytest.raises(ValueError, match="p:3"):
        apply_labels([r], [])


def test_spot_check_row_overridden_becomes_human():
    r = Row(id="c:1", text="t", source="clinc", licence="x", label="irrelevant")
    rec = {"id": "c:1", "reviewed": "y", "draft_label": "", "draft_topic": "", "draft_covered": "",
           "final_label": "in_scope", "final_topic": "", "final_covered": "no"}
    assert apply_labels([r], [rec])[0] == replace(r, label="in_scope", covered=False, labelled_by="human")
    same = {**rec, "final_label": "", "final_covered": ""}
    assert apply_labels([r], [same])[0] == r


def test_assign_weeks_is_balanced_and_keeps_pairs_together():
    rows = [Row(id=f"c:{i}", text=str(i), source="clinc", licence="x", label="irrelevant") for i in range(10)]
    rows += [Row(id=f"p:{i}", text=f"p{i}", source="pairs", licence="x", label="in_scope", pair_id=f"k{i // 2}")
             for i in range(8)]
    out = assign_weeks(rows)
    assert sum(r.week == 1 for r in out if r.source == "clinc") == 5
    weeks = defaultdict(set)
    for r in out:
        if r.pair_id:
            weeks[r.pair_id].add(r.week)
    assert all(len(w) == 1 for w in weeks.values())
    assert sum(1 for w in weeks.values() if w == {1}) == 2


def test_spot_check_is_ten_percent_of_source_labelled():
    rows = [Row(id=f"c:{i}", text=str(i), source="clinc", licence="x", label="irrelevant") for i in range(50)]
    rows += [Row(id=f"a:{i}", text=f"a{i}", source="aegis", licence="x", label="irrelevant") for i in range(30)]
    rows += [Row(id=f"p:{i}", text=f"p{i}", source="pairs", licence="x", label=None, needs_review=True)
             for i in range(20)]
    ids = spot_check_ids(rows)
    assert len([i for i in ids if i.startswith("c:")]) == 5 and len([i for i in ids if i.startswith("a:")]) == 3
    assert not any(i.startswith("p:") for i in ids)


def test_export_refuses_to_overwrite_reviewed_csv(tmp_path):
    path = tmp_path / "labels.csv"
    rows = [Row(id="p:1", text="t", source="pairs", licence="x", label=None, needs_review=True, note="expected: x")]
    export_label_csv(rows, set(), path)
    with path.open(newline="") as f:
        recs = list(csv.DictReader(f))
    assert recs[0]["expected"] == "expected: x" and recs[0]["spot_check"] == ""
    recs[0]["reviewed"] = "y"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]))
        w.writeheader()
        w.writerows(recs)
    with pytest.raises(FileExistsError):
        export_label_csv(rows, set(), path)


def _rec(rid, **kw):
    base = {"id": rid, "source": "pairs", "text": "t", "expected": "", "spot_check": "", "draft_label": "irrelevant",
            "draft_topic": "", "draft_covered": "", "draft_reason": "", "reviewed": "", "final_label": "",
            "final_topic": "", "final_covered": "", "note": ""}
    return base | kw


def test_apply_agent_review_applies_confident_verdicts_and_queues_unsure():
    from ppguard.build import apply_agent_review
    recs = [_rec("a"), _rec("b"), _rec("c")]
    review = [{"id": "a", "verdict": "agree", "label": "", "topic": "", "covered": "", "reason": "", "alternative": ""},
              {"id": "b", "verdict": "change", "label": "not_allowed", "topic": "legal", "covered": "",
               "reason": "asks if enforceable", "alternative": ""},
              {"id": "c", "verdict": "unsure", "label": "in_scope", "topic": "", "covered": "no",
               "reason": "HR or coaching?", "alternative": "irrelevant"}]
    out = {r["id"]: r for r in apply_agent_review(recs, review)}
    assert (out["a"]["reviewed"], out["a"]["reviewer"], out["a"]["final_label"]) == ("y", "opus", "")
    assert (out["b"]["reviewed"], out["b"]["final_label"], out["b"]["final_topic"]) == ("y", "not_allowed", "legal")
    assert (out["c"]["reviewed"], out["c"]["reviewer"], out["c"]["final_label"], out["c"]["final_covered"]) == \
        ("", "", "in_scope", "no")
    assert "irrelevant" in out["c"]["note"] and "HR or coaching?" in out["c"]["note"]


def test_apply_agent_review_requires_every_row():
    from ppguard.build import apply_agent_review
    with pytest.raises(ValueError, match="b"):
        apply_agent_review([_rec("a"), _rec("b")], [{"id": "a", "verdict": "agree", "label": "", "topic": "",
                                                     "covered": "", "reason": "", "alternative": ""}])


def test_apply_user_review_marks_user_and_requires_reviewed():
    from ppguard.build import apply_user_review
    recs = [_rec("c", final_label="in_scope", final_covered="no"), _rec("d", reviewed="y", reviewer="opus")]
    user = [{"id": "c", "reviewed": "y", "final_label": "irrelevant", "final_topic": "", "final_covered": ""}]
    out = {r["id"]: r for r in apply_user_review(recs, user)}
    assert (out["c"]["reviewed"], out["c"]["reviewer"], out["c"]["final_label"], out["c"]["final_covered"]) == \
        ("y", "user", "irrelevant", "")
    assert out["d"]["reviewer"] == "opus"
    with pytest.raises(ValueError, match="c"):
        apply_user_review(recs, [{**user[0], "reviewed": ""}])


def test_apply_labels_records_the_reviewer():
    r = Row(id="p:1", text="t", source="pairs", licence="x", label=None, needs_review=True)
    rec = {"id": "p:1", "reviewed": "y", "reviewer": "opus", "draft_label": "irrelevant", "draft_topic": "",
           "draft_covered": "", "final_label": "", "final_topic": "", "final_covered": ""}
    assert apply_labels([r], [rec])[0].labelled_by == "drafted+reviewed:opus"
    changed = {**rec, "reviewer": "user", "final_label": "ambiguous"}
    assert apply_labels([r], [changed])[0].labelled_by == "corrected:user"


def test_spot_check_partial_correction_applies_on_top_of_source():
    r = Row(id="a:1", text="t", source="aegis", licence="x", label="not_allowed", topic="harmful")
    rec = {"id": "a:1", "reviewed": "y", "draft_label": "", "draft_topic": "", "draft_covered": "",
           "final_label": "", "final_topic": "privacy", "final_covered": ""}
    out = apply_labels([r], [rec])[0]
    assert (out.label, out.topic, out.labelled_by) == ("not_allowed", "privacy", "human")
    c = Row(id="c:1", text="t", source="clinc", licence="x", label="in_scope", covered=True)
    cov = {**rec, "id": "c:1", "final_topic": "", "final_covered": "no"}
    assert apply_labels([c], [cov])[0].covered is False


def test_assign_weeks_keeps_existing_weeks():
    rows = [Row(id=f"c:{i}", text=str(i), source="clinc", licence="x", label="irrelevant") for i in range(10)]
    first = {r.id: r.week for r in assign_weeks(rows)}
    relabelled = [replace(r, label="in_scope", covered=False) if r.id == "c:0" else r for r in rows]
    again = {r.id: r.week for r in assign_weeks(relabelled, existing=first)}
    assert again == first
