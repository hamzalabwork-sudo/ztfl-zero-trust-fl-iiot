#!/usr/bin/env bash
# E8 defence matrix (src/defense.py, 1,260 runs) + E5e evidence variants (src/operating_curves.py).
# Seven workers split by dataset and seed (Forge is ~3x slower per run): GPU 0 Forge s42-44,
# GPU 1 Forge s45-46, Edge, WUSTL. E5e runs after the WUSTL worker. Finished runs are skipped,
# so the queue is resumable.
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
w() {  # w <gpu> <log> <args...>
    local gpu=$1 log=$2; shift 2
    (CUDA_VISIBLE_DEVICES=$gpu .venv/bin/python src/defense.py "$@" > "logs/$log.log" 2>&1; echo "== done" >> "logs/$log.log") &
}
for s in 42 43 44; do w 0 "defense_forge_s$s" --datasets forge --seeds $s; done
for s in 45 46; do w 1 "defense_forge_s$s" --datasets forge --seeds $s; done
w 1 defense_edge --datasets edgeiiot
(CUDA_VISIBLE_DEVICES=1 .venv/bin/python src/defense.py --datasets wustl > logs/defense_wustl.log 2>&1
 echo "== done" >> logs/defense_wustl.log
 for llr in monotone_balanced monotone_floor; do
     CUDA_VISIBLE_DEVICES=1 .venv/bin/python src/operating_curves.py --llr $llr >> logs/curves_e5e.log 2>&1
 done
 echo "== done" >> logs/curves_e5e.log) &
wait
