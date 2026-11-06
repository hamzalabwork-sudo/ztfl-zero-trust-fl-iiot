"""Per-operation cost of the Provenance contract, for the ledger cost table: deployment, round commit
vs. number of client hashes, decision batch, revocation, the isTrusted check before and after
revocation, and the three guards that must revert (out-of-order round, decision citing an
unregistered model, decision from a non-gateway account).

Local EVM node (anvil, 2 s blocks; unlocked accounts):
  docker run -d --rm --name ztfl-chainprobe -p 127.0.0.1:18555:18555 --entrypoint anvil \\
      ghcr.io/foundry-rs/foundry:v1.8.4 --host 0.0.0.0 --port 18555 --block-time 2 --silent
  python chain_probe.py                         # -> results/chain_probe.json
  docker stop ztfl-chainprobe

Live PureChain (free gas; locally signed with two throwaway keys, see ledger.EvmLedger):
  python chain_probe.py --rpc https://purechainnode.com --keys ~/.ztfl/purechain_keys.json --tag purechain
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from ledger import EvmLedger  # noqa: E402

ART = HERE.parent / "contracts" / "out" / "Provenance.sol" / "Provenance.json"


def h(s: str) -> bytes:
    return hashlib.sha256(s.encode()).digest()


def load_keys(path: str | None) -> tuple[str, str] | None:
    if not path:
        return None
    d = json.loads(Path(path).expanduser().read_text())
    return d["coordinator"], d["gateway"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="http://127.0.0.1:18555")
    ap.add_argument("--keys", default=None, help="JSON with coordinator/gateway private keys (public networks)")
    ap.add_argument("--tag", default="", help="suffix of the output file, e.g. purechain")
    ap.add_argument("--batches", type=int, default=5, help="decision batches to time")
    args = ap.parse_args()

    t0 = time.perf_counter()
    led = EvmLedger(args.rpc, str(ART), keys=load_keys(args.keys))
    setup_s = time.perf_counter() - t0
    w3, c, coord, gw = led.w3, led.contract, led.coordinator, led.gateway

    def send(fn, sender):
        t0 = time.perf_counter()
        r = w3.eth.wait_for_transaction_receipt(led._send(fn, sender), timeout=600, poll_latency=0.05)
        return {"gas": r.gasUsed, "ok": r.status == 1, "latency_s": time.perf_counter() - t0, "block": r.blockNumber}

    out = {"rpc": args.rpc, "chain_id": w3.eth.chain_id, "client": w3.client_version, "contract": c.address,
           "deploy": {"gas": led.deploy_gas, "deploy_plus_setgateway_s": setup_s, "block": led.deploy_block}}
    rounds = []
    for rnd, k in enumerate([0, 1, 5, 10, 20, 50], start=1):    # client hashes per round
        res = send(c.functions.commitRound(rnd, h(f"m{rnd}"), [h(f"u{rnd}.{i}") for i in range(k)],
                                           [1000] * k, 990000), coord)
        rounds.append({"round": rnd, "clients": k} | res)
    out["round_commit"] = rounds
    out["decision_batch"] = [send(c.functions.commitDecisions(h("m4"), 0, 100, 100, h(f"d{i}")), gw)
                             for i in range(args.batches)]
    out["trusted_before"] = c.functions.isTrusted(h("m4")).call()
    out["revoke"] = send(c.functions.revokeRound(4, "canary verdict failed; client 7 revoked"), coord)
    out["trusted_after"] = c.functions.isTrusted(h("m4")).call()
    out["trusted_other_round"] = c.functions.isTrusted(h("m3")).call()
    out["guard_round_order"] = send(c.functions.commitRound(99, h("x"), [], [], 0), coord)
    out["guard_unknown_model"] = send(c.functions.commitDecisions(h("never-committed"), 0, 100, 100, h("d")), gw)
    out["guard_not_gateway"] = send(c.functions.commitDecisions(h("m3"), 0, 100, 100, h("d")), coord)
    out["block_gas_limit"] = w3.eth.get_block("latest")["gasLimit"]
    name = f"chain_probe{'_' + args.tag if args.tag else ''}.json"
    (HERE / "results" / name).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
