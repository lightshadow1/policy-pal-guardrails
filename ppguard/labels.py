"""The four labels, the ground-truth topics, and the row every source is turned into.

Spec §3 (labels and what the bot does) and §4 (row format).
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

LABELS: tuple[str, ...] = ("in_scope", "irrelevant", "not_allowed", "ambiguous")
TOPICS: tuple[str, ...] = ("legal", "medical", "investment", "privacy", "harmful", "prompt_attack", "other")


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def make_id(source: str, text: str) -> str:
    digest = hashlib.sha1(f"{source}\n{normalize(text)}".encode()).hexdigest()[:12]
    return f"{source}:{digest}"


@dataclass(frozen=True)
class Row:
    id: str
    text: str
    source: str
    licence: str
    label: str | None             # None until a human has labelled it
    topic: str | None = None      # not_allowed only
    covered: bool | None = None   # in_scope only: does a policy section answer it?
    week: int | None = None       # 1 = discovery + validation, 2 = test
    pair_id: str | None = None    # matched pairs
    labelled_by: str = "source"   # source | human | drafted+reviewed
    note: str = ""
    needs_review: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Row":
        return cls(**d)


@dataclass(frozen=True)
class Decision:
    label: str
    topic: str | None = None
