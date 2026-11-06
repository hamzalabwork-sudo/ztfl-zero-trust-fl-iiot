"""Summarise E9 (results/e9/trust, full system) against its no-attribution baselines.

Baselines, all on the same seeds and federations:
- non-adaptive attacks: the E8 runs (training is identical until the first revocation) scored by
  replay_gates.py (results/defense_replay: tracks best, last, e8_d0.05, stat_slo);
- backdoor_adaptive vs stat_slo: results/e9/pilot (seeds 43-46 from scripts/e9_pilot_adaptive_queue.sh,
  42 from the pilot).
Seed 42 is the design seed of the attribution rule; seeds 43-46 are the evaluation and are
reported separately.

Per run: final backdoor success / excess, exposure, no-model rounds, revocations (true / false),
round of the first true revocation, and gateway grants (target streams, cusum_sprt_mix, both
evidence models). Writes results/e9/summary.md and results/e9/summary_long.csv.
Usage: python src/summarize_e9.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E9 = ROOT / "results" / "e9"
KEYS = ["dataset", "attack", "n_malicious", "aggregator", "onset", "seed"]


def load_e9(variant: str) -> pd.DataFrame:
    rows = []
    for p in sorted((E9 / variant).glob("*_m[0-9]_on*/*/*/*/mlp_s*.json")):
        r = json.loads(p.read_text())
        base = {k: r[k] for k in KEYS} | {"variant": variant}
        bad, rev = set(r["malicious"]), r["revoked"]
        tl = (r.get("trust") or {}).get("log", [])
        first_true = min((x["round"] for x in tl for c in x.get("revoked", []) if c in bad), default=None)
        for track, det in r["detector"].items():
            ex = r["exposure"][track]
            row = base | {"track": track, "bd": det.get("backdoor_success", 0.0), "f1": det.get("f1_macro", np.nan),
                          "round": det["round"], "bd_exp_max": ex["backdoor_success_max"],
                          "no_model_rounds": ex["no_model_rounds"], "stale": ex["stale_rounds_final"],
                          "revoked_true": len(set(rev) & bad), "revoked_false": len(set(rev) - bad),
                          "first_true_revocation": first_true, "head_ok": r["ledger"]["gateway_runs_registry_head"],
                          "ledger_ok": r["ledger"]["verified"] and sorted(r["ledger"]["revoked_on_ledger"]) == sorted(rev)}
            for llr, acc in r["access"].get(track, {}).items():
                for rho in ("rho1", "rho0.2"):
                    row[f"wrong:{llr}/{rho}"] = acc[f"target/{rho}"]["cusum_sprt_mix"]["wrongful_grant_rate"]
                    row[f"fiso:{llr}/{rho}"] = acc[f"all/{rho}"]["cusum_sprt_mix"]["false_isolation_rate"]
            rows.append(row)
    return pd.DataFrame(rows)


def load_replay() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "defense_replay" / "summary_long.csv")
    df = df[df.rule.isin(["best", "last", "e8_d0.05", "stat_slo"]) & df.aggregator.isin(["fedavg", "multi_krum"])].copy()
    df["track"] = df.rule.map({"best": "best", "last": "last", "e8_d0.05": "canary_e8", "stat_slo": "canary_stat_slo"})
    return df.assign(variant="baseline")[KEYS + ["variant", "track", "bd", "f1", "bd_exp_max", "no_model_rounds", "stale"]]


def md(df: pd.DataFrame) -> str:
    """Markdown table without the tabulate dependency (flattens column tuples)."""
    cols = [" / ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]
    names = [str(n) for n in df.index.names]
    out = ["| " + " | ".join(names + cols) + " |", "|---" * (len(names) + len(cols)) + "|"]
    for idx, row in df.iterrows():
        idx = idx if isinstance(idx, tuple) else (idx,)
        out.append("| " + " | ".join([str(i) for i in idx] + ["" if pd.isna(v) else f"{v:g}" for v in row]) + " |")
    return "\n".join(out)


def with_excess(df: pd.DataFrame) -> pd.DataFrame:
    clean = df[df.attack == "none"].groupby(["dataset", "aggregator", "seed", "track", "variant"]).bd.mean()
    df = df.join(clean.rename("bd_clean"), on=["dataset", "aggregator", "seed", "track", "variant"])
    df["bd_excess"] = df.bd - df.bd_clean
    return df


def main() -> None:
    trust = load_e9("trust")
    pilot = load_e9("pilot")
    base = pd.concat([load_replay(), pilot[pilot.attack == "backdoor_adaptive"].assign(variant="baseline")
                      [KEYS + ["variant", "track", "bd", "f1", "bd_exp_max", "no_model_rounds", "stale"]]])
    # clean reference for the baseline: E8 none runs (replay); E9 trust: its own none runs
    df = with_excess(pd.concat([trust, base], ignore_index=True))
    df.to_csv(E9 / "summary_long.csv", index=False)
    out = [f"# E9 summary\n\ntrust runs: {trust.groupby(KEYS).ngroups}; ledger ok {int(trust.groupby(KEYS).ledger_ok.first().sum())}, "
          f"gateway on registry head {int(trust.groupby(KEYS).head_ok.first().sum())}.\n"]
    for split, seeds in (("evaluation seeds 43-46", [43, 44, 45, 46]), ("design seed 42", [42])):
        x = df[df.seed.isin(seeds) & (df.track.isin(["last", "canary_stat_slo"]))]
        out.append(f"\n## {split}\n")
        for value, title in (("bd_excess", "backdoor success excess, final deployed model (pp)"),
                             ("bd_exp_max", "exposure: max backdoor success while deployed (%)")):
            p = (x.pivot_table(index=["dataset", "attack", "onset", "aggregator"], columns=["track", "variant"],
                               values=value, aggfunc="mean") * 100).round(1)
            out.append(f"\n**{title}** (m 1-3 pooled)\n\n" + md(p) + "\n")
        t = df[df.seed.isin(seeds) & (df.variant == "trust") & (df.track == "canary_stat_slo")]
        g = t.groupby(["dataset", "attack", "onset", "aggregator"]).agg(
            runs=("bd", "size"), attackers=("n_malicious", "sum"), revoked_true=("revoked_true", "sum"),
            revoked_false=("revoked_false", "sum"), first_true_mean=("first_true_revocation", "mean"),
            no_model_rounds=("no_model_rounds", "mean"))
        out.append("\n**revocations (full system)**\n\n" + md(g.round(2)) + "\n")
        w = t.groupby(["dataset", "attack", "onset", "aggregator"])[[c for c in t.columns if c.startswith("wrong:")]].mean() * 100
        out.append("\n**gateway, target streams, attack events granted % (full system, deployed head)**\n\n" + md(w.round(2)) + "\n")
    (E9 / "summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out)[:6000])


if __name__ == "__main__":
    main()
