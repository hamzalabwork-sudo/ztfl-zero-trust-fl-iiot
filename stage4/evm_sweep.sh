#!/bin/sh
# E10-chain: the testbed sessions re-run on the EVM ledger (after the round-order fix).
for ds in edgeiiot forge wustl; do for rho in 1.0 0.5 0.2; do
  [ "$ds" = edgeiiot ] && [ "$rho" = 1.0 ] && continue
  ${PYTHON:-python} run_e10.py --dataset $ds --rho $rho --ledger evm --run e10_${ds}_m2_rho${rho}_evm > results/evm_sweep_${ds}_${rho}.log 2>&1
  echo "$ds $rho exit=$?"
done; done
echo SWEEP_DONE
