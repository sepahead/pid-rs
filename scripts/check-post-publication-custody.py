#!/usr/bin/env python3
"""Check the immutable 2026-09-02 post-publication custody snapshot.

This is a standard-library-only, fail-closed checker.  It validates the record,
the exact tab-separated remote-heads preimage captured by a direct
``git ls-remote --heads`` observation, and the byte identities of the bound
presentation inputs and derivatives.  It does *not* contact GitHub, inspect a
local Git registry, authorize deletion, parse PDF semantics, or turn a dated
observation into a live manifest.  The recorded main OID is the publication
anchor for the observation; a later commit that adds this receipt is expected
to have a different main OID.

The checker intentionally duplicates the expected snapshot identities.  The
duplication is a guard against editing both the JSON and its manifest in the
same direction: a changed snapshot requires a reviewed checker update (or a
new dated receipt), rather than silently changing the meaning of this record.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, NoReturn


if sys.version_info < (3, 11):
    raise SystemExit("check-post-publication-custody.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "audit/evidence/post-publication-custody-2026-09-02.json"
MANIFEST = ROOT / "audit/evidence/post-publication-remote-heads-2026-09-02.tsv"

HEX40 = re.compile(r"^[0-9a-f]{40}$")
REF = re.compile(r"^refs/heads/[A-Za-z0-9._/-]+$")
UTC_TIMESTAMP = re.compile(r"^2026-09-02T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

EXPECTED_COMMIT = "c499653e4ac89733cb35330bf1a13c93a40ee385"
EXPECTED_PARENT = "30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1"
EXPECTED_TREE = "1a1f8dc9782d2f5d6cc9c3342b5395bc7240b975"
EXPECTED_PRIMARY_HEAD = "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"
EXPECTED_PRE_PACKED_SHA256 = "c7cc9b77613ef1942f05c2db98efcda8ddff5bff546e9ca78c6b2699406f6327"
EXPECTED_POST_PACKED_SHA256 = "813fe81e1ec218749f3b593cabc1dd74acfff87192b0b4bb1d0e8be3e722d31c"
EXPECTED_STATUS_HASH = "580884a0f59dd3aa47eaf973836bde8256264d5be906dac9a7c7dba7f23b4cb7"

# The order here is the canonical ref-name order of the captured manifest.
EXPECTED_HEADS: tuple[tuple[str, str], ...] = (
    ("062025c3fc283db9bdb105219dbcc82719771175", "refs/heads/archive/composite-v5-rejected-umask-20260818"),
    ("1ef37646e168b645853e1857d0205233a87b68dc", "refs/heads/archive/composite-v6-pre-r11-draft-20260818"),
    ("769547a6d6ed70a074707d90bc2f55393fd34fa4", "refs/heads/archive/composite-v9-rejected-local-authority-oversize-20260822"),
    ("113cbad2e58a9cfa40cf43b1c0ffc260b566aa92", "refs/heads/archive/composite-v9-rejected-r14-fixed-point-20260822"),
    ("0a6ece9c525ad7aad061f55b3edea83554891b42", "refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821"),
    ("60774437488b376d30702146301e76b3186b5dd3", "refs/heads/archive/exact-log-product-verifier-draft-20260828"),
    ("81d37370a21a4b5c9551e2cde7904e5e1ee28e67", "refs/heads/archive/real-r-constructor-v8-public-disposition"),
    ("9dcdf32f18076eefc768194079b4abf437009737", "refs/heads/codex/primegaps-pid-blueprint-20260819"),
    ("93edb4983129151ce0db8e58b0aad52cae0f47bc", "refs/heads/diagnostic/c3-pdf-capture-20260830"),
    (EXPECTED_COMMIT, "refs/heads/main"),
    ("80443f9f2fa66452237013c9881cfaeeb984e5c1", "refs/heads/sepahead/exact-log-hostile-v1"),
    ("75a7acaa3f9432dc323be7e49f5eee1f9af781fd", "refs/heads/sepahead/galadriel-placement-guide-v1"),
    ("caf8c7be3e2249df8e959c8940632fd22ed09923", "refs/heads/sepahead/pid2-rev4-assurance-v1"),
    ("e16a6915262e8bf2fac1752ff959d9d3733c7a7d", "refs/heads/sepahead/python-custody-m0-v1"),
)

EXPECTED_RETIRED: tuple[tuple[str, str], ...] = (
    ("refs/heads/sepahead/ci-pandoc-toolchain-fix", "b45a7eb2e15364d37ecffc3061bf4f9ac5812b7f"),
    ("refs/heads/sepahead/documentation-closure-v1", "30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1"),
    ("refs/heads/sepahead/galadriel-placement-main-v1", "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9"),
    ("refs/heads/sepahead/openaction-compat-candidate", "9ed6831d20de43467b1cff8adc8ee421a484f7fd"),
    ("refs/heads/sepahead/pdf-annotation-portability-corrected", "0af14fc97b7c5fe8c4df0361e37cd9cefaa9c6ba"),
    ("refs/heads/sepahead/pid-rs-release-integration-r4", "535d7a44e2f8108f806af48cc27b86009239ec4e"),
    ("refs/heads/sepahead/pid-rs-release-integration-r4-recovered", "008ee7fa615aa8370623566c21eb99862680c7b1"),
    ("refs/heads/archive/composite-v5-unqualified-draft-20260818", "f7c6122d25ea098a36fa1fc6d672d78f25b783bb"),
    ("refs/heads/sepahead/pid2-rev4-behavior-v1", "03c0980f256c2a66b3d64bff1686a8d116d76138"),
)

EXPECTED_RETIRED_REASONS = {
    "refs/heads/sepahead/ci-pandoc-toolchain-fix": "superseded by the mainline-published anchor",
    "refs/heads/sepahead/documentation-closure-v1": "predecessor of the mainline-published anchor",
    "refs/heads/sepahead/galadriel-placement-main-v1": "old main snapshot; the published anchor is newer",
    "refs/heads/sepahead/openaction-compat-candidate": "superseded compatibility candidate",
    "refs/heads/sepahead/pdf-annotation-portability-corrected": "superseded portability candidate",
    "refs/heads/sepahead/pid-rs-release-integration-r4": "integrated release line",
    "refs/heads/sepahead/pid-rs-release-integration-r4-recovered": "recovered predecessor; custody retained separately",
    "refs/heads/archive/composite-v5-unqualified-draft-20260818": "contained by the retained rejected-umask archive ref",
    "refs/heads/sepahead/pid2-rev4-behavior-v1": "contained by the retained pid2-rev4-assurance ref",
}

EXPECTED_CONTAINMENT = {
    "f7c6122d25ea098a36fa1fc6d672d78f25b783bb": (
        "refs/heads/archive/composite-v5-rejected-umask-20260818",
        "062025c3fc283db9bdb105219dbcc82719771175",
    ),
    "03c0980f256c2a66b3d64bff1686a8d116d76138": (
        "refs/heads/sepahead/pid2-rev4-assurance-v1",
        "caf8c7be3e2249df8e959c8940632fd22ed09923",
    ),
}

EXPECTED_NONCLAIMS = (
    "This receipt does not prove any PID theorem, probability law, estimator consistency, calibration, or application benefit.",
    "A green hosted run proves only the checked source and workflow predicates at the exact commit; it is not a mathematical or statistical certificate.",
    "Remote-main equality does not make the dirty primary worktree clean and does not authorize overwriting it.",
    "Git object reachability, a bundle digest, and a filesystem copy are different custody claims.",
    "The receipt is not a global filesystem inventory and does not authorize future deletion or garbage collection.",
    "The operator action record is not an independently witnessed transcript of every command or process.",
    "The receipt PDF and figure PDF are presentation derivatives; no PDF/UA, external-link reachability, or cross-toolchain equivalence claim is made.",
    "The cleanup operations did not alter estimator code, formal theorem source, fixtures, or numerical result bytes; process changes are not scientific validation.",
)

EXPECTED_REMOTE_RAW_SHA256 = "b8fee7265e8a6ea38adbd03324cbc22e07785689e5b55e4a51d2101fce018b82"
EXPECTED_REMOTE_WHOLE_LINE_SHA256 = "1806619eb44aad84806eb63085da1859fa146492611cb72aafefbdac2d3b23c3"
EXPECTED_RECORD_RAW_SHA256 = "e9eda59361a69f3a59b34cbc8f26b12955227ac32e541f904f08bf9d40ec79a2"
EXPECTED_RECORD_CANONICAL_SHA256 = "cca58d4bf2987816f76c72b192ef8d0cb1daf41844d19cc61baa84dec69b9024"


class CheckError(RuntimeError):
    """A malformed or semantically escalated snapshot."""


def fail(message: str) -> NoReturn:
    raise CheckError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def read_regular(path: Path) -> bytes:
    """Read a stable, single-link regular file without following a symlink."""
    try:
        before = os.lstat(path)
    except OSError as error:
        fail(f"cannot stat {path}: {error}")
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, f"not a single-link regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"cannot open {path} without following links: {error}")
    try:
        opened = os.fstat(descriptor)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, f"opened path is not regular: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        closed = os.fstat(descriptor)
        after = os.lstat(path)
        require(identity(before) == identity(opened) == identity(closed) == identity(after), f"file changed while reading: {path}")
        raw = b"".join(chunks)
        require(len(raw) == closed.st_size, f"file size changed while reading: {path}")
        return raw
    except OSError as error:
        fail(f"cannot read {path}: {error}")
    finally:
        os.close(descriptor)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    fail(f"non-finite JSON constant is forbidden: {value}")


def parse_record(raw: bytes) -> dict[str, Any]:
    require(raw.endswith(b"\n") and b"\r" not in raw, "record must be LF text ending in one newline")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"invalid record encoding or JSON: {error}")
    require(isinstance(value, dict), "record root must be an object")
    return value


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in all_strings(child)]
    if isinstance(value, dict):
        return [item for key, child in value.items() for item in (all_strings(key) + all_strings(child))]
    return []


def check_no_private_locator(value: Any) -> None:
    forbidden = ("/Users/", "/home/", "/private/", "file://", "Mobile Documents", "CloudDocs", "com~apple")
    for text in all_strings(value):
        require(not any(marker.casefold() in text.casefold() for marker in forbidden), "record leaks a private or absolute locator")


def parse_manifest(raw: bytes) -> tuple[list[tuple[str, str]], bytes]:
    require(raw.endswith(b"\n") and b"\r" not in raw, "remote manifest must be LF text ending in one newline")
    rows: list[tuple[str, str]] = []
    for index, line in enumerate(raw.splitlines(), start=1):
        fields = line.split(b"\t")
        require(len(fields) == 2, f"manifest line {index} must contain one tab")
        try:
            oid, ref = (field.decode("ascii") for field in fields)
        except UnicodeDecodeError:
            fail(f"manifest line {index} is not ASCII")
        require(HEX40.fullmatch(oid) is not None, f"manifest line {index} has invalid Git object ID")
        require(REF.fullmatch(ref) is not None, f"manifest line {index} has invalid ref name")
        require(".." not in ref and "//" not in ref, f"manifest line {index} has ambiguous ref spelling")
        rows.append((oid, ref))
    require(rows == list(EXPECTED_HEADS), "remote manifest differs from the exact observed head set or order")
    return rows, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_record_sha256(record: dict[str, Any]) -> str:
    """Bind every JSON key and value independently of whitespace and key order."""
    raw = json.dumps(
        record,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(raw)


def timestamp(value: Any) -> None:
    require(isinstance(value, str) and UTC_TIMESTAMP.fullmatch(value) is not None, "observation timestamp is not a 2026-09-02 UTC timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        fail(f"invalid observation timestamp: {error}")


def check_hex(value: Any, name: str) -> None:
    require(isinstance(value, str) and HEX40.fullmatch(value) is not None, f"{name} must be a lowercase 40-hex Git OID")


def check_snapshot(record: dict[str, Any], manifest_raw: bytes) -> None:
    require(record.get("schema") == "pid-rs/post-publication-custody/v2", "schema marker drifted")
    require(record.get("record_id") == "PPC-20260902-02", "record identity drifted")
    require(record.get("repository") == "sepahead/pid-rs", "repository identity drifted")
    require(record.get("observation_kind") == "dated_snapshot_not_live_manifest", "snapshot/live boundary drifted")
    phase_times = (
        record.get("observation_started_at_utc"),
        record.get("actions_completed_at_utc"),
        record.get("final_observed_at_utc"),
    )
    for value in phase_times:
        timestamp(value)
    require(
        phase_times
        == (
            "2026-09-02T00:06:18Z",
            "2026-09-02T00:07:35Z",
            "2026-09-02T04:43:02Z",
        ),
        "phase timestamp identity drifted",
    )
    require(tuple(sorted(phase_times)) == phase_times, "phase timestamps are not ordered")
    phase_basis = record.get("phase_timestamp_basis")
    require(isinstance(phase_basis, dict) and set(phase_basis) == {
        "observation_started_at_utc",
        "actions_completed_at_utc",
        "final_observed_at_utc",
        "ordering",
    }, "phase timestamp basis is incomplete")
    require(
        "not inferred from a filesystem mtime" in phase_basis["actions_completed_at_utc"]
        and "not an atomic snapshot or an attestation" in phase_basis["final_observed_at_utc"]
        and phase_basis["ordering"]
        == "observation_started_at_utc <= actions_completed_at_utc <= final_observed_at_utc",
        "phase timestamp boundary weakened",
    )
    scope = record.get("scope")
    require(isinstance(scope, str) and "does not rewrite dated snapshots" in scope and "future deletion" in scope, "scope boundary weakened")

    publication = record.get("publication")
    require(isinstance(publication, dict), "publication object missing")
    for key, expected in (
        ("commit", EXPECTED_COMMIT),
        ("parent", EXPECTED_PARENT),
        ("tree", EXPECTED_TREE),
        ("remote_main", EXPECTED_COMMIT),
        ("local_main", EXPECTED_COMMIT),
        ("primary_worktree_head", EXPECTED_PRIMARY_HEAD),
    ):
        check_hex(publication.get(key), f"publication.{key}")
        require(publication[key] == expected, f"publication.{key} drifted")
    require(publication.get("primary_worktree_status") == "dirty_review_lane_retained_and_not_overwritten", "dirty-lane boundary weakened")
    require(publication.get("anchor_kind") == "mainline_published_commit_observation", "publication anchor semantics drifted")
    require(publication.get("local_main_source") == {
        "repository_role": "primary common Git directory",
        "command": "git -C <primary-repository> rev-parse refs/heads/main",
        "meaning": "The local primary ref value observed during the dated cleanup; the detached receipt checkout is not evidence for this field.",
    }, "local-main evidence boundary drifted")
    require(publication.get("receipt_source_checkout") == {
        "state": "detached_at_publication_anchor",
        "meaning": "The checkout used to prepare this record was separate from the dirty primary lane.",
    }, "receipt-checkout boundary drifted")

    remote = record.get("live_remote_heads")
    require(isinstance(remote, dict), "live_remote_heads object missing")
    require(remote.get("observed_command") == "git ls-remote --heads git@github.com:sepahead/pid-rs.git", "remote command drifted")
    require(remote.get("query_observed_at_utc") == record["final_observed_at_utc"], "remote query timestamp is not the final observation timestamp")
    require(remote.get("manifest_path") == "audit/evidence/post-publication-remote-heads-2026-09-02.tsv", "manifest locator drifted")
    require(remote.get("manifest_encoding") == "UTF-8 bytes, LF line endings, final LF, one OID TAB refname record per line", "manifest encoding contract drifted")
    require(remote.get("head_count") == len(EXPECTED_HEADS), "remote head count drifted")
    require(remote.get("raw_output_sha256") == EXPECTED_REMOTE_RAW_SHA256, "raw remote digest drifted")
    require(remote.get("refname_sorted_output_sha256") == EXPECTED_REMOTE_RAW_SHA256, "ref-name digest drifted")
    require(remote.get("whole_line_sorted_output_sha256") == EXPECTED_REMOTE_WHOLE_LINE_SHA256, "whole-line digest drifted")
    require(remote.get("sort_contract") == "LC_ALL=C sort -t <TAB> -k2,2 on the tab-separated OID/refname lines; retain the final newline", "sort contract drifted")
    require(remote.get("retired_refs_absent_from_observed_manifest") is True, "retired-ref absence flag was weakened")
    absence_scope = remote.get("absence_scope")
    require(isinstance(absence_scope, str) and "observed 14-line direct-query manifest only" in absence_scope and "future absence" in absence_scope, "retired-ref absence scope weakened")
    note = remote.get("note")
    require(isinstance(note, str) and "local checkout may retain stale remote-tracking names" in note and "direct hosted query" in note and "dated snapshot, not a live branch inventory" in note, "remote/cache or snapshot distinction weakened")
    expected_entries = [{"oid": oid, "ref": ref} for oid, ref in EXPECTED_HEADS]
    require(remote.get("entries") == expected_entries, "JSON remote-entry projection differs from the exact manifest")
    expected_raw = b"".join(f"{oid}\t{ref}\n".encode("ascii") for oid, ref in EXPECTED_HEADS)
    require(manifest_raw == expected_raw, "manifest bytes are not the captured tab-separated preimage")
    require(sha256(manifest_raw) == EXPECTED_REMOTE_RAW_SHA256, "manifest digest does not match raw observation")
    require(sha256(b"".join(sorted(manifest_raw.splitlines(keepends=True)))) == EXPECTED_REMOTE_WHOLE_LINE_SHA256, "whole-line digest does not match")
    ref_sorted = b"".join(sorted(manifest_raw.splitlines(keepends=True), key=lambda line: line.split(b"\t", 1)[1]))
    require(sha256(ref_sorted) == EXPECTED_REMOTE_RAW_SHA256, "ref-name sorted digest does not match")
    expected_heads_by_ref = {ref: oid for oid, ref in EXPECTED_HEADS}
    require(publication["remote_main"] == expected_heads_by_ref["refs/heads/main"], "publication main is absent from manifest")
    retired_names = {name for name, _ in EXPECTED_RETIRED}
    require(retired_names.isdisjoint({ref for _, ref in EXPECTED_HEADS}), "retired ref remains in observed head manifest")

    local_reconcile = record.get("local_ref_reconciliation")
    require(isinstance(local_reconcile, dict), "local ref reconciliation missing")
    require(local_reconcile.get("operation") == "git pack-refs --all --prune", "reconciliation operation drifted")
    require(local_reconcile.get("pre_packed_refs_sha256") == EXPECTED_PRE_PACKED_SHA256, "pre-packed digest drifted")
    require(local_reconcile.get("post_packed_refs_sha256") == EXPECTED_POST_PACKED_SHA256, "post-packed digest drifted")
    require(local_reconcile.get("status_projection_sha256_before_after") == EXPECTED_STATUS_HASH, "status preservation digest drifted")
    require(local_reconcile.get("status_projection_line_count_before_after") == 126, "status line-count preservation drifted")
    require(local_reconcile.get("status_projection_command") == "git status --porcelain=v1 --untracked-files=normal | shasum -a 256", "status projection command drifted")
    require(local_reconcile.get("head_before_after") == EXPECTED_PRIMARY_HEAD, "checked-out head preservation drifted")
    values = local_reconcile.get("post_expected_values")
    require(values == {"refs/heads/main": EXPECTED_COMMIT, "refs/heads/review/sx-count-event-bridge-r2": EXPECTED_PRIMARY_HEAD, "refs/remotes/origin/main": EXPECTED_COMMIT}, "post-packed ref values drifted")
    result = local_reconcile.get("result")
    require(isinstance(result, str) and "garbage collection was not run" in result and "unchanged" in result, "reconciliation safety boundary weakened")

    tracking = record.get("local_tracking_cleanup")
    require(tracking == [{
        "ref": "refs/remotes/origin/sepahead/pid-rs-release-integration-r4",
        "old_oid": "535d7a44e2f8108f806af48cc27b86009239ec4e",
        "action": "pruned_after_direct_remote_absence_check",
        "object_custody": "retained by archive/bundle routes",
        "evidence_class": "operator_action_record",
        "action_scope": "local remote-tracking metadata only; no hosted-ref deletion claim",
    }], "local tracking cleanup record drifted")

    local_validation = record.get("local_validation")
    require(isinstance(local_validation, dict), "local validation object missing")
    require(local_validation.get("clean_checkout_ci") == "passed" and local_validation.get("focused_formal_and_hostile_suites") == "passed" and local_validation.get("publication_link_math_catalog_and_source_state_checks") == "passed", "local validation result drifted")
    validation_note = local_validation.get("note")
    require(isinstance(validation_note, str) and "separate throwaway clean validation checkout" in validation_note and "not the retained dirty primary" in validation_note, "validation checkout distinction weakened")

    retired = record.get("retired_remote_branches")
    require(isinstance(retired, list), "retired branch list missing")
    require(len(retired) == len(EXPECTED_RETIRED) and all(isinstance(item, dict) for item in retired), "retired branch records are not a complete object list")
    actual_retired = tuple((item["ref"], item["old_oid"]) for item in retired)
    require(actual_retired == EXPECTED_RETIRED, "retired branch identity/order drifted")
    for ref, old_oid in EXPECTED_RETIRED:
        check_hex(old_oid, f"retired {ref} old_oid")
        require(next(item["reason"] for item in retired if item["ref"] == ref) == EXPECTED_RETIRED_REASONS[ref], f"retired {ref} reason drifted")
        require(ref not in {head_ref for _, head_ref in EXPECTED_HEADS}, f"retired ref appears in manifest: {ref}")

    containment = record.get("containment_checks")
    require(isinstance(containment, list), "containment checks missing")
    require(len(containment) == len(EXPECTED_CONTAINMENT) and all(isinstance(item, dict) for item in containment), "containment records are not a complete object list")
    actual_containment = {
        item["retired_oid"]: (item["retained_ref"], item["retained_oid"])
        for item in containment
    }
    require(actual_containment == EXPECTED_CONTAINMENT, "containment projection drifted")
    require(all(item["predicate"] == "retired commit is an ancestor of retained ref" for item in containment), "containment predicate wording drifted")

    hosted_runs = record.get("hosted_runs")
    expected_runs = (
        (33547094635, "CI", "CI", "push", 47, "2026-09-01T23:05:44Z"),
        (33547094668, "SxPID3 informative-invariance verification", "SxPID3 informative-invariance verification", "push", 3, "2026-09-01T19:39:05Z"),
        (33547093983, "CodeQL", "Push on main", "dynamic", 4, "2026-09-01T19:11:34Z"),
        (33547094598, "Bounded SxPID3 keyed-scalar audit expressions", "Bounded SxPID3 keyed-scalar audit expressions", "push", 1, "2026-09-01T19:11:19Z"),
        (33547094741, "KSG M1a composite v12 terminal preservation", "KSG M1a composite v12 terminal preservation", "push", 1, "2026-09-01T19:02:01Z"),
    )
    require(isinstance(hosted_runs, list) and len(hosted_runs) == len(expected_runs) and all(isinstance(item, dict) for item in hosted_runs), "hosted run list cardinality or shape drifted")
    actual_runs = tuple((item["run_id"], item["workflow_name"], item["name"], item["event"], item["jobs"], item["updated_at_utc"]) for item in hosted_runs)
    require(actual_runs == expected_runs, "hosted run identity drifted")
    require(all(
        item["head_sha"] == EXPECTED_COMMIT
        and item["head_branch"] == "main"
        and item["attempt"] == 1
        and item["status"] == "completed"
        and item["conclusion"] == "success"
        and item["required"] is True
        and item["url"] == f"https://github.com/sepahead/pid-rs/actions/runs/{item['run_id']}"
        for item in hosted_runs
    ), "hosted run scope/status drifted")
    census = record.get("hosted_census")
    require(isinstance(census, dict), "hosted census missing")
    expected_census = {"required_runs": 5, "successful_runs": 5, "jobs": 56, "failed": 0, "skipped": 0, "cancelled": 0, "timed_out": 0, "action_required": 0, "neutral": 0, "stale": 0}
    require(all(census.get(key) == value for key, value in expected_census.items()), "hosted census drifted")
    require(sum(item["jobs"] for item in hosted_runs) == census["jobs"], "hosted job arithmetic does not close")
    require("Project-derived, not a native GitHub field" in census.get("stale_definition", ""), "stale-count boundary weakened")
    require("preregistered closure obligations" in census.get("required_set_basis", ""), "required-run-set boundary weakened")
    supplementary = census.get("supplementary_runs")
    require(isinstance(supplementary, list) and len(supplementary) == 1, "supplementary run record drifted")
    supplementary_run = supplementary[0]
    require(
        supplementary_run.get("run_id") == 33558833307
        and supplementary_run.get("workflow_name") == "CodeQL"
        and supplementary_run.get("event") == "schedule"
        and supplementary_run.get("head_sha") == EXPECTED_COMMIT
        and supplementary_run.get("status") == "completed"
        and supplementary_run.get("conclusion") == "success"
        and supplementary_run.get("jobs") == 4,
        "supplementary CodeQL run drifted",
    )

    routes = record.get("retired_ref_routes")
    require(isinstance(routes, list) and len(routes) == len(EXPECTED_RETIRED), "retired-ref route list drifted")
    require(tuple((item.get("retired_ref"), item.get("retired_oid")) for item in routes) == EXPECTED_RETIRED, "retired-ref route identity drifted")
    for index, item in enumerate(routes):
        if index < 7:
            require(item.get("route") == "ancestor_of_published_main" and item.get("custody_ref") == "refs/heads/main" and item.get("custody_oid") == EXPECTED_COMMIT, "mainline ancestry route drifted")
        else:
            retained_ref, retained_oid = EXPECTED_CONTAINMENT[item["retired_oid"]]
            require(item.get("route") == "ancestor_of_retained_ref" and item.get("custody_ref") == retained_ref and item.get("custody_oid") == retained_oid, "retained-ref ancestry route drifted")
        require(item.get("predicate") == "git merge-base --is-ancestor retired_oid custody_oid exited 0 in the cleanup observation", "ancestry predicate drifted")
    require("Ancestry does not imply byte identity" in record.get("retired_ref_route_boundary", "") and "continued future reachability" in record.get("retired_ref_route_boundary", ""), "ancestry boundary weakened")

    worktrees = record.get("retired_primary_worktrees")
    expected_worktrees = (
        ("recovery-c4", "bc3aa80fb6025e709c2906a08bce25a4fac40578", "candidate ancestry and complete bundle", 30416592, "503fa4917ab80c801b203c4cb3ee0d0683bb444ba39857eec481cf9a8917ff59"),
        ("ksg-revision-4", "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c", "archive head, exact 110-path comparison, and verified historical bundle observation", 11361236, "532ebec0a2a5f2757ccc872925888e1257a082031312d9c7fd4042f6c40cad40"),
        ("m1a-correction", "dc7b8de0a87443ef2bcde71b19938642f1af2197", "archive head, exact tracked/untracked comparison, ignored-output adjudication, and verified historical bundle observation", 11761811, "df4fa378a5a9faf97aa3410ed14a26a0fa870699945b1d91e6b73d2fa72ff2b3"),
    )
    require(isinstance(worktrees, list) and len(worktrees) == len(expected_worktrees) and all(isinstance(item, dict) for item in worktrees), "retired worktree list shape drifted")
    actual_worktrees = tuple((item["id"], item["head"], item["custody"], item["bundle_bytes"], item["bundle_sha256"]) for item in worktrees)
    require(actual_worktrees == expected_worktrees, "retired worktree identity/custody drifted")
    require(all(HEX40.fullmatch(item["head"]) for item in worktrees), "retired worktree head is not a Git OID")
    require(all(item.get("evidence_class") == "historical_operator_observation" for item in worktrees), "worktree evidence class drifted")
    require("complete bundle" in worktrees[0].get("bundle_verification", ""), "C4 bundle-verification boundary drifted")
    require(all("raw preimage is not present" in item.get("bundle_verification", "") for item in worktrees[1:]), "historical KSG/M1a bundle boundary weakened")
    controls = record.get("cleanup_controls")
    require(isinstance(controls, dict), "cleanup_controls missing")
    require("force only for a named linked worktree" in controls.get("worktree_deletion_method", "") and "no required bytes remained" in controls.get("worktree_deletion_method", ""), "force-removal predicate weakened")
    require(controls.get("garbage_collection") == "not run", "garbage-collection boundary weakened")
    require("force-with-lease" in controls.get("remote_deletion_method", "") and "explicit expected old object" in controls.get("remote_deletion_method", ""), "remote lease control weakened")
    require("fresh git ls-remote --heads" in controls.get("remote_post_absence", "") and "14 heads" in controls.get("remote_post_absence", ""), "remote post-absence control weakened")
    require("exact old object guard" in controls.get("local_ref_deletion_method", ""), "local ref deletion guard weakened")
    require("fresh worktree/ref/status/object-reachability" in controls.get("post_removal_check", "") and "missing" in controls.get("post_removal_check", ""), "post-removal check weakened")
    require(controls.get("action_evidence_class") == "bounded_operator_action_record" and "not an independently witnessed transcript" in controls.get("action_evidence_boundary", ""), "operator-evidence boundary weakened")
    require("Only the nine named remote refs" in controls.get("scope_boundary", "") and "no global branch" in controls.get("scope_boundary", ""), "cleanup scope boundary weakened")
    inventory = record.get("observed_local_inventory")
    require(isinstance(inventory, dict), "local inventory object missing")
    for key, expected in (("primary_registered_worktrees", 1), ("primary_local_heads", 4), ("primary_archive_refs", 3), ("primary_checkpoint_refs", 5), ("primary_quarantine_refs", 48), ("primary_remote_tracking_refs", 2)):
        require(inventory.get(key) == expected, f"local inventory value drifted: {key}")
    require(isinstance(inventory.get("inventory_note"), str) and "primary common Git directory" in inventory["inventory_note"] and "stale names" in inventory["inventory_note"], "inventory scope boundary weakened")

    final_local = record.get("final_local_observation")
    require(final_local == {
        "observed_at_utc": "2026-09-02T04:43:02Z",
        "head": EXPECTED_PRIMARY_HEAD,
        "status_projection_command": "git status --porcelain=v1 --untracked-files=normal | shasum -a 256",
        "status_projection_sha256": EXPECTED_STATUS_HASH,
        "status_projection_line_count": 126,
        "registered_worktrees": 1,
        "local_main": EXPECTED_COMMIT,
        "origin_main": EXPECTED_COMMIT,
        "boundary": "A bounded read-only projection of the primary common Git directory; the dirty review lane remains unadjudicated and was not overwritten. It is not an atomic filesystem inventory.",
    }, "final local observation drifted")

    temporary = record.get("retired_temporary_state")
    expected_temporary_kinds = ("clean_validation_checkout", "clean_release_audit_checkout", "render_and_source_state_scratch", "available_audit_clone", "build_targets_and_reproducible_render_caches")
    require(isinstance(temporary, list) and len(temporary) == len(expected_temporary_kinds) and all(isinstance(item, dict) for item in temporary), "temporary-state records are incomplete")
    require(tuple(item.get("kind") for item in temporary) == expected_temporary_kinds, "temporary-state identity/order drifted")
    require(all(isinstance(item.get("custody"), str) and isinstance(item.get("predicate"), str) and item["custody"] and item["predicate"] for item in temporary), "temporary-state custody predicates are incomplete")
    require("not this receipt source checkout" in temporary[0]["predicate"], "validation-source distinction weakened")

    historical = record.get("historical_records")
    require(historical == {
        "primary_ledger": "audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json",
        "sibling_ledger": "audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json",
        "interpretation": "Both are immutable, bounded pre-cleanup observations. Their no-authority fields remain correct for those observations and are not current cleanup state.",
    }, "historical-ledger interpretation drifted")

    retained = record.get("retained_state")
    require(isinstance(retained, dict), "retained-state object missing")
    required_retained = {
        "primary_dirty_review_lane",
        "latest_private_primary_package",
        "local_divergent_workflow_branches",
        "primary_archive_and_quarantine_refs",
        "remote_archive_and_diagnostic_refs",
        "c12_registry_and_r4_worktree",
        "c11_fresh_clone",
        "c3_guide_reproduction_clones",
    }
    require(set(retained) == required_retained, "retained-state categories drifted")
    require(retained["primary_dirty_review_lane"] == {"head": EXPECTED_PRIMARY_HEAD, "reason": "unpublished and not proved redundant; never overwritten"}, "dirty review lane custody weakened")
    require(retained["local_divergent_workflow_branches"] == ["refs/heads/codex/integration-20260804", "refs/heads/codex/workflow-publication-20260804"], "divergent branch retention drifted")
    package = retained["latest_private_primary_package"]
    require(package == {
        "captured_at_utc": "2026-09-02T04:36:04Z",
        "source_head": EXPECTED_PRIMARY_HEAD,
        "source_branch": "refs/heads/review/sx-count-event-bridge-r2",
        "status_projection_command": "git status --porcelain=v2 --branch --untracked-files=all -z",
        "status_projection_sha256": "991b4d72b2388d05ababf526af40a4eafdf836a3b6a9a2dc0daee269a2407e3a",
        "tracked_patch_bytes": 1549131,
        "tracked_patch_sha256": "d5b089ef4a5a93d8b96c7ef95d2da6b23c8c08bc75603ced11bdd2216f3537f1",
        "staged_patch_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "untracked_leaf_count": 160,
        "captured_untracked_leaf_count": 159,
        "excluded_untracked_path": ".local/state/gh/device-id",
        "untracked_tar_bytes": 1008981,
        "untracked_tar_sha256": "ae94bffad48b7eabae3d6a794fbb7676dbeb6230ea0c63755264e8f5d759ac40",
        "all_refs_bundle_bytes": 36426597,
        "all_refs_bundle_sha256": "07562762e2a68cffd41f3a44ae76f18fba118802927217f91cf47da5f94259ed",
        "bundle_verify_exit": 0,
        "bundle_verify_output_sha256": "80aaef8688091f51c56ed399697238506f0e7921f99308da390a1bc475716265",
        "manifest_sha256": "a14d4822846bf90c626c0266f283cfaa857abe37705d625647565d0ab395e9c9",
        "locator_class": "private local preservation; no public or absolute locator is recorded",
        "boundary": "This supplements rather than overwrites earlier dirty-primary packages. It preserves bytes for later adjudication; it does not publish or scientifically accept them.",
    }, "private primary-package custody record drifted")
    require(all(isinstance(retained[key], str) and retained[key] for key in required_retained if key not in {"primary_dirty_review_lane", "latest_private_primary_package", "local_divergent_workflow_branches"}), "retained-state rationale is incomplete")

    artifacts = record.get("presentation_artifacts")
    require(isinstance(artifacts, dict), "presentation artifact binding missing")
    expected_artifact_paths = {
        "builder": "scripts/build-post-publication-custody-pdf.sh",
        "markdown": "audit/evidence/post-publication-custody-2026-09-02.md",
        "header": "audit/evidence/post-publication-custody/header.tex",
        "filter": "audit/evidence/post-publication-custody/filter.lua",
        "figure_svg": "audit/formal/figures/post-publication-custody/state-machine.svg",
        "figure_pdf": "audit/formal/figures/post-publication-custody/state.pdf",
        "receipt_pdf": "output/pdf/post-publication-custody-2026-09-02.pdf",
    }
    for name, relative in expected_artifact_paths.items():
        item = artifacts.get(name)
        require(isinstance(item, dict) and item.get("path") == relative, f"presentation artifact path drifted: {name}")
        digest = item.get("sha256")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"presentation artifact digest missing: {name}")
        require(sha256(read_regular(ROOT / relative)) == digest, f"presentation artifact bytes drifted: {name}")
    require(artifacts["figure_pdf"].get("presentation_derivative") is True, "figure-PDF derivative boundary weakened")
    require(artifacts["receipt_pdf"].get("presentation_derivative") is True, "receipt-PDF derivative boundary weakened")
    require(artifacts["receipt_pdf"].get("pdf_version") == "1.7" and artifacts["receipt_pdf"].get("pages") == 6, "receipt PDF profile drifted")
    require(artifacts.get("tool_versions") == {
        "pandoc": "pandoc 3.10.2",
        "lualatex": "LuaHBTeX 1.18.0 (TeX Live 2024)",
        "rsvg_convert": "rsvg-convert 2.62.3",
        "pypdf": "6.15.0",
    }, "presentation tool profile drifted")
    require(artifacts.get("annotation_contract") == "Only HTTPS URI navigation links are admitted; relative, file, and /GoToR actions must be absent.", "annotation contract drifted")

    markdown = read_regular(ROOT / expected_artifact_paths["markdown"]).decode("utf-8")
    markdown_normalized = " ".join(markdown.split())
    for token in (
        "PPC-20260902-02",
        *phase_times,
        EXPECTED_COMMIT,
        EXPECTED_PRIMARY_HEAD,
        EXPECTED_REMOTE_RAW_SHA256,
        "not an independently witnessed execution transcript",
        "no PDF/UA",
    ):
        require(token in markdown_normalized, f"human receipt lacks bound token: {token}")
    require("PPC-20260902-01" not in markdown, "human receipt retains the stale record identifier")
    check_no_private_locator(markdown)

    review = record.get("review")
    require(review == {
        "mandatory_lenses": 20,
        "additional_lenses": 50,
        "total_lenses": 70,
        "visual_pdf_lenses": 20,
        "council_kind": "agent_self_review_not_independent_human_or_scientific_review",
        "lens_count_boundary": "Process coverage count, not an assurance probability or proof.",
        "council_disposition": "green_with_explicit_retention_caveats_for_custody_operation",
    }, "review receipt drifted")
    require(tuple(record.get("nonclaims", ())) == EXPECTED_NONCLAIMS, "nonclaim list drifted")
    check_no_private_locator(record)
    # This immutable dated record is closed-world.  The field-level checks above
    # provide causal diagnostics; the final canonical digest rejects unknown
    # keys, contradictory suffixes, or any coordinated semantic addition that
    # those checks do not yet name explicitly.
    require(
        canonical_record_sha256(record) == EXPECTED_RECORD_CANONICAL_SHA256,
        "record contains an unreviewed key or value",
    )


def main() -> int:
    try:
        record_raw = read_regular(RECORD)
        require(
            sha256(record_raw) == EXPECTED_RECORD_RAW_SHA256,
            "record byte identity drifted",
        )
        record = parse_record(record_raw)
        _, manifest_raw = parse_manifest(read_regular(MANIFEST))
        check_snapshot(record, manifest_raw)
    except CheckError as error:
        print(f"post-publication custody error: {error}", file=sys.stderr)
        return 1
    print("OK: post-publication custody snapshot and exact remote-head manifest are bounded and consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
