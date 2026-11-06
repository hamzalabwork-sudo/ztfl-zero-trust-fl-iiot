"""Summarise E5e: evidence-model variants (results/closed_loop/curves_<llr>/) against E5d (curves/),
paired seed by seed. Same detectors and streams; only the score -> LLR table differs.

Reports cusum_sprt_mix at Lorden's h (false isolation, wrongful grants, detection, time-to-isolation),
the equal-false-isolation comparison (oracle, analysis only) and the per-type isolation at Lorden's h.
Writes results/closed_loop/e5e_summary.md.
Usage: python src/summarize_e5e.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from summarize_curves import equal_budget, load, md_table, ROOT

BASE = ROOT / "results" / "closed_loop"
MODES = {"monotone": "curves", "monotone_balanced": "curves_monotone_balanced", "monotone_floor": "curves_monotone_floor"}
PCT = {"false_isolation_rate", "wrongful_grant_rate", "detection_rate", "device_isolated_rate"}


def main() -> None:
    pts, types, eqb = [], [], []
    for mode, sub in MODES.items():
        runs, p, _, t = load(BASE / sub)
        lorden = {(r["dataset"], r["seed"]): r["marks"]["cusum_lorden"] for r in runs}
        p["llr"], t["llr"] = mode, mode
        p["lorden"] = [lorden[k] for k in zip(p.dataset, p.seed)]
        pts.append(p[np.isclose(p.threshold, p.lorden) & (p.policy == "cusum_sprt_mix")])
        types.append(t[t.policy == "cusum_sprt_mix"])
        eqb.append(equal_budget(p).assign(llr=mode).set_index("llr", append=True))
    pts, types = pd.concat(pts), pd.concat(types)
    out = [f"# E5e: evidence-model variants vs E5d (monotone), {len(runs)} runs per mode", ""]
    lo = pts.groupby(["dataset", "rho", "llr"])[["false_isolation_rate", "wrongful_grant_rate", "detection_rate", "tti_median"]]
    out += ["## cusum_sprt_mix at Lorden's h = 10.82 (mean over seeds)", ""] + md_table(lo.mean(), PCT) + [""]
    fmax = pts.groupby(["dataset", "rho", "llr"])[["false_isolation_rate"]].max().rename(columns={"false_isolation_rate": "false_isolation_max"})
    out += ["## Worst seed: false isolation at Lorden's h", ""] + md_table(fmax, {"false_isolation_max"}) + [""]
    eq = pd.concat(eqb)[["false_isolation_rate", "wrongful_grant_rate", "detection_rate", "tti_median"]]
    eq = eq[eq.index.get_level_values("policy") == "cusum_sprt_mix"].droplevel("policy")
    out += ["## Equal realised false isolation <= 1% (oracle threshold, analysis only), cusum_sprt_mix", ""] + md_table(eq.sort_index(), PCT) + [""]
    ty = types[types.rho.isin(["rho1", "rho0.2"])].pivot_table(index=["dataset", "attack_type", "rho"], columns="llr",
                                                               values="device_isolated_rate", aggfunc="mean")[list(MODES)]
    out += ["## Per attack type: share of compromised devices isolated at Lorden's h", ""] + md_table(ty, set(MODES)) + [""]
    tw = types[types.rho.isin(["rho1", "rho0.2"])].pivot_table(index=["dataset", "attack_type", "rho"], columns="llr",
                                                               values="wrongful_grant_rate", aggfunc="mean")[list(MODES)]
    out += ["## Per attack type: attack events granted at Lorden's h", ""] + md_table(tw, set(MODES)) + [""]
    (BASE / "e5e_summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
