"""Summarise E7 / Stage 3 (results/poison/): the attack x aggregator x m matrix.

Detector: clean test macro-F1 and benign flag rate; for the backdoor, the success rate (target-type
test rows scored benign) and its excess over the clean baseline (attack "none", same aggregator and
f = m), since some target types are partly missed even without an attack. Access: wrongful-grant
rate of the gateway (E5c closed loop) for per_event vs cusum_sprt_mix, streams all / target.
Each cell is mean +- std over seeds; both deployments (best-val round, last round).

Writes results/poison/summary.md and results/poison/summary_long.csv.
Usage: python src/summarize_stage3.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "poison"
DATASETS = ("edgeiiot", "wustl", "forge")
ATTACKS = ("none", "label_flip", "alie", "minmax", "backdoor")
AGGS = ("fedavg", "median", "trimmed_mean", "multi_krum", "fltrust", "fltrust_v2")
POLICIES = ("per_event", "cusum_sprt_mix")


def load() -> pd.DataFrame:
    rows = []
    for p in sorted(RES.glob("*_m[0-9]/*/*/*/mlp_s*.json")):
        r = json.loads(p.read_text())
        base = {k: r[k] for k in ("dataset", "attack", "n_malicious", "aggregator", "seed", "best_round")}
        for deploy, det in r["detector"].items():
            row = base | {"deploy": deploy, "f1": det["f1_macro"], "benign_flag": det["benign_flag_rate"],
                          "recall": det["recall"], "bd": det["backdoor_success"]}
            for stream, per in r["access"][deploy].items():
                for policy, m in per.items():
                    key = f"{stream}/{policy}"
                    row[f"wrong:{key}"] = m["wrongful_grant_rate"]
                    row[f"deny:{key}"] = m["benign_denial_rate"]
                    row[f"fiso:{key}"] = m["false_isolation_rate"]
            rows.append(row)
    df = pd.DataFrame(rows)
    clean = (df[df.attack == "none"].groupby(["dataset", "aggregator", "n_malicious", "deploy", "seed"])
             .bd.first().rename("bd_clean"))
    df = df.join(clean, on=["dataset", "aggregator", "n_malicious", "deploy", "seed"])
    df["bd_excess"] = df.bd - df.bd_clean
    return df


def pm(s: pd.Series, pct: bool = True, nd: int = 1) -> str:
    k = 100 if pct else 1
    return f"{s.mean() * k:.{nd}f} ± {s.std(ddof=1) * k:.{nd}f}" if len(s) > 1 else f"{s.mean() * k:.{nd}f}"


def grid(df: pd.DataFrame, col: str, rows: tuple, row_key: str, pct: bool = True, nd: int = 1) -> str:
    """Markdown table: rows = row_key values, columns = aggregators, cells = mean +- std of col."""
    aggs = [a for a in AGGS if a in df.aggregator.unique()]
    out = ["| " + row_key + " | " + " | ".join(aggs) + " |", "|---" * (len(aggs) + 1) + "|"]
    for v in rows:
        sub = df[df[row_key] == v]
        if sub.empty:
            continue
        cells = [pm(sub[sub.aggregator == a][col], pct, nd) if (sub.aggregator == a).any() else "" for a in aggs]
        out.append(f"| {v} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    df = load()
    df.to_csv(RES / "summary_long.csv", index=False)
    n_runs = len(df) // 2
    md = [f"# E7 / Stage 3 summary\n\n{n_runs} runs ({df.seed.nunique()} seeds). Cells: mean ± std over seeds, in %. "
          "`fltrust` = first implementation (one-step root update, implementation error); `fltrust_v2` = faithful.\n"]
    for deploy in ("best", "last"):
        d = df[df.deploy == deploy]
        md.append(f"\n## Deployment: {deploy}\n")
        for ds in DATASETS:
            x = d[d.dataset == ds]
            md.append(f"\n### {ds}\n")
            for m in sorted(x.n_malicious.unique()):
                xm = x[x.n_malicious == m]
                md.append(f"\n**m = {m}: clean test macro-F1**\n\n" + grid(xm, "f1", ATTACKS, "attack", nd=2))
                md.append(f"\n\n**m = {m}: benign flag rate**\n\n" + grid(xm, "benign_flag", ATTACKS, "attack", nd=2))
            bd = x[x.attack == "backdoor"]
            md.append("\n\n**Backdoor success (target scored benign)**\n\n" + grid(bd, "bd", (1, 2, 3), "n_malicious"))
            md.append("\n\n**Clean baseline (attack none, same f)**\n\n" +
                      grid(x[x.attack == "none"], "bd", (1, 2, 3), "n_malicious"))
            md.append("\n\n**Backdoor excess over clean (pp)**\n\n" + grid(bd, "bd_excess", (1, 2, 3), "n_malicious"))
            for stream in ("all/rho1", "all/rho0.2", "target/rho1", "target/rho0.2"):
                for policy in POLICIES:
                    md.append(f"\n\n**Wrongful grants, {stream}, {policy}, m = 3**\n\n" +
                              grid(x[x.n_malicious == 3], f"wrong:{stream}/{policy}", ATTACKS, "attack", nd=2))
            md.append("\n\n**False isolation, all/rho1, cusum_sprt_mix, m = 3**\n\n" +
                      grid(x[x.n_malicious == 3], "fiso:all/rho1/cusum_sprt_mix", ATTACKS, "attack", nd=2))
            md.append("\n\n**Benign denial, all/rho1, per_event / cusum_sprt_mix, m = 3**\n\n" +
                      grid(x[x.n_malicious == 3], "deny:all/rho1/per_event", ATTACKS, "attack", nd=2) + "\n\n" +
                      grid(x[x.n_malicious == 3], "deny:all/rho1/cusum_sprt_mix", ATTACKS, "attack", nd=2) + "\n")
    (RES / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{n_runs} runs -> {RES / 'summary.md'}")


if __name__ == "__main__":
    main()
