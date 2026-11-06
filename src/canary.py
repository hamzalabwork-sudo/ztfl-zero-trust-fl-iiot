"""E8 -- the proposed defence ("ours"): a per-attack-type canary check before a model is deployed.

The server holds a labelled canary set; here it is the validation split, the same data the
best-val baseline already uses, so both rules see the same information. After every round the
candidate global model is scored on the canary set and promoted to the gateway only if
- for every attack type with >= N_MIN canary rows: detection >= ref_t - delta, where ref_t is the
  highest detection any promoted version reached on that type (a ratchet, so a slow attacker
  cannot walk the reference down by delta per round);
- benign flag rate <= ref_b + delta_benign, ref_b the lowest benign flag of any promoted version.
Otherwise the round is rejected and the gateway keeps the last promoted version. Training goes on
with the server's global model; only deployment is gated.

The first WARMUP rounds skip the per-type check (an untrained model has no meaningful per-type
profile) and the references start at the end of the warm-up. In every round after the first, a
version with canary macro-F1 < F1_FLOOR (worse than a trivial model, e.g. inverted by label
flipping) is never promoted. A version is registered on the provenance ledger only when promoted;
the gateway runs the registry head, so "rollback" = the head stays at the last version that passed.

Pre-registered: delta 0.05 (primary; 0.02, 0.10, 0.25 reported), delta_benign 0.01, N_MIN 20,
WARMUP 5. F1_FLOOR 0.5 was added after the seed-42 smoke run, before the full run: an inverted
model (F1 0.01) had been promoted during the warm-up.
"""
from __future__ import annotations

import functools

import numpy as np
from scipy.stats import beta, fisher_exact

DELTAS = (0.02, 0.05, 0.10, 0.25)
DELTA_PRIMARY = 0.05
DELTA_BENIGN = 0.01
N_MIN = 20
WARMUP = 5
F1_FLOOR = 0.5


def checked_types(type_val: np.ndarray, y_val: np.ndarray, n_min: int = N_MIN) -> list[str]:
    t, n = np.unique(type_val[y_val == 1], return_counts=True)
    return [str(a) for a, c in zip(t, n) if c >= n_min]


class Gate:
    def __init__(self, types: list[str], delta: float, delta_benign: float = DELTA_BENIGN, warmup: int = WARMUP):
        self.types, self.delta, self.delta_benign, self.warmup = types, delta, delta_benign, warmup
        self.ref_t: dict[str, float] | None = None
        self.ref_b: float | None = None
        self.promoted: list[int] = []
        self.log: list[dict] = []

    def thresholds(self) -> tuple[dict[str, float], float] | None:
        """What a candidate must reach (None during the warm-up)."""
        if self.ref_t is None:
            return None
        return {t: r - self.delta for t, r in self.ref_t.items()}, self.ref_b + self.delta_benign

    def check(self, rnd: int, det: dict[str, float], benign_flag: float, f1_macro: float) -> bool:
        th = self.thresholds()
        failed = ["f1_floor"] if self.promoted and f1_macro < F1_FLOOR else []
        if th is not None:
            failed += [t for t in self.types if det[t] < th[0][t]] + (["benign"] if benign_flag > th[1] else [])
        ok = not failed
        if ok:
            self.promoted.append(rnd)
            if rnd >= self.warmup:
                cur = {t: det[t] for t in self.types}
                self.ref_t = cur if self.ref_t is None else {t: max(self.ref_t[t], cur[t]) for t in self.types}
                self.ref_b = benign_flag if self.ref_b is None else min(self.ref_b, benign_flag)
        self.log.append({"round": rnd, "promoted": ok, "failed": failed})
        return ok

    def allowance(self) -> tuple[dict[str, float], float]:
        """How far below / above the references a candidate may land (used by the adaptive attacker)."""
        return {t: self.delta for t in self.types}, self.delta_benign

    @property
    def head(self) -> int:
        return self.promoted[-1]


class StatGate(Gate):
    """E8b -- the canary check with a statistical tolerance and an optional per-type floor (SLO).

    E8 showed that a fixed delta falsely rejects honest rounds on types with 20-60 canary rows,
    where one or two rows move detection by more than delta. Here a drop on type t (or a rise in the
    benign flag) fails the check only if it is both
    - material: at least delta (delta_benign) of the canary rows of that type, as in E8, and
    - significant: one-sided Fisher exact test of the candidate's counts against the reference's,
      p < alpha / (T + 1) (Bonferroni over the T checked types and benign).
    Large types are then held to delta as before; small types get a tolerance sized to their noise.
    The test needs only counts, so anyone can re-check a verdict from the ledger.

    slo: every checked type must reach detection >= slo, judged by the one-sided Clopper-Pearson
    upper bound at the same alpha / (T + 1), in EVERY round including the warm-up. It is the
    operator's security policy ("each known attack type is detected at least half the time") and the
    one reference that a federation poisoned from round 1 cannot move. Until a version passes, the
    gateway has no model (fail-closed).

    Pre-registered before any E8b result was looked at: delta 0.05, delta_benign 0.01, alpha 0.05,
    slo 0.5, references as in E8 (ratchet over promoted versions after the warm-up)."""

    def __init__(self, types: list[str], n: dict[str, int], n_benign: int, delta: float = DELTA_PRIMARY,
                 alpha: float = 0.05, slo: float | None = None, delta_benign: float = DELTA_BENIGN, warmup: int = WARMUP):
        super().__init__(types, delta, delta_benign, warmup)
        self.n, self.n_b, self.alpha, self.slo = n, n_benign, alpha, slo
        self.a = alpha / (len(types) + 1)
        self.k_slo = {t: self._k_slo(n[t]) for t in types} if slo is not None else {t: 0 for t in types}

    def _k_slo(self, n: int) -> int:
        """Smallest count whose one-sided upper confidence bound on detection reaches the SLO."""
        return next(k for k in range(n + 1) if k == n or beta.ppf(1 - self.a, k + 1, n - k) >= self.slo)

    @functools.lru_cache(maxsize=None)
    def _k_rel(self, k_ref: int, n: int) -> int:
        """Smallest candidate count that is not a material and significant drop from k_ref."""
        def rejected(k: int) -> bool:
            return (k_ref - k) >= self.delta * n - 1e-9 and fisher_exact(
                [[k_ref, n - k_ref], [k, n - k]], alternative="greater")[1] < self.a
        lo, hi = 0, k_ref                          # rejected() is monotone in k: binary search
        if not rejected(lo):
            return 0
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if rejected(mid) else (lo, mid)
        return hi

    @functools.lru_cache(maxsize=None)
    def _f_rel(self, f_ref: int) -> int:
        """Largest benign-flag count that is not a material and significant rise from f_ref."""
        n = self.n_b

        def rejected(f: int) -> bool:
            return (f - f_ref) >= self.delta_benign * n - 1e-9 and fisher_exact(
                [[f, n - f], [f_ref, n - f_ref]], alternative="greater")[1] < self.a
        lo, hi = f_ref, n
        if not rejected(hi):
            return n
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (lo, mid) if rejected(mid) else (mid, hi)
        return lo

    def _counts(self, det: dict[str, float]) -> dict[str, int]:
        return {t: int(round(det[t] * self.n[t])) for t in self.types}

    def thresholds(self) -> tuple[dict[str, float], float] | None:
        if self.ref_t is None and self.slo is None:
            return None
        k_ref = self._counts(self.ref_t) if self.ref_t is not None else None
        th = {t: max(self.k_slo[t], self._k_rel(k_ref[t], self.n[t]) if k_ref else 0) / self.n[t] for t in self.types}
        fb = self._f_rel(int(round(self.ref_b * self.n_b))) / self.n_b if self.ref_b is not None else 1.0
        return th, fb

    def allowance(self) -> tuple[dict[str, float], float]:
        th = self.thresholds()
        return {t: self.ref_t[t] - th[0][t] for t in self.types}, th[1] - self.ref_b

    def check(self, rnd: int, det: dict[str, float], benign_flag: float, f1_macro: float) -> bool:
        th = self.thresholds()
        failed = ["f1_floor"] if self.promoted and f1_macro < F1_FLOOR else []
        if th is not None:
            k = self._counts(det)
            failed += [t for t in self.types if k[t] < round(th[0][t] * self.n[t])]
            failed += ["benign"] if int(round(benign_flag * self.n_b)) > round(th[1] * self.n_b) else []
        ok = not failed
        if ok:
            self.promoted.append(rnd)
            if rnd >= self.warmup:
                cur = {t: det[t] for t in self.types}
                self.ref_t = cur if self.ref_t is None else {t: max(self.ref_t[t], cur[t]) for t in self.types}
                self.ref_b = benign_flag if self.ref_b is None else min(self.ref_b, benign_flag)
        self.log.append({"round": rnd, "promoted": ok, "failed": failed})
        return ok

    @property
    def head(self) -> int:
        return self.promoted[-1] if self.promoted else 0   # 0 = nothing passed yet: no model (fail-closed)
