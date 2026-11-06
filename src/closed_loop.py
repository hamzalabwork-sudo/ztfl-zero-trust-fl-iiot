"""Stage 2 -- closed-loop Zero-Trust simulator (semi-synthetic): claims C2 and C3.

One run = one (dataset, mode, seed):

1. Federated detector. train_fed (default MLP, Dirichlet alpha 0.5, K 10, 30 rounds). Every round
   goes on the provenance ledger: global model hash, client update hashes and sizes. The
   best-validation round is deployed at the gateway.
2. Server-side calibration on the validation split (test is never used for this):
   - score evidence LLR(s) = log f1(z) / f0(z), where z is the logit of the detector's P(attack)
     and f0 / f1 are smoothed per-class histograms;
   - each policy's alarm threshold is set so that at most BUDGET (1%) of benign validation device
     streams are ever isolated. All policies share the same false-isolation budget, which makes
     the comparison fair.
3. Device streams from the TEST split: N_DEV devices x T_EV events each.
   - A share COMPROMISED of the devices is compromised at an unknown time tau.
   - After tau, each event is an attack row with probability rho (one attack type per device);
     otherwise it is benign.
   - Each attack event targets a random other device.
   - Rows are drawn i.i.d. from the pools, so device identity and timing are synthetic. The
     emulated testbed (stage 4) replaces this with real per-device traffic.
4. Gateway policies, run on the same streams (paired comparison):
   - per_event: deny an event if s >= 0.5; never isolate (packet-level IDS gate).
   - ewma: also isolate when EWMA trust T <- lam*T + (1-lam)*(1-s) drops below theta. This is the
     weighted-trust formulation (aV + bC + gD) with only the detector term.
   - cusum: also isolate when the CUSUM of LLR exceeds h (quickest change detection).
   - cusum_sprt: like cusum, but an alarm starts a quarantine SPRT on the next events. The device
     is re-admitted when the test accepts benign; it is blocked when the test accepts attack or
     after Q_MAX undecided events. The attack hypothesis is "every event is an attack".
   - cusum_sprt_mix: the same, but the quarantine SPRT tests against a low-rate attacker, "a share
     RHO_MIN of events are attacks": LLR_mix = log(RHO_MIN * e^LLR + 1 - RHO_MIN).
   Every policy also applies the per-event deny. Isolated and quarantined devices are denied.
5. Access-control metrics:
   - wrongful-grant rate: attack events let through;
   - benign denial rate: events of benign devices that were denied (collateral damage);
   - false-isolation rate: benign devices ever isolated;
   - premature isolation: compromised devices isolated before tau;
   - detection share and time-to-isolation (events after tau);
   - false re-authorisation rate: compromised devices re-admitted while still compromised;
   - lateral reach: distinct devices a compromised device reached with granted attack events.
   Decision batches are digested and recorded on the ledger, tagged with the model version that
   made them.

Results: results/closed_loop/<llr>_<cusum-threshold>/<dataset>/<mode>/<model>_s<seed>.json (+ ..._ledger.json)
Usage: python src/closed_loop.py --datasets edgeiiot,forge,wustl --seeds 42,43,44,45,46
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.isotonic import IsotonicRegression

from datasets import PREP_VERSION, prepare
from ledger import EvmLedger, MemoryLedger, batch_digest, state_hash, update_hash
from models import SUPERVISED, build_model
from train_central import code_version, scores
from train_fed import train_fed

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "closed_loop"
SETTINGS = {"edgeiiot": "keep", "forge": "nofp", "wustl": "nofp"}  # nofp: no host-fingerprint features

N_DEV, T_EV, COMPROMISED, TAU_RANGE = 1000, 500, 0.2, (100, 300)
RHOS = (1.0, 0.5, 0.2)                  # share of a compromised device's events that are attacks
BUDGET, N_CAL = 0.01, 2000              # benign false-isolation budget, calibration streams
EWMA_LAMBDA = 0.9
SPRT_ALPHA = SPRT_BETA = 0.01
SPRT_A, SPRT_B = np.log((1 - SPRT_BETA) / SPRT_ALPHA), np.log(SPRT_BETA / (1 - SPRT_ALPHA))
Q_MAX = 100
RHO_MIN = 0.1                           # low-rate attacker the mixture SPRT must catch
BINS = np.linspace(-16, 16, 65)
LLR_CLIP = 8.0
DECISION_BATCH = 100                    # events per ledger decision record
POLICIES = ("per_event", "ewma", "cusum", "cusum_sprt", "cusum_sprt_mix")


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p.astype(np.float64), 1e-7, 1 - 1e-7)
    return np.log(p) - np.log1p(-p)


class Evidence:
    """Per-event log-likelihood ratio of the detector score, from validation histograms.

    hist: raw smoothed histogram ratio (E5). Empty bins get log(n_benign / n_attack), so an
    extreme attack-like score that never occurred in validation can count as benign evidence.
    monotone (E5b/E5c): isotonic (pool-adjacent-violators) fit of the bin LLRs, weighted by bin
    counts, so the LLR never decreases as the score grows; empty bins inherit their neighbours.
    E5e variants (both monotone):
    monotone_balanced: the attack likelihood is the equal-weight mixture of the per-attack-type
    histograms, so a rare type's score region is not drowned by the frequent types. It is still a
    density, so Lorden's bound (E_0[e^LLR] = 1) holds as before.
    monotone_floor: bins with score >= 0.5 (logit >= 0) get LLR >= 0: an event the per-event gate
    flags never counts as benign evidence. This breaks E_0[e^LLR] <= 1 slightly.
    """

    def __init__(self, s_val: np.ndarray, y_val: np.ndarray, mode: str = "hist", types_val: np.ndarray | None = None):
        z = np.clip(logit(s_val), BINS[0], BINS[-1])  # keep saturated scores inside the end bins
        n0, n1 = np.histogram(z[y_val == 0], BINS)[0], np.histogram(z[y_val == 1], BINS)[0]
        f0, f1 = n0 + 0.5, n1 + 0.5
        if mode == "monotone_balanced":
            at = np.unique(types_val[y_val == 1])
            f1 = np.mean([np.histogram(z[types_val == t], BINS)[0] / (types_val == t).sum() for t in at], axis=0)
            f1 = f1 + 0.5 / n1.sum()
        table = np.log(f1 / f1.sum()) - np.log(f0 / f0.sum())
        if mode.startswith("monotone"):
            table = IsotonicRegression().fit_transform(np.arange(len(table)), table, sample_weight=n0 + n1 + 1e-3)
        if mode == "monotone_floor":
            table = np.where(BINS[:-1] >= 0, np.maximum(table, 0.0), table)
        self.table = np.clip(table, -LLR_CLIP, LLR_CLIP)

    def __call__(self, s: np.ndarray) -> np.ndarray:
        return self.table[np.clip(np.digitize(logit(s), BINS) - 1, 0, len(self.table) - 1)]


def make_streams(rng, s, y, types, rho, only_type: str | None = None):
    """Scores S (n, t), attack mask A, compromise time tau (t_ev = never), attack targets, and each
    device's attack type ("" = never compromised). only_type: every compromised device uses this
    attack type (stage 3 backdoor target); the RNG draws are the same either way."""
    n, t = N_DEV, T_EV
    benign = np.flatnonzero(y == 0)
    attack_types = np.unique(types[y == 1]) if only_type is None else np.array([only_type])
    S = s[rng.choice(benign, (n, t))]
    A = np.zeros((n, t), dtype=bool)
    tau = np.full(n, t)
    dev_type = np.full(n, "", dtype=object)
    for dev in rng.permutation(n)[: int(round(COMPROMISED * n))]:
        tau[dev] = rng.integers(*TAU_RANGE)
        dev_type[dev] = rng.choice(attack_types)
        pool = np.flatnonzero(types == dev_type[dev])
        hit = (np.arange(t) >= tau[dev]) & (rng.random(t) < rho)
        A[dev, hit] = True
        S[dev, hit] = s[rng.choice(pool, hit.sum())]
    target = (np.arange(n)[:, None] + rng.integers(1, n, (n, t))) % n
    return S, A, tau, target, dev_type


def extreme(S: np.ndarray, L: np.ndarray, policy: str) -> np.ndarray:
    """Per-stream extreme of the policy statistic with no isolation (for threshold calibration)."""
    if policy == "ewma":
        trust, low = np.ones(len(S)), np.ones(len(S))
        for i in range(S.shape[1]):
            trust = EWMA_LAMBDA * trust + (1 - EWMA_LAMBDA) * (1 - S[:, i])
            low = np.minimum(low, trust)
        return low
    c, high = np.zeros(len(S)), np.zeros(len(S))
    for i in range(S.shape[1]):
        c = np.maximum(0.0, c + L[:, i])
        high = np.maximum(high, c)
    return high


def gate(S: np.ndarray, L: np.ndarray, policy: str, th: float):
    """Run one gateway policy. Returns granted (n, t), admitted (n, t), re-admission events."""
    n, t = S.shape
    sprt = policy.startswith("cusum_sprt")
    Lq = np.log(RHO_MIN * np.exp(L) + 1 - RHO_MIN) if policy == "cusum_sprt_mix" else L  # quarantine evidence
    flag = S >= 0.5
    granted = np.zeros((n, t), dtype=bool)
    admitted = np.zeros((n, t), dtype=bool)
    state = np.zeros(n, dtype=np.int8)           # 0 admitted, 1 quarantine, 2 blocked
    stat = np.ones(n) if policy == "ewma" else np.zeros(n)
    lam, qlen = np.zeros(n), np.zeros(n, dtype=int)
    readmits = []                                # (device, event index)
    for i in range(t):
        act = state == 0
        admitted[:, i] = act
        granted[:, i] = act & ~flag[:, i]
        if policy == "per_event":
            continue
        if sprt:                                 # quarantined devices: one SPRT step
            q = state == 1
            lam[q] += Lq[q, i]
            qlen[q] += 1
            ok, bad = q & (lam <= SPRT_B), q & ((lam >= SPRT_A) | (qlen >= Q_MAX))
            state[ok], stat[ok] = 0, 0.0
            state[bad & ~ok] = 2
            readmits += [(int(dv), i) for dv in np.flatnonzero(ok)]
        if policy == "ewma":
            stat[act] = EWMA_LAMBDA * stat[act] + (1 - EWMA_LAMBDA) * (1 - S[act, i])
            alarm = act & (stat < th)
        else:
            stat[act] = np.maximum(0.0, stat[act] + L[act, i])
            alarm = act & (stat > th)
        if sprt:
            state[alarm], lam[alarm], qlen[alarm] = 1, 0.0, 0
        else:
            state[alarm] = 2
    return granted, admitted, readmits


def access_metrics(granted, admitted, readmits, A, tau, target) -> dict:
    n, t = A.shape
    comp = tau < t
    idx = np.arange(t)
    out_after = ~admitted & (idx[None, :] >= tau[:, None])  # not admitted at/after compromise
    detected = out_after.any(axis=1) & comp
    tti = np.where(detected, out_after.argmax(axis=1) - tau, -1)
    premature = comp & (~admitted & (idx[None, :] < tau[:, None])).any(axis=1)
    false_reauth = {dv for dv, i in readmits if comp[dv] and i >= tau[dv]}
    quarantined_after = int(detected.sum())
    reach = [len(np.unique(target[dv, granted[dv] & A[dv]])) for dv in np.flatnonzero(comp)]
    return {
        "wrongful_grant_rate": float(granted[A].mean()),
        "benign_denial_rate": float(1 - granted[~comp].mean()),  # benign devices only
        "false_isolation_rate": float((~admitted[~comp]).any(axis=1).mean()),
        "benign_blocked_at_end": float((~admitted[~comp, -1]).mean()),
        "premature_isolation_rate": float(premature[comp].mean()),
        "detection_rate": float(detected[comp].mean()),
        "tti_median": float(np.median(tti[detected])) if detected.any() else None,
        "tti_p90": float(np.percentile(tti[detected], 90)) if detected.any() else None,
        "false_reauth_rate": len(false_reauth) / quarantined_after if quarantined_after else None,
        "lateral_reach_mean": float(np.mean(reach)),
        "granted_attacks_per_compromised": float(np.mean([(granted[dv] & A[dv]).sum() for dv in np.flatnonzero(comp)])),
    }


def deploy(ds: str, mode: str, seed: int, model_name: str, device: str, ledger: MemoryLedger):
    """Train the federated detector (every round recorded on the ledger) and score validation and
    test with the deployed best-val model. Returns (data, fed result, deployed hash, s_val, s_te)."""
    d = prepare(ds, mode, seed)

    def on_round(rnd, before, after, client_states, sizes, vm):
        ledger.record_round(rnd, state_hash(after), [update_hash(c, before) for c in client_states], sizes, vm["f1_macro"])

    fed = train_fed(model_name, d, seed, device, k=10, alpha=0.5, on_round=on_round, keep_state=True)
    model = build_model(model_name, d.input_dim).to(device)
    model.load_state_dict(fed.pop("_state"))
    fed.pop("_last_state")
    deployed = state_hash(model.state_dict())
    s_val = scores(model, torch.from_numpy(d.X_val).to(device), False).astype(np.float64)
    s_te = scores(model, torch.from_numpy(d.X_test).to(device), False).astype(np.float64)
    return d, fed, deployed, s_val, s_te


def run(ds: str, mode: str, seed: int, model_name: str, device: str, ledger: MemoryLedger | None = None,
        llr_mode: str = "hist", h_mode: str = "empirical") -> dict:
    """llr_mode: hist | monotone (see Evidence). h_mode for the CUSUM family: empirical = (1 - BUDGET)
    quantile of the max CUSUM on benign validation streams (E5, E5b); lorden = log(T_EV / BUDGET),
    from Lorden's bound ARL0 >= e^h, so P(false alarm within T_EV events) <~ T_EV * e^-h = BUDGET
    (E5c). EWMA has no such bound and is always calibrated empirically."""
    t0 = time.perf_counter()
    ledger = ledger or MemoryLedger()
    d, fed, deployed, s_val, s_te = deploy(ds, mode, seed, model_name, device, ledger)

    llr = Evidence(s_val, d.y_val, llr_mode)
    rng = np.random.default_rng(seed)
    S_cal = s_val[rng.choice(np.flatnonzero(d.y_val == 0), (N_CAL, T_EV))]
    L_cal = llr(S_cal)
    h = float(np.log(T_EV / BUDGET)) if h_mode == "lorden" else float(np.quantile(extreme(S_cal, L_cal, "cusum"), 1 - BUDGET))
    thresholds = {"per_event": 0.5, "ewma": float(np.quantile(extreme(S_cal, L_cal, "ewma"), BUDGET)), "cusum": h}
    thresholds["cusum_sprt"] = thresholds["cusum_sprt_mix"] = thresholds["cusum"]

    results = {}
    for rho in RHOS:
        S, A, tau, target, _ = make_streams(np.random.default_rng([seed, int(rho * 100)]), s_te, d.y_test, d.type_test, rho)
        L = llr(S)
        results[f"rho{rho:g}"] = {}
        for policy in POLICIES:
            granted, admitted, readmits = gate(S, L, policy, thresholds[policy])
            for a in range(0, T_EV, DECISION_BATCH):
                b = min(a + DECISION_BATCH, T_EV)
                ledger.record_decisions(deployed, f"{policy}/rho{rho:g}", a, b, granted[:, a:b].size,
                                        batch_digest(granted[:, a:b], admitted[:, a:b]))
            results[f"rho{rho:g}"][policy] = access_metrics(granted, admitted, readmits, A, tau, target)

    best_block = next(b for b in ledger.blocks if b["kind"] == "round" and b["model"] == deployed)
    t_sim = time.perf_counter() - t0
    chain = ledger.flush() | {"trusted_deployed": ledger.is_trusted(deployed)} if hasattr(ledger, "flush") else None
    return {
        "dataset": ds, "mode": mode, "seed": seed, "model": model_name,
        "detector": {"best_round": fed["best_round"], "test_f1_macro": fed["test"]["f1_macro"],
                     "test_benign_flag_rate": fed["test"]["benign_flag_rate"], "deployed_model": deployed,
                     "deployed_round_on_ledger": best_block["round"]},
        "config": {"llr_mode": llr_mode, "h_mode": h_mode, "n_dev": N_DEV, "t_ev": T_EV, "compromised": COMPROMISED, "tau_range": TAU_RANGE,
                   "budget": BUDGET, "n_cal": N_CAL, "ewma_lambda": EWMA_LAMBDA, "sprt_alpha": SPRT_ALPHA,
                   "sprt_beta": SPRT_BETA, "q_max": Q_MAX, "rho_min": RHO_MIN, "llr_clip": LLR_CLIP},
        "thresholds": thresholds, "llr_table": llr.table.tolist(), "results": results,
        "ledger": ledger.summary(), "chain": chain, "_ledger_blocks": ledger.blocks,
        "prep_version": PREP_VERSION, "code_version": code_version(), "torch": torch.__version__,
        "device": device, "host": platform.node(), "sim_seconds": t_sim, "wall_seconds": time.perf_counter() - t0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="edgeiiot,forge,wustl")
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--model", default="mlp", choices=SUPERVISED)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--ledger", choices=["memory", "evm"], default="memory")
    ap.add_argument("--rpc", default="http://127.0.0.1:18545", help="EVM node (evm ledger only)")
    ap.add_argument("--chain-tag", default="anvil", help="results/chain/<tag>/ subfolder (evm ledger only)")
    ap.add_argument("--llr", choices=["hist", "monotone"], default="hist")
    ap.add_argument("--cusum-threshold", choices=["empirical", "lorden"], default="empirical")
    args = ap.parse_args()
    calib = f"{args.llr}_{args.cusum_threshold}"
    out_root = OUT / calib if args.ledger == "memory" else ROOT / "results" / "chain" / args.chain_tag
    artifact = ROOT / "contracts" / "out" / "Provenance.sol" / "Provenance.json"
    for seed in map(int, args.seeds.split(",")):
        for ds in args.datasets.split(","):
            mode = SETTINGS[ds]
            out = out_root / ds / mode / f"{args.model}_s{seed}.json"
            if out.exists():
                continue
            ledger = EvmLedger(args.rpc, str(artifact)) if args.ledger == "evm" else None
            res = run(ds, mode, seed, args.model, args.device, ledger, args.llr, args.cusum_threshold)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.with_name(out.stem + "_ledger.json").write_text(json.dumps(res.pop("_ledger_blocks"), indent=1))
            out.write_text(json.dumps(res, indent=1))
            print(f"[{ds}/{mode}/{args.model}/s{seed}] detector F1={res['detector']['test_f1_macro']:.4f} "
                  f"ledger={res['ledger']['blocks']} blocks verified={res['ledger']['verified']} "
                  f"({res['wall_seconds']:.0f}s)", flush=True)
            if res["chain"]:
                print(f"   chain: {json.dumps(res['chain'])}", flush=True)
            for rho, per in res["results"].items():
                for policy, m in per.items():
                    print(f"   {rho:7s} {policy:10s} wrongful_grant={m['wrongful_grant_rate']:.4f} "
                          f"false_iso={m['false_isolation_rate']:.3f} detect={m['detection_rate']:.2f} "
                          f"tti_med={m['tti_median']} reauth_false={m['false_reauth_rate']} "
                          f"reach={m['lateral_reach_mean']:.1f}", flush=True)


if __name__ == "__main__":
    main()
