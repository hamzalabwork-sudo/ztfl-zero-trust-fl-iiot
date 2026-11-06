"""E8b live + E9 -- statistical canary, and zero trust for the FL clients themselves (C1 + C2 + C3).

E9 applies the Zero-Trust principle of E5 to the federation's own participants: submitting a model
update is a privilege, and it is re-earned every round from evidence. The evidence is the
leave-one-out (LOO) canary: the round's aggregate is scored on the server's canary with and
without each client. When the deployed gate rejects a round, the server finds the smallest set of
clients whose exclusion makes the aggregate pass (client_trust.CounterfactualTrust). A client
implicated in two rejected rounds has its update privilege revoked on the provenance ledger, its
updates are dropped from aggregation, and the training state rolls back to the last version that
passed the canary (the registry head; the genesis model if none).

Variants (results/e9/<variant>/...):
- pilot: LOO logged, nothing revoked (seed 42 only; design data for the attribution rule).
  With nothing revoked these runs are also the live E8b runs: StatGate deployment tracks, and the
  adaptive attacker playing against stat_slo.
- trust: the full system (counterfactual attribution + revocation + rollback).

Gates in every run: e8 (E8 Gate, delta 0.05), stat (StatGate), stat_slo (StatGate, slo 0.5).
The adaptive attacker plays against stat_slo, the deployed gate of the full system. The closed
loop runs for best, last and stat_slo with the E5c evidence (monotone) and the E5e one
(monotone_balanced).

Results: results/e9/<variant>/<attack>_m<m>_on<onset>/<aggregator>/<dataset>/<mode>/mlp_s<seed>.json
Usage: python src/e9.py --variant pilot --seeds 42
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from canary import WARMUP, Gate, StatGate, checked_types
from client_trust import CounterfactualTrust
from closed_loop import N_CAL, SETTINGS, T_EV
from datasets import PREP_VERSION, prepare
from ledger import MemoryLedger, state_hash, update_hash
from models import build_model
from poison import BACKDOOR_TARGET
from stage3 import closed_loop
from train_central import code_version, metrics, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "e9"
ATTACKS = ("none", "label_flip", "backdoor", "backdoor_adaptive")
AGGREGATORS = ("fedavg", "multi_krum")
ONSETS = (1, 11)
PRIMARY = "stat_slo"
LLR_MODES = ("monotone", "monotone_balanced")


def make_gates(d, t_ref=None, y_ref=None) -> dict:
    """Canary gates built from the reference set (the validation split by default; the disjoint
    training slice under R2, passed as t_ref/y_ref, so per-type thresholds use the ref counts)."""
    t_ref = d.type_val if t_ref is None else t_ref
    y_ref = d.y_val if y_ref is None else y_ref
    types = checked_types(t_ref, y_ref)
    t, c = np.unique(t_ref[y_ref == 1], return_counts=True)
    n, n_b = {str(a): int(b) for a, b in zip(t, c)}, int((y_ref == 0).sum())
    return {"e8": Gate(types, 0.05), "stat": StatGate(types, n, n_b), "stat_slo": StatGate(types, n, n_b, slo=0.5)}


def ref_split(d, seed: int) -> np.ndarray:
    """R2: a stratified reference slice carved from the training pool, with per-type counts matching
    the validation split (so the canary's per-type row counts are unchanged -- WUSTL's small canary
    is not confounded), held out of client data so the canary and FLTrust root are disjoint from the
    val split used for best-val selection and gateway calibration."""
    rng = np.random.default_rng([seed, 23])
    idx = [rng.choice(np.flatnonzero(d.type_train == t),
                      min(int((d.type_val == t).sum()), int((d.type_train == t).sum())), replace=False)
           for t in np.unique(d.type_train)]
    return np.sort(np.concatenate([a for a in idx if len(a)]))


def tracks(fed: dict) -> dict[str, list[int]]:
    """The round the gateway runs after each round (0 = no model yet, fail-closed)."""
    out, best, best_f1 = {"best": [], "last": []}, 0, -1.0
    for c in fed["curve"]:
        if c["val_f1_macro"] > best_f1:
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


def run(d, attack: str, m: int, aggregator: str, onset: int, seed: int, device: str, variant: str,
        poison_budget: str = "full", disjoint_root: bool = False) -> dict:
    t0 = time.perf_counter()
    ref_idx = ref_split(d, seed) if disjoint_root else None
    gates = make_gates(d, d.type_train[ref_idx], d.y_train[ref_idx]) if disjoint_root else make_gates(d)
    trust = CounterfactualTrust(gates[PRIMARY]) if variant == "trust" else None
    ledger, hashes = MemoryLedger(), {}

    def on_round(rnd, before, after, states, sizes, vm):
        for c, ev in vm.get("revoked", {}).items():   # revocations precede the round they roll back
            ledger.record_revocation(rnd, c, vm["rollback_to"], ev)
        hashes[rnd] = state_hash(after)
        ledger.record_round(rnd, hashes[rnd], [update_hash(s, before) for s in states], sizes, vm["f1_macro"])
        ledger.record_verdict(rnd, hashes[rnd], PRIMARY, vm["canary"][PRIMARY], gates[PRIMARY].log[-1]["failed"])

    fed = train_fed("mlp", d, seed, device, k=10, alpha=0.5, on_round=on_round, keep_state=True, attack=attack,
                    n_malicious=m, aggregator=aggregator, onset=onset, gates=gates, attacked_gate=PRIMARY,
                    keep_rounds=True, loo_types=gates[PRIMARY].types, trust=trust, rollback_gate=PRIMARY,
                    poison_budget=poison_budget, ref_idx=ref_idx)
    states = fed.pop("_rounds")
    fed.pop("_state"), fed.pop("_last_state")
    model = build_model("mlp", d.input_dim).to(device)
    Xva, Xte = torch.from_numpy(d.X_val).to(device), torch.from_numpy(d.X_test).to(device)
    target = BACKDOOR_TARGET[d.dataset]
    per_round = []
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
        res["detector"][name] = (per_round[r - 1] if r else {}) | {"round": r}
        after = seq[max(onset, WARMUP + 1) - 1:]
        bd = [per_round[x - 1]["backdoor_success"] if x else 0.0 for x in after]
        res["exposure"][name] = {"backdoor_success_max": max(bd), "backdoor_success_mean": float(np.mean(bd)),
                                 "f1_macro_min": min((per_round[x - 1]["f1_macro"] for x in after if x), default=None),
                                 "no_model_rounds": sum(x == 0 for x in after),
                                 "stale_rounds_final": len(seq) - r}
        if name in ("best", "last", f"canary_{PRIMARY}") and r:
            model.load_state_dict(states[r - 1])
            s_val = scores(model, Xva, False).astype(np.float64)
            s_te = scores(model, Xte, False).astype(np.float64)
            res["access"][name] = {llr: closed_loop(d, s_val, s_te, seed, llr) for llr in LLR_MODES}
    head = ledger.registry_head(PRIMARY)
    res["ledger"] = ledger.summary() | {
        "registry_head_round": next((rr for rr, h in hashes.items() if h == head), 0),
        "gateway_runs_registry_head": (hashes[seqs[f"canary_{PRIMARY}"][-1]] == head) if head else
                                      seqs[f"canary_{PRIMARY}"][-1] == 0,
        "rejected_rounds": [b["round"] for b in ledger.blocks if b["kind"] == "verdict" and not b["promoted"]],
        "revoked_on_ledger": ledger.revoked_clients()}
    res |= {"trust": trust.report()} if trust is not None else {}
    return res | {"per_round": per_round, "gates": fed["gates"], "best_round": fed["best_round"],
                  "malicious": fed.get("malicious", []), "revoked": fed.get("revoked", []), "curve": fed["curve"],
                  "train_seconds": fed["train_seconds"], "wall_seconds": time.perf_counter() - t0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("pilot", "trust"), required=True)
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--attacks", default=",".join(ATTACKS))
    ap.add_argument("--aggregators", default=",".join(AGGREGATORS))
    ap.add_argument("--malicious", default="1,2,3")
    ap.add_argument("--onsets", default=",".join(map(str, ONSETS)))
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--poison-budget", choices=("full", "realistic"), default="full",
                    help="R1a: realistic partitions the target class across malicious clients (BackFed)")
    ap.add_argument("--disjoint-root", action="store_true",
                    help="R2: canary + FLTrust root from a disjoint training slice (not the val split)")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    vdir = (args.variant + ("" if args.poison_budget == "full" else f"_{args.poison_budget}")
            + ("_disjoint" if args.disjoint_root else ""))
    version = code_version()
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            mode, d = SETTINGS[ds], None
            for m in map(int, args.malicious.split(",")):
                for attack in args.attacks.split(","):
                    for onset in map(int, args.onsets.split(",")):
                        if attack == "none" and onset != 1:
                            continue
                        for agg in args.aggregators.split(","):
                            out = OUT / vdir / f"{attack}_m{m}_on{onset}" / agg / ds / mode / f"mlp_s{seed}.json"
                            if out.exists():
                                continue
                            d = d or prepare(ds, mode, seed)
                            res = run(d, attack, m, agg, onset, seed, args.device, args.variant,
                                      args.poison_budget, args.disjoint_root)
                            res.update(dataset=ds, mode=mode, model="mlp", seed=seed, attack=attack, n_malicious=m,
                                       aggregator=agg, onset=onset, variant=args.variant,
                                       backdoor_target=BACKDOOR_TARGET[ds], n_cal=N_CAL, t_ev=T_EV,
                                       prep_version=PREP_VERSION, code_version=version, torch=torch.__version__,
                                       device=args.device, host=platform.node())
                            out.parent.mkdir(parents=True, exist_ok=True)
                            out.write_text(json.dumps(res, indent=1))
                            det, c = res["detector"], f"canary_{PRIMARY}"
                            print(f"[{args.variant}/{ds}/{attack}/m{m}/on{onset}/{agg}/s{seed}] bd best/last/e8/stat/slo="
                                  + "/".join(f"{det[k].get('backdoor_success', 0):.3f}" for k in
                                             ("best", "last", "canary_e8", "canary_stat", c))
                                  + f" slo_round={det[c]['round']} revoked={res['revoked']} bad={res['malicious']} "
                                  f"({res['wall_seconds']:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
