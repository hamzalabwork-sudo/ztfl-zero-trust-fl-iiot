"""E5d -- operating curves of the gateway policies, plus the per-attack-type breakdown.

E5-E5c compare policies at one calibrated threshold each, so a policy can look better only
because its calibration landed at a different realised false-isolation rate. Here every
threshold is swept on the same paired test streams as E5 (same detector, same seeds, same
stream RNG), giving test false isolation vs time-to-isolation / detection / wrongful grants:
- ewma: trust threshold theta over THETA_GRID;
- cusum, cusum_sprt_mix: CUSUM threshold h over H_GRID (Lorden's 10.82 and E5's empirical h are
  marked in the output);
- per_event: score threshold over P_GRID. It never isolates, so its trade-off is wrongful grants
  vs benign denial.
Evidence is the monotone LLR (E5b/E5c). Picking a threshold from these curves uses test data, so
the curves are an analysis of the policies, not a deployable calibration.

Per-attack-type breakdown (tests the E5c finding 4 hypothesis): for each attack type in test,
the per-event detection rate and LLR, and, at Lorden's threshold, the share of devices with that
attack type that get isolated and the wrongful-grant rate of their attack events.

E5e: --llr monotone_balanced | monotone_floor reruns the same sweep with that evidence variant
(closed_loop.Evidence), written to curves_<llr>/ so it pairs with E5d seed by seed.

Results: results/closed_loop/curves[_<llr>]/<dataset>/<mode>/<model>_s<seed>.json
Usage: python src/operating_curves.py --datasets edgeiiot,forge,wustl --seeds 42,43,44,45,46 [--llr monotone_balanced]
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import torch

from closed_loop import (BUDGET, N_CAL, OUT, RHOS, SETTINGS, T_EV, Evidence, access_metrics, deploy, extreme, gate,
                         make_streams)
from datasets import PREP_VERSION
from ledger import MemoryLedger
from models import SUPERVISED
from train_central import code_version

H_LORDEN = float(np.log(T_EV / BUDGET))
H_GRID = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, H_LORDEN, 13.0, 16.0, 20.0)
THETA_GRID = (0.995, 0.99, 0.98, 0.97, 0.95, 0.93, 0.9, 0.85, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2)
P_GRID = (0.5, 0.3, 0.1, 0.05, 0.01, 1e-3, 1e-4)
CURVE_POLICIES = {"ewma": THETA_GRID, "cusum": H_GRID, "cusum_sprt_mix": H_GRID}
KEEP = ("false_isolation_rate", "benign_denial_rate", "benign_blocked_at_end", "detection_rate", "tti_median",
        "tti_p90", "wrongful_grant_rate", "false_reauth_rate", "lateral_reach_mean")


def per_type(S, A, tau, dev_type, granted, admitted, s_te, y_te, types_te, llr) -> dict:
    """Per attack type: event-level detectability and device-level outcome under one policy run."""
    t = S.shape[1]
    out_after = ~admitted & (np.arange(t)[None, :] >= tau[:, None])
    out = {}
    for at in np.unique(types_te[y_te == 1]):
        rows = types_te == at
        devs = dev_type == at
        e = llr(s_te[rows])
        out[str(at)] = {
            "test_rows": int(rows.sum()),
            "event_detect_rate": float((s_te[rows] >= 0.5).mean()),
            "llr_mean": float(e.mean()),
            "llr_nonpositive_share": float((e <= 0).mean()),
            "devices": int(devs.sum()),
            "device_isolated_rate": float(out_after[devs].any(axis=1).mean()) if devs.any() else None,
            "wrongful_grant_rate": float(granted[devs][A[devs]].mean()) if A[devs].any() else None,
        }
    return out


def run(ds: str, mode: str, seed: int, model_name: str, device: str, llr_mode: str = "monotone") -> dict:
    t0 = time.perf_counter()
    d, fed, deployed, s_val, s_te = deploy(ds, mode, seed, model_name, device, MemoryLedger())
    llr = Evidence(s_val, d.y_val, llr_mode, d.type_val)
    rng = np.random.default_rng(seed)                      # same calibration draw as closed_loop.run
    S_cal = s_val[rng.choice(np.flatnonzero(d.y_val == 0), (N_CAL, T_EV))]
    L_cal = llr(S_cal)
    marks = {"cusum_lorden": H_LORDEN,
             "cusum_empirical": float(np.quantile(extreme(S_cal, L_cal, "cusum"), 1 - BUDGET)),
             "ewma_empirical": float(np.quantile(extreme(S_cal, L_cal, "ewma"), BUDGET))}
    curves, types = {}, {}
    for rho in RHOS:
        S, A, tau, target, dev_type = make_streams(np.random.default_rng([seed, int(rho * 100)]), s_te, d.y_test,
                                                   d.type_test, rho)
        L = llr(S)
        comp = tau < T_EV
        key = f"rho{rho:g}"
        curves[key] = {"per_event": [{"threshold": p,
                                      "wrongful_grant_rate": float((S[A] < p).mean()),
                                      "benign_denial_rate": float((S[~comp] >= p).mean())} for p in P_GRID]}
        for policy, grid in CURVE_POLICIES.items():
            pts = []
            for th in grid:
                m = access_metrics(*gate(S, L, policy, th), A, tau, target)
                pts.append({"threshold": th} | {k: m[k] for k in KEEP})
            curves[key][policy] = pts
        types[key] = {}
        for policy, th in (("per_event", 0.5), ("cusum_sprt_mix", H_LORDEN)):
            granted, admitted, _ = gate(S, L, policy, th)
            types[key][policy] = per_type(S, A, tau, dev_type, granted, admitted, s_te, d.y_test, d.type_test, llr)
    return {"dataset": ds, "mode": mode, "seed": seed, "model": model_name,
            "detector": {"best_round": fed["best_round"], "test_f1_macro": fed["test"]["f1_macro"],
                         "deployed_model": deployed},
            "llr_mode": llr_mode, "llr_table": llr.table.tolist(), "marks": marks, "curves": curves, "per_type": types,
            "prep_version": PREP_VERSION, "code_version": code_version(), "torch": torch.__version__,
            "device": device, "wall_seconds": time.perf_counter() - t0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--model", default="mlp", choices=SUPERVISED)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--llr", choices=["monotone", "monotone_balanced", "monotone_floor"], default="monotone")
    args = ap.parse_args()
    sub = "curves" if args.llr == "monotone" else f"curves_{args.llr}"
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            mode = SETTINGS[ds]
            out = OUT / sub / ds / mode / f"{args.model}_s{seed}.json"
            if out.exists():
                continue
            res = run(ds, mode, seed, args.model, args.device, args.llr)
            ref = OUT / "monotone_lorden" / ds / mode / f"{args.model}_s{seed}.json"
            if ref.exists():  # same detector as E5c? (determinism check)
                res["detector"]["matches_e5c"] = json.loads(ref.read_text())["detector"]["deployed_model"] == res["detector"]["deployed_model"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(res, indent=1))
            print(f"[{ds}/{mode}/{args.model}/s{seed}] detector F1={res['detector']['test_f1_macro']:.4f} "
                  f"matches_e5c={res['detector'].get('matches_e5c')} ({res['wall_seconds']:.0f}s)", flush=True)
            for at, m in res["per_type"]["rho1"]["cusum_sprt_mix"].items():
                print(f"   {at:28s} event_detect={m['event_detect_rate']:.3f} llr<=0={m['llr_nonpositive_share']:.3f} "
                      f"isolated={m['device_isolated_rate']} wrongful={m['wrongful_grant_rate']}", flush=True)


if __name__ == "__main__":
    main()
