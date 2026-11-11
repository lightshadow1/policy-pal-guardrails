"""All configuration comes from the environment (.env). No credentials in code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    typesafe_api_key: str
    typesafe_endpoint: str
    jev_model: str
    typesafe_input_usd_per_mtok: float
    gliner_endpoint: str
    jev_concurrency: int
    gliner_concurrency: int   # the GPU box is shared: keep this at 1
    max_retries: int
    output_dir: Path
    limit: int                # rows per run; 0 = all
    seed: int
    n_bootstrap: int

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        g = os.environ.get
        return cls(
            typesafe_api_key=g("TYPESAFE_API_KEY", ""),
            typesafe_endpoint=g("TYPESAFE_ENDPOINT", "https://api.typesafe.ai/v1/systemone"),
            jev_model=g("JEV_MODEL", "jev-1.14.0"),
            typesafe_input_usd_per_mtok=float(g("TYPESAFE_INPUT_USD_PER_MTOK", "0.042")),
            gliner_endpoint=g("GLINER_ENDPOINT", "").rstrip("/"),
            jev_concurrency=int(g("JEV_CONCURRENCY", "8")),
            gliner_concurrency=int(g("GLINER_CONCURRENCY", "1")),
            max_retries=int(g("MAX_RETRIES", "6")),
            output_dir=Path(g("OUTPUT_DIR", "results")),
            limit=int(g("LIMIT", "0")),
            seed=int(g("SEED", "42")),
            n_bootstrap=int(g("N_BOOTSTRAP", "2000")),
        )
