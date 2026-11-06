"""R1b -- backdoor success on UNSEEN test rows (strictest evaluation-leakage check).

A reviewer following BackFed (arXiv:2507.04903) can ask whether our reported backdoor
success is inflated by train/test *pattern* overlap: target-type test rows whose exact
cleaned feature vector also occurs in training (`test_seen==True`) could be memorised
rather than genuinely backdoored. `datasets.py` already flags each test row seen/unseen.

This script trains the worst-case (full-budget) FedAvg backdoor exactly as E7/E9 do
(m=3, onset=1) plus a clean baseline, takes the undefended final-round ("last") model,
and reports backdoor success and excess-over-clean on ALL target-type test rows vs the
UNSEEN subset only. If the unseen excess matches the overall excess, the headline numbers
are genuine generalisation, not seen-row memorisation.

Results: results/r1b/<dataset>/s<seed>.json
Usage: python src/r1b.py --datasets edgeiiot,forge,wustl --seeds 42,43,44,45,46
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from closed_loop import SETTINGS
from datasets import PREP_VERSION, prepare
from models import build_model
from poison import BACKDOOR_TARGET
from train_central import code_version, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "r1b"


def last_model_scores(d, attack: str, seed: int, device: str) -> np.ndarray:
    """Scores on the test set from the undefended final-round model (same path as E7/E9)."""
    fed = train_fed("mlp", d, seed, device, k=10, alpha=0.5, keep_state=True, attack=attack,
                    n_malicious=3, aggregator="fedavg", onset=1)
    model = build_model("mlp", d.input_dim).to(device)
    model.load_state_dict(fed["_last_state"])
    Xte = torch.from_numpy(d.X_test).to(device)
    return scores(model, Xte, False).astype(np.float64)


def bd_success(s: np.ndarray, mask: np.ndarray, thr: float = 0.5) -> float:
    """Share of masked target-type rows scored benign (== backdoor success)."""
    if not mask.any():
        return float("nan")
    return float((s[mask] < thr).mean())


def run(d, seed: int, device: str) -> dict:
    t0 = time.perf_counter()
    target = BACKDOOR_TARGET[d.dataset]
    tgt = d.type_test == target
    seen = d.test_seen.astype(bool)
    masks = {"all": tgt, "seen": tgt & seen, "unseen": tgt & ~seen}

    s_bd = last_model_scores(d, "backdoor", seed, device)
    s_cl = last_model_scores(d, "none", seed, device)

    out = {"n_target": {k: int(m.sum()) for k, m in masks.items()}}
    for split, m in masks.items():
        bd, cl = bd_success(s_bd, m), bd_success(s_cl, m)
        out[split] = {"backdoor_success": bd, "clean_baseline": cl, "excess": bd - cl}
    return out | {"wall_seconds": time.perf_counter() - t0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    version = code_version()
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            out = OUT / ds / f"s{seed}.json"
            if out.exists():
                continue
            d = prepare(ds, SETTINGS[ds], seed)
            res = run(d, seed, args.device)
            res.update(dataset=ds, mode=SETTINGS[ds], seed=seed, backdoor_target=BACKDOOR_TARGET[ds],
                       prep_version=PREP_VERSION, code_version=version, torch=torch.__version__,
                       device=args.device, host=platform.node())
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(res, indent=1))
            a, u = res["all"], res["unseen"]
            print(f"[r1b/{ds}/s{seed}] bd all/unseen={a['backdoor_success']:.3f}/{u['backdoor_success']:.3f} "
                  f"excess all/unseen={a['excess']:.3f}/{u['excess']:.3f} "
                  f"n_unseen={res['n_target']['unseen']} ({res['wall_seconds']:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
