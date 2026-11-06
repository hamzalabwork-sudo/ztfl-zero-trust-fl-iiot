"""Summarise E5d (results/closed_loop/curves/): operating-curve tables, an equal-false-isolation
comparison, the per-attack-type breakdown, and figures.

Writes curves/summary.md, curves/operating_curves_tti.png, curves/operating_curves_wrongful.png.
Usage: python src/summarize_curves.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "closed_loop" / "curves"
POLICIES = {"ewma": ("EWMA trust", "#2a78d6", "o"), "cusum": ("CUSUM", "#eb6834", "s"),
            "cusum_sprt_mix": ("CUSUM + mixture SPRT", "#1baf7a", "^")}
BUDGET = 0.01


def load(res: Path = RES):
    runs = [json.loads(p.read_text()) for p in sorted(res.glob("*/*/*_s[0-9]*.json"))]
    pts, pev, types = [], [], []
    for r in runs:
        base = {"dataset": r["dataset"], "seed": r["seed"]}
        for rho, per in r["curves"].items():
            for policy, rows in per.items():
                for m in rows:
                    (pev if policy == "per_event" else pts).append(base | {"rho": rho, "policy": policy, **m})
        for rho, per in r["per_type"].items():
            for policy, tps in per.items():
                for at, m in tps.items():
                    types.append(base | {"rho": rho, "policy": policy, "attack_type": at, **m})
    return runs, pd.DataFrame(pts), pd.DataFrame(pev), pd.DataFrame(types)


def equal_budget(pts: pd.DataFrame) -> pd.DataFrame:
    """Per seed: the threshold with the lowest wrongful-grant rate among those with realised test
    false isolation <= BUDGET (ties: faster isolation). Uses test data -> analysis only."""
    ok = pts[pts.false_isolation_rate <= BUDGET].sort_values(["wrongful_grant_rate", "tti_median"])
    best = ok.groupby(["dataset", "rho", "policy", "seed"], sort=False).head(1)
    return best.groupby(["dataset", "rho", "policy"])[["threshold", "false_isolation_rate", "wrongful_grant_rate",
                                                       "detection_rate", "tti_median", "lateral_reach_mean"]].mean()


def figure(pts: pd.DataFrame, marks: dict, y: str, ylabel: str, path: Path, logy: bool = False) -> None:
    dsets, rhos = sorted(pts.dataset.unique()), ["rho1", "rho0.5", "rho0.2"]
    fig, axes = plt.subplots(len(dsets), len(rhos), figsize=(11, 3.1 * len(dsets)), sharex=True, squeeze=False)
    mean = pts.groupby(["dataset", "rho", "policy", "threshold"])[["false_isolation_rate", y]].mean().reset_index()
    for i, ds in enumerate(dsets):
        for j, rho in enumerate(rhos):
            ax = axes[i][j]
            for policy, (label, color, marker) in POLICIES.items():
                c = mean[(mean.dataset == ds) & (mean.rho == rho) & (mean.policy == policy)].sort_values("false_isolation_rate")
                ax.plot(c.false_isolation_rate * 100, c[y] * (100 if y != "tti_median" else 1), color=color, lw=2,
                        marker=marker, ms=6, mec="white", mew=1, label=label)
                if policy == "cusum_sprt_mix":  # mark Lorden's threshold
                    lo = c[np.isclose(c.threshold, marks["cusum_lorden"])]
                    ax.plot(lo.false_isolation_rate * 100, lo[y] * (100 if y != "tti_median" else 1), "o", ms=13,
                            mfc="none", mec="#3d3d3a", mew=1.5, label="Lorden h = 10.82")
            ax.axvline(BUDGET * 100, color="#8a8a85", lw=1, ls="--")
            ax.set_xscale("symlog", linthresh=0.1)
            if logy:
                ax.set_yscale("log")
            ax.grid(True, color="#e6e5e0", lw=0.8)
            ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            ax.set_title(f"{ds}, rho = {rho[3:]}", fontsize=10, color="#3d3d3a")
            if i == len(dsets) - 1:
                ax.set_xlabel("benign devices falsely isolated (%, test)")
            if j == 0:
                ax.set_ylabel(ylabel)
    h, lab = axes[0][0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def md_table(df: pd.DataFrame, pct: set[str]) -> list[str]:
    cols = list(df.columns)
    lines = ["| " + " | ".join(df.index.names) + " | " + " | ".join(cols) + " |", "|---" * (len(cols) + df.index.nlevels) + "|"]
    for idx, row in df.iterrows():
        idx = idx if isinstance(idx, tuple) else (idx,)
        cells = [f"{row[c] * 100:.2f}" if c in pct else ("-" if pd.isna(row[c]) else f"{row[c]:.2f}") for c in cols]
        lines.append("| " + " | ".join(map(str, idx)) + " | " + " | ".join(cells) + " |")
    return lines


if __name__ == "__main__":
    runs, pts, pev, types = load()
    marks = defaultdict(list)
    for r in runs:
        for k, v in r["marks"].items():
            marks[k].append(v)
    marks = {k: float(np.mean(v)) for k, v in marks.items()}
    out = [f"# E5d operating curves ({len(runs)} runs; detector matches E5c: "
           f"{sum(r['detector'].get('matches_e5c', False) for r in runs)}/{len(runs)})", ""]
    out += ["## Equal realised false isolation (<= 1% on test; oracle threshold, analysis only)", ""]
    out += md_table(equal_budget(pts), {"false_isolation_rate", "wrongful_grant_rate", "detection_rate"}) + [""]
    pe = pev.groupby(["dataset", "rho", "threshold"])[["wrongful_grant_rate", "benign_denial_rate"]].mean()
    out += ["## per_event: score threshold vs wrongful grants and benign denial", ""]
    out += md_table(pe, {"wrongful_grant_rate", "benign_denial_rate"}) + [""]
    cur = pts.groupby(["dataset", "rho", "policy", "threshold"])[["false_isolation_rate", "detection_rate", "tti_median",
                                                                   "wrongful_grant_rate", "false_reauth_rate"]].mean()
    out += ["## Full curves (mean over seeds)", ""]
    out += md_table(cur, {"false_isolation_rate", "detection_rate", "wrongful_grant_rate", "false_reauth_rate"}) + [""]
    ty = types[types.rho.isin(["rho1", "rho0.2"])].pivot_table(
        index=["dataset", "attack_type", "rho"], columns="policy",
        values=["device_isolated_rate", "wrongful_grant_rate"], aggfunc="mean")
    ty.columns = [f"{a}:{b}" for a, b in ty.columns]
    ev = types[(types.rho == "rho1") & (types.policy == "per_event")].groupby(["dataset", "attack_type"])[
        ["event_detect_rate", "llr_nonpositive_share"]].mean()
    ty = ty.join(ev, on=["dataset", "attack_type"])
    out += ["## Per attack type (cusum_sprt_mix at Lorden's h; per_event at 0.5)", ""]
    out += md_table(ty, set(ty.columns)) + [""]
    (RES / "summary.md").write_text("\n".join(out), encoding="utf-8")
    figure(pts, marks, "tti_median", "median time-to-isolation (events)", RES / "operating_curves_tti.png", logy=True)
    figure(pts, marks, "wrongful_grant_rate", "attack events granted (%)", RES / "operating_curves_wrongful.png")
    print("\n".join(out[:60]))
