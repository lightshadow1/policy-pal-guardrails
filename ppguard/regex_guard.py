"""Policy Pal's input guardrail as shipped, mapped onto the four labels.

Same order as Policy Pal's pipeline: scrub PII, run `check_input`, then keyword retrieval. A retrieval miss is
how the shipped pipeline catches off-topic questions. The vendored code is never modified.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

from .labels import Decision

VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "policypal"
sys.path.insert(0, str(VENDOR))  # the vendored guardrails.py does `from pii_scrubber import scrub`

import guardrails  # noqa: E402
import pii_scrubber  # noqa: E402
import retrieval  # noqa: E402

_TOPIC_BY_POLICY = {
    "prompt_attack": "prompt_attack",
    "denied_topic:legal_advice": "legal",
    "denied_topic:medical_advice": "medical",
    "denied_topic:investment_advice": "investment",
}


def scrub_text(text: str) -> str:
    return pii_scrubber.scrub(text).scrubbed


@functools.cache
def _docs() -> dict[str, str]:
    return retrieval.load_policies(str(VENDOR / "policies"))


def retrieval_hit(text: str) -> bool:
    return retrieval.find_relevant_policy(text, _docs()) is not None


def regex_decide(text: str) -> Decision:
    clean = scrub_text(text)
    result = guardrails.check_input(clean)
    if result.action == guardrails.GuardrailAction.BLOCK:
        return Decision("not_allowed", _TOPIC_BY_POLICY.get(result.triggered_policy, "other"))
    return Decision("in_scope") if retrieval_hit(clean) else Decision("irrelevant")
