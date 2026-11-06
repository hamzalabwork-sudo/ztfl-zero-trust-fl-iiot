"""Model-provenance ledger (claim C3).

What is recorded:
- every FL round: global model hash, each client's update hash and size, validation macro-F1;
- every batch of gateway decisions: the model version (hash) that made them, the number of
  decisions, and a digest of the batch.

Any decision can therefore be traced to the exact global model and the client updates behind it.
When a round is later found poisoned, `decisions_under` lists what that model decided, i.e. what
to audit or roll back.

Backends: `MemoryLedger` is a hash-chained append-only log, used in simulation (every block
commits to the previous one, `verify` re-checks the chain). The EVM backend (local anvil, the
PureChain stand-in) exposes the same three methods. Enforcement never waits for the chain: the
gateway decides locally and the decision digests are written asynchronously.
"""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np
import torch


def state_hash(state: dict[str, torch.Tensor]) -> str:
    """sha256 over the parameter names and float32 bytes, in sorted key order."""
    h = hashlib.sha256()
    for k in sorted(state):
        h.update(k.encode())
        h.update(state[k].detach().to("cpu", torch.float32).contiguous().numpy().tobytes())
    return h.hexdigest()


def update_hash(client_state: dict, global_before: dict) -> str:
    """Hash of a client's update (client weights minus the global weights it started from)."""
    return state_hash({k: client_state[k].float() - global_before[k].float() for k in client_state})


def batch_digest(*arrays: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


class MemoryLedger:
    def __init__(self) -> None:
        self.blocks: list[dict] = []
        self.head = "0" * 64
        self.write_seconds = 0.0

    def _append(self, kind: str, payload: dict) -> str:
        t0 = time.perf_counter()
        body = {"height": len(self.blocks), "prev": self.head, "kind": kind, **payload}
        h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        self.blocks.append(body | {"hash": h})
        self.head = h
        self.write_seconds += time.perf_counter() - t0
        return h

    def record_round(self, rnd: int, model_hash: str, client_hashes: list[str], client_sizes: list[int],
                     val_f1_macro: float) -> str:
        return self._append("round", {"round": rnd, "model": model_hash, "clients": client_hashes,
                                      "sizes": [int(s) for s in client_sizes], "val_f1_macro": round(val_f1_macro, 6)})

    def record_decisions(self, model_hash: str, policy: str, t_from: int, t_to: int, n: int, digest: str) -> str:
        return self._append("decisions", {"model": model_hash, "policy": policy, "t": [t_from, t_to],
                                          "n": int(n), "digest": digest})

    def record_verdict(self, rnd: int, model_hash: str, gate: str, promoted: bool, failed: list[str]) -> str:
        """Canary check result (E8). Only promoted versions enter the registry the gateway follows."""
        return self._append("verdict", {"round": rnd, "model": model_hash, "gate": gate, "promoted": bool(promoted),
                                        "failed": failed})

    def record_revocation(self, rnd: int, client: int, rollback_to: int, evidence: float) -> str:
        """E9: a client's update privilege is revoked; training rolls back to registry version rollback_to."""
        return self._append("revocation", {"round": rnd, "client": int(client), "rollback_to": int(rollback_to),
                                           "evidence": float(evidence)})

    def revoked_clients(self) -> list[int]:
        return [b["client"] for b in self.blocks if b["kind"] == "revocation"]

    def registry_head(self, gate: str) -> str | None:
        heads = [b["model"] for b in self.blocks if b["kind"] == "verdict" and b["gate"] == gate and b["promoted"]]
        return heads[-1] if heads else None

    def decisions_under(self, model_hash: str) -> list[dict]:
        return [b for b in self.blocks if b["kind"] == "decisions" and b["model"] == model_hash]

    def verify(self) -> bool:
        prev = "0" * 64
        for b in self.blocks:
            body = {k: v for k, v in b.items() if k != "hash"}
            if body["prev"] != prev or hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != b["hash"]:
                return False
            prev = b["hash"]
        return True

    def summary(self) -> dict:
        kinds = [b["kind"] for b in self.blocks]
        return {"blocks": len(self.blocks), "rounds": kinds.count("round"), "decision_batches": kinds.count("decisions"),
                "head": self.head, "verified": self.verify(), "write_seconds": self.write_seconds}


class EvmLedger(MemoryLedger):
    """MemoryLedger plus the same records written to the Provenance contract on an EVM node.

    Records are appended locally first (hash chain); the on-chain write is queued to a background
    thread, so record_* returns immediately -- the gateway never waits for the chain. A second
    thread waits for receipts and timestamps confirmations. `flush()` blocks until everything is
    confirmed and returns latency / gas statistics. Uses the node's unlocked accounts (anvil):
    account 0 = FL coordinator, account 1 = gateway.
    """

    GAS = 3_000_000  # explicit gas: skips estimation, so a decision may be sent before its round is mined

    def __init__(self, rpc_url: str, artifact: str):
        super().__init__()
        import queue
        import threading
        from web3 import Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 120}))
        self.coordinator, self.gateway = self.w3.eth.accounts[:2]
        art = json.loads(open(artifact).read())
        factory = self.w3.eth.contract(abi=art["abi"], bytecode=art["bytecode"]["object"])
        receipt = self.w3.eth.wait_for_transaction_receipt(factory.constructor().transact({"from": self.coordinator}))
        self.contract = self.w3.eth.contract(address=receipt.contractAddress, abi=art["abi"])
        self.w3.eth.wait_for_transaction_receipt(
            self.contract.functions.setGateway(self.gateway, True).transact({"from": self.coordinator}))
        self.deploy_gas = receipt.gasUsed
        self.sent: queue.Queue = queue.Queue()
        self.todo: queue.Queue = queue.Queue()
        self.stats: list[dict] = []
        self.enqueue_seconds = 0.0
        threading.Thread(target=self._sender, daemon=True).start()
        threading.Thread(target=self._confirmer, daemon=True).start()

    @staticmethod
    def _b32(hex_digest: str) -> bytes:
        return bytes.fromhex(hex_digest)

    def _sender(self) -> None:
        while True:
            kind, fn, sender, t_enq = self.todo.get()
            self.sent.put((kind, fn.transact({"from": sender, "gas": self.GAS}), t_enq))
            self.todo.task_done()  # after the put, so flush() cannot see both queues empty mid-handoff

    def _confirmer(self) -> None:
        while True:
            kind, tx, t_enq = self.sent.get()
            r = self.w3.eth.wait_for_transaction_receipt(tx, timeout=600, poll_latency=0.05)
            self.stats.append({"kind": kind, "latency_s": time.perf_counter() - t_enq, "gas": r.gasUsed,
                               "ok": r.status == 1, "block": r.blockNumber})
            self.sent.task_done()

    def _enqueue(self, kind: str, fn, sender) -> None:
        t0 = time.perf_counter()
        self.todo.put((kind, fn, sender, t0))
        self.enqueue_seconds += time.perf_counter() - t0

    def record_round(self, rnd, model_hash, client_hashes, client_sizes, val_f1_macro) -> str:
        h = super().record_round(rnd, model_hash, client_hashes, client_sizes, val_f1_macro)
        fn = self.contract.functions.commitRound(rnd, self._b32(model_hash), [self._b32(c) for c in client_hashes],
                                                 [int(s) for s in client_sizes], int(round(val_f1_macro * 1e6)))
        self._enqueue("round", fn, self.coordinator)
        return h

    def record_decisions(self, model_hash, policy, t_from, t_to, n, digest) -> str:
        h = super().record_decisions(model_hash, policy, t_from, t_to, n, digest)
        fn = self.contract.functions.commitDecisions(self._b32(model_hash), t_from, t_to, int(n), self._b32(digest))
        self._enqueue("decisions", fn, self.gateway)
        return h

    def revoke(self, rnd: int, reason: str) -> None:
        self.w3.eth.wait_for_transaction_receipt(
            self.contract.functions.revokeRound(rnd, reason).transact({"from": self.coordinator}))

    def is_trusted(self, model_hash: str) -> bool:
        return self.contract.functions.isTrusted(self._b32(model_hash)).call()

    def audit(self) -> dict:
        """Re-derive the local records from the chain alone: every round and decision batch in the hash
        chain must appear, in order and field for field, as a RoundCommitted / DecisionsCommitted event."""
        ev = self.contract.events
        on_r = [(bytes(e.args.model).hex(), [bytes(c).hex() for c in e.args.clientUpdates])
                for e in ev.RoundCommitted.get_logs(from_block=0)]
        on_d = [(bytes(e.args.model).hex(), e.args.tFrom, e.args.tTo, e.args.n, bytes(e.args.digest).hex())
                for e in ev.DecisionsCommitted.get_logs(from_block=0)]
        loc_r = [(b["model"], b["clients"]) for b in self.blocks if b["kind"] == "round"]
        loc_d = [(b["model"], b["t"][0], b["t"][1], b["n"], b["digest"]) for b in self.blocks if b["kind"] == "decisions"]
        return {"onchain_rounds": len(on_r), "onchain_decisions": len(on_d), "rounds_match": on_r == loc_r,
                "decisions_match": on_d == loc_d,
                "trusted_models": [self.is_trusted(m) for m, _ in loc_r]}

    def flush(self) -> dict:
        self.todo.join()
        self.sent.join()
        out = {"contract": self.contract.address, "deploy_gas": self.deploy_gas,
               "enqueue_seconds_total": self.enqueue_seconds, "failed": sum(not s["ok"] for s in self.stats),
               "audit": self.audit(), "tx": self.stats}
        for kind in ("round", "decisions"):
            lat = np.array([s["latency_s"] for s in self.stats if s["kind"] == kind])
            gas = np.array([s["gas"] for s in self.stats if s["kind"] == kind])
            if len(lat):
                out[kind] = {"n": int(len(lat)), "latency_median_s": float(np.median(lat)),
                             "latency_p95_s": float(np.percentile(lat, 95)), "gas_median": int(np.median(gas))}
        return out
