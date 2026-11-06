"""E9 -- continuous authorization of FL clients: per-client CUSUM on leave-one-out canary evidence.

Each round the server has, for every admitted client i, the canary profile of the aggregate
without i next to the full aggregate (train_fed, loo_types). Per checked attack type t the change

    D_it = det_t(without i) - det_t(full)        (benign: flag(full) - flag(without i))

is how much removing i restores detection of t (or lowers the benign flag). A backdoor or
label-flip client pushes its types towards "benign", so removing it restores detection; removing
one honest client of ten changes a few canary rows. The noise of D_t depends on the type's canary
size (one row of a 21-row type is 0.048), so each type is scaled by its in-control noise

    s_t = max(q99 of honest D_t in the clean pilot runs, 2 canary rows),   z_it = D_it / s_t,
    e_i = max_t (z_it - median_j z_jt)

The median over the round's admitted clients removes common-mode effects: when the round's
aggregate is fragile on a type, removing almost any client restores it, which says nothing about
any one client. With fewer than half of the clients malicious, the median is an honest client's.

and a one-sided, winsorised CUSUM runs on it:  S_i <- max(0, S_i + min(e_i, CLIP) - KAPPA);  revoke i
when S_i >= H, from
round START on, at most MAX_REVOKED clients (fewer than half of K = 10). It is the same test the
gateway runs on devices (E5), applied to the federation's own participants.

Calibration (src/calibrate_trust.py, seed-42 pilot only, frozen before the evaluation seeds):
s_t per (dataset, aggregator) from the no-attack runs; KAPPA and START from a grid; H = 1.25 x the
highest CUSUM value any client reached in the no-attack runs.

Variant history (all on the seed-42 pilot, before any evaluation run; kept in the log):
- v1: unscaled max_t D_t. H had to sit above honest small-type noise (Forge / WUSTL), so 11% of
  attackers were caught within 10 rounds.
- v2: scaled, no median. 37% caught, but 117 honest clients in attack runs falsely alarmed:
  common-mode (e.g. Forge Multi-Krum mitm_ndp, where removing any of 5 honest clients restores it).
- v3: scaled, minus the round median. 38% caught, 144 false alarms: the false alarms are
  sporadic spikes (one round, one type, often shared by an honest and a malicious client; Forge
  mitm_arp / mitm_ndp, Multi-Krum's selection flipping when one client is left out), not
  common-mode. Attackers' evidence is moderate but persistent.
- v4 (this): v3 + winsorised increments (min(e, CLIP)), so one spike cannot revoke.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

CAL = Path(__file__).resolve().parents[1] / "results" / "e9" / "trust_calibration.json"
MAX_REVOKED = 4


def changes(full: dict[str, float], loo: dict[str, float]) -> dict[str, float]:
    d = {t: loo[t] - full[t] for t in full if t != "benign"}
    d["benign"] = full["benign"] - loo["benign"]
    return d


def harms(full: dict[str, float], loo: dict[int, dict[str, float]], scale: dict[str, float]) -> dict[int, float]:
    z = {i: {t: v / scale[t] for t, v in changes(full, l).items()} for i, l in loo.items()}
    med = {t: float(np.median([zi[t] for zi in z.values()])) for t in scale}
    return {i: max(zi[t] - med[t] for t in zi) for i, zi in z.items()}


class ClientTrust:
    def __init__(self, dataset: str, aggregator: str, cal: dict | None = None):
        cal = cal or json.loads(CAL.read_text())
        self.kappa, self.h, self.start, self.clip = cal["kappa"], cal["h"], cal["start"], cal["clip"]
        self.scale = cal["scale"][f"{dataset}/{aggregator}"]
        self.stat: dict[int, float] = {}
        self.revoked: list[int] = []
        self.log: list[dict] = []

    def update(self, rnd: int, full: dict[str, float], loo: dict[int, dict[str, float]]) -> list[int]:
        e = harms(full, loo, self.scale)
        if rnd >= self.start:
            for i, x in e.items():
                self.stat[i] = max(0.0, self.stat.get(i, 0.0) + min(x, self.clip) - self.kappa)
        cand = sorted((i for i in loo if self.stat.get(i, 0.0) >= self.h), key=lambda i: -self.stat[i])
        newly = cand[:max(0, MAX_REVOKED - len(self.revoked))]
        self.revoked += newly
        self.log.append({"round": rnd, "e": e, "S": dict(self.stat), "revoked": newly})
        return newly

    def report(self) -> dict:
        return {"kappa": self.kappa, "h": self.h, "start": self.start, "clip": self.clip, "max_revoked": MAX_REVOKED,
                "scale": self.scale, "revoked": self.revoked, "log": self.log}


R_IMPL = 2
START = 6                                          # first round after the canary warm-up


class CounterfactualTrust:
    """E9 v6 (the evaluated rule) -- attribution only when the canary rejects a round, by counterfactual.

    The CUSUM variants above (v1-v5) put a threshold on per-round LOO noise. Under non-IID data that
    noise differs between honest clients, and it grows during an attack. No threshold set on clean
    data then separated attackers without revoking many honest clients (EXPERIMENTS.md E9).

    Here a client is implicated only when the deployed gate (StatGate) rejects the round's aggregate
    and excluding that client is part of the smallest exclusion set the server finds that makes the
    aggregate pass the same check:
    - greedy: exclude the client whose exclusion leaves the smallest deficit (canary rows short of the
      thresholds, plus benign rows over), re-evaluate without it, and repeat, up to the revocation
      budget;
    - if no set within the budget passes, nobody is implicated.
    A client implicated in R_IMPL rejected rounds is revoked (ledger, rollback; train_fed). The proof
    on the ledger is counterfactual: "round r failed; without these clients it passes". Honest churn
    rarely fails a statistical gate, so honest clients are rarely examined at all.
    Pre-registered on the seed-42 pilot (single-exclusion replay) before the evaluation seeds:
    R_IMPL 2, START 6, MAX_REVOKED 4."""

    def __init__(self, gate, r_impl: int = R_IMPL, start: int = START, max_revoked: int = MAX_REVOKED):
        self.gate, self.r_impl, self.start, self.max_revoked = gate, r_impl, start, max_revoked
        self.stat: dict[int, int] = {}              # implications per client
        self.revoked: list[int] = []
        self.log: list[dict] = []

    def deficit(self, prof: dict[str, float], th) -> float:
        g = self.gate
        return (sum(max(0.0, th[0][t] - prof[t]) * g.n[t] for t in g.types)
                + max(0.0, prof["benign"] - th[1]) * g.n_b)

    def update(self, rnd: int, full: dict[str, float], loo: dict[int, dict[str, float]], evaluate) -> list[int]:
        th = self.gate.thresholds()
        rec = {"round": rnd, "implicated": [], "revoked": []}
        if rnd < self.start or th is None or self.deficit(full, th) < 0.5:
            self.log.append(rec)
            return []
        budget = self.max_revoked - len(self.revoked)
        excl, options, d = [], loo, self.deficit(full, th)
        rec["deficit"] = [d]
        while len(excl) < budget:
            best = min(options, key=lambda i: (self.deficit(options[i], th), i))
            excl.append(best)
            d = self.deficit(options[best], th)
            rec["deficit"].append(d)
            if d < 0.5:
                break
            options = {i: evaluate(excl + [i]) for i in loo if i not in excl}
        implicated = excl if d < 0.5 else []
        for i in implicated:
            self.stat[i] = self.stat.get(i, 0) + 1
        newly = [i for i in implicated if self.stat[i] >= self.r_impl][:budget]
        self.revoked += newly
        rec |= {"implicated": implicated, "tried": excl, "revoked": newly}
        self.log.append(rec)
        return newly

    def report(self) -> dict:
        return {"rule": "counterfactual", "r_impl": self.r_impl, "start": self.start, "max_revoked": self.max_revoked,
                "implications": self.stat, "revoked": self.revoked, "log": self.log}
