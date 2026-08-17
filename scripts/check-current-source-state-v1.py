#!/usr/bin/env python3
"""Generate and validate the deterministic self-excluding current source state.

The manifest binds repository-visible source bytes and Git modes but deliberately
does not claim its own SHA or a final containing commit.  Resolve the containing
commit from Git after commit.  This is a consistency record, not authenticity,
review completion, formal closure, or scientific validity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-current-source-state-v1.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
GIT_EXECUTABLE = Path("/usr/bin/git")
DEFAULT_MANIFEST = ROOT / "audit/evidence/current-source-state-v1.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/current-source-state-v1.schema.json"
MANIFEST_RELATIVE = "audit/evidence/current-source-state-v1.json"
SCHEMA_NAME = "pid-rs/current-source-state"
SCHEMA_REVISION = 1
GENERATOR = "scripts/check-current-source-state-v1.py"
REPOSITORY = "sepahead/pid-rs"
EXPECTED_SCHEMA_SHA256 = (
    "501ed8fcca211ae598e041a5596b44574c48da46a9143cafe7266a7493b93f53"
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
CRITICAL_ARTIFACTS = (
    ("assurance_registry_authority", "audit/evidence/assurance-registry.json"),
    (
        "assurance_registry_typed_view",
        "audit/evidence/assurance-registry-typed-view-v1.json",
    ),
    ("method_catalog", "method-catalog.json"),
    ("release_scope", "release-scope-1.0.json"),
    ("review_inventory", "audit/evidence/FILE_REVIEW_LEDGER.csv"),
    ("source_errata", "audit/source-errata.json"),
)
SUBPROJECTIONS = (
    ("claim_packets", ("claims/",)),
    ("formal_sources_and_receipts", ("audit/formal/",)),
    ("generated_pdf_set", ("output/pdf/",)),
    ("release_documents", ("README.md", "RELEASE_NOTES.md", "CHANGELOG.md")),
)
EXPECTED_PDF_PATHS = (
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "output/pdf/ecosystem-compatibility-audit.pdf",
    "output/pdf/exact-log-product-sxpid2-assurance.pdf",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "output/pdf/ksg-m1a-composite-v4-process.pdf",
    "output/pdf/mathematical-problem-solving-workflow.pdf",
    "output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf",
    "output/pdf/two-source-sxpid-count-atom-bridge.pdf",
)


class StateError(RuntimeError):
    """Source-state collection or validation failed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit",
        action="store_true",
        help="write the deterministic expected manifest to stdout instead of validating",
    )
    return parser.parse_args()


def reject_constant(value: str) -> Any:
    raise StateError(f"non-finite JSON constant is forbidden: {value}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise StateError(f"cannot canonicalize JSON: {error}") from error


def compact_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise StateError(f"cannot canonicalize projection: {error}") from error


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_environment() -> dict[str, str]:
    return {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
    }


def git(root: Path, *arguments: str) -> bytes:
    try:
        before = GIT_EXECUTABLE.lstat()
        resolved = GIT_EXECUTABLE.resolve(strict=True)
    except OSError as error:
        raise StateError(
            f"cannot inspect fixed Git executable {GIT_EXECUTABLE}: {error}"
        ) from error
    if resolved != GIT_EXECUTABLE or not stat.S_ISREG(before.st_mode):
        raise StateError(
            f"fixed Git executable is not a canonical regular file: {GIT_EXECUTABLE}"
        )
    command = [
        os.fspath(GIT_EXECUTABLE),
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-C",
        str(root),
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            env=safe_environment(),
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise StateError(f"cannot run fixed Git executable: {error}") from error
    try:
        after = GIT_EXECUTABLE.lstat()
    except OSError as error:
        raise StateError(
            f"cannot recheck fixed Git executable {GIT_EXECUTABLE}: {error}"
        ) from error

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after):
        raise StateError("fixed Git executable changed across invocation")
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise StateError(
            f"Git command failed ({completed.returncode}): {arguments}: {stderr}"
        )
    return completed.stdout


def ensure_git_root(root: Path) -> None:
    raw = git(root, "rev-parse", "--show-toplevel")
    try:
        reported = Path(raw.decode("utf-8").strip()).resolve(strict=True)
    except (UnicodeDecodeError, OSError) as error:
        raise StateError(f"Git root is not a resolvable UTF-8 path: {error}") from error
    if reported != root.resolve(strict=True):
        raise StateError(f"requested root {root} is not canonical Git root {reported}")


def decode_z_paths(raw: bytes, label: str) -> list[str]:
    if not raw.endswith(b"\0") and raw:
        raise StateError(f"{label} output lacks NUL termination")
    values = raw[:-1].split(b"\0") if raw else []
    try:
        paths = [value.decode("utf-8") for value in values]
    except UnicodeDecodeError as error:
        raise StateError(f"{label} contains a non-UTF-8 path: {error}") from error
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise StateError(f"{label} paths are not sorted unique")
    for path in paths:
        pure = PurePosixPath(path)
        if (
            not path
            or path.startswith("/")
            or ".." in pure.parts
            or pure.as_posix() != path
        ):
            raise StateError(f"unsafe or noncanonical repository path: {path!r}")
    return paths


def candidate_paths_and_modes(root: Path) -> list[tuple[str, str]]:
    # Only repository .gitignore files affect untracked inclusion.  Ambient global and
    # .git/info/exclude state cannot hide a source file from this projection.
    tracked = decode_z_paths(git(root, "ls-files", "--cached", "-z"), "tracked-files")
    untracked = decode_z_paths(
        git(root, "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"),
        "untracked-files",
    )
    stage_raw = git(root, "ls-files", "--stage", "-z")
    stage_records = stage_raw[:-1].split(b"\0") if stage_raw else []
    modes: dict[str, str] = {}
    for record in stage_records:
        try:
            prefix, raw_path = record.split(b"\t", 1)
            mode, _object_id, stage = prefix.split(b" ", 2)
            path = raw_path.decode("utf-8")
            rendered_mode = mode.decode("ascii")
            rendered_stage = stage.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise StateError(f"cannot parse Git index stage record: {error}") from error
        if rendered_stage != "0" or path in modes:
            raise StateError(f"unmerged or duplicate index entry: {path!r}")
        if rendered_mode not in {"100644", "100755", "120000"}:
            raise StateError(f"unsupported Git mode {rendered_mode} for {path!r}")
        modes[path] = rendered_mode
    if set(modes) != set(tracked):
        raise StateError("tracked path and stage-mode sets differ")

    combined: list[tuple[str, str]] = []
    for path in tracked:
        if path != MANIFEST_RELATIVE:
            combined.append((path, modes[path]))
    for path in untracked:
        if path == MANIFEST_RELATIVE:
            continue
        absolute = root / path
        try:
            metadata = absolute.lstat()
        except OSError as error:
            raise StateError(f"cannot stat untracked path {path!r}: {error}") from error
        if stat.S_ISLNK(metadata.st_mode):
            mode = "120000"
        elif stat.S_ISREG(metadata.st_mode):
            mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
        else:
            raise StateError(f"unsupported untracked path type: {path!r}")
        combined.append((path, mode))
    combined.sort()
    paths = [path for path, _mode in combined]
    if len(paths) != len(set(paths)):
        raise StateError("tracked and untracked source path sets overlap")
    return combined


def read_entry(root: Path, path: str, git_mode: str) -> dict[str, Any]:
    absolute = root / path
    try:
        before = absolute.lstat()
    except OSError as error:
        raise StateError(f"cannot stat source path {path!r}: {error}") from error
    if git_mode == "120000":
        if not stat.S_ISLNK(before.st_mode):
            raise StateError(f"Git symlink is not a worktree symlink: {path!r}")
        try:
            data = os.fsencode(os.readlink(absolute))
        except OSError as error:
            raise StateError(f"cannot read symlink {path!r}: {error}") from error
    else:
        if not stat.S_ISREG(before.st_mode):
            raise StateError(f"Git regular file is not regular: {path!r}")
        try:
            data = absolute.read_bytes()
        except OSError as error:
            raise StateError(f"cannot read source path {path!r}: {error}") from error
    try:
        after = absolute.lstat()
    except OSError as error:
        raise StateError(f"cannot restat source path {path!r}: {error}") from error
    observed_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    observed_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if observed_before != observed_after:
        raise StateError(f"source path changed during collection: {path!r}")
    return {
        "git_mode": git_mode,
        "path": path,
        "sha256": sha256_bytes(data),
        "size_bytes": len(data),
    }


def collect_entries_once(root: Path) -> list[dict[str, Any]]:
    return [
        read_entry(root, path, mode) for path, mode in candidate_paths_and_modes(root)
    ]


def collect_entries(root: Path) -> list[dict[str, Any]]:
    first = collect_entries_once(root)
    second = collect_entries_once(root)
    if first != second:
        raise StateError(
            "repository source state changed during the repeated projection"
        )
    return first


def entry_projection(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "entry_count": len(entries),
        "entries_sha256": sha256_bytes(compact_bytes(entries)),
    }


def select_projection(
    entries: list[dict[str, Any]], selectors: tuple[str, ...]
) -> dict[str, Any]:
    selected = [
        entry
        for entry in entries
        if any(
            entry["path"] == selector or entry["path"].startswith(selector)
            for selector in selectors
        )
    ]
    return entry_projection(selected)


def entry_map(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping = {entry["path"]: entry for entry in entries}
    if len(mapping) != len(entries):
        raise StateError("duplicate source-state entry")
    return mapping


def require_regular_file(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise StateError(f"required artifact is not a regular file: {relative}")
        data = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise StateError(
            f"cannot read required artifact {relative}: {error}"
        ) from error
    if (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise StateError(f"required artifact changed while being read: {relative}")
    return data


def parse_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, StateError) as error:
        raise StateError(f"cannot parse {label}: {error}") from error


def review_inventory(root: Path, mapping: dict[str, dict[str, Any]]) -> dict[str, Any]:
    relative = "audit/evidence/FILE_REVIEW_LEDGER.csv"
    raw = require_regular_file(root, relative)
    if mapping.get(relative, {}).get("sha256") != sha256_bytes(raw):
        raise StateError("review ledger bytes do not match source projection")
    try:
        text = raw.decode("utf-8")
        if "\r" in text or not text.endswith("\n"):
            raise StateError("review ledger must use LF and end with a newline")
        rows = list(csv.DictReader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise StateError(f"cannot parse review ledger: {error}") from error
    if not rows or any(None in row for row in rows):
        raise StateError("review ledger is empty or malformed")
    for field in ("reviewer", "review_status"):
        if field not in rows[0]:
            raise StateError(f"review ledger lacks {field!r}")
    paths = [row.get("path", "") for row in rows]
    if (
        any(not path for path in paths)
        or paths != sorted(paths)
        or len(paths) != len(set(paths))
    ):
        raise StateError("review ledger paths must be nonempty, sorted, and unique")
    line_reviewed = sum(
        row["review_status"] not in {"", "INVENTORIED_NOT_REVIEWED"} for row in rows
    )
    named_reviewers = sum(row["reviewer"] not in {"", "UNASSIGNED"} for row in rows)
    return {
        "artifact": relative,
        "evidence_scope": "historical_v0_9_0_exact_tag_tree_inventory",
        "human_reviewer_assignments": named_reviewers,
        "inventoried_files": len(rows),
        "line_review_dispositions": line_reviewed,
        "status": "inventory_is_not_review",
        "tagged_commit_sha": "a9a275157237999c8da6ab813130d74f6113dec9",
    }


def release_tag_fact(root: Path, mapping: dict[str, dict[str, Any]]) -> dict[str, Any]:
    relative = "audit/evidence/assurance-registry.json"
    raw = require_regular_file(root, relative)
    if mapping.get(relative, {}).get("sha256") != sha256_bytes(raw):
        raise StateError("assurance registry bytes do not match source projection")
    registry = parse_json_bytes(raw, "assurance registry")
    boundary = registry.get("release_boundary") if isinstance(registry, dict) else None
    if not isinstance(boundary, dict):
        raise StateError("assurance registry release_boundary is absent")
    tag = boundary.get("tag")
    object_sha = boundary.get("tag_object_sha")
    commit_sha = boundary.get("tagged_commit_sha")
    if (
        not isinstance(tag, str)
        or not isinstance(object_sha, str)
        or not SHA1_RE.fullmatch(object_sha)
        or not isinstance(commit_sha, str)
        or not SHA1_RE.fullmatch(commit_sha)
    ):
        raise StateError("assurance registry release tag fields are malformed")
    actual_object = git(root, "rev-parse", f"refs/tags/{tag}").decode("ascii").strip()
    actual_commit = (
        git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}").decode("ascii").strip()
    )
    if (actual_object, actual_commit) != (object_sha, commit_sha):
        raise StateError("historical release tag facts disagree with local Git objects")
    return {
        "evidence_class": "tag_release_fact",
        "review_completion_inferred": False,
        "tag": tag,
        "tag_object_sha": object_sha,
        "tagged_commit_sha": commit_sha,
    }


def build_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    ensure_git_root(root)
    entries = collect_entries(root)
    mapping = entry_map(entries)
    if MANIFEST_RELATIVE in mapping:
        raise StateError(
            "self-excluded manifest unexpectedly entered source projection"
        )

    critical: list[dict[str, Any]] = []
    for role, relative in CRITICAL_ARTIFACTS:
        entry = mapping.get(relative)
        if entry is None:
            raise StateError(
                f"critical artifact absent from source projection: {relative}"
            )
        raw = require_regular_file(root, relative)
        if entry["sha256"] != sha256_bytes(raw) or entry["size_bytes"] != len(raw):
            raise StateError(
                f"critical artifact changed after source projection: {relative}"
            )
        critical.append(
            {
                "path": relative,
                "role": role,
                "sha256": entry["sha256"],
                "size_bytes": entry["size_bytes"],
            }
        )

    pdf_entries = [mapping.get(path) for path in EXPECTED_PDF_PATHS]
    if any(entry is None for entry in pdf_entries):
        missing = [
            path
            for path, entry in zip(EXPECTED_PDF_PATHS, pdf_entries)
            if entry is None
        ]
        raise StateError(f"generated PDF set is incomplete: {missing}")
    generated_pdfs: list[dict[str, Any]] = []
    for path, entry in zip(EXPECTED_PDF_PATHS, pdf_entries):
        if entry is None:
            continue
        raw = require_regular_file(root, path)
        if entry["git_mode"] not in {"100644", "100755"}:
            raise StateError(f"generated PDF is not regular: {entry['path']}")
        if entry["sha256"] != sha256_bytes(raw) or entry["size_bytes"] != len(raw):
            raise StateError(f"generated PDF changed after source projection: {path}")
        generated_pdfs.append(
            {
                "path": path,
                "role": "generated_pdf_byte_identity_only",
                "sha256": entry["sha256"],
                "size_bytes": entry["size_bytes"],
            }
        )

    inventory = review_inventory(root, mapping)
    if (
        inventory["inventoried_files"] != 186
        or inventory["line_review_dispositions"] != 0
        or inventory["human_reviewer_assignments"] != 0
    ):
        raise StateError(
            "current source-state revision is pinned to 186 inventoried and zero reviewed files"
        )
    historical_release = release_tag_fact(root, mapping)
    if inventory["tagged_commit_sha"] != historical_release["tagged_commit_sha"]:
        raise StateError(
            "review-inventory scope and historical release tag name different commits"
        )

    return {
        "binding": {
            "commit_binding": (
                "not_self_asserted; resolve the manifest blob's containing commit from Git"
            ),
            "excluded_paths": [MANIFEST_RELATIVE],
            "generated_at": "omitted_for_determinism",
            "projection_algorithm": (
                "newline-free canonical compact JSON of sorted repository .gitignore-aware "
                "tracked-plus-untracked entries {git_mode,path,sha256,size_bytes}; ambient "
                "global and .git/info excludes are ignored"
            ),
            "scope_kind": "self_excluding_worktree_source_projection",
        },
        "critical_artifacts": critical,
        "generated_by": GENERATOR,
        "generated_pdfs": generated_pdfs,
        "historical_release": historical_release,
        "nonimplications": [
            "This deterministic consistency record is not authentication or attestation.",
            "It does not claim its own final SHA-256 or containing commit.",
            "It does not establish line review, human review, independent review, or institutional review.",
            "It does not establish source-to-formal correspondence, implementation refinement, estimator validity, or application validity.",
            "A generated PDF hash establishes byte identity only, not semantic or visual correctness.",
            "Ignored build products and Git object-store bytes are outside the source projection.",
            "The projection records repository index modes and worktree bytes; it is not an object-store integrity proof.",
        ],
        "repository": REPOSITORY,
        "review_inventory": inventory,
        "schema": SCHEMA_NAME,
        "schema_revision": SCHEMA_REVISION,
        "source_projection": {
            **entry_projection(entries),
            "entries": entries,
        },
        "subprojections": [
            {
                "name": name,
                "selectors": list(selectors),
                **select_projection(entries, selectors),
            }
            for name, selectors in SUBPROJECTIONS
        ],
    }


def load_canonical_json(
    path: Path, label: str, *, require_regular: bool
) -> tuple[Any, bytes]:
    try:
        if require_regular and not stat.S_ISREG(path.lstat().st_mode):
            raise StateError(f"{label} is not a regular file: {path}")
        raw = path.read_bytes()
    except OSError as error:
        raise StateError(f"cannot read {label} {path}: {error}") from error
    value = parse_json_bytes(raw, label)
    if raw != canonical_bytes(value):
        raise StateError(f"{label} is not canonical sorted UTF-8 JSON: {path}")
    return value, raw


def validate_manifest(
    value: Any,
    schema: Any,
    expected: dict[str, Any],
) -> None:
    if not isinstance(schema, dict):
        raise StateError("source-state schema root must be an object")
    if sha256_bytes(canonical_bytes(schema)) != EXPECTED_SCHEMA_SHA256:
        raise StateError("current source-state schema bytes changed")
    if canonical_bytes(value) != canonical_bytes(expected):
        raise StateError(
            "current source-state manifest is stale or was independently edited; regenerate "
            "only after the intended source tree is frozen"
        )
    if value["binding"]["excluded_paths"] != [MANIFEST_RELATIVE]:
        raise StateError("self-exclusion set changed")
    entries = value["source_projection"]["entries"]
    paths = [entry["path"] for entry in entries]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise StateError("source projection paths are not sorted unique")
    if MANIFEST_RELATIVE in paths:
        raise StateError("manifest claimed its own bytes")
    if value["source_projection"]["entry_count"] != len(entries):
        raise StateError("source projection entry count mismatch")
    if value["source_projection"]["entries_sha256"] != sha256_bytes(
        compact_bytes(entries)
    ):
        raise StateError("source projection digest mismatch")
    if value["repository"] != REPOSITORY:
        raise StateError("production repository identity changed")


def main() -> int:
    args = parse_args()
    schema, raw_schema = load_canonical_json(
        DEFAULT_SCHEMA, "source-state schema", require_regular=True
    )
    if sha256_bytes(raw_schema) != EXPECTED_SCHEMA_SHA256:
        raise StateError("current source-state schema raw bytes changed")
    expected = build_manifest(ROOT)
    if args.emit:
        sys.stdout.buffer.write(canonical_bytes(expected))
        return 0
    manifest, raw = load_canonical_json(
        DEFAULT_MANIFEST, "current source-state manifest", require_regular=True
    )
    validate_manifest(manifest, schema, expected)
    if raw != canonical_bytes(expected):
        raise StateError("source-state byte comparison changed unexpectedly")
    print(
        "OK: deterministic self-excluding source state binds "
        f"{expected['source_projection']['entry_count']} entries; no final commit, review, "
        "formal closure, or scientific validity is inferred"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StateError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
