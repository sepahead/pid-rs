#!/usr/bin/env python3
"""Mutation-test the frozen Lean 4.33.0 replay custody gate."""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
):
    print(
        "ERROR: check-lean-toolchain-freeze-self-test.py requires Python 3.11+ -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from collections.abc import Callable
from datetime import datetime, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-lean-toolchain-freeze.py"


class SelfTestError(RuntimeError):
    """The baseline failed or a hostile freeze/replay mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def load_checker() -> ModuleType:
    name = "pid_rs_lean_toolchain_freeze_checker"
    spec = importlib.util.spec_from_file_location(name, CHECKER)
    if spec is None or spec.loader is None:
        raise SelfTestError("could not load Lean toolchain freeze checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def required_paths(checker: ModuleType) -> set[str]:
    return {
        "audit/formal/lean/toolchain-freeze-policy.json",
        "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        *checker.EXPECTED_CONFIG_HASHES,
        *checker.EXPECTED_SOURCE_HASHES,
        *checker.EXPECTED_CURRENT_EVIDENCE_HASHES,
        *checker.EXPECTED_CHECKER_HASHES,
        *checker.EXPECTED_DERIVED_EVIDENCE_HASHES,
        *checker.EXPECTED_ACTIVE_CLAIM_HASHES,
        *checker.EXPECTED_ACTIVE_RESUME_HASHES,
        *checker.EXPECTED_OPERATIONAL_WIRING_HASHES,
        *checker.EXPECTED_CUSTODY_GATE_PATHS,
        *checker.PRESERVED_HISTORICAL_HASHES,
    }


def copy_fixture(checker: ModuleType, destination: Path) -> None:
    for relative in sorted(required_paths(checker)):
        source = ROOT / relative
        require(
            source.is_file() and not source.is_symlink(),
            f"fixture source is not regular: {relative}",
        )
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def canonical_json(path: Path, mutate: Callable[[dict], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON mutation root is not an object: {path}")
    mutate(value)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def configure_fixture(checker: ModuleType, root: Path) -> None:
    checker.ROOT = root
    checker.PROJECT = root / "audit/formal/lean"
    checker.POLICY = checker.PROJECT / "toolchain-freeze-policy.json"
    checker.RECEIPT = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )


def mutate_policy_remove_trigger(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(path, lambda value: value["reevaluation_triggers"].pop())
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def mutate_policy_enable_latest(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["automatic_update_policy"].__setitem__(
            "check_latest_release", True
        ),
    )
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def mutate_policy_remove_nontrigger(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(path, lambda value: value["nontriggers"].pop())
    refresh_policy_binding(checker, root)


def mutate_policy_weaken_baseline_unavailability(
    checker: ModuleType, root: Path
) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"

    def mutate(value: dict) -> None:
        trigger = next(
            item
            for item in value["reevaluation_triggers"]
            if item["id"] == "baseline_unavailability"
        )
        trigger["description"] = "One transient download failed."

    canonical_json(path, mutate)
    refresh_policy_binding(checker, root)


def mutate_policy_disable_rollback(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["candidate_transition_policy"].__setitem__(
            "rollback_plan_required_before_activation", False
        ),
    )
    refresh_policy_binding(checker, root)


def mutate_receipt_archive_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["official_archive"].__setitem__("sha256", "0" * 64),
    )


def mutate_receipt_optimized_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["python_optimization_parity"]["pairs"]["finite_checker"][
            "optimized_stdout"
        ].__setitem__("sha256", "0" * 64),
    )


def mutate_receipt_scope(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["scope_boundary"].__setitem__(
            0, "This replay proves Lean kernel soundness and Rust refinement."
        ),
    )


def mutate_environment_inheritance(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["environment_policy"].__setitem__(
            "ambient_environment_inherited", True
        ),
    )


def mutate_receipt_duplicate_key(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    text = path.read_text(encoding="utf-8")
    path.write_text('{\n  "status": "passed",' + text[1:], encoding="utf-8")


def mutate_receipt_noncanonical(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")


def mutate_self_test_with_coordinated_receipt_hash(
    _checker: ModuleType, root: Path
) -> None:
    relative = "scripts/check-lean-toolchain-freeze-self-test.py"
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        receipt,
        lambda value: (
            value["custody_gate_sha256"].__setitem__(relative, digest),
            value["replay_custody_gate_sha256"].__setitem__(relative, digest),
        ),
    )


def mutate_replay_checker_endpoint_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["replay_custody_gate_sha256"].__setitem__(
            "scripts/check-lean-toolchain-freeze.py", "0" * 64
        ),
    )


def mutate_local_archive_observation(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json",
        lambda value: value["official_archive_observation"].__setitem__(
            "sha256", "0" * 64
        ),
    )


def refresh_source_binding(checker: ModuleType, root: Path, relative: str) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_SOURCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        receipt,
        lambda value: value["source_sha256"].__setitem__(relative, digest),
    )


def mutate_broad_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    old = "set_option backward.isDefEq.respectTransparency.types false in"
    require(text.count(old) == 1, "broad-option mutation anchor drifted")
    path.write_text(
        text.replace(old, "set_option backward.isDefEq.respectTransparency false", 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_missing_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    old = "set_option backward.isDefEq.respectTransparency.types false in\n"
    require(text.count(old) == 1, "missing-option mutation anchor drifted")
    path.write_text(text.replace(old, "", 1), encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_extra_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    anchor = "set_option warningAsError true\n"
    require(text.count(anchor) == 1, "extra-option mutation anchor drifted")
    path.write_text(
        text.replace(anchor, anchor + checker.OPTION + "\n", 1), encoding="utf-8"
    )
    refresh_source_binding(checker, root, relative)


def mutate_manifest_pin(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/lake-manifest.json"
    path = root / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    package = next(item for item in value["packages"] if item["name"] == "mathlib")
    package["rev"] = "0" * 40
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.EXPECTED_CONFIG_HASHES[relative] = digest


def mutate_historical_bytes(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout"
    )
    path.write_bytes(b"historical drift\n")


def mutate_derived_output(_checker: ModuleType, root: Path) -> None:
    path = root / "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.33.0.stdout"
    path.write_text(
        path.read_text(encoding="utf-8").replace("instance_reducible", "regular", 1),
        encoding="utf-8",
    )


def mutate_policy_symlink(_checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    target = path.with_name("policy-target.json")
    shutil.copy2(path, target)
    path.unlink()
    path.symlink_to(target.name)


def mutate_receipt_hardlink(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    os.link(path, path.with_name("replay-second-link.json"))


def canonical_compact_json(path: Path, mutate: Callable[[dict], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON mutation root is not an object: {path}")
    mutate(value)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def refresh_current_evidence_binding(
    checker: ModuleType, root: Path, relative: str
) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_CURRENT_EVIDENCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        receipt,
        lambda value: value["current_evidence_sha256"].__setitem__(relative, digest),
    )


def refresh_policy_binding(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_manifest_binding(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/lake-manifest.json"
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_CONFIG_HASHES[relative] = digest
    policy = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        policy,
        lambda value: value["active_pin"].__setitem__("lake_manifest_sha256", digest),
    )
    refresh_policy_binding(checker, root)
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        receipt,
        lambda value: value["active_configuration"].__setitem__(relative, digest),
    )


def mutate_deriving_scope_after_target(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    target = checker.OPTION + "\nderiving instance Fintype for SxPid2Node"
    replacement = "deriving instance Fintype for SxPid2Node\n" + checker.OPTION
    require(text.count(target) == 1, "deriving-scope relocation anchor drifted")
    path.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_deriving_scope_with_comment_spoof(checker: ModuleType, root: Path) -> None:
    mutate_deriving_scope_after_target(checker, root)
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    text += (
        "\n/- Raw-text-only target spoof:\n"
        + checker.OPTION
        + "\nderiving instance Fintype for SxPid2Node\n-/\n"
    )
    path.write_text(text, encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_proof_scope_to_file_header(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergenceSemanticContract.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    target = checker.EXPECTED_OPTION_TARGETS[relative][0]
    require(text.count(target) == 1, "proof-scope relocation target drifted")
    text = text.replace(
        target, target.replace(" :=\n  " + checker.OPTION + " by", " := by"), 1
    )
    header = "set_option warningAsError true\n"
    require(text.count(header) == 1, "proof-scope relocation header drifted")
    text = text.replace(header, header + checker.OPTION + " by\n", 1)
    path.write_text(text, encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_option_true(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    require(text.count(checker.OPTION) == 1, "true-option mutation anchor drifted")
    path.write_text(
        text.replace(checker.OPTION, checker.OPTION.replace("false", "true"), 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_file_global_types_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    require(
        text.count(checker.OPTION) == 1, "file-global-option mutation anchor drifted"
    )
    path.write_text(
        text.replace(checker.OPTION, checker.OPTION.removesuffix(" in"), 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_current_evidence_identity(
    checker: ModuleType, root: Path, replacement: str
) -> None:
    relative = "audit/evidence/lean-citation-edge-countermodel-4.33.0.json"
    path = root / relative
    canonical_compact_json(
        path,
        lambda value: value.__setitem__("lean_version", replacement),
    )
    refresh_current_evidence_binding(checker, root, relative)


def mutate_wrong_lean_commit(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + "0" * 40
        + ", Release)",
    )


def mutate_wrong_lean_build(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + checker.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Debug)",
    )


def mutate_wrong_lean_platform(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, x86_64-unknown-linux-gnu, commit "
        + checker.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Release)",
    )


def mutate_manifest_regeneration_overclaim(checker: ModuleType, root: Path) -> None:
    relative = "audit/evidence/lean-4.33.0-manifest-regeneration-2026-08-11.json"
    path = root / relative
    canonical_compact_json(
        path,
        lambda value: value["procedure"].__setitem__("raw_command_log_retained", True),
    )
    refresh_current_evidence_binding(checker, root, relative)


def mutate_operational_wiring(root: Path, relative: str) -> None:
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_ci_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, ".github/workflows/ci.yml")


def mutate_agents_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "AGENTS.md")


def mutate_freeze_document_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md")


def mutate_just_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "justfile")


def mutate_scripts_readme_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/README.md")


def mutate_replay_generator_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/generate-lean-4.33-replay.py")


def mutate_mathlib_manifest_field(
    checker: ModuleType, root: Path, field: str, value: str
) -> None:
    path = root / "audit/formal/lean/lake-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    package = next(item for item in manifest["packages"] if item["name"] == "mathlib")
    package[field] = value
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_manifest_binding(checker, root)


def mutate_wrong_mathlib_tag(checker: ModuleType, root: Path) -> None:
    mutate_mathlib_manifest_field(checker, root, "inputRev", "v4.32.0")


def mutate_wrong_mathlib_revision(checker: ModuleType, root: Path) -> None:
    mutate_mathlib_manifest_field(checker, root, "rev", "0" * 40)


def mutate_stale_policy_manifest(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["active_pin"].__setitem__("lake_manifest_sha256", "0" * 64),
    )
    refresh_policy_binding(checker, root)


def mutate_receipt_missing_source(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        path,
        lambda value: value["source_sha256"].pop(next(iter(value["source_sha256"]))),
    )


def mutate_receipt_extra_evidence(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        path,
        lambda value: value["current_evidence_sha256"].__setitem__(
            "audit/evidence/unreviewed.json", "0" * 64
        ),
    )


def mutate_receipt_missing_checker(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        path,
        lambda value: value["checker_sha256"].pop(next(iter(value["checker_sha256"]))),
    )


def mutate_cached_build_credit(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )

    def mutate(value: dict) -> None:
        build = next(
            record
            for record in value["command_records"]
            if record["name"] == "clean_build"
        )
        build["cache_state"]["project_build_directory_absent_before"] = False
        build["cache_state"]["project_oleans_reused"] = True

    canonical_json(path, mutate)


def mutate_clean_build_transcript(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    replacement = b"unexpected clean-build output\n"

    def mutate(value: dict) -> None:
        build = next(
            record
            for record in value["command_records"]
            if record["name"] == "clean_build"
        )
        build["stdout"] = {
            "bytes": len(replacement),
            "sha256": hashlib.sha256(replacement).hexdigest(),
        }
        value["verification"]["clean_build"]["stdout_exact"] = replacement.decode(
            "utf-8"
        )

    canonical_json(path, mutate)


def mutate_valid_replay_timestamps(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )

    def shifted(value: str) -> str:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return (parsed + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def mutate(value: dict) -> None:
        for record in value["command_records"]:
            record["start_utc"] = shifted(record["start_utc"])
            record["end_utc"] = shifted(record["end_utc"])
        value["execution_window"]["start_utc"] = shifted(
            value["execution_window"]["start_utc"]
        )
        value["execution_window"]["end_utc"] = shifted(
            value["execution_window"]["end_utc"]
        )

    canonical_json(path, mutate)


def mutate_valid_replay_root(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )

    def mutate(value: dict) -> None:
        replacement = "/private/tmp/pid-rs-alternate-replay-root"
        value["execution_environment"]["repo_root_observed"] = replacement
        for record in value["command_records"]:
            relative = record["cwd_repo_relative"]
            record["cwd_observed_absolute"] = (
                replacement if relative == "." else f"{replacement}/{relative}"
            )

    canonical_json(path, mutate)


def mutate_paired_checker_output(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    replacement = b"OK: forged paired checker output\n"
    forged_stream = {
        "bytes": len(replacement),
        "sha256": hashlib.sha256(replacement).hexdigest(),
    }

    def mutate(value: dict) -> None:
        for mode in ("normal", "optimized"):
            record = next(
                item
                for item in value["command_records"]
                if item["name"] == f"finite_self_test:{mode}"
            )
            record["stdout"] = dict(forged_stream)
        parity = value["python_optimization_parity"]["pairs"]["finite_self_test"]
        parity["normal_stdout"] = dict(forged_stream)
        parity["optimized_stdout"] = dict(forged_stream)

    canonical_json(path, mutate)


def mutate_axiom_audit_stdin(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    trivial = b"#check True\n"

    def mutate(value: dict) -> None:
        audit = next(
            record
            for record in value["command_records"]
            if record["name"] == "theorem_axiom_audit"
        )
        audit["stdin"] = {
            "bytes": len(trivial),
            "sha256": hashlib.sha256(trivial).hexdigest(),
        }

    canonical_json(path, mutate)


def mutate_derived_receipt_overclaim(checker: ModuleType, root: Path) -> None:
    relative = "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-2026-08-11.json"
    path = root / relative

    def mutate(value: dict) -> None:
        comparison = value["comparison"]
        comparison.pop("normalized_printed_declaration_skeletons_and_synthesis_equal")
        comparison["normalized_types_bodies_and_synthesis_equal"] = True

    canonical_json(path, mutate)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.EXPECTED_DERIVED_EVIDENCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    canonical_json(
        receipt,
        lambda value: value["derived_instance_evidence_sha256"].__setitem__(
            relative, digest
        ),
    )


Mutation = tuple[str, Callable[[ModuleType, Path], None], str]
MUTATIONS: tuple[Mutation, ...] = (
    (
        "freeze-trigger-removal",
        mutate_policy_remove_trigger,
        "freeze trigger inventory drifted",
    ),
    (
        "latest-release-enable",
        mutate_policy_enable_latest,
        "enabled latest-release checks",
    ),
    (
        "freeze-nontrigger-removal",
        mutate_policy_remove_nontrigger,
        "freeze nontrigger inventory drifted",
    ),
    (
        "weaken-baseline-unavailability",
        mutate_policy_weaken_baseline_unavailability,
        "evidentiary threshold",
    ),
    (
        "disable-migration-rollback",
        mutate_policy_disable_rollback,
        "transition/rollback policy drifted",
    ),
    (
        "archive-digest",
        mutate_receipt_archive_hash,
        "official archive observation drifted",
    ),
    (
        "local-archive-observation-digest",
        mutate_local_archive_observation,
        "local archive bytes/identity drifted",
    ),
    (
        "optimized-parity",
        mutate_receipt_optimized_hash,
        "normal/-O replay parity summary drifted",
    ),
    ("scope-escalation", mutate_receipt_scope, "replay nonclaim disappeared"),
    (
        "ambient-environment-inheritance",
        mutate_environment_inheritance,
        "replay environment inherited ambient variables",
    ),
    ("duplicate-json-key", mutate_receipt_duplicate_key, "duplicate JSON key"),
    ("noncanonical-json", mutate_receipt_noncanonical, "not canonical JSON"),
    (
        "coordinated-self-test-custody-rewrite",
        mutate_self_test_with_coordinated_receipt_hash,
        "replay receipt reviewed projection drifted",
    ),
    (
        "replay-checker-endpoint-digest",
        mutate_replay_checker_endpoint_hash,
        "replay checker pre-pin reconstruction drifted",
    ),
    ("broad-transparency", mutate_broad_option, "transparency scope inventory drifted"),
    (
        "missing-transparency",
        mutate_missing_option,
        "transparency scope inventory drifted",
    ),
    ("extra-transparency", mutate_extra_option, "transparency scope inventory drifted"),
    ("true-transparency", mutate_option_true, "transparency scope inventory drifted"),
    (
        "file-global-types-transparency",
        mutate_file_global_types_option,
        "transparency scope inventory drifted",
    ),
    (
        "moved-deriving-scope",
        mutate_deriving_scope_after_target,
        "transparency setting moved away from reviewed target",
    ),
    (
        "moved-deriving-scope-comment-spoof",
        mutate_deriving_scope_with_comment_spoof,
        "transparency setting moved away from reviewed target",
    ),
    (
        "moved-proof-scope",
        mutate_proof_scope_to_file_header,
        "transparency setting moved away from reviewed target",
    ),
    ("wrong-lean-commit", mutate_wrong_lean_commit, "exact Lean identity line drifted"),
    ("wrong-lean-build", mutate_wrong_lean_build, "exact Lean identity line drifted"),
    (
        "wrong-lean-platform",
        mutate_wrong_lean_platform,
        "exact Lean identity line drifted",
    ),
    (
        "manifest-regeneration-overclaim",
        mutate_manifest_regeneration_overclaim,
        "manifest-regeneration procedure record drifted",
    ),
    (
        "ci-operational-wiring-drift",
        mutate_ci_wiring,
        "operational wiring digest mismatch: .github/workflows/ci.yml",
    ),
    (
        "agents-operational-wiring-drift",
        mutate_agents_wiring,
        "operational wiring digest mismatch: AGENTS.md",
    ),
    (
        "freeze-document-operational-wiring-drift",
        mutate_freeze_document_wiring,
        "operational wiring digest mismatch: audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
    ),
    (
        "just-operational-wiring-drift",
        mutate_just_wiring,
        "operational wiring digest mismatch: justfile",
    ),
    (
        "scripts-readme-operational-wiring-drift",
        mutate_scripts_readme_wiring,
        "operational wiring digest mismatch: scripts/README.md",
    ),
    (
        "replay-generator-operational-wiring-drift",
        mutate_replay_generator_wiring,
        "operational wiring digest mismatch: scripts/generate-lean-4.33-replay.py",
    ),
    (
        "wrong-mathlib-tag",
        mutate_wrong_mathlib_tag,
        "Lake package pin drifted: mathlib",
    ),
    (
        "wrong-mathlib-revision",
        mutate_wrong_mathlib_revision,
        "Lake package pin drifted: mathlib",
    ),
    (
        "stale-policy-manifest",
        mutate_stale_policy_manifest,
        "freeze manifest digest drifted",
    ),
    (
        "missing-source-member",
        mutate_receipt_missing_source,
        "replay source inventory drifted",
    ),
    (
        "extra-evidence-member",
        mutate_receipt_extra_evidence,
        "replay current evidence inventory drifted",
    ),
    (
        "missing-checker-member",
        mutate_receipt_missing_checker,
        "replay checker inventory drifted",
    ),
    (
        "cached-build-credit",
        mutate_cached_build_credit,
        "clean build cache-isolation record drifted",
    ),
    (
        "clean-build-transcript-drift",
        mutate_clean_build_transcript,
        "clean build replay drifted",
    ),
    (
        "valid-timestamp-rewrite",
        mutate_valid_replay_timestamps,
        "replay receipt reviewed projection drifted",
    ),
    (
        "valid-observed-root-rewrite",
        mutate_valid_replay_root,
        "replay receipt reviewed projection drifted",
    ),
    (
        "paired-checker-output-rewrite",
        mutate_paired_checker_output,
        "replay receipt reviewed projection drifted",
    ),
    ("trivial-axiom-audit-stdin", mutate_axiom_audit_stdin, "exact 246-name query"),
    (
        "historical-byte-drift",
        mutate_historical_bytes,
        "preserved historical 4.32 evidence digest mismatch",
    ),
    (
        "derived-output-drift",
        mutate_derived_output,
        "derived-instance evidence digest mismatch",
    ),
    (
        "derived-body-overclaim",
        mutate_derived_receipt_overclaim,
        "overclaims full body equality",
    ),
    ("policy-symlink", mutate_policy_symlink, "regular non-symbolic-link"),
    ("receipt-hardlink", mutate_receipt_hardlink, "exactly one hard link"),
)


def run_mutation(
    name: str, mutation: Callable[[ModuleType, Path], None], expected: str
) -> None:
    checker = load_checker()
    temp_parent = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix=f"pid-lean-freeze-{name}-", dir=temp_parent
    ) as directory:
        fixture = Path(directory) / "repo"
        copy_fixture(checker, fixture)
        configure_fixture(checker, fixture)
        mutation(checker, fixture)
        try:
            checker.check_all()
        except (checker.FreezeError, OSError) as error:
            require(expected in str(error), f"{name}: wrong diagnostic: {error}")
        else:
            raise SelfTestError(f"freeze mutation survived: {name}")


def main() -> int:
    try:
        baseline = load_checker()
    except (OSError, SelfTestError) as error:
        print(f"Lean toolchain freeze self-test failed: {error}", file=sys.stderr)
        return 1
    try:
        baseline.check_all()
        for name, mutation, expected in MUTATIONS:
            run_mutation(name, mutation, expected)
    except (baseline.FreezeError, OSError, SelfTestError) as error:
        print(f"Lean toolchain freeze self-test failed: {error}", file=sys.stderr)
        return 1
    print(
        "OK: Lean 4.33 freeze self-test rejected all "
        f"{len(MUTATIONS)} policy, replay, source-scope, pin, historical, "
        "derived-evidence, canonical-JSON, symlink, and hard-link mutations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
