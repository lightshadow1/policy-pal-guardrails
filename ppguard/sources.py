"""Turn each source dataset into `Row`s.

The builders are pure functions over already-loaded records, so they are tested offline. `load_all` is the only
function that touches the network (Hugging Face, cached after the first call).
"""
from __future__ import annotations

import html as htmllib
import json
import random
import re
from pathlib import Path

from .labels import Row, make_id

# ── StackExchange ─────────────────────────────────────────────────────────────

_SENTENCE = re.compile(r"[^.?!]+(?:[.?!]+|$)")


def se_excerpt(body_html: str, max_words: int = 60, max_sentences: int = 3, min_words: int = 4) -> str | None:
    """The first one to three sentences of a question body (no titles exist in the source), at most 60 words."""
    text = re.sub(r"<(pre|code)\b.*?</\1>", " ", body_html, flags=re.S | re.I)
    text = " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", text)).split())
    sentences = [s.strip() for s in _SENTENCE.findall(text) if s.strip()]
    if not sentences:
        return None
    first = sentences[0].split()
    if len(first) > max_words:
        picked = " ".join(first[:max_words])
    else:
        kept, words = [], 0
        for s in sentences[:max_sentences]:
            n = len(s.split())
            if words + n > max_words:
                break
            kept.append(s)
            words += n
        picked = " ".join(kept)
    return picked if len(picked.split()) >= min_words else None


def se_rows(site: str, records: list[dict], n: int, rng: random.Random, pattern: re.Pattern | None = None,
            expected: str = "") -> list[Row]:
    source = f"se:{site}"
    seen, rows = set(), []
    for rec in records:
        text = se_excerpt(rec.get("question") or "")
        if text is None or (pattern is not None and not pattern.search(text)):
            continue
        rid = make_id(source, text)
        if rid in seen:
            continue
        seen.add(rid)
        rows.append(Row(id=rid, text=text, source=source, licence="CC-BY-SA-4.0", label=None, needs_review=True,
                        note=f"expected: {expected} | qid: {rec.get('qid')}"))
    rng.shuffle(rows)
    return rows[:n]


# ── CLINC150 (`clinc/clinc_oos`, config `plus`, test split) ───────────────────

CLINC_COVERED = {"pto_request": True}  # hr §1.3 requests (§1.4 names no holiday dates, so next_holiday is uncovered)
CLINC_UNCOVERED = ("next_holiday", "pto_balance", "pto_used", "pto_request_status", "insurance", "insurance_change", "payday",
                   "direct_deposit", "w2", "income")  # personal records or benefits: in scope, redirect to HR
CLINC_REVIEW = ("taxes", "rollover_401k")             # personal tax help / close to investment advice
CLINC_MEETINGS = ("schedule_meeting", "meeting_schedule")
CLINC_WORK_INTENTS = frozenset(CLINC_COVERED) | frozenset(CLINC_UNCOVERED) | frozenset(CLINC_REVIEW) \
    | frozenset(CLINC_MEETINGS)
CLINC_N_OOS, CLINC_N_OTHER = 200, 140


def clinc_rows(rows: list[dict], intent_names: list[str], rng: random.Random) -> list[Row]:
    def make(text: str, intent: str, **kw) -> Row:
        return Row(id=make_id("clinc", text), text=text, source="clinc", licence="CC-BY-3.0", note=intent, **kw)

    out, oos, other = [], [], []
    for r in rows:
        intent = intent_names[r["intent"]]
        text = r["text"]
        if intent in CLINC_COVERED:
            out.append(make(text, intent, label="in_scope", covered=True))
        elif intent in CLINC_UNCOVERED:
            out.append(make(text, intent, label="in_scope", covered=False))
        elif intent in CLINC_REVIEW:
            out.append(make(text, intent, label=None, needs_review=True))
        elif intent in CLINC_MEETINGS:
            out.append(make(text, intent, label="irrelevant"))
        elif intent == "oos":
            oos.append(make(text, intent, label="irrelevant"))
        else:
            other.append(make(text, intent, label="irrelevant"))
    rng.shuffle(oos)
    rng.shuffle(other)
    return out + oos[:CLINC_N_OOS] + other[:CLINC_N_OTHER]


# ── Safety sets: XSTest, Aegis 2.0, CoCoNot, deepset prompt injections ────────

def _sample(rows: list[Row], n: int, rng: random.Random) -> list[Row]:
    unique = list({r.id: r for r in rows}.values())
    rng.shuffle(unique)
    return unique[:n]


def xstest_rows(rows: list[dict], n: int, rng: random.Random) -> list[Row]:
    safe = [Row(id=make_id("xstest", r["prompt"]), text=r["prompt"], source="xstest", licence="CC-BY-4.0",
                label="irrelevant", note=r.get("type") or "")
            for r in rows if r["label"] == "safe"]
    return _sample(safe, n, rng)


def aegis_rows(rows: list[dict], n_safe: int, n_unsafe: int, rng: random.Random) -> list[Row]:
    safe, unsafe = [], []
    for r in rows:
        text = (r.get("prompt") or "").strip()
        if not text or text == "REDACTED":
            continue
        cats = r.get("violated_categories") or ""
        base = dict(id=make_id("aegis", text), text=text, source="aegis", licence="CC-BY-4.0", note=cats)
        if r["prompt_label"] == "safe":
            safe.append(Row(**base, label="irrelevant"))
        else:
            unsafe.append(Row(**base, label="not_allowed", topic="privacy" if "PII/Privacy" in cats else "harmful"))
    return _sample(safe, n_safe, rng) + _sample(unsafe, n_unsafe, rng)


COCONOT_CATEGORY = "Requests with safety concerns"


def coconot_privacy_rows(rows: list[dict], n: int, rng: random.Random) -> list[Row]:
    keep = [Row(id=make_id("coconot", r["prompt"]), text=r["prompt"], source="coconot", licence="ODC-BY",
                label="not_allowed", topic="privacy")
            for r in rows if r["category"] == COCONOT_CATEGORY and r["subcategory"] == "privacy violations"]
    return _sample(keep, n, rng)


def deepset_rows(rows: list[dict]) -> list[Row]:
    keep = [Row(id=make_id("deepset", r["text"]), text=r["text"], source="deepset", licence="Apache-2.0",
                label="not_allowed", topic="prompt_attack")
            for r in rows if r["label"] == 1]
    return list({r.id: r for r in keep}.values())


# ── The user's own data: Policy Pal's logged queries, the matched pairs ───────

def policypal_rows(csv_records: list[dict]) -> list[Row]:
    out: dict[str, Row] = {}
    for rec in csv_records:
        text = (rec.get("original_question") or "").strip()
        if text:
            rid = make_id("policypal", text)
            out.setdefault(rid, Row(id=rid, text=text, source="policypal", licence="user's", label=None,
                                    needs_review=True, note="expected: "))
    return list(out.values())


def pair_rows(path: Path) -> list[Row]:
    rows = []
    for line in path.read_text().splitlines():
        p = json.loads(line)
        rows.append(Row(id=make_id("pairs", p["text"]), text=p["text"], source="pairs", licence="user's", label=None,
                        pair_id=p["pair_id"], needs_review=True,
                        note=f"expected: {p['label']}/{p['topic'] or ''} {p['policy_ref']}".rstrip()))
    return rows


# ── Loading everything (network on first call) ────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
SE_REPO = "HuggingFaceH4/stack-exchange-preferences"
POLICY_PAL_LOG = Path.home() / "dev/policy-pal/audit_log.csv"  # read only; written by a local Policy Pal run, not published
WORKPLACE_TOPICS = re.compile(r"\b(leave|vacation|holiday|pto|remote|work from home|expense|reimburs|review|appraisal"
                              r"|laptop|device|sick)\b", re.I)
SE_PLAN = [  # site, n, pattern, expected
    ("workplace.stackexchange.com", 100, WORKPLACE_TOPICS, "in_scope / irrelevant / ambiguous"),
    ("superuser.com", 30, None, "in_scope (work IT) / irrelevant / ambiguous"),
    ("askubuntu.com", 30, None, "in_scope (work IT) / irrelevant / ambiguous"),
    ("law.stackexchange.com", 100, None, "not_allowed/legal"),
    ("health.stackexchange.com", 100, None, "not_allowed/medical"),
    ("money.stackexchange.com", 100, None, "not_allowed/investment"),
]


def _se_records(site: str) -> list[dict]:
    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, hf_hub_download
    files = HfApi().list_repo_files(SE_REPO, repo_type="dataset")
    shard = sorted(f for f in files if f.startswith(f"data/{site}/"))[0]
    path = hf_hub_download(SE_REPO, shard, repo_type="dataset", local_dir=ROOT / "data/raw/se")
    return pq.read_table(path, columns=["qid", "question"]).to_pylist()


def load_all(seed: int = 42) -> list[Row]:
    import csv

    from datasets import load_dataset

    def rng(name: str) -> random.Random:
        return random.Random(f"{seed}:{name}")

    rows = pair_rows(ROOT / "data/pairs.jsonl")
    with POLICY_PAL_LOG.open(newline="", encoding="utf-8") as f:
        rows += policypal_rows(list(csv.DictReader(f)))
    clinc = load_dataset("clinc/clinc_oos", "plus", split="test")
    rows += clinc_rows(clinc.to_list(), clinc.features["intent"].names, rng("clinc"))
    for site, n, pattern, expected in SE_PLAN:
        rows += se_rows(site, _se_records(site), n, rng(site), pattern, expected)
    rows += xstest_rows(load_dataset("Paul/XSTest", split="train").to_list(), 150, rng("xstest"))
    rows += aegis_rows(load_dataset("nvidia/Aegis-AI-Content-Safety-Dataset-2.0", split="test").to_list(), 150, 200,
                       rng("aegis"))
    rows += coconot_privacy_rows(load_dataset("allenai/coconot", "original", split="test").to_list(), 80,
                                 rng("coconot"))
    rows += deepset_rows(load_dataset("deepset/prompt-injections", split="test").to_list())
    return rows
