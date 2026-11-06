#!/usr/bin/env bash
# Stage 3 baseline matrix: 5 attacks x 5 aggregators x m in {1,2,3} x 5 seeds, per dataset.
# GPU 0: Forge (slowest); GPU 1: Edge then WUSTL. Finished runs are skipped, so the queue is resumable.
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
(CUDA_VISIBLE_DEVICES=0 .venv/bin/python src/stage3.py --datasets forge > logs/stage3_forge.log 2>&1; echo "== done" >> logs/stage3_forge.log) &
(CUDA_VISIBLE_DEVICES=1 .venv/bin/python src/stage3.py --datasets edgeiiot,wustl > logs/stage3_edge_wustl.log 2>&1; echo "== done" >> logs/stage3_edge_wustl.log) &
wait
