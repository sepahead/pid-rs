#!/usr/bin/env python3
"""Generate the revision 0-4 pid-core API evidence from an exact clean source commit."""

from __future__ import annotations

# The fail-closed runtime bootstrap intentionally precedes ordinary imports.
# ruff: noqa: E402
import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize == 0
):
    print(
        "ERROR: capture-public-api-signature-revision.py requires "
        "Python 3.11+ -I -S -B without -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-release-scope.py"
SCOPE_PATH = ROOT / "release-scope-1.0.json"
REGISTRY_PATH = ROOT / "audit/api/public-api/pid-core-signature-revisions.json"
IDENTITY_PATH = ROOT / "crates/pid-core/identity/software-identity-reference-v1.json"
MARKDOWN_PATH = ROOT / "RELEASE_SCOPE_1_0.md"
MATERIALIZER = ROOT / "scripts/materialize-public-api-source-v2.sh"
PYTHON_EXECUTABLE = Path(os.path.realpath(sys.executable))
TARGET_EPOCH = 0
TARGET_REVISION = 4
TOOLCHAIN_ALIAS = os.environ.get("PID_RS_PUBLIC_API_TOOLCHAIN", "nightly-2026-06-16")


class CaptureError(RuntimeError):
    """A privacy-normalized source, build, or validation failure."""

    def __init__(
        self,
        detail: str = "",
        *,
        operation: str = "capture-validation",
        status: str = "rejected",
        stdout: bytes = b"",
        stderr: bytes | None = None,
    ) -> None:
        if (
            not operation
            or not status
            or any(
                character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
                for character in operation
            )
            or any(
                character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
                for character in status
            )
        ):
            raise ValueError("capture failure labels must be lowercase ASCII tokens")
        diagnostic = detail.encode("utf-8", errors="backslashreplace")
        stderr_bytes = diagnostic if stderr is None else stderr
        self.operation = operation
        self.status = status
        self.stdout_sha256 = sha256(stdout)
        self.stdout_bytes = len(stdout)
        self.stderr_sha256 = sha256(stderr_bytes)
        self.stderr_bytes = len(stderr_bytes)
        super().__init__(self.public_record())

    def public_record(self) -> str:
        """Return the only user-facing form: labels plus byte counts and digests."""

        return (
            f"operation={self.operation} status={self.status} "
            f"stdout_sha256={self.stdout_sha256} stdout_bytes={self.stdout_bytes} "
            f"stderr_sha256={self.stderr_sha256} stderr_bytes={self.stderr_bytes}"
        )


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_capture_failure(error: BaseException) -> CaptureError:
    """Map every internal exception to the same path-free public failure envelope."""

    if isinstance(error, CaptureError):
        return error
    return CaptureError(
        f"{type(error).__module__}.{type(error).__qualname__}: {error}",
        operation="unexpected-capture-failure",
        status="exception",
    )


def load_checker() -> Any:
    sys.path.insert(0, str(CHECKER_PATH.parent))
    spec = importlib.util.spec_from_file_location("pid_rs_release_scope", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise CaptureError("cannot load the release-scope checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical(path: Path) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise CaptureError(f"{path} contains duplicate key {key!r}")
            value[key] = item
        return value

    def reject_constant(token: str) -> None:
        raise CaptureError(f"{path} contains forbidden non-finite number {token}")

    try:
        raw = path.read_bytes()
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CaptureError(f"cannot load {path}: {error}") from error
    if raw != canonical_json(value):
        raise CaptureError(f"{path} is not canonical sorted two-space JSON")
    return value


def run(
    argv: list[str],
    *,
    operation: str,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    stdout: int | None = subprocess.PIPE,
) -> subprocess.CompletedProcess[bytes]:
    try:
        process = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise CaptureError(
            f"{type(error).__name__}: {error}",
            operation=operation,
            status="spawn-error",
        ) from error
    if process.returncode != 0:
        status = (
            f"exit-{process.returncode}"
            if process.returncode >= 0
            else f"signal-{-process.returncode}"
        )
        raise CaptureError(
            operation=operation,
            status=status,
            stdout=process.stdout or b"",
            stderr=process.stderr,
        )
    return process


def validate_pending_source_state() -> None:
    """Require the source commit to fail only at the intentional 0-3/0-4 cut."""

    process = subprocess.run(
        [
            os.fspath(PYTHON_EXECUTABLE),
            "-I",
            "-S",
            "-B",
            str(CHECKER_PATH),
            "--print-markdown",
        ],
        cwd=ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    expected = (
        "release scope error: embedded software identity does not equal the latest "
        "signature revision entry\n"
    ).encode("utf-8")
    if process.returncode != 1 or process.stdout or process.stderr != expected:
        raise CaptureError(
            operation="pending-source-preflight",
            status=(
                f"exit-{process.returncode}"
                if process.returncode >= 0
                else f"signal-{-process.returncode}"
            ),
            stdout=process.stdout,
            stderr=process.stderr,
        )


def isolated_environment(temp_root: Path) -> dict[str, str]:
    original_path = os.environ.get("PATH")
    if not original_path:
        raise CaptureError("PATH is required to locate the pinned Rust tools")
    rustup_path = shutil.which("rustup", path=original_path)
    if rustup_path is None or not Path(rustup_path).is_absolute():
        raise CaptureError("rustup must resolve to an absolute executable path")
    proxy_directory = Path(rustup_path).parent.resolve(strict=True)
    for executable_name in ("rustup", "cargo", "cargo-public-api"):
        endpoint = proxy_directory / executable_name
        if not endpoint.is_file() or not os.access(endpoint, os.X_OK):
            raise CaptureError(
                "the rustup proxy directory lacks an executable "
                f"{executable_name} endpoint"
            )

    keep = {
        name: os.environ[name]
        for name in (
            "ALL_PROXY",
            "HTTPS_PROXY",
            "HTTP_PROXY",
            "NO_PROXY",
            "RUSTUP_HOME",
            "all_proxy",
            "https_proxy",
            "http_proxy",
            "no_proxy",
        )
        if name in os.environ
    }
    home = os.environ.get("HOME")
    if not home:
        raise CaptureError("HOME is required to locate the pinned Rust toolchain")
    keep.update(
        {
            "CARGO_HOME": str(temp_root / "cargo-home"),
            "HOME": home,
            "LANG": "C",
            "LC_ALL": "C",
            # cargo-public-api launches Cargo internally. Keep the rustup proxy directory first
            # even when an unrelated system Cargo appears earlier in the caller's PATH.
            "PATH": os.fspath(proxy_directory) + os.pathsep + original_path,
            "RUSTUP_HOME": os.environ.get("RUSTUP_HOME", str(Path(home) / ".rustup")),
            "TMPDIR": str(temp_root),
            "TZ": "UTC",
        }
    )
    return keep


def reject_ancestor_cargo_configs(source_root: Path) -> None:
    current = source_root.resolve(strict=True)
    while True:
        for relative in (Path(".cargo/config"), Path(".cargo/config.toml")):
            candidate = current / relative
            if candidate.exists() or candidate.is_symlink():
                raise CaptureError(
                    f"public API capture rejects Cargo config in source ancestry: {candidate}"
                )
        if current.parent == current:
            return
        current = current.parent


def generation_command(
    profile: dict[str, Any],
    *,
    rustdoc_target: str,
    rustup_executable: Path,
) -> list[str]:
    command = [
        os.fspath(rustup_executable),
        "run",
        TOOLCHAIN_ALIAS,
        "cargo",
        "public-api",
        "--package",
        "pid-core",
        "--no-default-features",
        "--target",
        rustdoc_target,
        "-sss",
        "--color",
        "never",
    ]
    if profile["all_features"]:
        command.append("--all-features")
    elif profile["requested_features"]:
        command.extend(["--features", ",".join(profile["requested_features"])])
    return command


def capture_profiles(
    scope: dict[str, Any], *, source_root: Path, temp_root: Path
) -> dict[str, bytes]:
    reject_ancestor_cargo_configs(source_root)
    environment = isolated_environment(temp_root)
    (temp_root / "cargo-home").mkdir()
    rustup_route = shutil.which("rustup", path=environment["PATH"])
    cargo_proxy_route = shutil.which("cargo", path=environment["PATH"])
    if rustup_route is None or cargo_proxy_route is None:
        raise CaptureError("isolated Rust tool path omits rustup or Cargo")
    rustup_executable = Path(rustup_route)
    cargo_proxy = Path(cargo_proxy_route)
    if (
        not rustup_executable.is_absolute()
        or not cargo_proxy.is_absolute()
        or rustup_executable.parent != cargo_proxy.parent
    ):
        raise CaptureError("isolated Cargo is not the sibling rustup proxy")
    proxy_cargo_version = run(
        [os.fspath(cargo_proxy), f"+{TOOLCHAIN_ALIAS}", "--version"],
        operation="cargo-proxy-version",
        cwd=source_root,
        env=environment,
    ).stdout
    rustup_cargo_version = run(
        [
            os.fspath(rustup_executable),
            "run",
            TOOLCHAIN_ALIAS,
            "cargo",
            "--version",
        ],
        operation="rustup-cargo-version",
        cwd=source_root,
        env=environment,
    ).stdout
    if proxy_cargo_version != rustup_cargo_version:
        raise CaptureError(
            "rustup Cargo proxy and pinned rustup-run Cargo versions disagree"
        )
    expected_rustc = scope["api_snapshot_source"]["toolchain"]
    actual_rustc = (
        run(
            [
                os.fspath(rustup_executable),
                "run",
                TOOLCHAIN_ALIAS,
                "rustc",
                "--version",
            ],
            operation="rustc-version",
            env=environment,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    if actual_rustc != expected_rustc:
        raise CaptureError(
            f"public API rustc mismatch: expected {expected_rustc!r}, got {actual_rustc!r}"
        )
    verbose_rustc = run(
        [
            os.fspath(rustup_executable),
            "run",
            TOOLCHAIN_ALIAS,
            "rustc",
            "-vV",
        ],
        operation="rustc-verbose-version",
        env=environment,
    ).stdout.decode("utf-8")
    host_lines = [
        line for line in verbose_rustc.splitlines() if line.startswith("host: ")
    ]
    expected_host = scope["api_snapshot_source"]["host_triple"]
    if host_lines != [f"host: {expected_host}"]:
        raise CaptureError(
            f"public API generation host mismatch: expected {expected_host!r}"
        )
    actual_tool = (
        run(
            [
                os.fspath(rustup_executable),
                "run",
                TOOLCHAIN_ALIAS,
                "cargo",
                "public-api",
                "--version",
            ],
            operation="cargo-public-api-version",
            cwd=source_root,
            env=environment,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    expected_tool = scope["api_snapshot_source"]["tool"]
    if actual_tool != expected_tool:
        raise CaptureError(
            f"public API tool mismatch: expected {expected_tool!r}, got {actual_tool!r}"
        )
    rustdoc_target = scope["api_snapshot_source"]["rustdoc_target_triple"]
    target_libdir = (
        run(
            [
                os.fspath(rustup_executable),
                "run",
                TOOLCHAIN_ALIAS,
                "rustc",
                "--print",
                "target-libdir",
                "--target",
                rustdoc_target,
            ],
            operation="rustdoc-target-libdir",
            env=environment,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    if not Path(target_libdir).is_dir():
        raise CaptureError(
            f"public API rustdoc target is not installed: {rustdoc_target}"
        )

    lock_path = source_root / "Cargo.lock"
    if not lock_path.is_file() or lock_path.is_symlink():
        raise CaptureError("materialized source lacks a regular Cargo.lock")
    lock_bytes = lock_path.read_bytes()
    metadata_environment = dict(environment)
    metadata_environment["CARGO_TARGET_DIR"] = str(temp_root / "target-metadata")
    run(
        [
            os.fspath(rustup_executable),
            "run",
            TOOLCHAIN_ALIAS,
            "cargo",
            "metadata",
            "--locked",
            "--format-version",
            "1",
        ],
        operation="cargo-metadata-preflight",
        cwd=source_root,
        env=metadata_environment,
    )
    if lock_path.read_bytes() != lock_bytes:
        raise CaptureError("Cargo.lock changed during locked metadata preflight")

    generated: dict[str, bytes] = {}
    for profile in scope["feature_profiles"]:
        profile_id = profile["id"]
        profile_environment = dict(environment)
        target_dir = temp_root / f"target-{profile_id}"
        profile_environment["CARGO_TARGET_DIR"] = str(target_dir)
        process = run(
            generation_command(
                profile,
                rustdoc_target=rustdoc_target,
                rustup_executable=rustup_executable,
            ),
            operation="generate-public-api-profile",
            cwd=source_root,
            env=profile_environment,
        )
        raw = process.stdout
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CaptureError(f"{profile_id} snapshot is not UTF-8") from error
        if not raw or not raw.endswith(b"\n"):
            raise CaptureError(f"{profile_id} snapshot is empty or lacks a final LF")
        if lock_path.read_bytes() != lock_bytes:
            raise CaptureError(f"Cargo.lock changed while generating {profile_id}")
        generated[profile_id] = raw

    all_features = generated["pid-core-all-features"]
    experimental_all = generated["pid-core-experimental-all"]
    if all_features != experimental_all:
        raise CaptureError(
            "--all-features and --features experimental-all produced different declarations; "
            "the shared physical snapshot is no longer valid"
        )
    return generated


def candidate_values(
    checker: Any,
    scope: dict[str, Any],
    registry: dict[str, Any],
    identity: dict[str, Any],
    generated: dict[str, bytes],
    *,
    source_commit: str,
    source_tree: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, bytes]]:
    updated_scope = json.loads(json.dumps(scope))
    updated_registry = json.loads(json.dumps(registry))
    updated_identity = json.loads(json.dumps(identity))
    output_by_path: dict[str, bytes] = {}

    alias_path = "audit/api/public-api/revisions/0-4/pid-core-experimental-all.txt"
    for profile in updated_scope["feature_profiles"]:
        profile_id = profile["id"]
        relative = (
            alias_path
            if profile_id == "pid-core-all-features"
            else f"audit/api/public-api/revisions/0-4/{profile_id}.txt"
        )
        raw = generated[profile_id]
        prior = output_by_path.get(relative)
        if prior is not None and prior != raw:
            raise CaptureError(f"shared output path disagrees for {profile_id}")
        output_by_path[relative] = raw
        profile["public_api_snapshot"] = relative
        profile["public_api_snapshot_sha256"] = sha256(raw)

    if (
        len(output_by_path)
        != checker.SOURCE_EVIDENCE_TOPOLOGY["physical_snapshot_count"]
    ):
        raise CaptureError("capture did not produce exactly nine physical snapshots")
    checker.validate_public_api_profile_alias_contract(
        updated_scope["feature_profiles"]
    )
    updated_scope["api_snapshot_source"] = {
        "commit_sha": source_commit,
        **checker.API_SNAPSHOT_GENERATION,
        "tree_sha": source_tree,
    }
    profiles = sorted(
        (
            {
                "id": profile["id"],
                "public_api_snapshot": profile["public_api_snapshot"],
                "public_api_snapshot_sha256": profile["public_api_snapshot_sha256"],
            }
            for profile in updated_scope["feature_profiles"]
        ),
        key=lambda item: item["id"],
    )
    updated_registry["entries"].append(
        {
            "epoch": TARGET_EPOCH,
            "evidence_topology": checker.SOURCE_EVIDENCE_TOPOLOGY,
            "generation": checker.API_SNAPSHOT_GENERATION,
            "profiles": profiles,
            "revision": TARGET_REVISION,
            "scope": "proposed_release_scope_profiles",
            "snapshot_source_commit_sha": source_commit,
            "snapshot_source_tree_sha": source_tree,
            "status": "pre_1_0_review",
        }
    )
    registry_raw = canonical_json(updated_registry)
    updated_scope["public_rust_api_signature_revision_registry"][
        "canonical_json_sha256"
    ] = sha256(registry_raw)
    scope_raw = canonical_json(updated_scope)
    updated_identity["api_signature_identity"] = {
        "epoch": TARGET_EPOCH,
        "revision": TARGET_REVISION,
        "scope": "proposed_release_scope_profiles",
        "status": "pre_1_0_review",
    }
    references = [
        item
        for item in updated_identity["reference_artifacts"]
        if item.get("kind") == "proposed_release_scope"
    ]
    if len(references) != 1:
        raise CaptureError(
            "software identity lacks one proposed-release-scope reference"
        )
    references[0]["canonical_json_sha256"] = sha256(scope_raw)
    return (
        updated_scope,
        updated_registry,
        updated_identity,
        output_by_path,
    )


def write_candidate(
    scope: dict[str, Any],
    registry: dict[str, Any],
    identity: dict[str, Any],
    output_by_path: dict[str, bytes],
) -> None:
    revision_dir = ROOT / "audit/api/public-api/revisions/0-4"
    if revision_dir.exists() or revision_dir.is_symlink():
        raise CaptureError("revision 0-4 output directory already exists")
    revision_dir.mkdir(mode=0o755)
    for relative, raw in sorted(output_by_path.items()):
        destination = ROOT / relative
        destination.write_bytes(raw)
        destination.chmod(0o644)
    REGISTRY_PATH.write_bytes(canonical_json(registry))
    SCOPE_PATH.write_bytes(canonical_json(scope))
    IDENTITY_PATH.write_bytes(canonical_json(identity))


def validate_and_render_candidate() -> None:
    rendered = run(
        [
            os.fspath(PYTHON_EXECUTABLE),
            "-I",
            "-S",
            "-B",
            str(CHECKER_PATH),
            "--print-markdown",
        ],
        operation="render-release-scope-markdown",
    ).stdout
    MARKDOWN_PATH.write_bytes(rendered)
    run(
        [os.fspath(PYTHON_EXECUTABLE), "-I", "-S", "-B", str(CHECKER_PATH)],
        operation="validate-release-scope-normal",
    )
    run(
        [
            os.fspath(PYTHON_EXECUTABLE),
            "-O",
            "-I",
            "-S",
            "-B",
            str(CHECKER_PATH),
        ],
        operation="validate-release-scope-optimized",
    )


def main() -> int:
    try:
        checker = load_checker()
        if (
            not PYTHON_EXECUTABLE.is_absolute()
            or not PYTHON_EXECUTABLE.is_file()
            or not os.access(PYTHON_EXECUTABLE, os.X_OK)
        ):
            raise CaptureError(
                "the running Python endpoint is not an absolute executable file",
                operation="python-interpreter-preflight",
            )
        checker.validate_git_repository_context(ROOT)
        if checker.git_output(ROOT, "rev-parse", "--is-shallow-repository") != "false":
            raise CaptureError(
                "revision capture requires Git to report a non-shallow repository; "
                "that report does not establish a complete or non-promisor object graph",
                operation="git-shallow-state",
            )
        dirty = checker.git_output(
            ROOT, "status", "--porcelain=v1", "--untracked-files=all"
        )
        if dirty:
            raise CaptureError(
                "revision capture requires an exact clean source checkout"
            )
        source_commit = checker.git_output(ROOT, "rev-parse", "HEAD^{commit}")
        source_tree = checker.git_output(ROOT, "rev-parse", "HEAD^{tree}")

        scope = load_canonical(SCOPE_PATH)
        registry = load_canonical(REGISTRY_PATH)
        identity = load_canonical(IDENTITY_PATH)
        entries = registry.get("entries")
        if not isinstance(entries, list) or not entries:
            raise CaptureError("signature registry has no predecessor entry")
        latest = entries[-1]
        if (latest.get("epoch"), latest.get("revision")) != (0, 3):
            raise CaptureError(
                "revision 0-4 capture requires exact revision 0-3 predecessor"
            )
        if identity.get("api_signature_identity") != {
            "epoch": 0,
            "revision": 4,
            "scope": "proposed_release_scope_profiles",
            "status": "pre_1_0_review",
        }:
            raise CaptureError(
                "source commit does not declare pending API identity revision 0-4"
            )
        checker.validate_public_api_profile_alias_contract(scope["feature_profiles"])
        validate_pending_source_state()
        if (ROOT / "audit/api/public-api/revisions/0-4").exists():
            raise CaptureError("revision 0-4 evidence already exists")
        planned_paths = {
            (
                "audit/api/public-api/revisions/0-4/pid-core-experimental-all.txt"
                if profile["id"] == "pid-core-all-features"
                else f"audit/api/public-api/revisions/0-4/{profile['id']}.txt"
            )
            for profile in scope["feature_profiles"]
        }
        if len(planned_paths) != 9:
            raise CaptureError("revision 0-4 plan does not contain nine physical paths")
        for relative in sorted(planned_paths):
            if checker.checkout_path_addition_commits(ROOT, relative):
                raise CaptureError(
                    f"revision 0-4 path has prior reachable first-add history: {relative}"
                )

        with tempfile.TemporaryDirectory(
            prefix="pid-rs-public-api-r4-", dir=os.environ.get("TMPDIR")
        ) as temp_name:
            temp_root = Path(temp_name)
            source_root = temp_root / "source"
            run(
                [
                    str(MATERIALIZER),
                    str(ROOT),
                    source_commit,
                    source_tree,
                    str(source_root),
                    os.fspath(PYTHON_EXECUTABLE),
                ],
                operation="materialize-source-tree",
            )
            generated = capture_profiles(
                scope, source_root=source_root, temp_root=temp_root
            )
            updated_scope, updated_registry, updated_identity, outputs = (
                candidate_values(
                    checker,
                    scope,
                    registry,
                    identity,
                    generated,
                    source_commit=source_commit,
                    source_tree=source_tree,
                )
            )

        originals = {
            path: path.read_bytes()
            for path in (SCOPE_PATH, REGISTRY_PATH, IDENTITY_PATH, MARKDOWN_PATH)
        }
        try:
            write_candidate(updated_scope, updated_registry, updated_identity, outputs)
            validate_and_render_candidate()
        except BaseException:
            revision_dir = ROOT / "audit/api/public-api/revisions/0-4"
            if revision_dir.exists() and not revision_dir.is_symlink():
                shutil.rmtree(revision_dir)
            for path, raw in originals.items():
                path.write_bytes(raw)
            raise

        print(
            "OK: generated revision 0-4 candidate from source "
            f"{source_commit} ({len(outputs)} physical snapshots; 10 logical profiles)"
        )
        print(
            "NEXT: commit the generated evidence as a direct child whose only parent is the source commit, "
            "then rerun check-release-scope.py and check-public-api-snapshots.sh"
        )
        return 0
    except BaseException as error:
        failure = normalize_capture_failure(error)
        print(f"public API revision capture error: {failure}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
