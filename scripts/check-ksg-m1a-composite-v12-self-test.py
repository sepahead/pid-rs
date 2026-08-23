#!/usr/bin/env python3
"""Hostile controls for v12 semantics and checksum-bound v11 reuse."""

from __future__ import annotations

import sys


if not (
    sys.implementation.name == "cpython"
    and sys.version_info == (3, 14, 6, "final", 0)
    and sys._is_gil_enabled()
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-m1a-composite-v12-self-test.py requires "
        "GIL-enabled CPython 3.14.6 -I -S -B and at most one -O",
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
MODULE_PATHS = {
    "checker": ROOT / "scripts/check-ksg-m1a-composite-v12.py",
    "hosted": ROOT / "scripts/capture-ksg-m1a-composite-v12.py",
    "local": ROOT / "scripts/capture-ksg-m1a-composite-v12-local-closure.py",
}


class SelfTestError(RuntimeError):
    """A positive control failed or a hostile mutation survived."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def expect_rejection(operation, label: str) -> None:
    try:
        operation()
    except (OSError, RuntimeError, ValueError):
        return
    raise SelfTestError(f"hostile control passed: {label}")


def load_module(role: str, path: Path):
    name = f"pid_rs_composite_v12_self_test_{role}"
    specification = importlib.util.spec_from_file_location(name, path)
    require(
        specification is not None and specification.loader is not None,
        f"{role} module spec",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frozen_binding_controls(role: str, module) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix=f"pid-rs-v12-{role}-binding-") as raw:
        root = Path(raw)
        positive = root / "primitive.py"
        positive.write_bytes(module.V11_RAW)
        positive.chmod(0o644)
        require(
            module.read_bound_v11(positive) == module.V11_RAW,
            f"{role} frozen primitive positive control",
        )

        changed = root / "changed.py"
        changed.write_bytes(bytes([module.V11_RAW[0] ^ 1]) + module.V11_RAW[1:])
        changed.chmod(0o644)
        expect_rejection(
            lambda: module.read_bound_v11(changed), f"{role} changed digest"
        )
        rejected += 1

        short = root / "short.py"
        short.write_bytes(module.V11_RAW[:-1])
        short.chmod(0o644)
        expect_rejection(lambda: module.read_bound_v11(short), f"{role} short file")
        rejected += 1

        wrong_mode = root / "wrong-mode.py"
        wrong_mode.write_bytes(module.V11_RAW)
        wrong_mode.chmod(0o600)
        expect_rejection(
            lambda: module.read_bound_v11(wrong_mode), f"{role} wrong mode"
        )
        rejected += 1

        symlink = root / "symlink.py"
        symlink.symlink_to(positive.name)
        expect_rejection(
            lambda: module.read_bound_v11(symlink), f"{role} symlink primitive"
        )
        rejected += 1

        hardlink_source = root / "hardlink-source.py"
        hardlink_source.write_bytes(module.V11_RAW)
        hardlink_source.chmod(0o644)
        os.link(hardlink_source, root / "hardlink-peer.py")
        expect_rejection(
            lambda: module.read_bound_v11(hardlink_source),
            f"{role} hard-linked primitive",
        )
        rejected += 1
    require(rejected == 5, f"{role} frozen binding hostile count")
    return rejected


def write_fixture(root: Path, relative: str, raw: bytes, mode: int) -> Path:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    destination.chmod(mode)
    return destination


def filesystem_controls(v11) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-v12-checker-fs-") as raw:
        root = Path(raw).resolve(strict=True)
        expected = v11.ExpectedAuthority(
            "ordinary.bin", "ordinary", "100644", 0o644, "ordinary_2mib"
        )
        path = write_fixture(root, expected.path, b"A", 0o644)
        root_fd = os.open(root, v11.directory_flags())
        try:
            require(v11.stable_read(root_fd, expected) == b"A", "stable-read positive")
            path.write_bytes(b"A" * (v11.ORDINARY_LIMIT + 1))
            path.chmod(0o644)
            expect_rejection(
                lambda: v11.stable_read(root_fd, expected), "ordinary max plus one"
            )
            rejected += 1

            path.write_bytes(b"A")
            path.chmod(0o600)
            expect_rejection(lambda: v11.stable_read(root_fd, expected), "wrong mode")
            rejected += 1
            path.chmod(0o644)

            target = root / "target.bin"
            target.write_bytes(b"A")
            target.chmod(0o644)
            path.unlink()
            path.symlink_to(target.name)
            expect_rejection(lambda: v11.stable_read(root_fd, expected), "symlink leaf")
            rejected += 1
            path.unlink()
            path.write_bytes(b"A")
            path.chmod(0o644)

            peer = root / "peer.bin"
            os.link(path, peer)
            expect_rejection(lambda: v11.stable_read(root_fd, expected), "hard link")
            rejected += 1
            peer.unlink()

            real = root / "real"
            real.mkdir()
            (real / "leaf").write_bytes(b"A")
            (real / "leaf").chmod(0o644)
            (root / "linked").symlink_to(real, target_is_directory=True)
            linked = v11.ExpectedAuthority(
                "linked/leaf", "linked", "100644", 0o644, "ordinary_2mib"
            )
            expect_rejection(
                lambda: v11.stable_read(root_fd, linked), "symlink ancestor"
            )
            rejected += 1
        finally:
            os.close(root_fd)
    require(rejected == 5, "filesystem hostile count")
    return rejected


def descriptor_controls(v11) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-v12-input-fd-") as raw:
        path = Path(raw) / "input.json"
        path.write_bytes(b"{}\n")
        path.chmod(0o600)
        descriptor = os.open(path, os.O_RDONLY)
        try:
            body, identity = v11.bounded_input_fd(descriptor, "fixture", 16)
            require(body == b"{}\n" and len(identity) == 2, "descriptor positive")
        finally:
            os.close(descriptor)

        path.chmod(0o644)
        descriptor = os.open(path, os.O_RDONLY)
        try:
            expect_rejection(
                lambda: v11.bounded_input_fd(descriptor, "wrong-mode", 16),
                "descriptor wrong mode",
            )
            rejected += 1
        finally:
            os.close(descriptor)
        path.chmod(0o600)

        descriptor = os.open(path, os.O_RDWR)
        try:
            expect_rejection(
                lambda: v11.bounded_input_fd(descriptor, "writable", 16),
                "descriptor writable",
            )
            rejected += 1
        finally:
            os.close(descriptor)

        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.lseek(descriptor, 1, os.SEEK_SET)
            expect_rejection(
                lambda: v11.bounded_input_fd(descriptor, "offset", 16),
                "descriptor nonzero offset",
            )
            rejected += 1
        finally:
            os.close(descriptor)
    require(rejected == 3, "descriptor hostile count")
    return rejected


def failure_fixture(checker) -> dict:
    return {
        "credit": {
            "c12_qualification": "none",
            "l11": "consumed_failed",
            "q11": False,
            "r11": "permanently_unissued",
        },
        "diagnosis": {
            "complete": True,
            "surfaces": copy.deepcopy(checker.EXPECTED_FAILURE_SURFACES),
        },
        "first_observed_failure": {
            "command": ["just", "ksg-composite-v11"],
            "error": "certified SxPID2 claim check failed: release-audit just dependency line exact digest changed",
            "exit_code": 1,
            "phase": "local_L11_command",
            "production_launch_consumed": True,
            "record_emitted": False,
        },
        "nonimplications": checker.FAILURE_NONIMPLICATIONS,
        "repository": checker.REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-local-closure-failure/v12",
        "schema_revision": 12,
        "subject": {
            "c11_commit": checker.C11_COMMIT,
            "c11_message": checker.C11_MESSAGE,
            "c11_parent": checker.C9_COMMIT,
            "c11_tree": checker.C11_TREE,
        },
    }


def semantic_controls(checker) -> int:
    rejected = 0
    diagnostic = failure_fixture(checker)
    checker.validate_failure_diagnostic(diagnostic)
    policy = load_json(ROOT / checker.POLICY_PATH)
    checker.validate_policy(policy)

    mutations = []
    wrong_surface = copy.deepcopy(diagnostic)
    wrong_surface["diagnosis"]["surfaces"][0]["observed_sha256"] = "0" * 64
    mutations.append(
        (checker.validate_failure_diagnostic, wrong_surface, "failure digest")
    )
    replay = copy.deepcopy(diagnostic)
    replay["first_observed_failure"]["production_launch_consumed"] = False
    mutations.append((checker.validate_failure_diagnostic, replay, "unconsumed L11"))
    q11 = copy.deepcopy(diagnostic)
    q11["credit"]["q11"] = True
    mutations.append((checker.validate_failure_diagnostic, q11, "Q11 promoted"))
    missing_limit = copy.deepcopy(policy)
    missing_limit["authority_contract"]["aggregate_limit_bytes"] -= 1
    mutations.append((checker.validate_policy, missing_limit, "aggregate bound"))
    c12_parent = copy.deepcopy(policy)
    c12_parent["c12"]["parent"] = checker.C9_COMMIT
    mutations.append((checker.validate_policy, c12_parent, "C12 parent"))
    l12_run = copy.deepcopy(policy)
    l12_run["l12"]["status"] = "passed"
    mutations.append((checker.validate_policy, l12_run, "premature L12"))
    source_slot = copy.deepcopy(policy)
    source_slot["current_source_generation"]["generation_slot"] = 12
    mutations.append(
        (checker.validate_policy, source_slot, "current-source generation slot")
    )
    source_namespace = copy.deepcopy(policy)
    source_namespace["current_source_generation"]["namespace"] = "composite_r12_receipt"
    mutations.append(
        (checker.validate_policy, source_namespace, "current-source namespace")
    )
    source_status = copy.deepcopy(policy)
    source_status["current_source_generation"]["status"] = "not_generated"
    mutations.append(
        (checker.validate_policy, source_status, "current-source generation status")
    )
    retry = copy.deepcopy(policy)
    retry["qualification"]["attempt"] = 2
    mutations.append((checker.validate_policy, retry, "qualification retry"))
    special = copy.deepcopy(policy)
    special["authority_contract"]["special_limits"] = [{"path": "nearby"}]
    mutations.append((checker.validate_policy, special, "special limit"))
    atomic = copy.deepcopy(policy)
    atomic["authority_contract"]["concurrency_boundary"] = "atomic_snapshot"
    mutations.append((checker.validate_policy, atomic, "false atomicity"))

    for validator, value, label in mutations:
        expect_rejection(lambda v=value, f=validator: f(v), label)
        rejected += 1

    active = (ROOT / checker.WORKFLOW).read_text(encoding="utf-8")
    retired = (ROOT / checker.RETIRED_V11_WORKFLOW).read_text(encoding="utf-8")
    just = (ROOT / "justfile").read_text(encoding="utf-8")
    checker.validate_workflows_and_wiring(active, retired, just)
    workflow_mutants = (
        (active + "\ncontinue-on-error: true\n", retired, just, "continue on error"),
        (active.replace("push:", "push_removed:", 1), retired, just, "missing push"),
        (
            active.replace("--workflow", "--candidate"),
            retired,
            just,
            "missing workflow mode",
        ),
        (active, retired + "\npush:\n", just, "retired push"),
        (active, retired.replace("exit 1", "exit 0"), just, "retired success"),
        (
            active,
            retired,
            just.replace(
                "C11 L11 attempt is permanently consumed; refusing replay",
                "C11 replay enabled",
            ),
            "v11 Just replay",
        ),
        (
            active,
            retired,
            just.replace(
                "ksg-composite-v12 certified-sxpid", "ksg-composite-v11 certified-sxpid"
            ),
            "release uses v11",
        ),
    )
    for active_value, retired_value, just_value, label in workflow_mutants:
        expect_rejection(
            lambda a=active_value, r=retired_value, j=just_value: (
                checker.validate_workflows_and_wiring(a, r, j)
            ),
            label,
        )
        rejected += 1
    require(rejected == 19, "semantic/workflow hostile count")
    return rejected


def schema_controls(checker) -> int:
    schemas = {
        path: load_json(ROOT / path)
        for path in (
            checker.FAILURE_SCHEMA,
            checker.HOSTED_SCHEMA,
            checker.LOCAL_SCHEMA,
            checker.RECEIPT_SCHEMA,
        )
    }
    for path, value in schemas.items():
        checker.validate_schema(value, path)
    mutants = []
    failure = copy.deepcopy(schemas[checker.FAILURE_SCHEMA])
    failure["properties"]["schema_revision"]["const"] = 11
    mutants.append((checker.FAILURE_SCHEMA, failure, "failure revision"))
    hosted = copy.deepcopy(schemas[checker.HOSTED_SCHEMA])
    hosted["$ref"] = "#/$defs/predecessorDocument"
    mutants.append((checker.HOSTED_SCHEMA, hosted, "hosted predecessor branch"))
    local = copy.deepcopy(schemas[checker.LOCAL_SCHEMA])
    local["properties"]["authorities"]["maxItems"] -= 1
    mutants.append((checker.LOCAL_SCHEMA, local, "local authority count"))
    receipt = copy.deepcopy(schemas[checker.RECEIPT_SCHEMA])
    receipt["properties"]["qualification"]["properties"]["attempt"]["const"] = 2
    mutants.append((checker.RECEIPT_SCHEMA, receipt, "receipt attempt"))
    for path, value, label in mutants:
        expect_rejection(lambda p=path, v=value: checker.validate_schema(v, p), label)
    return len(mutants)


def static_digest_controls(checker) -> int:
    rejected = 0
    for path in sorted(checker.STATIC_SOURCE_SHA256):
        raw = (ROOT / path).read_bytes()
        checker.validate_static_source_digest(path, raw)
        expect_rejection(
            lambda p=path, r=raw: checker.validate_static_source_digest(p, r + b"\n"),
            f"static source digest {path}",
        )
        rejected += 1
    require(rejected == 11, "static source digest hostile count")
    return rejected


def lean_r14_split_controls(checker) -> int:
    receipt_raw = (ROOT / checker.LEAN_R14_RECEIPT).read_bytes()
    checker_raw = (ROOT / checker.LEAN_CHECKER).read_bytes()
    self_test_raw = (ROOT / checker.LEAN_SELF_TEST).read_bytes()
    checker.validate_lean_r14_history(receipt_raw, checker_raw, self_test_raw)
    receipt = json.loads(receipt_raw)

    def pretty(value: dict) -> bytes:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")

    mutants: list[tuple[bytes, bytes, bytes, str]] = []
    missing = copy.deepcopy(receipt)
    missing["operational_wiring_sha256"].pop(".github/workflows/ci.yml")
    mutants.append((pretty(missing), checker_raw, self_test_raw, "r14 path removal"))
    changed = copy.deepcopy(receipt)
    changed["operational_wiring_sha256"][".github/workflows/ci.yml"] = "0" * 64
    mutants.append((pretty(changed), checker_raw, self_test_raw, "r14 C9 digest"))
    final_custody = copy.deepcopy(receipt)
    final_custody["custody_gate_sha256"][checker.LEAN_CHECKER] = "0" * 64
    mutants.append(
        (pretty(final_custody), checker_raw, self_test_raw, "r14 final custody")
    )
    replay_custody = copy.deepcopy(receipt)
    replay_custody["replay_custody_gate_sha256"][checker.LEAN_CHECKER] = "0" * 64
    mutants.append(
        (pretty(replay_custody), checker_raw, self_test_raw, "r14 replay custody")
    )
    c9_checker = checker.V11.tree_blob(
        checker.C9_COMMIT,
        checker.LEAN_CHECKER,
        checker.LEAN_R14_HISTORY_FILE_LIMIT,
    )
    c9_self_test = checker.V11.tree_blob(
        checker.C9_COMMIT,
        checker.LEAN_SELF_TEST,
        checker.LEAN_R14_HISTORY_FILE_LIMIT,
    )
    mutants.append((receipt_raw, c9_checker, self_test_raw, "current checker rewind"))
    mutants.append((receipt_raw, checker_raw, c9_self_test, "current self-test rewind"))
    mutants.append((receipt_raw + b" ", checker_raw, self_test_raw, "r14 framing"))
    for mutant_receipt, mutant_checker, mutant_self_test, label in mutants:
        expect_rejection(
            lambda r=mutant_receipt, c=mutant_checker, s=mutant_self_test: (
                checker.validate_lean_r14_history(r, c, s)
            ),
            label,
        )
    require(len(mutants) == 7, "Lean r14/current-C12 split hostile count")
    return len(mutants)


def capture_and_canonical_controls(v11) -> int:
    body = b'{"ok":true}'

    def row(repetition: int) -> dict:
        return {
            "body_base64": base64.b64encode(body).decode("ascii"),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_size_bytes": len(body),
            "logical_request": "fixture_run",
            "media_type": "application/json",
            "page": 0,
            "path": f"/repos/{v11.REPOSITORY}/actions/runs/1",
            "redirect": None,
            "repetition": repetition,
            "response_kind": "json",
            "status_code": 200,
        }

    decoded = [
        v11.decode_capture_row(row(1), "fixture one"),
        v11.decode_capture_row(row(2), "fixture two"),
    ]
    require(
        len(v11.paired_capture_bodies(decoded, "fixture_run")) == 1,
        "paired capture positive",
    )
    rejected = 0
    wrong_digest = row(1)
    wrong_digest["body_sha256"] = "0" * 64
    expect_rejection(
        lambda: v11.decode_capture_row(wrong_digest, "wrong digest"),
        "capture digest",
    )
    rejected += 1
    duplicate = [
        v11.decode_capture_row(row(1), "duplicate one"),
        v11.decode_capture_row(row(1), "duplicate two"),
    ]
    expect_rejection(
        lambda: v11.paired_capture_bodies(duplicate, "fixture_run"),
        "capture repetition",
    )
    rejected += 1
    expect_rejection(
        lambda: v11.validate_no_duplicate_literal_dict_keys(
            b"value = {'schema': 1, 'schema': 2}\n", "duplicate.py"
        ),
        "duplicate literal key",
    )
    rejected += 1
    fixture = {"a": [True, "µ"], "z": 1}
    require(
        v11.parse_hosted_canonical_json(
            v11.hosted_pretty_json(fixture), "hosted canonical", 1024
        )
        == fixture,
        "hosted canonical positive",
    )
    for raw, label in (
        (v11.compact_json(fixture), "compact hosted JSON"),
        (v11.pretty_json(fixture), "non-ASCII hosted JSON"),
    ):
        expect_rejection(
            lambda r=raw: v11.parse_hosted_canonical_json(r, label, 1024), label
        )
        rejected += 1
    require(rejected == 5, "capture/canonical hostile count")
    return rejected


def zip_resource_controls(v11) -> dict[str, int]:
    safe_stream = io.BytesIO()
    with zipfile.ZipFile(
        safe_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("safe.bin", b"S" * (v11.ZIP_MEMBER_READ_CHUNK + 17))
    read_sizes: list[int] = []
    original_read = v11.zipfile.ZipExtFile.read

    def bounded_read(member, size=-1):
        read_sizes.append(size)
        return original_read(member, size)

    v11.zipfile.ZipExtFile.read = bounded_read
    try:
        require(
            v11.validate_zip_payload(safe_stream.getvalue(), "safe fixture")
            == {"safe.bin": b"S" * (v11.ZIP_MEMBER_READ_CHUNK + 17)},
            "safe ZIP positive",
        )
    finally:
        v11.zipfile.ZipExtFile.read = original_read
    require(
        read_sizes
        and all(0 <= size <= v11.ZIP_MEMBER_READ_CHUNK for size in read_sizes),
        "ZIP read bound",
    )

    oversized_stream = io.BytesIO()
    with zipfile.ZipFile(
        oversized_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("expansion.bin", b"A" * (v11.CAPTURE_BODY_LIMIT + 1))
    original_open = v11.zipfile.ZipFile.open

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("ZIP decompressed before aggregate preflight")

    v11.zipfile.ZipFile.open = forbidden_open
    try:
        expect_rejection(
            lambda: v11.validate_zip_payload(
                oversized_stream.getvalue(), "oversized expansion"
            ),
            "oversized ZIP expansion",
        )
    finally:
        v11.zipfile.ZipFile.open = original_open

    mismatch_stream = io.BytesIO()
    with zipfile.ZipFile(
        mismatch_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as archive:
        archive.writestr("mismatch.bin", b"M" * (v11.ZIP_MEMBER_READ_CHUNK * 2))
    mismatch = bytearray(mismatch_stream.getvalue())
    central_offset = mismatch.find(b"PK\x01\x02")
    require(central_offset >= 0, "mismatch ZIP central header")
    struct.pack_into("<I", mismatch, central_offset + 24, 1)
    mismatch_sizes: list[int] = []

    def mismatch_read(member, size=-1):
        mismatch_sizes.append(size)
        return original_read(member, size)

    v11.zipfile.ZipExtFile.read = mismatch_read
    try:
        expect_rejection(
            lambda: v11.validate_zip_payload(bytes(mismatch), "size mismatch"),
            "forged ZIP size",
        )
    finally:
        v11.zipfile.ZipExtFile.read = original_read
    require(
        mismatch_sizes
        and all(0 <= size <= v11.ZIP_MEMBER_READ_CHUNK for size in mismatch_sizes),
        "forged ZIP read bound",
    )
    return {
        "zip_aggregate_hostiles_rejected_before_member_open": 1,
        "zip_forged_size_hostiles_rejected_with_bounded_reads": 1,
        "zip_maximum_member_read_request_bytes": max(read_sizes + mismatch_sizes),
    }


def main() -> int:
    modules = {role: load_module(role, path) for role, path in MODULE_PATHS.items()}
    checker = modules["checker"]
    baseline = checker.offline_self_test()
    require(baseline["result"] == "pass", "checker offline baseline")
    for role in ("hosted", "local"):
        require(
            modules[role].offline_self_test()["result"] == "pass",
            f"{role} wrapper offline baseline",
        )
    binding_rejections = {
        role: frozen_binding_controls(role, module) for role, module in modules.items()
    }
    v11 = checker.V11
    inherited = v11.offline_self_test()
    require(
        inherited["result"] == "pass"
        and inherited["complete_probe_endpoint_hostiles_rejected"] == 3,
        "frozen outer-bracket controls changed",
    )
    duplicate_json = b'{"a":1,"a":2}'
    expect_rejection(
        lambda: v11.parse_json(duplicate_json, "duplicate"), "duplicate JSON"
    )
    zip_results = zip_resource_controls(v11)
    result = {
        "capture_and_canonical_hostiles_rejected": capture_and_canonical_controls(v11),
        "descriptor_input_hostiles_rejected": descriptor_controls(v11),
        "duplicate_json_mutants_rejected": 1,
        "filesystem_hostiles_rejected": filesystem_controls(v11),
        "frozen_binding_hostiles_rejected": binding_rejections,
        "frozen_v11_outer_bracket_hostiles_rejected": inherited[
            "complete_probe_endpoint_hostiles_rejected"
        ],
        "lifecycle_projection_hostiles_rejected": baseline[
            "lifecycle_projection_hostiles_rejected"
        ],
        "lean_r14_current_c12_split_hostiles_rejected": lean_r14_split_controls(
            checker
        ),
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-hostile-suite/v1",
        "schema_contract_mutants_rejected": schema_controls(checker),
        "semantic_and_workflow_mutants_rejected": semantic_controls(checker),
        "static_source_digest_mutants_rejected": static_digest_controls(checker),
        **zip_results,
    }
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"composite-v12 self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
