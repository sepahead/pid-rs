#!/usr/bin/env python3
"""Validate and render the pid-rs 1.0 public claim/symbol inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from typing import Any

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCOPE = ROOT / "release-scope-1.0.json"
DEFAULT_MARKDOWN = ROOT / "RELEASE_SCOPE_1_0.md"
DEFAULT_SCHEMA = ROOT / "audit/schemas/release-scope.schema.json"
DEFAULT_SIGNATURE_REGISTRY = (
    ROOT / "audit/api/public-api/pid-core-signature-revisions.json"
)
DEFAULT_SIGNATURE_REGISTRY_SCHEMA = (
    ROOT / "audit/schemas/public-rust-api-signature-revisions.schema.json"
)
DEFAULT_SOFTWARE_IDENTITY_REFERENCE = (
    ROOT / "crates/pid-core/identity/software-identity-reference-v1.json"
)
DEFAULT_LIB_RS = ROOT / "crates/pid-core/src/lib.rs"
DEFAULT_CARGO = ROOT / "crates/pid-core/Cargo.toml"
SCHEMA = "pid-rs/release-scope"
SCHEMA_REVISION = 1
API_SNAPSHOT_SOURCE = {
    "commit_sha": "633d4e2e77f7c74ff6e34054fd005706069ed7f8",
    "tree_sha": "70a233b7c4225a81e5eef78af7ffba13ce057108",
    "host_triple": "aarch64-apple-darwin",
    "rustdoc_target_triple": "aarch64-apple-darwin",
    "snapshot_format": "cargo-public-api simplified level 3, color disabled",
    "tool": "cargo-public-api 0.52.0",
    "toolchain": "rustc 1.98.0-nightly (01dfd7924 2026-06-15)",
}
SIGNATURE_REGISTRY_SCHEMA = "pid-rs/public-rust-api-signature-revisions"
SIGNATURE_REGISTRY_SCHEMA_REVISION = 1
SIGNATURE_REGISTRY_PATH = "audit/api/public-api/pid-core-signature-revisions.json"
SIGNATURE_SNAPSHOT_ROOT = "audit/api/public-api/revisions"
SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT = "633d4e2e77f7c74ff6e34054fd005706069ed7f8"
SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE = "70a233b7c4225a81e5eef78af7ffba13ce057108"
SIGNATURE_GENERATION_FIELDS = (
    "host_triple",
    "rustdoc_target_triple",
    "snapshot_format",
    "tool",
    "toolchain",
)
EXPECTED_MAINTAINER = "Sepehr Mahmoudian"
STABILITIES = {"stable", "experimental", "research-only", "unsupported"}
CLAIM_STATUSES = {
    "not_claimed",
    "claimed_pending",
    "qualified",
    "operationally_validated",
}
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MODULE_RE_TEMPLATE = r"\bpub\s+mod\s+{name}\s*\{{"
MODULE_FEATURES = {
    "experimental::continuous": "experimental-continuous",
    "experimental::continuous::raw_scalars": "experimental-continuous",
    "experimental::isx_heuristics": "experimental-heuristics",
    "experimental::mixed_dimension_pid3": "research-mixed-dimension-pid3",
    "experimental::hyperbolic": "experimental-hyperbolic",
    "experimental::hierarchy": "experimental-hierarchy",
    "experimental::pipelines": "experimental-pipelines",
}


class ScopeError(RuntimeError):
    """The machine scope, source exports, or rendered view disagree."""


GIT_ENVIRONMENT_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_ATTR_NOSYSTEM",
    "GIT_ATTR_SOURCE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_EXEC_PATH",
    "GIT_GLOB_PATHSPECS",
    "GIT_GRAFT_FILE",
    "GIT_ICASE_PATHSPECS",
    "GIT_INDEX_FILE",
    "GIT_INDEX_VERSION",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_LITERAL_PATHSPECS",
    "GIT_NAMESPACE",
    "GIT_NOGLOB_PATHSPECS",
    "GIT_NO_LAZY_FETCH",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_QUARANTINE_PATH",
    "GIT_REFERENCE_BACKEND",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_SUPER_PREFIX",
    "GIT_WORK_TREE",
}
GIT_ENVIRONMENT_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


def scrubbed_git_environment() -> dict[str, str]:
    """Return a deterministic read-only Git environment for repository evidence."""

    environment = dict(os.environ)
    for name in tuple(environment):
        if name in GIT_ENVIRONMENT_KEYS or name.startswith(GIT_ENVIRONMENT_PREFIXES):
            environment.pop(name)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def read_utf8_with_sha256(
    path: Path,
    *,
    label: str,
    observations: dict[Path, tuple[str, str]],
) -> tuple[str, str]:
    """Decode and hash exactly one byte observation, cached by resolved path."""

    resolved = path.resolve(strict=True)
    cached = observations.get(resolved)
    if cached is not None:
        return cached
    try:
        raw = resolved.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ScopeError(
            f"{label}: cannot read UTF-8 snapshot bytes: {error}"
        ) from error
    observed = (text, hashlib.sha256(raw).hexdigest())
    observations[resolved] = observed
    return observed


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScopeError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def reject_non_finite_json_constant(token: str) -> None:
    """Reject Python's non-standard JSON spellings for non-finite numbers."""

    raise ScopeError(f"non-finite JSON number is forbidden: {token}")


def load_json(path: Path, *, canonical: bool = False) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ScopeError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw != expected:
            raise ScopeError(
                f"{path} is not canonical sorted two-space JSON with one final LF"
            )
    return value


def load_json_with_sha256(path: Path, *, canonical: bool = False) -> tuple[Any, str]:
    """Parse and hash one immutable byte observation of a JSON artifact."""

    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ScopeError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw != expected:
            raise ScopeError(
                f"{path} is not canonical sorted two-space JSON with one final LF"
            )
    return value, hashlib.sha256(raw_bytes).hexdigest()


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ScopeError(
            f"{label}: path must be a non-empty repository-relative string"
        )
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise ScopeError(f"{label}: unsafe repository path {relative!r}")
    candidate = root / candidate_relative
    current = root
    for component in candidate_relative.parts:
        current = current / component
        if current.is_symlink():
            raise ScopeError(f"{label}: symlink paths are forbidden: {relative!r}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ScopeError(
            f"{label}: file is missing or escapes the repository: {relative!r}"
        ) from error
    if not resolved.is_file():
        raise ScopeError(f"{label}: expected a regular file: {relative!r}")
    return resolved


def git_output(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ScopeError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def git_commit_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    """Return Git ancestry without a shell; distinguish 'not ancestor' from Git failure."""

    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode == 0:
        return True
    if process.returncode == 1:
        return False
    detail = process.stderr.strip() or process.stdout.strip()
    raise ScopeError(
        f"git merge-base --is-ancestor failed for {ancestor} and {descendant}: {detail}"
    )


def validate_git_repository_context(root: Path) -> None:
    """Require Git's own worktree root to be the canonical repository being checked."""

    try:
        expected_root = root.resolve(strict=True)
        reported_root = Path(git_output(root, "rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as error:
        raise ScopeError(
            f"cannot resolve release-scope Git worktree root: {error}"
        ) from error
    if reported_root != expected_root:
        raise ScopeError(
            "release-scope Git worktree root mismatch: "
            f"expected {expected_root}, got {reported_root}"
        )


def checkout_path_history_commits(
    root: Path, relative: str, *, touch_label: str
) -> list[tuple[str, str]]:
    """Return HEAD boundaries and full-history touch witnesses for one path."""

    head = git_output(root, "rev-parse", "HEAD^{commit}")
    fields = git_output(root, "rev-list", "--parents", "-n", "1", head).split()
    if (
        not fields
        or fields[0] != head
        or any(not re.fullmatch(r"[0-9a-f]{40}", item) for item in fields)
    ):
        raise ScopeError(
            "cannot resolve exact HEAD and direct-parent history boundaries"
        )

    candidates = [("HEAD", head)]
    candidates.extend(
        (f"HEAD^{parent_index}", parent)
        for parent_index, parent in enumerate(fields[1:], start=1)
    )
    touched_raw = git_output(
        root,
        "rev-list",
        "--full-history",
        head,
        "--",
        relative,
    )
    touched = touched_raw.splitlines() if touched_raw else []
    if any(not re.fullmatch(r"[0-9a-f]{40}", commit) for commit in touched):
        raise ScopeError(f"cannot resolve exact {touch_label} history boundaries")
    candidates.extend(
        (f"{touch_label}[{index}]", commit) for index, commit in enumerate(touched)
    )

    commits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, commit in candidates:
        if commit not in seen:
            commits.append((label, commit))
            seen.add(commit)
    return commits


def checkout_history_commits(root: Path) -> list[tuple[str, str]]:
    """Return bounded witnesses for every relevant HEAD-reachable registry state."""

    return checkout_path_history_commits(
        root,
        SIGNATURE_REGISTRY_PATH,
        touch_label="registry-touch",
    )


def git_file_bytes_at_commit(root: Path, commit: str, relative: str) -> bytes | None:
    """Read exact tracked bytes, returning ``None`` when the path did not yet exist."""

    listed = git_output(root, "ls-tree", "--name-only", commit, "--", relative)
    if not listed:
        return None
    if listed != relative:
        raise ScopeError(f"unexpected Git tree result for {relative!r}: {listed!r}")
    process = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ScopeError(f"cannot read {relative!r} at {commit}: {detail}")
    return process.stdout


def git_file_at_commit(root: Path, commit: str, relative: str) -> str | None:
    """Read one tracked UTF-8 file, returning ``None`` when the path did not yet exist."""

    raw = git_file_bytes_at_commit(root, commit, relative)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ScopeError(f"{relative!r} at {commit} is not UTF-8") from error


def load_canonical_json_text(raw: str, *, label: str) -> Any:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except json.JSONDecodeError as error:
        raise ScopeError(f"cannot parse {label}: {error}") from error
    expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if raw != expected:
        raise ScopeError(
            f"{label} is not canonical sorted two-space JSON with one final LF"
        )
    return value


def sanitize_rust(source: str) -> str:
    """Replace comments and literals with spaces while preserving positions/newlines."""

    output = list(source)
    index = 0
    length = len(source)

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if output[position] != "\n":
                output[position] = " "

    while index < length:
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            if end == -1:
                end = length
            blank(index, end)
            index = end
            continue
        if source.startswith("/*", index):
            start = index
            depth = 1
            index += 2
            while index < length and depth:
                if source.startswith("/*", index):
                    depth += 1
                    index += 2
                elif source.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth:
                raise ScopeError("unterminated Rust block comment")
            blank(start, index)
            continue

        raw = re.match(r'(?:br|r)(#{0,255})"', source[index:])
        if raw:
            hashes = raw.group(1)
            start = index
            index += raw.end()
            terminator = '"' + hashes
            end = source.find(terminator, index)
            if end == -1:
                raise ScopeError("unterminated Rust raw string")
            index = end + len(terminator)
            blank(start, index)
            continue

        if source[index] == '"' or (
            source[index] == "b" and index + 1 < length and source[index + 1] == '"'
        ):
            start = index
            if source[index] == "b":
                index += 1
            index += 1
            escaped = False
            while index < length:
                character = source[index]
                index += 1
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    break
            else:
                raise ScopeError("unterminated Rust string")
            blank(start, index)
            continue

        if source[index] == "'":
            # Lifetimes (`'a`) are syntax, while short quoted forms are char literals.
            char_match = re.match(r"'(?:\\.|[^\\'\n])'", source[index:])
            if char_match:
                start = index
                index += char_match.end()
                blank(start, index)
                continue
        index += 1

    return "".join(output)


class RustModuleExports:
    def __init__(self, source: str) -> None:
        self.source = source
        self.sanitized = sanitize_rust(source)
        self.depths = self._brace_depths()
        self.brace_pairs = self._brace_pairs()

    def _brace_depths(self) -> list[int]:
        depths = [0] * (len(self.sanitized) + 1)
        depth = 0
        for index, character in enumerate(self.sanitized):
            depths[index] = depth
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth < 0:
                    raise ScopeError("unbalanced Rust closing brace")
        depths[len(self.sanitized)] = depth
        if depth:
            raise ScopeError("unbalanced Rust opening brace")
        return depths

    def _brace_pairs(self) -> dict[int, int]:
        stack: list[int] = []
        pairs: dict[int, int] = {}
        for index, character in enumerate(self.sanitized):
            if character == "{":
                stack.append(index)
            elif character == "}":
                if not stack:
                    raise ScopeError("unbalanced Rust closing brace")
                pairs[stack.pop()] = index
        if stack:
            raise ScopeError("unbalanced Rust opening brace")
        return pairs

    def module_span(self, module: str) -> tuple[int, int, int]:
        if module == "crate":
            return 0, len(self.source), 0
        start = 0
        end = len(self.source)
        direct_depth = 0
        for component in module.split("::"):
            if not IDENTIFIER_RE.fullmatch(component):
                raise ScopeError(f"invalid Rust module component: {component!r}")
            pattern = re.compile(MODULE_RE_TEMPLATE.format(name=re.escape(component)))
            match = next(
                (
                    candidate
                    for candidate in pattern.finditer(self.sanitized, start, end)
                    if self.depths[candidate.start()] == direct_depth
                ),
                None,
            )
            if match is None:
                raise ScopeError(f"public inline module {module!r} is missing")
            opening = self.sanitized.find("{", match.start(), match.end())
            closing = self.brace_pairs[opening]
            start = opening + 1
            end = closing
            direct_depth += 1
        return start, end, direct_depth

    @staticmethod
    def _split_top_level(value: str) -> list[str]:
        items = []
        start = 0
        depth = 0
        for index, character in enumerate(value):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            elif character == "," and depth == 0:
                items.append(value[start:index])
                start = index + 1
        items.append(value[start:])
        return [item.strip() for item in items if item.strip()]

    @classmethod
    def _use_names(cls, value: str) -> list[str]:
        value = value.strip()
        if "*" in value:
            raise ScopeError(
                f"glob re-exports are forbidden in the frozen API: {value}"
            )
        opening = value.find("{")
        if opening != -1:
            closing = value.rfind("}")
            if closing < opening:
                raise ScopeError(f"malformed pub use tree: {value}")
            names: list[str] = []
            for item in cls._split_top_level(value[opening + 1 : closing]):
                names.extend(cls._use_names(item))
            return names
        alias = re.search(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", value)
        if alias:
            return [alias.group(1)]
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", value)
        if not identifiers:
            raise ScopeError(f"cannot identify exported name in: {value}")
        if identifiers[-1] == "self" and len(identifiers) >= 2:
            return [identifiers[-2]]
        return [identifiers[-1]]

    def symbols(self, module: str) -> list[str]:
        start, end, direct_depth = self.module_span(module)
        function = r"(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?(?:extern\s+)?fn"
        declaration = re.compile(
            rf"\bpub\s+(use|extern\s+crate|{function}|const|static|type|struct|enum|union|trait|macro)\b"
        )
        symbols: list[str] = []
        for match in declaration.finditer(self.sanitized, start, end):
            if self.depths[match.start()] != direct_depth:
                continue
            kind = match.group(1)
            normalized_kind = " ".join(kind.split())
            if normalized_kind in {"use", "extern crate"}:
                semicolon = next(
                    (
                        index
                        for index in range(match.end(), end)
                        if self.sanitized[index] == ";"
                        and self.depths[index] == direct_depth
                    ),
                    None,
                )
                if semicolon is None:
                    raise ScopeError(f"unterminated pub use in {module}")
                value = self.source[match.end() : semicolon]
                if normalized_kind == "extern crate":
                    alias = re.search(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", value)
                    if alias:
                        symbols.append(alias.group(1))
                    else:
                        name = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", value)
                        if name is None:
                            raise ScopeError(
                                f"cannot parse public extern crate in {module}"
                            )
                        symbols.append(name.group(1))
                else:
                    symbols.extend(self._use_names(value))
            else:
                name_match = re.match(
                    r"\s*([A-Za-z_][A-Za-z0-9_]*)", self.sanitized[match.end() :]
                )
                if name_match is None:
                    raise ScopeError(f"cannot parse public {kind} in {module}")
                symbols.append(name_match.group(1))
        if module == "crate":
            # `#[macro_export] macro_rules!` is public at the crate root even when its physical
            # declaration is nested. It has no `pub` token, so inventory it explicitly.
            exported_macro = re.compile(
                r"#\s*\[\s*macro_export(?:\s*\([^\]]*\))?\s*\]"
                r"(?:\s*#\s*\[[^\]]*\])*\s*"
                r"macro_rules\s*!\s*([A-Za-z_][A-Za-z0-9_]*)"
            )
            symbols.extend(
                match.group(1) for match in exported_macro.finditer(self.sanitized)
            )
        duplicates = sorted(name for name in set(symbols) if symbols.count(name) > 1)
        if duplicates:
            raise ScopeError(
                f"duplicate direct exports in {module}: {', '.join(duplicates)}"
            )
        return sorted(symbols)

    def child_modules(self, module: str) -> list[str]:
        start, end, direct_depth = self.module_span(module)
        # Include out-of-line declarations (`pub mod name;`). They are not used by the frozen
        # facade, but silently omitting them would let an unscoped public module evade this check.
        # If one is ever added to the declared module tree, `module_span` will fail closed because
        # this parser intentionally inventories only the authoritative inline facade in lib.rs.
        declaration = re.compile(r"\bpub\s+mod\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\{;]")
        modules = [
            match.group(1)
            for match in declaration.finditer(self.sanitized, start, end)
            if self.depths[match.start()] == direct_depth
        ]
        duplicates = sorted(name for name in set(modules) if modules.count(name) > 1)
        if duplicates:
            raise ScopeError(
                f"duplicate public modules in {module}: {', '.join(duplicates)}"
            )
        return sorted(modules)


def validate_stable_profile_diff(
    profile_id: str,
    active_features: set[str],
    default_snapshot: str,
    profile_snapshot: str,
    conditional_members: list[dict[str, Any]],
) -> None:
    """Require the exact stable-namespace delta for one complete activation profile."""

    expected_added = {
        member["added_api_line"]
        for member in conditional_members
        if member["feature"] in active_features
    }
    expected_removed = {
        member["removed_api_line"]
        for member in conditional_members
        if member["feature"] in active_features
        and member["removed_api_line"] is not None
    }
    default_stable_lines = stable_namespace_lines(default_snapshot)
    profile_stable_lines = stable_namespace_lines(profile_snapshot)
    actual_added = profile_stable_lines - default_stable_lines
    actual_removed = default_stable_lines - profile_stable_lines
    if actual_added != expected_added or actual_removed != expected_removed:
        raise ScopeError(
            f"{profile_id}: stable-namespace diff disagrees with conditional_members; "
            f"unlisted added={sorted(actual_added - expected_added)!r}; "
            f"stale added={sorted(expected_added - actual_added)!r}; "
            f"unlisted removed={sorted(actual_removed - expected_removed)!r}; "
            f"stale removed={sorted(expected_removed - actual_removed)!r}"
        )


def feature_closure(features: dict[str, list[str]], requested: list[str]) -> list[str]:
    closure: set[str] = set()
    stack = list(requested)
    while stack:
        feature = stack.pop()
        if feature in closure:
            continue
        if feature not in features:
            raise ScopeError(f"unknown Cargo feature in scope: {feature}")
        closure.add(feature)
        for dependency in features[feature]:
            if dependency.startswith("dep:") or "/" in dependency:
                continue
            stack.append(dependency)
    return sorted(closure)


PID_PATH_RE = re.compile(r"pid_core(?:::[A-Za-z_][A-Za-z0-9_]*)*")
IMPL_RE = re.compile(r"^impl\b")


def is_experimental_pid_path(path: str) -> bool:
    return path == "pid_core::experimental" or path.startswith(
        "pid_core::experimental::"
    )


def impl_trait_and_self_subject(api_line: str) -> str:
    """Remove ``impl`` generics and trailing bounds from a normalized impl line."""

    subject = api_line[4:].lstrip()
    if subject.startswith("<"):
        depth = 0
        for index, character in enumerate(subject):
            if character == "<":
                depth += 1
            elif character == ">":
                depth -= 1
                if depth == 0:
                    subject = subject[index + 1 :].lstrip()
                    break
        else:
            return ""
    return subject.split(" where ", 1)[0]


def primary_pid_path(api_line: str) -> str | None:
    """Return the namespace-classifying pid-core path from one public-API line."""

    subject = (
        impl_trait_and_self_subject(api_line) if IMPL_RE.match(api_line) else api_line
    )
    matches = list(PID_PATH_RE.finditer(subject))
    if not matches:
        return None
    if IMPL_RE.match(api_line):
        # An impl contributes to both its trait and self type. Treat it as stable when
        # either side names a non-experimental pid-core path, including ``impl<T>`` forms.
        for match in matches:
            if not is_experimental_pid_path(match.group(0)):
                return match.group(0)
    return matches[0].group(0)


def stable_namespace_lines(snapshot: str) -> set[str]:
    lines: set[str] = set()
    for line in snapshot.splitlines():
        path = primary_pid_path(line)
        if path is None:
            continue
        if is_experimental_pid_path(path):
            continue
        lines.add(line)
    return lines


def validate_signature_registry_genesis(
    snapshot_source: dict[str, Any], *, historical_registry_present: bool
) -> None:
    """Permit a missing historical registry only at the immutable revision-1 source."""

    if historical_registry_present:
        return
    source = (snapshot_source.get("commit_sha"), snapshot_source.get("tree_sha"))
    genesis = (
        SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT,
        SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE,
    )
    if source != genesis:
        raise ScopeError(
            "a missing historical signature registry is permitted only at the immutable genesis source"
        )


def profile_signature(entry: dict[str, Any]) -> tuple[tuple[Any, Any], ...]:
    """Return declaration-signature identity, deliberately excluding storage paths."""

    profiles = entry.get("profiles", [])
    return tuple(
        (profile.get("id"), profile.get("public_api_snapshot_sha256"))
        for profile in profiles
        if isinstance(profile, dict)
    )


def signature_transition_is_meaningful(
    previous: dict[str, Any], current: dict[str, Any]
) -> bool:
    return (
        profile_signature(previous) != profile_signature(current)
        or previous.get("epoch") != current.get("epoch")
        or previous.get("scope") != current.get("scope")
        or previous.get("status") != current.get("status")
    )


def validate_signature_registry_extension(
    entries: list[dict[str, Any]],
    historical_entries: list[dict[str, Any]],
    *,
    history_label: str = "historical registry",
) -> None:
    """Require a first record or one exact append after a preserved historical prefix."""

    if not historical_entries:
        if len(entries) != 1:
            raise ScopeError(
                "the first signature registry update must contain exactly revision 1"
            )
        return
    validate_signature_registry_prefix(
        entries,
        historical_entries,
        history_label=history_label,
    )
    if len(entries) == len(historical_entries):
        return
    if len(entries) != len(historical_entries) + 1:
        raise ScopeError(
            "a signature evidence transition must append at most one contiguous registry entry"
        )
    historical_latest = historical_entries[-1]
    latest = entries[-1]
    if not signature_transition_is_meaningful(historical_latest, latest):
        raise ScopeError(
            "a pure signature revision-number bump without a profile, scope, status, or epoch change is forbidden"
        )


def validate_signature_registry_prefix(
    entries: list[dict[str, Any]],
    historical_entries: list[dict[str, Any]],
    *,
    history_label: str,
) -> None:
    """Require an exact retained prefix without limiting later append count."""

    if (
        len(entries) < len(historical_entries)
        or entries[: len(historical_entries)] != historical_entries
    ):
        raise ScopeError(
            f"signature registry does not preserve the {history_label} entry prefix"
        )


def signature_snapshot_directory(epoch: int, revision: int) -> str:
    return f"{SIGNATURE_SNAPSHOT_ROOT}/{epoch}-{revision}"


def validate_signature_registry_header(
    registry: dict[str, Any], historical: dict[str, Any], *, history_label: str
) -> None:
    for field in (
        "append_policy",
        "genesis_source_commit_sha",
        "genesis_source_tree_sha",
        "package",
        "schema",
        "schema_revision",
    ):
        if registry.get(field) != historical.get(field):
            raise ScopeError(
                f"signature registry header changed at {field} relative to {history_label}"
            )


def validate_signature_registry_history_text(
    registry: dict[str, Any],
    raw: str,
    *,
    registry_schema: Any,
    history_label: str,
) -> dict[str, Any]:
    historical = load_canonical_json_text(raw, label=history_label)
    try:
        validate_json_schema(
            historical,
            registry_schema,
            name=f"signature registry at {history_label}",
        )
    except SchemaValidationError as error:
        raise ScopeError(
            f"historical signature registry JSON Schema validation failed at {history_label}: {error}"
        ) from error
    validate_signature_registry_header(
        registry,
        historical,
        history_label=history_label,
    )
    validate_signature_registry_prefix(
        registry["entries"],
        historical["entries"],
        history_label=history_label,
    )
    return historical


def validate_signature_registry_historical_lineage(
    histories: dict[str, tuple[str, dict[str, Any] | None]], *, root: Path
) -> None:
    """Reject deletion, truncation, or rewrite across comparable retained baselines."""

    items = list(histories.items())
    for ancestor_commit, (ancestor_label, ancestor_registry) in items:
        for descendant_commit, (descendant_label, descendant_registry) in items:
            if ancestor_commit == descendant_commit or not git_commit_is_ancestor(
                root, ancestor_commit, descendant_commit
            ):
                continue
            if ancestor_registry is None:
                continue
            if descendant_registry is None:
                raise ScopeError(
                    "signature registry was deleted between comparable history boundaries: "
                    f"{ancestor_label} -> {descendant_label}"
                )
            ancestor_entries = ancestor_registry["entries"]
            descendant_entries = descendant_registry["entries"]
            if (
                len(descendant_entries) < len(ancestor_entries)
                or descendant_entries[: len(ancestor_entries)] != ancestor_entries
            ):
                raise ScopeError(
                    "signature registry history contains a truncation or rewrite between "
                    f"{ancestor_label} and {descendant_label}"
                )


def registry_snapshot_bindings(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Return the unique immutable path-to-digest bindings in registry entries."""

    bindings: dict[str, str] = {}
    for entry in entries:
        for profile in entry["profiles"]:
            relative = profile["public_api_snapshot"]
            digest = profile["public_api_snapshot_sha256"]
            prior = bindings.get(relative)
            if prior is not None and prior != digest:
                raise ScopeError(
                    f"signature snapshot path {relative!r} has conflicting registry digests"
                )
            bindings[relative] = digest
    return bindings


def validate_signature_snapshot_history(
    entries: list[dict[str, Any]],
    *,
    histories: dict[str, tuple[str, dict[str, Any] | None]],
    root: Path,
) -> None:
    """Reject any reachable snapshot mutation after its first committed binding."""

    for relative, expected_digest in registry_snapshot_bindings(entries).items():
        binding_commits: list[tuple[str, str]] = []
        for commit, (label, historical_registry) in histories.items():
            if historical_registry is None:
                continue
            historical_bindings = registry_snapshot_bindings(
                historical_registry["entries"]
            )
            if historical_bindings.get(relative) == expected_digest:
                binding_commits.append((label, commit))

        # A path first bound by the working-tree registry has no committed binding yet. Its
        # checked-out bytes were validated above; earlier path history remains pre-binding.
        if not binding_commits:
            continue

        candidates = [(f"{label} binding", commit) for label, commit in binding_commits]
        candidates.extend(
            checkout_path_history_commits(
                root,
                relative,
                touch_label="snapshot-touch",
            )
        )
        seen: set[str] = set()
        for label, commit in candidates:
            if commit in seen:
                continue
            seen.add(commit)
            binding_label = next(
                (
                    candidate_label
                    for candidate_label, binding_commit in binding_commits
                    if git_commit_is_ancestor(root, binding_commit, commit)
                ),
                None,
            )
            if binding_label is None:
                continue
            raw = git_file_bytes_at_commit(root, commit, relative)
            if raw is None:
                raise ScopeError(
                    f"immutable signature snapshot {relative!r} was absent after registry "
                    f"binding {binding_label} at {label} {commit}"
                )
            observed_digest = hashlib.sha256(raw).hexdigest()
            if observed_digest != expected_digest:
                raise ScopeError(
                    f"immutable signature snapshot {relative!r} changed after registry "
                    f"binding {binding_label} at {label} {commit}: expected "
                    f"{expected_digest}, got {observed_digest}"
                )


def validate_signature_registry_entries(
    entries: list[dict[str, Any]],
    *,
    root: Path,
    observations: dict[Path, tuple[str, str]],
) -> None:
    """Validate sequence, immutable bytes, source identity, and source ancestry."""

    validate_git_repository_context(root)
    shallow = git_output(root, "rev-parse", "--is-shallow-repository")
    if shallow not in {"true", "false"}:
        raise ScopeError(f"unexpected Git shallow-repository state: {shallow!r}")
    if shallow == "true":
        raise ScopeError(
            "signature registry ancestry requires a complete, non-shallow Git history"
        )
    head = git_output(root, "rev-parse", "HEAD^{commit}")
    previous_key: tuple[int, int] | None = None
    previous_entry: dict[str, Any] | None = None
    previous_source: str | None = None
    path_bindings: dict[str, str] = {}
    for index, entry in enumerate(entries):
        epoch = entry.get("epoch")
        revision = entry.get("revision")
        if (
            not isinstance(epoch, int)
            or isinstance(epoch, bool)
            or epoch < 0
            or not isinstance(revision, int)
            or isinstance(revision, bool)
            or revision < 1
        ):
            raise ScopeError(
                f"signature registry entry {index}: epoch must be non-negative and revision positive integers"
            )
        key = (epoch, revision)
        if previous_key is None:
            if key != (0, 1):
                raise ScopeError(
                    "signature revision registry must begin at epoch 0 revision 1"
                )
        else:
            same_epoch_next = key == (previous_key[0], previous_key[1] + 1)
            next_epoch_first = key == (previous_key[0] + 1, 1)
            if not (same_epoch_next or next_epoch_first):
                raise ScopeError(
                    "signature revision entries must be contiguous by epoch and revision"
                )
            assert previous_entry is not None
            if not signature_transition_is_meaningful(previous_entry, entry):
                raise ScopeError(
                    f"signature registry entry {index}: pure revision-number bumps are forbidden"
                )
        previous_key = key

        profiles = entry.get("profiles")
        if not isinstance(profiles, list):
            raise ScopeError(
                f"signature registry entry {index}: profiles must be an array"
            )
        profile_ids = [item.get("id") for item in profiles if isinstance(item, dict)]
        if len(profile_ids) != len(profiles) or profile_ids != sorted(set(profile_ids)):
            raise ScopeError(
                f"signature registry entry {index}: profiles must have sorted unique ids"
            )

        expected_directory = signature_snapshot_directory(epoch, revision)
        for profile in profiles:
            profile_id = profile["id"]
            relative = profile["public_api_snapshot"]
            if Path(relative).parent.as_posix() != expected_directory:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: snapshot path must be in {expected_directory}"
                )
            declared_digest = profile["public_api_snapshot_sha256"]
            prior_digest = path_bindings.get(relative)
            # Identical profiles may intentionally share one immutable file. Any conflicting
            # binding for the same path remains invalid.
            if prior_digest is not None and prior_digest != declared_digest:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: shared snapshot path has conflicting digests"
                )
            path_bindings[relative] = declared_digest
            snapshot_path = safe_repo_file(
                root,
                relative,
                label=f"signature registry entry {index} profile {profile_id} snapshot",
            )
            _, observed_digest = read_utf8_with_sha256(
                snapshot_path,
                label=f"signature registry entry {index} profile {profile_id} snapshot",
                observations=observations,
            )
            if observed_digest != declared_digest:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: retained snapshot digest mismatch"
                )

        commit = entry.get("snapshot_source_commit_sha")
        tree = entry.get("snapshot_source_tree_sha")
        if git_output(root, "rev-parse", f"{commit}^{{commit}}") != commit:
            raise ScopeError(
                f"signature registry entry {index}: source commit is not exact"
            )
        if git_output(root, "rev-parse", f"{commit}^{{tree}}") != tree:
            raise ScopeError(
                f"signature registry entry {index}: source tree does not match its commit"
            )
        if not git_commit_is_ancestor(root, commit, head):
            raise ScopeError(
                f"signature registry entry {index}: source commit is not an ancestor of HEAD"
            )
        if previous_source is not None and not git_commit_is_ancestor(
            root, previous_source, commit
        ):
            raise ScopeError(
                f"signature registry entry {index}: source commits are not monotone by ancestry"
            )
        if (
            previous_entry is not None
            and previous_source == commit
            and previous_entry.get("generation") == entry.get("generation")
            and profile_signature(previous_entry) != profile_signature(entry)
        ):
            raise ScopeError(
                f"signature registry entry {index}: unchanged source and generation cannot produce a different declaration signature"
            )
        previous_source = commit
        previous_entry = entry


def validate_signature_revision_registry(
    scope: dict[str, Any],
    *,
    registry: Any,
    registry_path: Path,
    registry_sha256: str,
    registry_schema: Any,
    identity_reference: Any,
    root: Path,
    observations: dict[Path, tuple[str, str]],
) -> None:
    """Bind the runtime signature revision to exact, append-only snapshot evidence."""

    try:
        validate_json_schema(
            registry,
            registry_schema,
            name="pid-core-signature-revisions.json",
        )
    except SchemaValidationError as error:
        raise ScopeError(
            f"signature registry JSON Schema validation failed: {error}"
        ) from error

    pointer = scope.get("public_rust_api_signature_revision_registry")
    if not isinstance(pointer, dict):
        raise ScopeError(
            "public Rust API signature revision registry pointer is missing"
        )
    expected_pointer = {
        "repository_path": SIGNATURE_REGISTRY_PATH,
        "schema": SIGNATURE_REGISTRY_SCHEMA,
        "schema_revision": SIGNATURE_REGISTRY_SCHEMA_REVISION,
    }
    for field, expected in expected_pointer.items():
        if pointer.get(field) != expected:
            raise ScopeError(
                f"signature registry pointer {field} mismatch: "
                f"expected {expected!r}, got {pointer.get(field)!r}"
            )
    if registry_path == DEFAULT_SIGNATURE_REGISTRY:
        safe_repo_file(
            root,
            pointer["repository_path"],
            label="public Rust API signature revision registry",
        )
    if registry_sha256 != pointer.get("canonical_json_sha256"):
        raise ScopeError("public Rust API signature revision registry digest mismatch")
    if (
        registry.get("schema") != SIGNATURE_REGISTRY_SCHEMA
        or registry.get("schema_revision") != SIGNATURE_REGISTRY_SCHEMA_REVISION
    ):
        raise ScopeError("unsupported public Rust API signature revision registry")
    if (
        registry.get("genesis_source_commit_sha")
        != SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT
        or registry.get("genesis_source_tree_sha")
        != SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE
    ):
        raise ScopeError("signature registry genesis source changed")

    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ScopeError("signature revision registry must contain at least one entry")
    validate_signature_registry_entries(
        entries,
        root=root,
        observations=observations,
    )

    latest = entries[-1]
    identity = (
        identity_reference.get("api_signature_identity")
        if isinstance(identity_reference, dict)
        else None
    )
    latest_identity = {
        field: latest.get(field) for field in ("epoch", "revision", "scope", "status")
    }
    if identity != latest_identity:
        raise ScopeError(
            "embedded software identity does not equal the latest signature revision entry"
        )

    snapshot_source = scope["api_snapshot_source"]
    if (
        latest.get("snapshot_source_commit_sha") != snapshot_source["commit_sha"]
        or latest.get("snapshot_source_tree_sha") != snapshot_source["tree_sha"]
    ):
        raise ScopeError(
            "latest signature revision source does not equal api_snapshot_source"
        )
    expected_generation = {
        field: snapshot_source[field] for field in SIGNATURE_GENERATION_FIELDS
    }
    if latest.get("generation") != expected_generation:
        raise ScopeError(
            "latest signature revision generation metadata does not equal api_snapshot_source"
        )
    expected_profiles = sorted(
        (
            {
                "id": profile["id"],
                "public_api_snapshot": profile["public_api_snapshot"],
                "public_api_snapshot_sha256": profile["public_api_snapshot_sha256"],
            }
            for profile in scope["feature_profiles"]
        ),
        key=lambda item: item["id"],
    )
    if latest.get("profiles") != expected_profiles:
        raise ScopeError(
            "latest signature revision profile evidence does not exactly match feature_profiles"
        )

    # The source commit precedes the evidence update. The history witnesses also include HEAD,
    # every direct HEAD parent, and every HEAD-reachable commit reported by Git's full path history
    # for the registry. Deduplication keeps the work bounded to relevant commit states.
    history_candidates = [
        ("api_snapshot_source", snapshot_source["commit_sha"]),
        *checkout_history_commits(root),
    ]
    history_requests: list[tuple[str, str]] = []
    requested_commits: set[str] = set()
    for history_name, history_commit in history_candidates:
        if history_commit not in requested_commits:
            history_requests.append((history_name, history_commit))
            requested_commits.add(history_commit)
    raw_by_commit: dict[str, str | None] = {}
    for _, history_commit in history_requests:
        if history_commit not in raw_by_commit:
            raw_by_commit[history_commit] = git_file_at_commit(
                root,
                history_commit,
                SIGNATURE_REGISTRY_PATH,
            )

    historical_raw = raw_by_commit[snapshot_source["commit_sha"]]
    validate_signature_registry_genesis(
        snapshot_source,
        historical_registry_present=historical_raw is not None,
    )

    # Every retained state must be a prefix of the checked-out registry. Comparable historical
    # states must preserve one another too, which exposes buried drops, rewrites, and divergent
    # merge-side reissues instead of checking only the checkout tip.
    histories: dict[str, tuple[str, dict[str, Any] | None]] = {}
    for history_name, history_commit in history_requests:
        history_label = f"{history_name} {history_commit}"
        history_raw = raw_by_commit[history_commit]
        if history_raw is None:
            histories.setdefault(history_commit, (history_label, None))
            continue
        historical_registry = validate_signature_registry_history_text(
            registry,
            history_raw,
            registry_schema=registry_schema,
            history_label=f"{SIGNATURE_REGISTRY_PATH} at {history_label}",
        )
        histories.setdefault(history_commit, (history_label, historical_registry))
    validate_signature_registry_historical_lineage(histories, root=root)
    validate_signature_snapshot_history(entries, histories=histories, root=root)

    # The source-to-evidence and committed-HEAD-to-working-tree boundaries each permit no more
    # than one append. Older path-history witnesses may legitimately be several revisions behind.
    transition_commits = [snapshot_source["commit_sha"]]
    head_commit = git_output(root, "rev-parse", "HEAD^{commit}")
    if head_commit not in transition_commits:
        transition_commits.append(head_commit)
    for transition_commit in transition_commits:
        transition_label, transition_registry = histories[transition_commit]
        validate_signature_registry_extension(
            entries,
            [] if transition_registry is None else transition_registry["entries"],
            history_label=transition_label,
        )


def validate_scope(
    scope: Any,
    *,
    schema: Any,
    lib_rs: Path,
    cargo_toml: Path,
    signature_registry: Any,
    signature_registry_path: Path,
    signature_registry_sha256: str,
    signature_registry_schema: Any,
    identity_reference: Any,
    root: Path,
) -> None:
    if not isinstance(scope, dict):
        raise ScopeError("scope root must be an object")
    try:
        validate_json_schema(scope, schema, name="release-scope-1.0.json")
    except SchemaValidationError as error:
        raise ScopeError(f"JSON Schema validation failed: {error}") from error
    if scope.get("schema") != SCHEMA or scope.get("schema_revision") != SCHEMA_REVISION:
        raise ScopeError("unsupported release-scope schema")
    if scope.get("release") != "1.0.0":
        raise ScopeError("release scope must identify 1.0.0")
    blockers = scope.get("acceptance_blockers")
    if (
        not isinstance(blockers, list)
        or not blockers
        or any(not isinstance(item, str) or not item for item in blockers)
    ):
        raise ScopeError(
            "acceptance_blockers must disclose at least one concrete blocker"
        )

    families = scope.get("families")
    if not isinstance(families, list) or not families:
        raise ScopeError("families must be a non-empty array")
    family_ids: set[str] = set()
    expected_by_module: dict[str, set[str]] = {}
    for family in families:
        if not isinstance(family, dict):
            raise ScopeError("every family must be an object")
        family_id = family.get("id")
        if not isinstance(family_id, str) or not family_id or family_id in family_ids:
            raise ScopeError(f"family id must be unique and non-empty: {family_id!r}")
        family_ids.add(family_id)
        if family.get("software_stability") not in STABILITIES:
            raise ScopeError(f"{family_id}: invalid software_stability")
        module = family.get("public_module")
        if not isinstance(module, str) or not module:
            raise ScopeError(f"{family_id}: public_module is required")
        symbols = family.get("symbols")
        if (
            not isinstance(symbols, list)
            or any(
                not isinstance(symbol, str) or not IDENTIFIER_RE.fullmatch(symbol)
                for symbol in symbols
            )
            or symbols != sorted(set(symbols))
        ):
            raise ScopeError(
                f"{family_id}: symbols must be sorted unique Rust identifiers"
            )
        overlap = expected_by_module.setdefault(module, set()).intersection(symbols)
        if overlap:
            raise ScopeError(
                f"{family_id}: symbols assigned twice within {module}: {', '.join(sorted(overlap))}"
            )
        expected_by_module[module].update(symbols)
        expected_feature = MODULE_FEATURES.get(module)
        stability = family["software_stability"]
        if stability == "stable":
            if expected_feature is not None or family.get("cargo_feature") is not None:
                raise ScopeError(
                    f"{family_id}: stable families cannot require research features"
                )
            if family.get("semver_1x") is not True:
                raise ScopeError(
                    f"{family_id}: stable families must enter the proposed 1.x SemVer scope"
                )
        elif stability in {"experimental", "research-only"}:
            if (
                family.get("cargo_feature") != expected_feature
                or expected_feature is None
            ):
                raise ScopeError(
                    f"{family_id}: feature label disagrees with its public module"
                )
            if family.get("semver_1x") is not False:
                raise ScopeError(
                    f"{family_id}: research/experimental symbols cannot enter the proposed 1.x SemVer scope"
                )
        if str(family.get("definition_revision", "")).startswith("multiple-") or str(
            family.get("estimator_revision", "")
        ).startswith("multiple-"):
            raise ScopeError(
                f"{family_id}: definition and estimator revisions must be unambiguous"
            )
        for field in (
            "mathematical_family",
            "definition_revision",
            "estimator_revision",
            "support_domain",
            "required_provenance",
            "known_failure_states",
            "rust_exposure",
            "python_exposure",
            "intended_ecosystem_consumers",
            "semver_1x",
        ):
            if field not in family:
                raise ScopeError(f"{family_id}: missing {field}")

    parser = RustModuleExports(lib_rs.read_text(encoding="utf-8"))

    public_modules = scope.get("public_modules")
    if (
        not isinstance(public_modules, list)
        or public_modules != sorted(set(public_modules))
        or any(not isinstance(module, str) or not module for module in public_modules)
    ):
        raise ScopeError(
            "public_modules must be a sorted unique non-empty string array"
        )
    family_modules = {family["public_module"] for family in families} - {"crate"}
    if family_modules - set(public_modules):
        raise ScopeError(
            "family modules absent from public_modules: "
            + ", ".join(sorted(family_modules - set(public_modules)))
        )
    expected_children: dict[str, set[str]] = {"crate": set()}
    for module in public_modules:
        parent, separator, child = module.rpartition("::")
        expected_children.setdefault(parent if separator else "crate", set()).add(
            child if separator else module
        )
        expected_children.setdefault(module, set())
    for parent, expected in sorted(expected_children.items()):
        actual = set(parser.child_modules(parent))
        if actual != expected:
            details = []
            if actual - expected:
                details.append(
                    "unscoped public modules: " + ", ".join(sorted(actual - expected))
                )
            if expected - actual:
                details.append(
                    "missing public modules: " + ", ".join(sorted(expected - actual))
                )
            raise ScopeError(f"{parent}: " + "; ".join(details))

    # Every public facade module is checked, including structural parents such as `stable` and
    # `experimental`. Parent modules may be symbol-empty without their own family row, but a direct
    # export added there must never remain unassigned.
    modules_to_check = set(public_modules) | {"crate"}
    for module in sorted(modules_to_check):
        expected = expected_by_module.get(module, set())
        actual = set(parser.symbols(module))
        added = sorted(actual - expected)
        missing = sorted(expected - actual)
        if added or missing:
            details = []
            if added:
                details.append("unscoped exports: " + ", ".join(added))
            if missing:
                details.append("missing exports: " + ", ".join(missing))
            raise ScopeError(f"{module}: " + "; ".join(details))

    snapshot_source = scope.get("api_snapshot_source", {})
    if snapshot_source != API_SNAPSHOT_SOURCE:
        differences = [
            f"{field}: expected {API_SNAPSHOT_SOURCE[field]!r}, got {snapshot_source.get(field)!r}"
            for field in API_SNAPSHOT_SOURCE
            if snapshot_source.get(field) != API_SNAPSHOT_SOURCE[field]
        ]
        raise ScopeError(
            "api snapshot source is not the frozen source: " + "; ".join(differences)
        )
    source_commit = snapshot_source.get("commit_sha")
    source_tree = snapshot_source.get("tree_sha")
    if git_output(root, "rev-parse", f"{source_commit}^{{commit}}") != source_commit:
        raise ScopeError("api snapshot source commit does not resolve to itself")
    if git_output(root, "rev-parse", f"{source_commit}^{{tree}}") != source_tree:
        raise ScopeError("api snapshot source tree does not match its commit")

    with cargo_toml.open("rb") as handle:
        cargo = tomllib.load(handle)
    features = cargo.get("features")
    if not isinstance(features, dict):
        raise ScopeError("pid-core Cargo features table is missing")
    normalized_features = {
        name: list(values)
        for name, values in features.items()
        if isinstance(values, list)
    }
    if normalized_features.get("default") != []:
        raise ScopeError("pid-core default features must remain empty")

    profiles = scope.get("feature_profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ScopeError("feature_profiles must be a non-empty array")
    profile_ids: set[str] = set()
    requested_single_features: set[str] = set()
    snapshot_text_by_id: dict[str, str] = {}
    snapshot_observations: dict[Path, tuple[str, str]] = {}
    expected_profile_ids = {
        "pid-core-default",
        "pid-core-all-features",
        *(
            f"pid-core-{feature}"
            for feature in normalized_features
            if feature != "default"
        ),
    }
    for profile in profiles:
        profile_id = profile.get("id")
        if (
            not isinstance(profile_id, str)
            or not profile_id
            or profile_id in profile_ids
        ):
            raise ScopeError(f"feature profile id must be unique: {profile_id!r}")
        profile_ids.add(profile_id)
        requested = profile.get("requested_features")
        if not isinstance(requested, list) or requested != sorted(set(requested)):
            raise ScopeError(
                f"{profile_id}: requested_features must be sorted and unique"
            )
        all_features = profile.get("all_features")
        if not isinstance(all_features, bool):
            raise ScopeError(f"{profile_id}: all_features must be Boolean")
        if all_features:
            if profile_id != "pid-core-all-features" or requested:
                raise ScopeError(
                    "only pid-core-all-features may activate --all-features"
                )
            actual_closure = sorted(normalized_features)
        else:
            actual_closure = feature_closure(normalized_features, requested)
        expected_arguments = [
            "--package",
            "pid-core",
            "--no-default-features",
            "-sss",
            "--color",
            "never",
        ]
        if all_features:
            expected_arguments.append("--all-features")
        elif requested:
            expected_arguments.extend(["--features", ",".join(requested)])
        if profile.get("generation_arguments") != expected_arguments:
            raise ScopeError(
                f"{profile_id}: cargo-public-api generation arguments mismatch"
            )
        if profile.get("feature_closure") != actual_closure:
            raise ScopeError(
                f"{profile_id}: feature closure mismatch: expected {actual_closure!r}"
            )
        if not all_features and len(requested) == 1:
            requested_single_features.add(requested[0])
        snapshot_path = safe_repo_file(
            root,
            profile.get("public_api_snapshot"),
            label=f"{profile_id} public API snapshot",
        )
        snapshot, observed_digest = read_utf8_with_sha256(
            snapshot_path,
            label=f"{profile_id} public API snapshot",
            observations=snapshot_observations,
        )
        if observed_digest != profile.get("public_api_snapshot_sha256"):
            raise ScopeError(f"{profile_id}: public API snapshot digest mismatch")
        snapshot_text_by_id[profile_id] = snapshot
        for forbidden in profile.get("forbidden_public_paths", []):
            if forbidden in snapshot:
                raise ScopeError(
                    f"{profile_id}: forbidden public path is present: {forbidden}"
                )
        for required in profile.get("required_public_paths", []):
            if required not in snapshot:
                raise ScopeError(
                    f"{profile_id}: required public path is absent: {required}"
                )

    if profile_ids != expected_profile_ids:
        raise ScopeError(
            "feature profile set mismatch; missing="
            + ",".join(sorted(expected_profile_ids - profile_ids))
            + "; unexpected="
            + ",".join(sorted(profile_ids - expected_profile_ids))
        )

    research_features = set(normalized_features) - {
        "default",
        "parallel",
        "experimental-all",
    }
    if research_features - requested_single_features:
        raise ScopeError(
            "missing individual feature profiles: "
            + ", ".join(sorted(research_features - requested_single_features))
        )

    conditional = scope.get("conditional_members")
    if not isinstance(conditional, list):
        raise ScopeError("conditional_members must be an array")
    conditional_paths: set[str] = set()
    profile_by_feature = {
        profile["requested_features"][0]: profile
        for profile in profiles
        if len(profile["requested_features"]) == 1
    }
    default_profile = next(
        (profile for profile in profiles if profile["id"] == "pid-core-default"), None
    )
    if default_profile is None:
        raise ScopeError("a default/no-default feature profile is required")
    default_snapshot = snapshot_text_by_id[default_profile["id"]]
    for member in conditional:
        path = member.get("public_path")
        feature = member.get("feature")
        if not isinstance(path, str) or not path or path in conditional_paths:
            raise ScopeError(f"conditional public_path must be unique: {path!r}")
        conditional_paths.add(path)
        if member.get("stable_namespace_leak") is not True:
            raise ScopeError(
                f"{path}: conditional members must disclose stable_namespace_leak"
            )
        profile = profile_by_feature.get(feature)
        if profile is None:
            raise ScopeError(f"{path}: no individual profile for feature {feature!r}")
        feature_snapshot = snapshot_text_by_id[profile["id"]]
        added_line = member.get("added_api_line")
        removed_line = member.get("removed_api_line")
        if not isinstance(added_line, str) or not added_line:
            raise ScopeError(f"{path}: exact added_api_line is required")
        if added_line in default_snapshot or added_line not in feature_snapshot:
            raise ScopeError(
                f"{path}: exact added API line disagrees with compiled snapshots"
            )
        if removed_line is not None:
            if not isinstance(removed_line, str) or not removed_line:
                raise ScopeError(f"{path}: removed_api_line must be null or non-empty")
            if removed_line not in default_snapshot or removed_line in feature_snapshot:
                raise ScopeError(
                    f"{path}: exact removed API line disagrees with compiled snapshots"
                )

    # Check complete activation profiles, not only one-feature requests. This catches public API
    # that appears under `cfg(all(feature = ...))` and would otherwise be invisible in every
    # individual feature comparison.
    for profile in profiles:
        validate_stable_profile_diff(
            profile["id"],
            set(profile["feature_closure"]),
            default_snapshot,
            snapshot_text_by_id[profile["id"]],
            conditional,
        )

    validate_signature_revision_registry(
        scope,
        registry=signature_registry,
        registry_path=signature_registry_path,
        registry_sha256=signature_registry_sha256,
        registry_schema=signature_registry_schema,
        identity_reference=identity_reference,
        root=root,
        observations=snapshot_observations,
    )

    integrations = scope.get("integration_claims")
    required_integrations = {
        "prisoma",
        "galadriel",
        "crebain",
        "external-authority",
        "haldir",
    }
    if not isinstance(integrations, list):
        raise ScopeError("integration_claims must be an array")
    integration_ids = {item.get("integration_id") for item in integrations}
    if integration_ids != required_integrations:
        raise ScopeError(
            "integration_claims must name every optional downstream integration"
        )
    for integration in integrations:
        if integration.get("claim_status") not in CLAIM_STATUSES:
            raise ScopeError(f"invalid integration claim status: {integration!r}")
        if integration.get("claim_status") != "not_claimed":
            raise ScopeError(
                f"{integration['integration_id']}: this core-only candidate must remain not_claimed"
            )

    prohibited = scope.get("prohibited_claims")
    if not isinstance(prohibited, list) or len(prohibited) < 8:
        raise ScopeError("at least eight explicit prohibited 1.0 claims are required")

    approvals = scope.get("review_approvals")
    required_roles = {"maintainer", "independent_scientific_reviewer"}
    if (
        not isinstance(approvals, list)
        or {item.get("role") for item in approvals} != required_roles
    ):
        raise ScopeError(
            "review_approvals must name maintainer and independent reviewer roles"
        )
    reviewers_by_role: dict[str, str] = {}
    for approval in approvals:
        status = approval.get("status")
        if status not in {"pending", "approved", "rejected"}:
            raise ScopeError(f"invalid review approval status: {approval!r}")
        if approval.get("commit_binding") != "api_snapshot_source_commit":
            raise ScopeError(f"{approval['role']}: unsupported approval commit binding")
        role = approval["role"]
        detail_fields = (
            "reviewer",
            "commit_sha",
            "evidence",
            "conflict_disclosure",
        )
        approval_details = {field: approval.get(field) for field in detail_fields}
        independence = approval.get("independence_statement")

        commit_sha = approval.get("commit_sha")
        if commit_sha is not None:
            if git_output(root, "rev-parse", f"{commit_sha}^{{commit}}") != commit_sha:
                raise ScopeError(f"{role}: review commit does not resolve to itself")
            if commit_sha != source_commit:
                raise ScopeError(
                    f"{role}: review commit must equal the frozen api_snapshot_source commit"
                )
        evidence = approval.get("evidence")
        if evidence is not None:
            safe_repo_file(root, evidence, label=f"{role} review evidence")

        if status == "pending":
            if any(
                value is not None
                for value in (*approval_details.values(), independence)
            ):
                raise ScopeError(f"{role}: pending review fields must all remain null")
            continue

        if any(
            not isinstance(value, str) or not value
            for value in approval_details.values()
        ):
            raise ScopeError(
                f"{role}: a decided review requires reviewer, commit, evidence, and conflict disclosure"
            )
        reviewer = approval_details["reviewer"]
        reviewers_by_role[role] = reviewer
        if role == "maintainer":
            if reviewer != EXPECTED_MAINTAINER:
                raise ScopeError(
                    f"maintainer review must be recorded by {EXPECTED_MAINTAINER}"
                )
            if independence is not None:
                raise ScopeError(
                    "maintainer review independence_statement must be null"
                )
        else:
            if reviewer == EXPECTED_MAINTAINER:
                raise ScopeError("independent reviewer cannot be the maintainer/author")
            if not isinstance(independence, str) or not independence:
                raise ScopeError(
                    "independent reviewer decision requires an independence_statement"
                )

    if len(set(reviewers_by_role.values())) != len(reviewers_by_role):
        raise ScopeError("maintainer and independent reviewer must be different people")


def markdown_cell(value: Any) -> str:
    if isinstance(value, list):
        rendered = "; ".join(str(item) for item in value)
    elif isinstance(value, bool):
        rendered = "yes" if value else "no"
    elif value is None:
        rendered = "—"
    else:
        rendered = str(value)
    return rendered.replace("|", "\\|").replace("\n", " ")


def render_markdown(scope: dict[str, Any], signature_registry: dict[str, Any]) -> str:
    lines = [
        "# pid-rs 1.0 release scope",
        "",
        "> **Scope state:** proposed 1.0 boundary for external review. The software publication",
        "> target is 0.9.0 first. This document does not claim 1.0 publication, registry availability,",
        "> independent acceptance, application validity, or a 1.x compatibility promise.",
        "",
        "The machine-readable source is `release-scope-1.0.json`. The scope checker regenerates",
        "this rendered view; the coherence job also rebuilds every compiled API profile and rejects",
        "unlisted `pid-core` exports/modules, stable-namespace drift, feature-closure changes, snapshot",
        "changes, schema violations, or ambiguous integration status.",
        "",
        "Enabling a research feature changes only software availability. It does **not** promote",
        "scientific maturity, widen support, establish calibration, or create a 1.x SemVer promise.",
        "",
        "## Capability matrix",
        "",
        "| ID | Public module | Cargo feature | Stability | Mathematical family / definition | Estimator revision | Support domain | Required provenance | Known failures | Rust | Python | Intended consumers | Proposed 1.x SemVer scope |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for family in scope["families"]:
        lines.append(
            "| {id} | `{module}` | {feature} | {stability} | {math} / `{definition}` | `{estimator}` | {support} | {provenance} | {failures} | {rust} | {python} | {consumers} | {semver} |".format(
                id=family["id"],
                module=family["public_module"],
                feature=markdown_cell(family["cargo_feature"]),
                stability=family["software_stability"],
                math=markdown_cell(family["mathematical_family"]),
                definition=family["definition_revision"],
                estimator=family["estimator_revision"],
                support=markdown_cell(family["support_domain"]),
                provenance=markdown_cell(family["required_provenance"]),
                failures=markdown_cell(family["known_failure_states"]),
                rust=markdown_cell(family["rust_exposure"]),
                python=markdown_cell(family["python_exposure"]),
                consumers=markdown_cell(family["intended_ecosystem_consumers"]),
                semver=markdown_cell(family["semver_1x"]),
            )
        )

    lines.extend(["", "## Exact public symbols", ""])
    for family in scope["families"]:
        lines.extend(
            [
                f"### `{family['id']}`",
                "",
                f"Module: `{family['public_module']}`. Export count: {len(family['symbols'])}.",
                "",
                "```text",
                *family["symbols"],
                "```",
                "",
            ]
        )

    conditional_members = scope["conditional_members"]
    if conditional_members:
        lines.extend(
            [
                "## Known stable-namespace leaks that block API freeze",
                "",
                "These members appear only when a research feature is enabled but mutate types also",
                "exported through stable/top-level paths. They are recorded as blockers, not approved",
                "1.x stable API. They must move behind a research-only type or entry point before the",
                "1.x API can freeze.",
                "",
                "| Public path | Feature | Kind | Removed default signature | 1.x promise |",
                "|---|---|---|---|---|",
            ]
        )
        for member in conditional_members:
            lines.append(
                f"| `{member['public_path']}` | `{member['feature']}` | {member['kind']} | {markdown_cell(member['removed_api_line'])} | no |"
            )
    else:
        lines.extend(
            [
                "## Stable-namespace feature isolation",
                "",
                "No checked feature profile adds or removes a stable or top-level public API line",
                "relative to the default snapshot. Feature-only APIs are isolated under the",
                "experimental namespace.",
            ]
        )

    registry_pointer = scope["public_rust_api_signature_revision_registry"]
    lines.extend(
        [
            "",
            "## Public Rust declaration-signature revision evidence",
            "",
            "The runtime declaration-signature identity is bound to the append-only registry",
            f"`{registry_pointer['repository_path']}` (SHA-256",
            f"`{registry_pointer['canonical_json_sha256']}`). Each revision records the exact",
            "source commit/tree, generation context, and every proposed feature-profile snapshot",
            "digest. Here *signature* means a normalized list of public Rust declarations; it is",
            "not cryptographic signing. The source commit/tree identifies the code whose",
            "declarations were generated. In the two-phase evidence flow, the immutable snapshot",
            "bytes live at the revision-scoped paths added by the evidence update and need not",
            "exist in that earlier source commit. This is declaration-signature evidence only:",
            "equality does not establish compatibility, behavior,",
            "scientific validity, application validity, executable identity, or numeric parity.",
            "Append preservation is checked against the source anchor, HEAD, every direct HEAD",
            "parent, and every registry-touch commit reachable from HEAD through Git's full path",
            "history. Once a committed registry binding is an ancestor, each snapshot path's exact",
            "byte digest is checked at binding states, HEAD/direct-parent boundaries, and every",
            "reachable commit in that snapshot's full path history. Pre-binding states and paths",
            "first bound only in the working tree are outside that historical interval; current",
            "working-tree bytes are still checked exactly. Git queries discard ambient routing,",
            "object, configuration, namespace, shallow-file, replacement, and pathspec inputs;",
            "replacement/graft overlays are disabled, and Git's canonical worktree root must",
            "equal the repository whose current files are checked. This covers only the reachable",
            "objects",
            "presented to the checker. It cannot observe a never-merged branch that is no longer",
            "reachable, deleted references, or an externally replaced history without an",
            "independent remote or transparency witness.",
            "",
            "| Epoch | Revision | Status | Scope | Source commit | Source tree | Profiles |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for entry in signature_registry["entries"]:
        lines.append(
            "| {epoch} | {revision} | `{status}` | `{scope}` | `{commit}` | `{tree}` | {profiles} |".format(
                epoch=entry["epoch"],
                revision=entry["revision"],
                status=entry["status"],
                scope=entry["scope"],
                commit=entry["snapshot_source_commit_sha"],
                tree=entry["snapshot_source_tree_sha"],
                profiles=len(entry["profiles"]),
            )
        )

    lines.extend(["", "## Optional integration claims", ""])
    for integration in scope["integration_claims"]:
        lines.append(
            f"- `{integration['integration_id']}`: **{integration['claim_status']}** — {integration['reason']}"
        )

    lines.extend(["", "## Acceptance blockers", ""])
    lines.extend(f"- {blocker}" for blocker in scope["acceptance_blockers"])
    lines.extend(["", "## Review approvals", ""])
    for approval in scope["review_approvals"]:
        lines.append(
            "- `{role}`: **{status}**; binding: `{binding}`; reviewer: {reviewer}; "
            "commit: {commit}; evidence: {evidence}; conflicts: {conflicts}; "
            "independence: {independence}".format(
                role=approval["role"],
                status=approval["status"],
                binding=approval["commit_binding"],
                reviewer=markdown_cell(approval["reviewer"]),
                commit=markdown_cell(approval["commit_sha"]),
                evidence=markdown_cell(approval["evidence"]),
                conflicts=markdown_cell(approval["conflict_disclosure"]),
                independence=markdown_cell(approval["independence_statement"]),
            )
        )

    lines.extend(["", "## Prohibited 1.0 claims", ""])
    lines.extend(f"- {claim}" for claim in scope["prohibited_claims"])
    lines.extend(["", "## Unsupported in 1.0", ""])
    lines.extend(f"- {claim}" for claim in scope["unsupported_in_1_0"])

    lines.extend(
        [
            "",
            "## Compiled public-API snapshots",
            "",
            "Snapshots were generated with the pinned tool recorded in this scope file. They are",
            "signature evidence, not scientific-validation evidence.",
            "",
            "| Profile | Activation | Requested features | Feature closure | Snapshot | SHA-256 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for profile in scope["feature_profiles"]:
        lines.append(
            "| `{id}` | {activation} | {requested} | {closure} | `{path}` | `{digest}` |".format(
                id=profile["id"],
                activation="`--all-features`"
                if profile["all_features"]
                else "explicit feature set",
                requested=markdown_cell(profile["requested_features"]),
                closure=markdown_cell(profile["feature_closure"]),
                path=profile["public_api_snapshot"],
                digest=profile["public_api_snapshot_sha256"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--signature-registry", type=Path, default=DEFAULT_SIGNATURE_REGISTRY
    )
    parser.add_argument(
        "--signature-registry-schema",
        type=Path,
        default=DEFAULT_SIGNATURE_REGISTRY_SCHEMA,
    )
    parser.add_argument(
        "--software-identity-reference",
        type=Path,
        default=DEFAULT_SOFTWARE_IDENTITY_REFERENCE,
    )
    parser.add_argument("--lib-rs", type=Path, default=DEFAULT_LIB_RS)
    parser.add_argument("--cargo-toml", type=Path, default=DEFAULT_CARGO)
    parser.add_argument("--print-markdown", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        scope = load_json(args.scope, canonical=True)
        schema = load_json(args.schema)
        signature_registry, signature_registry_sha256 = load_json_with_sha256(
            args.signature_registry,
            canonical=True,
        )
        signature_registry_schema = load_json(args.signature_registry_schema)
        identity_reference = load_json(
            args.software_identity_reference,
            canonical=True,
        )
        validate_scope(
            scope,
            schema=schema,
            lib_rs=args.lib_rs,
            cargo_toml=args.cargo_toml,
            signature_registry=signature_registry,
            signature_registry_path=args.signature_registry,
            signature_registry_sha256=signature_registry_sha256,
            signature_registry_schema=signature_registry_schema,
            identity_reference=identity_reference,
            root=ROOT,
        )
        rendered = render_markdown(scope, signature_registry)
        if args.print_markdown:
            print(rendered, end="")
        else:
            try:
                committed = args.markdown.read_text(encoding="utf-8")
            except OSError as error:
                raise ScopeError(
                    f"cannot read rendered scope {args.markdown}: {error}"
                ) from error
            if committed != rendered:
                raise ScopeError(
                    f"{args.markdown} is stale; regenerate it with --print-markdown"
                )
            print(
                f"OK: {len(scope['families'])} capability rows and "
                f"{sum(len(item['symbols']) for item in scope['families'])} source exports match"
            )
        return 0
    except ScopeError as error:
        print(f"release scope error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
