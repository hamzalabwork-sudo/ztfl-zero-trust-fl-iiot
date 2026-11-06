"""Stage 3 -- attack x defense matrix: poisoning the federated detector as privilege escalation (C1).

One run = (dataset, attack, malicious clients m, aggregator, seed). Federated MLP as in E2 (alpha
0.5, K 10, 30 rounds); m of the 10 clients are malicious (poison.py). Reported:
- detector: clean test macro-F1, benign flag rate, per-type detection, and the backdoor success
  rate (share of target-type test rows scored benign), for the best-val round and the last round;
- access control: the closed loop of E5c (monotone LLR, Lorden's h) with the poisoned detector as
  the gateway's model, policies per_event and cusum_sprt_mix, rho 1.0 / 0.2. Streams use all
  attack types ("all") and, separately, only the backdoor target type ("target": the attacker
  uses the attack it tried to whitelist). Both deployment practices are evaluated: the server's
  best-val round ("best") and always the latest round ("last").
Evidence and thresholds are calibrated on validation with the deployed (possibly poisoned) model,
as a real gateway would.

Results: results/poison/<attack>_m<m>/<aggregator>/<dataset>/<mode>/mlp_s<seed>.json
Usage: python src/stage3.py --datasets edgeiiot,forge,wustl --attacks none,label_flip,alie,minmax,backdoor \
         --aggregators fedavg,median,trimmed_mean,multi_krum,fltrust --malicious 1,2,3 --seeds 42,43,44,45,46
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from closed_loop import N_CAL, SETTINGS, T_EV, Evidence, access_metrics, gate, make_streams
from datasets import PREP_VERSION, prepare
from models import build_model
from operating_curves import H_LORDEN
from poison import AGGREGATORS, ATTACKS, BACKDOOR_TARGET
from train_central import code_version, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "poison"
RHOS = (1.0, 0.2)
POLICIES = {"per_event": 0.5, "cusum_sprt_mix": H_LORDEN}


def closed_loop(d, s_val, s_te, seed: int, llr_mode: str = "monotone") -> dict:
    llr = Evidence(s_val, d.y_val, llr_mode, d.type_val)
    target = BACKDOOR_TARGET[d.dataset]
    out = {}
    for streams in ("all", "target"):
        for rho in RHOS:
            S, A, tau, tgt, _ = make_streams(np.random.default_rng([seed, int(rho * 100)]), s_te, d.y_test, d.type_test,
                                             rho, None if streams == "all" else target)
            L = llr(S)
            out[f"{streams}/rho{rho:g}"] = {p: access_metrics(*gate(S, L, p, th), A, tau, tgt) for p, th in POLICIES.items()}
    return out


def run(d, attack: str, m: int, aggregator: str, seed: int, device: str) -> dict:
    t0 = time.perf_counter()
    fed = train_fed("mlp", d, seed, device, k=10, alpha=0.5, keep_state=True, attack=attack, n_malicious=m,
                    aggregator=aggregator)
    model = build_model("mlp", d.input_dim).to(device)
    Xva, Xte = torch.from_numpy(d.X_val).to(device), torch.from_numpy(d.X_test).to(device)
    target = BACKDOOR_TARGET[d.dataset]
    res = {"detector": {}, "access": {}}
    for deploy, key in (("best", "_state"), ("last", "_last_state")):
        model.load_state_dict(fed.pop(key))
        s_val = scores(model, Xva, False).astype(np.float64)
        s_te = scores(model, Xte, False).astype(np.float64)
        t = fed["test"] if deploy == "best" else fed["last_round"]["test"]
        res["detector"][deploy] = {"f1_macro": t["f1_macro"], "benign_flag_rate": t["benign_flag_rate"],
                                   "recall": t["recall"], "backdoor_success": 1 - t["detection_by_type"][target],
                                   "detection_by_type": t["detection_by_type"]}
        res["access"][deploy] = closed_loop(d, s_val, s_te, seed)
    return res | {"best_round": fed["best_round"], "malicious": fed.get("malicious", []),
                  "curve": fed["curve"], "train_seconds": fed["train_seconds"],
                  "wall_seconds": time.perf_counter() - t0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--attacks", default=",".join(ATTACKS))
    ap.add_argument("--aggregators", default=",".join(AGGREGATORS))
    ap.add_argument("--malicious", default="1,2,3")
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    version = code_version()
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            mode, d = SETTINGS[ds], None
            for m in map(int, args.malicious.split(",")):
                for attack in args.attacks.split(","):
                    for agg in args.aggregators.split(","):
                        out = OUT / f"{attack}_m{m}" / agg / ds / mode / f"mlp_s{seed}.json"
                        if out.exists():
                            continue
                        d = d or prepare(ds, mode, seed)
                        res = run(d, attack, m, agg, seed, args.device)
                        res.update(dataset=ds, mode=mode, model="mlp", seed=seed, attack=attack, n_malicious=m,
                                   aggregator=agg, backdoor_target=BACKDOOR_TARGET[ds], n_cal=N_CAL, t_ev=T_EV,
                                   prep_version=PREP_VERSION, code_version=version, torch=torch.__version__,
                                   device=args.device, host=platform.node())
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_text(json.dumps(res, indent=1))
                        b, a = res["detector"]["best"], res["access"]["best"]
                        print(f"[{ds}/{attack}/m{m}/{agg}/s{seed}] best r{res['best_round']} F1={b['f1_macro']:.4f} "
                              f"bd_success={b['backdoor_success']:.3f} last F1={res['detector']['last']['f1_macro']:.4f} "
                              f"last bd={res['detector']['last']['backdoor_success']:.3f} | wrongful all/rho1 "
                              f"per_event={a['all/rho1']['per_event']['wrongful_grant_rate']:.4f} "
                              f"mix={a['all/rho1']['cusum_sprt_mix']['wrongful_grant_rate']:.4f} target/rho1 "
                              f"per_event={a['target/rho1']['per_event']['wrongful_grant_rate']:.4f} "
                              f"mix={a['target/rho1']['cusum_sprt_mix']['wrongful_grant_rate']:.4f} "
                              f"({res['wall_seconds']:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
