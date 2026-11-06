"""R3 -- multi-seed emulated testbed (E10 robustness).

E10 headline results are seed 42 only. A reviewer can ask whether the end-to-end testbed
behaviour is a single-seed artifact. This driver reruns the headline attacked configuration
(m=2 compromised devices, rho=1.0, t_ev=500) for seeds 43-46 across all three datasets,
using the seed-specific export bundles (export/<dataset>/s<seed>/, built by export_testbed.py),
and prints the access-control metrics next to the seed-42 run.

Needs: Docker Desktop up; the ztfl-stage4 image built; export bundles for each seed present.
Usage: py -3.13 run_r3.py                 # all datasets, seeds 43-46
       py -3.13 run_r3.py --datasets forge --seeds 43,44
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = ("wrongful_grant_rate", "detection_rate", "tti_median", "false_isolation_rate",
           "false_reauth_rate", "lateral_reach_mean")


def run_name(ds: str, seed: int) -> str:
    return f"e10_{ds}_m2_rho1.0" + ("" if seed == 42 else f"_s{seed}")


def load_metrics(ds: str, seed: int) -> dict | None:
    p = HERE / "results" / f"{run_name(ds, seed)}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text()).get("metrics")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--seeds", default="43,44,45,46")
    ap.add_argument("--summary-only", action="store_true", help="skip running; just tabulate existing results")
    args = ap.parse_args()
    datasets = args.datasets.split(",")
    seeds = [int(s) for s in args.seeds.split(",")]

    if not args.summary_only:
        for ds in datasets:
            for seed in seeds:
                if load_metrics(ds, seed) is not None:
                    print(f"[skip] {run_name(ds, seed)} already present", flush=True)
                    continue
                bundle = HERE / "export" / ds / f"s{seed}" / "calib.json"
                if not bundle.exists():
                    print(f"[MISSING BUNDLE] {bundle} -- export it first; skipping", file=sys.stderr, flush=True)
                    continue
                cmd = [sys.executable, str(HERE / "run_e10.py"), "--dataset", ds, "--seed", str(seed),
                       "--m", "2", "--rho", "1.0", "--t-ev", "500", "--run", run_name(ds, seed)]
                print(f"[run] {' '.join(cmd[2:])}", flush=True)
                r = subprocess.run(cmd, cwd=HERE)
                if r.returncode != 0:
                    print(f"[FAILED] {run_name(ds, seed)} exit {r.returncode}", file=sys.stderr, flush=True)

    # tabulate: seed 42 baseline then 43-46 per dataset
    print("\n# R3 -- multi-seed testbed (m=2, rho=1.0, t_ev=500)\n")
    hdr = "| dataset | seed | " + " | ".join(METRICS) + " |"
    print(hdr)
    print("|" + "---|" * (len(METRICS) + 2))
    for ds in datasets:
        for seed in [42] + seeds:
            m = load_metrics(ds, seed)
            if m is None:
                continue
            cells = " | ".join(f"{m.get(k):.3f}" if isinstance(m.get(k), (int, float)) else str(m.get(k))
                               for k in METRICS)
            print(f"| {ds} | {seed} | {cells} |")
        print("|" + "---|" * (len(METRICS) + 2))


if __name__ == "__main__":
    main()
