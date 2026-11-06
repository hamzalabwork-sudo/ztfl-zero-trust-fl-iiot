"""Stage 0 dataset audit -- run before any model is trained.

The old Edge-IIoTSet pipeline reached 0.97 macro-F1 on a formatting artifact ('0' vs '0.0' in one
column) and on per-connection identifiers. This audit looks for the same failure modes in every
dataset, so the feature list of the new pipeline is decided from evidence, not by habit:

- identifier / time / address columns (by name), and whether timestamps and source addresses are
  usable for per-device, time-ordered streams (needed by the Zero-Trust experiments);
- spelling variants of one value ('0' / '0.0' / '0.000') whose label mix differs;
- single-feature shortcuts: a depth-3 tree on ONE column alone, scored on a held-out split;
- exact duplicate rows, and duplicate feature rows that carry both labels (label noise floor).

Usage (on the lab server):  .venv/bin/python src/audit_datasets.py [--datasets edgeiiot,forge,wustl]
Writes results/audit/<dataset>.json and results/audit/<dataset>.md.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results" / "audit"

DATASETS = {
    "edgeiiot": {"csv": "ML-EdgeIIoT-dataset.csv", "binary": "Attack_label", "multi": "Attack_type",
                 "src": "ip.src_host", "time": "frame.time"},
    "forge": {"csv": "Forge_IIOT_Pro.csv", "binary": "attack_label", "multi": "attack_type",
              "src": None, "time": "frame.time_epoch"},
    "wustl": {"csv": "wustl_iiot_2021.csv", "binary": "Target", "multi": "Traffic",
              "src": "SrcAddr", "time": "StartTime"},
}

# Column names that usually identify a connection, a host or a moment rather than behaviour.
ID_PATTERN = re.compile(
    r"(addr|host|ip\.src|ip\.dst|\bip\b|port|stream|checksum|frame\.number|time|epoch|"
    r"\.seq|ack_raw|trans_id|ipid|sipid|dipid|uri|payload|file_data|qry\.name|topic$|msg$)",
    re.IGNORECASE)

SHORTCUT_F1 = 0.95     # one column alone above this macro-F1 is treated as a suspected shortcut
SAMPLE_ROWS = 300_000  # rows used for the single-feature test (stratified), for speed


NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?"


def to_num(s: pd.Series) -> pd.Series:
    """pd.to_numeric(errors='coerce') on plain-looking numbers only; anything else -> NaN.

    pandas' float parser segfaults on huge exponents: hex payloads such as '3e19754008...'
    (tcp.payload, mqtt.msg) read as 3 x 10^19754008..., and also crash read_csv's dtype inference.
    """
    out = pd.Series(np.nan, index=s.index)
    plain = s.str.fullmatch(NUMBER).fillna(False).to_numpy(dtype=bool)
    out[plain] = pd.to_numeric(s[plain], errors="coerce")
    return out


def as_codes(col: pd.Series) -> np.ndarray:
    """A text column as model input: numeric (NaN -> -1) when it parses as numbers with one
    spelling per number; otherwise factorized with the raw spelling kept.

    Keeping the raw spelling is deliberate: '0' and '0.0' get different codes, which is exactly
    how the Edge-IIoTSet artifact leaked the label.
    """
    s = col.str.strip()
    num = to_num(s)
    if num.notna().mean() > 0.99 and s.nunique() == num.nunique():
        return num.fillna(-1).to_numpy(dtype=np.float64)
    return pd.factorize(s)[0].astype(np.float64)


def spelling_variants(col: pd.Series, y: np.ndarray, keep: int = 10) -> list[dict]:
    """Values that parse to the same number but are written differently, with each spelling's
    attack rate. A large rate gap between spellings of one value is a formatting leak."""
    s = col.str.strip()
    frame = pd.DataFrame({"s": s, "num": to_num(s), "y": y}).dropna(subset=["num"])
    g = frame.groupby(["num", "s"])["y"].agg(["size", "mean"]).reset_index()
    g = g[g.duplicated("num", keep=False)]
    found = []
    for value, grp in list(g.groupby("num"))[:keep]:
        found.append({"value": float(value),
                      "spellings": {r.s: {"rows": int(r.size), "attack_rate": round(float(r.mean), 4)}
                                    for r in grp.itertuples()}})
    return found


def single_feature_scores(df: pd.DataFrame, y: np.ndarray, seed: int = 42) -> dict[str, float]:
    """Binary macro-F1 of a depth-3 tree trained on each column alone (held-out 30%)."""
    idx = np.arange(len(df))
    if len(idx) > SAMPLE_ROWS:
        idx, _ = train_test_split(idx, train_size=SAMPLE_ROWS, stratify=y, random_state=seed)
    ys = y[idx]
    tr, te = train_test_split(np.arange(len(idx)), test_size=0.3, stratify=ys, random_state=seed)
    scores = {}
    for c in df.columns:
        x = as_codes(df[c].iloc[idx]).reshape(-1, 1)
        tree = DecisionTreeClassifier(max_depth=3, random_state=seed).fit(x[tr], ys[tr])
        scores[c] = round(float(f1_score(ys[te], tree.predict(x[te]), average="macro")), 4)
    return dict(sorted(scores.items(), key=lambda kv: -kv[1]))


def stream_readiness(df: pd.DataFrame, cfg: dict, y: np.ndarray) -> dict:
    """Can rows be grouped into per-device, time-ordered streams? (needed for Zero-Trust tests)"""
    out: dict = {}
    if cfg["src"] and cfg["src"] in df:
        src = df[cfg["src"]].str.strip()
        benign_src = src[y == 0].value_counts()
        attack_src = src[y == 1].value_counts()
        out["distinct_sources"] = int(src.nunique())
        out["benign_sources_with_100plus_rows"] = int((benign_src >= 100).sum())
        out["top_benign_sources"] = benign_src.head(10).to_dict()
        out["top_attack_sources"] = attack_src.head(10).to_dict()
        out["sources_in_both_labels"] = int(len(set(benign_src.index) & set(attack_src.index)))
    else:
        out["distinct_sources"] = None
    if cfg["time"] and cfg["time"] in df:
        t = to_num(df[cfg["time"]].str.strip())
        out["time_numeric_share"] = round(float(t.notna().mean()), 4)
        out["time_distinct"] = int(t.nunique())
        if t.notna().any():
            out["time_range"] = [float(t.min()), float(t.max())]
            out["time_monotonic_in_file"] = bool(t.dropna().is_monotonic_increasing)
    return out


def audit(name: str) -> dict:
    cfg = DATASETS[name]
    # Read every column as text: keeps the raw spellings, and pandas' dtype inference segfaults
    # on hex payloads that look like huge exponents (see to_num).
    df = pd.read_csv(RAW / cfg["csv"], dtype=str, keep_default_na=False)
    y = to_num(df[cfg["binary"]].str.strip()).fillna(0).astype(int).to_numpy()
    multi = df[cfg["multi"]].astype(str)
    feats = df.drop(columns=[cfg["binary"], cfg["multi"]])

    report: dict = {"dataset": name, "rows": len(df), "columns": feats.shape[1],
                    "binary_counts": {int(k): int(v) for k, v in zip(*np.unique(y, return_counts=True))},
                    "multiclass_counts": multi.value_counts().to_dict()}
    report["identifier_like_columns"] = [c for c in feats.columns if ID_PATTERN.search(c)]
    report["constant_columns"] = [c for c in feats.columns if feats[c].nunique(dropna=False) <= 1]

    report["spelling_variants"] = {}
    for c in feats.columns:
        v = spelling_variants(feats[c], y)
        if v:
            report["spelling_variants"][c] = v

    dup_full = df.duplicated().mean()
    row_hash = pd.util.hash_pandas_object(feats, index=False).to_numpy()
    labels_per_row = pd.Series(y).groupby(row_hash).nunique()
    report["duplicate_rows_share"] = round(float(dup_full), 4)
    report["distinct_feature_rows"] = int(len(labels_per_row))
    report["feature_rows_with_both_labels"] = int((labels_per_row > 1).sum())

    report["stream_readiness"] = stream_readiness(df, cfg, y)
    scores = single_feature_scores(feats, y)
    report["single_feature_macro_f1"] = scores
    report["suspected_shortcuts"] = [c for c, s in scores.items() if s >= SHORTCUT_F1]
    return report


def to_markdown(r: dict) -> str:
    lines = [f"# Audit: {r['dataset']}", "",
             f"- rows {r['rows']:,}, feature columns {r['columns']}, binary {r['binary_counts']}",
             f"- duplicate rows {r['duplicate_rows_share']:.1%}; distinct feature rows "
             f"{r['distinct_feature_rows']:,}, of which {r['feature_rows_with_both_labels']:,} carry both labels",
             f"- identifier-like columns: {', '.join(r['identifier_like_columns']) or 'none'}",
             f"- constant columns: {', '.join(r['constant_columns']) or 'none'}",
             f"- suspected single-feature shortcuts (macro-F1 >= {SHORTCUT_F1}): "
             f"{', '.join(r['suspected_shortcuts']) or 'none'}",
             f"- spelling variants: {', '.join(r['spelling_variants']) or 'none'}",
             f"- stream readiness: {json.dumps(r['stream_readiness'], default=str)}", "",
             "## Classes", "", "| type | rows |", "|---|---|"]
    lines += [f"| {k} | {v:,} |" for k, v in r["multiclass_counts"].items()]
    lines += ["", "## Top 25 single-feature macro-F1", "", "| column | macro-F1 |", "|---|---|"]
    lines += [f"| {c} | {s} |" for c, s in list(r["single_feature_macro_f1"].items())[:25]]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default=",".join(DATASETS))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in args.datasets.split(","):
        r = audit(name)
        (OUT / f"{name}.json").write_text(json.dumps(r, indent=2, default=str))
        (OUT / f"{name}.md").write_text(to_markdown(r))
        print(f"[{name}] shortcuts={r['suspected_shortcuts']} variants={list(r['spelling_variants'])} "
              f"sources={r['stream_readiness'].get('distinct_sources')}", flush=True)


if __name__ == "__main__":
    main()
