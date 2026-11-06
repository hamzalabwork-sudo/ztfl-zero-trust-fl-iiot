"""Check that data/raw/ holds exactly the dataset files used for the reported results.

Usage: python scripts/check_data.py
Exit code 0 if every file is present and matches its SHA-256, 1 otherwise.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
EXPECTED = {
    "ML-EdgeIIoT-dataset.csv": "53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a",
    "Forge_IIOT_Pro.csv": "173f33313cdbcfa848c09fd9c586dd3106b2df517b6717068379b852d538d243",
    "wustl_iiot_2021.csv": "f897b24578cc6fdeb3e7a0e9ff63efd5bbdc926a545abbda725e0dbb348c6bca",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ok = True
    for name, want in EXPECTED.items():
        path = RAW / name
        if not path.exists():
            print(f"MISSING   {name}  (see data/README.md)")
            ok = False
            continue
        got = sha256(path)
        status = "OK" if got == want else "MISMATCH"
        ok &= got == want
        print(f"{status:9s} {name}  {got}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
