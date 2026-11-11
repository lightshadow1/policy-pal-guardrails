"""GPU box, inside the gliner-decide image: score any classification tasks offline, every label's score per text.
Called by finetune/run_all.sh, for example:

    python predict_tasks.py --adapter none --tag base
    python predict_tasks.py --adapter /work/out/lora_s42/best --tag ft_s42_best

Reads data/schema.json and data/texts.jsonl ({id, text}); writes out/tasks_<tag>.jsonl with
{"id", "<task>": {label: score}} per text.
"""
import argparse
import json

import torch
from gliner2 import AutoExtractor

BASE, REVISION = "fastino/GLiNER2.5-Decide", "9d1bfb848cd16d93ee56ccbc59cd92bf0f284d90"
MAX_WORDS = 384


def label_scores(out) -> dict:
    """Multi-label tasks return a list of {label, confidence}; single-label tasks (policy-pal-guardrails v2) return one
    {label, confidence} dict for the chosen label."""
    if isinstance(out, dict):
        out = [out]
    return {s["label"]: float(s["confidence"]) for s in out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, help="LoRA adapter directory, or 'none' for the base model")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--out", default="/work/out")
    ap.add_argument("--schema", default="schema.json")
    ap.add_argument("--texts", default="texts.jsonl")
    ap.add_argument("--batch-size", type=int, default=16)
    a = ap.parse_args()

    model = AutoExtractor.from_pretrained(BASE, revision=REVISION)
    if a.adapter != "none":
        model.load_adapter(a.adapter)
    model.to("cuda").eval()
    tasks = json.load(open(f"{a.data}/{a.schema}"))
    schema = model.create_schema()
    for name, config in tasks.items():  # same construction as the server's classification_schema
        options = dict(config)
        schema.classification(name, options.pop("labels"), **options)
    items = [json.loads(line) for line in open(f"{a.data}/{a.texts}")]

    with open(f"{a.out}/tasks_{a.tag}.jsonl", "w") as f, torch.inference_mode():
        for i in range(0, len(items), a.batch_size):
            batch = items[i:i + a.batch_size]
            try:
                results = model.batch_extract([it["text"] for it in batch], schema, batch_size=len(batch),
                                              threshold=0.5, include_confidence=True, max_len=MAX_WORDS)
            except torch.cuda.OutOfMemoryError:  # long texts: fall back to one at a time
                torch.cuda.empty_cache()
                results = [model.batch_extract([it["text"]], schema, batch_size=1, threshold=0.5,
                                               include_confidence=True, max_len=MAX_WORDS)[0] for it in batch]
            for it, r in zip(batch, results):
                f.write(json.dumps({"id": it["id"], **{t: label_scores(r[t]) for t in tasks}}) + "\n")
    print(f"scored {len(items)} texts -> {a.out}/tasks_{a.tag}.jsonl")


if __name__ == "__main__":
    main()
