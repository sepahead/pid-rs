#!/usr/bin/env python3
"""Hostile controls for the inert negative-archive integrity checker."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Final, NoReturn


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CHECKER: Final[Path] = ROOT / "scripts/check-inert-negative-archives.py"
ARCHIVES: Final[tuple[str, ...]] = (
    "ksg-m1a-rejected-lifecycle-checker-20260828",
    "sxpid3-s1-historical-checkers-v1",
    "numerical-claim-history-20260725",
    "python-verifier-custody-m0-20260830",
)
FAILURE_MARKER: Final[bytes] = b"ERROR: inert negative archive rejected:"


class SelfTestError(RuntimeError):
    """A hostile archive mutation did not fail closed."""


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def command(root: Path, checker: Path = CHECKER) -> list[str]:
    result = [sys.executable]
    if sys.flags.optimize:
        result.append("-O")
    result.extend(["-I", "-S", "-B", str(checker), "--root", str(root)])
    return result


def run(root: Path, checker: Path = CHECKER) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command(root, checker),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "")},
    )


def copy_archives(destination: Path) -> None:
    for archive in ARCHIVES:
        source = ROOT / "audit/archive" / archive
        target = destination / "audit/archive" / archive
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    numerical_index = json.loads(
        index_path(ROOT, ARCHIVES[2]).read_text(encoding="utf-8")
    )
    for paths in numerical_index["successor_groups"].values():
        for relative in paths:
            source = ROOT / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def require_rejected(
    label: str,
    mutation: Callable[[Path], None],
) -> None:
    with tempfile.TemporaryDirectory(prefix="pid-rs-inert-archive-self-test-") as temporary:
        mirror = Path(temporary) / "repo"
        copy_archives(mirror)
        mutation(mirror)
        completed = run(mirror)
        if completed.returncode == 0:
            fail(f"{label}: hostile mutation was accepted")
        if FAILURE_MARKER not in completed.stderr:
            fail(
                f"{label}: failure lacked marker: "
                f"{completed.stderr.decode('utf-8', 'replace')}"
            )


def resealed_checker(root: Path, archive: str) -> Path:
    original_index = index_path(ROOT, archive).read_bytes()
    mutated_index = index_path(root, archive).read_bytes()
    old_length = len(original_index)
    new_length = len(mutated_index)
    old_digest = hashlib.sha256(original_index).hexdigest()
    new_digest = hashlib.sha256(mutated_index).hexdigest()
    source = CHECKER.read_text(encoding="utf-8")
    length_needle = f'"index_bytes": {old_length},'
    digest_needle = f'"index_sha256": "{old_digest}",'
    if source.count(length_needle) != 1 or source.count(digest_needle) != 1:
        fail(f"{archive}: checker byte-custody constants are not uniquely patchable")
    source = source.replace(length_needle, f'"index_bytes": {new_length},', 1)
    source = source.replace(
        digest_needle,
        f'"index_sha256": "{new_digest}",',
        1,
    )
    checker = root / "scripts/check-inert-negative-archives-resealed.py"
    checker.parent.mkdir(parents=True, exist_ok=True)
    checker.write_text(source, encoding="utf-8")
    return checker


def require_coherent_reseal_rejected(
    label: str,
    archive: str,
    mutation: Callable[[Path], None],
) -> None:
    with tempfile.TemporaryDirectory(prefix="pid-rs-inert-reseal-self-test-") as temporary:
        mirror = Path(temporary) / "repo"
        copy_archives(mirror)
        clean = run(mirror)
        if clean.returncode != 0:
            fail(
                f"{label}: clean hostile mirror was invalid: "
                f"{clean.stderr.decode('utf-8', 'replace')}"
            )
        mutation(mirror)
        checker = resealed_checker(mirror, archive)
        completed = run(mirror, checker)
        if completed.returncode == 0:
            fail(f"{label}: coherent matched-wrong reseal was accepted")
        if FAILURE_MARKER not in completed.stderr:
            fail(
                f"{label}: coherent reseal failure lacked marker: "
                f"{completed.stderr.decode('utf-8', 'replace')}"
            )


def index_path(root: Path, archive: str) -> Path:
    return root / "audit/archive" / archive / "INDEX.json"


def payload_path(root: Path, archive: str, ordinal: int = 0) -> Path:
    value = json.loads(index_path(root, archive).read_text(encoding="utf-8"))
    return root / value["payloads"][ordinal]["archive_path"]


def mutate_index(
    root: Path,
    archive: str,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    path = index_path(root, archive)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail("test fixture index is not an object")
    mutation(value)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def coherently_substitute_payload(
    root: Path,
    archive: str,
    ordinal: int = 0,
    *,
    rebind_source_oid: bool = True,
) -> None:
    path = payload_path(root, archive, ordinal)
    raw = path.read_bytes() + b"\nmatched-wrong-substitution\n"
    path.write_bytes(raw)

    def update(value: dict[str, Any]) -> None:
        payload = value["payloads"][ordinal]
        payload["byte_length"] = len(raw)
        payload["sha256"] = hashlib.sha256(raw).hexdigest()
        if rebind_source_oid:
            header = f"blob {len(raw)}\0".encode("ascii")
            payload["source_blob_oid"] = hashlib.sha1(
                header + raw,
                usedforsecurity=False,
            ).hexdigest()

    mutate_index(root, archive, update)


def coherently_rewrite_disposition(root: Path, archive: str) -> None:
    path = root / "audit/archive" / archive / "DISPOSITION.md"
    raw = path.read_bytes() + b"\nMatched-wrong authority rewrite.\n"
    path.write_bytes(raw)

    def update(value: dict[str, Any]) -> None:
        value["disposition"]["byte_length"] = len(raw)
        value["disposition"]["sha256"] = hashlib.sha256(raw).hexdigest()

    mutate_index(root, archive, update)


def main() -> int:
    baseline = run(ROOT)
    if baseline.returncode != 0:
        fail(f"baseline checker failed: {baseline.stderr.decode('utf-8', 'replace')}")

    ksg = ARCHIVES[0]
    s1 = ARCHIVES[1]
    numerical = ARCHIVES[2]
    python_custody = ARCHIVES[3]

    cases: list[tuple[str, Callable[[Path], None]]] = [
        (
            "payload-byte",
            lambda root: payload_path(root, ksg).write_bytes(
                payload_path(root, ksg).read_bytes() + b"\n"
            ),
        ),
        (
            "disposition-byte",
            lambda root: (
                root / "audit/archive" / ksg / "DISPOSITION.md"
            ).write_bytes(
                (root / "audit/archive" / ksg / "DISPOSITION.md").read_bytes() + b"\n"
            ),
        ),
        (
            "current-authority",
            lambda root: mutate_index(
                root, ksg, lambda value: value.__setitem__("current_authority", True)
            ),
        ),
        (
            "payload-executable-claim",
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["payloads"][0].__setitem__("executable", True),
            ),
        ),
        (
            "payload-executable-mode",
            lambda root: payload_path(root, ksg).chmod(0o755),
        ),
        (
            "s1-promoted",
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"].__setitem__(
                    "status", "accepted"
                ),
            ),
        ),
        (
            "s1-closed",
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"].__setitem__("s1", "ACCEPT"),
            ),
        ),
        (
            "program-closed",
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"].__setitem__(
                    "programs_closed", 1
                ),
            ),
        ),
        (
            "neumaier-history-promoted",
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: next(
                    item
                    for item in value["payloads"]
                    if item["id"] == "neumaier-guard-discriminator-open"
                ).__setitem__("role", "current_universal_equivalence"),
            ),
        ),
        (
            "noncanonical-index",
            lambda root: index_path(root, ksg).write_text(
                json.dumps(json.loads(index_path(root, ksg).read_text(encoding="utf-8"))),
                encoding="utf-8",
            ),
        ),
        (
            "duplicate-member",
            lambda root: index_path(root, ksg).write_text(
                index_path(root, ksg)
                .read_text(encoding="utf-8")
                .replace(
                    '  "archive_id":',
                    '  "archive_id": "duplicate",\n  "archive_id":',
                    1,
                ),
                encoding="utf-8",
            ),
        ),
        (
            "extra-file",
            lambda root: (
                root / "audit/archive" / ksg / "UNDECLARED.txt"
            ).write_text("unexpected\n", encoding="utf-8"),
        ),
        (
            "missing-payload",
            lambda root: payload_path(root, ksg).unlink(),
        ),
    ]

    for label, mutation in cases:
        require_rejected(label, mutation)

    def symbolic(root: Path) -> None:
        target = payload_path(root, ksg)
        replacement = payload_path(root, ksg, 1)
        target.unlink()
        target.symlink_to(replacement.name)

    require_rejected("symbolic-payload", symbolic)

    def hard_link(root: Path) -> None:
        target = payload_path(root, ksg)
        source = payload_path(root, ksg, 1)
        target.unlink()
        os.link(source, target)

    require_rejected("hard-linked-payload", hard_link)

    reseal_cases: list[tuple[str, str, Callable[[Path], None]]] = [
        (
            "reseal-ksg-case-identity",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["cases"].__setitem__(0, "FG-WRONG-CASE"),
            ),
        ),
        (
            "reseal-ksg-integration-source",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["integration_source"].__setitem__(
                    "commit", "0" * 40
                ),
            ),
        ),
        (
            "reseal-ksg-recovered-source",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["recovered_source"].__setitem__(
                    "local_ref", "refs/custody/rejected/wrong"
                ),
            ),
        ),
        (
            "reseal-ksg-replay-activation",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["replay"].__setitem__(
                    "archived_replay_source_executed", True
                ),
            ),
        ),
        (
            "reseal-ksg-mathematical-authority",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["scope"].__setitem__(
                    "mathematical_authority", True
                ),
            ),
        ),
        (
            "reseal-ksg-receipt-role",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: next(
                    item
                    for item in value["payloads"]
                    if item["id"] == "historical-negative-receipt"
                ).__setitem__("role", "current_qualification_authority"),
            ),
        ),
        (
            "reseal-ksg-original-path",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["payloads"][0].__setitem__(
                    "original_path", "scripts/not-the-source.py"
                ),
            ),
        ),
        (
            "reseal-ksg-integration-source-path",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["payloads"][0].__setitem__(
                    "source_path", "scripts/not-the-source.py"
                ),
            ),
        ),
        (
            "reseal-ksg-archive-path-traversal",
            ksg,
            lambda root: mutate_index(
                root,
                ksg,
                lambda value: value["payloads"][0].__setitem__(
                    "archive_path",
                    "audit/archive/ksg-m1a-rejected-lifecycle-checker-20260828/"
                    "payload/../DISPOSITION.md",
                ),
            ),
        ),
        (
            "reseal-ksg-coherent-payload-substitution",
            ksg,
            lambda root: coherently_substitute_payload(root, ksg),
        ),
        (
            "reseal-ksg-payload-substitution-without-source-rebind",
            ksg,
            lambda root: coherently_substitute_payload(
                root,
                ksg,
                rebind_source_oid=False,
            ),
        ),
        (
            "reseal-ksg-coherent-disposition-rewrite",
            ksg,
            lambda root: coherently_rewrite_disposition(root, ksg),
        ),
        (
            "reseal-s1-packet-promotion",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"].__setitem__(
                    "status", "accepted"
                ),
            ),
        ),
        (
            "reseal-s1-fills-h1",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["scope"].__setitem__("fills_h1", True),
            ),
        ),
        (
            "reseal-s1-excluded-binding-digest",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"]["bindings"][1].__setitem__(
                    "sha256", "0" * 64
                ),
            ),
        ),
        (
            "reseal-s1-record-custody-promotion",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"]["bindings"][1].__setitem__(
                    "custody", "accepted_current_review"
                ),
            ),
        ),
        (
            "reseal-s1-program-closure",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["excluded_open_packet"].__setitem__(
                    "programs_closed", 1
                ),
            ),
        ),
        (
            "reseal-s1-historical-source",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: value["payloads"][0].__setitem__(
                    "historical_commit", "0" * 40
                ),
            ),
        ),
        (
            "reseal-s1-record-role",
            s1,
            lambda root: mutate_index(
                root,
                s1,
                lambda value: next(
                    item
                    for item in value["payloads"]
                    if item["id"] == "false-green-record-v3"
                ).__setitem__("role", "current_source_review_authority"),
            ),
        ),
        (
            "reseal-numerical-population-claim",
            numerical,
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: value["scope"].__setitem__(
                    "population_claimed", True
                ),
            ),
        ),
        (
            "reseal-numerical-universal-refinement",
            numerical,
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: value["scope"].__setitem__(
                    "universal_binary64_refinement_claimed", True
                ),
            ),
        ),
        (
            "reseal-numerical-successor-route",
            numerical,
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: value["successor_groups"]["categorical_imin"].__setitem__(
                    0, "crates/pid-core/tests/imin.rs"
                ),
            ),
        ),
        (
            "reseal-numerical-role-promotion",
            numerical,
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: next(
                    item
                    for item in value["payloads"]
                    if item["id"] == "neumaier-guard-discriminator-open"
                ).__setitem__("role", "current_universal_equivalence"),
            ),
        ),
        (
            "reseal-numerical-integration-source",
            numerical,
            lambda root: mutate_index(
                root,
                numerical,
                lambda value: value["integration_source"].__setitem__(
                    "tree", "0" * 40
                ),
            ),
        ),
        (
            "reseal-python-omitted-registry-promotion",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: value["omitted_derived_registry"].__setitem__(
                    "custody", "copied_current_authority"
                ),
            ),
        ),
        (
            "reseal-python-drift-probe-promotion",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: value["current_drift_probe"].__setitem__(
                    "status", "current_inventory_authority"
                ),
            ),
        ),
        (
            "reseal-python-execution-custody",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: value["scope"].__setitem__(
                    "execution_custody_closed", True
                ),
            ),
        ),
        (
            "reseal-python-replay-activation",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: value["replay"].__setitem__(
                    "archived_checker_executed", True
                ),
            ),
        ),
        (
            "reseal-python-process-lesson",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: value["process_lessons"].__setitem__(
                    0, "stored_source_proves_execution"
                ),
            ),
        ),
        (
            "reseal-python-checker-role",
            python_custody,
            lambda root: mutate_index(
                root,
                python_custody,
                lambda value: next(
                    item
                    for item in value["payloads"]
                    if item["id"] == "inventory-checker"
                ).__setitem__("role", "current_execution_custody_authority"),
            ),
        ),
    ]

    for label, archive, mutation in reseal_cases:
        require_coherent_reseal_rejected(label, archive, mutation)

    print(
        "OK: inert negative archive self-test rejected "
        f"{len(cases) + 2 + len(reseal_cases)} byte, metadata, authority, source, "
        "inventory, filesystem, and coherent-reseal mutations"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as error:
        print(f"ERROR: inert negative archive self-test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
