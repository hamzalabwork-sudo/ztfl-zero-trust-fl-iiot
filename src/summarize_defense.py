"""Summarise E8 (results/defense/): the canary check against the E7 deployment practices.

Per run and deployment track (best, last, canary_d<delta>): final backdoor success, F1, benign flag;
exposure (max / mean backdoor success while deployed from max(onset, 6) on); false rejections and
staleness; gateway wrongful grants (best, last, canary_d0.05). Excess = success minus the same
track's success in the no-attack run (same dataset, aggregator, m, seed).

Writes results/defense/summary.md and results/defense/summary_long.csv.
Usage: python src/summarize_defense.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "defense"
DATASETS = ("edgeiiot", "wustl", "forge")
AGGS = ("fedavg", "median", "multi_krum", "fltrust_v2")
MAIN_TRACKS = ("best", "last", "canary_d0.05")


def load() -> pd.DataFrame:
    rows = []
    for p in sorted(RES.glob("*_m[0-9]_on*/*/*/*/mlp_s*.json")):
        r = json.loads(p.read_text())
        base = {k: r[k] for k in ("dataset", "attack", "n_malicious", "aggregator", "onset", "seed")}
        checked = [g for g in r["gates"]["d0.05"]["log"] if g["round"] > r["gates"]["d0.05"]["warmup"]]
        for track, det in r["detector"].items():
            ex = r["exposure"][track]
            row = base | {"track": track, "bd": det["backdoor_success"], "f1": det["f1_macro"],
                          "benign_flag": det["benign_flag_rate"], "round": det["round"],
                          "bd_exp_max": ex["backdoor_success_max"], "bd_exp_mean": ex["backdoor_success_mean"],
                          "f1_exp_min": ex["f1_macro_min"], "stale": ex["stale_rounds_final"]}
            if track.startswith("canary_"):
                g = r["gates"][track[len("canary_"):]]
                post = [x for x in g["log"] if x["round"] > g["warmup"]]
                row["rejected_share"] = sum(not x["promoted"] for x in post) / len(post)
            for stream, per in r["access"].get(track, {}).items():
                for policy, m in per.items():
                    row[f"wrong:{stream}/{policy}"] = m["wrongful_grant_rate"]
                    row[f"fiso:{stream}/{policy}"] = m["false_isolation_rate"]
            rows.append(row)
        rows[-1]["head_ok"] = r["ledger"]["gateway_runs_registry_head"] and r["ledger"]["verified"]
        assert len(checked) == 30 - r["gates"]["d0.05"]["warmup"]
    df = pd.DataFrame(rows)
    clean = (df[df.attack == "none"].set_index(["dataset", "aggregator", "n_malicious", "seed", "track"])
             [["bd", "bd_exp_max"]].add_suffix("_clean"))
    df = df.join(clean, on=["dataset", "aggregator", "n_malicious", "seed", "track"])
    df["bd_excess"] = df.bd - df.bd_clean
    df["bd_exp_max_excess"] = df.bd_exp_max - df.bd_exp_max_clean
    return df


def pm(s: pd.Series, k: float = 100, nd: int = 1) -> str:
    s = s.dropna()
    if s.empty:
        return ""
    return f"{s.mean() * k:.{nd}f} ± {s.std(ddof=1) * k:.{nd}f}" if len(s) > 1 else f"{s.mean() * k:.{nd}f}"


def table(df: pd.DataFrame, rows: list[str], col: str, value: str, k: float = 100, nd: int = 1) -> str:
    present = set(df[col].unique())
    cols = [c for c in MAIN_TRACKS if c in present] if present <= set(MAIN_TRACKS) else sorted(present)
    head = "| " + " | ".join(rows) + " | " + " | ".join(map(str, cols)) + " |"
    out = [head, "|---" * (len(rows) + len(cols)) + "|"]
    for key, sub in df.groupby(rows, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        out.append("| " + " | ".join(map(str, key)) + " | " + " | ".join(pm(sub[sub[col] == c][value], k, nd) for c in cols) + " |")
    return "\n".join(out)


def main() -> None:
    df = load()
    df.to_csv(RES / "summary_long.csv", index=False)
    n = df.groupby(["dataset", "attack", "n_malicious", "aggregator", "onset", "seed"]).ngroups
    md = [f"# E8 summary\n\n{n} runs. Cells: mean ± std over seeds, in %. Ledger head check passed in "
          f"{int(df.head_ok.sum())} of {int(df.head_ok.notna().sum())} runs.\n"]
    main_t = df[df.track.isin(MAIN_TRACKS)]
    order = {"attack": {"none": 0, "label_flip": 1, "backdoor": 2, "backdoor_adaptive": 3}}
    main_t = main_t.sort_values(["attack", "onset"], key=lambda s: s.map(order["attack"]) if s.name == "attack" else s)
    for ds in DATASETS:
        x = main_t[main_t.dataset == ds]
        md.append(f"\n## {ds}\n")
        for value, title in (("bd", "backdoor success, final deployed model"),
                             ("bd_excess", "backdoor success excess over the no-attack run (pp), final"),
                             ("bd_exp_max", "exposure: max backdoor success while deployed"),
                             ("f1", "macro-F1, final deployed model"), ("f1_exp_min", "exposure: min macro-F1 while deployed"),
                             ("stale", "staleness of the final deployed model (rounds)")):
            md.append(f"\n**{title}**\n\n" + table(x, ["attack", "onset", "aggregator", "n_malicious"], "track", value,
                                                    k=1 if value == "stale" else 100))
        md.append("\n\n**gateway: attack events granted, target streams, cusum_sprt_mix, rho 1 / rho 0.2 (m = 3)**\n\n" +
                  table(x[x.n_malicious == 3], ["attack", "onset", "aggregator"], "track", "wrong:target/rho1/cusum_sprt_mix", nd=2)
                  + "\n\n" +
                  table(x[x.n_malicious == 3], ["attack", "onset", "aggregator"], "track", "wrong:target/rho0.2/cusum_sprt_mix", nd=2))
        can = df[(df.dataset == ds) & df.track.str.startswith("canary_")]
        md.append("\n\n**delta sweep: rejected share of checked rounds (rounds 6-30)**\n\n" +
                  table(can, ["attack", "onset", "aggregator"], "track", "rejected_share"))
        md.append("\n\n**delta sweep: final backdoor success**\n\n" + table(can, ["attack", "onset", "aggregator"], "track", "bd"))
        md.append("\n\n**delta sweep: exposure max backdoor success**\n\n" +
                  table(can, ["attack", "onset", "aggregator"], "track", "bd_exp_max") + "\n")
    (RES / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{n} runs -> {RES / 'summary.md'}")


if __name__ == "__main__":
    main()
