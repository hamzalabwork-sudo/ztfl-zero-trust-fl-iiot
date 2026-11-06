"""E8b -- replay canary rules offline on the E8 runs (no retraining).

The gate only decides deployment; it never changes training. So for every non-adaptive E8 run,
any rule can be re-applied to the stored per-round canary metrics (curve: val_detection_by_type,
val_benign_flag_rate, val_f1_macro) and scored with the stored per-round test metrics (per_round).
backdoor_adaptive runs are skipped: those attackers adapted to the E8 gate, so a replay would
overstate a new rule. The adaptive attacker against StatGate is run live in E9.

Fidelity check: replaying the E8 Gate for every delta must reproduce the stored promoted rounds.

Rules: e8_d<delta> (as run), stat (StatGate, no SLO), stat_slo (StatGate, slo 0.5).
Rounds with no deployed model (stat_slo before its first pass) count as backdoor success 0 and
are reported as no_model rounds (an availability cost, not a security one).

Writes results/defense_replay/summary_long.csv and summary.md.
Usage (needs the prepared datasets for the canary sizes): python src/replay_gates.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from canary import DELTAS, WARMUP, Gate, StatGate
from closed_loop import SETTINGS
from datasets import prepare

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results" / "defense", ROOT / "results" / "defense_replay"


def canary_sizes(ds: str, seed: int) -> tuple[dict[str, int], int]:
    d = prepare(ds, SETTINGS[ds], seed)
    t, n = np.unique(d.type_val[d.y_val == 1], return_counts=True)
    return {str(a): int(c) for a, c in zip(t, n)}, int((d.y_val == 0).sum())


def replay(gate: Gate, curve: list[dict]) -> list[int]:
    """Head after each round (0 = no model)."""
    head, seq = 0, []
    for c in curve:
        if gate.check(c["round"], c["val_detection_by_type"], c["val_benign_flag_rate"], c["val_f1_macro"]):
            head = c["round"]
        seq.append(head)
    return seq


def score(seq: list[int], per_round: list[dict], onset: int) -> dict:
    after = seq[max(onset, WARMUP + 1) - 1:]
    bd = [per_round[r - 1]["backdoor_success"] if r else 0.0 for r in after]
    r = seq[-1]
    return {"round": r, "bd": per_round[r - 1]["backdoor_success"] if r else 0.0,
            "f1": per_round[r - 1]["f1_macro"] if r else np.nan, "bd_exp_max": max(bd), "bd_exp_mean": float(np.mean(bd)),
            "stale": len(seq) - r if r else len(seq), "no_model_rounds": sum(x == 0 for x in after),
            "no_model_final": r == 0}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes, rows, mismatch = {}, [], 0
    for p in sorted(RES.glob("*_m[0-9]_on*/*/*/*/mlp_s*.json")):
        r = json.loads(p.read_text())
        if r["attack"] == "backdoor_adaptive":
            continue
        key = (r["dataset"], r["seed"])
        if key not in sizes:
            sizes[key] = canary_sizes(*key)
            print("sizes", key, sizes[key], flush=True)
        n, n_b = sizes[key]
        types = r["gates"]["d0.05"]["types"]
        base = {k: r[k] for k in ("dataset", "attack", "n_malicious", "aggregator", "onset", "seed")}
        gates = {f"e8_d{x:g}": Gate(types, x) for x in DELTAS}
        gates |= {"stat": StatGate(types, n, n_b), "stat_slo": StatGate(types, n, n_b, slo=0.5)}
        for name, g in gates.items():
            seq = replay(g, r["curve"])
            if name.startswith("e8_") and g.promoted != r["gates"][name[3:]]["promoted"]:
                mismatch += 1
            post = [x for x in g.log if x["round"] > WARMUP]
            rows.append(base | {"rule": name, "rejected_share": sum(not x["promoted"] for x in post) / len(post),
                                "failed_types": ";".join(sorted({t for x in post for t in x["failed"]}))}
                        | score(seq, r["per_round"], r["onset"]))
        for track in ("best", "last"):
            seq = r["tracks"][track]
            rows.append(base | {"rule": track} | score(seq, r["per_round"], r["onset"]))
    df = pd.DataFrame(rows)
    clean = df[df.attack == "none"].set_index(["dataset", "aggregator", "n_malicious", "seed", "rule"])[["bd"]]
    df = df.join(clean.add_suffix("_clean"), on=["dataset", "aggregator", "n_malicious", "seed", "rule"])
    df["bd_excess"] = df.bd - df.bd_clean
    df.to_csv(OUT / "summary_long.csv", index=False)
    print(f"{df.groupby(['dataset', 'attack', 'n_malicious', 'aggregator', 'onset', 'seed']).ngroups} runs replayed; "
          f"E8 gate replay mismatches: {mismatch}")
    (OUT / "sizes.json").write_text(json.dumps({f"{k[0]}_s{k[1]}": v for k, v in sizes.items()}, indent=1))


if __name__ == "__main__":
    main()
