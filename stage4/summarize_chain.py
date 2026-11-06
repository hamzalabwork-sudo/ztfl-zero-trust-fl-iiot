"""E10-chain summary: the testbed sessions on the EVM ledger (after the round-order fix).

For each dataset x rho it reports the on-chain transactions (count, failures, gas, confirmation
latency), the on-chain audit (every local record re-derived from contract events), and whether the
access-control metrics equal the memory-ledger run of the same configuration (the chain must not
change enforcement). Writes results/chain_summary.json (the figure reads it) and prints a table.

  python summarize_chain.py                 # local EVM node (anvil): *_evm.json
  python summarize_chain.py purechain       # live PureChain: *_purechain.json -> chain_summary_purechain.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent / "results"
DATASETS, RHOS = ["edgeiiot", "forge", "wustl"], ["1.0", "0.5", "0.2"]


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else "evm"
    rows, lat_dec, lat_round, gas = [], [], [], {"round": [], "decisions": []}
    enq_us, score_ms, by_ds = [], [], {ds: [] for ds in DATASETS}
    for ds in DATASETS:
        for rho in RHOS:
            evm = json.loads((R / f"e10_{ds}_m2_rho{rho}_{tag}.json").read_text())
            mem = json.loads((R / f"e10_{ds}_m2_rho{rho}.json").read_text())
            c, tx = evm["chain"], evm["chain"]["tx"]
            same = all(np.isclose(evm["metrics"][k], mem["metrics"][k], rtol=0, atol=1e-12)    # float summation order
                       if isinstance(mem["metrics"][k], float) else evm["metrics"][k] == mem["metrics"][k]
                       for k in mem["metrics"])
            for t in tx:
                gas[t["kind"]].append(t["gas"])
                (lat_dec if t["kind"] == "decisions" else lat_round).append(t["latency_s"])
                if t["kind"] == "decisions":
                    by_ds[ds].append(t["latency_s"])
            enq_us.append(1e6 * c["enqueue_seconds_total"] / len(tx))
            score_ms.append(evm["score_ms_per_event"])
            a = c["audit"]
            rows.append({"dataset": ds, "rho": rho, "tx": len(tx), "failed": c["failed"],
                         "onchain_records": a["onchain_rounds"] + a["onchain_decisions"],
                         "local_records": evm["ledger"]["rounds"] + evm["ledger"]["decision_batches"],
                         "audit_match": a["rounds_match"] and a["decisions_match"],
                         "deployed_trusted": all(a["trusted_models"]), "hash_chain_verified": evm["ledger"]["verified"],
                         "metrics_equal_memory": same,
                         "decision_latency_median_s": c["decisions"]["latency_median_s"],
                         "decision_latency_p95_s": c["decisions"]["latency_p95_s"]})
    lat_dec = np.array(lat_dec)
    out = {"sessions": rows,
           "totals": {"tx": int(sum(r["tx"] for r in rows)), "failed": int(sum(r["failed"] for r in rows)),
                      "onchain_records": int(sum(r["onchain_records"] for r in rows)),
                      "audit_match_all": all(r["audit_match"] for r in rows),
                      "metrics_equal_memory_all": all(r["metrics_equal_memory"] for r in rows),
                      "decision_latency_median_s": float(np.median(lat_dec)),
                      "decision_latency_p95_s": float(np.percentile(lat_dec, 95)),
                      "decision_latency_max_s": float(lat_dec.max()),
                      "round_latency_median_s": float(np.median(lat_round)),
                      "gas_decisions_median": float(np.median(gas["decisions"])),
                      "gas_decisions_range": [int(min(gas["decisions"])), int(max(gas["decisions"]))],
                      "gas_round_median": float(np.median(gas["round"])),
                      "enqueue_us_per_write_median": float(np.median(enq_us)),
                      "score_ms_per_event_median": float(np.median(score_ms))},
           "decision_latencies_s_by_dataset": by_ds}
    (R / ("chain_summary.json" if tag == "evm" else f"chain_summary_{tag}.json")).write_text(json.dumps(out, indent=1))
    print(f"{'dataset':9} {'rho':4} {'tx':>3} {'fail':>4} {'chain=local':>11} {'trusted':>7} {'=memory':>7} "
          f"{'med s':>6} {'p95 s':>6}")
    for r in rows:
        print(f"{r['dataset']:9} {r['rho']:4} {r['tx']:3d} {r['failed']:4d} "
              f"{str(r['audit_match']) + ' ' + str(r['onchain_records']) + '/' + str(r['local_records']):>11} "
              f"{str(r['deployed_trusted']):>7} {str(r['metrics_equal_memory']):>7} "
              f"{r['decision_latency_median_s']:6.2f} {r['decision_latency_p95_s']:6.2f}")
    print(json.dumps(out["totals"], indent=1))


if __name__ == "__main__":
    main()
