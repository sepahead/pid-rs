#!/usr/bin/env python3
"""Audit publication links against the exact stage-0 Git snapshot.

The publication boundary is every indexed Markdown document, every indexed
PDF below ``output/pdf``, and the declared root blueprint PDF. The checker
reads stage-0 blobs and requires each audited worktree file to be a stable,
byte-identical regular file. It rejects
intent-to-add, unmerged entries, non-regular index modes, and extra PDFs.

Markdown is parsed with a digest-pinned Pandoc GFM parser. Local targets and
canonical ``sepahead/pid-rs`` ``main`` navigation URLs must resolve, with exact
case, inside the same index snapshot. PDF actions are checked by strict pypdf
parses of indexed bytes. Relative PDF URIs and GoToR actions are forbidden.

This deterministic portability gate does not test unrelated external service
reachability. A ``blob/main`` URL is mutable navigation, not provenance.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn
from urllib.parse import unquote, urlsplit

import pypdf
from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    StreamObject,
    TextStringObject,
)


CHECK_NAME = "publication link portability check"
EXPECTED_PYPDF_VERSION = "6.15.0"
EXPECTED_PANDOC_VERSION = "pandoc 3.10.2"
EXPECTED_PANDOC_API = [1, 23, 1, 2]
ADMITTED_PANDOC_SHA256 = frozenset(
    {
        # Homebrew pandoc 3.10.2, Darwin arm64.
        "1662f49c035168d1e608ad9d923df75e4b00ac014d096349b2027ad38f84dd6e",
        # Reviewed Ubuntu 24.04 hosted pandoc 3.10.2.
        "867c5fc83e6b18991d1880e040867d31d09a0d5e68b0bfae362d2fbc71cf25ce",
    }
)
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
REGULAR_INDEX_MODES = frozenset({"100644", "100755"})
EXTERNAL_SCHEMES = frozenset({"http", "https", "mailto"})
FORBIDDEN_SCHEMES = frozenset({"data", "file", "javascript", "vbscript"})
ADMITTED_ACTIONS = frozenset({"/GoTo", "/URI"})
GITHUB_REPOSITORY_ROOT = "/sepahead/pid-rs/"
GITHUB_BLOB_MAIN_PREFIX = GITHUB_REPOSITORY_ROOT + "blob/main/"
GITHUB_TREE_MAIN_PREFIX = GITHUB_REPOSITORY_ROOT + "tree/main/"
RAW_GITHUB_MAIN_PREFIX = "/sepahead/pid-rs/main/"
ROOT_PUBLICATION_PDFS = frozenset(
    {PurePosixPath("PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf")}
)
PERCENT_ESCAPE = re.compile(r"%([0-9A-Fa-f]{2})")
MALFORMED_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
SOURCE_POSITION = re.compile(r"^(\d+):(\d+)-(\d+):(\d+)$")
SHA1_OR_SHA256 = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
EXPLICIT_DESTINATION_ARITY = {
    "/XYZ": 5,
    "/Fit": 2,
    "/FitH": 3,
    "/FitV": 3,
    "/FitR": 6,
    "/FitB": 2,
    "/FitBH": 3,
    "/FitBV": 3,
}


@dataclass(frozen=True)
class IndexEntry:
    path: PurePosixPath
    mode: str
    oid: str


@dataclass(frozen=True)
class Link:
    source: PurePosixPath
    line: int
    target: str
    kind: str


@dataclass(frozen=True)
class LocalTarget:
    path: PurePosixPath
    fragment: str
    expected_kind: str = "either"
    route: str = "relative"


class AuditError(RuntimeError):
    """A fail-closed checker-environment or input-shape failure."""


def fail(message: str) -> NoReturn:
    raise AuditError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_semantic_dictionary(value: Any) -> bool:
    """Return true for PDF dictionaries, excluding stream subtype confusion."""

    return isinstance(value, DictionaryObject) and not isinstance(value, StreamObject)


def git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def git_executable() -> Path:
    candidate = Path("/usr/bin/git")
    if not candidate.is_file():
        discovered = shutil.which("git")
        if discovered is None:
            fail("missing git executable")
        candidate = Path(discovered)
    resolved = candidate.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        fail(f"unusable Git executable: {resolved}")
    return resolved


def run_git(arguments: list[str], *, cwd: Path | None = None) -> bytes:
    completed = subprocess.run(
        [
            str(git_executable()),
            "--no-replace-objects",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.fsmonitor=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            *arguments,
        ],
        cwd=cwd,
        env=git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        fail(f"git {' '.join(arguments)!r} failed: {detail}")
    return completed.stdout


def repository_root() -> Path:
    raw = run_git(["rev-parse", "--show-toplevel"])
    try:
        value = raw.decode("utf-8", "strict").rstrip("\n")
    except UnicodeDecodeError as error:
        fail(f"repository root is not UTF-8: {error}")
    root = Path(value).resolve(strict=True)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        fail(f"unusable repository root: {root}")
    canonical = run_git(["-C", str(root), "rev-parse", "--show-toplevel"])
    observed = Path(canonical.decode("utf-8", "strict").rstrip("\n")).resolve(
        strict=True
    )
    if observed != root:
        fail("repository root changed during canonicalization")
    return root


def read_index(root: Path) -> dict[PurePosixPath, IndexEntry]:
    raw = run_git(["-C", str(root), "ls-files", "--stage", "-z"])
    entries: dict[PurePosixPath, IndexEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            header_raw, path_raw = record.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = header_raw.split(b" ", 2)
            mode = mode_raw.decode("ascii", "strict")
            oid = oid_raw.decode("ascii", "strict")
            stage = int(stage_raw.decode("ascii", "strict"), 10)
            path_text = path_raw.decode("utf-8", "strict")
        except (UnicodeError, ValueError) as error:
            fail(f"malformed Git index record: {record!r}: {error}")
        path = PurePosixPath(path_text)
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or str(path) in {"", "."}
        ):
            fail(f"unsafe indexed path: {path_text!r}")
        if stage != 0:
            fail(f"unmerged index entry at stage {stage}: {path}")
        if path in entries:
            fail(f"duplicate stage-0 index entry: {path}")
        if mode not in REGULAR_INDEX_MODES:
            fail(
                f"unsupported index mode {mode} for {path}; only regular files are admitted"
            )
        if not SHA1_OR_SHA256.fullmatch(oid):
            fail(f"malformed object id for {path}: {oid!r}")
        entries[path] = IndexEntry(path, mode, oid)
    if not entries:
        fail("Git index is empty")
    return entries


def intent_to_add_paths(root: Path) -> frozenset[PurePosixPath]:
    raw = run_git(
        [
            "-C",
            str(root),
            "diff-files",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
            "--name-only",
            "--diff-filter=A",
            "-z",
            "--",
        ]
    )
    result: set[PurePosixPath] = set()
    for item in raw.split(b"\0"):
        if not item:
            continue
        try:
            result.add(PurePosixPath(item.decode("utf-8", "strict")))
        except UnicodeDecodeError as error:
            fail(f"intent-to-add path is not UTF-8: {error}")
    return frozenset(result)


def index_tags(root: Path) -> dict[PurePosixPath, str]:
    """Reject index flags that can hide an intent-to-add placeholder."""

    raw = run_git(["-C", str(root), "ls-files", "-v", "-z", "--"])
    result: dict[PurePosixPath, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        if len(record) < 3 or record[1:2] != b" ":
            fail(f"malformed Git index-tag record: {record!r}")
        try:
            tag = record[:1].decode("ascii", "strict")
            path = PurePosixPath(record[2:].decode("utf-8", "strict"))
        except UnicodeError as error:
            fail(f"invalid Git index-tag record: {record!r}: {error}")
        if path in result:
            fail(f"duplicate Git index-tag entry: {path}")
        if tag != "H":
            fail(
                f"hidden index flag {tag!r} for {path}; "
                "skip-worktree and assume-unchanged are not admitted"
            )
        result[path] = tag
    return result


def read_blob(root: Path, entry: IndexEntry) -> bytes:
    return run_git(["-C", str(root), "cat-file", "blob", entry.oid])


def read_stable_worktree_file(root: Path, path: PurePosixPath) -> bytes:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        fail("this link gate requires O_NOFOLLOW and O_DIRECTORY")
    descriptors: list[int] = []
    try:
        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        descriptors.append(directory_fd)
        for component in path.parts[:-1]:
            directory_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory_fd,
            )
            descriptors.append(directory_fd)
        file_fd = os.open(
            path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
        )
        descriptors.append(file_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            fail(f"audited worktree path is not a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, name) != getattr(after, name) for name in fields):
            fail(f"audited worktree file changed while it was read: {path}")
        final = os.stat(path.parts[-1], dir_fd=directory_fd, follow_symlinks=False)
        if (final.st_dev, final.st_ino) != (after.st_dev, after.st_ino):
            fail(f"audited worktree path changed while it was read: {path}")
        return b"".join(chunks)
    except (FileNotFoundError, NotADirectoryError, OSError) as error:
        fail(
            f"cannot read audited worktree path {path} without following links: {error}"
        )
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def worktree_publication_pdfs(
    root: Path,
) -> tuple[frozenset[PurePosixPath], list[str]]:
    start = root / "output" / "pdf"
    if not start.is_dir() or start.is_symlink():
        fail("output/pdf is missing, symbolic, or not a directory")
    result: set[PurePosixPath] = set()
    errors: list[str] = []
    pending = [start]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as error:
            fail(f"cannot enumerate publication PDF directory {directory}: {error}")
        for child in children:
            relative = PurePosixPath(Path(child.path).relative_to(root).as_posix())
            if child.is_symlink():
                errors.append(
                    f"{relative}: symbolic links below output/pdf are not admitted"
                )
                if child.name.lower().endswith(".pdf"):
                    result.add(relative)
                continue
            if child.is_dir(follow_symlinks=False):
                pending.append(Path(child.path))
            elif child.name.lower().endswith(".pdf"):
                result.add(relative)
    for relative in sorted(ROOT_PUBLICATION_PDFS, key=str):
        path = root.joinpath(*relative.parts)
        try:
            metadata = os.lstat(path)
        except FileNotFoundError:
            continue
        except OSError as error:
            errors.append(
                f"{relative}: cannot inspect declared root publication PDF: {error}"
            )
            continue
        if stat.S_ISLNK(metadata.st_mode):
            errors.append(
                f"{relative}: declared root publication PDF is a symbolic link"
            )
        elif not stat.S_ISREG(metadata.st_mode):
            errors.append(
                f"{relative}: declared root publication PDF is not a regular file"
            )
        else:
            result.add(relative)
    return frozenset(result), errors


def pandoc_executable(root: Path) -> Path:
    discovered = shutil.which("pandoc")
    if discovered is None:
        fail("missing Pandoc executable")
    executable = Path(discovered).resolve(strict=True)
    if not executable.is_file() or executable.is_symlink():
        fail(f"unusable Pandoc executable: {executable}")
    if executable == root or root in executable.parents:
        fail("Pandoc resolved from inside the repository")
    digest = sha256_bytes(executable.read_bytes())
    if digest not in ADMITTED_PANDOC_SHA256:
        fail(f"unreviewed Pandoc executable digest: {digest}")
    completed = subprocess.run(
        [str(executable), "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    lines = completed.stdout.decode("utf-8", "strict").splitlines()
    observed = lines[0] if lines else "<none>"
    if completed.returncode != 0 or observed != EXPECTED_PANDOC_VERSION:
        fail(f"requires {EXPECTED_PANDOC_VERSION}, observed {observed}")
    return executable


def parse_markdown(pandoc: Path, source: PurePosixPath, blob: bytes) -> dict[str, Any]:
    try:
        blob.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise ValueError(f"Markdown source is not strict UTF-8: {error}") from error
    completed = subprocess.run(
        [str(pandoc), "--sandbox", "--from=gfm+sourcepos", "--to=json"],
        input=blob,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"Pandoc GFM parse failed: {detail}")
    if completed.stderr:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"Pandoc GFM parse emitted a diagnostic: {detail}")
    try:
        document = json.loads(completed.stdout.decode("utf-8", "strict"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Pandoc returned invalid JSON: {error}") from error
    observed = (
        document.get("pandoc-api-version") if isinstance(document, dict) else None
    )
    if not isinstance(document, dict) or observed != EXPECTED_PANDOC_API:
        raise ValueError(f"Pandoc API changed: {observed!r}")
    if not isinstance(document.get("blocks"), list):
        raise ValueError("Pandoc JSON has no block array")
    return document


def attribute_line(attribute: Any) -> int | None:
    if (
        not isinstance(attribute, list)
        or len(attribute) != 3
        or not isinstance(attribute[2], list)
    ):
        return None
    for pair in attribute[2]:
        if isinstance(pair, list) and len(pair) == 2 and pair[0] == "data-pos":
            match = SOURCE_POSITION.fullmatch(str(pair[1]))
            if match is not None:
                return int(match.group(1), 10)
    return None


def node_line(node: dict[str, Any], inherited: int) -> int:
    contents = node.get("c")
    if not isinstance(contents, list):
        return inherited
    candidates: list[Any] = []
    if (
        node.get("t")
        in {
            "Link",
            "Image",
            "Span",
            "Div",
            "Code",
            "CodeBlock",
        }
        and contents
    ):
        candidates.append(contents[0])
    if node.get("t") == "Header" and len(contents) >= 2:
        candidates.append(contents[1])
    for candidate in candidates:
        line = attribute_line(candidate)
        if line is not None:
            return line
    return inherited


def inline_text(value: Any) -> str:
    pieces: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        if not isinstance(node, dict):
            return
        kind = node.get("t")
        contents = node.get("c")
        if kind == "Str" and isinstance(contents, str):
            pieces.append(contents)
        elif kind in {"Space", "SoftBreak", "LineBreak"}:
            pieces.append(" ")
        elif (
            kind in {"Code", "Math"}
            and isinstance(contents, list)
            and len(contents) >= 2
        ):
            pieces.append(str(contents[1]))
        elif (
            kind == "RawInline"
            and isinstance(contents, list)
            and contents[:1] == ["html"]
        ):
            return
        elif kind == "Note":
            raise ValueError(
                "footnoted heading anchor semantics are outside the admitted GitHub-slug profile"
            )
        else:
            visit(contents)

    visit(value)
    return "".join(pieces)


def github_slug(title: str) -> str:
    kept: list[str] = []
    for character in title.lower():
        category = unicodedata.category(character)
        if character == " ":
            kept.append("-")
        elif character.isspace():
            continue
        elif character in {"-", "_"}:
            kept.append(character)
        elif category[0] in {"L", "M"} or category in {"Nd", "Nl", "Pc"}:
            kept.append(character)
    return "".join(kept)


class RawHTMLTargets(HTMLParser):
    def __init__(self, base_line: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base_line = base_line
        self.links: list[tuple[int, str, str]] = []
        self.anchors: set[str] = set()

    def record(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        line = self.base_line + self.getpos()[0] - 1
        lowered = tag.lower()
        for key, value in attributes:
            if value is None:
                continue
            name = key.lower()
            if name in {"href", "src"}:
                self.links.append((line, value, f"html-{name}"))
            if lowered == "a" and name in {"id", "name"}:
                self.anchors.add(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.record(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.record(tag, attrs)


def extract_markdown(
    source: PurePosixPath, document: dict[str, Any]
) -> tuple[list[Link], frozenset[str]]:
    links: list[Link] = []
    anchors: set[str] = set()
    used_slugs: set[str] = set()

    def visit(node: Any, inherited_line: int = 1) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child, inherited_line)
            return
        if not isinstance(node, dict):
            return
        line = node_line(node, inherited_line)
        kind = node.get("t")
        contents = node.get("c")
        if kind in {"Link", "Image"}:
            if not isinstance(contents, list) or len(contents) != 3:
                raise ValueError(f"malformed Pandoc {kind} node")
            target_pair = contents[2]
            if (
                not isinstance(target_pair, list)
                or len(target_pair) != 2
                or not isinstance(target_pair[0], str)
            ):
                raise ValueError(f"malformed Pandoc {kind} target")
            links.append(Link(source, line, target_pair[0], f"markdown-{kind.lower()}"))
        elif kind == "Header":
            if not isinstance(contents, list) or len(contents) != 3:
                raise ValueError("malformed Pandoc Header node")
            base = github_slug(inline_text(contents[2]))
            if base:
                candidate = base
                suffix = 0
                while candidate in used_slugs:
                    suffix += 1
                    candidate = f"{base}-{suffix}"
                used_slugs.add(candidate)
                anchors.add(candidate)
        elif kind in {"RawInline", "RawBlock"}:
            if (
                isinstance(contents, list)
                and len(contents) == 2
                and contents[0] == "html"
                and isinstance(contents[1], str)
            ):
                parser = RawHTMLTargets(line)
                try:
                    parser.feed(contents[1])
                    parser.close()
                except Exception as error:
                    raise ValueError(
                        f"cannot parse raw HTML target attributes: {error}"
                    ) from error
                anchors.update(parser.anchors)
                for target_line, target, target_kind in parser.links:
                    links.append(Link(source, target_line, target, target_kind))
        visit(contents, line)

    visit(document.get("blocks", []))
    return links, frozenset(anchors)


def reject_controls_or_backslashes(value: str, label: str) -> None:
    if any(
        ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F for character in value
    ):
        raise ValueError(f"{label} contains a control character")
    if "\\" in value:
        raise ValueError(f"{label} contains a backslash")


def percent_decode(value: str, label: str) -> str:
    if MALFORMED_PERCENT.search(value):
        raise ValueError(f"{label} has malformed percent encoding")
    for match in PERCENT_ESCAPE.finditer(value):
        decoded = chr(int(match.group(1), 16))
        if (
            decoded in {"/", "\\", "."}
            or ord(decoded) < 0x20
            or 0x7F <= ord(decoded) <= 0x9F
        ):
            raise ValueError(
                f"{label} uses a structural or control percent alias {match.group(0)!r}"
            )
    try:
        decoded = unquote(value, encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError(
            f"{label} has invalid UTF-8 percent encoding: {error}"
        ) from error
    reject_controls_or_backslashes(decoded, label)
    return decoded


def normalize_path(base: tuple[str, ...], value: str) -> PurePosixPath:
    components = list(base)
    for component in value.split("/"):
        if component in {"", "."}:
            continue
        if component == "..":
            if not components:
                raise ValueError("local target escapes repository root")
            components.pop()
        else:
            components.append(component)
    return PurePosixPath(*components) if components else PurePosixPath(".")


def same_repository_main_target(value: str) -> LocalTarget | None:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    normalized_host = host.rstrip(".")
    github_hosts = {"github.com", "www.github.com"}
    raw_hosts = {"raw.githubusercontent.com", "raw.github.com"}
    if normalized_host not in github_hosts | raw_hosts:
        return None
    decoded_path = percent_decode(parsed.path, "same-repository URL path")

    def is_default_revision_alias(component: str) -> bool:
        folded = component.casefold()
        if folded in {"main", "head", "@"}:
            return True
        return bool(re.fullmatch(r"(?:main|head|@)(?:[~^].*|@\{.*\})", folded))

    def tail_uses_main(tail: str, *, raw_route: bool) -> bool:
        components = tail.split("/")
        if components and is_default_revision_alias(components[0]):
            return True
        if (
            len(components) >= 3
            and components[:2] == ["refs", "heads"]
            and is_default_revision_alias(components[2])
        ):
            return True
        return bool(
            raw_route
            and len(components) >= 2
            and components[0] == "heads"
            and is_default_revision_alias(components[1])
        )

    def is_main_route(path: str) -> bool:
        folded = path.casefold()
        repository = GITHUB_REPOSITORY_ROOT.casefold()
        if not folded.startswith(repository):
            return False
        remainder = folded[len(repository) :]
        if normalized_host in github_hosts:
            route, separator, tail = remainder.partition("/")
            return bool(
                separator
                and route in {"blob", "tree", "raw"}
                and tail_uses_main(tail, raw_route=route == "raw")
            )
        return tail_uses_main(remainder, raw_route=True)

    path_components = decoded_path.split("/")
    normalized_components: list[str] = []
    for component in path_components:
        if component in {"", "."}:
            continue
        if component == "..":
            if normalized_components:
                normalized_components.pop()
            continue
        normalized_components.append(component)
    normalized_path = "/" + "/".join(normalized_components)
    if is_main_route(normalized_path) and any(
        component in {".", ".."} for component in path_components
    ):
        raise ValueError(
            "canonical same-repository URL contains a literal dot-segment alias"
        )
    if is_main_route(normalized_path) and "//" in decoded_path:
        raise ValueError(
            "canonical same-repository URL contains a repeated-slash path alias"
        )

    main_alias = is_main_route(decoded_path)
    route: str | None = None
    expected_kind = "file"
    remainder: str | None = None
    if (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith(GITHUB_BLOB_MAIN_PREFIX)
    ):
        route = "github-blob-main"
        remainder = decoded_path[len(GITHUB_BLOB_MAIN_PREFIX) :]
    elif (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith(GITHUB_TREE_MAIN_PREFIX)
    ):
        route = "github-tree-main"
        expected_kind = "directory"
        remainder = decoded_path[len(GITHUB_TREE_MAIN_PREFIX) :]
    elif (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and decoded_path == GITHUB_TREE_MAIN_PREFIX.rstrip("/")
    ):
        route = "github-tree-main"
        expected_kind = "directory"
        remainder = "."
    elif (
        parsed.scheme == "https"
        and parsed.netloc == "raw.githubusercontent.com"
        and parsed.path.startswith(RAW_GITHUB_MAIN_PREFIX)
    ):
        route = "raw-github-main"
        remainder = decoded_path[len(RAW_GITHUB_MAIN_PREFIX) :]
    elif (
        parsed.scheme == "https"
        and parsed.netloc == "raw.githubusercontent.com"
        and decoded_path == RAW_GITHUB_MAIN_PREFIX.rstrip("/")
    ):
        raise ValueError("same-repository raw main URL has no target path")
    elif main_alias:
        raise ValueError("same-repository main URL is not in canonical HTTPS form")
    else:
        return None

    if parsed.query:
        raise ValueError("same-repository main URL has a query component")
    if route == "github-tree-main" and remainder == "":
        remainder = "."
    if not remainder:
        raise ValueError("same-repository main URL has no target path")
    if route in {"github-blob-main", "raw-github-main"} and remainder.endswith("/"):
        raise ValueError("same-repository file URL has a terminal directory marker")
    fragment = percent_decode(parsed.fragment, "same-repository URL fragment")
    if route == "raw-github-main" and fragment:
        raise ValueError(
            "raw same-repository URL cannot provide a rendered-document anchor"
        )
    return LocalTarget(
        normalize_path((), remainder),
        fragment,
        expected_kind=expected_kind,
        route=route,
    )


def classify_target(
    source: PurePosixPath, target: str, *, pdf_uri: bool = False
) -> LocalTarget | None:
    value = target
    if value != value.strip():
        raise ValueError("target has leading or trailing whitespace")
    reject_controls_or_backslashes(value, "target")
    if MALFORMED_PERCENT.search(value):
        raise ValueError("target has malformed percent encoding")
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme:
        internal = same_repository_main_target(value)
        if internal is not None:
            return internal
        if scheme in FORBIDDEN_SCHEMES:
            raise ValueError(f"forbidden {scheme}: URI")
        if scheme not in EXTERNAL_SCHEMES:
            raise ValueError(f"unapproved URI scheme {scheme!r}")
        if scheme in {"http", "https"}:
            if not parsed.netloc or parsed.hostname is None:
                raise ValueError(f"{scheme} URL has no authority")
            if parsed.username is not None or parsed.password is not None:
                raise ValueError(f"{scheme} URL contains credentials")
        elif not parsed.path:
            raise ValueError("mailto URL has no recipient")
        return None
    if parsed.netloc or value.startswith("//"):
        raise ValueError("scheme-relative URL is not admitted")
    if pdf_uri:
        raise ValueError(
            "relative PDF URI is not portable; use an absolute HTTPS navigation URL"
        )
    if parsed.query:
        raise ValueError("local target has a query component")
    decoded_path = percent_decode(parsed.path, "local target path")
    fragment = percent_decode(parsed.fragment, "local target fragment")
    if decoded_path.startswith("/"):
        raise ValueError("local absolute path is not portable")
    path = (
        source
        if not decoded_path
        else normalize_path(source.parent.parts, decoded_path)
    )
    return LocalTarget(path, fragment)


def indexed_directories(
    entries: dict[PurePosixPath, IndexEntry],
) -> frozenset[PurePosixPath]:
    result = {PurePosixPath(".")}
    for path in entries:
        parent = path.parent
        while str(parent) != ".":
            result.add(parent)
            parent = parent.parent
    return frozenset(result)


def case_mismatch(
    target: PurePosixPath,
    entries: dict[PurePosixPath, IndexEntry],
    directories: frozenset[PurePosixPath],
) -> str | None:
    folded = str(target).casefold()
    candidates = sorted(
        str(path)
        for path in [*entries.keys(), *directories]
        if str(path).casefold() == folded
    )
    return candidates[0] if candidates else None


def validate_target(
    source: PurePosixPath,
    target: str,
    entries: dict[PurePosixPath, IndexEntry],
    directories: frozenset[PurePosixPath],
    anchors: dict[PurePosixPath, frozenset[str]],
    *,
    pdf_uri: bool = False,
    require_file: bool = False,
) -> list[str]:
    if require_file:
        parsed_resource = urlsplit(target)
        if not parsed_resource.scheme and not parsed_resource.path:
            return ["image/resource target has no file path"]
        if parsed_resource.scheme.lower() not in {"", "http", "https"}:
            return ["image/resource target requires a local file or HTTP(S) URL"]
    try:
        local = classify_target(source, target, pdf_uri=pdf_uri)
    except ValueError as error:
        return [str(error)]
    if local is None:
        return []
    is_file = local.path in entries
    is_directory = local.path in directories
    if not is_file and not is_directory:
        mismatch = case_mismatch(local.path, entries, directories)
        if mismatch is not None:
            return [f"case mismatch for {local.path}; indexed spelling is {mismatch}"]
        return [f"target is not present in the staged index: {local.path}"]
    if local.expected_kind == "file" and not is_file:
        return [f"{local.route} targets a directory, not a file: {local.path}"]
    if local.expected_kind == "directory" and not is_directory:
        return [f"{local.route} targets a file, not a directory: {local.path}"]
    if require_file and not is_file:
        return [f"image/resource target is not an indexed file: {local.path}"]
    if is_directory and local.fragment:
        return [f"directory target cannot validate fragment #{local.fragment}"]
    if is_file and local.fragment and local.path.suffix.lower() in MARKDOWN_SUFFIXES:
        available = anchors.get(local.path)
        if available is None:
            return [f"Markdown anchors are unavailable for {local.path}"]
        if local.fragment not in available:
            return [f"missing Markdown anchor #{local.fragment} in {local.path}"]
    return []


class PdfLinkAudit:
    def __init__(
        self,
        reader: PdfReader,
        source: PurePosixPath,
        entries: dict[PurePosixPath, IndexEntry],
        directories: frozenset[PurePosixPath],
        anchors: dict[PurePosixPath, frozenset[str]],
    ) -> None:
        self.reader = reader
        self.source = source
        self.entries = entries
        self.directories = directories
        self.anchors = anchors
        self.errors: list[str] = []
        self.action_count = 0
        self.destination_count = 0
        self.seen_walk_indirect: set[tuple[int, int]] = set()
        self.seen_walk_direct: set[int] = set()
        self.validated_actions: set[tuple[str, int, int] | tuple[str, int]] = set()
        self.active_actions: set[tuple[str, int, int] | tuple[str, int]] = set()
        self.page_references: set[tuple[int, int]] = set()
        for page in reader.pages:
            reference = getattr(page, "indirect_reference", None)
            if isinstance(reference, IndirectObject):
                self.page_references.add((reference.idnum, reference.generation))
        self.named_destinations = self.collect_named_destinations()
        self.structure_references = self.collect_structure_references()

    @staticmethod
    def identity(
        value: Any,
    ) -> tuple[str, int, int] | tuple[str, int]:
        if isinstance(value, IndirectObject):
            return ("indirect", value.idnum, value.generation)
        return ("direct", id(value))

    @staticmethod
    def resolve(value: Any, location: str) -> Any:
        if isinstance(value, IndirectObject):
            try:
                return value.get_object()
            except Exception as error:
                raise ValueError(
                    f"cannot dereference object at {location}: {error}"
                ) from error
        return value

    def error(self, location: str, message: str) -> None:
        self.errors.append(f"{location}: {message}")

    @staticmethod
    def name_tree_key(value: Any, location: str) -> tuple[bytes, str]:
        if not isinstance(value, TextStringObject):
            raise ValueError(
                f"{location}: destination name-tree key is not a text string"
            )
        try:
            raw = value.get_original_bytes()
        except Exception as error:
            raise ValueError(
                f"{location}: cannot recover destination name-tree key bytes: {error}"
            ) from error
        return raw, str(value)

    def collect_named_destinations(self) -> frozenset[str]:
        """Validate the raw destination name tree before resolving any names."""

        root = self.reader.root_object
        if "/Dests" in root:
            self.error(
                "catalog/Dests",
                "legacy catalog destination dictionaries are not admitted",
            )
        if "/Names" not in root:
            return frozenset()
        try:
            names = self.resolve(root.raw_get("/Names"), "catalog/Names")
        except ValueError as error:
            self.error("catalog/Names", str(error))
            return frozenset()
        if not is_semantic_dictionary(names):
            self.error(
                "catalog/Names", "catalog name-tree container is not a dictionary"
            )
            return frozenset()
        if "/Dests" not in names:
            return frozenset()

        decoded_names: set[str] = set()
        seen: set[tuple[str, int, int] | tuple[str, int]] = set()
        active: set[tuple[str, int, int] | tuple[str, int]] = set()

        def limits(node: DictionaryObject, location: str) -> tuple[bytes, bytes] | None:
            if "/Limits" not in node:
                return None
            value = node.raw_get("/Limits")
            if not isinstance(value, ArrayObject) or len(value) != 2:
                self.error(location, "destination name-tree /Limits is not a pair")
                return None
            try:
                low, _ = self.name_tree_key(list.__getitem__(value, 0), location)
                high, _ = self.name_tree_key(list.__getitem__(value, 1), location)
            except ValueError as error:
                self.error(location, str(error))
                return None
            if low > high:
                self.error(location, "destination name-tree /Limits are reversed")
            return low, high

        def visit(
            value: Any, location: str, *, is_root: bool = False
        ) -> tuple[bytes, bytes] | None:
            identity = self.identity(value)
            if identity in active:
                self.error(location, "cyclic destination name tree")
                return None
            if identity in seen:
                self.error(location, "shared destination name-tree node")
                return None
            active.add(identity)
            seen.add(identity)
            try:
                if not is_root and not isinstance(value, IndirectObject):
                    self.error(location, "destination name-tree child is not indirect")
                try:
                    node = self.resolve(value, location)
                except ValueError as error:
                    self.error(location, str(error))
                    return None
                if not is_semantic_dictionary(node):
                    self.error(
                        location, "destination name-tree node is not a dictionary"
                    )
                    return None
                has_names = "/Names" in node
                has_kids = "/Kids" in node
                if has_names == has_kids:
                    self.error(
                        location,
                        "destination name-tree node must contain exactly one of /Names or /Kids",
                    )
                    return None
                allowed = {"/Limits", "/Names" if has_names else "/Kids"}
                unexpected = sorted(str(key) for key in node if str(key) not in allowed)
                if unexpected:
                    self.error(
                        location,
                        f"destination name-tree node has unexpected keys {unexpected}",
                    )
                declared_limits = limits(node, location)
                if not is_root and declared_limits is None:
                    self.error(location, "destination name-tree child has no /Limits")

                extrema: tuple[bytes, bytes] | None = None
                if has_names:
                    pairs = node.raw_get("/Names")
                    if (
                        not isinstance(pairs, ArrayObject)
                        or not pairs
                        or len(pairs) % 2
                    ):
                        self.error(
                            location,
                            "destination name-tree /Names must be a nonempty even array",
                        )
                        return None
                    previous: bytes | None = None
                    first: bytes | None = None
                    for index in range(0, len(pairs), 2):
                        try:
                            raw_key, decoded = self.name_tree_key(
                                list.__getitem__(pairs, index),
                                f"{location}/Names[{index}]",
                            )
                        except ValueError as error:
                            self.error(location, str(error))
                            continue
                        if previous is not None and raw_key <= previous:
                            self.error(
                                location,
                                "destination name-tree keys are not strictly ordered by bytes",
                            )
                        previous = raw_key
                        if first is None:
                            first = raw_key
                        if decoded in decoded_names:
                            self.error(
                                location,
                                f"duplicate decoded destination name {decoded!r}",
                            )
                        decoded_names.add(decoded)
                        raw_destination = list.__getitem__(pairs, index + 1)
                        try:
                            wrapper = self.resolve(
                                raw_destination,
                                f"{location}/Names[{index + 1}]",
                            )
                        except ValueError as error:
                            self.error(location, str(error))
                            continue
                        if isinstance(wrapper, ArrayObject):
                            destination = raw_destination
                        elif is_semantic_dictionary(wrapper):
                            wrapper_keys = set(map(str, wrapper.keys()))
                            if wrapper_keys == {"/D"}:
                                destination = wrapper.raw_get("/D")
                            elif (
                                wrapper_keys == {"/D", "/S"}
                                and str(wrapper.get("/S")) == "/GoTo"
                            ):
                                destination = wrapper.raw_get("/D")
                            else:
                                self.error(
                                    location,
                                    "destination name-tree wrapper is not a bounded "
                                    "/D or /GoTo dictionary",
                                )
                                continue
                        else:
                            self.error(
                                location,
                                "destination name-tree value is neither an explicit "
                                "destination nor a bounded destination wrapper",
                            )
                            continue
                        try:
                            explicit = self.resolve(
                                destination,
                                f"{location}/Names[{index + 1}]/D",
                            )
                        except ValueError as error:
                            self.error(location, str(error))
                            continue
                        if not isinstance(explicit, ArrayObject):
                            self.error(
                                location,
                                "destination name-tree entry does not resolve to an "
                                "explicit destination array",
                            )
                            continue
                        self.validate_destination(
                            destination, f"{location}/Names[{index + 1}]/D"
                        )
                    if first is not None and previous is not None:
                        extrema = (first, previous)
                else:
                    children = node.raw_get("/Kids")
                    if not isinstance(children, ArrayObject) or not children:
                        self.error(
                            location,
                            "destination name-tree /Kids must be a nonempty array",
                        )
                        return None
                    child_extrema: list[tuple[bytes, bytes]] = []
                    for index, child in enumerate(children):
                        observed = visit(child, f"{location}/Kids[{index}]")
                        if observed is not None:
                            child_extrema.append(observed)
                    for previous, current in zip(
                        child_extrema, child_extrema[1:], strict=False
                    ):
                        if current[0] <= previous[1]:
                            self.error(
                                location,
                                "destination name-tree child ranges overlap or are unordered",
                            )
                    if child_extrema:
                        extrema = (child_extrema[0][0], child_extrema[-1][1])

                if (
                    declared_limits is not None
                    and extrema is not None
                    and declared_limits != extrema
                ):
                    self.error(
                        location,
                        "destination name-tree /Limits do not equal subtree extrema",
                    )
                return extrema
            finally:
                active.remove(identity)

        visit(names.raw_get("/Dests"), "catalog/Names/Dests", is_root=True)
        return frozenset(decoded_names)

    def collect_structure_references(self) -> set[tuple[int, int]]:
        """Index indirect structure elements reachable through StructTreeRoot /K."""

        references: set[tuple[int, int]] = set()
        root = self.reader.root_object
        if "/StructTreeRoot" not in root:
            return references
        structure_root_value = root.raw_get("/StructTreeRoot")
        if not isinstance(structure_root_value, IndirectObject):
            self.error("catalog/StructTreeRoot", "structure root is not indirect")
            return references
        try:
            structure_root = self.resolve(
                structure_root_value, "catalog/StructTreeRoot"
            )
        except ValueError as error:
            self.error("catalog/StructTreeRoot", str(error))
            return references
        if not is_semantic_dictionary(structure_root):
            self.error("catalog/StructTreeRoot", "structure root is not a dictionary")
            return references
        if str(structure_root.get("/Type")) != "/StructTreeRoot":
            self.error(
                "catalog/StructTreeRoot",
                "structure root has no /Type /StructTreeRoot",
            )
            return references

        active: set[tuple[str, int, int] | tuple[str, int]] = set()
        seen: set[tuple[str, int, int] | tuple[str, int]] = set()

        root_identity = self.identity(structure_root_value)

        def visit(
            value: Any,
            location: str,
            expected_parent: tuple[str, int, int] | tuple[str, int],
        ) -> None:
            identity = self.identity(value)
            if identity in active:
                self.error(location, "cyclic structure-child graph")
                return
            if identity in seen:
                self.error(location, "shared structure-child object")
                return
            active.add(identity)
            try:
                try:
                    resolved = self.resolve(value, location)
                except ValueError as error:
                    self.error(location, str(error))
                    return
                if isinstance(resolved, ArrayObject):
                    for index, child in enumerate(resolved):
                        visit(child, f"{location}[{index}]", expected_parent)
                    return
                if isinstance(resolved, NumberObject):
                    return
                if not is_semantic_dictionary(resolved):
                    self.error(
                        location,
                        "structure child is not an array, integer, or dictionary",
                    )
                    return
                child_type = resolved.get("/Type")
                if str(child_type) in {"/MCR", "/OBJR"}:
                    return
                if str(child_type) != "/StructElem":
                    self.error(
                        location,
                        f"unsupported structure-child type {child_type!r}",
                    )
                    return
                if not isinstance(value, IndirectObject):
                    self.error(location, "structure element is not indirect")
                    return
                reference = (value.idnum, value.generation)
                references.add(reference)
                role = resolved.get("/S")
                if not isinstance(role, NameObject):
                    self.error(location, "StructElem has no NameObject /S role")
                if "/P" not in resolved:
                    self.error(location, "StructElem has no /P parent")
                else:
                    parent = resolved.raw_get("/P")
                    if not isinstance(parent, IndirectObject):
                        self.error(location, "StructElem /P parent is not indirect")
                    elif self.identity(parent) != expected_parent:
                        self.error(
                            location, "StructElem /P parent does not match traversal"
                        )
                if "/K" in resolved:
                    visit(resolved.raw_get("/K"), f"{location}/K", self.identity(value))
            finally:
                active.remove(identity)
                seen.add(identity)

        if "/K" not in structure_root:
            self.error("catalog/StructTreeRoot", "structure root has no /K")
            return references
        visit(
            structure_root.raw_get("/K"),
            "catalog/StructTreeRoot/K",
            root_identity,
        )
        return references

    def validate_named_destination(self, value: str, location: str) -> None:
        candidates = [value]
        if value.startswith("/"):
            candidates.append(value[1:])
        if not any(name in self.named_destinations for name in candidates):
            self.error(location, f"unresolved named destination {value!r}")

    def validate_destination(self, value: Any, location: str) -> None:
        self.destination_count += 1
        try:
            resolved = self.resolve(value, location)
        except ValueError as error:
            self.error(location, str(error))
            return
        if isinstance(resolved, (NameObject, TextStringObject)):
            self.validate_named_destination(str(resolved), location)
            return
        if not isinstance(resolved, ArrayObject):
            self.error(
                location,
                "destination must be a name, text string, or explicit array, "
                f"not {type(resolved).__name__}",
            )
            return
        if len(resolved) < 2:
            self.error(location, "explicit destination array is too short")
            return
        page = resolved[0]
        if (
            not isinstance(page, IndirectObject)
            or (page.idnum, page.generation) not in self.page_references
        ):
            self.error(
                location,
                "explicit destination does not name an in-document page reference",
            )
        fit = resolved[1]
        if (
            not isinstance(fit, NameObject)
            or str(fit) not in EXPLICIT_DESTINATION_ARITY
        ):
            self.error(
                location,
                f"explicit destination has unsupported fit mode {fit!r}",
            )
            return
        expected = EXPLICIT_DESTINATION_ARITY[str(fit)]
        if len(resolved) != expected:
            self.error(
                location,
                f"explicit destination {fit} requires {expected} entries, "
                f"observed {len(resolved)}",
            )
        numeric_types = (NumberObject, FloatObject)
        admitted_types = (
            numeric_types if str(fit) == "/FitR" else (*numeric_types, NullObject)
        )
        for parameter in resolved[2:]:
            if not isinstance(parameter, admitted_types):
                self.error(
                    location,
                    f"explicit destination parameter for {fit} has nonnumeric type "
                    f"{type(parameter).__name__}",
                )

    def validate_structure_destination(self, value: Any, location: str) -> None:
        try:
            resolved = self.resolve(value, location)
        except ValueError as error:
            self.error(location, str(error))
            return
        if not isinstance(resolved, ArrayObject) or len(resolved) < 2:
            self.error(location, "structure destination is not an explicit array")
            return
        element = resolved[0]
        if not isinstance(element, IndirectObject):
            self.error(
                location, "structure destination does not name an indirect element"
            )
        else:
            reference = (element.idnum, element.generation)
            if reference not in self.structure_references:
                self.error(
                    location,
                    "structure destination is outside the catalog StructTreeRoot /K graph",
                )
            try:
                structure = self.resolve(element, f"{location}[0]")
            except ValueError as error:
                self.error(location, str(error))
            else:
                if (
                    not is_semantic_dictionary(structure)
                    or str(structure.get("/Type")) != "/StructElem"
                ):
                    self.error(
                        location, "structure destination target is not a StructElem"
                    )
        fit = resolved[1]
        if (
            not isinstance(fit, NameObject)
            or str(fit) not in EXPLICIT_DESTINATION_ARITY
        ):
            self.error(
                location, f"structure destination has unsupported fit mode {fit!r}"
            )
            return
        expected = EXPLICIT_DESTINATION_ARITY[str(fit)]
        if len(resolved) != expected:
            self.error(
                location,
                f"structure destination {fit} requires {expected} entries, "
                f"observed {len(resolved)}",
            )
        numeric_types = (NumberObject, FloatObject)
        admitted_types = (
            numeric_types if str(fit) == "/FitR" else (*numeric_types, NullObject)
        )
        for parameter in resolved[2:]:
            if not isinstance(parameter, admitted_types):
                self.error(
                    location,
                    f"structure destination parameter for {fit} has nonnumeric type "
                    f"{type(parameter).__name__}",
                )

    def process_action_sequence(self, value: Any, location: str) -> None:
        try:
            resolved = self.resolve(value, location)
        except ValueError as error:
            self.error(location, str(error))
            return
        if isinstance(resolved, ArrayObject):
            if not resolved:
                self.error(location, "action sequence is empty")
            for index, child in enumerate(resolved):
                self.process_action(child, f"{location}[{index}]")
        else:
            self.process_action(value, location)

    def process_action(self, value: Any, location: str) -> None:
        identity = self.identity(value)
        if identity in self.active_actions:
            self.error(location, "cyclic /Next action graph")
            return
        if identity in self.validated_actions:
            return
        self.active_actions.add(identity)
        self.action_count += 1
        try:
            try:
                action = self.resolve(value, location)
            except ValueError as error:
                self.error(location, str(error))
                return
            if not is_semantic_dictionary(action):
                self.error(
                    location,
                    f"action slot is not a dictionary: {type(action).__name__}",
                )
                return
            action_type = action.get("/Type")
            if action_type is not None and (
                not isinstance(action_type, NameObject) or str(action_type) != "/Action"
            ):
                self.error(location, f"action has invalid /Type {action_type!r}")
            name = action.get("/S")
            if not isinstance(name, NameObject):
                self.error(location, "action has no NameObject /S")
                return
            action_name = str(name)
            if action_name not in ADMITTED_ACTIONS:
                self.error(location, f"PDF action {action_name} is not admitted")
            elif action_name == "/GoTo":
                allowed = {"/Type", "/S", "/D", "/Next", "/SD"}
                unexpected = sorted(
                    str(key) for key in action if str(key) not in allowed
                )
                if unexpected:
                    self.error(
                        location, f"GoTo action has unexpected keys {unexpected}"
                    )
                if "/D" not in action:
                    self.error(location, "GoTo action has no /D destination")
                else:
                    self.validate_destination(action.raw_get("/D"), f"{location}/D")
                if "/SD" in action:
                    self.validate_structure_destination(
                        action.raw_get("/SD"), f"{location}/SD"
                    )
            elif action_name == "/URI":
                allowed = {"/Type", "/S", "/URI", "/IsMap", "/Next"}
                unexpected = sorted(
                    str(key) for key in action if str(key) not in allowed
                )
                if unexpected:
                    self.error(location, f"URI action has unexpected keys {unexpected}")
                target = action.get("/URI")
                if not isinstance(target, TextStringObject):
                    self.error(location, "URI action target is not a text string")
                else:
                    for problem in validate_target(
                        self.source,
                        str(target),
                        self.entries,
                        self.directories,
                        self.anchors,
                        pdf_uri=True,
                    ):
                        self.error(
                            location,
                            f"URI target {str(target)!r}: {problem}",
                        )
                if "/IsMap" in action:
                    try:
                        is_map = self.resolve(
                            action.raw_get("/IsMap"), f"{location}/IsMap"
                        )
                    except ValueError as error:
                        self.error(location, str(error))
                    else:
                        if not isinstance(is_map, BooleanObject):
                            self.error(location, "URI action /IsMap is not Boolean")
            if "/Next" in action:
                self.process_action_sequence(
                    action.raw_get("/Next"), f"{location}/Next"
                )
        finally:
            self.active_actions.remove(identity)
            self.validated_actions.add(identity)

    def process_open_action(self, value: Any, location: str) -> None:
        try:
            resolved = self.resolve(value, location)
        except ValueError as error:
            self.error(location, str(error))
            return
        if is_semantic_dictionary(resolved):
            self.process_action(value, location)
        elif isinstance(resolved, (ArrayObject, NameObject, TextStringObject)):
            self.validate_destination(value, location)
        else:
            self.error(
                location,
                "OpenAction is neither an action nor a destination: "
                f"{type(resolved).__name__}",
            )

    def process_additional_actions(self, value: Any, location: str) -> None:
        try:
            additional = self.resolve(value, location)
        except ValueError as error:
            self.error(location, str(error))
            return
        if not is_semantic_dictionary(additional):
            self.error(location, "additional-actions slot is not a dictionary")
            return
        for key, action in additional.items():
            if not isinstance(key, NameObject):
                self.error(
                    location,
                    f"additional-action event key is not a name: {key!r}",
                )
                continue
            self.process_action(action, f"{location}/{str(key).lstrip('/')}")

    def validate_outline_navigation(self) -> None:
        """Reject ambiguous action/destination pairs in the actual outline hierarchy."""

        root = self.reader.root_object
        if "/Outlines" not in root:
            return
        try:
            outlines = self.resolve(root.raw_get("/Outlines"), "catalog/Outlines")
        except ValueError as error:
            self.error("catalog/Outlines", str(error))
            return
        if not is_semantic_dictionary(outlines):
            self.error("catalog/Outlines", "outline root is not a dictionary")
            return
        if "/First" not in outlines:
            return
        active: set[tuple[str, int, int] | tuple[str, int]] = set()
        seen: set[tuple[str, int, int] | tuple[str, int]] = set()

        def visit(value: Any, location: str) -> None:
            identity = self.identity(value)
            if identity in active:
                self.error(location, "cyclic outline-item hierarchy")
                return
            if identity in seen:
                self.error(location, "shared outline item")
                return
            active.add(identity)
            seen.add(identity)
            try:
                if not isinstance(value, IndirectObject):
                    self.error(location, "outline item is not indirect")
                try:
                    item = self.resolve(value, location)
                except ValueError as error:
                    self.error(location, str(error))
                    return
                if not is_semantic_dictionary(item):
                    self.error(location, "outline item is not a dictionary")
                    return
                if "/A" in item and "/Dest" in item:
                    self.error(
                        location,
                        "outline item contains mutually exclusive /A and /Dest entries",
                    )
                if "/First" in item:
                    visit(item.raw_get("/First"), f"{location}/First")
                if "/Next" in item:
                    visit(item.raw_get("/Next"), f"{location}/Next")
            finally:
                active.remove(identity)

        visit(outlines.raw_get("/First"), "catalog/Outlines/First")

    def walk(self, value: Any, location: str) -> None:
        if isinstance(value, IndirectObject):
            identity = (value.idnum, value.generation)
            if identity in self.seen_walk_indirect:
                return
            self.seen_walk_indirect.add(identity)
            try:
                value = value.get_object()
            except Exception as error:
                self.error(
                    location,
                    f"cannot dereference reachable object {identity}: {error}",
                )
                return
        if isinstance(value, StreamObject):
            return
        if isinstance(value, DictionaryObject):
            identity = id(value)
            if identity in self.seen_walk_direct:
                return
            self.seen_walk_direct.add(identity)
            if (
                str(value.get("/Subtype")) == "/Link"
                and "/A" in value
                and "/Dest" in value
            ):
                self.error(
                    location,
                    "Link annotation contains mutually exclusive /A and /Dest entries",
                )
            if "/OpenAction" in value:
                self.process_open_action(
                    value.raw_get("/OpenAction"), f"{location}/OpenAction"
                )
            if "/AA" in value:
                self.process_additional_actions(value.raw_get("/AA"), f"{location}/AA")
            if "/A" in value:
                self.process_action(value.raw_get("/A"), f"{location}/A")
            if "/Dest" in value:
                self.validate_destination(value.raw_get("/Dest"), f"{location}/Dest")
            for key, child in value.items():
                self.walk(child, f"{location}/{str(key).lstrip('/')}")
        elif isinstance(value, (ArrayObject, list, tuple)):
            for index, child in enumerate(value):
                self.walk(child, f"{location}[{index}]")


def audit_pdf(
    source: PurePosixPath,
    blob: bytes,
    entries: dict[PurePosixPath, IndexEntry],
    directories: frozenset[PurePosixPath],
    anchors: dict[PurePosixPath, frozenset[str]],
) -> tuple[list[str], int, int]:
    try:
        reader = PdfReader(BytesIO(blob), strict=True)
    except Exception as error:
        return [f"cannot parse indexed PDF strictly: {error}"], 0, 0
    if reader.is_encrypted:
        return ["encrypted publication PDFs are not admitted"], 0, 0
    audit = PdfLinkAudit(reader, source, entries, directories, anchors)
    try:
        root = reader.root_object
        names = root.raw_get("/Names") if "/Names" in root else None
        if isinstance(names, IndirectObject):
            names = names.get_object()
        if names is not None and not is_semantic_dictionary(names):
            audit.errors.append("catalog /Names is not a dictionary")
        elif is_semantic_dictionary(names):
            for forbidden in ("/JavaScript", "/EmbeddedFiles"):
                if forbidden in names:
                    audit.errors.append(
                        f"catalog /Names {forbidden} content is not admitted"
                    )
        uri_dictionary = root.raw_get("/URI") if "/URI" in root else None
        if isinstance(uri_dictionary, IndirectObject):
            uri_dictionary = uri_dictionary.get_object()
        if uri_dictionary is not None and not is_semantic_dictionary(uri_dictionary):
            audit.errors.append("catalog /URI is not a dictionary")
        elif is_semantic_dictionary(uri_dictionary) and "/Base" in uri_dictionary:
            audit.errors.append("catalog /URI /Base changes relative-link semantics")
        audit.validate_outline_navigation()
        audit.walk(reader.trailer, "trailer")
    except Exception as error:
        audit.errors.append(f"unexpected PDF object-graph failure: {error}")
    return audit.errors, audit.action_count, audit.destination_count


def main() -> int:
    if pypdf.__version__ != EXPECTED_PYPDF_VERSION:
        fail(f"requires pypdf {EXPECTED_PYPDF_VERSION}, observed {pypdf.__version__}")
    root = repository_root()
    module_path = Path(pypdf.__file__).resolve(strict=True)
    if module_path == root or root in module_path.parents:
        fail("pypdf resolved from inside the repository")
    pandoc = pandoc_executable(root)
    entries = read_index(root)
    tags = index_tags(root)
    if set(tags) != set(entries):
        fail("Git index stage and index-tag inventories differ")
    intended = intent_to_add_paths(root)
    errors: list[str] = []
    if intended:
        errors.extend(
            f"{path}: intent-to-add entries are not publication content"
            for path in sorted(intended, key=str)
        )

    markdown_paths = sorted(
        (path for path in entries if path.suffix.lower() in MARKDOWN_SUFFIXES),
        key=str,
    )
    for declared_pdf in sorted(ROOT_PUBLICATION_PDFS, key=str):
        if declared_pdf not in entries:
            errors.append(
                f"{declared_pdf}: declared root publication PDF is absent from the staged index"
            )
    pdf_paths = sorted(
        (
            path
            for path in entries
            if (
                path in ROOT_PUBLICATION_PDFS
                or (len(path.parts) >= 3 and path.parts[:2] == ("output", "pdf"))
            )
            and path.suffix.lower() == ".pdf"
        ),
        key=str,
    )
    if not markdown_paths:
        fail("Git index contains no Markdown documents")
    if not pdf_paths:
        errors.append("Git index contains no declared publication PDFs")

    audited_paths = sorted(set(markdown_paths) | set(pdf_paths), key=str)
    blobs: dict[PurePosixPath, bytes] = {}
    for path in audited_paths:
        blob = read_blob(root, entries[path])
        blobs[path] = blob
        worktree = read_stable_worktree_file(root, path)
        if worktree != blob:
            errors.append(
                f"{path}: worktree/index byte divergence "
                f"(index {sha256_bytes(blob)}, worktree {sha256_bytes(worktree)})"
            )

    worktree_pdfs, worktree_pdf_errors = worktree_publication_pdfs(root)
    errors.extend(worktree_pdf_errors)
    indexed_pdf_set = frozenset(pdf_paths)
    for path in sorted(worktree_pdfs - indexed_pdf_set, key=str):
        errors.append(
            f"{path}: worktree publication PDF is not present in the staged index"
        )
    for path in sorted(indexed_pdf_set - worktree_pdfs, key=str):
        errors.append(
            f"{path}: indexed publication PDF is absent from the worktree inventory"
        )

    links: list[Link] = []
    anchors: dict[PurePosixPath, frozenset[str]] = {}
    for source in markdown_paths:
        try:
            document = parse_markdown(pandoc, source, blobs[source])
            extracted, source_anchors = extract_markdown(source, document)
            links.extend(extracted)
            anchors[source] = source_anchors
        except ValueError as error:
            errors.append(f"{source}: {error}")

    directories = indexed_directories(entries)
    for link in links:
        for problem in validate_target(
            link.source,
            link.target,
            entries,
            directories,
            anchors,
            require_file=link.kind in {"markdown-image", "html-src"},
        ):
            errors.append(
                f"{link.source}:{link.line}: {link.kind} target "
                f"{link.target!r}: {problem}"
            )

    action_count = 0
    destination_count = 0
    for source in pdf_paths:
        pdf_errors, actions, destinations = audit_pdf(
            source, blobs[source], entries, directories, anchors
        )
        errors.extend(f"{source}: {error}" for error in pdf_errors)
        action_count += actions
        destination_count += destinations

    final_entries = read_index(root)
    final_tags = index_tags(root)
    final_intended = intent_to_add_paths(root)
    if final_entries != entries:
        errors.append("Git index changed during the publication-link audit")
    if final_intended != intended:
        errors.append("intent-to-add state changed during the publication-link audit")
    if final_tags != tags:
        errors.append("Git index flags changed during the publication-link audit")

    if errors:
        print(f"{CHECK_NAME}: FAILED ({len(errors)} problem(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "OK: publication links are portable from the staged snapshot "
        f"({len(markdown_paths)} Markdown files, {len(links)} rendered targets, "
        f"{len(pdf_paths)} PDFs, {action_count} unique PDF action dictionaries, "
        f"{destination_count} PDF destinations; external reachability is outside "
        "this deterministic gate)"
    )
    return 0


if __name__ == "__main__":
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        raise SystemExit(main())
    except AuditError as error:
        print(f"{CHECK_NAME}: FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
