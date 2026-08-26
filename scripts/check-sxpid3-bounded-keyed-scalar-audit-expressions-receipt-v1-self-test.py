#!/usr/bin/env python3
"""Fail-closed mutation suite for the SxPID3 audit-expression receipt validator."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import py_compile
import shlex
import stat
import subprocess
import sys
import tempfile
import types
from typing import Any


if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.no_site == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: checker self-test requires CPython 3.11+ with -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / "check-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.py"
)
SCHEMA_PATH = (
    ROOT
    / "audit"
    / "schemas"
    / "sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.schema.json"
)


class SelfTestError(RuntimeError):
    """A positive or hostile control failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def load_checker() -> Any:
    before = CHECKER_PATH.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not CHECKER_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o755
        and 0 < before.st_size <= 4 * 1024 * 1024,
        "checker source metadata rejected",
    )
    descriptor = os.open(
        CHECKER_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    )
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", "checker source short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "checker source grew during read")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = CHECKER_PATH.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "checker source changed during read",
        )
    raw = b"".join(chunks)
    name = "pid_rs_sxpid3_audit_expression_receipt_checker_v1"
    module = types.ModuleType(name)
    module.__file__ = os.fspath(CHECKER_PATH)
    module.__package__ = ""
    sys.modules[name] = module
    exec(
        compile(
            raw,
            os.fspath(CHECKER_PATH),
            "exec",
            flags=0,
            dont_inherit=True,
            optimize=sys.flags.optimize,
        ),
        module.__dict__,
    )
    return module


def expect_rejected(
    function: Any,
    label: str,
    expected: type[BaseException] | tuple[type[BaseException], ...],
) -> BaseException:
    try:
        function()
    except expected as error:
        return error
    except BaseException as error:
        raise SelfTestError(
            f"mutation raised the wrong exception for {label}: {type(error).__name__}"
        ) from error
    raise SelfTestError(f"mutation escaped: {label}")


def source_fixture(checker: Any) -> dict[str, Any]:
    delta: list[dict[str, Any]] = []
    for index, relative in enumerate(sorted(checker.SOURCE_DELTA), start=1):
        status, mode = checker.SOURCE_DELTA[relative]
        delta.append(
            {
                "path": relative,
                "status": status,
                "base_mode": None if status == "A" else mode,
                "source_mode": mode,
                "source_blob_oid": f"{index:040x}",
                "source_sha256": f"{index:064x}",
                "source_bytes": 100 + index,
            }
        )
    return {
        "source_commit": "f" * 40,
        "source_tree": "e" * 40,
        "sole_parent": checker.BASE_COMMIT,
        "base_tree": checker.BASE_TREE,
        "direct_child_of_required_base": True,
        "source_delta": delta,
        "receipt_path": checker.RECEIPT_RELATIVE,
        "receipt_absent_from_source_commit": True,
    }


def input_fixture(checker: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, relative in enumerate(sorted(checker.INPUT_ROLES), start=20):
        mode = "100755" if relative.endswith(".py") else "100644"
        result.append(
            {
                "path": relative,
                "role": checker.INPUT_ROLES[relative],
                "source_blob_oid": f"{index:040x}",
                "git_mode": mode,
                "live_mode": "0755" if mode == "100755" else "0644",
                "byte_count": 200 + index,
                "sha256": f"{index:064x}",
                "source_blob_matches_live_file": True,
            }
        )
    return result


def p1_fixture(checker: Any) -> dict[str, Any]:
    paths: list[dict[str, Any]] = []
    for index, relative in enumerate(checker.P1_PATHS, start=40):
        paths.append(
            {
                "path": relative,
                "baseline_blob_oid": f"{index:040x}",
                "source_blob_oid": f"{index:040x}",
                "git_mode": "100644",
                "byte_count": 300 + index,
                "sha256": f"{index:064x}",
                "unchanged_at_source": True,
            }
        )
    return {
        "baseline_commit": checker.P1_COMMIT,
        "baseline_tree": checker.P1_TREE,
        "adjacent_child_commit": checker.BASE_COMMIT,
        "adjacent_child_has_p1_as_sole_parent": True,
        "baseline_is_ancestor_of_source": True,
        "path_count": 10,
        "paths": paths,
        "consumed": False,
        "replayed": False,
        "fresh_execution_credit": "none",
        "semantic_transfer": "none",
        "relationship": "adjacent_separate_lane_provenance_only",
    }


def command_fixture(checker: Any, inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    input_by_path = {entry["path"]: entry for entry in inputs}
    result: list[dict[str, Any]] = []
    for base_id, relative, stdout_sha256, stdout_format, stdout_bytes in checker.COMMAND_ROSTER:
        for mode in ("normal", "optimized"):
            argv = ["$PYTHON"]
            if mode == "optimized":
                argv.append("-O")
            argv.extend(["-I", "-S", "-B", f"$REPOSITORY/{relative}"])
            result.append(
                {
                    "id": f"{base_id}_{mode}",
                    "entrypoint": relative,
                    "mode": mode,
                    "argv": argv,
                    "timeout_seconds": 7_200,
                    "stdout_cap_bytes": 4 * 1024 * 1024,
                    "stderr_cap_bytes": 1024 * 1024,
                    "exit_status": 0,
                    "timed_out": False,
                    "stdout_bytes": stdout_bytes,
                    "stdout_sha256": stdout_sha256,
                    "stdout_format": stdout_format,
                    "stderr_bytes": 0,
                    "stderr_sha256": checker.EMPTY_SHA256,
                    "entrypoint_source_sha256": input_by_path[relative]["sha256"],
                }
            )
    return result


def receipt_fixture(
    checker: Any,
    source: dict[str, Any],
    inputs: list[dict[str, Any]],
    adjacent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "pid-rs/sxpid3-bounded-keyed-scalar-audit-expressions-receipt/v1",
        "schema_revision": 1,
        "result_id": checker.RESULT_ID,
        "captured_at_utc": "2026-08-26T12:00:00Z",
        "source_package": source,
        "execution_inputs": inputs,
        "commands": command_fixture(checker, inputs),
        "findings": checker.expected_findings(),
        "p1_adjacent_lane": adjacent,
        "validation": checker.EXPECTED_VALIDATION,
        "nonclaims": checker.NONCLAIMS,
        "host_boundary": {
            "python": {
                "public_name": "$PYTHON",
                "version": "CPython 3.14.6",
                "executable_sha256": "b" * 64,
                "executable_bytes": 1,
            },
            "git": {
                "public_name": "$GIT",
                "version": "git version 2.51.0",
                "executable_sha256": "c" * 64,
                "executable_bytes": 1,
            },
            "required_python_flags": ["-I", "-S", "-B"],
            "python_optimize": 0,
            "observation_class": "bounded_local_execution_environment_observation_not_attestation",
        },
    }


def mutate_and_reject(
    checker: Any,
    baseline: dict[str, Any],
    schema: dict[str, Any],
    source: dict[str, Any],
    inputs: list[dict[str, Any]],
    adjacent: dict[str, Any],
    mutation: Any,
    label: str,
) -> None:
    candidate = copy.deepcopy(baseline)
    mutation(candidate)
    expect_rejected(
        lambda: checker.validate_receipt_document(
            candidate,
            schema,
            source,
            inputs,
            adjacent,
        ),
        label,
        checker.CheckError,
    )


def main() -> int:
    checker = load_checker()
    loader_controls = 0
    capture_source = checker.bootstrap_read_source(
        checker.CAPTURE_SUPPORT_PATH, 0o755
    )
    require(
        checker.sha256_bytes(capture_source) == checker.CAPTURE_SUPPORT_SHA256,
        "checker bootstrap generator pin drifted",
    )
    loader_controls += 1
    with tempfile.TemporaryDirectory(prefix="pid-rs-p5-source-loader-") as raw:
        directory = Path(raw)
        marker = directory / "executed-marker"
        hostile = directory / "hostile.py"
        hostile.write_text(
            f"open({os.fspath(marker)!r}, 'wb').write(b'executed')\n",
            encoding="utf-8",
        )
        hostile.chmod(0o755)
        expect_rejected(
            lambda: checker.load_source_module(
                hostile,
                "pid_rs_p5_hostile_generator_must_not_execute",
                0o755,
                "0" * 64,
            ),
            "modified-generator-before-exec",
            RuntimeError,
        )
        require(not marker.exists(), "modified generator executed before hash rejection")
        loader_controls += 1
        hostile_symlink = directory / "hostile-symlink.py"
        hostile_symlink.symlink_to(hostile.name)
        expect_rejected(
            lambda: checker.bootstrap_read_source(hostile_symlink, 0o755),
            "bootstrap-source-symlink",
            RuntimeError,
        )
        loader_controls += 1
        hostile_peer = directory / "hostile-hardlink.py"
        os.link(hostile, hostile_peer)
        expect_rejected(
            lambda: checker.bootstrap_read_source(hostile, 0o755),
            "bootstrap-source-hardlink",
            RuntimeError,
        )
        loader_controls += 1
        hostile_peer.unlink()

        pyc_marker = directory / "pyc-executed-marker"
        probe = directory / "probe.py"
        hostile_probe = (
            f"VALUE='hostile'\nopen({os.fspath(pyc_marker)!r},'wb').write(b'pyc')\n"
        ).encode("utf-8")
        benign_prefix = b"VALUE='source'\n"
        require(
            len(hostile_probe) > len(benign_prefix) + 1,
            "pyc fixture source lengths are invalid",
        )
        benign_probe = (
            benign_prefix
            + b"#" * (len(hostile_probe) - len(benign_prefix) - 1)
            + b"\n"
        )
        probe.write_bytes(hostile_probe)
        probe.chmod(0o755)
        original_probe_metadata = probe.stat()
        cache = (
            directory
            / "__pycache__"
            / f"probe.{sys.implementation.cache_tag}.pyc"
        )
        cache.parent.mkdir()
        py_compile.compile(
            os.fspath(probe), cfile=os.fspath(cache), doraise=True
        )
        probe.write_bytes(benign_probe)
        probe.chmod(0o755)
        os.utime(
            probe,
            ns=(
                original_probe_metadata.st_atime_ns,
                original_probe_metadata.st_mtime_ns,
            ),
        )
        pyc_probe = subprocess.run(
            [
                os.fspath(Path(sys.executable).resolve()),
                "-S",
                "-B",
                "-c",
                f"import sys;sys.path.insert(0,{os.fspath(directory)!r});import probe",
            ],
            cwd=directory,
            env={
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.environ.get("PATH", ""),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        require(
            pyc_probe.returncode == 0
            and pyc_probe.stdout == b""
            and pyc_probe.stderr == b""
            and pyc_marker.read_bytes() == b"pyc",
            "crafted hostile pyc was not a valid import candidate",
        )
        pyc_marker.unlink()
        loaded_probe = checker.load_source_module(
            probe,
            "pid_rs_p5_source_loader_ignores_pyc",
            0o755,
            checker.sha256_bytes(benign_probe),
        )
        require(
            loaded_probe.VALUE == "source" and not pyc_marker.exists(),
            "exact-source loader consumed hostile cached bytecode",
        )
        loader_controls += 1
    schema = checker.strict_json(SCHEMA_PATH.read_bytes(), "self-test schema")
    checker.validate_schema_definition(schema)
    source = source_fixture(checker)
    inputs = input_fixture(checker)
    adjacent = p1_fixture(checker)
    baseline = receipt_fixture(checker, source, inputs, adjacent)
    checker.validate_receipt_document(baseline, schema, source, inputs, adjacent)

    mutation_controls = 0
    mutations: list[tuple[str, Any]] = [
        ("receipt-additional-property", lambda value: value.__setitem__("extra", True)),
        (
            "impossible-calendar-time",
            lambda value: value.__setitem__(
                "captured_at_utc", "2026-99-99T99:99:99Z"
            ),
        ),
        (
            "source-parent-relation",
            lambda value: value["source_package"].__setitem__("sole_parent", "0" * 40),
        ),
        (
            "source-tree-binding",
            lambda value: value["source_package"].__setitem__("source_tree", "0" * 40),
        ),
        (
            "source-Git-mode-binding",
            lambda value: value["source_package"]["source_delta"][0].__setitem__(
                "source_mode", "100644"
                if value["source_package"]["source_delta"][0]["source_mode"]
                == "100755"
                else "100755",
            ),
        ),
        (
            "integer-rejects-boolean",
            lambda value: value["source_package"]["source_delta"][0].__setitem__(
                "source_bytes", True
            ),
        ),
        (
            "integer-rejects-equal-float-token",
            lambda value: value.__setitem__("schema_revision", 1.0),
        ),
        (
            "programmatic-nonfinite-instance",
            lambda value: value["source_package"]["source_delta"][0].__setitem__(
                "source_bytes", float("nan")
            ),
        ),
        (
            "missing-required-root-field",
            lambda value: value.pop("host_boundary"),
        ),
        (
            "input-duplicate",
            lambda value: value["execution_inputs"].__setitem__(
                1, copy.deepcopy(value["execution_inputs"][0])
            ),
        ),
        (
            "input-missing",
            lambda value: value["execution_inputs"].pop(),
        ),
        (
            "input-reordered",
            lambda value: value["execution_inputs"].__setitem__(
                slice(0, 2),
                [value["execution_inputs"][1], value["execution_inputs"][0]],
            ),
        ),
        (
            "input-path-escape",
            lambda value: value["execution_inputs"][0].__setitem__(
                "path", "../outside"
            ),
        ),
        (
            "input-live-mode-binding",
            lambda value: value["execution_inputs"][0].__setitem__(
                "live_mode",
                "0644"
                if value["execution_inputs"][0]["live_mode"] == "0755"
                else "0755",
            ),
        ),
        (
            "command-stdout-pin",
            lambda value: value["commands"][0].__setitem__("stdout_sha256", "0" * 64),
        ),
        (
            "command-entrypoint",
            lambda value: value["commands"][0].__setitem__("entrypoint", value["commands"][2]["entrypoint"]),
        ),
        (
            "command-duplicate",
            lambda value: value["commands"].__setitem__(
                1, copy.deepcopy(value["commands"][0])
            ),
        ),
        ("command-missing", lambda value: value["commands"].pop()),
        (
            "command-reordered",
            lambda value: value["commands"].__setitem__(
                slice(0, 2), [value["commands"][1], value["commands"][0]]
            ),
        ),
        (
            "entrypoint-source-binding",
            lambda value: value["commands"][0].__setitem__("entrypoint_source_sha256", "0" * 64),
        ),
        (
            "P1-consumed-flag",
            lambda value: value["p1_adjacent_lane"].__setitem__("consumed", True),
        ),
        (
            "P1-path-blob",
            lambda value: value["p1_adjacent_lane"]["paths"][0].__setitem__("source_blob_oid", "0" * 40),
        ),
        (
            "sign-census",
            lambda value: value["findings"]["sign_census"]["atom.net"].__setitem__("negative", 31_283),
        ),
        (
            "route-boundary",
            lambda value: value["findings"]["lexical_rust_route"]["boundaries"].pop(),
        ),
        (
            "Rust-numeric-comparison-count",
            lambda value: value["findings"]["lexical_rust_route"].__setitem__("numeric_rust_expressions_compared", 1),
        ),
        (
            "neutral-v2-digest",
            lambda value: value["findings"]["digests"].__setitem__("route_neutral_v2_expression_stream_sha256", "0" * 64),
        ),
        (
            "validation-boolean",
            lambda value: value["validation"].__setitem__("all_stderr_empty", False),
        ),
        ("nonclaim-removal", lambda value: value["nonclaims"].pop()),
    ]
    for label, mutation in mutations:
        mutate_and_reject(
            checker,
            baseline,
            schema,
            source,
            inputs,
            adjacent,
            mutation,
            label,
        )
        mutation_controls += 1

    hostile_schema = copy.deepcopy(schema)
    hostile_schema["$defs"]["sha256"]["unknownAssertion"] = True
    expect_rejected(
        lambda: checker.validate_receipt_document(
            baseline,
            hostile_schema,
            source,
            inputs,
            adjacent,
        ),
        "unknown-schema-keyword",
        checker.CheckError,
    )
    mutation_controls += 1
    schema_mutations: list[tuple[str, Any]] = []

    ref_sibling = copy.deepcopy(schema)
    ref_sibling["$defs"]["sha256"]["$ref"] = "#/$defs/sha256"
    schema_mutations.append(("ref-assertion-sibling", ref_sibling))

    unresolved_ref = copy.deepcopy(schema)
    unresolved_ref["properties"]["schema"] = {"$ref": "#/$defs/absent"}
    schema_mutations.append(("unresolved-ref", unresolved_ref))

    cyclic_ref = copy.deepcopy(schema)
    cyclic_ref["$defs"]["cycle"] = {"$ref": "#/$defs/cycle"}
    schema_mutations.append(("cyclic-ref", cyclic_ref))

    malformed_ref_escape = copy.deepcopy(schema)
    malformed_ref_escape["properties"]["schema"] = {
        "$ref": "#/$defs/bad~2escape"
    }
    schema_mutations.append(("malformed-ref-escape", malformed_ref_escape))

    duplicate_required = copy.deepcopy(schema)
    duplicate_required["required"].append(duplicate_required["required"][0])
    schema_mutations.append(("duplicate-required", duplicate_required))

    required_outside_properties = copy.deepcopy(schema)
    required_outside_properties["required"].append("undeclared")
    schema_mutations.append(
        ("required-outside-properties", required_outside_properties)
    )

    unsupported_type = copy.deepcopy(schema)
    unsupported_type["$defs"]["sha256"]["type"] = "number"
    schema_mutations.append(("unsupported-number-type", unsupported_type))

    open_object = copy.deepcopy(schema)
    open_object["additionalProperties"] = True
    schema_mutations.append(("open-object-schema", open_object))

    array_without_items = copy.deepcopy(schema)
    array_without_items["properties"]["commands"].pop("items")
    schema_mutations.append(("array-without-items", array_without_items))

    nonfinite_schema = copy.deepcopy(schema)
    nonfinite_schema["$defs"]["sha256"]["const"] = float("nan")
    schema_mutations.append(("programmatic-nonfinite-schema", nonfinite_schema))

    for label, hostile in schema_mutations:
        expect_rejected(
            lambda hostile=hostile: checker.validate_receipt_document(
                baseline, hostile, source, inputs, adjacent
            ),
            label,
            checker.CheckError,
        )
        mutation_controls += 1
    expect_rejected(
        lambda: checker.strict_json(b'{"schema":1,"schema":2}\n', "duplicate-key"),
        "duplicate-JSON-key",
        checker.CheckError,
    )
    mutation_controls += 1
    for token in (b"NaN", b"Infinity", b"-Infinity"):
        expect_rejected(
            lambda token=token: checker.strict_json(
                b'{"value":' + token + b"}\n", "non-finite-number"
            ),
            f"non-finite-{token.decode('ascii')}",
            checker.CheckError,
        )
        mutation_controls += 1

    canonical_baseline = checker.canonical_json(baseline)
    for raw, label in (
        (canonical_baseline + b"\n", "trailing-receipt-bytes"),
        (
            json.dumps(
                baseline,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
            "noncanonical-receipt-layout",
        ),
    ):
        parsed = checker.strict_json(raw, label)
        expect_rejected(
            lambda parsed=parsed, raw=raw: checker.require(
                checker.canonical_json(parsed) == raw,
                "receipt encoding is not canonical",
            ),
            label,
            checker.CheckError,
        )
        mutation_controls += 1

    expected_blob = ("100644", "d" * 40, b"receipt")
    checker.require_preserved_receipt_chain(
        [("e" * 40, expected_blob), ("f" * 40, expected_blob)], expected_blob
    )
    for chain, label in (
        (
            [("e" * 40, expected_blob), ("f" * 40, ("100644", "0" * 40, b"mutated")), ("1" * 40, expected_blob)],
            "modify-then-revert-ancestry",
        ),
        (
            [("e" * 40, expected_blob), ("f" * 40, None), ("1" * 40, expected_blob)],
            "delete-then-readd-ancestry",
        ),
        (
            [("e" * 40, expected_blob), ("f" * 40, ("100755", expected_blob[1], expected_blob[2]))],
            "receipt-mode-ancestry",
        ),
    ):
        expect_rejected(
            lambda chain=chain: checker.require_preserved_receipt_chain(chain, expected_blob),
            label,
            checker.CheckError,
        )
        mutation_controls += 1

    dag_controls = 0

    def run_dag_git(repository: Path, arguments: list[str]) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            env={
                "GIT_ATTR_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.environ.get("PATH", ""),
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        require(
            completed.returncode == 0 and completed.stderr == b"",
            f"temporary DAG command failed: {' '.join(arguments)}",
        )
        return completed.stdout.decode("ascii", errors="strict").strip()

    def initialize_dag(repository: Path) -> str:
        run_dag_git(repository, ["init", "-q"])
        run_dag_git(repository, ["config", "user.name", "P5 DAG fixture"])
        run_dag_git(repository, ["config", "user.email", "p5-dag@example.invalid"])
        (repository / "tracked").write_bytes(b"baseline\n")
        run_dag_git(repository, ["add", "--", "tracked"])
        run_dag_git(repository, ["commit", "-q", "-m", "base"])
        return run_dag_git(repository, ["rev-parse", "HEAD"])

    def write_dag_receipt(repository: Path) -> None:
        path = repository / checker.RECEIPT_RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"identical receipt bytes\n")

    def commit_dag_receipt(repository: Path, message: str) -> str:
        run_dag_git(repository, ["add", "--", checker.RECEIPT_RELATIVE])
        run_dag_git(repository, ["commit", "-q", "-m", message])
        return run_dag_git(repository, ["rev-parse", "HEAD"])

    git_security_controls = 0

    def exercise_checker_canonical_threat(
        label: str, expected_fragment: str, mutation: Any
    ) -> None:
        nonlocal git_security_controls
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-p5-checker-git-security-"
        ) as raw_repository:
            repository = Path(raw_repository)
            fixture_head = initialize_dag(repository)
            fixture_tree = run_dag_git(repository, ["rev-parse", "HEAD^{tree}"])
            original_root = checker.ROOT
            original_base_commit = checker.BASE_COMMIT
            original_base_tree = checker.BASE_TREE
            checker.ROOT = repository.resolve()
            checker.BASE_COMMIT = fixture_head
            checker.BASE_TREE = fixture_tree
            try:
                checker.canonical_repository()
                mutation(repository)
                error = expect_rejected(
                    checker.canonical_repository, label, checker.CheckError
                )
                require(
                    expected_fragment in str(error),
                    f"checker Git security control rejected for wrong reason: {label}",
                )
            finally:
                checker.ROOT = original_root
                checker.BASE_COMMIT = original_base_commit
                checker.BASE_TREE = original_base_tree
        git_security_controls += 1

    def checker_write_graft(repository: Path) -> None:
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        (repository / ".git" / "info" / "grafts").write_text(
            f"{head}\n", encoding="ascii"
        )

    def checker_write_alternate(repository: Path) -> None:
        (repository / ".git" / "objects" / "info" / "alternates").write_text(
            "/nonexistent/object/store\n", encoding="utf-8"
        )

    def checker_write_sparse(repository: Path) -> None:
        (repository / ".git" / "info" / "sparse-checkout").write_text(
            "/*\n", encoding="utf-8"
        )

    def checker_write_promisor(repository: Path) -> None:
        (repository / ".git" / "objects" / "pack" / "fixture.promisor").write_bytes(
            b""
        )

    def checker_write_shallow(repository: Path) -> None:
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        (repository / ".git" / "shallow").write_text(f"{head}\n", encoding="ascii")

    def checker_configure_partial(repository: Path) -> None:
        run_dag_git(repository, ["config", "extensions.partialClone", "origin"])

    def checker_configure_include(repository: Path) -> None:
        run_dag_git(repository, ["config", "include.path", "/nonexistent/config"])

    def checker_configure_filter(repository: Path) -> None:
        run_dag_git(repository, ["config", "filter.fixture.clean", "cat"])

    def checker_write_info_attributes(repository: Path) -> None:
        (repository / ".git" / "info" / "attributes").write_bytes(
            b"tracked filter=fixture\n"
        )

    def checker_write_replace(repository: Path) -> None:
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        replacement = repository / ".git" / "refs" / "replace" / head
        replacement.parent.mkdir(parents=True, exist_ok=True)
        replacement.write_text(f"{head}\n", encoding="ascii")

    def checker_symlink_object_directory(repository: Path, component: str) -> None:
        directory = (
            repository / ".git" / "objects" / component
            if component
            else repository / ".git" / "objects"
        )
        moved = directory.with_name(directory.name + "-real")
        directory.rename(moved)
        directory.symlink_to(moved.name, target_is_directory=True)

    for label, fragment, mutation in (
        ("checker-graft", "exact HEAD bootstrap failed closed", checker_write_graft),
        ("checker-alternate", "exact HEAD bootstrap failed closed", checker_write_alternate),
        ("checker-sparse", "sparse-checkout state", checker_write_sparse),
        ("checker-promisor", "promisor object packs", checker_write_promisor),
        ("checker-shallow", "shallow history", checker_write_shallow),
        ("checker-partial", "partial-clone, promisor, or sparse", checker_configure_partial),
        ("checker-include", "partial-clone, promisor, or sparse", checker_configure_include),
        ("checker-filter-config", "partial-clone, promisor, or sparse", checker_configure_filter),
        ("checker-info-attributes", "info/attributes", checker_write_info_attributes),
        ("checker-replace", "replacement refs", checker_write_replace),
        (
            "checker-symlink-objects",
            "object storage directories",
            lambda repository: checker_symlink_object_directory(repository, ""),
        ),
        (
            "checker-symlink-info",
            "object storage directories",
            lambda repository: checker_symlink_object_directory(repository, "info"),
        ),
        (
            "checker-symlink-pack",
            "object storage directories",
            lambda repository: checker_symlink_object_directory(repository, "pack"),
        ),
    ):
        exercise_checker_canonical_threat(label, fragment, mutation)

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-p5-checker-index-security-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_dag(repository)
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            require(checker.status_bytes() == b"", "checker rejected clean index")
            run_dag_git(repository, ["update-index", "--assume-unchanged", "tracked"])
            expect_rejected(
                checker.status_bytes, "checker-assume-unchanged", checker.CheckError
            )
            run_dag_git(repository, ["update-index", "--no-assume-unchanged", "tracked"])
            git_security_controls += 1
            run_dag_git(repository, ["update-index", "--skip-worktree", "tracked"])
            expect_rejected(
                checker.status_bytes, "checker-skip-worktree", checker.CheckError
            )
            run_dag_git(repository, ["update-index", "--no-skip-worktree", "tracked"])
            git_security_controls += 1
            head = run_dag_git(repository, ["rev-parse", "HEAD"])
            run_dag_git(
                repository,
                ["update-index", "--add", "--cacheinfo", f"160000,{head},nested"],
            )
            expect_rejected(
                checker.status_bytes, "checker-gitlink-index", checker.CheckError
            )
            run_dag_git(repository, ["update-index", "--force-remove", "nested"])
            git_security_controls += 1
            (repository / "ordinary-link").symlink_to("tracked")
            run_dag_git(repository, ["add", "--", "ordinary-link"])
            run_dag_git(repository, ["commit", "-q", "-m", "ordinary symlink"])
            require(
                checker.status_bytes() == b"",
                "checker incorrectly rejected an ordinary stage-0 symlink",
            )
            git_security_controls += 1
        finally:
            checker.ROOT = original_root

    original_git_bytes = checker.git_bytes
    index_fixture = {
        "visible": b"H tracked\0",
        "stage": b"100644 " + b"0" * 40 + b" 0\ttracked\0",
    }

    def checker_index_git_bytes(
        arguments: list[str],
        *,
        stdin_bytes: bytes | None = None,
        attribute_source: str | None = None,
        pin_attributes: bool = True,
    ) -> bytes:
        require(
            stdin_bytes is None
            and attribute_source == "f" * 40
            and pin_attributes,
            "checker index mock was not exact-HEAD pinned",
        )
        if arguments == ["ls-files", "-v", "-z"]:
            return index_fixture["visible"]
        if arguments == ["ls-files", "--sparse", "--stage", "-z"]:
            return index_fixture["stage"]
        raise SelfTestError("unexpected checker index mock invocation")

    checker.git_bytes = checker_index_git_bytes
    try:
        checker.require_index_state_closed("f" * 40)
        index_fixture["stage"] = (
            b"040000 " + b"0" * 40 + b" 0\ttracked\0"
        )
        expect_rejected(
            lambda: checker.require_index_state_closed("f" * 40),
            "checker-sparse-directory-index",
            checker.CheckError,
        )
        git_security_controls += 1
        index_fixture["stage"] = (
            b"100644 "
            + b"0" * 40
            + b" 0\ttracked\0"
            + b"100644 "
            + b"0" * 40
            + b" 0\ttracked\0"
        )
        expect_rejected(
            lambda: checker.require_index_state_closed("f" * 40),
            "checker-duplicate-stage-path",
            checker.CheckError,
        )
        git_security_controls += 1
    finally:
        checker.git_bytes = original_git_bytes

    def initialize_checker_attributes(repository: Path) -> None:
        initialize_dag(repository)

    def commit_checker_attributes(repository: Path, contents: bytes) -> None:
        (repository / ".gitattributes").write_bytes(contents)
        run_dag_git(repository, ["add", "--", ".gitattributes"])
        run_dag_git(repository, ["commit", "-q", "-m", "attributes"])

    def exercise_checker_attribute_threat(
        label: str, setup: Any, fragment: str
    ) -> None:
        nonlocal git_security_controls
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-p5-checker-attribute-"
        ) as raw_repository:
            repository = Path(raw_repository)
            initialize_checker_attributes(repository)
            setup(repository)
            original_root = checker.ROOT
            checker.ROOT = repository.resolve()
            try:
                error = expect_rejected(
                    checker.status_bytes, label, checker.CheckError
                )
                require(
                    fragment in str(error),
                    f"checker attribute control rejected for wrong reason: {label}",
                )
            finally:
                checker.ROOT = original_root
        git_security_controls += 1

    exercise_checker_attribute_threat(
        "checker-exact-HEAD-filter",
        lambda repository: commit_checker_attributes(
            repository, b"tracked filter=fixture\n"
        ),
        "exact HEAD attributes",
    )
    exercise_checker_attribute_threat(
        "checker-effective-filter",
        lambda repository: (repository / ".gitattributes").write_bytes(
            b"tracked filter=fixture\n"
        ),
        "effective worktree/index attributes",
    )

    def checker_remove_head_filter(repository: Path) -> None:
        commit_checker_attributes(repository, b"tracked filter=fixture\n")
        (repository / ".gitattributes").write_bytes(b"tracked text\n")

    exercise_checker_attribute_threat(
        "checker-dirty-filter-removal",
        checker_remove_head_filter,
        "exact HEAD attributes",
    )
    exercise_checker_attribute_threat(
        "checker-unset-filter",
        lambda repository: commit_checker_attributes(repository, b"tracked -filter\n"),
        "exact HEAD attributes",
    )
    exercise_checker_attribute_threat(
        "checker-unspecified-driver-name",
        lambda repository: commit_checker_attributes(
            repository, b"tracked filter=unspecified\n"
        ),
        "exact HEAD attributes",
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-p5-checker-attribute-unspecified-positive-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_checker_attributes(repository)
        commit_checker_attributes(repository, b"tracked !filter\n")
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            require(
                checker.status_bytes() == b"",
                "checker rejected safe explicitly-unspecified filter attribute",
            )
        finally:
            checker.ROOT = original_root
        git_security_controls += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-p5-checker-attribute-potency-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_checker_attributes(repository)
        marker = repository / "ordinary-status-filter-executed"
        (repository / ".gitattributes").write_bytes(b"tracked filter=sentinel\n")
        (repository / "tracked").write_bytes(b"changed!\n")
        run_dag_git(
            repository,
            [
                "config",
                "filter.sentinel.clean",
                f"touch {shlex.quote(os.fspath(marker))}; cat",
            ],
        )
        run_dag_git(
            repository,
            ["status", "--porcelain=v1", "--ignore-submodules=all"],
        )
        require(marker.exists(), "checker filter potency control was inert")
        git_security_controls += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-p5-checker-attribute-gap-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_checker_attributes(repository)
        marker = repository / "pinned-status-filter-executed"
        original_root = checker.ROOT
        original_closure = checker.require_status_attribute_closure
        closure_calls = 0

        def checker_mutate_after_probe(head_oid: str) -> None:
            nonlocal closure_calls
            closure_calls += 1
            original_closure(head_oid)
            if closure_calls == 1:
                (repository / ".gitattributes").write_bytes(
                    b"tracked filter=sentinel\n"
                )
                (repository / "tracked").write_bytes(b"changed!\n")
                run_dag_git(
                    repository,
                    [
                        "config",
                        "filter.sentinel.clean",
                        f"touch {shlex.quote(os.fspath(marker))}; cat",
                    ],
                )

        checker.ROOT = repository.resolve()
        checker.require_status_attribute_closure = checker_mutate_after_probe
        try:
            error = expect_rejected(
                checker.status_bytes,
                "checker-attribute-gap",
                checker.CheckError,
            )
            require(
                "filter, attribute, or include configuration" in str(error)
                and closure_calls >= 2
                and not marker.exists(),
                "checker exact-OID status pin did not suppress gap filter",
            )
        finally:
            checker.require_status_attribute_closure = original_closure
            checker.ROOT = original_root
        git_security_controls += 1

    guarded_calls: list[tuple[list[str], dict[str, str]]] = []
    original_run_capped = checker.CAPTURE_SUPPORT.run_capped

    def record_guarded_call(*arguments: Any, **keywords: Any) -> Any:
        guarded_calls.append((list(arguments[0]), dict(keywords["environment"])))
        return original_run_capped(*arguments, **keywords)

    checker.CAPTURE_SUPPORT.run_capped = record_guarded_call
    try:
        status, stdout, stderr = checker.run_git(["version"])
    finally:
        checker.CAPTURE_SUPPORT.run_capped = original_run_capped
    require(
        status == 0 and stdout.startswith(b"git version ") and stderr == b"",
        "checker guarded Git positive control failed",
    )
    require(len(guarded_calls) >= 2, "checker guarded call roster is incomplete")
    for argv, environment in guarded_calls:
        for required in (
            "core.commitGraph=false",
            f"core.attributesFile={os.devnull}",
            "core.filemode=true",
            "core.symlinks=true",
            "core.checkStat=default",
            "core.trustctime=true",
        ):
            require(required in argv, f"checker guarded Git omitted {required}")
        require(
            environment.get("GIT_ATTR_NOSYSTEM") == "1"
            and environment.get("GIT_CONFIG_GLOBAL") == os.devnull
            and environment.get("GIT_CONFIG_SYSTEM") == os.devnull,
            "checker guarded Git environment isolation drifted",
        )
    ordinary_calls = [
        environment
        for argv, environment in guarded_calls
        if argv[-1] == "version"
    ]
    require(
        len(ordinary_calls) == 1
        and ordinary_calls[0].get("GIT_ATTR_SOURCE")
        == checker.bootstrap_head_oid(),
        "checker ordinary Git call was not pinned to the exact HEAD OID",
    )
    git_security_controls += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-p5-linear-dag-") as raw:
        repository = Path(raw)
        initialize_dag(repository)
        write_dag_receipt(repository)
        evidence = commit_dag_receipt(repository, "E")
        original_root = checker.ROOT
        original_git_bytes = checker.git_bytes
        calls: list[list[str]] = []

        def recording_git_bytes(arguments: list[str]) -> bytes:
            calls.append(list(arguments))
            return original_git_bytes(arguments)

        checker.ROOT = repository.resolve()
        checker.git_bytes = recording_git_bytes
        try:
            require(
                checker.receipt_introduction_frontiers(evidence) == [evidence],
                "linear E frontier was not discovered exactly once",
            )
            require(
                calls
                and calls[0] == ["rev-list", "--parents", evidence]
                and checker.RECEIPT_RELATIVE not in calls[0]
                and "--" not in calls[0],
                "frontier discovery did not use the raw no-pathspec parent graph",
            )
        finally:
            checker.git_bytes = original_git_bytes
            checker.ROOT = original_root
        dag_controls += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-p5-carry-merge-dag-") as raw:
        repository = Path(raw)
        base = initialize_dag(repository)
        run_dag_git(repository, ["checkout", "-q", "-b", "with-receipt"])
        write_dag_receipt(repository)
        evidence = commit_dag_receipt(repository, "E")
        run_dag_git(repository, ["checkout", "-q", "-b", "without-receipt", base])
        (repository / "other.txt").write_bytes(b"other branch\n")
        run_dag_git(repository, ["add", "--", "other.txt"])
        run_dag_git(repository, ["commit", "-q", "-m", "absent branch"])
        run_dag_git(repository, ["checkout", "-q", "with-receipt"])
        run_dag_git(
            repository,
            ["merge", "-q", "--no-ff", "-m", "carry merge", "without-receipt"],
        )
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            require(
                checker.receipt_introduction_frontiers(head) == [evidence],
                "carry merge was falsely classified as a second introduction",
            )
        finally:
            checker.ROOT = original_root
        dag_controls += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-p5-sibling-dag-") as raw:
        repository = Path(raw)
        base = initialize_dag(repository)
        run_dag_git(repository, ["checkout", "-q", "-b", "left"])
        write_dag_receipt(repository)
        left_e = commit_dag_receipt(repository, "left E")
        run_dag_git(repository, ["checkout", "-q", "-b", "right", base])
        write_dag_receipt(repository)
        right_e = commit_dag_receipt(repository, "right E")
        run_dag_git(repository, ["merge", "-q", "--no-ff", "-m", "sibling merge", "left"])
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            require(
                checker.receipt_introduction_frontiers(head)
                == sorted([left_e, right_e]),
                "sibling introductions were not both discovered",
            )
            error = expect_rejected(
                lambda: checker.unique_introduction_commit(head),
                "sibling-introduction-frontiers",
                checker.CheckError,
            )
            require(
                "not one unique raw-full-history frontier" in str(error),
                "sibling frontier rejected for the wrong reason",
            )
        finally:
            checker.ROOT = original_root
        dag_controls += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-p5-delete-readd-dag-") as raw:
        repository = Path(raw)
        initialize_dag(repository)
        write_dag_receipt(repository)
        first_e = commit_dag_receipt(repository, "first E")
        run_dag_git(repository, ["rm", "-q", "--", checker.RECEIPT_RELATIVE])
        run_dag_git(repository, ["commit", "-q", "-m", "delete receipt"])
        write_dag_receipt(repository)
        second_e = commit_dag_receipt(repository, "second E")
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            require(
                checker.receipt_introduction_frontiers(second_e)
                == sorted([first_e, second_e]),
                "delete/readd introductions were not both discovered",
            )
            error = expect_rejected(
                lambda: checker.unique_introduction_commit(second_e),
                "delete-readd-frontiers",
                checker.CheckError,
            )
            require(
                "not one unique raw-full-history frontier" in str(error),
                "delete/readd frontier rejected for the wrong reason",
            )
        finally:
            checker.ROOT = original_root
        dag_controls += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-p5-modify-revert-merge-dag-"
    ) as raw:
        repository = Path(raw)
        initialize_dag(repository)
        write_dag_receipt(repository)
        evidence = commit_dag_receipt(repository, "E")
        run_dag_git(repository, ["checkout", "-q", "-b", "modify-revert"])
        receipt_path = repository / checker.RECEIPT_RELATIVE
        receipt_path.write_bytes(b"hostile same-path receipt bytes\n")
        run_dag_git(repository, ["add", "--", checker.RECEIPT_RELATIVE])
        run_dag_git(repository, ["commit", "-q", "-m", "modify receipt"])
        modified = run_dag_git(repository, ["rev-parse", "HEAD"])
        receipt_path.write_bytes(b"identical receipt bytes\n")
        run_dag_git(repository, ["add", "--", checker.RECEIPT_RELATIVE])
        run_dag_git(repository, ["commit", "-q", "-m", "revert receipt bytes"])
        reverted = run_dag_git(repository, ["rev-parse", "HEAD"])
        run_dag_git(repository, ["checkout", "-q", "-b", "clean-side", evidence])
        (repository / "unrelated.txt").write_bytes(b"unrelated\n")
        run_dag_git(repository, ["add", "--", "unrelated.txt"])
        run_dag_git(repository, ["commit", "-q", "-m", "unrelated side"])
        clean_side = run_dag_git(repository, ["rev-parse", "HEAD"])
        run_dag_git(
            repository,
            [
                "merge",
                "-q",
                "--no-ff",
                "-m",
                "merge modify-revert history",
                "modify-revert",
            ],
        )
        head = run_dag_git(repository, ["rev-parse", "HEAD"])
        original_root = checker.ROOT
        checker.ROOT = repository.resolve()
        try:
            ancestry = checker.ancestry_path(evidence, head)
            require(
                ancestry[0] == evidence
                and ancestry[-1] == head
                and {modified, reverted, clean_side}.issubset(set(ancestry)),
                "raw ancestry-path omitted a modify/revert or divergent commit",
            )
            expected = checker.ls_tree_entry(evidence, checker.RECEIPT_RELATIVE)
            require(expected is not None, "real preservation fixture lacks E receipt")
            error = expect_rejected(
                lambda: checker.require_preserved_receipt_chain(
                    [
                        (
                            commit,
                            checker.ls_tree_entry(commit, checker.RECEIPT_RELATIVE),
                        )
                        for commit in ancestry
                    ],
                    expected,
                ),
                "real-modify-revert-merge-preservation",
                checker.CheckError,
            )
            require(
                "does not preserve the exact receipt" in str(error),
                "real modify/revert merge was rejected for the wrong reason",
            )
        finally:
            checker.ROOT = original_root
        dag_controls += 1

    python = os.fspath(Path(sys.executable).resolve())
    help_run = subprocess.run(
        [python, "-I", "-S", "-B", os.fspath(CHECKER_PATH), "--help"],
        cwd=ROOT,
        env={
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    require(
        help_run.returncode == 0
        and help_run.stderr == b""
        and all(
            flag in help_run.stdout
            for flag in (
                b"--source-side",
                b"--prospective",
                b"--committed-or-preserved",
                b"--workflow",
            )
        )
        and b"--self-test" not in help_run.stdout,
        "checker CLI surface drifted",
    )

    result = {
        "ancestry_preservation_controls": 3,
        "raw_history_frontier_controls": dag_controls,
        "format": "/pid-rs/sxpid3-bounded-keyed-scalar-audit-expressions-receipt-checker-self-test/v1",
        "exact_source_loader_controls": loader_controls,
        "git_and_attribute_security_controls": git_security_controls,
        "mutation_controls": mutation_controls,
        "normal_optimized_self_test_contract": True,
        "production_hidden_test_hook": False,
        "status": "GO",
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SelfTestError) as error:
        print(f"ERROR: checker self-test failed closed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
