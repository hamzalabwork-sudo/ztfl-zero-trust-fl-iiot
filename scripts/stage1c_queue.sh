#!/usr/bin/env bash
# Stage 1c queue (EXPERIMENTS.md E3 + E4), run from the repository root:
#   CUDA_VISIBLE_DEVICES=1 setsid nohup nice -n 5 bash scripts/stage1c_queue.sh > logs/stage1c.log 2>&1 < /dev/null &
set -e
FED=".venv/bin/python -X faulthandler -u src/train_fed.py --datasets edgeiiot,wustl,forge --seeds 42,43,44,45,46"
echo "== E4 autoencoder, validation-optimal threshold (alpha 0.5)"
$FED --models autoencoder --ae-threshold valopt
echo "== E3 non-IID ablation, alpha 0.1 (extreme)"
$FED --models mlp,transformer,cnn,lstm --alpha 0.1
echo "== E3 non-IID ablation, alpha 100 (near-IID)"
$FED --models mlp,transformer,cnn,lstm --alpha 100
echo "== done"
