#!/usr/bin/env python3
"""Hostile controls for the independent composite-v11 checker."""

from __future__ import annotations

import sys


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-m1a-composite-v11-self-test.py requires Python 3.11+ "
        "-I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)


import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import zipfile


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v11.py"


class SelfTestError(RuntimeError):
    """A positive control failed or a hostile mutation survived."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_checker():
    specification = importlib.util.spec_from_file_location(
        "pid_rs_v11_checker", CHECKER
    )
    require(
        specification is not None and specification.loader is not None,
        "checker module spec",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(operation, label: str) -> None:
    try:
        operation()
    except (OSError, RuntimeError, ValueError):
        return
    raise SelfTestError(f"hostile control passed: {label}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_fixture(root: Path, relative: str, raw: bytes, mode: int) -> Path:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    destination.chmod(mode)
    return destination


def filesystem_controls(checker) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-v11-checker-fs-") as raw:
        root = Path(raw).resolve(strict=True)
        ordinary = checker.ExpectedAuthority(
            "ordinary.bin", "ordinary", "100644", 0o644, "ordinary_2mib"
        )
        special = checker.ExpectedAuthority(
            checker.SPECIAL_PATH,
            "terminal",
            "100644",
            0o644,
            "terminal_c9_capture_4mib",
            False,
        )
        ordinary_path = write_fixture(root, ordinary.path, b"A", 0o644)
        special_raw = b"B" * (checker.ORDINARY_LIMIT + 1)
        write_fixture(root, special.path, special_raw, 0o644)
        root_fd = os.open(root, checker.directory_flags())
        try:
            require(checker.stable_read(root_fd, ordinary) == b"A", "ordinary positive")
            require(
                checker.stable_read(root_fd, special) == special_raw,
                "special exact-path positive",
            )

            ordinary_path.write_bytes(b"A" * (checker.ORDINARY_LIMIT + 1))
            ordinary_path.chmod(0o644)
            expect_rejection(
                lambda: checker.stable_read(root_fd, ordinary),
                "ordinary max-plus-one",
            )
            rejected += 1

            ordinary_path.write_bytes(b"A")
            ordinary_path.chmod(0o600)
            expect_rejection(
                lambda: checker.stable_read(root_fd, ordinary), "wrong mode"
            )
            rejected += 1
            ordinary_path.chmod(0o644)

            target = root / "target.bin"
            target.write_bytes(b"A")
            target.chmod(0o644)
            ordinary_path.unlink()
            ordinary_path.symlink_to(target.name)
            expect_rejection(
                lambda: checker.stable_read(root_fd, ordinary), "symlink leaf"
            )
            rejected += 1
            ordinary_path.unlink()
            ordinary_path.write_bytes(b"A")
            ordinary_path.chmod(0o644)

            hardlink = root / "hardlink.bin"
            os.link(ordinary_path, hardlink)
            expect_rejection(
                lambda: checker.stable_read(root_fd, ordinary), "hard link"
            )
            rejected += 1
            hardlink.unlink()

            real = root / "real"
            real.mkdir()
            (real / "leaf").write_bytes(b"A")
            (real / "leaf").chmod(0o644)
            (root / "linked").symlink_to(real, target_is_directory=True)
            linked = checker.ExpectedAuthority(
                "linked/leaf", "linked", "100644", 0o644, "ordinary_2mib"
            )
            expect_rejection(
                lambda: checker.stable_read(root_fd, linked), "symlink ancestor"
            )
            rejected += 1
        finally:
            os.close(root_fd)
    return rejected


def descriptor_controls(checker) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-v11-input-fd-") as raw:
        root = Path(raw)
        path = root / "input.json"
        path.write_bytes(b"{}\n")
        path.chmod(0o600)
        descriptor = os.open(path, os.O_RDONLY)
        try:
            body, identity = checker.bounded_input_fd(descriptor, "fixture", 16)
            require(body == b"{}\n" and len(identity) == 2, "descriptor positive")
        finally:
            os.close(descriptor)

        path.chmod(0o644)
        descriptor = os.open(path, os.O_RDONLY)
        try:
            expect_rejection(
                lambda: checker.bounded_input_fd(descriptor, "wrong-mode", 16),
                "descriptor wrong mode",
            )
            rejected += 1
        finally:
            os.close(descriptor)
        path.chmod(0o600)

        descriptor = os.open(path, os.O_RDWR)
        try:
            expect_rejection(
                lambda: checker.bounded_input_fd(descriptor, "writable", 16),
                "descriptor writable",
            )
            rejected += 1
        finally:
            os.close(descriptor)

        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.lseek(descriptor, 1, os.SEEK_SET)
            expect_rejection(
                lambda: checker.bounded_input_fd(descriptor, "offset", 16),
                "descriptor offset",
            )
            rejected += 1
        finally:
            os.close(descriptor)
    return rejected


def semantic_controls(checker) -> int:
    rejected = 0
    diagnostic = load_json(ROOT / checker.DIAGNOSTIC_PATH)
    checker.validate_diagnostic(diagnostic)
    policy = load_json(ROOT / checker.POLICY_PATH)
    checker.validate_policy(policy)

    mutations = []
    first_size = copy.deepcopy(diagnostic)
    first_size["first_observed_rejection"]["authority_observed_bytes"] -= 1
    mutations.append((checker.validate_diagnostic, first_size, "first rejection size"))
    c10_tree = copy.deepcopy(diagnostic)
    c10_tree["diagnostic_boundary"]["c10_tree"] = "0" * 40
    mutations.append((checker.validate_diagnostic, c10_tree, "C10 tree"))
    promoted_latent = copy.deepcopy(diagnostic)
    promoted_latent["latent_not_reached_defects"][0]["worktree_mode"] = "0644"
    mutations.append((checker.validate_diagnostic, promoted_latent, "latent mode"))

    special_path = copy.deepcopy(policy)
    special_path["authority_contract"]["special_limits"][0]["path"] += ".nearby"
    mutations.append((checker.validate_policy, special_path, "special nearby path"))
    c10_parent = copy.deepcopy(policy)
    c10_parent["c11"]["parent"] = checker.C10_COMMIT
    mutations.append((checker.validate_policy, c10_parent, "C10 parent"))
    r15 = copy.deepcopy(policy)
    r15["r16_current_source"]["accepted_r15_reuse"] = True
    mutations.append((checker.validate_policy, r15, "R15 reuse"))
    retry_l11 = copy.deepcopy(policy)
    retry_l11["l11"]["attempt_semantics"] = "retry_until_success"
    mutations.append((checker.validate_policy, retry_l11, "L11 retry semantics"))
    atomic_claim = copy.deepcopy(policy)
    atomic_claim["authority_contract"]["concurrency_boundary"] = (
        "complete_probe_atomic_snapshot"
    )
    mutations.append((checker.validate_policy, atomic_claim, "false atomicity claim"))

    for validator, value, label in mutations:
        expect_rejection(
            lambda validator=validator, value=value: validator(value), label
        )
        rejected += 1

    active = (ROOT / checker.WORKFLOW).read_text(encoding="utf-8")
    retired = (ROOT / checker.RETIRED_V9_WORKFLOW).read_text(encoding="utf-8")
    checker.validate_workflows(active, retired)
    for hostile_active, hostile_retired, label in (
        (active + "\ncontinue-on-error: true\n", retired, "continue-on-error"),
        (active.replace("push:", "push_removed:", 1), retired, "missing push"),
        (
            active.replace("--workflow", "--candidate"),
            retired,
            "missing lifecycle auto-classification",
        ),
        (active, retired + "\npush:\n", "retired push"),
    ):
        expect_rejection(
            lambda hostile_active=hostile_active, hostile_retired=hostile_retired: (
                checker.validate_workflows(hostile_active, hostile_retired)
            ),
            label,
        )
        rejected += 1
    return rejected


def schema_controls(checker) -> int:
    rejected = 0
    schemas = {
        path: load_json(ROOT / path)
        for path in (
            checker.HOSTED_SCHEMA,
            checker.LOCAL_SCHEMA,
            checker.RECEIPT_SCHEMA,
        )
    }
    for path, value in schemas.items():
        checker.validate_schema(value, path)
    mutants = []
    hosted = copy.deepcopy(schemas[checker.HOSTED_SCHEMA])
    hosted["$defs"]["successorDocument"]["properties"]["phase"]["const"] = (
        "predecessor_failure"
    )
    mutants.append((checker.HOSTED_SCHEMA, hosted, "hosted phase"))
    local = copy.deepcopy(schemas[checker.LOCAL_SCHEMA])
    local["properties"]["authorities"]["maxItems"] -= 1
    mutants.append((checker.LOCAL_SCHEMA, local, "local authority count"))
    receipt = copy.deepcopy(schemas[checker.RECEIPT_SCHEMA])
    receipt["properties"]["qualification"]["properties"]["attempt"]["const"] = 2
    mutants.append((checker.RECEIPT_SCHEMA, receipt, "receipt attempt"))
    for path, value, label in mutants:
        expect_rejection(
            lambda path=path, value=value: checker.validate_schema(value, path), label
        )
        rejected += 1
    return rejected


def capture_row_controls(checker) -> int:
    body = b'{"ok":true}'

    def row(repetition: int) -> dict:
        return {
            "body_base64": base64.b64encode(body).decode("ascii"),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_size_bytes": len(body),
            "logical_request": "fixture_run",
            "media_type": "application/json",
            "page": 0,
            "path": f"/repos/{checker.REPOSITORY}/actions/runs/1",
            "redirect": None,
            "repetition": repetition,
            "response_kind": "json",
            "status_code": 200,
        }

    decoded = [
        checker.decode_capture_row(row(1), "fixture one"),
        checker.decode_capture_row(row(2), "fixture two"),
    ]
    require(
        len(checker.paired_capture_bodies(decoded, "fixture_run")) == 1,
        "paired capture positive control",
    )
    root = {"captures": [row(1), row(2)], "retry_events": []}
    checked, retries = checker.decode_capture_document(root, "fixture capture")
    require(len(checked) == 2 and retries == 0, "capture-document positive control")

    rejected = 0
    wrong_digest = row(1)
    wrong_digest["body_sha256"] = "0" * 64
    expect_rejection(
        lambda: checker.decode_capture_row(wrong_digest, "wrong digest"),
        "capture body digest",
    )
    rejected += 1
    duplicate_repetition = [
        checker.decode_capture_row(row(1), "duplicate one"),
        checker.decode_capture_row(row(1), "duplicate two"),
    ]
    expect_rejection(
        lambda: checker.paired_capture_bodies(duplicate_repetition, "fixture_run"),
        "capture repetition",
    )
    rejected += 1
    retry_without_success = copy.deepcopy(root)
    retry_without_success["retry_events"] = [
        {
            "attempt": 1,
            "category": "transport",
            "logical_request": "foreign_request",
            "page": 0,
            "path": f"/repos/{checker.REPOSITORY}/actions/runs/2",
            "repetition": 1,
            "response_sha256": hashlib.sha256(b"failure").hexdigest(),
            "response_size_bytes": 7,
        }
    ]
    expect_rejection(
        lambda: checker.decode_capture_document(retry_without_success, "foreign retry"),
        "retry without success row",
    )
    rejected += 1
    literal_duplicate = b"value = {'schema': 1, 'schema': 2}\n"
    expect_rejection(
        lambda: checker.validate_no_duplicate_literal_dict_keys(
            literal_duplicate, "duplicate-literal.py"
        ),
        "duplicate literal dict key",
    )
    rejected += 1
    hosted_fixture = {"a": [True, "µ"], "z": 1}
    require(
        checker.parse_hosted_canonical_json(
            checker.hosted_pretty_json(hosted_fixture),
            "hosted canonical fixture",
            1024,
        )
        == hosted_fixture,
        "hosted pretty-canonical positive control",
    )
    for raw, label in (
        (checker.compact_json(hosted_fixture), "hosted compact JSON form"),
        (checker.pretty_json(hosted_fixture), "hosted non-ASCII JSON form"),
    ):
        expect_rejection(
            lambda raw=raw: checker.parse_hosted_canonical_json(
                raw, "hosted canonical mutant", 1024
            ),
            label,
        )
        rejected += 1
    return rejected


def zip_resource_controls(checker) -> dict[str, int]:
    safe_stream = io.BytesIO()
    with zipfile.ZipFile(
        safe_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("safe.bin", b"S" * (checker.ZIP_MEMBER_READ_CHUNK + 17))
    read_sizes: list[int] = []
    original_member_read = checker.zipfile.ZipExtFile.read

    def bounded_read(member, size=-1):
        read_sizes.append(size)
        return original_member_read(member, size)

    checker.zipfile.ZipExtFile.read = bounded_read
    try:
        require(
            checker.validate_zip_payload(safe_stream.getvalue(), "safe fixture")
            == {"safe.bin": b"S" * (checker.ZIP_MEMBER_READ_CHUNK + 17)},
            "safe ZIP positive control",
        )
    finally:
        checker.zipfile.ZipExtFile.read = original_member_read
    require(
        read_sizes
        and max(read_sizes) <= checker.ZIP_MEMBER_READ_CHUNK
        and all(size >= 0 for size in read_sizes),
        "ZIP member read request escaped the 64 KiB bound",
    )

    oversized_stream = io.BytesIO()
    with zipfile.ZipFile(
        oversized_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("expansion.bin", b"A" * (checker.CAPTURE_BODY_LIMIT + 1))
    oversized = oversized_stream.getvalue()
    require(
        len(oversized) < checker.RECORD_LIMIT,
        "oversized-expansion ZIP input is not a compact hostile fixture",
    )
    original_open = checker.zipfile.ZipFile.open

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("ZIP payload was decompressed before aggregate preflight")

    checker.zipfile.ZipFile.open = forbidden_open
    try:
        expect_rejection(
            lambda: checker.validate_zip_payload(oversized, "oversized expansion"),
            "oversized ZIP expansion before decompression",
        )
    finally:
        checker.zipfile.ZipFile.open = original_open

    mismatch_stream = io.BytesIO()
    with zipfile.ZipFile(
        mismatch_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("mismatch.bin", b"M" * (checker.ZIP_MEMBER_READ_CHUNK * 2))
    mismatch = bytearray(mismatch_stream.getvalue())
    central_offset = mismatch.find(b"PK\x01\x02")
    require(central_offset >= 0, "mismatch ZIP lacks its central header")
    struct.pack_into("<I", mismatch, central_offset + 24, 1)
    mismatch_read_sizes: list[int] = []

    def mismatch_bounded_read(member, size=-1):
        mismatch_read_sizes.append(size)
        return original_member_read(member, size)

    checker.zipfile.ZipExtFile.read = mismatch_bounded_read
    try:
        expect_rejection(
            lambda: checker.validate_zip_payload(
                bytes(mismatch), "declared-size mismatch"
            ),
            "forged ZIP central-directory size",
        )
    finally:
        checker.zipfile.ZipExtFile.read = original_member_read
    require(
        mismatch_read_sizes
        and all(
            0 <= size <= checker.ZIP_MEMBER_READ_CHUNK for size in mismatch_read_sizes
        ),
        "forged ZIP triggered an oversized member read request",
    )
    return {
        "zip_aggregate_hostiles_rejected_before_member_open": 1,
        "zip_forged_size_hostiles_rejected_with_bounded_reads": 1,
        "zip_maximum_member_read_request_bytes": max(read_sizes + mismatch_read_sizes),
    }


def main() -> int:
    checker = load_checker()
    baseline = checker.offline_self_test()
    require(baseline["result"] == "pass", "checker offline baseline")
    duplicate = b'{"a":1,"a":2}'
    expect_rejection(
        lambda: checker.parse_json(duplicate, "duplicate fixture"), "duplicate JSON"
    )
    zip_results = zip_resource_controls(checker)
    result = {
        "checker_authority_mutants_rejected": baseline[
            "authority_class_mutants_rejected"
        ],
        "duplicate_json_mutants_rejected": 1,
        "descriptor_input_hostiles_rejected": descriptor_controls(checker),
        "filesystem_hostiles_rejected": filesystem_controls(checker),
        "capture_and_literal_hostiles_rejected": capture_row_controls(checker),
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-hostile-suite/v1",
        "schema_contract_mutants_rejected": schema_controls(checker),
        "semantic_and_workflow_mutants_rejected": semantic_controls(checker),
        **zip_results,
    }
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"composite-v11 self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
