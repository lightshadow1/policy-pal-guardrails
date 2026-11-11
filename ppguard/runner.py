"""Score rows with Jev or GLiNER, with an incremental on-disk cache.

results/cache/<guard>/round<N>.jsonl : one line per scored row (append-only), tagged with fingerprint(d, guard)
results/cache/<guard>/errors.jsonl   : rows that failed after all retries (not cached, retried next run)

The cache stores raw scores, so thresholds are applied at evaluation time. Every guardrail sees the PII-scrubbed
text, as in Policy Pal's pipeline.

    uv run python -m ppguard.runner --guard jev --round 1
"""
from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .config import Config
from .definitions import Definitions, fingerprint
from .labels import Row
from .regex_guard import scrub_text

log = logging.getLogger("ppguard.runner")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # torn last line from an interrupted run
    return out


def cache_path(cfg: Config, guard: str, d: Definitions) -> Path:
    return cfg.output_dir / "cache" / guard / f"round{d.round}.jsonl"


def _backend(cfg: Config, guard: str):
    from .client import GlinerBackend, TypeSafeBackend
    return TypeSafeBackend(cfg) if guard == "jev" else GlinerBackend(cfg)


def run(cfg: Config, guard: str, d: Definitions, rows: list[Row], backend=None) -> dict[str, dict]:
    """Score every row not already cached. Returns id -> cached row for the requested rows that have one."""
    if guard not in ("jev", "gliner"):
        raise ValueError(f"unknown guard {guard!r}")
    rows = rows[:cfg.limit] if cfg.limit else rows
    path = cache_path(cfg, guard, d)
    path.parent.mkdir(parents=True, exist_ok=True)
    err_path = path.parent / "errors.jsonl"
    fp = fingerprint(d, guard)
    wanted = {r.id for r in rows}
    cached = {r["id"]: r for r in read_jsonl(path) if r.get("fingerprint") == fp and r["id"] in wanted}
    todo = [r for r in rows if r.id not in cached]
    log.info("[%s round %d] %d cached, %d to run", guard, d.round, len(cached), len(todo))
    if not todo:
        return cached
    backend = backend or _backend(cfg, guard)

    if path.exists() and path.stat().st_size and not path.read_bytes().endswith(b"\n"):
        with path.open("a") as f:
            f.write("\n")  # terminate a torn last line so the next append starts on its own line
    err_path.write_text("")  # errors reflect only the current attempt
    lock = threading.Lock()

    def work(r: Row) -> dict:
        t0 = time.monotonic()
        scores, usage = backend.score(d, scrub_text(r.text))
        return {"id": r.id, "fingerprint": fp, "scores": scores, "latency_s": round(time.monotonic() - t0, 4),
                "input_tokens": usage.input_tokens, "cost_usd": usage.cost_usd}

    workers = cfg.jev_concurrency if guard == "jev" else cfg.gliner_concurrency
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex, path.open("a") as cf, err_path.open("a") as ef:
        futs = {ex.submit(work, r): r for r in todo}
        for fut in as_completed(futs):
            r = futs[fut]
            try:
                out = fut.result()
                with lock:
                    cf.write(json.dumps(out) + "\n")
                    cf.flush()  # incremental: survives a crash mid-run
                cached[r.id] = out
            except Exception as e:  # noqa: BLE001 - record and continue
                with lock:
                    ef.write(json.dumps({"id": r.id, "text": scrub_text(r.text)[:200], "error": f"{type(e).__name__}: {e}"})
                             + "\n")
                    ef.flush()
    return cached


def load_rows(path: Path | None = None) -> list[Row]:
    from .build import CANDIDATES, TESTSET, _read_rows
    return _read_rows(path or (TESTSET if TESTSET.exists() else CANDIDATES))


def main(argv: list[str] | None = None) -> None:
    from . import definitions
    ap = argparse.ArgumentParser(prog="python -m ppguard.runner")
    ap.add_argument("--guard", choices=["jev", "gliner"], required=True)
    ap.add_argument("--round", type=int, choices=[1, 2], required=True)
    ap.add_argument("--rows", type=Path)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    d = definitions.ROUND1 if args.round == 1 else definitions.ROUND2
    if d is None:
        raise SystemExit("ROUND2 is not defined yet (set it after the week 1 review)")
    cfg = Config.from_env()
    rows = load_rows(args.rows)
    t0 = time.monotonic()
    out = run(cfg, args.guard, d, rows)
    n = min(len(rows), cfg.limit) if cfg.limit else len(rows)
    errors = read_jsonl(cache_path(cfg, args.guard, d).parent / "errors.jsonl")
    cost = sum(r.get("cost_usd") or 0 for r in out.values())
    lat = sorted(r["latency_s"] for r in out.values())
    p50 = lat[len(lat) // 2] if lat else 0
    print(f"{args.guard} round {args.round}: {len(out)}/{n} rows scored, {len(errors)} errors, "
          f"cost ${cost:.4f} (cached rows included), p50 {p50 * 1000:.0f} ms, wall {time.monotonic() - t0:.0f}s")


if __name__ == "__main__":
    main()
