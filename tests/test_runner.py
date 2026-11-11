from dataclasses import replace

from conftest import cfg, row

from ppguard.client import Usage
from ppguard.definitions import ROUND1, score_names
from ppguard.runner import run


class FakeBackend:
    def __init__(self, fail_on=()):
        self.texts, self.fail_on = [], set(fail_on)

    def score(self, d, text):
        self.texts.append(text)
        if text in self.fail_on:
            raise RuntimeError("boom")
        return {n: 0.1 for n in score_names(d)}, Usage(10, 0, 1e-6)


def test_runner_sends_scrubbed_text(tmp_path):
    fb = FakeBackend()
    run(cfg(out=tmp_path), "jev", ROUND1, [row("My SSN is 123-45-6789")], backend=fb)
    assert "123-45-6789" not in fb.texts[0]


def test_runner_resumes_and_skips_cached(tmp_path):
    rows = [row("a"), row("b"), row("c")]
    first = run(cfg(out=tmp_path), "jev", ROUND1, rows, backend=FakeBackend(fail_on={"b"}))
    assert set(first) == {rows[0].id, rows[2].id}
    assert "b" in (tmp_path / "cache/jev/errors.jsonl").read_text()
    fb = FakeBackend()
    second = run(cfg(out=tmp_path), "jev", ROUND1, rows, backend=fb)
    assert fb.texts == ["b"] and set(second) == {r.id for r in rows}


def test_runner_ignores_rows_from_other_definitions(tmp_path):
    rows = [row("a")]
    run(cfg(out=tmp_path), "jev", ROUND1, rows, backend=FakeBackend())
    fb = FakeBackend()
    run(cfg(out=tmp_path), "jev", replace(ROUND1, topics={"legal": "changed"}), rows, backend=fb)
    assert fb.texts == ["a"]


def test_runner_respects_limit_and_records_cost(tmp_path):
    out = run(cfg(out=tmp_path, limit=2), "gliner", ROUND1, [row("a"), row("b"), row("c")], backend=FakeBackend())
    assert len(out) == 2 and all(r["cost_usd"] == 1e-6 and r["scores"]["legal"] == 0.1 for r in out.values())
    assert (tmp_path / "cache/gliner/round1.jsonl").exists()


def test_runner_errors_log_holds_scrubbed_text_only(tmp_path):
    from ppguard.regex_guard import scrub_text
    text = "My SSN is 123-45-6789"
    run(cfg(out=tmp_path), "jev", ROUND1, [row(text)], backend=FakeBackend(fail_on={scrub_text(text)}))
    import json
    err = json.loads((tmp_path / "cache/jev/errors.jsonl").read_text())
    assert "boom" in err["error"] and "123-45-6789" not in err["text"]  # (test ids are the text; real ids are hashes)
