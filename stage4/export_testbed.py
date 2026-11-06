"""Stage 4 (E10) -- export the deployed final-system detector as a testbed bundle.

The emulated testbed scores events with the EXACT model and calibration the simulation validated
(E7-E9): FedAvg detector, the stat_slo canary registry head deployed at the gateway, the
monotone_balanced evidence model, and Lorden's CUSUM threshold. Nothing about the detector or the
decision rule changes in the testbed; stage 4 only replaces the semi-synthetic i.i.d. device
streams with real per-device MQTT sessions (real identity, timing and enforcement).

For one (dataset, seed) this writes stage4/export/<dataset>/:
  model.pt     deployed state_dict (the stat_slo registry head of a clean federated run)
  calib.json   model name, input_dim, feature_names, the monotone_balanced LLR table and bins,
               the Lorden CUSUM threshold, the per-event threshold, and the SPRT constants copied
               verbatim from closed_loop.py so the gateway's per-device authoriser is bit-identical
               to the simulator's cusum_sprt_mix policy.
  pool.npz     held-out TEST feature vectors (X float32, y int8, type <U32) the devices emit.
  model_hash   sha256 of the deployed state_dict (the provenance id recorded on the ledger).

Run on the lab server or the laptop (CPU is fine; edge cache ships with the laptop):
  PYTHONPATH=src python stage4/export_testbed.py --dataset edgeiiot --seed 42
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

import closed_loop as cl
from closed_loop import SETTINGS, Evidence, logit
from datasets import PREP_VERSION, prepare
from e9 import make_gates, tracks
from ledger import state_hash
from models import build_model
from train_central import code_version, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "stage4" / "export"
PRIMARY = "stat_slo"


def deploy_head(d, seed: int, device: str):
    """Train a clean federated detector with the canary gates and return the stat_slo registry-head
    model state (the version the gateway follows) together with the fed result."""
    gates = make_gates(d)
    fed = train_fed("mlp", d, seed, device, k=10, alpha=0.5, gates=gates, attacked_gate=PRIMARY,
                    keep_state=True, keep_rounds=True)
    states = fed.pop("_rounds")
    head = tracks(fed)[f"canary_{PRIMARY}"][-1]          # 0 only if nothing was ever promoted
    state = states[head - 1] if head else fed["_state"]
    return state, head, fed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="edgeiiot")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    mode = SETTINGS[args.dataset]
    d = prepare(args.dataset, mode, args.seed)
    state, head, fed = deploy_head(d, args.seed, args.device)

    model = build_model("mlp", d.input_dim).to(args.device)
    model.load_state_dict(state)
    model_hash = state_hash(model.state_dict())
    s_val = scores(model, torch.from_numpy(d.X_val).to(args.device), False).astype(np.float64)

    # Calibration identical to closed_loop.run: monotone_balanced evidence, Lorden's threshold.
    llr = Evidence(s_val, d.y_val, "monotone_balanced", d.type_val)
    h = float(np.log(cl.T_EV / cl.BUDGET))
    calib = {
        "dataset": args.dataset, "mode": mode, "seed": args.seed, "model": "mlp",
        "input_dim": int(d.input_dim), "feature_names": d.feature_names,
        "deployed_round": int(head), "model_hash": model_hash,
        "llr_mode": "monotone_balanced", "llr_table": llr.table.tolist(), "bins": cl.BINS.tolist(),
        "llr_clip": cl.LLR_CLIP, "h_mode": "lorden", "cusum_h": h, "per_event_threshold": 0.5,
        "rho_min": cl.RHO_MIN, "sprt_a": float(cl.SPRT_A), "sprt_b": float(cl.SPRT_B), "q_max": cl.Q_MAX,
        "backdoor_target": __import__("poison").BACKDOOR_TARGET[args.dataset],
        "t_ev": cl.T_EV, "compromised": cl.COMPROMISED, "tau_range": list(cl.TAU_RANGE), "rhos": list(cl.RHOS),
        "prep_version": PREP_VERSION, "code_version": code_version(), "torch": torch.__version__,
        "detector_val_f1_macro": float(fed["history"][-1]["val_f1_macro"]) if fed.get("history") else None,
    }

    out = OUT / args.dataset if args.seed == 42 else OUT / args.dataset / f"s{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "model.pt")
    (out / "calib.json").write_text(json.dumps(calib, indent=1))
    np.savez_compressed(out / "pool.npz", X=d.X_test.astype(np.float32), y=d.y_test.astype(np.int8),
                        type=d.type_test.astype("<U32"))

    # sanity: the exported table reproduces Evidence.__call__ via plain numpy (what the gateway uses)
    probe = s_val[:256]
    ref = llr(probe)
    idx = np.clip(np.digitize(logit(probe), cl.BINS) - 1, 0, len(calib["llr_table"]) - 1)
    got = np.asarray(calib["llr_table"])[idx]
    assert np.allclose(ref, got), "exported LLR table does not reproduce Evidence"

    print(f"[{args.dataset}/s{args.seed}] deployed round {head} hash {model_hash[:12]} "
          f"dim {d.input_dim} pool {len(d.y_test)} rows ({(d.y_test == 0).sum()} benign) "
          f"target {calib['backdoor_target']}  LLR table ok")


if __name__ == "__main__":
    main()
