"""Shared test helpers."""
from __future__ import annotations

from ppguard.labels import Row


def row(text: str, label: str | None = None, **kw) -> Row:
    """A Row whose id is its text, so tests can key decisions by text."""
    fields = {"id": text, "text": text, "source": "test", "licence": "x", "label": label} | kw
    return Row(**fields)


def cfg(key: str = "", gliner: str = "", out=None, limit: int = 0):
    from pathlib import Path

    from ppguard.config import Config
    return Config(typesafe_api_key=key, typesafe_endpoint="https://api.typesafe.ai/v1/systemone",
                  jev_model="jev-1.14.0", typesafe_input_usd_per_mtok=0.042, gliner_endpoint=gliner,
                  jev_concurrency=2, gliner_concurrency=1, max_retries=0, output_dir=Path(out or "results"),
                  limit=limit, seed=42, n_bootstrap=50)
