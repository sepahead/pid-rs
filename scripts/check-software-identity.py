#!/usr/bin/env python3
"""Validate pid-core's embedded, package-safe software identity reference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-software-identity.py requires Python 3.11 or newer")

import tomllib

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = Path("crates/pid-core/identity/software-identity-reference-v1.json")
DEFAULT_SCHEMA = Path("audit/schemas/software-identity-reference.schema.json")
DEFAULT_CARGO = Path("crates/pid-core/Cargo.toml")
EXPECTED_ARTIFACTS = (
    ("method_catalog", "method-catalog.json", "pid-rs/method-catalog", 1),
    (
        "proposed_release_scope",
        "release-scope-1.0.json",
        "pid-rs/release-scope",
        1,
    ),
)
REQUIRED_PACKAGE_FILES = {
    "build.rs",
    "build_support.rs",
    "identity/software-identity-reference-v1.json",
    "src/identity.rs",
    "tests/software_identity.rs",
    "tests/software_identity_build.rs",
}


class IdentityError(RuntimeError):
    """The embedded identity, referenced artifacts, or package inventory disagree."""


RustToken = tuple[str, str]


def _raw_string_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust raw-string token beginning at ``start``, if present."""

    for prefix in ("br", "cr", "r"):
        if not source.startswith(prefix, start):
            continue
        cursor = start + len(prefix)
        while cursor < len(source) and source[cursor] == "#":
            cursor += 1
        if cursor >= len(source) or source[cursor] != '"':
            continue
        terminator = '"' + "#" * (cursor - start - len(prefix))
        end = source.find(terminator, cursor + 1)
        if end < 0:
            raise IdentityError("build.rs contains an unterminated raw string literal")
        end += len(terminator)
        return ("raw_string", source[start:end]), end
    return None


def _quoted_string_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust quoted string/byte-string token beginning at ``start``."""

    prefix_length = 1 if source.startswith(("b\"", "c\""), start) else 0
    quote = start + prefix_length
    if quote >= len(source) or source[quote] != '"':
        return None
    cursor = quote + 1
    while cursor < len(source):
        if source[cursor] == "\\":
            cursor += 2
            continue
        if source[cursor] == '"':
            end = cursor + 1
            return ("string", source[start:end]), end
        cursor += 1
    raise IdentityError("build.rs contains an unterminated string literal")


def _quoted_char_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust character/byte-character token beginning at ``start``."""

    prefix_length = 1 if source.startswith("b'", start) else 0
    quote = start + prefix_length
    if quote >= len(source) or source[quote] != "'":
        return None
    cursor = quote + 1
    if cursor >= len(source):
        return None

    if source[cursor] == "\\":
        cursor += 1
        if cursor >= len(source):
            return None
        escape = source[cursor]
        if escape == "x":
            cursor += 3
        elif escape == "u" and source.startswith("u{", cursor):
            closing_brace = source.find("}", cursor + 2)
            if closing_brace < 0:
                return None
            cursor = closing_brace + 1
        else:
            cursor += 1
    else:
        if source[cursor] in {"'", "\r", "\n"}:
            return None
        cursor += 1

    if cursor >= len(source) or source[cursor] != "'":
        # This was a lifetime such as `'a`, not a character literal.
        return None
    end = cursor + 1
    return ("char", source[start:end]), end


def rust_source_tokens(source: str) -> list[RustToken]:
    """Tokenize the Rust subset needed to identify a live const declaration.

    Rust line comments and nested block comments are discarded. Character,
    quoted-string, and raw-string literals remain single tokens, so
    declaration-shaped text inside them cannot be mistaken for code.
    """

    tokens: list[RustToken] = []
    cursor = 0
    while cursor < len(source):
        if source[cursor].isspace():
            cursor += 1
            continue
        if source.startswith("//", cursor):
            newline = source.find("\n", cursor + 2)
            cursor = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", cursor):
            depth = 1
            cursor += 2
            while cursor < len(source) and depth:
                if source.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif source.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise IdentityError("build.rs contains an unterminated block comment")
            continue

        raw_string = _raw_string_token(source, cursor)
        if raw_string is not None:
            token, cursor = raw_string
            tokens.append(token)
            continue
        quoted_string = _quoted_string_token(source, cursor)
        if quoted_string is not None:
            token, cursor = quoted_string
            tokens.append(token)
            continue
        quoted_char = _quoted_char_token(source, cursor)
        if quoted_char is not None:
            token, cursor = quoted_char
            tokens.append(token)
            continue

        if (
            source.startswith("r#", cursor)
            and cursor + 2 < len(source)
            and (source[cursor + 2].isalpha() or source[cursor + 2] == "_")
        ):
            end = cursor + 3
            while end < len(source) and (
                source[end].isalnum() or source[end] == "_"
            ):
                end += 1
            tokens.append(("raw_ident", source[cursor + 2 : end]))
            cursor = end
            continue
        if source[cursor].isalpha() or source[cursor] == "_":
            end = cursor + 1
            while end < len(source) and (
                source[end].isalnum() or source[end] == "_"
            ):
                end += 1
            tokens.append(("ident", source[cursor:end]))
            cursor = end
            continue

        tokens.append(("punct", source[cursor]))
        cursor += 1
    return tokens


def validate_build_manifest_declaration(source: str, expected_value: str) -> None:
    """Require one live, literal ``IDENTITY_MANIFEST`` const declaration."""

    tokens = rust_source_tokens(source)
    bindings: list[tuple[int, str]] = []
    for index, (kind, value) in enumerate(tokens):
        if kind not in {"ident", "raw_ident"} or value != "IDENTITY_MANIFEST":
            continue
        previous = index - 1
        while previous >= 0 and tokens[previous] in {
            ("ident", "mut"),
            ("ident", "ref"),
        }:
            previous -= 1
        if previous >= 0 and tokens[previous] in {
            ("ident", "const"),
            ("ident", "static"),
            ("ident", "let"),
        }:
            bindings.append((previous, tokens[previous][1]))

    expected_tokens: list[RustToken] = [
        ("ident", "const"),
        ("ident", "IDENTITY_MANIFEST"),
        ("punct", ":"),
        ("punct", "&"),
        ("ident", "str"),
        ("punct", "="),
        ("string", f'"{expected_value}"'),
        ("punct", ";"),
    ]
    if len(bindings) != 1 or bindings[0][1] != "const":
        raise IdentityError(
            "build.rs does not uniquely embed the checked software-identity manifest"
        )
    declaration_start = bindings[0][0]
    if tokens[declaration_start : declaration_start + len(expected_tokens)] != expected_tokens:
        raise IdentityError(
            "build.rs does not uniquely embed the checked software-identity manifest"
        )


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise IdentityError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def load_json(path: Path, *, canonical: bool = False) -> Any:
    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IdentityError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw_bytes != expected.encode("ascii"):
            raise IdentityError(
                f"{path} is not canonical sorted two-space ASCII JSON with one final LF"
            )
    return value


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise IdentityError(f"{label}: path must be a non-empty repository-relative string")
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise IdentityError(f"{label}: unsafe repository path {relative!r}")
    current = root
    for component in relative_path.parts:
        current = current / component
        if current.is_symlink():
            raise IdentityError(f"{label}: symlink paths are forbidden: {relative!r}")
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise IdentityError(
            f"{label}: file is missing or escapes the repository: {relative!r}"
        ) from error
    if not resolved.is_file():
        raise IdentityError(f"{label}: expected a regular file: {relative!r}")
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cargo_features(path: Path) -> list[str]:
    try:
        with path.open("rb") as handle:
            cargo = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise IdentityError(f"cannot read {path}: {error}") from error
    features = cargo.get("features")
    if not isinstance(features, dict):
        raise IdentityError("pid-core Cargo features table is missing")
    names = sorted(features)
    if features.get("default") != []:
        raise IdentityError("pid-core default features must remain empty")
    normalized: dict[str, str] = {}
    for feature in names:
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", feature) is None:
            raise IdentityError(
                f"Cargo feature name is outside the identity grammar: {feature!r}"
            )
        env_name = "CARGO_FEATURE_" + feature.upper().replace("-", "_")
        previous = normalized.setdefault(env_name, feature)
        if previous != feature:
            raise IdentityError(
                f"Cargo feature environment-name collision: {previous!r} and {feature!r}"
            )

    optional_dependencies: set[str] = set()

    def collect_optional(table: Any) -> None:
        if not isinstance(table, dict):
            return
        for name, specification in table.items():
            if isinstance(specification, dict) and specification.get("optional") is True:
                optional_dependencies.add(name)

    collect_optional(cargo.get("dependencies"))
    targets = cargo.get("target", {})
    if isinstance(targets, dict):
        for target in targets.values():
            if isinstance(target, dict):
                collect_optional(target.get("dependencies"))

    explicit_optional_dependencies = {
        item.removeprefix("dep:")
        for members in features.values()
        if isinstance(members, list)
        for item in members
        if isinstance(item, str) and item.startswith("dep:")
    }
    missing_dep_prefix = sorted(optional_dependencies - explicit_optional_dependencies)
    if missing_dep_prefix:
        raise IdentityError(
            "optional pid-core dependencies must use explicit dep: feature edges: "
            + ", ".join(missing_dep_prefix)
        )
    return names


def package_files(root: Path) -> set[str]:
    process = subprocess.run(
        [
            "cargo",
            "package",
            "--locked",
            "--allow-dirty",
            "--no-verify",
            "--list",
            "-p",
            "pid-core",
        ],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise IdentityError(f"cargo package --list failed: {detail}")
    return {line.strip() for line in process.stdout.splitlines() if line.strip()}


def validate_identity(
    *,
    root: Path,
    manifest_path: Path,
    schema_path: Path,
    cargo_path: Path,
    check_package: bool,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    expected_paths = {
        "software identity manifest": DEFAULT_MANIFEST,
        "software identity schema": DEFAULT_SCHEMA,
        "pid-core Cargo manifest": DEFAULT_CARGO,
    }
    supplied_paths = {
        "software identity manifest": manifest_path,
        "software identity schema": schema_path,
        "pid-core Cargo manifest": cargo_path,
    }
    checked_paths: dict[str, Path] = {}
    for label, expected_relative in expected_paths.items():
        supplied = supplied_paths[label]
        try:
            supplied_relative = supplied.absolute().relative_to(root).as_posix()
        except ValueError as error:
            raise IdentityError(f"{label}: path is outside the repository") from error
        if supplied_relative != expected_relative.as_posix():
            raise IdentityError(
                f"{label}: expected {expected_relative.as_posix()!r}, "
                f"got {supplied_relative!r}"
            )
        checked_paths[label] = safe_repo_file(root, supplied_relative, label=label)
    manifest_path = checked_paths["software identity manifest"]
    schema_path = checked_paths["software identity schema"]
    cargo_path = checked_paths["pid-core Cargo manifest"]

    manifest = load_json(manifest_path, canonical=True)
    schema = load_json(schema_path, canonical=True)
    try:
        validate_json_schema(manifest, schema, name="software identity reference")
    except SchemaValidationError as error:
        raise IdentityError(f"software identity schema validation failed: {error}") from error

    expected_features = cargo_features(cargo_path)
    if manifest["recognized_cargo_features"] != expected_features:
        raise IdentityError(
            "recognized Cargo feature inventory disagrees with pid-core Cargo.toml: "
            f"expected={expected_features!r}, "
            f"got={manifest['recognized_cargo_features']!r}"
        )

    artifacts = manifest["reference_artifacts"]
    for index, expected in enumerate(EXPECTED_ARTIFACTS):
        artifact = artifacts[index]
        kind, relative, artifact_schema, schema_revision = expected
        actual_identity = (
            artifact["kind"],
            artifact["repository_path"],
            artifact["schema"],
            artifact["schema_revision"],
        )
        if actual_identity != expected:
            raise IdentityError(
                f"reference_artifacts[{index}] identity mismatch: "
                f"expected={expected!r}, got={actual_identity!r}"
            )
        path = safe_repo_file(root, relative, label=f"reference artifact {kind}")
        referenced = load_json(path, canonical=True)
        if referenced.get("schema") != artifact_schema:
            raise IdentityError(
                f"{relative}: schema identity disagrees with embedded reference"
            )
        if referenced.get("schema_revision") != schema_revision:
            raise IdentityError(
                f"{relative}: schema revision disagrees with embedded reference"
            )
        actual_digest = sha256_file(path)
        if artifact["canonical_json_sha256"] != actual_digest:
            raise IdentityError(
                f"{relative}: SHA-256 mismatch: expected {actual_digest}, "
                f"got {artifact['canonical_json_sha256']}"
            )

    build_source = safe_repo_file(root, "crates/pid-core/build.rs", label="build script")
    source_text = build_source.read_text(encoding="utf-8")
    manifest_relative = manifest_path.resolve(strict=True).relative_to(root).as_posix()
    expected_value = Path(manifest_relative).relative_to("crates/pid-core").as_posix()
    validate_build_manifest_declaration(source_text, expected_value)

    if check_package:
        packaged = package_files(root)
        missing = sorted(REQUIRED_PACKAGE_FILES - packaged)
        if missing:
            raise IdentityError(
                "pid-core package omits required identity files: " + ", ".join(missing)
            )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--skip-package-list",
        action="store_true",
        help="skip Cargo package inventory (intended only for isolated mutation fixtures)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    manifest = root / DEFAULT_MANIFEST
    schema = root / DEFAULT_SCHEMA
    cargo = root / DEFAULT_CARGO
    try:
        value = validate_identity(
            root=root,
            manifest_path=manifest,
            schema_path=schema,
            cargo_path=cargo,
            check_package=not args.skip_package_list,
        )
    except (IdentityError, ValueError) as error:
        print(f"software identity error: {error}", file=sys.stderr)
        return 1
    print(
        "OK: software identity format "
        f"{value['identity_format']}, {len(value['recognized_cargo_features'])} Cargo "
        f"features, and {len(value['reference_artifacts'])} forensic references are coherent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
