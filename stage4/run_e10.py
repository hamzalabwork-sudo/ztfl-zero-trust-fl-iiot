"""Stage 4 (E10) runner (laptop, Docker Desktop). Generates a compose file with a broker, the
gateway and N device containers (each its own network identity), brings it up, waits for the
gateway to finish and tears it down. The last N-m devices are compromised with the dataset's
backdoor target type from a per-device onset tau.

  py -3.13 run_e10.py --dataset edgeiiot --n-dev 10 --m 2 --rho 1.0 --t-ev 500 --run e10_edge_m2

Needs stage4/export/<dataset>/ (build it with export_testbed.py). Results land in stage4/results/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "ztfl-stage4:1.0"


def svc_device(i: int, role: str, tau: int, rho: float, atk: str, args) -> str:
    env = {"DEVICE_ID": i, "N_DEV": args.n_dev, "SEED": args.seed, "ROLE": role, "TAU": tau,
           "RHO": rho, "ATTACK_TYPE": atk, "T_EV": args.t_ev, "TICK": args.tick, "BROKER": "broker"}
    lines = "\n".join(f"      {k}: \"{v}\"" for k, v in env.items())
    return f"""  device-{i}:
    image: {IMAGE}
    command: ["python", "device_app.py"]
    depends_on: [broker]
    restart: "no"
    cpus: 0.5
    mem_limit: 512m
    volumes:
      - ./export/{args.exp}:/export:ro
    environment:
{lines}
"""


def compose(args, compromised: dict[int, int], atk: str) -> str:
    anvil = """  anvil:
    image: ghcr.io/foundry-rs/foundry:v1.8.4
    entrypoint: ["anvil", "--host", "0.0.0.0", "--port", "18545", "--block-time", "2", "--silent"]
""" if args.ledger == "evm" else ""
    gw_dep = "[broker, anvil]" if args.ledger == "evm" else "[broker]"
    gw_limits = f"\n    cpus: {args.gateway_cpus}\n    mem_limit: {args.gateway_mem}" if args.gateway_cpus else ""
    gw_threads = (f"\n      OMP_NUM_THREADS: \"{args.gateway_threads}\""
                  f"\n      MKL_NUM_THREADS: \"{args.gateway_threads}\"") if args.gateway_threads else ""
    devices = "".join(svc_device(i, "compromised" if i in compromised else "benign",
                                  compromised.get(i, args.t_ev), args.rho, atk, args)
                      for i in range(args.n_dev))
    return f"""name: ztfl-e10

services:
  broker:
    image: eclipse-mosquitto:2
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
{anvil}  gateway:
    image: {IMAGE}
    build: .
    command: ["python", "gateway_app.py"]
    depends_on: {gw_dep}{gw_limits}
    volumes:
      - ./export/{args.exp}:/export:ro
      - ./results:/results
      - ../src:/src:ro
      - ../contracts:/app/contracts:ro
    environment:
      RUN: "{args.run}"
      N_DEV: "{args.n_dev}"
      T_EV: "{args.t_ev}"
      LEDGER: "{args.ledger}"
      RPC: "http://anvil:18545"
      BROKER: "broker"
      GATEWAY_CPUS: "{args.gateway_cpus or ''}"{gw_threads}
{devices}"""


def dc(*cmd: str, **kw):
    return subprocess.run(["docker", "compose", "-f", str(HERE / "docker-compose.gen.yml"), *cmd],
                          cwd=HERE, **kw)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="edgeiiot")
    ap.add_argument("--n-dev", type=int, default=10)
    ap.add_argument("--m", type=int, default=2, help="compromised devices (the last m)")
    ap.add_argument("--rho", type=float, default=1.0)
    ap.add_argument("--t-ev", type=int, default=500)
    ap.add_argument("--tick", type=float, default=0.03)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ledger", choices=["memory", "evm"], default="memory")
    ap.add_argument("--gateway-cpus", default=None, help="constrain the gateway to N cpus (Pi stand-in, e.g. 1.0)")
    ap.add_argument("--gateway-mem", default="1g", help="gateway memory limit when --gateway-cpus is set")
    ap.add_argument("--gateway-threads", default="", help="OMP/MKL threads in the gateway (empty = torch default)")
    ap.add_argument("--run", default=None)
    args = ap.parse_args()
    args.run = args.run or f"e10_{args.dataset}_m{args.m}_rho{args.rho:g}_{args.ledger}"
    # seed 42 stays at export/<dataset>/ (validated bundle); other seeds under s<seed>/ (R3)
    args.exp = args.dataset if args.seed == 42 else f"{args.dataset}/s{args.seed}"

    calib = json.loads((HERE / "export" / args.exp / "calib.json").read_text())
    atk, (lo, hi) = calib["backdoor_target"], calib["tau_range"]
    import numpy as np
    rng = np.random.default_rng([args.seed, 9])
    compromised = {i: int(rng.integers(lo, hi)) for i in range(args.n_dev - args.m, args.n_dev)}

    (HERE / "docker-compose.gen.yml").write_text(compose(args, compromised, atk))
    print(f"[run] {args.run}: {args.n_dev} devices, {args.m} compromised {sorted(compromised)} "
          f"type={atk} rho={args.rho} tau={compromised}", flush=True)
    (HERE / "results").mkdir(exist_ok=True)
    result = HERE / "results" / f"{args.run}.json"
    if result.exists():
        result.unlink()

    dc("up", "-d", "--build", check=True)
    try:
        gid = dc("ps", "-q", "gateway", capture_output=True, text=True).stdout.strip()
        deadline = time.time() + args.t_ev * args.tick * 2 + 240
        while time.time() < deadline:
            st = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", gid],
                                capture_output=True, text=True).stdout.strip()
            if st in ("exited", "dead"):
                break
            time.sleep(2)
        else:
            print("[run] TIMEOUT waiting for gateway", file=sys.stderr)
        dc("logs", "--no-color", "--tail", "40", "gateway")
    finally:
        dc("down", "-v", "-t", "3")

    if result.exists():
        m = json.loads(result.read_text())["metrics"]
        print(f"\n[run] {args.run} metrics:\n" + json.dumps(m, indent=1))
    else:
        print(f"[run] no result file at {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
