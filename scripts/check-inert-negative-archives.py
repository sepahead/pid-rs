#!/usr/bin/env python3
"""Validate inert historical negative-evidence archives without executing payloads.

The fixed byte digest and independent semantic-contract digest make a matched metadata
reseal fail closed. Payload bytes are also bound to their declared Git blob object IDs.
This is internal byte/source correspondence, not authenticity, scientific truth, or
current checker authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Any, Final, NoReturn


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
FORMAT: Final[str] = "pid-rs/inert-negative-evidence-archive/v1"
PROFILES: Final[dict[str, dict[str, Any]]] = {
    "ksg-m1a-rejected-lifecycle-checker-20260828": {
        "index": "audit/archive/ksg-m1a-rejected-lifecycle-checker-20260828/INDEX.json",
        "index_bytes": 8180,
        "index_sha256": "4ae7fce1092dc2bcd3ec371f134b95cfe6c1f9307da265e81799b9117216d90c",
        "semantic_sha256": "c1c5566c1be5f9d89c3a740dab7e0e2dd0ff05957f02574073f318fbb30a3a84",
        "payloads": 9,
        "authority_role": "inert_historical_negative_evidence_never_current_authority",
        "integration_source": {
            "commit": "f8bed18dbbcc77e621ddb6a628d5e9a006ade99b",
            "parent": "9eb5ad48b9d15081ffd0e7056a0332e89765cac4",
            "tree": "294bb43e51c37826783ae1eda52ca858a832db7c",
        },
    },
    "sxpid3-s1-historical-checkers-v1": {
        "index": "audit/archive/sxpid3-s1-historical-checkers-v1/INDEX.json",
        "index_bytes": 5386,
        "index_sha256": "d1e8e97de4c957e97e2f939f453135cdb86a234c03718e1e7c8b4a5e150907e5",
        "semantic_sha256": "626a278b926f7896d4a0a8f1d33d7f7cca7c44be24d5a91e543d3dbc98fc107f",
        "payloads": 3,
        "authority_role": "inert_historical_checker_negative_evidence_never_source_review",
        "integration_source": {
            "commit": "dfdfd0b5c46b765338cc66a27973524d531b3388",
            "parent": "9ed6831d20de43467b1cff8adc8ee421a484f7fd",
            "tree": "8636722bce447e972817b5349849049b7e16961e",
        },
    },
    "numerical-claim-history-20260725": {
        "index": "audit/archive/numerical-claim-history-20260725/INDEX.json",
        "index_bytes": 8762,
        "index_sha256": "edd3a034616d92bbff574d3920c09a872619cf9b88c5112aca7658205de60e91",
        "semantic_sha256": "87c1ebb1e635720ec0d1a89364dfc02bef26d28751ed223169939ce8dcde45e4",
        "payloads": 11,
        "authority_role": "inert_historical_mathematical_and_numerical_witnesses",
        "integration_source": {
            "commit": "86faa9a0850ca416f54a467230106b01d4162687",
            "parent": "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56",
            "tree": "4f6fddb80754645cf6fa0fa48cdb82db457bb478",
        },
    },
    "python-verifier-custody-m0-20260830": {
        "index": "audit/archive/python-verifier-custody-m0-20260830/INDEX.json",
        "index_bytes": 5486,
        "index_sha256": "36274ec0ae8433b1e6a064dcb4277434fc76a2f2ac7f8d4abeb47f07c9483909",
        "semantic_sha256": "eff8b60bd5651d3448b3a6e7ee8b724677efc0766569b9d268c8fc7f939c9322",
        "payloads": 5,
        "authority_role": "inert_historical_process_custody_prototype_never_current_authority",
        "integration_source": {
            "commit": "e16a6915262e8bf2fac1752ff959d9d3733c7a7d",
            "parent": "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9",
            "tree": "74030de0ec545e29fd35429dfc2c889f676dfc8d",
        },
    },
}


class CheckError(RuntimeError):
    """An archive failed its closed-world integrity contract."""


def fail(message: str) -> NoReturn:
    raise CheckError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    fail(f"non-finite JSON number forbidden: {value}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_oid(raw: bytes) -> str:
    """Return Git's SHA-1 object name for exact blob bytes, not a security digest."""

    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def semantic_contract(index: dict[str, Any], label: str) -> bytes:
    """Canonicalize every index field except independently checked payload custody."""

    payloads = index.get("payloads")
    require(type(payloads) is list, f"{label} payload list absent")
    projected_payloads: list[dict[str, Any]] = []
    for ordinal, payload in enumerate(payloads):
        require(type(payload) is dict, f"{label} payload {ordinal} is not an object")
        projected_payloads.append(
            {
                key: value
                for key, value in payload.items()
                if key not in {"byte_length", "sha256"}
            }
        )
    contract = {
        key: projected_payloads if key == "payloads" else value
        for key, value in index.items()
    }
    return json.dumps(
        contract,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def safe_read(path: Path, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode), f"{label} is not a regular file")
        require(before.st_nlink == 1, f"{label} must have exactly one hard link")
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"cannot safely open {label}: {error}")
    try:
        opened = os.fstat(descriptor)
        buffer = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            buffer.extend(chunk)
        closed = os.fstat(descriptor)
    except OSError as error:
        fail(f"cannot read {label}: {error}")
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        fail(f"cannot restat {label}: {error}")

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    require(
        identity(before) == identity(opened) == identity(closed) == identity(after),
        f"{label} changed during read",
    )
    require(len(buffer) == after.st_size, f"{label} short or overlong read")
    return bytes(buffer)


def parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"{label} is not UTF-8: {error}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, CheckError) as error:
        fail(f"{label} is invalid JSON: {error}")
    require(type(value) is dict, f"{label} root must be an object")
    canonical = json.dumps(
        value,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    require(text == canonical, f"{label} is not canonical JSON")
    return value


def checked_relative(value: Any, prefix: str, label: str) -> str:
    require(type(value) is str and value, f"{label} must be a nonempty string")
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"{label} must be relative")
    require("\\" not in value, f"{label} must use POSIX separators")
    require(all(part not in {"", ".", ".."} for part in path.parts), f"{label} has unsafe components")
    require(path.as_posix() == value, f"{label} is not a canonical POSIX path")
    require(value.startswith(prefix + "/"), f"{label} escaped its archive")
    return value


def checked_repo_relative(value: Any, label: str) -> str:
    require(type(value) is str and value, f"{label} must be a nonempty string")
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"{label} must be relative")
    require("\\" not in value, f"{label} must use POSIX separators")
    require(all(part not in {"", ".", ".."} for part in path.parts), f"{label} has unsafe components")
    require(path.as_posix() == value, f"{label} is not a canonical POSIX path")
    return value


def exact_files(directory: Path, root: Path) -> set[str]:
    require(directory.exists(), f"archive directory absent: {directory}")
    require(not directory.is_symlink(), f"archive directory is a symlink: {directory}")
    observed: set[str] = set()
    for current, directories, files in os.walk(directory, followlinks=False):
        current_path = Path(current)
        for name in directories:
            child = current_path / name
            metadata = child.lstat()
            require(stat.S_ISDIR(metadata.st_mode), f"non-directory archive node: {child}")
            require(not stat.S_ISLNK(metadata.st_mode), f"archive directory symlink: {child}")
        for name in files:
            child = current_path / name
            metadata = child.lstat()
            require(stat.S_ISREG(metadata.st_mode), f"non-regular archive node: {child}")
            require(metadata.st_nlink == 1, f"archive file has multiple hard links: {child}")
            observed.add(child.relative_to(root).as_posix())
    return observed


def validate_archive(root: Path, archive_id: str, profile: dict[str, Any]) -> tuple[int, int]:
    index_relative = profile["index"]
    index_path = root / index_relative
    index_raw = safe_read(index_path, f"{archive_id} index")
    require(len(index_raw) == profile["index_bytes"], f"{archive_id} index length drift")
    require(sha256(index_raw) == profile["index_sha256"], f"{archive_id} index digest drift")
    index = parse_canonical_json(index_raw, f"{archive_id} index")

    require(index.get("archive_id") == archive_id, f"{archive_id} identity mismatch")
    require(index.get("format") == FORMAT, f"{archive_id} format mismatch")
    require(index.get("current_authority") is False, f"{archive_id} claimed current authority")
    require(
        index.get("authority_role") == profile["authority_role"],
        f"{archive_id} authority role drift",
    )
    require(
        index.get("integration_source") == profile["integration_source"],
        f"{archive_id} integration source route drift",
    )
    require(
        sha256(semantic_contract(index, f"{archive_id} semantic contract"))
        == profile["semantic_sha256"],
        f"{archive_id} semantic contract drift after byte custody",
    )

    archive_prefix = str(PurePosixPath(index_relative).parent)
    disposition = index.get("disposition")
    require(type(disposition) is dict, f"{archive_id} disposition binding absent")
    disposition_relative = checked_relative(
        disposition.get("archive_path"),
        archive_prefix,
        f"{archive_id} disposition path",
    )
    require(
        disposition_relative == f"{archive_prefix}/DISPOSITION.md",
        f"{archive_id} disposition path mismatch",
    )
    disposition_raw = safe_read(root / disposition_relative, f"{archive_id} disposition")
    require(
        len(disposition_raw) == disposition.get("byte_length"),
        f"{archive_id} disposition length drift",
    )
    require(
        sha256(disposition_raw) == disposition.get("sha256"),
        f"{archive_id} disposition digest drift",
    )

    payloads = index.get("payloads")
    require(type(payloads) is list, f"{archive_id} payload list absent")
    require(len(payloads) == profile["payloads"], f"{archive_id} payload count drift")
    paths: set[str] = set()
    identifiers: set[str] = set()
    payload_by_id: dict[str, dict[str, Any]] = {}
    python_payloads = 0
    for ordinal, payload in enumerate(payloads):
        require(type(payload) is dict, f"{archive_id} payload {ordinal} is not an object")
        required_keys = {
            "archive_path",
            "byte_length",
            "executable",
            "id",
            "original_path",
            "role",
            "sha256",
            "source_blob_oid",
            "source_path",
        }
        optional_keys = {
            "historical_commit",
            "historical_tree",
            "observed_false_green_shapes",
            "syntax_language",
        }
        require(required_keys <= payload.keys(), f"{archive_id} payload {ordinal} binding incomplete")
        require(
            set(payload) <= required_keys | optional_keys,
            f"{archive_id} payload {ordinal} has an unrecognized authority field",
        )
        require(payload.get("executable") is False, f"{archive_id} payload {ordinal} became executable")
        identifier = payload.get("id")
        require(type(identifier) is str and identifier, f"{archive_id} payload {ordinal} ID absent")
        require(identifier not in identifiers, f"{archive_id} duplicate payload ID: {identifier}")
        identifiers.add(identifier)
        payload_by_id[identifier] = payload
        relative = checked_relative(
            payload.get("archive_path"),
            f"{archive_prefix}/payload",
            f"{archive_id} payload {ordinal} path",
        )
        require(relative.endswith(".txt"), f"{archive_id} payload {ordinal} lost inert .txt suffix")
        require(relative not in paths, f"{archive_id} duplicate payload path: {relative}")
        paths.add(relative)
        raw = safe_read(root / relative, f"{archive_id} payload {ordinal}")
        require(
            type(payload.get("byte_length")) is int
            and payload["byte_length"] >= 0
            and len(raw) == payload["byte_length"],
            f"{archive_id} payload {ordinal} length drift",
        )
        require(
            type(payload.get("sha256")) is str
            and len(payload["sha256"]) == 64
            and sha256(raw) == payload["sha256"],
            f"{archive_id} payload {ordinal} digest drift",
        )
        require(
            git_blob_oid(raw) == payload.get("source_blob_oid"),
            f"{archive_id} payload {ordinal} Git blob source binding drift",
        )
        checked_repo_relative(
            payload.get("original_path"),
            f"{archive_id} payload {ordinal} original path",
        )
        checked_repo_relative(
            payload.get("source_path"),
            f"{archive_id} payload {ordinal} integration source path",
        )
        require(
            type(payload.get("role")) is str and payload["role"],
            f"{archive_id} payload {ordinal} role absent",
        )
        mode = (root / relative).lstat().st_mode
        require(mode & 0o111 == 0, f"{archive_id} payload {ordinal} has executable mode bits")
        syntax_language = payload.get("syntax_language")
        require(
            syntax_language in {None, "python"},
            f"{archive_id} payload {ordinal} has unknown syntax language",
        )
        if syntax_language == "python":
            try:
                source = raw.decode("utf-8")
                compile(
                    source,
                    relative,
                    "exec",
                    dont_inherit=True,
                    optimize=sys.flags.optimize,
                )
            except (UnicodeDecodeError, SyntaxError) as error:
                fail(f"{archive_id} Python payload {ordinal} is invalid: {error}")
            python_payloads += 1

    expected = {index_relative, disposition_relative, *paths}
    observed = exact_files(root / archive_prefix, root)
    require(observed == expected, f"{archive_id} closed-world file inventory drift")

    if archive_id == "ksg-m1a-rejected-lifecycle-checker-20260828":
        require(
            index.get("cases")
            == [
                "FG-JUST-PRESERVATION-COMMAND-COMMENTED",
                "FG-WORKFLOW-V9-COMMENTED-EXIT",
                "FG-AUDIENCE-HIDDEN-BANNER",
                "FG-WORKFLOW-V11-COMMENTED-EXIT",
                "FG-WORKFLOW-V12-BODY-TRUE",
                "FG-JUST-PRESERVATION-EARLY-SUCCESS",
                "FG-JUST-UNKNOWN-V13",
            ],
            "KSG false-green case identities drifted",
        )
        require(
            index.get("recovered_source")
            == {
                "commit": "2b0093537439ee1f4ca7073ee4800835a06fb9a0",
                "local_ref": "refs/custody/rejected/ksg-lifecycle-2b009353",
                "parent": "008ee7fa615aa8370623566c21eb99862680c7b1",
                "remote_ref_observed": False,
                "tree": "48b71a0302b0ebd46bc318e51220e8809ab8d240",
            },
            "KSG recovered source route drift",
        )
        require(
            index.get("replay")
            == {
                "archived_files_executed": False,
                "archived_replay_source_executed": False,
                "current_lifecycle_checker_restored": False,
                "negative_receipt_promoted": False,
                "validation": "integrity_and_python_syntax_only",
            },
            "KSG inert replay boundary drift",
        )
        require(
            index.get("scope")
            == {
                "application_authority": False,
                "estimator_authority": False,
                "mathematical_authority": False,
                "release_authority": False,
            },
            "KSG non-authority scope drift",
        )
    elif archive_id == "sxpid3-s1-historical-checkers-v1":
        excluded = index["excluded_open_packet"]
        bindings = excluded.get("bindings")
        require(type(bindings) is list and len(bindings) == 5, "S1 v3 binding roster drift")
        for ordinal, binding in enumerate(bindings):
            require(type(binding) is dict, f"S1 v3 binding {ordinal} is not an object")
            require(
                set(binding) == {"byte_length", "custody", "path", "sha256", "source_blob_oid"},
                f"S1 v3 binding {ordinal} field roster drift",
            )
            checked_repo_relative(binding["path"], f"S1 v3 binding {ordinal} path")
            require(
                type(binding["byte_length"]) is int and binding["byte_length"] >= 0,
                f"S1 v3 binding {ordinal} byte length invalid",
            )
            require(
                type(binding["sha256"]) is str
                and len(binding["sha256"]) == 64
                and all(character in "0123456789abcdef" for character in binding["sha256"]),
                f"S1 v3 binding {ordinal} SHA-256 invalid",
            )
            require(
                type(binding["source_blob_oid"]) is str
                and len(binding["source_blob_oid"]) == 40
                and all(
                    character in "0123456789abcdef"
                    for character in binding["source_blob_oid"]
                ),
                f"S1 v3 binding {ordinal} source blob OID invalid",
            )
            require(
                binding["custody"]
                in {"not_copied_not_accepted", "copied_as_inert_false_green_record_only"},
                f"S1 v3 binding {ordinal} custody state invalid",
            )
        require(
            excluded["status"]
            == "false_green_record_copied_inert_remaining_packet_not_copied_not_accepted",
            "S1 v3 packet custody or acceptance status drift",
        )
        require(excluded["s1"] == "NO_GO_OPEN", "S1 v3 status is not NO-GO/open")
        require(excluded["h1"] == "open", "S1 v3 H1 status is not open")
        require(excluded["programs_closed"] == 0, "S1 v3 closed a program")
        require(excluded["programs_total"] == 5, "S1 v3 program count drift")
        require(
            index.get("replay")
            == {
                "archived_checkers_executed": False,
                "historical_record_parsed_as_authority": False,
                "validation": "integrity_and_python_syntax_only",
            },
            "S1 inert replay boundary drift",
        )
        require(
            index.get("scope")
            == {
                "fills_h1": False,
                "fills_review_slot": False,
                "mathematical_counterexample": False,
                "programs_closed": 0,
                "s1_closed": False,
            },
            "S1 non-authority scope drift",
        )
        record_binding = next(
            binding
            for binding in excluded["bindings"]
            if binding["path"]
            == "audit/evidence/sxpid3-mgw-v5-source-correspondence-s1-v3.json"
        )
        archived_record = payload_by_id["false-green-record-v3"]
        require(
            record_binding["custody"] == "copied_as_inert_false_green_record_only"
            and record_binding["byte_length"] == archived_record["byte_length"]
            and record_binding["sha256"] == archived_record["sha256"]
            and record_binding["source_blob_oid"] == archived_record["source_blob_oid"],
            "S1 v3 false-green record custody binding drift",
        )
    elif archive_id == "numerical-claim-history-20260725":
        roles = {payload["id"]: payload["role"] for payload in payloads}
        require(
            roles.get("neumaier-guard-discriminator-open")
            == "historically_open_narrowly_superseded_by_explicit_overflow_discriminator",
            "Neumaier historical-open disposition drift",
        )
        require(
            index.get("scope")
            == {
                "estimator_attainability_claimed": False,
                "pid_theorem_defect_claimed": False,
                "population_claimed": False,
                "universal_binary64_refinement_claimed": False,
            },
            "numerical archive claim scope drift",
        )
        successors = index.get("successor_groups")
        require(type(successors) is dict and successors, "numerical successor map absent")
        for group, successor_paths in successors.items():
            require(type(group) is str and group, "numerical successor group name absent")
            require(type(successor_paths) is list and successor_paths, f"{group} successor paths absent")
            for ordinal, successor in enumerate(successor_paths):
                relative = checked_repo_relative(successor, f"{group} successor {ordinal}")
                try:
                    metadata = (root / relative).lstat()
                except OSError as error:
                    fail(f"{group} successor {ordinal} unavailable: {error}")
                require(
                    stat.S_ISREG(metadata.st_mode),
                    f"{group} successor {ordinal} is not a regular current-tree file",
                )
    elif archive_id == "python-verifier-custody-m0-20260830":
        require(
            index.get("historical_census")
            == {
                "import_statements": 2110,
                "imported_name_edges": 2295,
                "operational_roots": 66,
                "python_files": 186,
                "selected_dynamic_calls": 165,
                "static_launch_candidates": 1057,
                "tracked_tree_entries": 1040,
            },
            "Python custody historical census drift",
        )
        require(
            index.get("current_drift_probe")
            == {
                "import_statements": 2286,
                "imported_name_edges": 2530,
                "operational_roots": 73,
                "python_files": 201,
                "selected_dynamic_calls": 176,
                "static_launch_candidates": 1138,
                "status": "diagnostic_non_authoritative",
                "worktree_date": "2026-08-31",
            },
            "Python custody current diagnostic probe was promoted or changed",
        )
        require(
            index.get("omitted_derived_registry")
            == {
                "byte_length": 5473991,
                "custody": "not_copied_derived_from_reachable_historical_tree",
                "original_path": "audit/python-verifier-custody/registry-v1.json",
                "reason": (
                    "stale_large_derived_inventory_adds_no_unique_reasoning_and_"
                    "must_not_appear_current"
                ),
                "sha256": (
                    "ce11224f6fb95246a43dd36c24da57501f3854bf2f667c483f99125d751f016a"
                ),
                "source_blob_oid": "a7a101bff380e64f18fcba2b9cc0bd5b61ee6af9",
            },
            "Python custody omitted derived-registry binding drift",
        )
        require(
            index.get("process_lessons")
            == [
                "stored_source_is_not_loaded_source",
                "loaded_source_is_not_executed_source",
                "execution_is_not_result_correctness",
                "result_correctness_is_not_mathematical_or_scientific_validity",
                "unknown_import_launch_and_process_edges_remain_open",
                "hostile_tests_show_named_fault_sensitivity_not_completeness",
            ],
            "Python custody process-lesson boundary drift",
        )
        require(
            index.get("replay")
            == {
                "archived_checker_executed": False,
                "archived_self_test_executed": False,
                "current_registry_generated": False,
                "validation": "integrity_and_python_syntax_only",
            },
            "Python custody inert replay boundary drift",
        )
        require(
            index.get("scope")
            == {
                "current_inventory_authority": False,
                "execution_custody_closed": False,
                "implementation_activated": False,
                "mathematical_authority": False,
                "scientific_novelty_claimed": False,
            },
            "Python custody non-authority scope drift",
        )
        require(
            {payload["id"]: payload["role"] for payload in payloads}
            == {
                "design-record": (
                    "historical_process_design_never_current_policy_or_authority"
                ),
                "documentation": (
                    "historical_explanation_never_current_documentation_or_readme"
                ),
                "inventory-checker": (
                    "historical_static_inventory_prototype_never_execute_or_treat_as_current"
                ),
                "inventory-checker-self-test": (
                    "historical_hostile_suite_never_execute_or_infer_completeness"
                ),
                "registry-schema": (
                    "historical_data_model_never_current_schema_authority"
                ),
            },
            "Python custody payload roles drift",
        )

    return len(payloads), python_payloads


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    arguments = parser.parse_args()
    root = arguments.root.absolute()
    try:
        root_metadata = root.lstat()
    except OSError as error:
        fail(f"cannot inspect archive root: {error}")
    require(stat.S_ISDIR(root_metadata.st_mode), "archive root must be a directory")
    require(not stat.S_ISLNK(root_metadata.st_mode), "archive root must not be a symlink")
    total_payloads = 0
    total_python = 0
    for archive_id, profile in PROFILES.items():
        payloads, python_payloads = validate_archive(root, archive_id, profile)
        total_payloads += payloads
        total_python += python_payloads
    print(
        "OK: inert negative archives bind "
        f"{len(PROFILES)} packets, {total_payloads} payloads, and "
        f"{total_python} syntax-checked Python sources; no payload executed"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as error:
        print(f"ERROR: inert negative archive rejected: {error}", file=sys.stderr)
        raise SystemExit(1)
