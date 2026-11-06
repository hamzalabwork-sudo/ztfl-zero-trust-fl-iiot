#!/bin/sh
# E10-chain on live PureChain: the nine attacked testbed sessions, ledger on the public free-gas
# network. Keys: two throwaway test keys in ~/.ztfl/purechain_keys.json (never committed); they reach
# the gateway container through the LEDGER_KEYS environment variable only.
PY=${PYTHON:-python}
export LEDGER_KEYS="$($PY -c "import json,pathlib; d=json.loads((pathlib.Path.home()/'.ztfl'/'purechain_keys.json').read_text()); print(d['coordinator']+','+d['gateway'])")"
for ds in edgeiiot forge wustl; do for rho in 1.0 0.5 0.2; do
  [ -f results/e10_${ds}_m2_rho${rho}_purechain.json ] && continue
  $PY run_e10.py --dataset $ds --rho $rho --ledger evm --rpc https://purechainnode.com \
      --run e10_${ds}_m2_rho${rho}_purechain > results/purechain_sweep_${ds}_${rho}.log 2>&1
  echo "$ds $rho exit=$?"
done; done
echo SWEEP_DONE
