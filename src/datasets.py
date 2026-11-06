"""Stage 1 data pipeline: clean, split and transform the three public datasets.

Rules (decided from the stage 0 audit, results/audit/*.md):

1. Every value is read as text and converted with ONE canonical rule (`to_num`), so '0', '0.0'
   and '0x00000000' are the same number. In Edge-IIoTSet the benign capture writes empty fields
   as '0' and the attack captures as '0.0'; six columns predicted the label perfectly from that
   spelling alone.
2. Identifier columns are dropped: addresses, timestamps, capture-order and stream indices,
   checksums, raw payloads and free text. Raw ports become one service-port category from a fixed
   IANA list (the lower port of a connection is the service; the other is ephemeral).
3. Suspected stack fingerprints (TTL, TCP option layout, window scaling) are a separate column
   group, kept or dropped by `mode` ("keep" / "nofp"), so their effect is reported, not hidden.
4. Malformed classes are dropped (Edge-IIoTSet DDoS_UDP and MITM: no behavioural fields set).

The split is a stratified 70 / 10 / 20 random split by attack type. The validation split is the
only one anything is selected on; test is scored for reporting. Each test row is also marked
seen / unseen (does its exact cleaned feature pattern occur in training?) as a generalization check.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"
PREP_VERSION = 1

MAX_PER_CLASS = 50_000  # per attack type, rarer classes kept whole
CLIP = 10.0             # transformed features clipped to +-CLIP (a constant: federated-exact)
MODES = ["keep", "nofp"]

SERVICE_PORTS = {80: "http", 443: "https", 1883: "mqtt", 8883: "mqtt_tls", 502: "modbus",
                 5900: "vnc", 53: "dns", 22: "ssh", 21: "ftp", 23: "telnet", 123: "ntp",
                 67: "dhcp", 68: "dhcp", 5353: "mdns", 1900: "ssdp", 20000: "dnp3"}

DATASETS = {
    "edgeiiot": {
        "csv": "ML-EdgeIIoT-dataset.csv", "binary": "Attack_label", "multi": "Attack_type",
        "drop": [
            # addresses, timestamps, free text / payloads
            "frame.time", "ip.src_host", "ip.dst_host", "arp.dst.proto_ipv4", "arp.src.proto_ipv4",
            "http.file_data", "http.request.full_uri", "http.request.uri.query", "http.referer",
            "http.request.version", "icmp.transmit_timestamp", "dns.qry.name", "tcp.payload",
            "tcp.options", "mqtt.msg", "mqtt.topic", "mqtt.protoname",
            # capture-order indices, counters, checksums
            "udp.stream", "tcp.ack_raw", "tcp.checksum", "icmp.checksum", "icmp.seq_le",
            "mbtcp.trans_id", "udp.port",
        ],
        "categorical": ["http.request.method"],
        "ports": ("tcp.srcport", "tcp.dstport"),
        "fingerprint": [],
        "drop_classes": ["DDoS_UDP", "MITM"],
    },
    "forge": {
        "csv": "Forge_IIOT_Pro.csv", "binary": "attack_label", "multi": "attack_type",
        "drop": ["frame.number", "frame.time_epoch", "frame.time_delta", "tcp.stream", "udp.stream",
                 "ip.checksum", "tcp.checksum", "udp.checksum", "icmp.checksum", "icmpv6.checksum"],
        "categorical": [],
        "ports": None,
        "fingerprint": ["ip.ttl", "ip.ttl.lncb", "ip.dsfield.dscp", "ip.flags.df", "tcp.hdr_len",
                        "tcp.option_kind", "tcp.option_len", "tcp.options.mss_val",
                        "tcp.window_size", "tcp.window_size_scalefactor"],
        "drop_classes": [],
    },
    "wustl": {
        "csv": "wustl_iiot_2021.csv", "binary": "Target", "multi": "Traffic",
        "drop": ["StartTime", "LastTime", "SrcAddr", "DstAddr", "sIpId", "dIpId"],
        "categorical": [],
        "ports": ("Sport", "Dport"),
        "fingerprint": ["sTtl", "dTtl", "sTos"],
        "drop_classes": [],
    },
}

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?"
HEX = r"0[xX][0-9a-fA-F]{1,16}"


def to_num(s: pd.Series) -> pd.Series:
    """Canonical text -> float: plain decimals and 0x-hex; anything else -> NaN.

    Only plain-looking numbers reach pd.to_numeric: its parser segfaults on hex payloads such as
    '3e19754008...' that read as huge exponents.
    """
    s = s.str.strip()
    out = pd.Series(np.nan, index=s.index)
    plain = s.str.fullmatch(NUMBER).fillna(False).to_numpy(dtype=bool)
    out[plain] = pd.to_numeric(s[plain], errors="coerce")
    hexa = s.str.fullmatch(HEX).fillna(False).to_numpy(dtype=bool)
    out[hexa] = s[hexa].map(lambda v: float(int(v, 16)))
    return out


def service_port(src: pd.Series, dst: pd.Series) -> pd.Series:
    """Direction-agnostic service category from a fixed list (nothing learned from the data)."""
    src, dst = to_num(src).fillna(0), to_num(dst).fillna(0)
    port = np.where((src > 0) & (dst > 0), np.minimum(src, dst), np.maximum(src, dst)).astype(np.int64)
    named = pd.Series(port).map(SERVICE_PORTS)
    bucket = np.select([port == 0, port < 1024, port < 49152], ["none", "wellknown_other", "registered"], "dynamic")
    return named.fillna(pd.Series(bucket)).rename("service_port")


@dataclass
class Prepared:
    dataset: str
    mode: str
    seed: int
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    type_train: np.ndarray   # attack-type name per row (partitioning, per-type detection)
    type_val: np.ndarray
    type_test: np.ndarray
    test_seen: np.ndarray    # True where the cleaned pattern also occurs in training
    feature_names: list[str]
    report: dict

    @property
    def input_dim(self) -> int:
        return self.X_train.shape[1]


def clean(dataset: str, mode: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, dict]:
    """Raw CSV -> numeric feature frame, binary labels, attack types, cleaning report."""
    cfg = DATASETS[dataset]
    df = pd.read_csv(RAW / cfg["csv"], dtype=str, keep_default_na=False)
    report: dict = {"raw_rows": len(df)}
    types = df[cfg["multi"]].str.strip()
    bad = types.isin(cfg["drop_classes"]).to_numpy()
    report["dropped_classes"] = types[bad].value_counts().to_dict()
    df, types = df[~bad].reset_index(drop=True), types[~bad].reset_index(drop=True)
    y = to_num(df[cfg["binary"]]).fillna(0).astype(np.int64).to_numpy()

    drop = set(cfg["drop"]) | {cfg["binary"], cfg["multi"]}
    if mode == "nofp":
        drop |= set(cfg["fingerprint"])
    feats = df.drop(columns=[c for c in df.columns if c in drop])

    extra = []
    if cfg["ports"]:
        extra.append(service_port(feats[cfg["ports"][0]], feats[cfg["ports"][1]]))
        feats = feats.drop(columns=list(cfg["ports"]))
    for c in cfg["categorical"]:
        v = feats[c].str.strip()
        v = v.where(to_num(v).isna(), "none")  # '0' / '0.0' / '' all mean "absent"
        extra.append(v.replace("", "none").rename(c))
        feats = feats.drop(columns=[c])

    numeric = {}
    unparsed = {}
    for c in feats.columns:
        v = to_num(feats[c])
        nonempty = feats[c].str.strip().ne("").to_numpy()
        bad_vals = int((v.isna().to_numpy() & nonempty).sum())
        if bad_vals:
            unparsed[c] = bad_vals
        numeric[c] = v.fillna(0.0).to_numpy(dtype=np.float64)
    out = pd.DataFrame(numeric)
    if extra:
        cats = pd.get_dummies(pd.concat(extra, axis=1), dtype=np.float64)
        out = pd.concat([out, cats], axis=1)
    constant = [c for c in out.columns if out[c].nunique() <= 1]
    out = out.drop(columns=constant)

    report.update(rows=len(out), features=out.shape[1], unparsed_values=unparsed,
                  dropped_constant=constant, fingerprint_dropped=mode == "nofp" and cfg["fingerprint"])
    return out, y, types.to_numpy(dtype=object), report


def cap_indices(types: np.ndarray, max_per_class: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    keep = []
    for t in np.unique(types):
        idx = np.flatnonzero(types == t)
        keep.append(rng.choice(idx, size=max_per_class, replace=False) if len(idx) > max_per_class else idx)
    idx = np.concatenate(keep)
    rng.shuffle(idx)
    return idx


def prepare(dataset: str, mode: str = "keep", seed: int = 42, max_per_class: int = MAX_PER_CLASS) -> Prepared:
    """Cleaned, capped, split and transformed data for one (dataset, mode, seed); cached as npz."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode == "nofp" and not DATASETS[dataset]["fingerprint"]:
        raise ValueError(f"{dataset} has no fingerprint group; use mode='keep'")
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{dataset}_{mode}_s{seed}_cap{max_per_class}_v{PREP_VERSION}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=True)
        meta = json.loads(str(z["meta"]))
        arrays = {k: z[k] for k in z.files if k != "meta"}
        return Prepared(dataset, mode, seed, **arrays, feature_names=meta["feature_names"], report=meta["report"])

    feats, y, types, report = clean(dataset, mode)
    sel = cap_indices(types, max_per_class, seed)
    X = feats.to_numpy(dtype=np.float64)[sel]
    y, types = y[sel], types[sel]
    pattern = pd.util.hash_pandas_object(pd.DataFrame(X), index=False).to_numpy()

    idx = np.arange(len(y))
    pool, te = train_test_split(idx, test_size=0.2, stratify=types, random_state=seed)
    tr, va = train_test_split(pool, test_size=0.125, stratify=types[pool], random_state=seed)  # 70/10/20

    # signed log1p then z-score, fit on train only: tames byte/packet-count tails and needs only
    # per-feature sums and sums of squares, so it is exactly computable in federation.
    def logt(a: np.ndarray) -> np.ndarray:
        return np.sign(a) * np.log1p(np.abs(a))
    scaler = StandardScaler().fit(logt(X[tr]))
    tf = lambda a: np.clip(scaler.transform(logt(a)), -CLIP, CLIP).astype(np.float32)

    seen = np.isin(pattern[te], pattern[tr])
    report.update(rows_after_cap=len(y), split={"train": len(tr), "val": len(va), "test": len(te)},
                  rows_per_type={k: int(v) for k, v in zip(*np.unique(types, return_counts=True))},
                  test_unseen=int((~seen).sum()), test_unseen_benign=int(((~seen) & (y[te] == 0)).sum()))
    data = Prepared(dataset, mode, seed, tf(X[tr]), y[tr], tf(X[va]), y[va], tf(X[te]), y[te],
                    types[tr], types[va], types[te], seen, feats.columns.tolist(), report)
    np.savez_compressed(path, X_train=data.X_train, y_train=data.y_train, X_val=data.X_val, y_val=data.y_val,
                        X_test=data.X_test, y_test=data.y_test, type_train=data.type_train,
                        type_val=data.type_val, type_test=data.type_test, test_seen=data.test_seen,
                        meta=json.dumps({"feature_names": data.feature_names, "report": report}, default=str))
    return data


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build and cache prepared splits, print the cleaning report")
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    for name in args.datasets.split(","):
        for mode in (MODES if DATASETS[name]["fingerprint"] else ["keep"]):
            d = prepare(name, mode, args.seed)
            print(f"[{name}/{mode}] features={d.input_dim} {json.dumps(d.report, default=str)}", flush=True)
