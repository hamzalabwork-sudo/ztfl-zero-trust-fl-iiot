"""Stage 4 (E10) shared code: the LLR table and the per-device continuous-authorisation state
machine. Both are the simulator's logic (closed_loop.Evidence.__call__ and the cusum_sprt_mix
branch of closed_loop.gate) rewritten for one device receiving events one at a time, instead of a
vectorised (n_dev, t) sweep. All constants come from calib.json, which export_testbed.py copied
verbatim from closed_loop.py, so a device's decisions are identical to the paired simulation run.

Kept dependency-free (numpy only) so the device image stays small and the gateway needs no sklearn.
"""
from __future__ import annotations

import numpy as np


def logit(p):
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-7, 1 - 1e-7)
    return np.log(p) - np.log1p(-p)


class Evidence:
    """closed_loop.Evidence.__call__ via the exported table (no sklearn): score -> per-event LLR."""

    def __init__(self, calib: dict):
        self.table = np.asarray(calib["llr_table"], dtype=np.float64)
        self.bins = np.asarray(calib["bins"], dtype=np.float64)

    def __call__(self, s) -> np.ndarray:
        idx = np.clip(np.digitize(logit(s), self.bins) - 1, 0, len(self.table) - 1)
        return self.table[idx]


# device authorisation states
ADMITTED, QUARANTINE, BLOCKED = 0, 1, 2


class DeviceAuthorizer:
    """Streaming cusum_sprt_mix for one device. One call to `step` per event mirrors one column of
    closed_loop.gate: record admit/grant at the event's start, run the quarantine SPRT, then the
    CUSUM alarm on devices that were admitted at the start of the event."""

    def __init__(self, calib: dict):
        self.h = float(calib["cusum_h"])
        self.rho_min = float(calib["rho_min"])
        self.sprt_a = float(calib["sprt_a"])          # log((1-beta)/alpha) > 0  -> accept "attack"
        self.sprt_b = float(calib["sprt_b"])          # log(beta/(1-alpha)) < 0  -> accept "benign"
        self.q_max = int(calib["q_max"])
        self.per_event = float(calib["per_event_threshold"])
        self.state = ADMITTED
        self.cusum = 0.0
        self.lam = 0.0
        self.qlen = 0
        self.events = 0

    def step(self, s: float, llr: float) -> dict:
        """s = detector P(attack), llr = Evidence(s). Returns the decision for this event."""
        self.events += 1
        act = self.state == ADMITTED
        admitted = act
        granted = act and (s < self.per_event)
        readmit = blocked_now = quarantined_now = False

        if self.state == QUARANTINE:                  # one SPRT step against the low-rate attacker
            lq = float(np.log(self.rho_min * np.exp(llr) + 1 - self.rho_min))
            self.lam += lq
            self.qlen += 1
            if self.lam <= self.sprt_b:               # accept "benign" -> re-admit
                self.state, self.cusum, readmit = ADMITTED, 0.0, True
            elif self.lam >= self.sprt_a or self.qlen >= self.q_max:  # accept "attack" / timeout
                self.state, blocked_now = BLOCKED, True

        if act:                                       # CUSUM only on devices admitted at event start
            self.cusum = max(0.0, self.cusum + llr)
            if self.cusum > self.h:
                self.state, self.lam, self.qlen, quarantined_now = QUARANTINE, 0.0, 0, True

        return {"event": self.events, "score": float(s), "llr": float(llr),
                "admitted": bool(admitted), "granted": bool(granted), "deny": bool(not granted),
                "state": int(self.state), "readmit": readmit,
                "blocked_now": blocked_now, "quarantined_now": quarantined_now}
