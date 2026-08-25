#!/usr/bin/env python3
"""Hostile isolated mutations for check-advisory-councils-archive.py."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable


if sys.version_info < (3, 11):
    raise SystemExit(
        "check-advisory-councils-archive-self-test.py requires Python 3.11 or newer"
    )


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-advisory-councils-archive.py"
ARCHIVE_REL = Path("audit/archive/advisory-councils-20260725-20260726")
INDEX_REL = ARCHIVE_REL / "INDEX.json"
SCHEMA_REL = ARCHIVE_REL / "INDEX.schema.json"
DISPOSITION_REL = ARCHIVE_REL / "DISPOSITION.md"
EXPECTED_STDOUT = (
    '{"archive_id":"advisory-councils-20260725-20260726","payloads":5,'
    '"rederivation_candidates":10,"status":"ok","withheld_hash_only":10}\n'
)
AUTHORITY_SURFACES = (
    "method-catalog.json",
    "METHODS.md",
    "release-scope-1.0.json",
    "RELEASE_SCOPE_1_0.md",
    "audit/evidence/assurance-registry.json",
    "audit/evidence/assurance-registry-typed-view-v1.json",
    "ecosystem-capabilities.json",
    "ECOSYSTEM_CAPABILITIES.md",
    "audit/source-errata.json",
)
Mutation = Callable[[Path], None]


class SelfTestError(RuntimeError):
    """The hostile suite did not discriminate a mutation."""


def canonical_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    path.chmod(0o644)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SelfTestError(f"fixture JSON root is not an object: {path}")
    return value


def mutate_index(root: Path, mutation: Callable[[dict[str, Any]], None]) -> None:
    path = root / INDEX_REL
    value = load_json(path)
    mutation(value)
    canonical_write(path, value)


def mutate_schema(root: Path, mutation: Callable[[dict[str, Any]], None]) -> None:
    path = root / SCHEMA_REL
    value = load_json(path)
    mutation(value)
    canonical_write(path, value)


def set_nested(value: dict[str, Any], path: tuple[Any, ...], replacement: Any) -> None:
    cursor: Any = value
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement


def append_bytes(path: Path, suffix: bytes) -> None:
    path.write_bytes(path.read_bytes() + suffix)
    path.chmod(0o644)


def materialize_baseline(destination: Path) -> None:
    shutil.copytree(
        ROOT / ARCHIVE_REL, destination / ARCHIVE_REL, copy_function=shutil.copy2
    )
    for relative in AUTHORITY_SURFACES:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    index = load_json(ROOT / INDEX_REL)
    for payload in index["payloads"]:
        for successor in payload["current_successors"]:
            relative = Path(successor["path"])
            source = ROOT / relative
            target = destination / relative
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    for relative in ("Cargo.toml", "justfile"):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    for relative in ("crates", "scripts", ".github/workflows"):
        (destination / relative).mkdir(parents=True, exist_ok=True)


def checker_command(root: Path) -> list[str]:
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-O")
    command.extend(["-I", "-S", "-B", str(CHECKER), "--root", str(root)])
    return command


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("PYTHON")
    }
    environment.setdefault("LC_ALL", "C")
    environment.setdefault("TZ", "UTC")
    return subprocess.run(
        checker_command(root),
        cwd=root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )


def require_pass(root: Path, label: str) -> None:
    result = run_checker(root)
    if result.returncode != 0:
        raise SelfTestError(
            f"{label}: baseline failed with {result.returncode}: {result.stderr!r}"
        )
    if result.stdout != EXPECTED_STDOUT or result.stderr:
        raise SelfTestError(
            f"{label}: baseline output changed: stdout={result.stdout!r} "
            f"stderr={result.stderr!r}"
        )


def require_rejection(
    baseline: Path,
    scratch_parent: Path,
    name: str,
    expected_fragment: str,
    mutation: Mutation,
) -> None:
    fixture = scratch_parent / name
    shutil.copytree(baseline, fixture, copy_function=shutil.copy2)
    mutation(fixture)
    result = run_checker(fixture)
    if result.returncode == 0:
        raise SelfTestError(f"{name}: mutation was accepted")
    if result.stdout:
        raise SelfTestError(
            f"{name}: rejected mutation wrote stdout: {result.stdout!r}"
        )
    expected = f"advisory archive check failed: {expected_fragment}"
    if expected not in result.stderr:
        raise SelfTestError(
            f"{name}: wrong diagnostic; expected {expected!r}, got {result.stderr!r}"
        )


def payload_path(root: Path, name: str) -> Path:
    return root / ARCHIVE_REL / "payload" / name


def mutate_duplicate_index_key(root: Path) -> None:
    path = root / INDEX_REL
    raw = path.read_text(encoding="utf-8")
    needle = '  "archive_id": "advisory-councils-20260725-20260726",\n'
    if raw.count(needle) != 1:
        raise SelfTestError("duplicate-key mutation anchor changed")
    path.write_text(raw.replace(needle, needle + needle, 1), encoding="utf-8")
    path.chmod(0o644)


def mutate_noncanonical_index(root: Path) -> None:
    path = root / INDEX_REL
    raw = path.read_bytes()
    path.write_bytes(b" \n" + raw)
    path.chmod(0o644)


def mutate_payload_byte(root: Path) -> None:
    append_bytes(
        payload_path(root, "fable5-completion-triage-prompt.md"),
        b"hostile-byte\n",
    )


def mutate_payload_mode(root: Path) -> None:
    payload_path(root, "fable5-completion-triage-prompt.md").chmod(0o755)


def mutate_payload_symlink(root: Path) -> None:
    target = payload_path(root, "fable5-completion-triage-prompt.md")
    target.unlink()
    target.symlink_to("fable5-imin-tie-swap-review-prompt.md")


def mutate_extra_archive_file(root: Path) -> None:
    path = root / ARCHIVE_REL / "payload" / "extra.md"
    path.write_text("extra\n", encoding="utf-8")
    path.chmod(0o644)


def mutate_add_readme(root: Path) -> None:
    path = root / ARCHIVE_REL / "README.md"
    path.write_text("forbidden\n", encoding="utf-8")
    path.chmod(0o644)


def mutate_authority_wire(root: Path) -> None:
    append_bytes(
        root / "method-catalog.json",
        b'\n"audit/archive/advisory-councils-20260725-20260726"\n',
    )


def mutate_execution_wire(root: Path) -> None:
    append_bytes(
        root / "justfile",
        b"\n# fable5-completion-triage-prompt.md\n",
    )


def mutate_missing_successor(root: Path) -> None:
    (root / "PID_MATHEMATICAL_AUDIT_PROTOCOL.md").unlink()


def mutate_original_prompt_copy(root: Path) -> None:
    path = root / "audit/evidence/fable5-completion-triage-prompt.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("duplicate authority ambiguity\n", encoding="utf-8")
    path.chmod(0o644)


def mutate_raw_withheld_copy(root: Path) -> None:
    path = root / "audit/evidence/fable5-completion-triage-review-2026-07-25.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("withheld\n", encoding="utf-8")
    path.chmod(0o644)


def mutate_disposition(root: Path) -> None:
    append_bytes(root / DISPOSITION_REL, b"drift\n")


def main() -> int:
    require_pass(ROOT, "production baseline")

    cases: list[tuple[str, str, Mutation]] = [
        (
            "current-authority",
            "authority.current_authority must be exact boolean False",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("authority", "current_authority"), True
                ),
            ),
        ),
        (
            "evidence-authority",
            "authority.evidence_authority must be exact boolean False",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("authority", "evidence_authority"), True
                ),
            ),
        ),
        (
            "payload-status",
            "completion-triage-20260725: status must remain historical-prompt",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("payloads", 0, "status"), "accepted-result"
                ),
            ),
        ),
        (
            "payload-importable",
            "completion-triage-20260725.importable must be exact boolean False",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(value, ("payloads", 0, "importable"), True),
            ),
        ),
        (
            "payload-executable",
            "completion-triage-20260725.executable must be exact boolean False",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(value, ("payloads", 0, "executable"), True),
            ),
        ),
        (
            "payload-digest-declaration",
            "completion-triage-20260725: declared digest drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(value, ("payloads", 0, "sha256"), "0" * 64),
            ),
        ),
        (
            "payload-byte",
            "completion-triage-20260725: payload bytes or digest changed",
            mutate_payload_byte,
        ),
        (
            "payload-mode",
            "payload completion-triage-20260725 mode drifted",
            mutate_payload_mode,
        ),
        (
            "payload-symlink",
            "archive symlink is forbidden",
            mutate_payload_symlink,
        ),
        (
            "original-path",
            "completion-triage-20260725: original path drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("payloads", 0, "original_path"),
                    "audit/evidence/renamed.md",
                ),
            ),
        ),
        (
            "source-branch",
            "source branch/head/intake/status provenance drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("source_observation", "observed_source_branch"),
                    "main",
                ),
            ),
        ),
        (
            "source-head",
            "source branch/head/intake/status provenance drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("source_observation", "observed_source_head"),
                    "0" * 40,
                ),
            ),
        ),
        (
            "frozen-intake",
            "source branch/head/intake/status provenance drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("source_observation", "frozen_intake_head"),
                    "0" * 40,
                ),
            ),
        ),
        (
            "source-status",
            "source branch/head/intake/status provenance drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("source_observation", "source_status_sha256"),
                    "0" * 64,
                ),
            ),
        ),
        (
            "successor-removed",
            "completion-triage-20260725: current successor set/order/role drifted",
            lambda root: mutate_index(
                root,
                lambda value: value["payloads"][0]["current_successors"].pop(),
            ),
        ),
        (
            "successor-role",
            "completion-triage-20260725: current successor set/order/role drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("payloads", 0, "current_successors", 0, "role"),
                    "scientific evidence",
                ),
            ),
        ),
        (
            "successor-missing",
            "completion-triage-20260725: current successor missing or symlinked",
            mutate_missing_successor,
        ),
        (
            "license-top",
            "top-level license boundary drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("license_boundary", "expression"), "NOASSERTION"
                ),
            ),
        ),
        (
            "license-payload",
            "completion-triage-20260725: license boundary drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("payloads", 0, "license", "external_payload_embedded"),
                    True,
                ),
            ),
        ),
        (
            "privacy-top",
            "privacy/scan boundary drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("privacy_boundary", "literal_absolute_local_paths_retained"),
                    0,
                ),
            ),
        ),
        (
            "privacy-payload",
            "completion-triage-20260725: absolute-path disclosure count drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("payloads", 0, "privacy", "absolute_user_path_occurrences"),
                    0,
                ),
            ),
        ),
        (
            "withheld-included",
            "completion-triage-response-20260725.included must be exact boolean False",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("withheld_records", 0, "included"), True
                ),
            ),
        ),
        (
            "withheld-payload-path",
            "completion-triage-response-20260725: withheld payload path must remain null",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("withheld_records", 0, "payload_path"),
                    "payload/response.md",
                ),
            ),
        ),
        (
            "withheld-digest",
            "completion-triage-response-20260725: withheld digest/length drifted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value, ("withheld_records", 0, "sha256"), "0" * 64
                ),
            ),
        ),
        (
            "rederivation-promoted",
            "imin-exact-target-tie-predicate: rederivation status was promoted",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("rederivation_queue", 0, "status"),
                    "accepted",
                ),
            ),
        ),
        (
            "index-digest-only",
            "INDEX.json size or digest changed",
            lambda root: mutate_index(
                root,
                lambda value: set_nested(
                    value,
                    ("payloads", 0, "scientific_value"),
                    value["payloads"][0]["scientific_value"] + " drift",
                ),
            ),
        ),
        (
            "index-duplicate-key",
            "invalid INDEX.json: duplicate JSON key",
            mutate_duplicate_index_key,
        ),
        (
            "index-noncanonical",
            "INDEX.json is not canonical sorted JSON",
            mutate_noncanonical_index,
        ),
        (
            "schema-digest",
            "INDEX.schema.json size or digest changed",
            lambda root: mutate_schema(
                root,
                lambda value: set_nested(value, ("$id",), "hostile/schema"),
            ),
        ),
        (
            "disposition-digest",
            "DISPOSITION.md size or digest changed",
            mutate_disposition,
        ),
        (
            "extra-archive-file",
            "archive file inventory changed",
            mutate_extra_archive_file,
        ),
        (
            "archive-readme",
            "archive file inventory changed",
            mutate_add_readme,
        ),
        (
            "authority-wire",
            "archive authority wiring is forbidden",
            mutate_authority_wire,
        ),
        (
            "execution-wire",
            "archive execution/import wiring is forbidden",
            mutate_execution_wire,
        ),
        (
            "original-prompt-duplicate",
            "completion-triage-20260725: original evidence-path copy is forbidden; archive only",
            mutate_original_prompt_copy,
        ),
        (
            "raw-withheld-companion",
            "completion-triage-response-20260725: raw withheld companion is present",
            mutate_raw_withheld_copy,
        ),
    ]

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-advisory-archive-self-test-"
    ) as scratch_text:
        scratch = Path(scratch_text)
        baseline = scratch / "baseline"
        materialize_baseline(baseline)
        require_pass(baseline, "isolated baseline")
        mutations = scratch / "mutations"
        mutations.mkdir()
        for name, expected_fragment, mutation in cases:
            require_rejection(
                baseline,
                mutations,
                name,
                expected_fragment,
                mutation,
            )

    print(
        json.dumps(
            {
                "baseline_checks": 2,
                "mutations": len(cases),
                "status": "ok",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
