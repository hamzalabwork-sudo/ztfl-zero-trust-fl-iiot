"""Stage 3 -- poisoning attacks on the federated detector and robust aggregation rules (claim C1).

Updates are handled as flat float64 vectors u_k = client_state_k - global_state.

Attacks (a fixed, seed-chosen set of malicious clients; they collude and know the aggregation rule):
- label_flip: malicious clients train honestly but on flipped labels (y -> 1 - y).
- alie: "a little is enough" (Baruch et al., 2019). Every malicious client sends mu - z * sigma, the
  coordinate-wise mean / std of the honest updates; z from the number of clients and attackers.
- minmax: Shejwalkar & Houmansadr (2021, NDSS). mu + gamma * p with p = -sigma (unit-normalised),
  gamma as large as possible while the malicious update stays within the largest honest-honest distance.
- backdoor ("whitelist-me", targeted): malicious clients add the training rows of the target attack
  type relabelled benign to their data, and scale their update by K / m (model replacement,
  Bagdasaryan et al., 2020). Success = the target type is scored benign, i.e. granted.
- backdoor_adaptive (E8): the backdoor against the canary check (canary.py). The attackers know the
  rule, delta and the public registry of promoted versions, but not the canary rows. They track their
  own proxy (the target-type training rows and their own benign rows) on every promoted version, and
  scale the boost to the largest lambda in [0, K/m] whose aggregate still passes the proxy check
  with a 20% safety margin. During the gate's warm-up they boost fully.
The model-poisoning attacks (alie, minmax, backdoor_adaptive) are omniscient: they see all honest
updates of the round, the standard worst case in these papers. Attacks start at round `onset`;
before it the malicious clients behave honestly.

Aggregators: fedavg (row-weighted mean), median (coordinate-wise), trimmed_mean (coordinate-wise,
drop the f largest and f smallest), multi_krum (Blanchard et al., 2017; keep the K - f updates with
the lowest Krum score, average them), fltrust (Cao et al., 2021; trust = ReLU(cos(u_k, g0)) against
the server's update g0 on a small clean root set, updates rescaled to ||g0||). fltrust as first run
trained g0 on the 500-row root set for one epoch = ONE optimiser step, while clients take 20-70, so
g0 was close to a sign vector (implementation error, kept as recorded). fltrust_v2 is the faithful
version: the root set is tiled to the mean client size, so the server takes as many steps as an
average client, as in Cao et al. f = the number of
malicious clients the defender assumes (set to the true m: the defender's best case).
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.stats import norm

ATTACKS = ("none", "label_flip", "alie", "minmax", "backdoor", "backdoor_adaptive")
ADAPTIVE_MARGIN = 0.8                             # the adaptive attacker aims at 80% of the allowed drop
AGGREGATORS = ("fedavg", "median", "trimmed_mean", "multi_krum", "fltrust", "fltrust_v2")
BACKDOOR_TARGET = {"edgeiiot": "Backdoor", "forge": "malw_back", "wustl": "Backdoor"}
ROOT_ROWS = 500                                   # FLTrust root set, drawn from the server's validation split


def flatten(state: dict, ref: dict) -> np.ndarray:
    return torch.cat([(state[k].double() - ref[k].double()).flatten() for k in ref]).cpu().numpy()


def unflatten(u: np.ndarray, ref: dict) -> dict:
    out, i = {}, 0
    for k, v in ref.items():
        n = v.numel()
        out[k] = (v.double() + torch.from_numpy(u[i:i + n]).to(v.device).view_as(v)).to(v.dtype)
        i += n
    return out


def alie(honest: np.ndarray, n: int, m: int) -> np.ndarray:
    s = n // 2 + 1 - m                            # supporters needed for a majority
    z = norm.ppf((n - s) / n) if 0 < s < n else 1.0
    return honest.mean(0) - z * honest.std(0)


def minmax(honest: np.ndarray) -> np.ndarray:
    mu, p = honest.mean(0), -honest.std(0)
    p /= np.linalg.norm(p) + 1e-12
    d_max = max(np.linalg.norm(a - b) for a in honest for b in honest)
    lo, hi = 0.0, 1.0
    while np.linalg.norm(honest - (mu + hi * p), axis=1).max() <= d_max:
        hi *= 2
    for _ in range(30):                           # binary search for the largest admissible gamma
        g = (lo + hi) / 2
        lo, hi = (g, hi) if np.linalg.norm(honest - (mu + g * p), axis=1).max() <= d_max else (lo, g)
    return mu + lo * p


def adaptive_boost(U: np.ndarray, bad: list[int], lam_max: float, passes, steps: int = 12) -> float:
    """Largest boost lambda in [0, lam_max] for the malicious rows of U with passes(U') True."""
    raw = U[bad].copy()

    def at(lam: float) -> np.ndarray:
        V = U.copy()
        V[bad] = lam * raw
        return V

    if passes(at(lam_max)):
        return lam_max
    lo, hi = 0.0, lam_max
    for _ in range(steps):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if passes(at(mid)) else (lo, mid)
    return lo


def aggregate(rule: str, U: np.ndarray, sizes: list[int], f: int, g0: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Aggregate update vectors U (n, d). Returns the aggregate and per-client info (kept / trust)."""
    n = len(U)
    w = np.asarray(sizes, dtype=np.float64)
    if rule == "fedavg":
        return (w / w.sum()) @ U, {"weight": (w / w.sum()).tolist()}
    if rule == "median":
        return np.median(U, axis=0), {}
    if rule == "trimmed_mean":
        b = min(f, (n - 1) // 2)
        return np.sort(U, axis=0)[b:n - b].mean(0), {"trim_each_side": b}
    if rule == "multi_krum":
        d2 = ((U[:, None, :] - U[None, :, :]) ** 2).sum(-1)
        k = max(n - f - 2, 1)
        score = np.sort(d2, axis=1)[:, 1:k + 1].sum(1)
        keep = np.argsort(score)[: n - f]
        return (w[keep] / w[keep].sum()) @ U[keep], {"kept": sorted(int(i) for i in keep)}
    if rule in ("fltrust", "fltrust_v2"):
        g_norm = np.linalg.norm(g0) + 1e-12
        norms = np.linalg.norm(U, axis=1) + 1e-12
        ts = np.maximum(0.0, U @ g0 / (norms * g_norm))
        if ts.sum() == 0:
            return g0.copy(), {"trust": ts.tolist()}
        return (ts[:, None] * U * (g_norm / norms)[:, None]).sum(0) / ts.sum(), {"trust": ts.tolist()}
    raise ValueError(rule)


def malicious_clients(k: int, m: int, seed: int) -> list[int]:
    return sorted(int(c) for c in np.random.default_rng([seed, 7]).choice(k, m, replace=False))
