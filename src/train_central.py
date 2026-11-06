"""Stage 1a -- centralized detector zoo on the cleaned public datasets.

Every model in models.MODEL_NAMES (plus gradient boosting as a non-deep reference) is trained on
every (dataset, mode) with every seed, under one protocol:

- AdamW, cosine lr 1e-3 -> 1e-4, batch 512, 30 epochs, inverse-frequency class weights;
- the checkpoint with the best VALIDATION macro-F1 is kept (test is never used to choose);
- autoencoder: benign training rows only; threshold = 99th percentile of benign validation error;
- test metrics: macro-F1, benign false-alarm rate, recall, ROC-AUC, PR-AUC, per-attack-type
  detection, the same on never-seen test patterns, parameters, training time, and CPU
  single-row inference latency (one thread -- the edge-relevant number).

One JSON per run in results/central/<dataset>/<mode>/<model>_s<seed>.json; finished runs are
skipped, so the sweep can be stopped and restarted.

Usage: .venv/bin/python src/train_central.py --datasets edgeiiot,forge,wustl --seeds 42,43,44,45,46
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score

from datasets import DATASETS, MODES, PREP_VERSION, Prepared, prepare
from models import MODEL_NAMES, SUPERVISED, build_model, n_params

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "central"
EPOCHS, BATCH, LR_MAX, LR_MIN = 30, 512, 1e-3, 1e-4
AE_QUANTILE = 0.99
EVAL_CHUNK = 8192


def code_version() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "src").glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def seed_all(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@torch.no_grad()
def scores(model: nn.Module, X: torch.Tensor, autoencoder: bool) -> np.ndarray:
    """Attack score per row: P(attack) for classifiers, reconstruction error for the autoencoder."""
    model.eval()
    out = []
    for i in range(0, len(X), EVAL_CHUNK):
        xb = X[i : i + EVAL_CHUNK]
        out.append(model.score(xb) if autoencoder else torch.softmax(model(xb), dim=1)[:, 1])
    return torch.cat(out).float().cpu().numpy()


def metrics(y: np.ndarray, s: np.ndarray, thr: float, types: np.ndarray | None = None) -> dict:
    pred = (s >= thr).astype(int)
    m = {"f1_macro": f1_score(y, pred, average="macro"), "f1": f1_score(y, pred, zero_division=0),
         "precision": precision_score(y, pred, zero_division=0), "recall": recall_score(y, pred, zero_division=0),
         "benign_flag_rate": float(pred[y == 0].mean()) if (y == 0).any() else None,
         "accuracy": float((pred == y).mean())}
    if len(np.unique(y)) == 2:
        m["roc_auc"] = roc_auc_score(y, s)
        m["pr_auc"] = average_precision_score(y, s)
    if types is not None:  # share of each traffic type called "attack" (for benign: false alarms)
        m["detection_by_type"] = {str(t): float(pred[types == t].mean()) for t in np.unique(types)}
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in m.items()}


def cpu_latency_ms(model: nn.Module, x_row: np.ndarray, autoencoder: bool, reps: int = 300) -> float:
    """Median single-row inference time on one CPU thread (edge proxy)."""
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    m = model.to("cpu").eval()
    x = torch.from_numpy(x_row[None, :])
    fn = (lambda: m.score(x)) if autoencoder else (lambda: m(x))
    times = []
    with torch.no_grad():
        for i in range(reps + 30):
            t0 = time.perf_counter()
            fn()
            if i >= 30:
                times.append((time.perf_counter() - t0) * 1e3)
    torch.set_num_threads(threads)
    return float(np.median(times))


def train_torch(name: str, d: Prepared, seed: int, device: str) -> dict:
    seed_all(seed)
    ae = name == "autoencoder"
    model = build_model(name, d.input_dim).to(device)
    Xtr = torch.from_numpy(d.X_train[d.y_train == 0] if ae else d.X_train).to(device)
    ytr = torch.from_numpy(d.y_train).to(device)
    Xva, Xte = torch.from_numpy(d.X_val).to(device), torch.from_numpy(d.X_test).to(device)

    counts = np.bincount(d.y_train, minlength=2).astype(np.float64)
    weights = torch.tensor(len(d.y_train) / (2 * counts), dtype=torch.float32, device=device)
    loss_fn = nn.MSELoss() if ae else nn.CrossEntropyLoss(weight=weights)
    opt = torch.optim.AdamW(model.parameters(), lr=LR_MAX, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS, eta_min=LR_MIN)
    gen = torch.Generator(device=device).manual_seed(seed)

    best = {"val_f1_macro": -1.0}
    history = []
    t0 = time.perf_counter()
    for epoch in range(1, EPOCHS + 1):
        model.train()
        perm = torch.randperm(len(Xtr), generator=gen, device=device)
        total = 0.0
        for i in range(0, len(perm), BATCH):
            idx = perm[i : i + BATCH]
            xb = Xtr[idx]
            loss = loss_fn(model(xb), xb) if ae else loss_fn(model(xb), ytr[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        sched.step()
        s_val = scores(model, Xva, ae)
        thr = float(np.quantile(s_val[d.y_val == 0], AE_QUANTILE)) if ae else 0.5
        vm = metrics(d.y_val, s_val, thr)
        history.append({"epoch": epoch, "loss": total / len(perm), "val_f1_macro": vm["f1_macro"],
                        "val_benign_flag_rate": vm["benign_flag_rate"]})
        if vm["f1_macro"] > best["val_f1_macro"]:
            best = {"val_f1_macro": vm["f1_macro"], "epoch": epoch, "threshold": thr,
                    "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
    train_s = time.perf_counter() - t0

    final_val = metrics(d.y_val, scores(model, Xva, ae), thr)  # thr: last epoch's threshold
    final_test = metrics(d.y_test, scores(model, Xte, ae), thr)
    model.load_state_dict(best["state"])
    s_val, s_te = scores(model, Xva, ae), scores(model, Xte, ae)
    unseen = ~d.test_seen
    return {
        "params": n_params(model), "train_seconds": train_s, "best_epoch": best["epoch"],
        "threshold": best["threshold"],
        "val": metrics(d.y_val, s_val, best["threshold"]),
        "test": metrics(d.y_test, s_te, best["threshold"], d.type_test),
        "test_unseen": metrics(d.y_test[unseen], s_te[unseen], best["threshold"]),
        "last_epoch_val": final_val, "last_epoch_test": final_test,
        "cpu_latency_ms": cpu_latency_ms(model, d.X_test[0], ae),
        "history": history,
    }


def train_hgb(d: Prepared, seed: int) -> dict:
    """Gradient boosting reference (not a deep model): shows what a strong non-DL baseline gets."""
    t0 = time.perf_counter()
    clf = HistGradientBoostingClassifier(max_iter=300, early_stopping=True, validation_fraction=0.1,
                                         class_weight="balanced", random_state=seed).fit(d.X_train, d.y_train)
    train_s = time.perf_counter() - t0
    s_val, s_te = clf.predict_proba(d.X_val)[:, 1], clf.predict_proba(d.X_test)[:, 1]
    x = d.X_test[:1]
    times = []
    for i in range(130):
        t1 = time.perf_counter()
        clf.predict_proba(x)
        if i >= 30:
            times.append((time.perf_counter() - t1) * 1e3)
    unseen = ~d.test_seen
    return {"params": None, "train_seconds": train_s, "best_epoch": None, "threshold": 0.5,
            "val": metrics(d.y_val, s_val, 0.5), "test": metrics(d.y_test, s_te, 0.5, d.type_test),
            "test_unseen": metrics(d.y_test[unseen], s_te[unseen], 0.5),
            "cpu_latency_ms": float(np.median(times))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--models", default=",".join(MODEL_NAMES + ["hgb"]))
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    version = code_version()

    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            for mode in (MODES if DATASETS[ds]["fingerprint"] else ["keep"]):
                d = None
                for name in args.models.split(","):
                    out = OUT / ds / mode / f"{name}_s{seed}.json"
                    if out.exists():
                        continue
                    d = d or prepare(ds, mode, seed)
                    t0 = time.perf_counter()
                    res = train_hgb(d, seed) if name == "hgb" else train_torch(name, d, seed, args.device)
                    res.update(dataset=ds, mode=mode, model=name, seed=seed, features=d.input_dim,
                               split=d.report["split"], prep_version=PREP_VERSION, code_version=version,
                               torch=torch.__version__, device=args.device, host=platform.node(),
                               wall_seconds=time.perf_counter() - t0)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(res, indent=1))
                    t = res["test"]
                    print(f"[{ds}/{mode}/{name}/s{seed}] test macroF1={t['f1_macro']:.4f} "
                          f"benign_flag={t['benign_flag_rate']:.4f} unseen_F1={res['test_unseen']['f1_macro']:.4f} "
                          f"params={res['params']} lat={res['cpu_latency_ms']:.3f}ms "
                          f"({res['wall_seconds']:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
