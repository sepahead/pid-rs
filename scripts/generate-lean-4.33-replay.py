#!/usr/bin/env python3
"""Generate one exact, environment-isolated Lean 4.33 current-project replay receipt."""

# ruff: noqa: E402 -- isolation is checked before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
):
    print(
        "ERROR: generator requires Python 3.11+ -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import atexit
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


def die(message: str) -> None:
    raise SystemExit(message)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        die(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def stream(payload: bytes) -> dict[str, object]:
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> int:
    if len(sys.argv) != 6:
        die("usage: generator REPO LEAN_BIN PYTHON ARCHIVE OUTPUT")
    root = Path(sys.argv[1]).resolve(strict=True)
    lean_bin = Path(sys.argv[2]).resolve(strict=True)
    python = Path(sys.argv[3]).resolve(strict=True)
    archive = Path(os.path.abspath(os.fspath(Path(sys.argv[4]))))
    output = Path(sys.argv[5])
    freeze = load_module(root / "scripts/check-lean-toolchain-freeze.py", "pid_freeze")
    finite = load_module(
        root / "scripts/check-lean-finite-convergence.py", "pid_finite"
    )
    lake = (lean_bin / "lake").resolve(strict=True)
    lean = (lean_bin / "lean").resolve(strict=True)
    project = root / "audit/formal/lean"
    if os.path.lexists(project / ".lake/build") or os.path.lexists(
        project / ".lake/config"
    ):
        die("project build/config must be absent before replay")
    if (
        not os.path.lexists(project / ".lake/packages")
        or (project / ".lake/packages").is_symlink()
        or not (project / ".lake/packages").is_dir()
    ):
        die("dependency packages directory is absent")

    archive_start = timestamp()
    try:
        archive_lstat_before = os.lstat(archive)
    except OSError as error:
        die(f"cannot inspect archive: {error}")
    if (
        not stat.S_ISREG(archive_lstat_before.st_mode)
        or archive_lstat_before.st_nlink != 1
    ):
        die("archive must be a single-link regular file")
    archive_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        archive_flags |= os.O_NOFOLLOW
    descriptor = os.open(archive, archive_flags)
    try:
        archive_fstat_before = os.fstat(descriptor)
        archive_hasher = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            archive_hasher.update(chunk)
        archive_fstat_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    archive_lstat_after = os.lstat(archive)

    def archive_identity(value):
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        archive_identity(archive_lstat_before)
        == archive_identity(archive_fstat_before)
        == archive_identity(archive_fstat_after)
        == archive_identity(archive_lstat_after)
    ):
        die("archive identity changed during hashing")
    archive_digest = archive_hasher.hexdigest()
    if (
        archive_fstat_after.st_size != freeze.EXPECTED_ARCHIVE["size_bytes"]
        or archive_digest != freeze.EXPECTED_ARCHIVE["sha256"]
        or archive.name != freeze.EXPECTED_ARCHIVE["file_name"]
    ):
        die("archive size, digest, or basename differs from the frozen pin")
    archive_end = timestamp()
    archive_observation = {
        "end_utc": archive_end,
        "path_observed_absolute": os.fspath(archive),
        "sha256": archive_digest,
        "single_link_regular_file": True,
        "size_bytes": archive_fstat_after.st_size,
        "stable_descriptor_identity": True,
        "start_utc": archive_start,
    }

    environment_root = Path(
        tempfile.mkdtemp(prefix="pid-rs-lean433-replay-env.", dir="/private/tmp")
    ).resolve(strict=True)
    atexit.register(shutil.rmtree, environment_root, ignore_errors=True)
    isolated_home = environment_root / "home"
    isolated_tmpdir = environment_root / "tmp"
    isolated_home.mkdir(mode=0o700)
    isolated_tmpdir.mkdir(mode=0o700)
    environment = {
        "HOME": os.fspath(isolated_home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join(
            (os.fspath(lean_bin), "/opt/homebrew/bin", "/usr/bin", "/bin")
        ),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": os.fspath(isolated_tmpdir),
        "TZ": "UTC",
    }
    if tuple(sorted(environment)) != (
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
        "TMPDIR",
        "TZ",
    ):
        die("effective environment allowlist drifted")
    freeze.check_static_without_receipt()
    custody_before = {
        relative: freeze.stable_read(
            root / relative, f"pre-replay custody gate: {relative}"
        )
        for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS
    }
    records: list[dict[str, object]] = []
    axiom_input: bytes | None = None
    build_stdout = b""

    for name, cwd_relative, logical in freeze.expected_command_specs():
        cwd = root if cwd_relative == "." else root / cwd_relative
        if logical[0] == "lean":
            executed = (os.fspath(lean), *logical[1:])
        elif logical[0] == "lake":
            executed = (os.fspath(lake), *logical[1:])
        elif logical[0] == "python3":
            executed = (os.fspath(python), *logical[1:])
        else:
            die(f"unsupported executable: {logical[0]}")
        input_bytes = None
        cache_state = None
        if name == "theorem_axiom_audit":
            _source_count, _declaration_count, theorem_names = finite.check_sources()
            input_bytes = finite.theorem_axiom_audit_source(theorem_names).encode(
                "utf-8"
            )
            if stream(input_bytes) != freeze.EXPECTED_THEOREM_AXIOM_AUDIT_STDIN:
                die("theorem axiom query identity differs from the frozen expectation")
            axiom_input = input_bytes
        elif name == "clean_build":
            build_absent = not os.path.lexists(project / ".lake/build")
            config_absent = not os.path.lexists(project / ".lake/config")
            packages_present = (
                os.path.lexists(project / ".lake/packages")
                and not (project / ".lake/packages").is_symlink()
                and (project / ".lake/packages").is_dir()
            )
            if not (build_absent and config_absent and packages_present):
                die("clean-build cache preflight changed before launch")
            cache_state = {
                "dependency_packages_directory_present_before": packages_present,
                "project_build_directory_absent_before": build_absent,
                "project_config_directory_absent_before": config_absent,
                "project_oleans_reused": False,
            }
        start = timestamp()
        process = subprocess.run(
            executed,
            cwd=cwd,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        end = timestamp()
        if process.returncode != 0:
            sys.stderr.buffer.write(process.stderr)
            die(f"{name} failed with exit {process.returncode}")
        if process.stderr:
            sys.stderr.buffer.write(process.stderr)
            die(f"{name} emitted stderr")
        if name == "lean_version_probe" and process.stdout != (
            "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
            + freeze.EXPECTED_LEAN_IDENTITY["commit"]
            + ", Release)\n"
        ).encode("utf-8"):
            die("Lean version probe did not match the frozen identity")
        if name == "lake_version_probe" and process.stdout != (
            "Lake version 5.0.0-src+d8b1897 (Lean version 4.33.0)\n"
        ).encode("utf-8"):
            die("Lake version probe did not match the frozen identity")
        if name == "clean_build":
            build_stdout = process.stdout
        records.append(
            {
                "argv_executed": list(executed),
                "argv_logical": list(logical),
                "cache_state": cache_state,
                "cwd_observed_absolute": os.fspath(cwd),
                "cwd_repo_relative": cwd_relative,
                "end_utc": end,
                "exit_code": process.returncode,
                "name": name,
                "start_utc": start,
                "stderr": stream(process.stderr),
                "stdin": stream(input_bytes) if input_bytes is not None else None,
                "stdout": stream(process.stdout),
            }
        )

    freeze.check_static_without_receipt()
    custody_after = {
        relative: freeze.stable_read(
            root / relative, f"post-replay custody gate: {relative}"
        )
        for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS
    }
    for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS:
        if (
            custody_before[relative].sha256 != custody_after[relative].sha256
            or custody_before[relative].identity != custody_after[relative].identity
        ):
            die(f"custody gate changed during replay: {relative}")
    by_name = {record["name"]: record for record in records}
    lean_line = (
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + freeze.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Release)\n"
    )
    lake_line = "Lake version 5.0.0-src+d8b1897 (Lean version 4.33.0)\n"
    if by_name["lean_version_probe"]["stdout"] != stream(lean_line.encode("utf-8")):
        die("Lean version record drifted")
    if by_name["lake_version_probe"]["stdout"] != stream(lake_line.encode("utf-8")):
        die("Lake version record drifted")
    if (
        build_stdout.decode("utf-8", errors="strict")
        != freeze.EXPECTED_CLEAN_BUILD_STDOUT
    ):
        die("quiet warning-failing clean build emitted stdout")
    if axiom_input is None:
        die("axiom input was not recorded")

    parity: dict[str, object] = {}
    for pair in freeze.PYTHON_COMMAND_PAIRS:
        normal = by_name[f"{pair}:normal"]
        optimized = by_name[f"{pair}:optimized"]
        if (
            normal["stdout"] != optimized["stdout"]
            or normal["stderr"] != optimized["stderr"]
        ):
            die(f"normal/-O output differs: {pair}")
        parity[pair] = {
            "normal_stderr": normal["stderr"],
            "normal_stdout": normal["stdout"],
            "optimized_stderr": optimized["stderr"],
            "optimized_stdout": optimized["stdout"],
        }

    packages = {
        name: {
            "inherited": inherited,
            "input_revision": input_revision,
            "revision": revision,
            "url": url,
        }
        for name, (
            url,
            revision,
            input_revision,
            inherited,
        ) in freeze.EXPECTED_PACKAGE_PINS.items()
    }
    receipt = {
        "active_claim_authority_sha256": freeze.EXPECTED_ACTIVE_CLAIM_HASHES,
        "active_configuration": freeze.EXPECTED_CONFIG_HASHES,
        "active_resume_sha256": freeze.EXPECTED_ACTIVE_RESUME_HASHES,
        "checker_sha256": freeze.EXPECTED_CHECKER_HASHES,
        "command_records": records,
        "compatibility_scope": {
            "broad_or_file_global_occurrences": 0,
            "command_scoped_fintype_derivation_occurrences": 3,
            "option": freeze.OPTION,
            "proof_term_local_occurrences": 4,
            "total_occurrences": 7,
        },
        "current_evidence_sha256": freeze.EXPECTED_CURRENT_EVIDENCE_HASHES,
        "custody_gate_sha256": {
            path: custody_after[path].sha256
            for path in freeze.EXPECTED_CUSTODY_GATE_PATHS
        },
        "derived_instance_evidence_sha256": freeze.EXPECTED_DERIVED_EVIDENCE_HASHES,
        "environment_policy": {
            "ambient_environment_inherited": False,
            "effective_nonsecret_environment": environment,
            "isolated_home_initially_empty": True,
            "isolated_tmpdir_initially_empty": True,
            "python_isolation_flags": ["-I", "-S", "-B"],
            "routing_variables_inherited": [],
        },
        "execution_environment": {
            "lake_executable": os.fspath(lake),
            "lean_bin_directory": os.fspath(lean_bin),
            "lean_executable": os.fspath(lean),
            "python_executable": os.fspath(python),
            "repo_root_observed": os.fspath(root),
        },
        "execution_window": {
            "end_utc": records[-1]["end_utc"],
            "start_utc": records[0]["start_utc"],
        },
        "historical_preservation_sha256": freeze.PRESERVED_HISTORICAL_HASHES,
        "lake_identity": freeze.EXPECTED_LAKE_IDENTITY,
        "lake_version_line": lake_line,
        "lake_version_stderr": stream(b""),
        "lean_identity": freeze.EXPECTED_LEAN_IDENTITY,
        "lean_version_line": lean_line,
        "lean_version_stderr": stream(b""),
        "official_archive": freeze.EXPECTED_ARCHIVE,
        "official_archive_observation": archive_observation,
        "operational_wiring_sha256": freeze.EXPECTED_OPERATIONAL_WIRING_HASHES,
        "package_pins": packages,
        "provider_observations": freeze.EXPECTED_PROVIDER_OBSERVATIONS,
        "python_optimization_parity": {"all_equal": True, "pairs": parity},
        "replay_custody_gate_sha256": {
            path: custody_after[path].sha256
            for path in freeze.EXPECTED_CUSTODY_GATE_PATHS
        },
        "schema": "pid-rs/lean-current-project-replay/v1",
        "scope_boundary": [
            "Archive digest equality is an observed provider-byte relationship; it does not establish executed-tree-to-archive byte provenance or publisher authentication.",
            "This is not a reproducible build from the reported Lean source commit.",
            "Kernel replay is bounded evidence, not a proof of kernel soundness.",
            "The compatibility port is not a theorem of semantic equivalence between Lean releases.",
            "Exact-real theorem replay does not establish refinement to Rust or binary64 arithmetic.",
            "Pretty-printed derived declarations do not expose or compare generated helper proof bodies.",
            "This replay does not establish theorem intent, scientific validity, estimator validity, sampling claims, or application correctness; pre/post static endpoint equality is not an atomic snapshot.",
        ],
        "source_sha256": freeze.EXPECTED_SOURCE_HASHES,
        "status": "passed",
        "verification": {
            "bound_static_surface": {
                "atomic_snapshot_claimed": False,
                "custody_gate_endpoint_identity_equal": True,
                "custody_gate_files": 2,
                "post_commands": "passed",
                "pre_commands": "passed",
            },
            "clean_build": {
                "dependency_cache_reused": True,
                "project_oleans_reused": False,
                "status": "passed",
                "stdout_exact": freeze.EXPECTED_CLEAN_BUILD_STDOUT,
                "warnings": 0,
                "warnings_fail_build": True,
            },
            "direct_lean_t0": {
                "count": 11,
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
            "forbidden_placeholder_hits": 0,
            "imported_modules": 8,
            "leanchecker": {
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
            "named_source_theorems": 246,
            "permitted_axioms": ["Classical.choice", "Quot.sound", "propext"],
            "python_checker_pairs": len(freeze.PYTHON_COMMAND_PAIRS),
            "source_written_declarations": 339,
            "theorem_axiom_audit": {
                "named_theorems": 246,
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
        },
    }
    raw = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, output)
    print(
        f"wrote {output} ({len(raw)} bytes, sha256={hashlib.sha256(raw).hexdigest()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
