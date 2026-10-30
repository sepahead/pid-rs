#!/usr/bin/env python3
"""Check that the predecessor evidence of the workflow publication survives in Git history.

Until the October 2026 republication, the exact workflow gate accepted the PDF through two links: the
5 September 2026 visual review (v3), bound to a retained pre-authorship PDF copy, and an
authorship-only delta check from that copy to the current PDF. The republication changed the content,
so the current gate accepts a new visual review instead, and the retained copies may later be
redacted. This check keeps the old evidence verifiable from Git alone:

1. every file entry of the authorship receipt matches its exact blob, by size and SHA-256, at the
   merge that introduced the receipt and at the last commit before the republication;
2. the two receipt files in the current tree are byte-identical to their historical blobs; and
3. the v3 visual-receipt validator, extracted from the pinned historical checker blob, accepts the
   historical receipt, view records, PDF copy and rendering receipt again.

With `--authorship-replay` it also re-runs the historical authorship-only delta check on the
historical blobs; that step needs Poppler's `pdfinfo` and `pdftotext`. The check needs full Git
history and fails closed in a shallow clone. Agreement shows that the historical bytes and their
historical acceptance are reproducible; it is not a new review of the old publication.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if sys.version_info < (3, 11):
    raise SystemExit("check-workflow-publication-history.py requires Python 3.11+")

ROOT = Path(__file__).resolve().parent.parent
GIT_EXECUTABLE = "/usr/bin/git"
RECEIPT_DIRECTORY = "audit/evidence/mathematical-workflow-authorship-2026-09-23"
RECEIPT = f"{RECEIPT_DIRECTORY}/SUCCESSOR-v2.json"
PRIOR_RECEIPT = f"{RECEIPT_DIRECTORY}/SUCCESSOR.json"
RECEIPT_SHA256 = "be777ffd770e403bc807ab7e57021439fdeaf35f317ee5889c36000ce5958600"
# The merge that introduced the receipt, and the last commit whose gate used the old evidence chain.
INTRODUCING_COMMIT = "b5afd1b9580538f31b161201b80afeb12ae194cb"
LAST_COMMIT = "6aad6ad020260e57a5e3de18f8b3594cafc67293"
HISTORICAL_COMMITS = (INTRODUCING_COMMIT, LAST_COMMIT)
CHECKER = "scripts/check-mathematical-workflow-pdf.sh"
CHECKER_SHA256 = "085bcdefecf76b1e9a67436004e82918bd66f75543ed1e6af96e12da6e2c843c"
EXPECTED_ENTRY_COUNT = 21
V3_START = '    "$SNAPSHOT_ROOT/$AUTHORSHIP_DIR/previous-actual-views.json.txt" <<\'PY\''
AUTHORSHIP_START = '  python3 -I -S -B - "$SNAPSHOT_ROOT" "$AUTHORSHIP_RECEIPT_SHA256" <<\'PY_AUTHORSHIP\''


class HistoryError(Exception):
    pass


def git_blob(git_root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        [GIT_EXECUTABLE, "-C", str(git_root), "cat-file", "blob", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise HistoryError(f"{commit[:12]}:{path} is not retrievable; the check needs full Git history")
    return result.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise HistoryError(f"receipt has a duplicate JSON member: {key}")
        result[key] = value
    return result


def receipt_entries(receipt_bytes: bytes) -> dict[str, dict[str, object]]:
    try:
        record = json.loads(receipt_bytes.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, ValueError) as error:
        raise HistoryError(f"receipt is not strict UTF-8 JSON: {error}") from error
    files = record.get("files") if isinstance(record, dict) else None
    if not isinstance(files, dict) or len(files) != EXPECTED_ENTRY_COUNT:
        raise HistoryError(f"receipt file inventory is not the expected {EXPECTED_ENTRY_COUNT} entries")
    for path, entry in files.items():
        if (
            not isinstance(entry, dict)
            or set(entry) != {"bytes", "sha256"}
            or type(entry["bytes"]) is not int
            or not isinstance(entry["sha256"], str)
            or len(entry["sha256"]) != 64
            or entry["sha256"].strip("0123456789abcdef")
        ):
            raise HistoryError(f"receipt entry is malformed: {path!r}")
    return files


def verify_entries(git_root: Path, commits: tuple[str, ...], receipt_bytes: bytes) -> int:
    entries = receipt_entries(receipt_bytes)
    for commit in commits:
        for path, entry in entries.items():
            data = git_blob(git_root, commit, path)
            if len(data) != entry["bytes"] or sha256(data) != entry["sha256"]:
                raise HistoryError(f"{commit[:12]}:{path} differs from the receipt entry")
    return len(entries)


def heredoc(script: str, start_line: str, end_line: str) -> str:
    lines = script.split("\n")
    if lines.count(start_line) != 1:
        raise HistoryError(f"historical checker does not contain exactly one block start {start_line.strip()!r}")
    begin = lines.index(start_line) + 1
    try:
        end = lines.index(end_line, begin)
    except ValueError as error:
        raise HistoryError(f"historical checker block lacks its end marker {end_line!r}") from error
    return "\n".join(lines[begin:end]) + "\n"


def historical_checker(git_root: Path, checker_sha256: str) -> str:
    data = git_blob(git_root, LAST_COMMIT, CHECKER)
    if sha256(data) != checker_sha256:
        raise HistoryError("historical checker bytes differ from the pinned checker digest")
    return data.decode("utf-8")


def run_block(block: str, arguments: list[str], label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="workflow-history-block-") as temporary:
        script = Path(temporary) / "block.py"
        script.write_text(block, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-B", str(script), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["no diagnostic"]
        raise HistoryError(f"historical {label} validation failed: {detail[0]}")


def replay_v3(git_root: Path, checker_sha256: str, replacements: dict[str, bytes] | None = None) -> None:
    """Re-run the historical v3 receipt validator on the historical blobs (optionally replaced)."""
    block = heredoc(historical_checker(git_root, checker_sha256), V3_START, "PY")
    names = {
        "receipt": f"{RECEIPT_DIRECTORY}/previous-visual-receipt.md.txt",
        "pdf": f"{RECEIPT_DIRECTORY}/previous.pdf.bin",
        "rendering": f"{RECEIPT_DIRECTORY}/previous-rendering-receipt.tsv.txt",
        "records": f"{RECEIPT_DIRECTORY}/previous-actual-views.json.txt",
    }
    with tempfile.TemporaryDirectory(prefix="workflow-history-v3-") as temporary:
        paths = {}
        for key, path in names.items():
            data = (replacements or {}).get(key)
            target = Path(temporary) / key
            target.write_bytes(data if data is not None else git_blob(git_root, LAST_COMMIT, path))
            paths[key] = str(target)
        run_block(block, [paths["receipt"], paths["pdf"], paths["rendering"], "87", "120", "300",
                          paths["records"]], "v3 visual-receipt")


def replay_authorship(git_root: Path, checker_sha256: str, receipt_bytes: bytes) -> None:
    block = heredoc(historical_checker(git_root, checker_sha256), AUTHORSHIP_START, "PY_AUTHORSHIP")
    with tempfile.TemporaryDirectory(prefix="workflow-history-authorship-") as temporary:
        root = Path(temporary)
        for path in receipt_entries(receipt_bytes):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git_blob(git_root, LAST_COMMIT, path))
        for path in (RECEIPT, PRIOR_RECEIPT):
            (root / path).write_bytes(git_blob(git_root, LAST_COMMIT, path))
        run_block(block, [str(root), RECEIPT_SHA256], "authorship-only")


def check(tree_root: Path, git_root: Path, receipt_sha256: str, checker_sha256: str,
          authorship_replay: bool = False) -> int:
    historical_receipt = git_blob(git_root, INTRODUCING_COMMIT, RECEIPT)
    if sha256(historical_receipt) != receipt_sha256:
        raise HistoryError("historical receipt bytes differ from the pinned receipt digest")
    for path in (RECEIPT, PRIOR_RECEIPT):
        if (tree_root / path).read_bytes() != git_blob(git_root, INTRODUCING_COMMIT, path):
            raise HistoryError(f"{path} in the current tree differs from its historical bytes")
    count = verify_entries(git_root, HISTORICAL_COMMITS, historical_receipt)
    replay_v3(git_root, checker_sha256)
    if authorship_replay:
        replay_authorship(git_root, checker_sha256, historical_receipt)
    return count


def main() -> int:
    arguments = sys.argv[1:]
    if arguments not in ([], ["--authorship-replay"]):
        print("usage: check-workflow-publication-history.py [--authorship-replay]", file=sys.stderr)
        return 2
    authorship = arguments == ["--authorship-replay"]
    try:
        count = check(ROOT, ROOT, RECEIPT_SHA256, CHECKER_SHA256, authorship)
    except (HistoryError, OSError, UnicodeDecodeError) as error:
        print(f"workflow publication history check failed: {error}", file=sys.stderr)
        return 1
    replayed = "v3 visual-receipt and authorship-only checks" if authorship else "v3 visual-receipt check"
    print(
        f"OK: the authorship receipt and its {count} file entries match exact Git blobs at "
        f"{len(HISTORICAL_COMMITS)} historical commits, the current receipt files are unchanged, and "
        f"the historical {replayed} accepted the historical blobs again"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
