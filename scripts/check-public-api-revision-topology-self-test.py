#!/usr/bin/env python3
"""Hostile controls for the revision 0-4 source/evidence topology."""

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
    and _bootstrap_sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-public-api-revision-topology-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-release-scope.py"


def load_checker() -> Any:
    sys.path.insert(0, str(CHECKER.parent))
    spec = importlib.util.spec_from_file_location("pid_rs_api_topology", CHECKER)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load release-scope checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker()


def canonical(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def fixture_git(root: Path, *args: str) -> str:
    environment = checker.scrubbed_git_environment()
    environment.update(
        {
            "GIT_AUTHOR_EMAIL": "api-topology@example.invalid",
            "GIT_AUTHOR_NAME": "API Topology Test",
            "GIT_COMMITTER_EMAIL": "api-topology@example.invalid",
            "GIT_COMMITTER_NAME": "API Topology Test",
        }
    )
    process = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        cwd=root,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        raise SystemExit(
            f"fixture git {' '.join(args)} failed: "
            f"{process.stderr.strip() or process.stdout.strip()}"
        )
    return process.stdout.strip()


def commit_all(root: Path, message: str) -> str:
    fixture_git(root, "add", "-A")
    fixture_git(root, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", message)
    return fixture_git(root, "rev-parse", "HEAD")


PROFILE_IDS = [
    "pid-core-all-features",
    "pid-core-default",
    "pid-core-experimental-all",
    "pid-core-experimental-continuous",
    "pid-core-experimental-heuristics",
    "pid-core-experimental-hierarchy",
    "pid-core-experimental-hyperbolic",
    "pid-core-experimental-pipelines",
    "pid-core-parallel",
    "pid-core-research-mixed-dimension-pid3",
]


def build_fixture(
    root: Path,
    *,
    commit_evidence: bool = True,
    register_base_as_source: bool = False,
    wrong_content_digest: bool = False,
) -> dict[str, Any]:
    root.mkdir()
    fixture_git(root, "init", "-q", "-b", "main")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    base = commit_all(root, "base")

    historical_entries = [
        {
            "epoch": 0,
            "generation": deepcopy(checker.API_SNAPSHOT_GENERATION),
            "profiles": [
                {
                    "id": "pid-core-default",
                    "public_api_snapshot": (
                        f"audit/api/public-api/revisions/0-{revision}/pid-core-default.txt"
                    ),
                    "public_api_snapshot_sha256": f"{revision}" * 64,
                }
            ],
            "revision": revision,
            "scope": "proposed_release_scope_profiles",
            "snapshot_source_commit_sha": "1" * 40,
            "snapshot_source_tree_sha": "2" * 40,
            "status": "pre_1_0_review",
        }
        for revision in (1, 2, 3)
    ]
    registry = {
        "append_policy": "strict_prefix_by_epoch_revision",
        "entries": historical_entries,
        "genesis_source_commit_sha": checker.SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT,
        "genesis_source_tree_sha": checker.SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE,
        "package": "pid-core",
        "schema": checker.SIGNATURE_REGISTRY_SCHEMA,
        "schema_revision": checker.SIGNATURE_REGISTRY_SCHEMA_REVISION,
    }
    registry_path = root / checker.SIGNATURE_REGISTRY_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(canonical(registry), encoding="utf-8")
    source = commit_all(root, "source")
    source_tree = fixture_git(root, "rev-parse", f"{source}^{{tree}}")

    physical: dict[str, bytes] = {}
    profiles: list[dict[str, str]] = []
    for profile_id in PROFILE_IDS:
        relative = (
            "audit/api/public-api/revisions/0-4/pid-core-experimental-all.txt"
            if profile_id == "pid-core-all-features"
            else f"audit/api/public-api/revisions/0-4/{profile_id}.txt"
        )
        raw = (
            b"pid-core-experimental-all\n"
            if profile_id
            in {
                "pid-core-all-features",
                "pid-core-experimental-all",
            }
            else f"{profile_id}\n".encode("utf-8")
        )
        physical.setdefault(relative, raw)
        digest = hashlib.sha256(raw).hexdigest()
        if wrong_content_digest and profile_id == "pid-core-default":
            digest = "0" * 64
        profiles.append(
            {
                "id": profile_id,
                "public_api_snapshot": relative,
                "public_api_snapshot_sha256": digest,
            }
        )
    entry = {
        "epoch": 0,
        "evidence_topology": deepcopy(checker.SOURCE_EVIDENCE_TOPOLOGY),
        "generation": deepcopy(checker.API_SNAPSHOT_GENERATION),
        "profiles": profiles,
        "revision": 4,
        "scope": "proposed_release_scope_profiles",
        "snapshot_source_commit_sha": base if register_base_as_source else source,
        "snapshot_source_tree_sha": (
            fixture_git(root, "rev-parse", f"{base}^{{tree}}")
            if register_base_as_source
            else source_tree
        ),
        "status": "pre_1_0_review",
    }
    registry["entries"].append(entry)
    for relative, raw in physical.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    registry_path.write_text(canonical(registry), encoding="utf-8")
    evidence = commit_all(root, "evidence") if commit_evidence else None
    return {
        "base": base,
        "entry": entry,
        "evidence": evidence,
        "registry": registry,
        "root": root,
        "source": source,
        "source_tree": source_tree,
    }


def expect_failure(label: str, expected: str, operation: Callable[[], None]) -> None:
    try:
        operation()
    except checker.ScopeError as error:
        if expected not in str(error):
            raise SystemExit(f"{label} failed for the wrong reason: {error}")
    else:
        raise SystemExit(f"{label} was accepted")


def topology(
    fixture: dict[str, Any], entry: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any] | None:
    return checker.validate_revision_four_source_evidence_topology(
        entry,
        registry,
        root=fixture["root"],
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-api-topology-") as temp_name:
        temp = Path(temp_name)
        fixture = build_fixture(temp / "valid")
        relation = topology(fixture, fixture["entry"], fixture["registry"])
        expected_relation = {
            "evidence_commit": fixture["evidence"],
            "evidence_parent_count": 1,
            "source_commit": fixture["source"],
        }
        if relation != expected_relation:
            raise SystemExit(f"valid source/evidence relation drifted: {relation!r}")
        result = checker.source_evidence_result(relation)
        if result != {
            "format": checker.SOURCE_EVIDENCE_RELATION_FORMAT,
            "source_evidence_relation": expected_relation,
            "status": "pass",
        }:
            raise SystemExit("bounded source/evidence result shape drifted")
        rendered_result = checker.canonical_json(result)
        if (
            json.loads(rendered_result) != result
            or checker.canonical_json(json.loads(rendered_result)) != rendered_result
            or "full_history" in rendered_result
            or str(temp) in rendered_result
        ):
            raise SystemExit("source/evidence result is not canonical and path-free")

        pending_fixture = build_fixture(temp / "pending", commit_evidence=False)
        pending_relation = topology(
            pending_fixture,
            pending_fixture["entry"],
            pending_fixture["registry"],
        )
        if pending_relation is not None:
            raise SystemExit("pending pre-evidence state emitted a relation")
        expect_failure(
            "pending relation output",
            "pending; no passing relation",
            lambda: checker.source_evidence_result(pending_relation),
        )

        wrong_revision_entry = deepcopy(fixture["entry"])
        wrong_revision_entry["revision"] = 5
        wrong_revision_registry = deepcopy(fixture["registry"])
        wrong_revision_registry["entries"][-1] = wrong_revision_entry
        expect_failure(
            "wrong revision",
            "received the wrong registry entry",
            lambda: topology(
                fixture,
                wrong_revision_entry,
                wrong_revision_registry,
            ),
        )

        omitted_entry = deepcopy(fixture["entry"])
        omitted_entry["profiles"] = omitted_entry["profiles"][:-1]
        omitted_registry = deepcopy(fixture["registry"])
        omitted_registry["entries"][-1] = omitted_entry
        expect_failure(
            "omitted logical profile",
            "omits a logical public API profile",
            lambda: topology(fixture, omitted_entry, omitted_registry),
        )

        parent_fixture = build_fixture(
            temp / "changed-parent", register_base_as_source=True
        )
        expect_failure(
            "changed source parent",
            "sole parent is not the registered source commit",
            lambda: topology(
                parent_fixture, parent_fixture["entry"], parent_fixture["registry"]
            ),
        )

        tree_entry = deepcopy(fixture["entry"])
        tree_entry["snapshot_source_tree_sha"] = "0" * 40
        tree_registry = deepcopy(fixture["registry"])
        tree_registry["entries"][-1] = tree_entry
        expect_failure(
            "changed source tree",
            "source tree does not match",
            lambda: topology(fixture, tree_entry, tree_registry),
        )

        generation_entry = deepcopy(fixture["entry"])
        generation_entry["generation"]["tool"] = "cargo-public-api 0.52.1"
        generation_registry = deepcopy(fixture["registry"])
        generation_registry["entries"][-1] = generation_entry
        expect_failure(
            "toolchain drift",
            "generation toolchain drifted",
            lambda: topology(fixture, generation_entry, generation_registry),
        )

        reordered_entry = deepcopy(fixture["entry"])
        reordered_entry["profiles"].reverse()
        reordered_registry = deepcopy(fixture["registry"])
        reordered_registry["entries"][-1] = reordered_entry
        expect_failure(
            "snapshot profile reordering",
            "sorted unique ids",
            lambda: checker.validate_signature_entry_profile_topology(reordered_entry),
        )

        drift_fixture = build_fixture(temp / "content-drift", wrong_content_digest=True)
        expect_failure(
            "snapshot content drift",
            "bytes do not match derived digest",
            lambda: topology(
                drift_fixture, drift_fixture["entry"], drift_fixture["registry"]
            ),
        )

        shallow_fixture = build_fixture(temp / "shallow")
        (shallow_fixture["root"] / ".git/shallow").write_text(
            f"{shallow_fixture['source']}\n",
            encoding="ascii",
        )
        expect_failure(
            "shallow source/evidence history",
            "requires Git to report a non-shallow repository",
            lambda: topology(
                shallow_fixture,
                shallow_fixture["entry"],
                shallow_fixture["registry"],
            ),
        )

        rewritten_source_registry = deepcopy(fixture["registry"])
        rewritten_source_registry["entries"] = deepcopy(
            fixture["registry"]["entries"][:3]
        )
        rewritten_source_registry["entries"][0]["status"] = "rewritten"
        expect_failure(
            "old-history rewrite",
            "truncation or rewrite",
            lambda: checker.validate_signature_registry_historical_lineage(
                {
                    fixture["source"]: ("source", rewritten_source_registry),
                    fixture["evidence"]: ("evidence", fixture["registry"]),
                },
                root=fixture["root"],
            ),
        )

        scope = json.loads(
            (ROOT / "release-scope-1.0.json").read_text(encoding="utf-8")
        )
        conflated = deepcopy(scope["feature_profiles"])
        all_features = next(
            profile for profile in conflated if profile["id"] == "pid-core-all-features"
        )
        all_features["all_features"] = False
        all_features["requested_features"] = ["experimental-all"]
        all_features["generation_arguments"][-1:] = ["--features", "experimental-all"]
        expect_failure(
            "stable/experimental activation conflation",
            "distinct --all-features activation semantics",
            lambda: checker.validate_public_api_profile_alias_contract(conflated),
        )

        nonisolated = subprocess.run(
            [
                sys.executable,
                "-S",
                "-B",
                str(CHECKER),
                "--source-evidence-relation-json",
            ],
            cwd=ROOT,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if (
            nonisolated.returncode == 0
            or nonisolated.stdout
            or "requires Python 3.11+ -I -S -B" not in nonisolated.stderr
        ):
            raise SystemExit(
                "non-isolated relation invocation was not rejected cleanly"
            )

    print("OK: 12 revision-4 source/evidence hostile controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
