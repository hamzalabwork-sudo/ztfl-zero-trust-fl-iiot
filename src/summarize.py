"""Collect results/<run>/**.json into one table per (dataset, mode): mean +- std over seeds.

Rows are ranked by VALIDATION macro-F1 (the only split anything is chosen on); test columns are
reported alongside. For federated runs the table adds the last-5-round mean test macro-F1 and the
centralized test macro-F1 of the same model (the FL gap). Writes <run>/summary.csv and summary.md.

Usage: python src/summarize.py [central | fed/a0.5_k10]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

COLUMNS = {  # output name -> path in the result json
    "val_f1_macro": ("val", "f1_macro"),
    "test_f1_macro": ("test", "f1_macro"),
    "test_benign_flag": ("test", "benign_flag_rate"),
    "test_recall": ("test", "recall"),
    "test_roc_auc": ("test", "roc_auc"),
    "test_pr_auc": ("test", "pr_auc"),
    "unseen_f1_macro": ("test_unseen", "f1_macro"),
    "unseen_benign_flag": ("test_unseen", "benign_flag_rate"),
    "last5_f1_macro": ("last5", "f1_macro"),            # federated only
    "last5_benign_flag": ("last5", "benign_flag_rate"),  # federated only
}


def load(run: str) -> pd.DataFrame:
    rows = []
    for p in (RESULTS / run).glob("*/*/*.json"):
        r = json.loads(p.read_text())
        row = {k: r[k] for k in ("dataset", "mode", "model", "seed", "params", "train_seconds", "cpu_latency_ms")}
        for name, (part, key) in COLUMNS.items():
            row[name] = r.get(part, {}).get(key)
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in COLUMNS if df[c].notna().any()] + ["train_seconds", "cpu_latency_ms"]
    g = df.groupby(["dataset", "mode", "model"])
    out = g[metrics].agg(["mean", "std"])
    out.columns = [f"{a}_{b}" for a, b in out.columns]
    out["params"] = g["params"].first()
    out["seeds"] = g["seed"].nunique()
    return out.reset_index().sort_values(["dataset", "mode", "val_f1_macro_mean"], ascending=[True, True, False])


def to_markdown(s: pd.DataFrame) -> str:
    def pm(r, c, pct=False):
        m, sd = r.get(f"{c}_mean"), r.get(f"{c}_std")
        if m is None or pd.isna(m):
            return "-"
        sd = 0 if pd.isna(sd) else sd
        return f"{m * 100:.2f} ± {sd * 100:.2f}" if pct else f"{m:.4f} ± {sd:.4f}"
    fed = "last5_f1_macro_mean" in s
    head = ["model", "seeds", "val macro-F1", "test macro-F1", "benign flagged %"]
    if fed:
        head += ["last-5-round macro-F1", "centralized macro-F1"]
    head += ["unseen macro-F1", "PR-AUC", "params", "CPU latency ms"]
    lines = []
    for (ds, mode), part in s.groupby(["dataset", "mode"], sort=False):
        lines += [f"## {ds} / {mode}", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        for _, r in part.iterrows():
            cells = [r["model"], str(r["seeds"]), pm(r, "val_f1_macro"), pm(r, "test_f1_macro"),
                     pm(r, "test_benign_flag", True)]
            if fed:
                cells += [pm(r, "last5_f1_macro"), pm(r, "central_f1_macro")]
            params = "-" if pd.isna(r["params"]) else f"{int(r['params']):,}"
            cells += [pm(r, "unseen_f1_macro"), pm(r, "test_pr_auc"), params, f"{r['cpu_latency_ms_mean']:.3f}"]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    run = sys.argv[1] if len(sys.argv) > 1 else "central"
    s = summarize(load(run))
    if run != "central" and (RESULTS / "central").exists():  # attach the centralized reference
        c = summarize(load("central"))[["dataset", "mode", "model", "test_f1_macro_mean", "test_f1_macro_std"]]
        c.columns = ["dataset", "mode", "model", "central_f1_macro_mean", "central_f1_macro_std"]
        s = s.merge(c, on=["dataset", "mode", "model"], how="left")
    s.to_csv(RESULTS / run / "summary.csv", index=False)
    (RESULTS / run / "summary.md").write_text(to_markdown(s), encoding="utf-8")
    print(to_markdown(s))
