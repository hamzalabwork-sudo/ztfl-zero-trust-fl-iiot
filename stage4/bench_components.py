"""Per-event cost of each enforcement component, one CPU thread, for the pillar ablation table.

Replays the gateway's exact per-event path (gateway/app.py) on 5,000 held-out events of each dataset's
deployed bundle: (1) detector scoring of one event; (2) evidence + per-device CUSUM/SPRT authorizer
step (10 devices); (3) appending one local hash-chain record per 100 decisions (amortized per event).
The on-chain write is a queue put measured in the testbed (E10-chain / E12), added from those results.
Client-side Zero Trust (gate, attribution) runs on the server once per round, not per event.

  python bench_components.py        # -> results/bench_components.json
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src")); sys.path.insert(0, str(HERE))
from common import DeviceAuthorizer, Evidence  # noqa: E402
from ledger import MemoryLedger, batch_digest  # noqa: E402
from models import build_model  # noqa: E402

N, REPS, N_DEV, BATCH = 5000, 5, 10, 100


def bench(ds: str) -> dict:
    exp = HERE / "export" / ds
    calib = json.loads((exp / "calib.json").read_text())
    model = build_model(calib["model"], calib["input_dim"])
    model.load_state_dict(torch.load(exp / "model.pt", map_location="cpu")); model.eval()
    X = np.load(exp / "pool.npz")["X"]
    rows = X[np.random.default_rng(0).choice(len(X), N, replace=False)].tolist()
    ev = Evidence(calib)
    det, auth, led = [], [], []
    for _ in range(REPS + 1):                                   # first repetition is warm-up
        t0 = time.perf_counter(); scores = []
        for v in rows:
            x = torch.tensor([v], dtype=torch.float32)
            with torch.no_grad():
                scores.append(torch.softmax(model(x), dim=1)[0, 1].item())
        t1 = time.perf_counter()
        auths = [DeviceAuthorizer(calib) for _ in range(N_DEV)]
        out = [auths[i % N_DEV].step(s, float(ev(s))) for i, s in enumerate(scores)]
        t2 = time.perf_counter()
        ml = MemoryLedger()
        for k in range(0, N, BATCH):
            chunk = out[k:k + BATCH]
            ml.record_decisions("0" * 64, "bench", 0, len(chunk), len(chunk),
                                batch_digest(np.array([a["granted"] for a in chunk]),
                                             np.array([a["admitted"] for a in chunk])))
        t3 = time.perf_counter()
        det.append((t1 - t0) / N); auth.append((t2 - t1) / N); led.append((t3 - t2) / N)
    ms = lambda xs: 1e3 * st.median(xs[1:])
    return {"detector_ms": ms(det), "authorizer_ms": ms(auth), "local_ledger_ms": ms(led)}


def main() -> None:
    torch.set_num_threads(1)
    res = HERE / "results"
    chain = {"local_evm_us_per_record": json.loads((res / "chain_summary.json").read_text())["totals"]["enqueue_us_per_write_median"]}
    live = res / "chain_summary_purechain.json"
    if live.exists():
        chain["purechain_us_per_record"] = json.loads(live.read_text())["totals"]["enqueue_us_per_write_median"]
    out = {"setup": {"events": N, "repetitions": REPS, "devices": N_DEV, "torch_threads": 1, "batch": BATCH},
           "onchain_write_queue_put": chain,
           "datasets": {ds: bench(ds) for ds in ("edgeiiot", "forge", "wustl")}}
    (res / "bench_components.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
