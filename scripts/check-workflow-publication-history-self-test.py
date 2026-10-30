#!/usr/bin/env python3
"""Mutation self-test for check-workflow-publication-history.py.

The positive control is the real repository history. Each hostile case changes one input of a
production function (a commit, a pinned digest, a current receipt file, a receipt entry, a historical
v3 receipt or record, or the checker text) and must fail with the message of the check it targets.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-workflow-publication-history.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("workflow_history", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_checker()
    if module.check(ROOT, ROOT, module.RECEIPT_SHA256, module.CHECKER_SHA256) != module.EXPECTED_ENTRY_COUNT:
        raise SystemExit("positive control checked an unexpected number of entries")
    receipt = module.git_blob(ROOT, module.INTRODUCING_COMMIT, module.RECEIPT)
    cases: list[tuple[str, str, object]] = []

    def case(label: str, needle: str, call) -> None:
        cases.append((label, needle, call))

    case("missing commit", "not retrievable",
         lambda: module.verify_entries(ROOT, ("0" * 40,), receipt))
    case("commit before the receipt", "not retrievable",
         lambda: module.git_blob(ROOT, "41ba5f9f447d8ea8f94dca5efe0d92c1ed801b08", module.RECEIPT))
    case("pinned receipt digest", "pinned receipt digest",
         lambda: module.check(ROOT, ROOT, "f" * 64, module.CHECKER_SHA256))
    case("pinned checker digest", "pinned checker digest",
         lambda: module.check(ROOT, ROOT, module.RECEIPT_SHA256, "e" * 64))

    first = next(iter(json.loads(receipt)["files"]))

    def mutated_receipt(mutate) -> bytes:
        record = json.loads(receipt)
        mutate(record)
        return json.dumps(record).encode()

    for label, mutate, needle in (
        ("entry digest", lambda r: r["files"][first].__setitem__("sha256", "0" * 64), "differs from the receipt entry"),
        ("entry size", lambda r: r["files"][first].__setitem__("bytes", r["files"][first]["bytes"] + 1), "differs from the receipt entry"),
        ("entry size as float", lambda r: r["files"][first].__setitem__("bytes", float(r["files"][first]["bytes"])), "malformed"),
        ("entry size as Boolean", lambda r: r["files"][first].__setitem__("bytes", True), "malformed"),
        ("uppercase digest", lambda r: r["files"][first].__setitem__("sha256", r["files"][first]["sha256"].upper()), "malformed"),
        ("extra entry member", lambda r: r["files"][first].__setitem__("mode", "100644"), "malformed"),
        ("missing entry", lambda r: r["files"].pop(first), "expected 21 entries"),
    ):
        data = mutated_receipt(mutate)
        case(label, needle, lambda data=data: module.verify_entries(ROOT, module.HISTORICAL_COMMITS, data))
    case("duplicate member", "duplicate JSON member",
         lambda: module.receipt_entries(b'{"files": {}, "files": {}}'))

    v3_receipt = module.git_blob(ROOT, module.LAST_COMMIT, f"{module.RECEIPT_DIRECTORY}/previous-visual-receipt.md.txt")
    v3_records = module.git_blob(ROOT, module.LAST_COMMIT, f"{module.RECEIPT_DIRECTORY}/previous-actual-views.json.txt")
    case("v3 lens outcome", "v3 visual-receipt validation failed",
         lambda: module.replay_v3(ROOT, module.CHECKER_SHA256,
                                  {"receipt": v3_receipt.replace(b"| hierarchy | passed |", b"| hierarchy | failed |", 1)}))
    case("v3 reviewed PDF", "v3 visual-receipt validation failed",
         lambda: module.replay_v3(ROOT, module.CHECKER_SHA256, {"pdf": b"%PDF-1.7\n"}))
    records = json.loads(v3_records)
    records["views"].pop()
    case("v3 missing view record", "v3 visual-receipt validation failed",
         lambda: module.replay_v3(ROOT, module.CHECKER_SHA256, {"records": (json.dumps(records) + "\n").encode()}))
    case("checker without the v3 block", "exactly one block start",
         lambda: module.heredoc("echo\nPY\n", module.V3_START, "PY"))

    with tempfile.TemporaryDirectory(prefix="workflow-history-tree-") as temporary:
        tree = Path(temporary)
        (tree / module.RECEIPT_DIRECTORY).mkdir(parents=True)
        for path in (module.RECEIPT, module.PRIOR_RECEIPT):
            shutil.copyfile(ROOT / path, tree / path)
        current = tree / module.RECEIPT
        current.write_bytes(current.read_bytes() + b" ")
        case("changed current receipt", "differs from its historical bytes",
             lambda: module.check(tree, ROOT, module.RECEIPT_SHA256, module.CHECKER_SHA256))
        for label, needle, call in cases:
            try:
                call()
            except module.HistoryError as error:
                if needle not in str(error):
                    raise SystemExit(f"{label}: failed for the wrong reason: {error}")
                continue
            raise SystemExit(f"{label}: was accepted")
        shutil.copyfile(ROOT / module.RECEIPT, current)
        prior = tree / module.PRIOR_RECEIPT
        prior.write_bytes(prior.read_bytes().replace(b"Sepehr", b"sepehr", 1))
        try:
            module.check(tree, ROOT, module.RECEIPT_SHA256, module.CHECKER_SHA256)
        except module.HistoryError as error:
            if "differs from its historical bytes" not in str(error):
                raise SystemExit(f"changed prior receipt: failed for the wrong reason: {error}")
        else:
            raise SystemExit("changed prior receipt: was accepted")
    total = len(cases) + 1
    print(f"OK: workflow publication history checker accepted the repository and rejected {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
