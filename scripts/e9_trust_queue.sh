#!/usr/bin/env bash
# E9 full system (StatGate+SLO deployment, counterfactual attribution, revocation, rollback): (client_trust.CounterfactualTrust), pre-registered on the
# seed-42 pilot. Seeds 43-46 = evaluation; 42 = in-sample, reported apart.
set -u
cd "$(dirname "$0")/.."
mkdir -p logs

w() {  # w <gpu> <log> <args...>
    local gpu=$1 log=$2; shift 2
    (CUDA_VISIBLE_DEVICES=$gpu .venv/bin/python src/e9.py --variant trust "$@" > "logs/$log.log" 2>&1; echo "== done" >> "logs/$log.log") &
}
for s in 42 43 44; do w 0 "e9_trust_forge_s$s" --datasets forge --seeds $s; done
for s in 45 46; do w 1 "e9_trust_forge_s$s" --datasets forge --seeds $s; done
w 1 e9_trust_edge --datasets edgeiiot
w 1 e9_trust_wustl --datasets wustl
wait
