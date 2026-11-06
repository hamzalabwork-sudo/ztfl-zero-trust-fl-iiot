"""E8 -- the proposed defence: per-type canary check + provenance registry with rollback (C1 + C3).

One run = (dataset, attack, m, aggregator, onset, seed); the federation as in E7. Every round's
global model is checked by canary.Gate for each delta in canary.DELTAS. The round hash, client
update hashes and the primary gate's verdict go on the provenance ledger, and the gateway follows
the registry head (the last promoted version).

Attacks: none, label_flip, backdoor, backdoor_adaptive (poison.py). ALIE and min-max are left
out: they did not move the detector in E7. Onset 1 = attack from the first round (as in E7; the
gate's warm-up is then poisoned too); onset 11 = clients compromised after 10 clean rounds.

Deployment tracks, all from the same training run (paired):
- best: the best-val round so far (E7's "best"); last: the latest round (E7's "last");
- canary_d<delta>: the registry head under that delta.
Per track: the final deployed model (detector metrics, backdoor success) and the exposure over
time, i.e. the backdoor success of the model the gateway runs after each round from
max(onset, WARMUP + 1) on (max and mean), so untrained warm-up rounds do not count. The closed loop of E5c / E7 runs for best, last and the primary canary track.

Results: results/defense/<attack>_m<m>_on<onset>/<aggregator>/<dataset>/<mode>/mlp_s<seed>.json
Usage: python src/defense.py --datasets forge --seeds 42
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from canary import DELTA_PRIMARY, DELTAS, WARMUP, Gate, checked_types
from closed_loop import N_CAL, SETTINGS, T_EV
from datasets import PREP_VERSION, prepare
from ledger import MemoryLedger, state_hash, update_hash
from models import build_model
from poison import BACKDOOR_TARGET
from stage3 import closed_loop
from train_central import code_version, metrics, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "defense"
ATTACKS = ("none", "label_flip", "backdoor", "backdoor_adaptive")
AGGREGATORS = ("fedavg", "median", "multi_krum", "fltrust_v2")
ONSETS = (1, 11)
PRIMARY = f"d{DELTA_PRIMARY:g}"


def tracks(fed: dict) -> dict[str, list[int]]:
    """For each deployment practice, the round the gateway runs after each round (1-based)."""
    out, best, best_f1 = {"best": [], "last": []}, 0, -1.0
    for c in fed["curve"]:
        if c["val_f1_macro"] > best_f1:           # same rule as train_fed's best-val selection
            best, best_f1 = c["round"], c["val_f1_macro"]
        out["best"].append(best)
        out["last"].append(c["round"])
    for name, g in fed["gates"].items():
        promoted, head, seq = set(g["promoted"]), 0, []
        for c in fed["curve"]:
            head = c["round"] if c["round"] in promoted else head
            seq.append(head)
        out[f"canary_{name}"] = seq
    return out


def run(d, attack: str, m: int, aggregator: str, onset: int, seed: int, device: str) -> dict:
    t0 = time.perf_counter()
    types = checked_types(d.type_val, d.y_val)
    gates = {f"d{x:g}": Gate(types, x) for x in DELTAS}
    ledger, hashes = MemoryLedger(), {}

    def on_round(rnd, before, after, states, sizes, vm):
        hashes[rnd] = state_hash(after)
        ledger.record_round(rnd, hashes[rnd], [update_hash(s, before) for s in states], sizes, vm["f1_macro"])
        ledger.record_verdict(rnd, hashes[rnd], PRIMARY, vm["canary"][PRIMARY], gates[PRIMARY].log[-1]["failed"])

    fed = train_fed("mlp", d, seed, device, k=10, alpha=0.5, on_round=on_round, keep_state=True, attack=attack,
                    n_malicious=m, aggregator=aggregator, onset=onset, gates=gates, attacked_gate=PRIMARY,
                    keep_rounds=True)
    states = fed.pop("_rounds")
    fed.pop("_state"), fed.pop("_last_state")
    model = build_model("mlp", d.input_dim).to(device)
    Xva, Xte = torch.from_numpy(d.X_val).to(device), torch.from_numpy(d.X_test).to(device)
    target = BACKDOOR_TARGET[d.dataset]
    per_round = []                                # test metrics of every round's global model
    for st in states:
        model.load_state_dict(st)
        t = metrics(d.y_test, scores(model, Xte, False).astype(np.float64), 0.5, d.type_test)
        per_round.append({"f1_macro": t["f1_macro"], "benign_flag_rate": t["benign_flag_rate"],
                          "backdoor_success": 1 - t["detection_by_type"][target],
                          "detection_by_type": t["detection_by_type"]})
    seqs = tracks(fed)
    res = {"detector": {}, "exposure": {}, "access": {}, "tracks": seqs}
    for name, seq in seqs.items():
        r = seq[-1]
        res["detector"][name] = per_round[r - 1] | {"round": r}
        after = [per_round[x - 1] for x in seq[max(onset, WARMUP + 1) - 1:]]
        res["exposure"][name] = {"backdoor_success_max": max(a["backdoor_success"] for a in after),
                                 "backdoor_success_mean": float(np.mean([a["backdoor_success"] for a in after])),
                                 "benign_flag_max": max(a["benign_flag_rate"] for a in after),
                                 "f1_macro_min": min(a["f1_macro"] for a in after),
                                 "stale_rounds_final": len(seq) - r}
        if name in ("best", "last", f"canary_{PRIMARY}"):
            model.load_state_dict(states[r - 1])
            s_val = scores(model, Xva, False).astype(np.float64)
            s_te = scores(model, Xte, False).astype(np.float64)
            res["access"][name] = closed_loop(d, s_val, s_te, seed)
    head = ledger.registry_head(PRIMARY)
    res["ledger"] = ledger.summary() | {
        "registry_head_round": next(rr for rr, h in hashes.items() if h == head),
        "gateway_runs_registry_head": hashes[seqs[f"canary_{PRIMARY}"][-1]] == head,
        "rejected_rounds": [b["round"] for b in ledger.blocks if b["kind"] == "verdict" and not b["promoted"]]}
    return res | {"per_round": per_round, "gates": fed["gates"], "best_round": fed["best_round"],
                  "malicious": fed.get("malicious", []), "curve": fed["curve"], "train_seconds": fed["train_seconds"],
                  "wall_seconds": time.perf_counter() - t0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--attacks", default=",".join(ATTACKS))
    ap.add_argument("--aggregators", default=",".join(AGGREGATORS))
    ap.add_argument("--malicious", default="1,2,3")
    ap.add_argument("--onsets", default=",".join(map(str, ONSETS)))
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    version = code_version()
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            mode, d = SETTINGS[ds], None
            for m in map(int, args.malicious.split(",")):
                for attack in args.attacks.split(","):
                    for onset in map(int, args.onsets.split(",")):
                        if attack == "none" and onset != 1:   # nothing starts: same run as onset 1
                            continue
                        for agg in args.aggregators.split(","):
                            out = OUT / f"{attack}_m{m}_on{onset}" / agg / ds / mode / f"mlp_s{seed}.json"
                            if out.exists():
                                continue
                            d = d or prepare(ds, mode, seed)
                            res = run(d, attack, m, agg, onset, seed, args.device)
                            res.update(dataset=ds, mode=mode, model="mlp", seed=seed, attack=attack, n_malicious=m,
                                       aggregator=agg, onset=onset, backdoor_target=BACKDOOR_TARGET[ds], n_cal=N_CAL,
                                       t_ev=T_EV, prep_version=PREP_VERSION, code_version=version,
                                       torch=torch.__version__, device=args.device, host=platform.node())
                            out.parent.mkdir(parents=True, exist_ok=True)
                            out.write_text(json.dumps(res, indent=1))
                            det, exp = res["detector"], res["exposure"]
                            c = f"canary_{PRIMARY}"
                            print(f"[{ds}/{attack}/m{m}/on{onset}/{agg}/s{seed}] bd final best/last/ours="
                                  f"{det['best']['backdoor_success']:.3f}/{det['last']['backdoor_success']:.3f}/"
                                  f"{det[c]['backdoor_success']:.3f} exposure max={exp['best']['backdoor_success_max']:.3f}/"
                                  f"{exp['last']['backdoor_success_max']:.3f}/{exp[c]['backdoor_success_max']:.3f} "
                                  f"F1 ours={det[c]['f1_macro']:.4f} r{det[c]['round']} "
                                  f"rejected={len(res['ledger']['rejected_rounds'])} "
                                  f"head_ok={res['ledger']['gateway_runs_registry_head']} ({res['wall_seconds']:.0f}s)",
                                  flush=True)


if __name__ == "__main__":
    main()
