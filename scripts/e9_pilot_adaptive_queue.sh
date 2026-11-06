#!/usr/bin/env bash
# No-attribution baseline for E9 on the evaluation seeds: backdoor_adaptive vs stat_slo, nothing revoked.
# (Non-adaptive attacks: the E8 runs are that baseline -- identical training -- scored by replay_gates.py.)
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
for ds in forge edgeiiot wustl; do
    (CUDA_VISIBLE_DEVICES=1 .venv/bin/python src/e9.py --variant pilot --attacks backdoor_adaptive --datasets $ds \
         --seeds 43,44,45,46 > logs/e9_pilotad_$ds.log 2>&1; echo "== done" >> logs/e9_pilotad_$ds.log) &
done
wait
