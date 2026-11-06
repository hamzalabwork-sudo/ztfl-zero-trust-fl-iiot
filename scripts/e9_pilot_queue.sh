#!/usr/bin/env bash
# E9 pilot (seed 42 = calibration seed): LOO canary logged, nothing revoked. Also the live E8b runs.
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
w() {  # w <gpu> <log> <args...>
    local gpu=$1 log=$2; shift 2
    (CUDA_VISIBLE_DEVICES=$gpu .venv/bin/python src/e9.py --variant pilot --seeds 42 "$@" > "logs/$log.log" 2>&1; echo "== done" >> "logs/$log.log") &
}
w 0 e9_pilot_forge_fedavg --datasets forge --aggregators fedavg
w 0 e9_pilot_forge_mk --datasets forge --aggregators multi_krum
w 1 e9_pilot_edge --datasets edgeiiot
w 1 e9_pilot_wustl --datasets wustl
wait
