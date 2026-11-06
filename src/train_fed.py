"""Stage 1b -- the same detector zoo trained federated (FedAvg), same data, same protocol.

- K clients (default 10), non-IID: every traffic type's training rows are split over the clients
  with Dirichlet(alpha) proportions. The public datasets have no device field, so clients differ by
  the attack/benign mix they see (the usual IDS-FL setup; stated as a deviation in reports);
- 30 rounds x 1 local epoch = the same 30 passes over the training data as centralized;
- client: AdamW (fresh state each round), batch 512, lr from the server's cosine schedule
  1e-3 -> 1e-4 over rounds, class weights from the summed client class counts (= centralized);
  autoencoder clients train on their benign rows only (clients without benign rows sit out);
- server: FedAvg weighted by client rows, clients in fixed order (same seed = same run). It holds
  the validation split: picks the best round on validation macro-F1 and sets the autoencoder
  threshold (99th percentile of benign validation error). Test is never used to choose;
- reported: test metrics of the best-VAL round (comparable to centralized), of the last round,
  the mean over the last 5 rounds (robust to single-round FedAvg dips), the per-round curves,
  client data mix, and bytes sent per round.

The loop runs in-process (one model, clients trained one after another) -- the same FedAvg maths
as Flower, deterministic and fast; Flower is used for the real deployment (laptop / Raspberry Pi).

Autoencoder threshold: the pre-registered rule is the 99th percentile of benign validation error
(q99). --ae-threshold valopt is a separate, labelled variant (E4): the threshold that maximises
validation macro-F1, written to its own results folder (suffix _aevalopt).

One JSON per run in results/fed/a<alpha>_k<K>[_aevalopt]/<dataset>/<mode>/<model>_s<seed>.json;
finished runs are skipped.

Usage: .venv/bin/python src/train_fed.py --datasets edgeiiot,wustl,forge --seeds 42,43,44,45,46
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from sklearn.metrics import f1_score

from datasets import DATASETS, MODES, PREP_VERSION, Prepared, prepare
from models import MODEL_NAMES, build_model, n_params
from poison import (ADAPTIVE_MARGIN, BACKDOOR_TARGET, ROOT_ROWS, adaptive_boost, aggregate, alie, flatten,
                    malicious_clients, minmax, unflatten)
from train_central import AE_QUANTILE, BATCH, LR_MAX, LR_MIN, code_version, cpu_latency_ms, metrics, scores, seed_all

ROOT = Path(__file__).resolve().parents[1]
ROUNDS, LOCAL_EPOCHS, LAST_K = 30, 1, 5


def partition(types: np.ndarray, k: int, alpha: float, seed: int, min_rows: int = 64) -> list[np.ndarray]:
    """Split row indices over k clients: each traffic type's rows by Dirichlet(alpha) proportions."""
    rng = np.random.default_rng(seed)
    for _ in range(1000):
        parts = [[] for _ in range(k)]
        for t in np.unique(types):
            idx = rng.permutation(np.flatnonzero(types == t))
            cuts = (np.cumsum(rng.dirichlet(np.full(k, alpha))) * len(idx)).astype(int)[:-1]
            for c, chunk in enumerate(np.split(idx, cuts)):
                parts[c].append(chunk)
        parts = [np.sort(np.concatenate(p)) for p in parts]
        if min(len(p) for p in parts) >= min_rows:
            return parts
    raise RuntimeError(f"no Dirichlet({alpha}) split gives every client >= {min_rows} rows")


def cosine_lr(rnd: int) -> float:
    """lr for round rnd (1-based); the same values CosineAnnealingLR gives the centralized epochs."""
    return LR_MIN + 0.5 * (LR_MAX - LR_MIN) * (1 + math.cos(math.pi * (rnd - 1) / ROUNDS))


def ae_threshold(s_val: np.ndarray, y_val: np.ndarray, rule: str) -> float:
    if rule == "q99":
        return float(np.quantile(s_val[y_val == 0], AE_QUANTILE))
    cands = np.unique(np.quantile(s_val, np.linspace(0.005, 0.995, 199)))
    return float(max(cands, key=lambda t: f1_score(y_val, (s_val >= t).astype(int), average="macro")))


def local_train(model: nn.Module, X: torch.Tensor, y: torch.Tensor | None, loss_fn: nn.Module,
                lr: float, gen: torch.Generator) -> None:
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    model.train()
    for _ in range(LOCAL_EPOCHS):
        perm = torch.randperm(len(X), generator=gen, device=X.device)
        for i in range(0, len(perm), BATCH):
            idx = perm[i : i + BATCH]
            xb = X[idx]
            loss = loss_fn(model(xb), xb) if y is None else loss_fn(model(xb), y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()


def fedavg(states: list[dict], weights: list[int]) -> dict:
    w = np.asarray(weights, dtype=np.float64) / sum(weights)
    return {k: sum(float(wi) * s[k].double() for wi, s in zip(w, states)).to(states[0][k].dtype)
            for k in states[0]}


def train_fed(name: str, d: Prepared, seed: int, device: str, k: int, alpha: float, ae_rule: str = "q99",
              on_round=None, keep_state: bool = False, attack: str = "none", n_malicious: int = 0,
              aggregator: str = "fedavg", onset: int = 1, gates: dict | None = None,
              attacked_gate: str | None = None, keep_rounds: bool = False, loo_types: list[str] | None = None,
              trust=None, rollback_gate: str | None = None, poison_budget: str = "full",
              ref_idx: "np.ndarray | None" = None) -> dict:
    """on_round(rnd, global_before, global_after, client_states, client_sizes, val_metrics) is called
    after every aggregation (provenance logging, stage 2). keep_state adds the best-val model state
    under "_state" and the last round's under "_last_state" (not JSON-serialisable; pop both before
    writing).

    Stage 3: attack / n_malicious / aggregator (see poison.py). The defaults (no attack, FedAvg) run
    the original E2 code path unchanged. client_states passed to on_round are what the clients sent,
    poisoned updates included.

    E8: attacks start at round `onset`. `gates` ({name: canary.Gate}) check every round's global
    model on the validation canary; the verdicts are in val_metrics["canary"] for on_round and in
    the result under "gates". backdoor_adaptive plays against gates[attacked_gate]. keep_rounds adds
    every round's global state under "_rounds".

    E9: loo_types (attack types to score) turns on the leave-one-out canary: every round, for each
    client still admitted, the aggregate without that client is scored on the validation canary
    (detection per type in loo_types, benign flag) next to the full aggregate; logged in the curve
    under "loo". trust (client_trust.ClientTrust) turns these into per-client evidence and returns
    clients to revoke. A revoked client's updates are dropped from every later aggregation (it
    still trains locally, so the random stream and the honest clients' training stay paired with
    the run without revocation). On a revocation the round's aggregate is discarded and the
    training state rolls back to the head of gates[rollback_gate] (the genesis model if nothing
    passed yet)."""
    seed_all(seed)
    ae = name == "autoencoder"
    parts = partition(d.type_train, k, alpha, seed)
    X, y = torch.from_numpy(d.X_train).to(device), torch.from_numpy(d.y_train).to(device)
    # R2: reference set for the canary + FLTrust root. Default = the validation split (E7-E9,
    # bit-identical). With ref_idx, a disjoint stratified slice of the training pool, held out of
    # client data, so the canary and root are independent of the val split used for best-val
    # selection and gateway calibration.
    if ref_idx is not None:
        parts = [p[~np.isin(p, ref_idx)] for p in parts]
        rt = torch.from_numpy(ref_idx).to(device)
        X_ref, y_ref, t_ref = X[rt], d.y_train[ref_idx], d.type_train[ref_idx]
    else:
        X_ref, y_ref, t_ref = torch.from_numpy(d.X_val).to(device), d.y_val, d.type_val
    clients = []  # (X_k, y_k or None, n_k) -- autoencoder clients keep benign rows only
    for p in parts:
        p = p[d.y_train[p] == 0] if ae else p
        pt = torch.from_numpy(p).to(device)
        clients.append((X[pt], None if ae else y[pt], len(p)))
    poisoned = attack != "none" or aggregator != "fedavg" or loo_types is not None
    bad = malicious_clients(k, n_malicious, seed) if attack != "none" else []
    assert not (poisoned and ae), "stage 3 uses supervised detectors only"
    honest_clients, clients = clients, list(clients)
    if attack in ("backdoor", "backdoor_adaptive"):
        tgt = torch.from_numpy(np.flatnonzero(d.type_train == BACKDOOR_TARGET[d.dataset])).to(device)
        # R1a: "realistic" poison budget (BackFed) -- partition the target class into distinct
        # per-client subsets instead of giving every malicious client the whole class, and cap each
        # at the client's own benign row count so poison data never exceeds benign data. The adaptive
        # attacker's proxy (X_tgt below) still uses the full target class: that is its knowledge, not
        # its injected data. "full" keeps the E7-E9 worst-case code path bit-identical.
        tgt_rows = {}
        if poison_budget == "realistic" and bad:
            perm = np.random.default_rng([seed, 11]).permutation(tgt.cpu().numpy())
            for c, sl in zip(bad, np.array_split(perm, len(bad))):
                nben = int((clients[c][1] == 0).sum().item())
                tgt_rows[int(c)] = torch.from_numpy(sl[: max(1, nben)]).to(device)
    for c in bad:                                 # data-poisoning attacks change the malicious clients' data
        Xk, yk, nk = clients[c]
        if attack == "label_flip":
            clients[c] = (Xk, 1 - yk, nk)
        elif attack in ("backdoor", "backdoor_adaptive"):
            ti = tgt_rows.get(int(c), tgt)        # realistic slice, else the full class (worst case)
            clients[c] = (torch.cat([Xk, X[ti]]), torch.cat([yk, torch.zeros_like(y[ti])]), nk + len(ti))
    poisoned_clients = clients
    if attack == "backdoor_adaptive":             # the attackers' proxy canary: target rows + their own benign rows
        gate = gates[attacked_gate]
        X_tgt, target_type = X[tgt], BACKDOOR_TARGET[d.dataset]
        X_ben = torch.cat([honest_clients[c][0][honest_clients[c][1] == 0] for c in bad])
        proxy = {}                                # round -> (target detection, benign flag) of that global model

        def proxy_metrics(state: dict) -> tuple[float, float]:
            model.load_state_dict(state)
            return float((scores(model, X_tgt, False) >= 0.5).mean()), float((scores(model, X_ben, False) >= 0.5).mean())
    if aggregator.startswith("fltrust"):          # server's clean root set: a stratified sample of the reference set
        rr = np.random.default_rng([seed, 11])
        root = np.concatenate([rr.choice(np.flatnonzero(y_ref == c), ROOT_ROWS // 2, replace=False) for c in (0, 1)])
        if aggregator == "fltrust_v2":            # tile to the mean client size: same number of local steps
            root = np.tile(np.sort(root), int(np.ceil(np.mean([c[2] for c in clients]) / len(root))))
        root_t = torch.from_numpy(np.sort(root)).to(device)
        X_root, y_root = X_ref[root_t], torch.from_numpy(y_ref).to(device)[root_t]
    Xva, Xte = torch.from_numpy(d.X_val).to(device), torch.from_numpy(d.X_test).to(device)

    counts = sum(np.bincount(d.y_train[p], minlength=2) for p in parts).astype(np.float64)  # server sums client counts
    weights = torch.tensor(counts.sum() / (2 * counts), dtype=torch.float32, device=device)
    loss_fn = nn.MSELoss() if ae else nn.CrossEntropyLoss(weight=weights)
    model = build_model(name, d.input_dim).to(device)
    global_state = {kk: v.detach().clone() for kk, v in model.state_dict().items()}
    gen = torch.Generator(device=device).manual_seed(seed)
    revoked: set[int] = set()
    if loo_types is not None:                     # E9: canary scoring of candidate aggregates
        genesis, versions = global_state, {}
        masks = {t: t_ref == t for t in loo_types} | {"benign": y_ref == 0}

        def canary(state: dict) -> dict[str, float]:
            model.load_state_dict(state)
            flag = scores(model, X_ref, False) >= 0.5
            return {t: float(flag[mk].mean()) for t, mk in masks.items()}

    best = {"val_f1_macro": -1.0}
    curve, rounds = [], []
    t0 = time.perf_counter()
    for rnd in range(1, ROUNDS + 1):
        t_round = time.perf_counter()
        lr = cosine_lr(rnd)
        active = rnd >= onset
        clients = poisoned_clients if active else honest_clients
        states, sizes = [], []
        for Xk, yk, nk in clients:
            if nk == 0:
                continue
            model.load_state_dict(global_state)
            local_train(model, Xk, yk, loss_fn, lr, gen)
            states.append({kk: v.detach().clone() for kk, v in model.state_dict().items()})
            sizes.append(nk)
        agg_info = None
        if not poisoned:
            global_before, global_state = global_state, fedavg(states, sizes)
        else:
            U = np.stack([flatten(s, global_state) for s in states])
            good = [c for c in range(len(U)) if c not in bad]
            g0 = None
            if aggregator.startswith("fltrust"):  # computed first: an omniscient attacker may use it
                model.load_state_dict(global_state)
                local_train(model, X_root, y_root, loss_fn, lr, gen)
                g0 = flatten(model.state_dict(), global_state)
            lam = None
            live = [i for i in range(len(U)) if i not in revoked]

            def agg_live(V: np.ndarray, drop=()) -> tuple[np.ndarray, dict]:
                drop = {drop} if isinstance(drop, int) else set(drop)
                keep = [i for i in live if i not in drop]
                return aggregate(aggregator, V[keep], [sizes[i] for i in keep], n_malicious, g0)
            if not active:
                pass
            elif attack == "backdoor":
                U[bad] *= k / len(bad)            # model replacement boost
            elif attack == "backdoor_adaptive":
                th = gate.thresholds()
                if th is None:                    # gate still in warm-up: nothing to evade
                    lam = k / len(bad)
                else:                             # the attacker's estimate of the references
                    ref = [proxy[r] for r in gate.promoted if r >= gate.warmup]
                    if ref:                       # E8 Gate: allowance = delta; StatGate: its tolerance
                        allow_t, allow_b = gate.allowance()
                        need_t = max(p[0] for p in ref) - ADAPTIVE_MARGIN * allow_t.get(target_type, gate.delta)
                        need_b = min(p[1] for p in ref) + ADAPTIVE_MARGIN * allow_b
                    else:                         # StatGate SLO in the warm-up: the floor plus the margin
                        need_t = th[0].get(target_type, 0.0) + (1 - ADAPTIVE_MARGIN) * gate.delta
                        need_b = 1.0

                    def passes(V: np.ndarray) -> bool:
                        det_t, flag_b = proxy_metrics(unflatten(agg_live(V)[0], global_state))
                        return det_t >= need_t and flag_b <= need_b

                    lam = adaptive_boost(U, bad, k / len(bad), passes)
                U[bad] *= lam
            elif attack == "alie":
                U[bad] = alie(U[good], len(U), len(bad))
            elif attack == "minmax":
                U[bad] = minmax(U[good])
            agg, agg_info = agg_live(U)
            if lam is not None:
                agg_info = agg_info | {"boost": lam}
            if bad:
                states = [unflatten(u, global_state) for u in U]   # what was actually sent
            new_state = unflatten(agg, global_state)
            if loo_types is not None:
                full = canary(new_state)
                loo = {i: canary(unflatten(agg_live(U, drop=i)[0], global_state)) for i in live}
                agg_info = (agg_info or {}) | {"loo_full": full, "loo": loo, "revoked_before": sorted(revoked)}
                newly = trust.update(rnd, full, loo, lambda ex: canary(unflatten(agg_live(U, drop=ex)[0], global_state))
                                     ) if trust is not None else []
                if newly:                         # revoke, discard this aggregate, roll back
                    revoked |= set(newly)
                    head = gates[rollback_gate].promoted
                    new_state = versions[head[-1]] if head else genesis
                    agg_info |= {"revoked": sorted(newly), "rollback_to": head[-1] if head else 0}
            global_before, global_state = global_state, new_state
        if attack == "backdoor_adaptive":
            proxy[rnd] = proxy_metrics(global_state)
        model.load_state_dict(global_state)
        s_val = scores(model, Xva, ae)
        thr = ae_threshold(s_val, d.y_val, ae_rule) if ae else 0.5
        vm = metrics(d.y_val, s_val, thr, d.type_val if gates else None)
        tm = metrics(d.y_test, scores(model, Xte, ae), thr)
        if gates:
            # the canary verdict is computed on the reference set (val by default; the disjoint
            # train slice under R2) -- vm stays on val for best-val selection and logging.
            rm = vm if ref_idx is None else metrics(y_ref, scores(model, X_ref, ae), thr, t_ref)
            vm["canary"] = {name: g.check(rnd, rm["detection_by_type"], rm["benign_flag_rate"], rm["f1_macro"])
                            for name, g in gates.items()}
            if loo_types is not None:
                vm["revoked"] = {c: trust.stat[c] for c in (agg_info or {}).get("revoked", [])}
                vm["rollback_to"] = (agg_info or {}).get("rollback_to")
            if loo_types is not None and rollback_gate and vm["canary"][rollback_gate]:
                versions[rnd] = {kk: v.detach().clone() for kk, v in global_state.items()}
        if keep_rounds:
            rounds.append({kk: v.detach().clone() for kk, v in global_state.items()})
        if on_round is not None:
            on_round(rnd, global_before, global_state, states, sizes, vm)
        curve.append({"round": rnd, "lr": lr, "clients": len(states), "seconds": time.perf_counter() - t_round,
                      "val_f1_macro": vm["f1_macro"], "val_benign_flag_rate": vm["benign_flag_rate"],
                      "test_f1_macro": tm["f1_macro"], "test_benign_flag_rate": tm["benign_flag_rate"]}
                     | ({"agg": agg_info} if agg_info else {})
                     | ({"val_detection_by_type": vm["detection_by_type"], "canary": vm["canary"]} if gates else {}))
        if vm["f1_macro"] > best["val_f1_macro"]:
            best = {"val_f1_macro": vm["f1_macro"], "round": rnd, "threshold": thr,
                    "state": {kk: v.detach().clone() for kk, v in global_state.items()}}
    train_s = time.perf_counter() - t0

    last_round = {"val": metrics(d.y_val, scores(model, Xva, ae), thr),
                  "test": metrics(d.y_test, scores(model, Xte, ae), thr, d.type_test)}
    tail = curve[-LAST_K:]
    last5 = {key: float(np.mean([c[f"test_{key}"] for c in tail])) for key in ("f1_macro", "benign_flag_rate")}
    last5["f1_macro_min"] = float(min(c["test_f1_macro"] for c in tail))
    model.load_state_dict(best["state"])
    s_val, s_te = scores(model, Xva, ae), scores(model, Xte, ae)
    unseen = ~d.test_seen
    params = n_params(model)
    extra = ({"_state": best["state"], "_last_state": global_state} if keep_state else {}) | (
        {"_rounds": rounds} if keep_rounds else {})
    return extra | {
        "params": params, "train_seconds": train_s, "best_round": best["round"], "threshold": best["threshold"],
        "val": metrics(d.y_val, s_val, best["threshold"]),
        "test": metrics(d.y_test, s_te, best["threshold"], d.type_test),
        "test_unseen": metrics(d.y_test[unseen], s_te[unseen], best["threshold"]),
        "last_round": last_round, "last5": last5,
        "bytes_per_round": 2 * 4 * params * curve[-1]["clients"],  # float32 down + up, participating clients
        "clients": [{"rows": len(p), "benign_share": float((d.y_train[p] == 0).mean()),
                     "types": int(len(np.unique(d.type_train[p])))} for p in parts],
        "cpu_latency_ms": cpu_latency_ms(model, d.X_test[0], ae),
        "curve": curve,
    } | ({"attack": attack, "aggregator": aggregator, "malicious": bad} if poisoned else {}) | (
        {"revoked": sorted(revoked)} if loo_types is not None else {}) | (
        {"onset": onset, "gates": {name: {"types": g.types, "delta": g.delta, "delta_benign": g.delta_benign,
                                          "warmup": g.warmup, "promoted": g.promoted, "log": g.log}
                                   for name, g in gates.items()}} if gates else {})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--models", default=",".join(MODEL_NAMES))
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--clients", type=int, default=10)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--ae-threshold", choices=["q99", "valopt"], default="q99")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    version = code_version()
    suffix = "" if args.ae_threshold == "q99" else f"_ae{args.ae_threshold}"
    out_root = ROOT / "results" / "fed" / f"a{args.alpha:g}_k{args.clients}{suffix}"

    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            for mode in (MODES if DATASETS[ds]["fingerprint"] else ["keep"]):
                d = None
                for name in args.models.split(","):
                    out = out_root / ds / mode / f"{name}_s{seed}.json"
                    if out.exists():
                        continue
                    d = d or prepare(ds, mode, seed)
                    t0 = time.perf_counter()
                    res = train_fed(name, d, seed, args.device, args.clients, args.alpha, args.ae_threshold)
                    res.update(dataset=ds, mode=mode, model=name, seed=seed, features=d.input_dim,
                               n_clients=args.clients, alpha=args.alpha, rounds=ROUNDS, local_epochs=LOCAL_EPOCHS,
                               ae_threshold=args.ae_threshold if name == "autoencoder" else None,
                               split=d.report["split"], prep_version=PREP_VERSION, code_version=version,
                               torch=torch.__version__, device=args.device, host=platform.node(),
                               wall_seconds=time.perf_counter() - t0)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(res, indent=1))
                    t, l5 = res["test"], res["last5"]
                    print(f"[{ds}/{mode}/{name}/s{seed}] best-val r{res['best_round']} test macroF1={t['f1_macro']:.4f} "
                          f"benign_flag={t['benign_flag_rate']:.4f} last5={l5['f1_macro']:.4f} (min {l5['f1_macro_min']:.4f}) "
                          f"unseen_F1={res['test_unseen']['f1_macro']:.4f} ({res['wall_seconds']:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
