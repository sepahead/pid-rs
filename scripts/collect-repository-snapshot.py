#!/usr/bin/env python3
"""Collect and validate the immutable repository cut used by the 1.0 audit.

The snapshot body is deterministic for unchanged repositories and GitHub release
state. Collection time lives in a separate envelope so it does not perturb the
snapshot digest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from typing import Any

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


SCHEMA = "pid-rs/repository-snapshot"
SCHEMA_REVISION = 2
COLLECTOR_REVISION = "pid-rs-repository-snapshot-collector/2"
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "audit"
    / "schemas"
    / "repository-snapshot.schema.json"
)
LEGACY_SCHEMA_PATH = SCHEMA_PATH.with_name("repository-snapshot-v1.schema.json")
LEGACY_V1_SNAPSHOT_SHA256 = (
    "b57e506bbf30183c29bea4ff062a3711a3e471400dd91ebbdd8f787152af4b56"
)
LEGACY_V1_COMMAND_LOG_SHA256 = (
    "419a3786364dd7f32c842b14e7db7dc461048e85f9a491c57b556f7dfaa7f16d"
)
LEGACY_V1_ENVELOPE_SHA256 = (
    "1d753d6d5fbd930499fd5bd8d99d4d2d3157e001392ef2008186387659ff32d7"
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LOCKFILE_NAMES = {
    "Cargo.lock",
    "uv.lock",
    "bun.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
}
TOOLCHAIN_NAMES = {
    "rust-toolchain",
    "rust-toolchain.toml",
    ".python-version",
    ".node-version",
    ".nvmrc",
}
CONTRACT_PATH_RE = re.compile(
    r"(?:contract|schema|protocol|producer|observation|evidence|receipt)", re.IGNORECASE
)
DEFAULT_REPOSITORIES = ("pid-rs", "prisoma", "galadriel", "crebain", "haldir")
DEFAULT_CLAIMS = {
    "pid-rs": "claimed_core",
    "prisoma": "not_claimed",
    "galadriel": "not_claimed",
    "crebain": "not_claimed",
    "haldir": "not_claimed",
}
CANONICAL_PID_RS_GIT_URLS = {
    "https://github.com/sepahead/pid-rs",
    "https://github.com/sepahead/pid-rs.git",
}


class SnapshotError(RuntimeError):
    """A repository cut is dirty, ambiguous, or structurally invalid."""


class CommandLog:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def run(
        self,
        repo_name: str,
        repo_path: Path,
        args: list[str],
        *,
        check: bool = True,
    ) -> str:
        completed = subprocess.run(
            args,
            cwd=repo_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.entries.append(
            {
                "command": args,
                "cwd": repo_name,
                "exit_code": completed.returncode,
                "stderr": completed.stderr,
                "stdout": completed.stdout,
            }
        )
        if check and completed.returncode != 0:
            rendered = " ".join(args)
            raise SnapshotError(
                f"{repo_name}: command failed ({completed.returncode}): {rendered}\n"
                f"{completed.stderr.strip()}"
            )
        return completed.stdout

    def status(self, repo_name: str, repo_path: Path, args: list[str]) -> int:
        completed = subprocess.run(
            args,
            cwd=repo_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.entries.append(
            {
                "command": args,
                "cwd": repo_name,
                "exit_code": completed.returncode,
                "stderr": completed.stderr,
                "stdout": completed.stdout,
            }
        )
        return completed.returncode

    def run_bytes(self, repo_name: str, repo_path: Path, args: list[str]) -> bytes:
        completed = subprocess.run(
            args,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.entries.append(
            {
                "command": args,
                "cwd": repo_name,
                "exit_code": completed.returncode,
                "stderr": completed.stderr.decode("utf-8", errors="replace"),
                "stdout": (
                    f"<binary {len(completed.stdout)} bytes; "
                    f"sha256={sha256_bytes(completed.stdout)}>"
                ),
            }
        )
        if completed.returncode != 0:
            rendered = " ".join(args)
            stderr = completed.stderr.decode("utf-8", errors="replace").strip()
            raise SnapshotError(
                f"{repo_name}: command failed ({completed.returncode}): {rendered}\n{stderr}"
            )
        return completed.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def require_sha1(value: str, field: str) -> None:
    if not SHA1_RE.fullmatch(value):
        raise SnapshotError(f"{field} must be a lowercase full 40-hex SHA-1")


def require_sha256(value: str, field: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise SnapshotError(f"{field} must be a lowercase 64-hex SHA-256")


def tracked_files(name: str, path: Path, commands: CommandLog) -> list[str]:
    output = commands.run(name, path, ["git", "ls-files", "-z"])
    return sorted(item for item in output.split("\0") if item)


def tracked_blob_bytes(
    name: str, repo_path: Path, relative: str, commands: CommandLog
) -> bytes:
    return commands.run_bytes(
        name, repo_path, ["git", "cat-file", "blob", f"HEAD:{relative}"]
    )


def hash_selected_files(
    name: str,
    repo_path: Path,
    tracked: list[str],
    predicate: Any,
    commands: CommandLog,
) -> list[dict[str, str]]:
    result = []
    for relative in tracked:
        if not predicate(relative):
            continue
        # Bind detailed hashes to the already-recorded HEAD tree, rather than to a worktree that
        # can be sparse, contain symlinks, or conceal edits with assume-unchanged index flags.
        blob = tracked_blob_bytes(name, repo_path, relative, commands)
        result.append({"path": relative, "sha256": sha256_bytes(blob)})
    return result


def parse_toml(data: bytes, label: str) -> dict[str, Any]:
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise SnapshotError(f"cannot parse {label}: {error}") from error
    if not isinstance(parsed, dict):
        raise SnapshotError(f"{label}: TOML root is not a table")
    return parsed


def collect_git_dependencies(
    name: str, repo_path: Path, tracked: list[str], commands: CommandLog
) -> list[dict[str, Any]]:
    dependencies: list[dict[str, Any]] = []

    def walk(node: Any, manifest: str, route: list[str]) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("git"), str):
                dependencies.append(
                    {
                        "declaration_path": ".".join(route),
                        "features": sorted(node.get("features", [])),
                        "git": node["git"],
                        "manifest": manifest,
                        "package": node.get("package"),
                        "pin_kind": next(
                            (key for key in ("rev", "tag", "branch") if key in node),
                            "unversioned",
                        ),
                        "pin_value": next(
                            (
                                node[key]
                                for key in ("rev", "tag", "branch")
                                if key in node
                            ),
                            None,
                        ),
                        "version": node.get("version"),
                    }
                )
            for key in sorted(node):
                walk(node[key], manifest, [*route, str(key)])
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, manifest, [*route, str(index)])

    for relative in tracked:
        if Path(relative).name != "Cargo.toml":
            continue
        manifest = tracked_blob_bytes(name, repo_path, relative, commands)
        walk(parse_toml(manifest, relative), relative, [])

    unique = {canonical_json_bytes(item): item for item in dependencies}
    return sorted(
        unique.values(),
        key=lambda item: (
            item["manifest"],
            item["declaration_path"],
            item["git"],
            str(item["pin_value"]),
        ),
    )


def collect_declared_rust_versions(
    name: str, repo_path: Path, tracked: list[str], commands: CommandLog
) -> list[dict[str, str]]:
    versions = []
    for relative in tracked:
        if Path(relative).name != "Cargo.toml":
            continue
        manifest = tracked_blob_bytes(name, repo_path, relative, commands)
        parsed = parse_toml(manifest, relative)
        package = parsed.get("package")
        workspace_package = parsed.get("workspace", {}).get("package")
        for route, table in (
            ("package", package),
            ("workspace.package", workspace_package),
        ):
            if isinstance(table, dict) and isinstance(table.get("rust-version"), str):
                versions.append(
                    {
                        "manifest": relative,
                        "route": f"{route}.rust-version",
                        "value": table["rust-version"],
                    }
                )
    return sorted(versions, key=lambda item: (item["manifest"], item["route"]))


def collect_remote_refs(
    name: str, path: Path, branch: str, commands: CommandLog
) -> tuple[str, list[dict[str, Any]]]:
    if branch == "DETACHED":
        raise SnapshotError(f"{name}: repository snapshot collection requires a branch")
    output = commands.run(
        name,
        path,
        [
            "git",
            "ls-remote",
            "--symref",
            "origin",
            "HEAD",
            f"refs/heads/{branch}",
            "refs/tags/*",
        ],
    )
    symref: str | None = None
    refs: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            continue
        try:
            value, ref = line.split("\t", 1)
        except ValueError as error:
            raise SnapshotError(
                f"{name}: malformed git ls-remote line: {line!r}"
            ) from error
        if value.startswith("ref: "):
            if ref != "HEAD" or symref is not None:
                raise SnapshotError(f"{name}: ambiguous remote HEAD symref")
            symref = value.removeprefix("ref: ")
            continue
        require_sha1(value, f"{name} remote ref {ref}")
        if ref in refs:
            raise SnapshotError(f"{name}: duplicate remote ref {ref}")
        refs[ref] = value

    expected_head = f"refs/heads/{branch}"
    if symref != expected_head:
        raise SnapshotError(
            f"{name}: remote HEAD points to {symref!r}, expected {expected_head!r}"
        )
    remote_head_sha = refs.get("HEAD")
    branch_sha = refs.get(expected_head)
    if remote_head_sha is None or branch_sha is None or remote_head_sha != branch_sha:
        raise SnapshotError(
            f"{name}: remote HEAD and {expected_head} are missing or disagree"
        )

    remote_tags = {
        ref.removeprefix("refs/tags/"): value
        for ref, value in refs.items()
        if ref.startswith("refs/tags/")
    }
    tags = []
    for tag_name in sorted(remote_tags):
        if tag_name.endswith("^{}"):
            continue
        object_sha = remote_tags[tag_name]
        peeled = remote_tags.get(f"{tag_name}^{{}}", object_sha)
        temporary_ref = f"refs/pid-rs-snapshot/tags/{tag_name}"
        commands.run(
            name, path, ["git", "update-ref", "-d", temporary_ref], check=False
        )
        try:
            commands.run(
                name,
                path,
                [
                    "git",
                    "fetch",
                    "--no-tags",
                    "origin",
                    f"refs/tags/{tag_name}:{temporary_ref}",
                ],
            )
            fetched_sha = commands.run(
                name, path, ["git", "rev-parse", temporary_ref]
            ).strip()
            if fetched_sha != object_sha:
                raise SnapshotError(
                    f"{name}: fetched tag {tag_name!r} differs from live remote projection"
                )
            object_type = commands.run(
                name, path, ["git", "cat-file", "-t", temporary_ref]
            ).strip()
            if peeled == object_sha:
                if object_type != "commit":
                    raise SnapshotError(
                        f"{name}: unpeeled remote tag {tag_name!r} targets {object_type}, not commit"
                    )
            else:
                if object_type != "tag":
                    raise SnapshotError(
                        f"{name}: peeled remote tag {tag_name!r} is not an annotated tag object"
                    )
                fetched_commit = commands.run(
                    name, path, ["git", "rev-parse", f"{temporary_ref}^{{commit}}"]
                ).strip()
                if fetched_commit != peeled:
                    raise SnapshotError(
                        f"{name}: annotated tag {tag_name!r} has inconsistent peeled commit"
                    )
            tags.append(
                {
                    "name": tag_name,
                    "object_sha": object_sha,
                    "object_type": object_type,
                    "peeled_commit_sha": peeled,
                }
            )
        finally:
            commands.run(
                name, path, ["git", "update-ref", "-d", temporary_ref], check=False
            )
    orphaned_peeled = sorted(
        tag_name
        for tag_name in remote_tags
        if tag_name.endswith("^{}") and tag_name.removesuffix("^{}") not in remote_tags
    )
    if orphaned_peeled:
        raise SnapshotError(
            f"{name}: peeled tag refs lack tag objects: {orphaned_peeled}"
        )
    return remote_head_sha, tags


def github_releases(organization: str, repository: str) -> dict[str, Any]:
    base_url = f"https://api.github.com/repos/{organization}/{repository}/releases"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": COLLECTOR_REVISION,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    parsed: list[Any] = []
    page = 1
    while True:
        url = f"{base_url}?per_page=100&page={page}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            raise SnapshotError(
                f"{repository}: cannot collect public GitHub release state: {error}"
            ) from error
        try:
            page_items = json.loads(body)
        except json.JSONDecodeError as error:
            raise SnapshotError(
                f"{repository}: GitHub returned invalid JSON"
            ) from error
        if not isinstance(page_items, list):
            raise SnapshotError(f"{repository}: GitHub release response is not a list")
        if len(page_items) > 100:
            raise SnapshotError(
                f"{repository}: GitHub release page exceeds per_page=100"
            )
        parsed.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
        if page > 1000:
            raise SnapshotError(
                f"{repository}: GitHub release pagination exceeded 1000 pages"
            )

    releases = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise SnapshotError(
                f"{repository}: GitHub release {index} is not an object"
            )
        required = ("draft", "id", "prerelease", "published_at", "tag_name")
        if any(key not in item for key in required):
            raise SnapshotError(
                f"{repository}: GitHub release {index} lacks required fields"
            )
        if not isinstance(item["draft"], bool) or not isinstance(
            item["prerelease"], bool
        ):
            raise SnapshotError(
                f"{repository}: GitHub release {index} has invalid boolean fields"
            )
        if (
            not isinstance(item["id"], int)
            or isinstance(item["id"], bool)
            or item["id"] <= 0
        ):
            raise SnapshotError(
                f"{repository}: GitHub release {index} has an invalid id"
            )
        if not isinstance(item["tag_name"], str) or not item["tag_name"]:
            raise SnapshotError(
                f"{repository}: GitHub release {index} has an invalid tag_name"
            )
        if item["published_at"] is not None and not isinstance(
            item["published_at"], str
        ):
            raise SnapshotError(
                f"{repository}: GitHub release {index} has invalid published_at"
            )
        immutable = item.get("immutable", False)
        if not isinstance(immutable, bool):
            raise SnapshotError(
                f"{repository}: GitHub release {index} has invalid immutable"
            )
        # Authentication is used to avoid public API rate exhaustion, but a privileged token can
        # make draft releases visible. The snapshot promises public release state, so exclude
        # drafts and keep the resulting projection independent of caller privilege.
        if item["draft"]:
            continue
        releases.append(
            {
                "draft": item["draft"],
                "id": item["id"],
                "immutable": immutable,
                "prerelease": item["prerelease"],
                "published_at": item.get("published_at"),
                "tag_name": item["tag_name"],
            }
        )
    releases = sorted(releases, key=lambda item: (item["tag_name"], item["id"]))
    ids = [item["id"] for item in releases]
    tags = [item["tag_name"] for item in releases]
    if len(ids) != len(set(ids)) or len(tags) != len(set(tags)):
        raise SnapshotError(
            f"{repository}: GitHub release pagination returned duplicate ids or tags"
        )
    return {
        "api_projection_sha256": sha256_bytes(canonical_json_bytes(releases)),
        "collection_status": "queried",
        "releases": releases,
    }


def collect_submodules(
    name: str, path: Path, commands: CommandLog
) -> list[dict[str, Any]]:
    raw = commands.run(
        name, path, ["git", "submodule", "status", "--recursive"], check=True
    )
    submodules = []
    for line in raw.splitlines():
        if not line:
            continue
        state = line[0]
        fields = line[1:].strip().split()
        if len(fields) < 2:
            raise SnapshotError(f"{name}: malformed submodule status line: {line!r}")
        checked_out_sha, relative = fields[0], fields[1]
        require_sha1(checked_out_sha, f"{name} submodule {relative} checked_out_sha")
        tree_line = commands.run(
            name, path, ["git", "ls-tree", "HEAD", "--", relative]
        ).strip()
        match = re.fullmatch(r"160000 commit ([0-9a-f]{40})\t(.+)", tree_line)
        if not match:
            raise SnapshotError(f"{name}: cannot resolve gitlink for {relative}")
        gitlink_sha = match.group(1)
        matches = state == " " and gitlink_sha == checked_out_sha
        if not matches:
            raise SnapshotError(
                f"{name}: submodule {relative} does not match gitlink "
                f"({checked_out_sha} != {gitlink_sha}, state={state!r})"
            )
        submodules.append(
            {
                "checked_out_sha": checked_out_sha,
                "gitlink_sha": gitlink_sha,
                "matches_gitlink": True,
                "path": relative,
                "status_prefix": state,
            }
        )
    return sorted(submodules, key=lambda item: item["path"])


def collect_repository(
    name: str,
    path: Path,
    organization: str,
    claim_status: str,
    commands: CommandLog,
    *,
    skip_github: bool,
) -> dict[str, Any]:
    if not (path / ".git").exists():
        raise SnapshotError(f"{name}: {path} is not a Git checkout")

    status_output = commands.run(
        name, path, ["git", "status", "--porcelain=v2", "--untracked-files=all"]
    )
    status_lines = status_output.splitlines()
    if status_lines:
        raise SnapshotError(f"{name}: checkout is dirty: {status_lines[0]}")

    branch = commands.run(name, path, ["git", "branch", "--show-current"]).strip()
    if not branch:
        branch = "DETACHED"
    commit_sha = commands.run(name, path, ["git", "rev-parse", "HEAD"]).strip()
    tree_sha = commands.run(name, path, ["git", "rev-parse", "HEAD^{tree}"]).strip()
    require_sha1(commit_sha, f"{name}.commit_sha")
    require_sha1(tree_sha, f"{name}.tree_sha")

    remote_url = commands.run(
        name, path, ["git", "config", "--get", "remote.origin.url"]
    ).strip()
    resolved_remote_url = commands.run(
        name, path, ["git", "remote", "get-url", "origin"]
    ).strip()
    expected_url = f"https://github.com/{organization}/{name}.git"
    if remote_url != expected_url or resolved_remote_url != expected_url:
        raise SnapshotError(
            f"{name}: origin must resolve without rewriting to {expected_url!r}; "
            f"configured={remote_url!r}, resolved={resolved_remote_url!r}"
        )
    remote_head_ref = f"origin/{branch}"
    remote_head_sha, tags = collect_remote_refs(name, path, branch, commands)
    if commit_sha != remote_head_sha:
        raise SnapshotError(
            f"{name}: checked-out HEAD {commit_sha} differs from {remote_head_ref} {remote_head_sha}"
        )

    tracked = tracked_files(name, path, commands)
    lockfiles = hash_selected_files(
        name,
        path,
        tracked,
        lambda relative: Path(relative).name in LOCKFILE_NAMES,
        commands,
    )
    toolchain_files = hash_selected_files(
        name,
        path,
        tracked,
        lambda relative: Path(relative).name in TOOLCHAIN_NAMES,
        commands,
    )
    contract_files = hash_selected_files(
        name,
        path,
        tracked,
        lambda relative: (
            bool(CONTRACT_PATH_RE.search(relative))
            and Path(relative).suffix.lower()
            in {".json", ".md", ".rs", ".toml", ".yaml", ".yml"}
        ),
        commands,
    )

    releases = (
        {"collection_status": "skipped", "releases": []}
        if skip_github
        else github_releases(organization, name)
    )
    declared_rust_versions = collect_declared_rust_versions(
        name, path, tracked, commands
    )
    git_dependencies = collect_git_dependencies(name, path, tracked, commands)
    submodules = collect_submodules(name, path, commands)

    final_remote_head_sha, final_tags = collect_remote_refs(
        name, path, branch, commands
    )
    if (final_remote_head_sha, final_tags) != (remote_head_sha, tags):
        raise SnapshotError(
            f"{name}: live remote HEAD or tags changed during collection"
        )
    if not skip_github:
        final_releases = github_releases(organization, name)
        if final_releases != releases:
            raise SnapshotError(
                f"{name}: public GitHub release state changed during collection"
            )

    # The collector cannot make multiple repositories and remote APIs globally atomic, but paired
    # remote/API observations plus these final local checks reject ordinary TOCTOU. Recheck every
    # local identity used above after all worktree reads so a concurrent edit, checkout, or origin
    # rewrite does not produce a mixed record.
    final_status = commands.run(
        name, path, ["git", "status", "--porcelain=v2", "--untracked-files=all"]
    ).splitlines()
    final_branch = commands.run(name, path, ["git", "branch", "--show-current"]).strip()
    if not final_branch:
        final_branch = "DETACHED"
    final_commit = commands.run(name, path, ["git", "rev-parse", "HEAD"]).strip()
    final_tree = commands.run(name, path, ["git", "rev-parse", "HEAD^{tree}"]).strip()
    final_remote_url = commands.run(
        name, path, ["git", "config", "--get", "remote.origin.url"]
    ).strip()
    final_resolved_remote_url = commands.run(
        name, path, ["git", "remote", "get-url", "origin"]
    ).strip()
    if final_status:
        raise SnapshotError(
            f"{name}: checkout changed during collection: {final_status[0]}"
        )
    if (final_branch, final_commit, final_tree) != (branch, commit_sha, tree_sha):
        raise SnapshotError(f"{name}: HEAD or branch changed during collection")
    if (final_remote_url, final_resolved_remote_url) != (
        remote_url,
        resolved_remote_url,
    ):
        raise SnapshotError(f"{name}: origin changed during collection")

    return {
        "branch": branch,
        "commit_sha": commit_sha,
        "contract_file_hashes": contract_files,
        "declared_rust_versions": declared_rust_versions,
        "git_dependencies": git_dependencies,
        "github_releases": releases,
        "head_tags": sorted(
            tag["name"] for tag in tags if tag["peeled_commit_sha"] == commit_sha
        ),
        "lockfiles": lockfiles,
        "name": name,
        "release_claim_status": claim_status,
        "remote_head_ref": remote_head_ref,
        "remote_head_sha": remote_head_sha,
        "remote_url": remote_url,
        "status_porcelain_v2": status_lines,
        "submodules": submodules,
        "tags": tags,
        "toolchain_files": toolchain_files,
        "tree_sha": tree_sha,
    }


def resolve_cross_repository_checks(
    repositories: list[dict[str, Any]], workspace: Path, commands: CommandLog
) -> dict[str, Any]:
    by_name = {item["name"]: item for item in repositories}
    checks: dict[str, Any] = {}

    prisoma = by_name.get("prisoma")
    if prisoma is not None:
        pid_submodule = next(
            (item for item in prisoma["submodules"] if item["path"] == "pid-rs"), None
        )
        if pid_submodule is None:
            raise SnapshotError("prisoma: required pid-rs gitlink is missing")
        checks["prisoma_pid_rs_submodule"] = pid_submodule

    galadriel = by_name.get("galadriel")
    pid_rs = by_name.get("pid-rs")
    if galadriel is not None and pid_rs is not None:
        dependencies = [
            item
            for item in galadriel["git_dependencies"]
            if item["git"].rstrip("/") in CANONICAL_PID_RS_GIT_URLS
        ]
        if not dependencies:
            raise SnapshotError("galadriel: no exact pid-rs Git dependency found")
        resolved = []
        pid_path = workspace / "pid-rs"
        for dependency in dependencies:
            pin = dependency["pin_value"]
            if dependency["pin_kind"] != "rev" or not isinstance(pin, str):
                raise SnapshotError(
                    "galadriel: pid-rs dependency must use an exact rev"
                )
            require_sha1(pin, "galadriel pid-rs dependency rev")
            commands.run(
                "pid-rs",
                pid_path,
                ["git", "cat-file", "-e", f"{pin}^{{commit}}"],
            )
            live_targets = {
                pid_rs["remote_head_sha"],
                *(tag["peeled_commit_sha"] for tag in pid_rs["tags"]),
            }
            reachable_from_live_ref = any(
                commands.status(
                    "pid-rs",
                    pid_path,
                    ["git", "merge-base", "--is-ancestor", pin, target],
                )
                == 0
                for target in sorted(live_targets)
            )
            if not reachable_from_live_ref:
                raise SnapshotError(
                    "galadriel: pid-rs dependency rev is not reachable from live remote HEAD or a live tag"
                )
            v1_tag = next(
                (tag for tag in pid_rs["tags"] if tag["name"] == "v1.0.0"), None
            )
            reachable = False
            if v1_tag is not None:
                status = commands.status(
                    "pid-rs",
                    pid_path,
                    [
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        pin,
                        v1_tag["peeled_commit_sha"],
                    ],
                )
                reachable = status == 0
            resolved.append(
                {
                    "declaration_path": dependency["declaration_path"],
                    "manifest": dependency["manifest"],
                    "pin_sha": pin,
                    "resolves_in_pid_rs": True,
                    "v1_0_0_tag_exists": v1_tag is not None,
                    "reachable_from_v1_0_0": reachable,
                }
            )
        checks["galadriel_pid_rs_dependency"] = resolved

    return checks


def validate_snapshot(snapshot: Any, *, allow_skipped_github: bool = False) -> int:
    if not isinstance(snapshot, dict):
        raise SnapshotError("snapshot root must be an object")
    revision = snapshot.get("schema_revision")
    collector_revision = snapshot.get("collector_revision")
    if revision == 1 and collector_revision == "pid-rs-repository-snapshot-collector/1":
        digest = sha256_bytes(canonical_json_bytes(snapshot))
        if digest != LEGACY_V1_SNAPSHOT_SHA256:
            raise SnapshotError(
                "legacy snapshot v1 is historical evidence; only its exact recorded digest is accepted"
            )
        schema_path = LEGACY_SCHEMA_PATH
    elif revision == SCHEMA_REVISION and collector_revision == COLLECTOR_REVISION:
        schema_path = SCHEMA_PATH
    else:
        raise SnapshotError(
            "unsupported repository snapshot schema/collector revision pair"
        )

    try:
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        validate_json_schema(snapshot, schema, name="repository-snapshot.json")
    except (OSError, json.JSONDecodeError, SchemaValidationError) as error:
        raise SnapshotError(
            f"repository snapshot schema validation failed: {error}"
        ) from error

    if revision == 1:
        return 1

    repositories = snapshot["repositories"]
    names: set[str] = set()
    for index, repository in enumerate(repositories):
        name = repository["name"]
        if name in names:
            raise SnapshotError(
                f"repositories[{index}].name must be unique and non-empty"
            )
        names.add(name)
        remote_match = re.fullmatch(
            r"https://github\.com/[^/]+/([^/]+)\.git", repository["remote_url"]
        )
        if remote_match is None or remote_match.group(1) != name:
            raise SnapshotError(
                f"{name}: remote_url repository name does not match the record"
            )
        if repository["commit_sha"] != repository["remote_head_sha"]:
            raise SnapshotError(f"{name}: commit_sha differs from live remote_head_sha")
        if repository["remote_head_ref"] != f"origin/{repository['branch']}":
            raise SnapshotError(
                f"{name}: remote_head_ref does not match the recorded branch"
            )

        for group in ("lockfiles", "toolchain_files", "contract_file_hashes"):
            paths = [item["path"] for item in repository[group]]
            if paths != sorted(paths) or len(paths) != len(set(paths)):
                raise SnapshotError(f"{name}.{group} paths must be unique and sorted")

        rust_versions = repository["declared_rust_versions"]
        rust_keys = [(item["manifest"], item["route"]) for item in rust_versions]
        if rust_keys != sorted(rust_keys) or len(rust_keys) != len(set(rust_keys)):
            raise SnapshotError(
                f"{name}.declared_rust_versions must be unique and sorted"
            )

        dependencies = repository["git_dependencies"]
        dependency_keys = [
            (
                item["manifest"],
                item["declaration_path"],
                item["git"],
                str(item["pin_value"]),
            )
            for item in dependencies
        ]
        if dependency_keys != sorted(dependency_keys) or len(dependency_keys) != len(
            set(dependency_keys)
        ):
            raise SnapshotError(f"{name}.git_dependencies must be unique and sorted")
        for dependency in dependencies:
            if dependency["features"] != sorted(dependency["features"]):
                raise SnapshotError(f"{name}: dependency features must be sorted")
            if (
                dependency["pin_kind"] == "unversioned"
                and dependency["pin_value"] is not None
            ):
                raise SnapshotError(f"{name}: unversioned dependency has a pin value")
            if dependency["pin_kind"] != "unversioned" and not isinstance(
                dependency["pin_value"], str
            ):
                raise SnapshotError(f"{name}: versioned dependency lacks a pin value")

        tags = repository["tags"]
        tag_names = [tag["name"] for tag in tags]
        if tag_names != sorted(tag_names) or len(tag_names) != len(set(tag_names)):
            raise SnapshotError(f"{name}.tags must have unique sorted names")
        for tag in tags:
            if (
                tag["object_type"] == "commit"
                and tag["object_sha"] != tag["peeled_commit_sha"]
            ):
                raise SnapshotError(f"{name}: lightweight tag object and commit differ")
            if (
                tag["object_type"] == "tag"
                and tag["object_sha"] == tag["peeled_commit_sha"]
            ):
                raise SnapshotError(
                    f"{name}: annotated tag object equals its peeled commit"
                )
        expected_head_tags = sorted(
            tag["name"]
            for tag in tags
            if tag["peeled_commit_sha"] == repository["commit_sha"]
        )
        if repository["head_tags"] != expected_head_tags:
            raise SnapshotError(
                f"{name}: head_tags do not match the recorded remote tags"
            )

        submodules = repository["submodules"]
        submodule_paths = [submodule["path"] for submodule in submodules]
        if submodule_paths != sorted(submodule_paths) or len(submodule_paths) != len(
            set(submodule_paths)
        ):
            raise SnapshotError(f"{name}.submodules must have unique sorted paths")
        for submodule in submodules:
            if submodule["checked_out_sha"] != submodule["gitlink_sha"]:
                raise SnapshotError(
                    f"{name}: submodule checkout differs from its gitlink"
                )

        release_record = repository["github_releases"]
        releases = release_record["releases"]
        if (
            release_record["collection_status"] == "skipped"
            and not allow_skipped_github
        ):
            raise SnapshotError(
                f"{name}: skipped GitHub release state is accepted only with --skip-github"
            )
        release_keys = [(release["tag_name"], release["id"]) for release in releases]
        if release_keys != sorted(release_keys) or len(release_keys) != len(
            set(release_keys)
        ):
            raise SnapshotError(f"{name}: GitHub releases must be unique and sorted")
        release_ids = [release["id"] for release in releases]
        release_tags = [release["tag_name"] for release in releases]
        if len(release_ids) != len(set(release_ids)) or len(release_tags) != len(
            set(release_tags)
        ):
            raise SnapshotError(
                f"{name}: GitHub release ids and tags must each be unique"
            )
        if release_record["collection_status"] == "queried":
            if any(release["draft"] for release in releases):
                raise SnapshotError(
                    f"{name}: public GitHub release projection contains a draft"
                )
            expected_digest = sha256_bytes(canonical_json_bytes(releases))
            if release_record["api_projection_sha256"] != expected_digest:
                raise SnapshotError(
                    f"{name}: GitHub release projection digest mismatch"
                )

    by_name = {repository["name"]: repository for repository in repositories}
    claimed = sorted(
        repository["name"]
        for repository in repositories
        if repository["release_claim_status"] == "claimed_core"
    )
    if claimed != ["pid-rs"]:
        raise SnapshotError(
            "pid-rs-core-only snapshots must claim exactly pid-rs and no downstream repository"
        )

    cross_checks = snapshot["cross_repository_checks"]
    expected_cross_checks: set[str] = set()
    if "prisoma" in by_name:
        expected_cross_checks.add("prisoma_pid_rs_submodule")
    if "galadriel" in by_name and "pid-rs" in by_name:
        expected_cross_checks.add("galadriel_pid_rs_dependency")
    if set(cross_checks) != expected_cross_checks:
        raise SnapshotError(
            "cross_repository_checks do not exactly cover the repositories in this snapshot"
        )
    prisoma_check = cross_checks.get("prisoma_pid_rs_submodule")
    if prisoma_check is not None:
        prisoma = by_name.get("prisoma")
        if (
            prisoma is None
            or prisoma_check["path"] != "pid-rs"
            or prisoma_check not in prisoma["submodules"]
        ):
            raise SnapshotError(
                "Prisoma cross-check is not bound to its repository record"
            )

    dependency_checks = cross_checks.get("galadriel_pid_rs_dependency", [])
    if dependency_checks:
        galadriel = by_name.get("galadriel")
        pid_rs = by_name.get("pid-rs")
        if galadriel is None or pid_rs is None:
            raise SnapshotError(
                "Galadriel dependency checks require both repository records"
            )
        expected_dependency_keys = []
        for dependency in galadriel["git_dependencies"]:
            if dependency["git"].rstrip("/") not in CANONICAL_PID_RS_GIT_URLS:
                continue
            if dependency["pin_kind"] != "rev" or not isinstance(
                dependency["pin_value"], str
            ):
                raise SnapshotError(
                    "Galadriel pid-rs dependencies must use exact revisions"
                )
            require_sha1(dependency["pin_value"], "Galadriel pid-rs dependency pin")
            expected_dependency_keys.append(
                (
                    dependency["manifest"],
                    dependency["declaration_path"],
                    dependency["pin_value"],
                )
            )
        expected_dependency_keys.sort()
        check_keys = [
            (check["manifest"], check["declaration_path"], check["pin_sha"])
            for check in dependency_checks
        ]
        if (
            check_keys != sorted(check_keys)
            or len(check_keys) != len(set(check_keys))
            or check_keys != expected_dependency_keys
        ):
            raise SnapshotError(
                "Galadriel dependency cross-checks must uniquely and completely cover pid-rs dependencies"
            )
        v1_tag_exists = any(tag["name"] == "v1.0.0" for tag in pid_rs["tags"])
        for check in dependency_checks:
            matching = [
                dependency
                for dependency in galadriel["git_dependencies"]
                if dependency["manifest"] == check["manifest"]
                and dependency["declaration_path"] == check["declaration_path"]
                and dependency["pin_kind"] == "rev"
                and dependency["pin_value"] == check["pin_sha"]
                and dependency["git"].rstrip("/") in CANONICAL_PID_RS_GIT_URLS
            ]
            if len(matching) != 1:
                raise SnapshotError(
                    "Galadriel dependency cross-check lacks one exact source record"
                )
            if check["v1_0_0_tag_exists"] != v1_tag_exists:
                raise SnapshotError(
                    "Galadriel dependency cross-check has stale v1.0.0 tag state"
                )
            if not v1_tag_exists and check["reachable_from_v1_0_0"]:
                raise SnapshotError(
                    "dependency cannot be reachable from a missing v1.0.0 tag"
                )
    return 2


def validate_legacy_v1_bundle(snapshot_path: Path) -> None:
    evidence_dir = snapshot_path.parent
    sidecar = evidence_dir / "repository-snapshot.json.sha256"
    envelope = evidence_dir / "repository-snapshot-envelope.json"
    command_log = evidence_dir / "repository-snapshot-command-log.json"
    expected_sidecar = f"{LEGACY_V1_SNAPSHOT_SHA256}  repository-snapshot.json\n"
    if sidecar.read_text(encoding="utf-8") != expected_sidecar:
        raise SnapshotError("historical snapshot v1 sidecar is missing or stale")
    if sha256_file(envelope) != LEGACY_V1_ENVELOPE_SHA256:
        raise SnapshotError(
            "historical snapshot v1 envelope differs from recorded provenance"
        )
    if sha256_file(command_log) != LEGACY_V1_COMMAND_LOG_SHA256:
        raise SnapshotError(
            "historical snapshot v1 command log differs from recorded provenance"
        )

    envelope_value = json.loads(envelope.read_text(encoding="utf-8"))
    if (
        envelope_value.get("collector_revision")
        != "pid-rs-repository-snapshot-collector/1"
        or envelope_value.get("snapshot_sha256") != LEGACY_V1_SNAPSHOT_SHA256
    ):
        raise SnapshotError(
            "historical snapshot v1 envelope is internally inconsistent"
        )

    log_value = json.loads(command_log.read_text(encoding="utf-8"))
    commands = [entry.get("command", []) for entry in log_value.get("commands", [])]
    if (
        log_value.get("collector_revision") != "pid-rs-repository-snapshot-collector/1"
        or not any(command[:2] == ["git", "for-each-ref"] for command in commands)
        or not any("refs/remotes/origin/HEAD" in command for command in commands)
        or any("ls-remote" in command for command in commands)
    ):
        raise SnapshotError(
            "historical snapshot v1 command log does not disclose cached-ref/local-tag semantics"
        )


def render_markdown(snapshot: dict[str, Any], digest: str) -> str:
    lines = [
        "# pid-rs repository snapshot v2",
        "",
        "This is a human-readable rendering of `repository-snapshot.json`. Collector v2 records",
        "the exact clean cut and queries remote HEAD and tag refs live. Only `pid-rs` core is",
        "claimed; all downstream repositories are explicitly `not_claimed`.",
        "",
        f"Snapshot SHA-256: `{digest}`",
        "",
        "| Repository | Branch | Commit | Tree | Claim status | Clean | Head tags | Releases |",
        "|---|---|---|---|---|---:|---|---:|",
    ]
    for repository in snapshot["repositories"]:
        release_count = len(repository["github_releases"]["releases"])
        tags = ", ".join(repository["head_tags"]) or "none"
        lines.append(
            "| {name} | `{branch}` | `{commit}` | `{tree}` | `{claim}` | yes | {tags} | {releases} |".format(
                name=repository["name"],
                branch=repository["branch"],
                commit=repository["commit_sha"],
                tree=repository["tree_sha"],
                claim=repository["release_claim_status"],
                tags=tags,
                releases=release_count,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This snapshot proves repository identity and cleanliness only. It does not prove",
            "mathematical correctness, estimator validity, consumer compatibility, application",
            "validity, operational safety, or publication. A changed `pid-rs` commit requires new",
            "candidate evidence; it does not rewrite this historical audit cut.",
            "",
        ]
    )
    return "\n".join(lines)


def collect(args: argparse.Namespace) -> tuple[dict[str, Any], CommandLog]:
    workspace = args.workspace.resolve()
    names = tuple(item.strip() for item in args.repositories.split(",") if item.strip())
    if not names:
        raise SnapshotError("at least one repository is required")
    if len(names) != len(set(names)):
        raise SnapshotError("repository names must be unique")
    if any(
        re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?", name) is None
        for name in names
    ):
        raise SnapshotError("repository names must be single safe path components")
    claims = dict(DEFAULT_CLAIMS)
    assigned_claims: set[str] = set()
    for assignment in args.claim:
        if "=" not in assignment:
            raise SnapshotError(f"invalid --claim value: {assignment!r}")
        name, status = assignment.split("=", 1)
        if name not in names:
            raise SnapshotError(f"--claim names an uncollected repository: {name!r}")
        if name in assigned_claims:
            raise SnapshotError(
                f"duplicate --claim assignment for repository: {name!r}"
            )
        if status not in {"claimed_core", "not_claimed"}:
            raise SnapshotError(f"invalid release claim status: {status!r}")
        assigned_claims.add(name)
        claims[name] = status
    commands = CommandLog()
    repositories = [
        collect_repository(
            name,
            workspace / name,
            args.organization,
            claims.get(name, "not_claimed"),
            commands,
            skip_github=args.skip_github,
        )
        for name in names
    ]
    snapshot = {
        "canonicalization": "UTF-8; JSON object keys sorted lexicographically; two-space indentation; final LF",
        "collector_revision": COLLECTOR_REVISION,
        "cross_repository_checks": resolve_cross_repository_checks(
            repositories, workspace, commands
        ),
        "release_scope": "pid-rs-core-only",
        "repositories": repositories,
        "schema": SCHEMA,
        "schema_revision": SCHEMA_REVISION,
    }
    validate_snapshot(snapshot, allow_skipped_github=args.skip_github)
    return snapshot, commands


def write_outputs(
    output_dir: Path,
    snapshot: dict[str, Any],
    commands: CommandLog,
    collected_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_bytes = canonical_json_bytes(snapshot)
    digest = sha256_bytes(snapshot_bytes)
    (output_dir / "repository-snapshot.json").write_bytes(snapshot_bytes)
    (output_dir / "repository-snapshot.json.sha256").write_text(
        f"{digest}  repository-snapshot.json\n", encoding="utf-8"
    )
    envelope = {
        "collected_at_utc": collected_at,
        "collector_revision": COLLECTOR_REVISION,
        "snapshot_sha256": digest,
        "source_kind": "clean_public_https_clones",
    }
    (output_dir / "repository-snapshot-envelope.json").write_bytes(
        canonical_json_bytes(envelope)
    )
    command_log = {
        "collector_revision": COLLECTOR_REVISION,
        "commands": commands.entries,
        "schema": "pid-rs/repository-snapshot-command-log",
        "schema_revision": 1,
    }
    (output_dir / "repository-snapshot-command-log.json").write_bytes(
        canonical_json_bytes(command_log)
    )
    (output_dir / "repository-snapshot.md").write_text(
        render_markdown(snapshot, digest), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace", type=Path, help="parent directory containing repositories"
    )
    parser.add_argument(
        "--output-dir", type=Path, help="directory for generated evidence"
    )
    parser.add_argument("--organization", default="sepahead")
    parser.add_argument("--repositories", default=",".join(DEFAULT_REPOSITORIES))
    parser.add_argument(
        "--claim",
        action="append",
        default=[],
        metavar="REPOSITORY=STATUS",
        help="override claimed_core/not_claimed status",
    )
    parser.add_argument(
        "--skip-github",
        action="store_true",
        help=(
            "explicitly allow a test-only snapshot with GitHub release collection skipped "
            "(required again when validating that snapshot)"
        ),
    )
    parser.add_argument(
        "--validate", type=Path, help="validate an existing snapshot and exit"
    )
    parser.add_argument(
        "--compare", type=Path, help="fail unless generated bytes equal this file"
    )
    parser.add_argument(
        "--collected-at",
        help="UTC RFC3339 timestamp for the separate envelope (defaults to current UTC)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.validate is not None:
            with args.validate.open("rb") as handle:
                snapshot = json.load(handle)
            revision = validate_snapshot(
                snapshot, allow_skipped_github=args.skip_github
            )
            canonical = canonical_json_bytes(snapshot)
            if args.validate.read_bytes() != canonical:
                raise SnapshotError(
                    "snapshot is valid but not in canonical repository format"
                )
            if revision == 1:
                validate_legacy_v1_bundle(args.validate)
                print(
                    "OK: exact historical snapshot v1 validated "
                    "(legacy cached-ref/local-tag provenance)"
                )
            elif any(
                repository["github_releases"]["collection_status"] == "skipped"
                for repository in snapshot["repositories"]
            ):
                print(
                    "OK: repository snapshot v2 validated "
                    "(GitHub release projection explicitly skipped)"
                )
            else:
                print("OK: repository snapshot v2 live-remote projection validated")
            return 0

        if args.workspace is None:
            raise SnapshotError("--workspace is required when collecting")
        snapshot, commands = collect(args)
        snapshot_bytes = canonical_json_bytes(snapshot)
        if args.compare is not None and args.compare.read_bytes() != snapshot_bytes:
            raise SnapshotError(
                f"generated repository cut differs from {args.compare}; evidence is stale"
            )
        if args.output_dir is not None:
            collected_at = args.collected_at or dt.datetime.now(
                dt.timezone.utc
            ).isoformat(timespec="seconds").replace("+00:00", "Z")
            if (
                re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
                    collected_at,
                )
                is None
            ):
                raise SnapshotError(
                    "--collected-at must be a UTC RFC3339 timestamp ending in Z"
                )
            try:
                parsed_collected_at = dt.datetime.fromisoformat(
                    collected_at.removesuffix("Z") + "+00:00"
                )
            except ValueError as error:
                raise SnapshotError(
                    "--collected-at is not a valid calendar timestamp"
                ) from error
            if parsed_collected_at.tzinfo != dt.timezone.utc:
                raise SnapshotError("--collected-at must use UTC")
            write_outputs(args.output_dir, snapshot, commands, collected_at)
        elif args.compare is None:
            sys.stdout.buffer.write(snapshot_bytes)
        return 0
    except (OSError, SnapshotError, json.JSONDecodeError) as error:
        print(f"repository snapshot error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
