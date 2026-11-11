#!/bin/sh
# Runs inside the gliner-decide image on the GPU box (started by finetune/remote.sh start).
# Stops at the first failure. Order: 20-step smoke run, base-model scores, then three seeds of
# train + score both checkpoints (best dev loss, final); ppguard.finetune evaluate picks one per seed by dev macro-F1.
# Batch size 4 for scoring: 16 ran out of GPU memory on long texts in v1.
set -e
cd /work
python train.py --max-steps 20 --grad-checkpointing --out /work/out/lora_smoke > out/smoke.log 2>&1
python predict_tasks.py --adapter none --tag base --schema schema.json --texts texts.jsonl --batch-size 4 \
  > out/predict_base.log 2>&1
for s in 42 43 44; do
  python train.py --grad-checkpointing --seed $s --out /work/out/lora_s$s > out/train_s$s.log 2>&1
  for c in best final; do
    python predict_tasks.py --adapter /work/out/lora_s$s/$c --tag ft_s${s}_$c --schema schema.json \
      --texts texts.jsonl --batch-size 4 > out/predict_s${s}_$c.log 2>&1
  done
done
echo done > out/ALL_DONE
