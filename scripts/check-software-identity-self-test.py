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
    raise SystemExit(
        "check-software-identity-self-test.py requires Python 3.11 or newer"
    )


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-software-identity.py"
MANIFEST = ROOT / "crates/pid-core/identity/software-identity-reference-v1.json"
MUTATION_COUNT = 0
PASSING_FIXTURE_COUNT = 0


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode()


def canonical_write(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def copy_fixture(destination: Path) -> None:
    for relative in [
        "audit/schemas/software-identity-reference.schema.json",
        "crates/pid-core/Cargo.toml",
        "crates/pid-core/build.rs",
        "crates/pid-core/identity/software-identity-reference-v1.json",
        "crates/pid-python/pid_core_rs.pyi",
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


def manifest_mutation(
    function: Callable[[dict[str, Any]], None],
) -> Callable[[Path, dict[str, Any]], None]:
    def apply(root: Path, value: dict[str, Any]) -> None:
        function(value)
        write_manifest(root, value)

    return apply


def pyi_mutation(old: str, new: str) -> Callable[[Path, dict[str, Any]], None]:
    def apply(root: Path, value: dict[str, Any]) -> None:
        path = root / "crates/pid-python/pid_core_rs.pyi"
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise RuntimeError(f"stub fixture does not contain exactly one {old!r}")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
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
        raise RuntimeError(
            f"baseline identity checker failed:\n{baseline.stderr}{baseline.stdout}"
        )

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
        manifest_mutation(
            lambda value: value.update({"attestation": "binary_verified"})
        ),
        "schema validation failed",
    )
    expect_failure(
        "stub-format-literal",
        pyi_mutation(
            "    identity_format: Literal[1]",
            "    identity_format: Literal[2]",
        ),
        "identity Literal _SoftwareIdentity.identity_format mismatch",
    )
    expect_failure(
        "stub-api-epoch-literal",
        pyi_mutation("    epoch: Literal[0]", "    epoch: Literal[1]"),
        "identity Literal _PublicRustApiSignatureIdentity.epoch mismatch",
    )
    expect_failure(
        "stub-api-revision-literal",
        pyi_mutation("    revision: Literal[1]", "    revision: Literal[2]"),
        "identity Literal _PublicRustApiSignatureIdentity.revision mismatch",
    )
    expect_failure(
        "stub-api-scope-literal",
        pyi_mutation(
            '    scope: Literal["proposed_release_scope_profiles"]',
            '    scope: Literal["default_only"]',
        ),
        "identity Literal _PublicRustApiSignatureIdentity.scope mismatch",
    )
    expect_failure(
        "stub-api-status-literal",
        pyi_mutation(
            '    status: Literal["pre_1_0_review"]',
            '    status: Literal["stable_1_x"]',
        ),
        "identity Literal _PublicRustApiSignatureIdentity.status mismatch",
    )
    expect_failure(
        "stub-reference-kind-literal",
        pyi_mutation(
            '    kind: Literal["method_catalog", "proposed_release_scope"]',
            '    kind: Literal["method_catalog"]',
        ),
        "identity Literal _ReferenceArtifactIdentity.kind mismatch",
    )
    expect_failure(
        "stub-reference-schema-revision-literal",
        pyi_mutation(
            "    schema_revision: Literal[1]",
            "    schema_revision: Literal[2]",
        ),
        "identity Literal _ReferenceArtifactIdentity.schema_revision mismatch",
    )
    expect_failure(
        "stub-reference-digest-scope-literal",
        pyi_mutation(
            '    digest_scope: Literal["sha256_of_canonical_file_bytes"]',
            '    digest_scope: Literal["sha256_of_semantic_json"]',
        ),
        "identity Literal _ReferenceArtifactIdentity.digest_scope mismatch",
    )
    expect_failure(
        "stub-reference-role-literal",
        pyi_mutation(
            '    role: Literal["forensic_reference_only"]',
            '    role: Literal["validity_certificate"]',
        ),
        "identity Literal _ReferenceArtifactIdentity.role mismatch",
    )
    expect_failure(
        "stub-attestation-literal",
        pyi_mutation(
            '    attestation: Literal["none"]',
            '    attestation: Literal["binary_verified"]',
        ),
        "identity Literal _SoftwareIdentity.attestation mismatch",
    )
    expect_failure(
        "stub-api-identity-not-typed-dict",
        pyi_mutation(
            "class _PublicRustApiSignatureIdentity(TypedDict):",
            "class _PublicRustApiSignatureIdentity(dict):",
        ),
        "_PublicRustApiSignatureIdentity must inherit exactly from TypedDict",
    )
    expect_failure(
        "stub-build-context-not-typed-dict",
        pyi_mutation(
            "class _BuildContext(TypedDict):",
            "class _BuildContext(dict):",
        ),
        "_BuildContext must inherit exactly from TypedDict",
    )
    expect_failure(
        "stub-envelope-not-typed-dict",
        pyi_mutation(
            "class _SoftwareIdentity(TypedDict):",
            "class _SoftwareIdentity(dict):",
        ),
        "_SoftwareIdentity must inherit exactly from TypedDict",
    )
    expect_failure(
        "stub-envelope-public-api-detached",
        pyi_mutation(
            "    public_rust_api_signature_identity: _PublicRustApiSignatureIdentity",
            "    public_rust_api_signature_identity: dict[str, object]",
        ),
        "_SoftwareIdentity.public_rust_api_signature_identity annotation must be exactly",
    )
    expect_failure(
        "stub-envelope-source-detached",
        pyi_mutation(
            "    source: (\n"
            "        _WorkspaceGitSourceIdentity\n"
            "        | _CargoPackageSourceIdentity\n"
            "        | _UnavailableSourceIdentity\n"
            "    )",
            "    source: object",
        ),
        "_SoftwareIdentity.source annotation must be exactly",
    )
    expect_failure(
        "stub-envelope-build-detached",
        pyi_mutation(
            "    build: _BuildContext",
            "    build: dict[str, object]",
        ),
        "_SoftwareIdentity.build annotation must be exactly",
    )
    expect_failure(
        "stub-envelope-references-detached",
        pyi_mutation(
            "    reference_artifacts: list[_ReferenceArtifactIdentity]",
            "    reference_artifacts: list[dict[str, object]]",
        ),
        "_SoftwareIdentity.reference_artifacts annotation must be exactly",
    )
    expect_failure(
        "stub-workspace-commit-detached",
        pyi_mutation(
            '    kind: Literal["workspace_git"]\n    commit_sha1: str',
            '    kind: Literal["workspace_git"]\n    commit_sha1: int',
        ),
        "_WorkspaceGitSourceIdentity.commit_sha1 annotation must be exactly str",
    )
    expect_failure(
        "stub-unavailable-reason-detached",
        pyi_mutation(
            '        "invalid_git_commit",\n',
            "",
        ),
        "_UnavailableSourceIdentity.reason annotation must be exactly",
    )
    expect_failure(
        "stub-build-features-detached",
        pyi_mutation(
            "    enabled_features: list[str]",
            "    enabled_features: list[object]",
        ),
        "_BuildContext.enabled_features annotation must be exactly list[str]",
    )
    expect_failure(
        "stub-reference-schema-detached",
        pyi_mutation(
            "    schema: str",
            "    schema: object",
        ),
        "_ReferenceArtifactIdentity.schema annotation must be exactly str",
    )
    expect_failure(
        "stub-root-return-detached",
        pyi_mutation(
            "def software_identity() -> _SoftwareIdentity: ...",
            "def software_identity() -> dict[str, object]: ...",
        ),
        "software_identity must return exactly _SoftwareIdentity",
    )
    expect_failure(
        "stub-stable-return-detached",
        pyi_mutation(
            "    def software_identity(self) -> _SoftwareIdentity: ...",
            "    def software_identity(self) -> dict[str, object]: ...",
        ),
        "_StableModule.software_identity must return exactly _SoftwareIdentity",
    )
    expect_failure(
        "stub-root-return-decorated",
        pyi_mutation(
            "def software_identity() -> _SoftwareIdentity: ...",
            "@staticmethod\ndef software_identity() -> _SoftwareIdentity: ...",
        ),
        "software_identity must not have decorators",
    )
    expect_failure(
        "stub-root-return-required-argument",
        pyi_mutation(
            "def software_identity() -> _SoftwareIdentity: ...",
            "def software_identity(required: int) -> _SoftwareIdentity: ...",
        ),
        "software_identity parameters must be exactly ()",
    )
    expect_failure(
        "stub-root-return-varargs",
        pyi_mutation(
            "def software_identity() -> _SoftwareIdentity: ...",
            "def software_identity(*args: object) -> _SoftwareIdentity: ...",
        ),
        "software_identity parameters must be exactly ()",
    )
    expect_failure(
        "stub-root-return-executable-body",
        pyi_mutation(
            "def software_identity() -> _SoftwareIdentity: ...",
            "def software_identity() -> _SoftwareIdentity:\n    raise RuntimeError",
        ),
        "software_identity body must be exactly an ellipsis",
    )
    expect_failure(
        "stub-stable-return-decorated",
        pyi_mutation(
            "    def software_identity(self) -> _SoftwareIdentity: ...",
            "    @staticmethod\n"
            "    def software_identity(self) -> _SoftwareIdentity: ...",
        ),
        "_StableModule.software_identity must not have decorators",
    )
    expect_failure(
        "stub-stable-return-required-argument",
        pyi_mutation(
            "    def software_identity(self) -> _SoftwareIdentity: ...",
            "    def software_identity(self, required: int) -> _SoftwareIdentity: ...",
        ),
        "_StableModule.software_identity parameters must be exactly (self)",
    )
    expect_failure(
        "stub-envelope-decorated",
        pyi_mutation(
            "class _SoftwareIdentity(TypedDict):",
            "@final\nclass _SoftwareIdentity(TypedDict):",
        ),
        "_SoftwareIdentity must inherit exactly from TypedDict",
    )
    expect_failure(
        "stub-envelope-conditional-field",
        pyi_mutation(
            '    attestation: Literal["none"]\n\n\n__version__',
            '    attestation: Literal["none"]\n'
            "    if True:\n"
            "        package_name: object\n\n\n__version__",
        ),
        "_SoftwareIdentity body may contain only its field annotations",
    )
    expect_failure(
        "stub-envelope-rebound",
        pyi_mutation(
            "diagnostics: _DiagnosticsModule\n",
            "diagnostics: _DiagnosticsModule\n_SoftwareIdentity = dict[str, object]\n",
        ),
        "checked stub name _SoftwareIdentity must not be rebound",
    )
    expect_failure(
        "stub-root-return-conditionally-redefined",
        pyi_mutation(
            "diagnostics: _DiagnosticsModule\n",
            "diagnostics: _DiagnosticsModule\n"
            "if True:\n"
            "    def software_identity() -> dict[str, object]: ...\n",
        ),
        "software_identity must have only the checked root and stable definitions",
    )
    expect_failure(
        "stub-typed-dict-shadowed",
        pyi_mutation(
            "from typing import Final, Literal, Self, Sequence, TypedDict, final",
            "from typing import Final, Literal, Self, Sequence, TypedDict, final\n"
            "TypedDict = dict",
        ),
        "checked stub name TypedDict must not be rebound",
    )
    expect_failure(
        "stub-module-type-provenance-detached",
        pyi_mutation(
            "from types import ModuleType",
            "from collections.abc import Callable as ModuleType",
        ),
        "ModuleType must be imported exactly once from types",
    )
    expect_failure(
        "stub-stable-binding-detached",
        pyi_mutation("stable: _StableModule", "stable: ModuleType"),
        "stable must be declared exactly as _StableModule",
    )
    expect_failure(
        "stub-root-return-not-exported",
        pyi_mutation('    "software_identity",\n', ""),
        "__all__ must export software_identity exactly once",
    )
    expect_failure(
        "stub-builtin-shadowed",
        pyi_mutation(
            "diagnostics: _DiagnosticsModule\n",
            "diagnostics: _DiagnosticsModule\nstr = object\n",
        ),
        "checked stub name str must not be rebound",
    )
    expect_failure(
        "wrong-reference-use",
        manifest_mutation(
            lambda value: value.update(
                {"reference_artifact_use": "validity_certificate"}
            )
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
        manifest_mutation(lambda value: value["recognized_cargo_features"].reverse()),
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
                .replace(
                    "default = []\n", "default = []\nidentity-self-test = []\n", 1
                ),
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
        artifact = json.loads(
            (root / "method-catalog.json").read_text(encoding="utf-8")
        )
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
        value["reference_artifacts"][0]["canonical_json_sha256"] = hashlib.sha256(
            raw
        ).hexdigest()
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
            "/*\n"
            'const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";\n'
            "*/\n"
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
            "const IDENTITY_MANIFEST: &str = "
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
            "const IDENTITY_MANIFEST: &str = "
            '"identity/software-identity-reference-v1.json";'
        )
        lexer_fixtures = (
            '/* outer /* nested const IDENTITY_MANIFEST: &str = "identity/other.json"; */ */\n'
            "const STRING_FIXTURE: &str = "
            '"// const IDENTITY_MANIFEST: &str = \\"identity/other.json\\";";\n'
            "const RAW_STRING_FIXTURE: &str = "
            'r###"/* const IDENTITY_MANIFEST: &str = "identity/other.json"; */"###;\n'
            "const CHAR_FIXTURE: char = '\\\"';\n"
            "const BYTE_CHAR_FIXTURE: u8 = b'\\\\';\n"
            "fn lifetime_fixture<'a>(value: &'a str) -> &'a str { value }\n"
        )
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                marker, lexer_fixtures + marker, 1
            ),
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
