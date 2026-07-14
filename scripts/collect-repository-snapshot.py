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


SCHEMA = "pid-rs/repository-snapshot"
SCHEMA_REVISION = 1
COLLECTOR_REVISION = "pid-rs-repository-snapshot-collector/1"
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


def hash_selected_files(
    repo_path: Path, tracked: list[str], predicate: Any
) -> list[dict[str, str]]:
    result = []
    for relative in tracked:
        if not predicate(relative):
            continue
        candidate = repo_path / relative
        if candidate.is_file():
            result.append({"path": relative, "sha256": sha256_file(candidate)})
    return result


def parse_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            parsed = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise SnapshotError(f"cannot parse {path.name}: {error}") from error
    if not isinstance(parsed, dict):
        raise SnapshotError(f"{path.name}: TOML root is not a table")
    return parsed


def collect_git_dependencies(repo_path: Path, tracked: list[str]) -> list[dict[str, Any]]:
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
                            (node[key] for key in ("rev", "tag", "branch") if key in node),
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
        walk(parse_toml(repo_path / relative), relative, [])

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
    repo_path: Path, tracked: list[str]
) -> list[dict[str, str]]:
    versions = []
    for relative in tracked:
        if Path(relative).name != "Cargo.toml":
            continue
        parsed = parse_toml(repo_path / relative)
        package = parsed.get("package")
        workspace_package = parsed.get("workspace", {}).get("package")
        for route, table in (("package", package), ("workspace.package", workspace_package)):
            if isinstance(table, dict) and isinstance(table.get("rust-version"), str):
                versions.append(
                    {
                        "manifest": relative,
                        "route": f"{route}.rust-version",
                        "value": table["rust-version"],
                    }
                )
    return sorted(versions, key=lambda item: (item["manifest"], item["route"]))


def collect_tags(name: str, path: Path, commands: CommandLog) -> list[dict[str, Any]]:
    output = commands.run(
        name,
        path,
        [
            "git",
            "for-each-ref",
            "--format=%(refname:strip=2)%00%(objectname)%00%(objecttype)",
            "refs/tags",
        ],
    )
    tags = []
    for line in output.splitlines():
        if not line:
            continue
        tag_name, object_sha, object_type = line.split("\0")
        require_sha1(object_sha, f"{name} tag {tag_name} object_sha")
        peeled = commands.run(
            name,
            path,
            ["git", "rev-parse", f"{tag_name}^{{commit}}"],
        ).strip()
        require_sha1(peeled, f"{name} tag {tag_name} peeled_commit_sha")
        tags.append(
            {
                "name": tag_name,
                "object_sha": object_sha,
                "object_type": object_type,
                "peeled_commit_sha": peeled,
            }
        )
    return sorted(tags, key=lambda item: item["name"])


def github_releases(organization: str, repository: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{organization}/{repository}/releases?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": COLLECTOR_REVISION,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise SnapshotError(
            f"{repository}: cannot collect public GitHub release state: {error}"
        ) from error
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as error:
        raise SnapshotError(f"{repository}: GitHub returned invalid JSON") from error
    if not isinstance(parsed, list):
        raise SnapshotError(f"{repository}: GitHub release response is not a list")
    releases = []
    for item in parsed:
        releases.append(
            {
                "draft": bool(item["draft"]),
                "id": int(item["id"]),
                "immutable": bool(item.get("immutable", False)),
                "prerelease": bool(item["prerelease"]),
                "published_at": item.get("published_at"),
                "tag_name": item["tag_name"],
            }
        )
    return {
        "api_projection_sha256": sha256_bytes(canonical_json_bytes(releases)),
        "collection_status": "queried",
        "releases": sorted(releases, key=lambda item: (item["tag_name"], item["id"])),
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
        name, path, ["git", "remote", "get-url", "origin"]
    ).strip()
    expected_url = f"https://github.com/{organization}/{name}.git"
    if remote_url != expected_url:
        raise SnapshotError(
            f"{name}: origin must be the public HTTPS URL {expected_url!r}, got {remote_url!r}"
        )
    remote_head_ref = commands.run(
        name,
        path,
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
    ).strip()
    remote_head_sha = commands.run(
        name, path, ["git", "rev-parse", "refs/remotes/origin/HEAD"]
    ).strip()
    require_sha1(remote_head_sha, f"{name}.remote_head_sha")
    if commit_sha != remote_head_sha:
        raise SnapshotError(
            f"{name}: checked-out HEAD {commit_sha} differs from {remote_head_ref} {remote_head_sha}"
        )

    tracked = tracked_files(name, path, commands)
    lockfiles = hash_selected_files(
        path, tracked, lambda relative: Path(relative).name in LOCKFILE_NAMES
    )
    toolchain_files = hash_selected_files(
        path, tracked, lambda relative: Path(relative).name in TOOLCHAIN_NAMES
    )
    contract_files = hash_selected_files(
        path,
        tracked,
        lambda relative: bool(CONTRACT_PATH_RE.search(relative))
        and Path(relative).suffix.lower() in {".json", ".md", ".rs", ".toml", ".yaml", ".yml"},
    )

    releases = (
        {"collection_status": "skipped", "releases": []}
        if skip_github
        else github_releases(organization, name)
    )
    tags = collect_tags(name, path, commands)

    return {
        "branch": branch,
        "commit_sha": commit_sha,
        "contract_file_hashes": contract_files,
        "declared_rust_versions": collect_declared_rust_versions(path, tracked),
        "git_dependencies": collect_git_dependencies(path, tracked),
        "github_releases": releases,
        "head_tags": sorted(tag["name"] for tag in tags if tag["peeled_commit_sha"] == commit_sha),
        "lockfiles": lockfiles,
        "name": name,
        "release_claim_status": claim_status,
        "remote_head_ref": remote_head_ref,
        "remote_head_sha": remote_head_sha,
        "remote_url": remote_url,
        "status_porcelain_v2": status_lines,
        "submodules": collect_submodules(name, path, commands),
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
            if item["git"].rstrip("/").endswith("sepahead/pid-rs")
        ]
        if not dependencies:
            raise SnapshotError("galadriel: no exact pid-rs Git dependency found")
        resolved = []
        pid_path = workspace / "pid-rs"
        for dependency in dependencies:
            pin = dependency["pin_value"]
            if dependency["pin_kind"] != "rev" or not isinstance(pin, str):
                raise SnapshotError("galadriel: pid-rs dependency must use an exact rev")
            require_sha1(pin, "galadriel pid-rs dependency rev")
            commands.run(
                "pid-rs",
                pid_path,
                ["git", "cat-file", "-e", f"{pin}^{{commit}}"],
            )
            v1_tag = next((tag for tag in pid_rs["tags"] if tag["name"] == "v1.0.0"), None)
            reachable = False
            if v1_tag is not None:
                status = commands.status(
                    "pid-rs",
                    pid_path,
                    ["git", "merge-base", "--is-ancestor", pin, v1_tag["peeled_commit_sha"]],
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


def validate_snapshot(snapshot: Any) -> None:
    if not isinstance(snapshot, dict):
        raise SnapshotError("snapshot root must be an object")
    if snapshot.get("schema") != SCHEMA or snapshot.get("schema_revision") != SCHEMA_REVISION:
        raise SnapshotError("unsupported repository snapshot schema")
    repositories = snapshot.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise SnapshotError("repositories must be a non-empty array")
    names: set[str] = set()
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            raise SnapshotError(f"repositories[{index}] must be an object")
        name = repository.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise SnapshotError(f"repositories[{index}].name must be unique and non-empty")
        names.add(name)
        require_sha1(repository.get("commit_sha", ""), f"{name}.commit_sha")
        require_sha1(repository.get("tree_sha", ""), f"{name}.tree_sha")
        require_sha1(repository.get("remote_head_sha", ""), f"{name}.remote_head_sha")
        if repository.get("status_porcelain_v2") != []:
            raise SnapshotError(f"{name}: recorded checkout is not clean")
        if repository.get("release_claim_status") not in {"claimed_core", "not_claimed"}:
            raise SnapshotError(f"{name}: invalid release_claim_status")
        for group in ("lockfiles", "toolchain_files", "contract_file_hashes"):
            if not isinstance(repository.get(group), list):
                raise SnapshotError(f"{name}.{group} must be an array")
            for item in repository[group]:
                require_sha256(item.get("sha256", ""), f"{name}.{group}.sha256")
        for tag in repository.get("tags", []):
            require_sha1(tag.get("object_sha", ""), f"{name}.tag.object_sha")
            require_sha1(
                tag.get("peeled_commit_sha", ""), f"{name}.tag.peeled_commit_sha"
            )
        for submodule in repository.get("submodules", []):
            require_sha1(
                submodule.get("gitlink_sha", ""), f"{name}.submodule.gitlink_sha"
            )
            require_sha1(
                submodule.get("checked_out_sha", ""),
                f"{name}.submodule.checked_out_sha",
            )
            if submodule.get("matches_gitlink") is not True:
                raise SnapshotError(f"{name}: submodule mismatch recorded")


def render_markdown(snapshot: dict[str, Any], digest: str) -> str:
    lines = [
        "# pid-rs 1.0 repository snapshot",
        "",
        "This is a human-readable rendering of `repository-snapshot.json`. It records the exact",
        "moving-branch cut used to begin the 1.0 audit. Only `pid-rs` core is claimed; all",
        "downstream repositories are explicitly `not_claimed` and are therefore non-blocking.",
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
    claims = dict(DEFAULT_CLAIMS)
    for assignment in args.claim:
        if "=" not in assignment:
            raise SnapshotError(f"invalid --claim value: {assignment!r}")
        name, status = assignment.split("=", 1)
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
    validate_snapshot(snapshot)
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
    parser.add_argument("--workspace", type=Path, help="parent directory containing repositories")
    parser.add_argument("--output-dir", type=Path, help="directory for generated evidence")
    parser.add_argument("--organization", default="sepahead")
    parser.add_argument("--repositories", default=",".join(DEFAULT_REPOSITORIES))
    parser.add_argument(
        "--claim",
        action="append",
        default=[],
        metavar="REPOSITORY=STATUS",
        help="override claimed_core/not_claimed status",
    )
    parser.add_argument("--skip-github", action="store_true")
    parser.add_argument("--validate", type=Path, help="validate an existing snapshot and exit")
    parser.add_argument("--compare", type=Path, help="fail unless generated bytes equal this file")
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
            validate_snapshot(snapshot)
            canonical = canonical_json_bytes(snapshot)
            if args.validate.read_bytes() != canonical:
                raise SnapshotError("snapshot is valid but not in canonical repository format")
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
            write_outputs(args.output_dir, snapshot, commands, collected_at)
        elif args.compare is None:
            sys.stdout.buffer.write(snapshot_bytes)
        return 0
    except (OSError, SnapshotError, json.JSONDecodeError) as error:
        print(f"repository snapshot error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
