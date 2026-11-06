"""Blockchain ablation: what the EVM ledger adds over the local hash chain alone.

A gateway records one deployed-model round and 20 decision batches on both ledgers (EvmLedger keeps
the local hash chain and writes the same records to the Provenance contract). An insider with write
access to the gateway's log then tampers with it in four ways. For each, we ask whether the local
hash chain (MemoryLedger.verify) and the on-chain audit (EvmLedger.audit) detect it:

  1. edit a decision digest in place (no re-hashing);
  2. edit a decision digest and recompute the whole local hash chain from that block on;
  3. delete a decision batch and recompute the local hash chain;
  4. swap the deployed model hash on a decision batch (claim another model made it) and re-hash.

  docker run -d --rm --name ztfl-chainprobe -p 127.0.0.1:18555:18555 --entrypoint anvil \\
      ghcr.io/foundry-rs/foundry:v1.8.4 --host 0.0.0.0 --port 18555 --block-time 2 --silent
  python tamper_probe.py           # -> results/tamper_probe.json
  docker stop ztfl-chainprobe

Live PureChain: python tamper_probe.py --rpc https://purechainnode.com --keys ~/.ztfl/purechain_keys.json --tag purechain
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from ledger import EvmLedger  # noqa: E402
from chain_probe import load_keys  # noqa: E402

ART = HERE.parent / "contracts" / "out" / "Provenance.sol" / "Provenance.json"
N_BATCH = 20


def rehash(blocks: list[dict]) -> tuple[list[dict], str]:
    """What an insider does to hide an edit: rebuild every block hash so the local chain verifies."""
    prev, out = "0" * 64, []
    for i, b in enumerate(blocks):
        body = {k: v for k, v in b.items() if k != "hash"} | {"height": i, "prev": prev}
        h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        out.append(body | {"hash": h})
        prev = h
    return out, prev


def check(led: EvmLedger, blocks: list[dict], head: str) -> dict:
    led.blocks, led.head = blocks, head
    a = led.audit()
    return {"local_hash_chain_verifies": led.verify(),
            "onchain_audit_matches": a["rounds_match"] and a["decisions_match"],
            "local_decisions": sum(b["kind"] == "decisions" for b in blocks),
            "onchain_decisions": a["onchain_decisions"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="http://127.0.0.1:18555")
    ap.add_argument("--keys", default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    led = EvmLedger(args.rpc, str(ART), keys=load_keys(args.keys))
    model = hashlib.sha256(b"deployed-model").hexdigest()
    other = hashlib.sha256(b"some-other-model").hexdigest()
    led.record_round(1, model, [], [], 0.998)
    for i in range(N_BATCH):
        led.record_decisions(model, "cusum_sprt_mix", 0, 100, 100, hashlib.sha256(f"batch{i}".encode()).hexdigest())
    chain = led.flush()
    honest, head = copy.deepcopy(led.blocks), led.head
    k = 1 + N_BATCH // 2                                      # the decision batch the insider targets
    forged = hashlib.sha256(b"forged-decisions").hexdigest()

    out = {"onchain_failed": chain["failed"], "untouched": check(led, copy.deepcopy(honest), head)}
    b = copy.deepcopy(honest); b[k]["digest"] = forged
    out["edit_in_place"] = check(led, b, head)
    b = copy.deepcopy(honest); b[k]["digest"] = forged
    out["edit_and_rehash"] = check(led, *rehash(b))
    b = copy.deepcopy(honest); del b[k]
    out["delete_and_rehash"] = check(led, *rehash(b))
    b = copy.deepcopy(honest); b[k]["model"] = other
    out["swap_model_and_rehash"] = check(led, *rehash(b))
    out["rpc"], out["contract"] = args.rpc, led.contract.address
    name = f"tamper_probe{'_' + args.tag if args.tag else ''}.json"
    (HERE / "results" / name).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
