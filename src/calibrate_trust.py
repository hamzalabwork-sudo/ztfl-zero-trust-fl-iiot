"""E9 -- calibrate the client CUSUM (client_trust.py) on the seed-42 pilot, then freeze it.

The pilot logged, every round, the LOO canary profile of every client with nothing revoked.
1. Per (dataset, aggregator) and type: s_t = max(q99 of honest D_t over the no-attack runs from
   round START on, 2 canary rows) -- the in-control noise an operator can measure on a clean
   federation.
2. For each (KAPPA, START) on a grid, the CUSUM is replayed offline on every client:
   H = H_MARGIN x the highest CUSUM value any client reaches in the no-attack runs; score = share
   of attacker clients alarmed within WINDOW rounds of the onset minus the share of honest clients
   in attack runs falsely alarmed; ties -> earlier mean alarm, then larger KAPPA.
One (KAPPA, START, H) for all datasets. Writes results/e9/trust_calibration.json.

v1 (unscaled harm, KAPPA grid 0-0.05; results/e9/trust_calibration_v1.json, script kept as
results/e9/calibrate_trust_v1.py.txt) chose KAPPA 0.05, START 6, H 2.04: 11% of attackers caught
within 10 rounds, 16 false revocations. v2 (scaled, no round median; trust_calibration_v2.json):
37% caught, 117 false revocations. v3 (minus the round median; _v3.json): 38%, 144. This script
now calibrates v4 = v3 with winsorised increments (CLIP grid). All before any evaluation run.
Usage: python src/calibrate_trust.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from client_trust import changes

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "results" / "e9" / "pilot"
SIZES = ROOT / "results" / "defense_replay" / "sizes.json"   # canary sizes per dataset (seed 42)
KAPPAS = (0.5, 1.0, 1.5, 2.0, 3.0)
CLIPS = (2.0, 3.0, 5.0, float("inf"))
STARTS = (2, 6)
H_MARGIN = 1.25
WINDOW = 10
FLOOR_ROWS = 2


def load() -> list[dict]:
    runs = []
    for p in sorted(PILOT.glob("*_m[0-9]_on*/*/*/*/mlp_s42.json")):
        r = json.loads(p.read_text())
        D = [{int(i): changes(c["agg"]["loo_full"], l) for i, l in c["agg"]["loo"].items()} for c in r["curve"]]
        runs.append({k: r[k] for k in ("dataset", "attack", "n_malicious", "aggregator", "onset", "malicious")} | {"D": D})
    return runs


def scales(runs: list[dict], start: int) -> dict[str, dict[str, float]]:
    sizes = json.loads(SIZES.read_text())
    out = {}
    for key in sorted({(r["dataset"], r["aggregator"]) for r in runs}):
        n_t, n_b = sizes[f"{key[0]}_s42"]
        clean = [r for r in runs if (r["dataset"], r["aggregator"]) == key and r["attack"] == "none"]
        s = {}
        for t in clean[0]["D"][0][0]:
            v = [D[i][t] for r in clean for D in r["D"][start - 1:] for i in D]
            floor = FLOOR_ROWS / (n_b if t == "benign" else n_t[t])
            s[t] = float(max(np.quantile(v, 0.99), floor))
        out[f"{key[0]}/{key[1]}"] = s
    return out


def paths(run: dict, scale: dict, kappa: float, start: int, clip: float) -> dict[int, np.ndarray]:
    S, out = {}, {i: [] for i in run["D"][0]}
    for rnd, Dr in enumerate(run["D"], 1):
        z = {i: {t: v / scale[t] for t, v in d.items()} for i, d in Dr.items()}
        med = {t: float(np.median([zi[t] for zi in z.values()])) for t in scale}
        for i, zi in z.items():
            if rnd >= start:
                S[i] = max(0.0, S.get(i, 0.0) + min(max(zi[t] - med[t] for t in zi), clip) - kappa)
            out[i].append(S.get(i, 0.0))
    return {i: np.array(v) for i, v in out.items()}


def evaluate(runs, sc, kappa, start, clip, h=None):
    P = [paths(r, sc[f"{r['dataset']}/{r['aggregator']}"], kappa, start, clip) for r in runs]
    honest = max(p[i].max() for r, p in zip(runs, P) if r["attack"] == "none" for i in p)
    h = H_MARGIN * honest if h is None else h
    alarms, false_rev, n_honest, det = [], 0, 0, []
    for r, p in zip(runs, P):
        if r["attack"] == "none":
            continue
        false_rev += sum(p[i].max() >= h for i in p if i not in r["malicious"])
        n_honest += sum(i not in r["malicious"] for i in p)
        for i in r["malicious"]:
            hit = np.flatnonzero(p[i] >= h)
            alarms.append(int(hit[0]) + 1 - r["onset"] if len(hit) else np.inf)
            det.append({k: r[k] for k in ("dataset", "attack", "aggregator", "n_malicious", "onset")}
                       | {"client": i, "alarm_round": int(hit[0]) + 1 if len(hit) else None})
    a = np.array(alarms)
    return {"kappa": kappa, "start": start, "clip": clip, "honest_max": honest, "h": h, "false_revocations": false_rev,
            "score": float(np.mean(a < WINDOW)) - false_rev / n_honest, "caught_in_window": float(np.mean(a < WINDOW)),
            "caught_ever": float(np.mean(np.isfinite(a))),
            "delay_mean": float(np.mean(a[np.isfinite(a)])) if np.isfinite(a).any() else np.nan}, pd.DataFrame(det)


def main() -> None:
    runs = load()
    print(f"{len(runs)} pilot runs")
    rows, sc_by_start = [], {s: scales(runs, s) for s in STARTS}
    for kappa in KAPPAS:
        for start in STARTS:
            for clip in CLIPS:
                if clip > kappa:
                    rows.append(evaluate(runs, sc_by_start[start], kappa, start, clip)[0])
    df = pd.DataFrame(rows).sort_values(["score", "delay_mean", "kappa"], ascending=[False, True, False])
    print(df.to_string(index=False))
    best = df.iloc[0]
    sc = sc_by_start[int(best.start)]
    cal = {"version": 4, "kappa": float(best.kappa), "start": int(best.start), "clip": float(best.clip), "h": float(best.h), "h_margin": H_MARGIN,
           "honest_max": float(best.honest_max), "floor_rows": FLOOR_ROWS, "pilot_runs": len(runs), "seed": 42,
           "scale": sc, "grid": df.to_dict(orient="records")}
    (ROOT / "results" / "e9" / "trust_calibration.json").write_text(json.dumps(cal, indent=1))
    _, det = evaluate(runs, sc, cal["kappa"], cal["start"], cal["clip"], cal["h"])
    print(det.groupby(["dataset", "attack", "aggregator", "onset"]).alarm_round
          .agg(caught=lambda s: f"{s.notna().sum()}/{len(s)}", first=lambda s: s.min()).to_string())
    print("chosen:", {k: v for k, v in cal.items() if k not in ("grid", "scale")})
    print(json.dumps(sc)[:1500])


if __name__ == "__main__":
    main()
