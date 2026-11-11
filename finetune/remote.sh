#!/usr/bin/env bash
# GLiNER fine-tune on a GPU box over ssh, inside a Docker image tagged gliner-decide:local (torch + gliner2).
# Set GPU_HOST=user@host first; the box gets its own folder, ~/dev/ppguard-finetune.
#   finetune/remote.sh push      copy the scripts and data/finetune/ to the box
#   finetune/remote.sh start     run finetune/run_all.sh there in the background (container ppguard-ft)
#   finetune/remote.sh status    container state, GPU users, latest log lines
#   finetune/remote.sh pull      copy predictions, logs and run stats back into results/finetune/
set -euo pipefail
HOST=${GPU_HOST:?set GPU_HOST=user@host}
DIR=dev/ppguard-finetune
LIB=/usr/lib/x86_64-linux-gnu
root=$(cd "$(dirname "$0")/.." && pwd)
V=${FT_VERSION:-1}                       # FT_VERSION=2 uses data/finetune_v2 and results/finetune_v2
SUFFIX=$([ "$V" = 1 ] && echo "" || echo "_v$V")
case "${1:-}" in
  push)
    ssh "$HOST" "mkdir -p $DIR/out $DIR/data"
    rsync -a "$root/finetune/train.py" "$root/finetune/predict_tasks.py" "$root/finetune/run_all.sh" "$HOST:$DIR/"
    rsync -a --delete "$root/data/finetune$SUFFIX/" "$HOST:$DIR/data/" ;;
  start)
    ssh "$HOST" "docker run -d --rm --name ppguard-ft \
      --device /dev/nvidiactl --device /dev/nvidia0 --device /dev/nvidia-uvm --device /dev/nvidia-uvm-tools \
      -v $LIB/libcuda.so.1:$LIB/libcuda.so.1:ro \
      -v $LIB/libnvidia-ml.so.1:$LIB/libnvidia-ml.so.1:ro \
      -v $LIB/libnvidia-ptxjitcompiler.so.1:$LIB/libnvidia-ptxjitcompiler.so.1:ro \
      -v gliner-decide_hf-cache:/home/app/.cache/huggingface -e HF_HUB_OFFLINE=1 \
      -v \$HOME/$DIR:/work -w /work --shm-size 2g \
      --entrypoint sh gliner-decide:local /work/run_all.sh" ;;
  status)
    ssh "$HOST" "docker ps --filter name=ppguard-ft --format '{{.Names}} {{.Status}}'; \
      nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader; \
      ls -t $DIR/out/*.log 2>/dev/null | head -1 | xargs -r tail -n 3" ;;
  pull)
    mkdir -p "$root/results/finetune$SUFFIX"
    rsync -a --include='tasks_*.jsonl' --include='*.log' --include='ALL_DONE' --include='lora_*/' \
      --include='lora_*/run_stats.json' --exclude='*' "$HOST:$DIR/out/" "$root/results/finetune$SUFFIX/" ;;
  *) sed -n 4,7p "$0"; exit 1 ;;
esac
