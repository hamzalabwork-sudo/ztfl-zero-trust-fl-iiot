"""Per-operation cost of the Provenance contract on a fresh anvil node (2 s blocks), for the ledger
cost table: deployment, round commit vs. number of client hashes, decision batch, revocation, the
isTrusted check before and after revocation, and the three guards that must revert (out-of-order
round, decision citing an unregistered model, decision from a non-gateway account).

  docker run -d --rm --name ztfl-chainprobe -p 127.0.0.1:18555:18555 --entrypoint anvil \\
      ghcr.io/foundry-rs/foundry:v1.8.4 --host 0.0.0.0 --port 18555 --block-time 2 --silent
  python chain_probe.py            # -> results/chain_probe.json
  docker stop ztfl-chainprobe
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from web3 import Web3

HERE = Path(__file__).resolve().parent
ART = HERE.parent / "contracts" / "out" / "Provenance.sol" / "Provenance.json"
GAS = 3_000_000


def h(s: str) -> bytes:
    return hashlib.sha256(s.encode()).digest()


def main() -> None:
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:18555"))
    coord, gw = w3.eth.accounts[:2]
    art = json.loads(ART.read_text())

    def send(fn, sender):
        t0 = time.perf_counter()
        r = w3.eth.wait_for_transaction_receipt(fn.transact({"from": sender, "gas": GAS}), poll_latency=0.05)
        return {"gas": r.gasUsed, "ok": r.status == 1, "latency_s": time.perf_counter() - t0}

    t0 = time.perf_counter()
    r = w3.eth.wait_for_transaction_receipt(
        w3.eth.contract(abi=art["abi"], bytecode=art["bytecode"]["object"]).constructor().transact({"from": coord}))
    out = {"deploy": {"gas": r.gasUsed, "latency_s": time.perf_counter() - t0}}
    c = w3.eth.contract(address=r.contractAddress, abi=art["abi"])
    send(c.functions.setGateway(gw, True), coord)

    rounds = []
    for rnd, k in enumerate([0, 1, 5, 10, 20, 50], start=1):    # client hashes per round
        res = send(c.functions.commitRound(rnd, h(f"m{rnd}"), [h(f"u{rnd}.{i}") for i in range(k)],
                                           [1000] * k, 990000), coord)
        rounds.append({"round": rnd, "clients": k} | res)
    out["round_commit"] = rounds
    out["decision_batch"] = [send(c.functions.commitDecisions(h("m4"), 0, 100, 100, h(f"d{i}")), gw)
                             for i in range(5)]
    out["trusted_before"] = c.functions.isTrusted(h("m4")).call()
    out["revoke"] = send(c.functions.revokeRound(4, "canary verdict failed; client 7 revoked"), coord)
    out["trusted_after"] = c.functions.isTrusted(h("m4")).call()
    out["trusted_other_round"] = c.functions.isTrusted(h("m3")).call()
    out["guard_round_order"] = send(c.functions.commitRound(99, h("x"), [], [], 0), coord)
    out["guard_unknown_model"] = send(c.functions.commitDecisions(h("never-committed"), 0, 100, 100, h("d")), gw)
    out["guard_not_gateway"] = send(c.functions.commitDecisions(h("m3"), 0, 100, 100, h("d")), coord)
    out["block_gas_limit"] = w3.eth.get_block("latest")["gasLimit"]
    (HERE / "results" / "chain_probe.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
