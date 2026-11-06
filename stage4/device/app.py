"""Stage 4 (E10) device emulator. One container = one IIoT device with its own network identity
and MQTT client id. It emits T_EV events over a real session: each event is a held-out feature
vector published to the gateway. A benign device only ever emits benign vectors; a compromised
device is clean until an unknown time tau, after which a share rho of its events carry its backdoor
attack type (C1: the device is compromised mid-session). The RNG is seeded per device so a run is
reproducible and pairs with the simulation's stream construction.

Env: DEVICE_ID, N_DEV, SEED, ROLE(benign|compromised), TAU, RHO, ATTACK_TYPE, T_EV, TICK, BROKER.
The vectors are drawn from /export/pool.npz (mounted read-only); numpy only, no torch.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
import paho.mqtt.client as mqtt

DEV = int(os.environ["DEVICE_ID"])
N_DEV = int(os.environ["N_DEV"])
SEED = int(os.environ.get("SEED", "42"))
ROLE = os.environ.get("ROLE", "benign")
TAU = int(os.environ.get("TAU", "200"))
RHO = float(os.environ.get("RHO", "1.0"))
ATTACK_TYPE = os.environ.get("ATTACK_TYPE", "")
T_EV = int(os.environ.get("T_EV", "500"))
TICK = float(os.environ.get("TICK", "0.05"))
BROKER = os.environ.get("BROKER", "broker")
REQ, CTL, START = "ztfl/req", "ztfl/ctl", "ztfl/start"


def main() -> None:
    z = np.load("/export/pool.npz", allow_pickle=False)
    X, y, typ = z["X"], z["y"], z["type"]
    benign = np.flatnonzero(y == 0)
    attack = np.flatnonzero((y == 1) & (typ == ATTACK_TYPE)) if ROLE == "compromised" else np.array([], int)
    if ROLE == "compromised" and len(attack) == 0:
        raise SystemExit(f"device {DEV}: no rows of attack type {ATTACK_TYPE!r} in the pool")

    rng = np.random.default_rng([SEED, DEV])
    started = {"go": False}
    cli = mqtt.Client(client_id=f"device-{DEV}", protocol=mqtt.MQTTv311)
    cli.on_message = lambda c, u, m: started.__setitem__("go", bool(m.payload))
    for _ in range(60):
        try:
            cli.connect(BROKER, 1883, 60)
            break
        except OSError:
            time.sleep(1.0)
    else:
        raise SystemExit(f"device {DEV}: broker {BROKER} unreachable")
    cli.subscribe(START, 1)                             # retained flag the gateway sets when ready
    cli.loop_start()
    for _ in range(600):                                # wait for the gateway to be subscribed
        if started["go"]:
            break
        time.sleep(0.1)
    else:
        raise SystemExit(f"device {DEV}: gateway start signal not received")

    n_attack = 0
    for e in range(T_EV):
        is_attack = ROLE == "compromised" and e >= TAU and rng.random() < RHO
        pool = attack if is_attack else benign
        row = int(rng.choice(pool))
        target = int((DEV + rng.integers(1, N_DEV)) % N_DEV)        # some other device
        msg = {"device": DEV, "event": e, "target": target, "truth_attack": bool(is_attack),
               "truth_type": (ATTACK_TYPE if is_attack else "benign"), "tau": TAU if ROLE == "compromised" else -1,
               "vec": X[row].astype(float).tolist()}
        cli.publish(REQ, json.dumps(msg), qos=1)
        n_attack += is_attack
        time.sleep(TICK * (0.5 + rng.random()))                    # jittered inter-event time
    cli.publish(CTL, json.dumps({"device": DEV, "done": True, "emitted": T_EV, "attacks": n_attack}), qos=1)
    time.sleep(2.0)
    cli.loop_stop()
    cli.disconnect()
    print(f"device {DEV} ({ROLE}) done: {T_EV} events, {n_attack} attack", flush=True)


if __name__ == "__main__":
    main()
