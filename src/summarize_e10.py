"""Summarise the Stage 4 (E10) emulated-testbed runs in stage4/results/*.json.

Each run is one live MQTT session (one dataset, N devices, m compromised, attack rate rho, ledger
backend). The gateway scored every event with the deployed final-system detector and enforced the
cusum_sprt_mix policy. This prints the access-control metrics next to the simulated closed-loop
numbers (E5/E9) for the same policy, and the ledger / latency facts that only the real testbed
gives (detector ms per event, chain write latency, hash-chain verification).

Usage: python src/summarize_e10.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "stage4" / "results"
COLS = [("rho", "rho"), ("m", "n_compromised"), ("wrong grant", "wrongful_grant_rate"),
        ("detect", "detection_rate"), ("tti med", "tti_median"), ("false iso", "false_isolation_rate"),
        ("false reauth", "false_reauth_rate"), ("reach", "lateral_reach_mean"),
        ("benign deny", "benign_denial_rate")]


def fmt(v) -> str:
    if v is None:
        return "-"
    return f"{v:.3g}" if isinstance(v, float) else str(v)


def main() -> None:
    runs = []
    for p in sorted(RES.glob("*.json")):
        if p.stem.endswith("_sessions"):
            continue
        d = json.loads(p.read_text())
        m = d["metrics"]
        runs.append((p.stem, d, m))
    if not runs:
        print("no E10 result files in", RES)
        return

    out = ["# E10 -- emulated testbed (Stage 4) summary\n",
           f"{len(runs)} live sessions. Detector = deployed final-system model (stat_slo registry head); "
           "policy = cusum_sprt_mix; evidence = monotone_balanced; threshold = Lorden h.\n",
           "\n## Access-control outcomes (real per-device MQTT sessions)\n",
           "| run | " + " | ".join(c[0] for c in COLS) + " |",
           "|---" * (len(COLS) + 1) + "|"]
    for name, d, m in runs:
        vals = {"rho": d.get("run", "").split("rho")[-1].split("_")[0] if "rho" in name else "", **m}
        out.append("| " + name + " | " + " | ".join(fmt(vals.get(k)) for _, k in COLS) + " |")

    out.append("\n## Testbed facts (not available in simulation)\n")
    out.append("| run | events | detector ms/event | ledger blocks | chain | verified | wall s |")
    out.append("|---|---|---|---|---|---|---|")
    for name, d, m in runs:
        ch = d.get("chain", {})
        chain = ch.get("backend", "?")
        if chain == "evm" and "decisions" in ch:
            chain = f"evm {ch['decisions'].get('latency_median_s', '?')}s/batch"
        out.append(f"| {name} | {d['events_total']} | {d['score_ms_per_event']:.3f} | "
                   f"{d['ledger']['blocks']} | {chain} | {d['ledger']['verified']} | {d['session_wall_seconds']:.1f} |")

    text = "\n".join(out)
    (RES / "summary.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
