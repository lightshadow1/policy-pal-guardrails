"""Step 2 (GPU box, inside the gliner-decide image): LoRA fine-tune GLiNER2.5-Decide on train.jsonl.

    python train.py --max-steps 20 --grad-checkpointing --out /work/out/lora_smoke   # speed + memory check first
    python train.py --grad-checkpointing --seed 42 --out /work/out/lora_s42          # full run

Writes LoRA adapters to <out>/best (lowest dev loss) and <out>/final. The base weights never change.
Everything it needs is in data/ (written by `ppguard.finetune build`).
"""
import argparse
import json
import time
from pathlib import Path

import torch
from gliner2 import AutoExtractor
from gliner2.training.trainer import ExtractorTrainer, TrainingConfig

BASE, REVISION = "fastino/GLiNER2.5-Decide", "9d1bfb848cd16d93ee56ccbc59cd92bf0f284d90"  # the server's pin
MAX_WORDS = 384  # the server truncates texts to this, so train on what inference will see


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--train", default="train.jsonl", help="file under --data (learning-curve subsets differ)")
    ap.add_argument("--dev", default="dev.jsonl", help="file under --data")
    ap.add_argument("--out", default="/work/out/lora")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-steps", type=int, default=-1, help="stop early, e.g. 20 for a smoke check")
    # From jev2: batches of 8 run out of the 1080 Ti's memory (DeBERTa-v3-large keeps several attention-sized
    # tensors per layer and every input carries all label descriptions). 4 x 2 keeps an effective batch of 8.
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--grad-checkpointing", action="store_true", help="less memory, ~30%% slower")
    ap.add_argument("--lr", type=float, default=5e-4, help="LoRA learning rate (the trainer's task_lr)")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--seed", type=int, default=42, help="LoRA init and batch order; the data stays fixed")
    a = ap.parse_args()

    model = AutoExtractor.from_pretrained(BASE, revision=REVISION)  # fp32; the trainer moves it to the GPU
    config = TrainingConfig(
        output_dir=a.out, num_epochs=a.epochs, max_steps=a.max_steps,
        batch_size=a.batch_size, gradient_accumulation_steps=a.grad_accum, eval_batch_size=4,
        gradient_checkpointing=a.grad_checkpointing, task_lr=a.lr,
        # The GTX 1080 Ti (Pascal) has very slow fp16 math and no bf16, so train in fp32.
        fp16=False, bf16=False,
        # LoRA: freeze the base weights and train small low-rank updates on top of them.
        # Only the encoder and the classification head; the span/count heads serve entity extraction.
        use_lora=True, lora_r=a.lora_r, lora_alpha=2 * a.lora_r,
        lora_target_modules=["encoder", "classifier"],
        # Score dev every 100 steps, keep the best, stop after 3 evaluations without improvement.
        eval_strategy="steps", eval_steps=100, save_best=True, metric_for_best="eval_loss",
        early_stopping=True, early_stopping_patience=3,
        logging_steps=10, num_workers=2, max_len=MAX_WORDS, seed=a.seed,
    )
    t0 = time.time()
    summary = ExtractorTrainer(model, config).train(
        train_data=f"{a.data}/{a.train}", eval_data=f"{a.data}/{a.dev}")
    stats = {"train_file": a.train, "dev_file": a.dev, "seed": a.seed, "wall_minutes": round((time.time() - t0) / 60, 1),
             "peak_gpu_gib": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
    print(json.dumps({k: v for k, v in summary.items() if k != "history"}, default=str))
    print(json.dumps(stats))
    Path(a.out, "run_stats.json").write_text(json.dumps(stats))
    # The trainer logs a batch that fails (e.g. out of memory) to failed_batches.jsonl and moves on,
    # so a run can "finish" having learned from almost nothing. Treat any skipped batch as a failure.
    failed = Path(a.out, "failed_batches.jsonl")
    if failed.exists() and (n := sum(1 for _ in failed.open())):
        raise SystemExit(f"{n} batches failed and were skipped; see {failed}")


if __name__ == "__main__":
    main()
