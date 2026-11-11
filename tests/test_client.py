import pytest
from conftest import cfg

from ppguard import client
from ppguard.client import GlinerBackend, ParseError, TypeSafeBackend
from ppguard.definitions import ROUND1, Definitions, score_names


def test_typesafe_parses_every_score(monkeypatch):
    sent = {}

    def fake_post(url, *, headers, payload, max_retries, timeout=60):
        sent.update(payload)
        return {"answers": {n: {"noul": 0.25} for n in payload["questions"]}, "usage": {"input_tokens": 1000}}
    monkeypatch.setattr(client, "post_with_retry", fake_post)
    scores, usage = TypeSafeBackend(cfg(key="k")).score(ROUND1, "hello")
    assert scores == {n: 0.25 for n in score_names(ROUND1)}
    assert sent["state"] == {"user_message": "hello"} and sent["model"] == "jev-1.14.0"
    assert usage.cost_usd == pytest.approx(1000 * 0.042 / 1e6)


def test_typesafe_missing_answer_raises_parse_error(monkeypatch):
    monkeypatch.setattr(client, "post_with_retry", lambda *a, **k: {"answers": {"legal": {"noul": 0.1}}})
    with pytest.raises(ParseError):
        TypeSafeBackend(cfg(key="k")).score(ROUND1, "hello")


def test_typesafe_requires_key():
    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY"):
        TypeSafeBackend(cfg(key=""))


def test_gliner_converts_single_label_to_probability(monkeypatch):
    d = Definitions(2, topics={"legal": "l"}, in_scope="s", ambiguous="a")
    body = {"result": {"topic": [{"label": "legal", "confidence": 0.7}],
                       "scope": {"label": "irrelevant", "confidence": 0.8},
                       "clarity": {"label": "ambiguous", "confidence": 0.6}}}
    monkeypatch.setattr(client, "post_with_retry", lambda *a, **k: body)
    scores, _ = GlinerBackend(cfg(gliner="http://g")).score(d, "t")
    assert scores == pytest.approx({"legal": 0.7, "in_scope": 0.2, "ambiguous": 0.6})
