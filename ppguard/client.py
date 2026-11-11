"""Jev (TypeSafe /v1/systemone) and GLiNER2.5-Decide (/v1/classify) scorers.

Both return `(scores, usage)`, where `scores` maps every name in `score_names(d)` to a probability.
"""
from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass

import requests

from .config import Config
from .definitions import Definitions, gliner_tasks, jev_questions, score_names

log = logging.getLogger("ppguard.client")

RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504, 529}


@dataclass(frozen=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None  # only when known: computed from list price (Jev)


class ParseError(RuntimeError):
    """The model answered, but not in a usable format."""


class RequestFailed(RuntimeError):
    """HTTP request failed after all retries."""


_tls = threading.local()


def _session() -> requests.Session:
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
    return _tls.s


def post_with_retry(url: str, *, headers: dict, payload: dict, max_retries: int, timeout: float = 60) -> dict:
    """POST JSON with exponential backoff + jitter on 429/5xx/529 and network errors."""
    last: str = ""
    for attempt in range(max_retries + 1):
        retry_after = None
        try:
            r = _session().post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code not in RETRYABLE_STATUS:
                raise RequestFailed(last)  # 4xx like 401/422 will not fix themselves
            ra = r.headers.get("Retry-After")
            retry_after = float(ra) if ra and ra.replace(".", "", 1).isdigit() else None
        except (requests.ConnectionError, requests.Timeout) as e:
            last = f"{type(e).__name__}: {e}"
        if attempt == max_retries:
            break
        delay = retry_after if retry_after is not None else min(60.0, 2.0 ** attempt) * random.uniform(0.5, 1.5)
        log.warning("retry %d/%d in %.1fs (%s)", attempt + 1, max_retries, delay, last[:120])
        time.sleep(delay)
    raise RequestFailed(f"gave up after {max_retries + 1} attempts: {last}")


def _clamp(p) -> float:
    return min(1.0, max(0.0, float(p)))


class TypeSafeBackend:
    def __init__(self, cfg: Config):
        if not cfg.typesafe_api_key:
            raise RuntimeError("TYPESAFE_API_KEY is required for Jev")
        self.cfg = cfg

    def score(self, d: Definitions, text: str) -> tuple[dict[str, float], Usage]:
        body = post_with_retry(
            self.cfg.typesafe_endpoint,
            headers={"Authorization": f"Bearer {self.cfg.typesafe_api_key}"},
            payload={"model": self.cfg.jev_model, "state": {"user_message": text}, "questions": jev_questions(d)},
            max_retries=self.cfg.max_retries, timeout=120,
        )
        try:
            answers = body["answers"]
            scores = {name: _clamp(answers[name]["noul"]) for name in score_names(d)}
        except (KeyError, TypeError, ValueError) as e:
            raise ParseError(f"unexpected TypeSafe response: {str(body)[:300]}") from e
        u = body.get("usage") or {}
        tin = u.get("input_tokens")
        cost = tin * self.cfg.typesafe_input_usd_per_mtok / 1e6 if tin is not None else None  # output is free
        return scores, Usage(tin, u.get("output_tokens"), cost)


class GlinerBackend:
    """One text per request (large schemas + batches OOM on the shared 1080 Ti)."""

    def __init__(self, cfg: Config):
        if not cfg.gliner_endpoint:
            raise RuntimeError("GLINER_ENDPOINT is required for GLiNER")
        self.cfg = cfg

    def score(self, d: Definitions, text: str) -> tuple[dict[str, float], Usage]:
        body = post_with_retry(
            f"{self.cfg.gliner_endpoint}/v1/classify", headers={},
            payload={"text": text, "tasks": gliner_tasks(d), "include_confidence": True},
            max_retries=self.cfg.max_retries,
        )
        try:
            result = body["result"]
            by_label = {s["label"]: _clamp(s["confidence"]) for s in result["topic"]}
            scores = {name: by_label[name] for name in d.topics}
            # single-label tasks are a softmax over two labels: the returned one carries `conf`
            if d.in_scope:
                s = result["scope"]
                scores["in_scope"] = _clamp(s["confidence"]) if s["label"] == "in_scope" else 1 - _clamp(s["confidence"])
            if d.ambiguous:
                c = result["clarity"]
                scores["ambiguous"] = _clamp(c["confidence"]) if c["label"] == "ambiguous" else 1 - _clamp(c["confidence"])
        except (KeyError, TypeError, ValueError) as e:
            raise ParseError(f"unexpected GLiNER response: {str(body)[:300]}") from e
        return scores, Usage()
