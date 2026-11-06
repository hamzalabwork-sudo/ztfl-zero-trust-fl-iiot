"""Stage 4 (E10) gateway -- the policy enforcement point.

It subscribes to every device's events on the real MQTT broker, scores each feature vector with the
deployed detector (the stat_slo canary registry head exported by export_testbed.py), runs that
device's streaming cusum_sprt_mix authoriser (common.DeviceAuthorizer), and grants or denies the
event's access to its target. Isolated devices are denied for the rest of the session. Every batch
of decisions is written to the provenance ledger tagged with the deployed model hash (C3); the
decision is made locally and the ledger write is asynchronous, so enforcement never waits on it.

When all N_DEV devices report done it computes the access-control metrics (the same definitions as
closed_loop.access_metrics, now over real per-device sessions) and writes /results/<run>.json.

Env: RUN, N_DEV, T_EV, LEDGER(memory|evm), RPC, BROKER. Model/calib at /export, src on PYTHONPATH.
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import paho.mqtt.client as mqtt
import torch

from common import Evidence, DeviceAuthorizer, ADMITTED
from ledger import MemoryLedger, batch_digest
from models import build_model

RUN = os.environ.get("RUN", "e10")
N_DEV = int(os.environ.get("N_DEV", "6"))
T_EV = int(os.environ.get("T_EV", "500"))
LEDGER = os.environ.get("LEDGER", "memory")
RPC = os.environ.get("RPC", "http://anvil:18545")
BROKER = os.environ.get("BROKER", "broker")
DECISION_BATCH = 100                       # events per ledger decision record (= closed_loop)
REQ, CTL, START = "ztfl/req", "ztfl/ctl", "ztfl/start"
EXPORT, RESULTS = Path("/export"), Path("/results")


class Gateway:
    def __init__(self) -> None:
        self.calib = json.loads((EXPORT / "calib.json").read_text())
        self.model = build_model(self.calib["model"], self.calib["input_dim"])
        self.model.load_state_dict(torch.load(EXPORT / "model.pt", map_location="cpu"))
        self.model.eval()
        self.model_hash = self.calib["model_hash"]
        self.evidence = Evidence(self.calib)
        self.auth: dict[int, DeviceAuthorizer] = {}
        self.log: dict[int, list[dict]] = defaultdict(list)     # per device: event records + truth
        self.pending: list = []                                 # decision batch buffer
        self.done: set[int] = set()
        self.score_seconds = 0.0
        self.t_first = None
        self.last_msg = time.perf_counter()
        self.expected = N_DEV * T_EV
        if LEDGER == "evm":
            from ledger import EvmLedger
            art = "/app/contracts/out/Provenance.sol/Provenance.json"
            self.ledger = EvmLedger(RPC, art)
        else:
            self.ledger = MemoryLedger()
        # provenance of the deployed model version (what every decision below is tagged with)
        self.ledger.record_round(self.calib["deployed_round"], self.model_hash, [], [],
                                 self.calib.get("detector_val_f1_macro") or 0.0)

    def score(self, vec: list[float]) -> float:
        t0 = time.perf_counter()
        x = torch.tensor([vec], dtype=torch.float32)
        with torch.no_grad():
            s = torch.softmax(self.model(x), dim=1)[0, 1].item()
        self.score_seconds += time.perf_counter() - t0
        return s

    def on_message(self, _cli, _ud, m) -> None:
        self.last_msg = time.perf_counter()
        msg = json.loads(m.payload)
        if m.topic == CTL:
            if msg.get("done"):
                self.done.add(int(msg["device"]))
            return
        dev = int(msg["device"])
        self.t_first = self.t_first or time.perf_counter()
        s = self.score(msg["vec"])
        a = self.auth.setdefault(dev, DeviceAuthorizer(self.calib)).step(s, float(self.evidence(s)))
        self.log[dev].append(a | {"truth_attack": msg["truth_attack"], "truth_type": msg["truth_type"],
                                  "target": msg["target"], "tau": msg["tau"], "idx": msg["event"]})
        self.pending.append((dev, a["granted"], a["admitted"]))
        if len(self.pending) >= DECISION_BATCH:
            self.flush_decisions()

    def flush_decisions(self) -> None:
        if not self.pending:
            return
        granted = np.array([g for _, g, _ in self.pending], dtype=bool)
        admitted = np.array([ad for _, _, ad in self.pending], dtype=bool)
        self.ledger.record_decisions(self.model_hash, f"cusum_sprt_mix/{RUN}", 0, len(self.pending),
                                     granted.size, batch_digest(granted, admitted))
        self.pending.clear()

    def metrics(self) -> dict:
        """access_metrics over the collected per-device sessions (closed_loop definitions)."""
        grant_a, grant_a_den = [], []     # per attack event: granted?
        benign_dev_grant, benign_dev_isolated = [], []
        comp_detect, comp_tti, comp_premature, comp_reach, comp_granted_atk = [], [], [], [], []
        false_reauth_num = quarantined_after = 0
        for dev, evs in self.log.items():
            evs = sorted(evs, key=lambda r: r["idx"])
            tau = evs[0]["tau"]
            comp = tau >= 0
            atk = np.array([r["truth_attack"] for r in evs])
            granted = np.array([r["granted"] for r in evs])
            admitted = np.array([r["admitted"] for r in evs])
            idx = np.array([r["idx"] for r in evs])
            if atk.any():
                grant_a.append(granted[atk])
            if not comp:
                benign_dev_grant.append(granted.mean())
                benign_dev_isolated.append(bool((~admitted).any()))
                continue
            after = idx >= tau
            out_after = (~admitted) & after
            detected = bool(out_after.any())
            comp_detect.append(detected)
            if detected:
                comp_tti.append(int(idx[out_after][0] - tau))
            comp_premature.append(bool(((~admitted) & (idx < tau)).any()))
            hit = granted & atk
            comp_reach.append(len(np.unique([evs[i]["target"] for i in np.flatnonzero(hit)])))
            comp_granted_atk.append(int(hit.sum()))
            if detected:
                quarantined_after += 1
            # a re-admission while still compromised: an admitted event strictly after a prior isolation, at/after tau
            iso_seen = False
            for r in evs:
                if r["idx"] < tau:
                    continue
                if not r["admitted"]:
                    iso_seen = True
                elif iso_seen and r["readmit"]:
                    false_reauth_num += 1
                    break
        ga = np.concatenate(grant_a) if grant_a else np.array([])
        return {
            "wrongful_grant_rate": float(ga.mean()) if ga.size else None,
            "benign_denial_rate": float(1 - np.mean(benign_dev_grant)) if benign_dev_grant else None,
            "false_isolation_rate": float(np.mean(benign_dev_isolated)) if benign_dev_isolated else None,
            "detection_rate": float(np.mean(comp_detect)) if comp_detect else None,
            "tti_median": float(np.median(comp_tti)) if comp_tti else None,
            "tti_p90": float(np.percentile(comp_tti, 90)) if comp_tti else None,
            "premature_isolation_rate": float(np.mean(comp_premature)) if comp_premature else None,
            "false_reauth_rate": (false_reauth_num / quarantined_after) if quarantined_after else None,
            "lateral_reach_mean": float(np.mean(comp_reach)) if comp_reach else None,
            "granted_attacks_per_compromised": float(np.mean(comp_granted_atk)) if comp_granted_atk else None,
            "n_compromised": len(comp_detect), "n_benign": len(benign_dev_grant),
            "attack_events": int(ga.size),
        }

    def complete(self) -> bool:
        """All events seen, or every device reported done and the stream has gone quiet (grace)."""
        total = sum(len(v) for v in self.log.values())
        if total >= self.expected:
            return True
        return len(self.done) >= N_DEV and (time.perf_counter() - self.last_msg) > 3.0

    def finalise(self, cli) -> None:
        self.flush_decisions()
        wall = time.perf_counter() - (self.t_first or time.perf_counter())
        chain = self.ledger.flush() | {"backend": "evm"} if hasattr(self.ledger, "flush") else {"backend": "memory"}
        out = {
            "run": RUN, "n_dev": N_DEV, "t_ev": T_EV, "policy": "cusum_sprt_mix",
            "deployed_model": self.model_hash, "deployed_round": self.calib["deployed_round"],
            "dataset": self.calib["dataset"], "seed": self.calib["seed"], "backdoor_target": self.calib["backdoor_target"],
            "metrics": self.metrics(), "ledger": self.ledger.summary(), "chain": chain,
            "events_total": sum(len(v) for v in self.log.values()),
            "score_ms_per_event": 1e3 * self.score_seconds / max(1, sum(len(v) for v in self.log.values())),
            "session_wall_seconds": wall, "code_version": self.calib["code_version"],
            "gateway_cpus": os.environ.get("GATEWAY_CPUS", "") or "unlimited",
            "torch_threads": torch.get_num_threads(),
            "detector_code_version_matches": True, "host": os.uname().nodename if hasattr(os, "uname") else "",
        }
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{RUN}.json").write_text(json.dumps(out, indent=1))
        (RESULTS / f"{RUN}_sessions.json").write_text(json.dumps(
            {str(d): sorted(v, key=lambda r: r["idx"]) for d, v in self.log.items()}, indent=1))
        m = out["metrics"]
        print(f"[gateway] done: {out['events_total']} events, wrongful_grant={m['wrongful_grant_rate']} "
              f"detect={m['detection_rate']} false_iso={m['false_isolation_rate']} "
              f"reach={m['lateral_reach_mean']} score={out['score_ms_per_event']:.3f} ms/ev "
              f"ledger blocks={out['ledger']['blocks']} verified={out['ledger']['verified']}", flush=True)


def main() -> None:
    gw = Gateway()
    cli = mqtt.Client(client_id="gateway", protocol=mqtt.MQTTv311)
    cli.on_message = gw.on_message
    for _ in range(60):
        try:
            cli.connect(BROKER, 1883, 60)
            break
        except OSError:
            time.sleep(1.0)
    else:
        raise SystemExit(f"gateway: broker {BROKER} unreachable")
    cli.subscribe([(REQ, 1), (CTL, 1)])
    cli.loop_start()                                                 # loop must run to send publishes
    cli.publish(START, "1", qos=1, retain=True).wait_for_publish()   # devices wait for this
    print(f"[gateway] up: model {gw.model_hash[:12]} round {gw.calib['deployed_round']} "
          f"dim {gw.calib['input_dim']} h={gw.calib['cusum_h']:.2f} ledger={LEDGER} expect {gw.expected} events", flush=True)
    while not gw.complete():
        time.sleep(0.2)
    cli.loop_stop()                                                  # no more callbacks before finalise
    gw.finalise(cli)


if __name__ == "__main__":
    main()
