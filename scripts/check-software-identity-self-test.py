#!/usr/bin/env python3
"""Failure-injection tests for check-software-identity.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable

if sys.version_info < (3, 11):
    raise SystemExit("check-software-identity-self-test.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-software-identity.py"
MANIFEST = ROOT / "crates/pid-core/identity/software-identity-reference-v1.json"
MUTATION_COUNT = 0
PASSING_FIXTURE_COUNT = 0


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def canonical_write(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def copy_fixture(destination: Path) -> None:
    for relative in [
        "audit/schemas/software-identity-reference.schema.json",
        "crates/pid-core/Cargo.toml",
        "crates/pid-core/build.rs",
        "crates/pid-core/identity/software-identity-reference-v1.json",
        "method-catalog.json",
        "release-scope-1.0.json",
    ]:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--root",
            str(root),
            "--skip-package-list",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def expect_failure(
    name: str,
    mutate: Callable[[Path, dict[str, Any]], None],
    expected: str,
) -> None:
    global MUTATION_COUNT
    with tempfile.TemporaryDirectory(prefix=f"pid-rs-identity-{name}-") as raw:
        root = Path(raw)
        copy_fixture(root)
        path = root / MANIFEST.relative_to(ROOT)
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(root, value)
        process = run_checker(root)
        combined = process.stdout + process.stderr
        if process.returncode == 0 or expected not in combined:
            raise RuntimeError(
                f"{name}: expected failure containing {expected!r}, got "
                f"status {process.returncode}:\n{combined}"
            )
        MUTATION_COUNT += 1


def expect_success(
    name: str,
    mutate: Callable[[Path, dict[str, Any]], None],
) -> None:
    global PASSING_FIXTURE_COUNT
    with tempfile.TemporaryDirectory(prefix=f"pid-rs-identity-{name}-") as raw:
        root = Path(raw)
        copy_fixture(root)
        path = root / MANIFEST.relative_to(ROOT)
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(root, value)
        process = run_checker(root)
        if process.returncode != 0:
            combined = process.stdout + process.stderr
            raise RuntimeError(
                f"{name}: expected success, got status {process.returncode}:\n{combined}"
            )
        PASSING_FIXTURE_COUNT += 1


def write_manifest(root: Path, value: dict[str, Any]) -> None:
    canonical_write(root / MANIFEST.relative_to(ROOT), value)


def manifest_mutation(function: Callable[[dict[str, Any]], None]) -> Callable[[Path, dict[str, Any]], None]:
    def apply(root: Path, value: dict[str, Any]) -> None:
        function(value)
        write_manifest(root, value)

    return apply


def main() -> int:
    global MUTATION_COUNT
    baseline = subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if baseline.returncode != 0:
        raise RuntimeError(f"baseline identity checker failed:\n{baseline.stderr}{baseline.stdout}")

    expect_failure(
        "unknown-field",
        manifest_mutation(lambda value: value.update({"built_at": "2026-01-01"})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-schema",
        manifest_mutation(lambda value: value.update({"schema": "pid-rs/other"})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-schema-revision",
        manifest_mutation(lambda value: value.update({"schema_revision": 2})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-format",
        manifest_mutation(lambda value: value.update({"identity_format": 2})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-package",
        manifest_mutation(lambda value: value.update({"package": "pid-runlog"})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-api-epoch",
        manifest_mutation(
            lambda value: value["api_signature_identity"].update({"epoch": 1})
        ),
        "schema validation failed",
    )
    expect_failure(
        "wrong-api-revision",
        manifest_mutation(
            lambda value: value["api_signature_identity"].update({"revision": 2})
        ),
        "schema validation failed",
    )
    expect_failure(
        "wrong-api-scope",
        manifest_mutation(
            lambda value: value["api_signature_identity"].update(
                {"scope": "default_only"}
            )
        ),
        "schema validation failed",
    )
    expect_failure(
        "wrong-api-status",
        manifest_mutation(
            lambda value: value["api_signature_identity"].update(
                {"status": "stable_1_x"}
            )
        ),
        "schema validation failed",
    )
    expect_failure(
        "invented-attestation",
        manifest_mutation(lambda value: value.update({"attestation": "binary_verified"})),
        "schema validation failed",
    )
    expect_failure(
        "wrong-reference-use",
        manifest_mutation(
            lambda value: value.update({"reference_artifact_use": "validity_certificate"})
        ),
        "schema validation failed",
    )
    expect_failure(
        "missing-feature",
        manifest_mutation(lambda value: value["recognized_cargo_features"].pop()),
        "feature inventory disagrees",
    )
    expect_failure(
        "extra-feature",
        manifest_mutation(
            lambda value: value["recognized_cargo_features"].append("unknown-feature")
        ),
        "feature inventory disagrees",
    )
    expect_failure(
        "reordered-features",
        manifest_mutation(
            lambda value: value["recognized_cargo_features"].reverse()
        ),
        "feature inventory disagrees",
    )
    expect_failure(
        "duplicate-feature",
        manifest_mutation(
            lambda value: value["recognized_cargo_features"].append(
                value["recognized_cargo_features"][-1]
            )
        ),
        "schema validation failed",
    )
    expect_failure(
        "cargo-side-feature",
        lambda root, value: (
            (root / "crates/pid-core/Cargo.toml").write_text(
                (root / "crates/pid-core/Cargo.toml")
                .read_text(encoding="utf-8")
                .replace("default = []\n", "default = []\nidentity-self-test = []\n", 1),
                encoding="utf-8",
            ),
            write_manifest(root, value),
        ),
        "feature inventory disagrees",
    )

    def implicit_optional_dependency_feature(root: Path, value: dict[str, Any]) -> None:
        cargo = root / "crates/pid-core/Cargo.toml"
        source = cargo.read_text(encoding="utf-8").replace(
            'parallel = ["dep:rayon"]', 'parallel = ["rayon"]', 1
        )
        cargo.write_text(source, encoding="utf-8")
        write_manifest(root, value)

    expect_failure(
        "implicit-optional-dependency-feature",
        implicit_optional_dependency_feature,
        "must use explicit dep: feature edges",
    )
    expect_failure(
        "removed-artifact",
        manifest_mutation(lambda value: value["reference_artifacts"].pop()),
        "schema validation failed",
    )
    expect_failure(
        "swapped-artifacts",
        manifest_mutation(lambda value: value["reference_artifacts"].reverse()),
        "identity mismatch",
    )
    expect_failure(
        "unsafe-artifact-path",
        manifest_mutation(
            lambda value: value["reference_artifacts"][0].update(
                {"repository_path": "x/../../method-catalog.json"}
            )
        ),
        "identity mismatch",
    )
    expect_failure(
        "wrong-artifact-role",
        manifest_mutation(
            lambda value: value["reference_artifacts"][0].update(
                {"role": "compatibility_certificate"}
            )
        ),
        "schema validation failed",
    )
    expect_failure(
        "uppercase-digest",
        manifest_mutation(
            lambda value: value["reference_artifacts"][0].update(
                {"canonical_json_sha256": "A" * 64}
            )
        ),
        "schema validation failed",
    )
    expect_failure(
        "wrong-digest",
        manifest_mutation(
            lambda value: value["reference_artifacts"][0].update(
                {"canonical_json_sha256": "0" * 64}
            )
        ),
        "SHA-256 mismatch",
    )

    def compact_digest(root: Path, value: dict[str, Any]) -> None:
        artifact = json.loads((root / "method-catalog.json").read_text(encoding="utf-8"))
        compact = json.dumps(
            artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        value["reference_artifacts"][0]["canonical_json_sha256"] = hashlib.sha256(
            compact
        ).hexdigest()
        write_manifest(root, value)

    expect_failure(
        "compact-semantic-digest",
        compact_digest,
        "SHA-256 mismatch",
    )

    def noncanonical_reference(root: Path, value: dict[str, Any]) -> None:
        path = root / "method-catalog.json"
        artifact = json.loads(path.read_text(encoding="utf-8"))
        raw = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
        path.write_bytes(raw)
        value["reference_artifacts"][0]["canonical_json_sha256"] = hashlib.sha256(raw).hexdigest()
        write_manifest(root, value)

    expect_failure(
        "noncanonical-reference",
        noncanonical_reference,
        "is not canonical sorted two-space ASCII JSON",
    )

    def duplicate_reference_key(root: Path, value: dict[str, Any]) -> None:
        path = root / "method-catalog.json"
        raw = path.read_text(encoding="utf-8").replace(
            "{\n", '{\n  "schema": "pid-rs/method-catalog",\n', 1
        )
        path.write_text(raw, encoding="utf-8")
        value["reference_artifacts"][0]["canonical_json_sha256"] = hashlib.sha256(
            raw.encode()
        ).hexdigest()
        write_manifest(root, value)

    expect_failure(
        "duplicate-reference-key",
        duplicate_reference_key,
        "duplicate JSON object key",
    )

    def noncanonical_manifest(root: Path, value: dict[str, Any]) -> None:
        path = root / MANIFEST.relative_to(ROOT)
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    expect_failure(
        "noncanonical-manifest",
        noncanonical_manifest,
        "is not canonical sorted two-space ASCII JSON",
    )

    def crlf_manifest(root: Path, value: dict[str, Any]) -> None:
        path = root / MANIFEST.relative_to(ROOT)
        path.write_bytes(canonical_bytes(value).replace(b"\n", b"\r\n"))

    expect_failure(
        "crlf-manifest",
        crlf_manifest,
        "is not canonical sorted two-space ASCII JSON",
    )

    def duplicate_manifest_key(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / MANIFEST.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8").replace(
            "{\n", '{\n  "schema_revision": 1,\n', 1
        )
        path.write_text(raw, encoding="utf-8")

    expect_failure(
        "duplicate-manifest-key",
        duplicate_manifest_key,
        "duplicate JSON object key",
    )

    def detached_build_manifest(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        source = path.read_text(encoding="utf-8").replace(
            "identity/software-identity-reference-v1.json",
            "identity/other.json",
            1,
        )
        path.write_text(source, encoding="utf-8")

    expect_failure(
        "detached-build-manifest",
        detached_build_manifest,
        "does not uniquely embed",
    )

    def commented_build_manifest_decoy(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        source = path.read_text(encoding="utf-8").replace(
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";',
            'const IDENTITY_MANIFEST: &str = "identity/other.json";\n'
            '// const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";',
            1,
        )
        path.write_text(source, encoding="utf-8")

    expect_failure(
        "commented-build-manifest-decoy",
        commented_build_manifest_decoy,
        "does not uniquely embed",
    )

    def block_commented_manifest_with_alternate_live_declaration(
        root: Path, value: dict[str, Any]
    ) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        source = path.read_text(encoding="utf-8").replace(
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";',
            '/*\n'
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";\n'
            '*/\n'
            'const IDENTITY_MANIFEST : & str = "identity/other.json";',
            1,
        )
        path.write_text(source, encoding="utf-8")

    expect_failure(
        "block-commented-manifest-with-alternate-live-declaration",
        block_commented_manifest_with_alternate_live_declaration,
        "does not uniquely embed",
    )

    def duplicate_live_manifest_declaration(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        source = path.read_text(encoding="utf-8").replace(
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";',
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";\n'
            'const IDENTITY_MANIFEST: &str = "identity/other.json";',
            1,
        )
        path.write_text(source, encoding="utf-8")

    expect_failure(
        "duplicate-live-manifest-declaration",
        duplicate_live_manifest_declaration,
        "does not uniquely embed",
    )

    def computed_manifest_declaration(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        source = path.read_text(encoding="utf-8").replace(
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";',
            'const IDENTITY_MANIFEST: &str = '
            'concat!("identity/software-identity-reference-v1.json");',
            1,
        )
        path.write_text(source, encoding="utf-8")

    expect_failure(
        "computed-manifest-declaration",
        computed_manifest_declaration,
        "does not uniquely embed",
    )

    def comments_and_strings_around_manifest(root: Path, value: dict[str, Any]) -> None:
        del value
        path = root / "crates/pid-core/build.rs"
        marker = (
            'const IDENTITY_MANIFEST: &str = '
            '"identity/software-identity-reference-v1.json";'
        )
        lexer_fixtures = (
            '/* outer /* nested const IDENTITY_MANIFEST: &str = "identity/other.json"; */ */\n'
            'const STRING_FIXTURE: &str = '
            '"// const IDENTITY_MANIFEST: &str = \\\"identity/other.json\\\";";\n'
            'const RAW_STRING_FIXTURE: &str = '
            'r###"/* const IDENTITY_MANIFEST: &str = "identity/other.json"; */"###;\n'
            "const CHAR_FIXTURE: char = '\\\"';\n"
            "const BYTE_CHAR_FIXTURE: u8 = b'\\\\';\n"
            "fn lifetime_fixture<'a>(value: &'a str) -> &'a str { value }\n"
        )
        path.write_text(
            path.read_text(encoding="utf-8").replace(marker, lexer_fixtures + marker, 1),
            encoding="utf-8",
        )

    expect_success(
        "comments-and-strings-around-manifest",
        comments_and_strings_around_manifest,
    )

    spec = importlib.util.spec_from_file_location("pid_rs_identity_checker", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import identity checker")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    with tempfile.TemporaryDirectory(prefix="pid-rs-identity-symlink-") as raw:
        root = Path(raw)
        target = root / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        link = root / "linked.json"
        link.symlink_to(target)
        try:
            checker.safe_repo_file(root, "linked.json", label="self-test symlink")
        except checker.IdentityError as error:
            if "symlink paths are forbidden" not in str(error):
                raise
            MUTATION_COUNT += 1
        else:
            raise RuntimeError("symlink path mutation unexpectedly passed")

    print(
        f"OK: baseline package inventory passed and {MUTATION_COUNT} software-identity "
        f"mutations were rejected; {PASSING_FIXTURE_COUNT} lexer regression fixture passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
