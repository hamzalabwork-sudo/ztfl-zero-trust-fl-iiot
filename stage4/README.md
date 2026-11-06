# Stage 4 (E10) -- emulated device testbed

The simulation (E5/E9) draws device streams i.i.d. from the public test split, so device identity
and timing are synthetic and enforcement is abstract. Stage 4 keeps the **exact validated detector
and decision rule** and makes those three things real: each device is its own container with its own
network identity, events arrive over a real MQTT session with real timing, and the gateway is a
policy enforcement point that grants or denies each event and isolates compromised devices.

Nothing in the detector or the policy is re-tuned. `export_testbed.py` copies the CUSUM/SPRT
constants and the monotone_balanced LLR table verbatim from `closed_loop.py`, and the per-device
authoriser in `common.py` is a streaming rewrite of `closed_loop.gate`'s `cusum_sprt_mix` branch,
verified bit-identical to it. So E10 measures the same system E7-E9 validated, now end to end.

## Components (laptop, Docker Desktop)

| service | image | role |
|---|---|---|
| broker | eclipse-mosquitto:2 | real MQTT transport |
| device-i | ztfl-stage4 | one IIoT device: emits held-out feature vectors; the last m are compromised at an onset tau with the backdoor target type (C1) |
| gateway | ztfl-stage4 | PEP: scores each event with the deployed stat_slo registry-head detector, runs per-device cusum_sprt_mix (C2), grants/denies/isolates, records decisions to the ledger tagged with the model version (C3) |
| anvil | foundry | local EVM for the provenance ledger (`--ledger evm`) |

The deployed detector is the **stat_slo canary registry head** of a clean federated run -- the final
system of E9. Devices carry the ground-truth label only so the gateway can score access-control
metrics; the detector never sees it.

## Run

```
# 1. export the bundle (server or laptop; edge cache ships with the laptop)
PYTHONPATH=src python stage4/export_testbed.py --dataset edgeiiot --seed 42

# 2. build the image
docker build -t ztfl-stage4:1.0 stage4

# 3. a live session: 10 devices, 2 compromised from a mid-session onset, attack rate rho
py -3.13 stage4/run_e10.py --dataset edgeiiot --n-dev 10 --m 2 --rho 1.0 --run e10_edge_m2_rho1
#   --ledger evm   to write the provenance chain to a real local EVM node and measure write latency;
#                  the result's chain.failed must be 0 and chain.audit must match (records rebuilt from the chain)

# 3b. all nine attacked sessions on the EVM ledger, then the ledger summary (E10-chain)
sh stage4/evm_sweep.sh            # run from stage4/
python stage4/summarize_chain.py  # -> stage4/results/chain_summary.json

# 3c. live PureChain (E12): the same nine sessions on the public free-gas network
#     (chain ID 900520900520). Put two private keys of your own in ~/.ztfl/purechain_keys.json as
#     {"coordinator": "0x...", "gateway": "0x..."}; no funds are needed (zero gas price). The keys reach the
#     gateway container only through the LEDGER_KEYS environment variable, never the compose file.
sh stage4/purechain_sweep.sh                 # run from stage4/; skips sessions already stored
python stage4/summarize_chain.py purechain   # -> stage4/results/chain_summary_purechain.json
#     behind an HTTPS-inspecting proxy, point REQUESTS_CA_BUNDLE at a bundle that includes its root

# 4. summarise
python src/summarize_e10.py        # -> stage4/results/summary.md
```

`run_e10.py` generates `docker-compose.gen.yml`, brings the stack up, waits for the gateway to
finish, and tears it down. Results: `stage4/results/<run>.json` (metrics, ledger, latency) and
`<run>_sessions.json` (every device's per-event decisions).

## What is real vs still modelled

- **Real:** device network identity, MQTT protocol and serialisation, per-event timing and jitter,
  concurrent devices, the gateway scoring/deciding online, the provenance ledger (hash-chain or a
  real EVM node) and its measured write latency, detector CPU latency per event.
- **Still modelled:** the *content* of each event is a held-out dataset feature vector, not traffic
  parsed live off the wire (the public datasets' tshark feature space cannot be reconstructed from
  raw MQTT/Modbus packets). Enforcement is at the policy layer (grant/deny/isolate), the faithful
  Zero-Trust PEP semantics; a packet-level firewall drop (routing device traffic through the
  gateway) is a possible Stage 4b extension.
