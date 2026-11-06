"""Collect results/closed_loop/<calibration>/**/<model>_s<seed>.json into access-control tables
(mean +- std over seeds) per (dataset, mode, rho). Writes <calibration>/summary.{csv,md}.

Usage: python src/summarize_closed_loop.py [hist_empirical | monotone_empirical | monotone_lorden]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "closed_loop"
METRICS = {  # column -> (header, percent?)
    "wrongful_grant_rate": ("wrongful grant %", True),
    "benign_denial_rate": ("benign denial %", True),
    "false_isolation_rate": ("false isolation %", True),
    "benign_blocked_at_end": ("benign blocked at end %", True),
    "detection_rate": ("detected %", True),
    "tti_median": ("time-to-isolation median", False),
    "tti_p90": ("time-to-isolation p90", False),
    "false_reauth_rate": ("false re-auth %", True),
    "lateral_reach_mean": ("lateral reach", False),
}


def load(res: Path) -> pd.DataFrame:
    rows = []
    for p in res.glob("*/*/*_s[0-9]*.json"):
        if p.stem.endswith("_ledger"):
            continue
        r = json.loads(p.read_text())
        for rho, per in r["results"].items():
            for policy, m in per.items():
                rows.append({"dataset": r["dataset"], "mode": r["mode"], "model": r["model"], "seed": r["seed"],
                             "rho": rho, "policy": policy, "detector_f1": r["detector"]["test_f1_macro"], **m})
    return pd.DataFrame(rows)


def to_markdown(df: pd.DataFrame) -> str:
    order = list(dict.fromkeys(df["policy"]))
    lines = []
    for (ds, mode, model, rho), part in df.groupby(["dataset", "mode", "model", "rho"], sort=False):
        f1 = part.drop_duplicates("seed")["detector_f1"]
        lines += [f"## {ds} / {mode} / {model} / {rho}  (seeds {part['seed'].nunique()}, detector macro-F1 "
                  f"{f1.mean():.4f} ± {f1.std():.4f})", "",
                  "| policy | " + " | ".join(h for h, _ in METRICS.values()) + " |", "|---" * (len(METRICS) + 1) + "|"]
        g = part.groupby("policy")
        for policy in order:
            cells = []
            for col, (_, pct) in METRICS.items():
                v = pd.to_numeric(g.get_group(policy)[col], errors="coerce")
                if v.isna().all():
                    cells.append("-")
                    continue
                m, sd = v.mean(), (0 if pd.isna(v.std()) else v.std())
                cells.append(f"{m * 100:.2f} ± {sd * 100:.2f}" if pct else f"{m:.1f} ± {sd:.1f}")
            lines.append(f"| {policy} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    res = RESULTS / (sys.argv[1] if len(sys.argv) > 1 else "hist_empirical")
    df = load(res).sort_values(["dataset", "rho", "seed"], ascending=[True, False, True])
    df.to_csv(res / "summary.csv", index=False)
    md = to_markdown(df)
    (res / "summary.md").write_text(md, encoding="utf-8")
    print(md)
