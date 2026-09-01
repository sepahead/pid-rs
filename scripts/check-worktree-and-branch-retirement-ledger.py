#!/usr/bin/env python3
"""Validate the bounded primary worktree/ref/branch retirement ledger.

The checked-in record is an immutable observation, not a live-state probe and not
deletion authority.  The validator binds its exact bytes, applies a closed JSON
Schema, recomputes manifest projections, and rejects scope or custody escalation.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types
from typing import Any


if sys.version_info < (3, 11):
    raise SystemExit("check-worktree-and-branch-retirement-ledger.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent


def load_schema_validator() -> tuple[type[ValueError], Any]:
    """Compile the checked-in validator without relying on ``sys.path``."""
    path = ROOT / "scripts/json_schema_subset.py"
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit("JSON-schema validator is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        source = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            source.extend(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)

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

    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size
    ):
        raise SystemExit("JSON-schema validator changed during exact-source read")
    module = types.ModuleType("retirement_ledger_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source),
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


SchemaValidationError, validate_json_schema = load_schema_validator()
LEDGER = ROOT / "audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json"
SCHEMA = ROOT / "audit/evidence/worktree-and-branch-retirement-ledger-v1.schema.json"
EXPECTED_LEDGER_SHA256 = "29c6d6e0b2fe4b51b154e88be950db32ad214f64a67041c1ad215e756c8270bf"
EXPECTED_SCHEMA_SHA256 = "3e53bdc07785af6cf9394f2b5b3d62e3640b15be79a88c82ff2b56648be61e75"
EXPECTED_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EXPECTED_NAMESPACE_STATE = {
    "refs/archive": (3, "7ffdcc2da869f0790049b09b10b691bae3b33d00ebe09cc4b7b4f29d0aa99953"),
    "refs/codex/checkpoints": (5, "fba248c8e5680846990eb7221b15415c9fd1a6dab15d6fc98117ddbdb8d72c52"),
    "refs/heads": (7, "9e475349caddce278e512bc5bcfc948559c21c658ba848003a4baab75a8b11f0"),
    "refs/pid-rs/quarantine/20260825": (48, "2eaf684c95ebfa7ae3d8f67df184ccd198a11373e9967687b650e14a80c934a9"),
    "refs/remotes": (3, "b913f1fef8780a07d5d854f120adedf5535a720fba6f70f4ccf3031b97276e13"),
    "refs/tags": (1, "cb99f04e5d0030c0866fa4e76f73436f3938c1777f13c15b0014b368973a71f9"),
}
EXPECTED_NAMESPACE_ORDER = tuple(EXPECTED_NAMESPACE_STATE)
EXPECTED_WORKTREE_STATE = {
    "primary-review": {
        "branch": "refs/heads/review/sx-count-event-bridge-r2",
        "custody_status": "not_complete_for_current_dirty_bytes",
        "disposition": "retain_pending_dirty_state_adjudication",
        "head": "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56",
        "head_mode": "branch",
        "reason": (
            "The current methods narrative and one worktree-local identifier require separate "
            "adjudication; the current dirty bytes are not wholly represented by one durable "
            "snapshot."
        ),
        "tracked": 69,
        "tracked_sha256": "a84df45226c665c9330d42de3ec94138a9e1510af2ff7d6f430cd9f27f416415",
        "untracked": 160,
        "untracked_sha256": "a62cc7bf0cf3c5b5066846a7b123906c423a90c1df6c9e02421a55712e5bd962",
    },
    "recovery-c4": {
        "branch": "detached",
        "custody_status": "clean_head_advertised_in_complete_bundle",
        "disposition": "conditional_retirement_candidate_after_final_main_gates",
        "head": "bc3aa80fb6025e709c2906a08bce25a4fac40578",
        "head_mode": "detached",
        "reason": (
            "The lane is clean and its head is preserved, but the final candidate and exact "
            "final-main gates do not yet exist."
        ),
        "tracked": 0,
        "tracked_sha256": EXPECTED_EMPTY_SHA256,
        "untracked": 0,
        "untracked_sha256": EXPECTED_EMPTY_SHA256,
    },
    "ksg-revision-4": {
        "branch": "refs/heads/codex/ksg-rev4-candidate-20260726",
        "custody_status": "dirty_paths_previously_byte_compared_to_archive_head",
        "disposition": (
            "conditional_retirement_candidate_after_fresh_110_path_comparison_and_final_main_gates"
        ),
        "head": "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c",
        "head_mode": "branch",
        "reason": (
            "The 38 tracked and 72 untracked paths require a fresh byte comparison to the "
            "preserved archive head immediately before retirement."
        ),
        "tracked": 38,
        "tracked_sha256": "005e99c75d8e3ba5731b6d662a62e5cd078e7b643d0a9a33d1f08c4e81958f60",
        "untracked": 72,
        "untracked_sha256": "7a01a06bd98a5e652da8db15c4ed48209941ef35019ef0ce53b0aba161d652e3",
    },
    "m1a-correction": {
        "branch": "refs/heads/codex/m1a-ci-fix-20260727",
        "custody_status": (
            "dirty_paths_previously_byte_compared_to_archive_head_but_ignored_outputs_excluded"
        ),
        "disposition": "retain_pending_ignored_output_adjudication",
        "head": "dc7b8de0a87443ef2bcde71b19938642f1af2197",
        "head_mode": "branch",
        "reason": (
            "The 34 tracked and 11 untracked paths have prior archive coverage, but 143 ignored "
            "presentation files remain outside that coverage and require adjudication."
        ),
        "tracked": 34,
        "tracked_sha256": "dc1aabdf5ffee7b2cdf3d6e7144cb5e9bf68814716d67c98daecc95575e68598",
        "untracked": 11,
        "untracked_sha256": "97270180998665706fe36e3bd589772403c59e2d1a87a9b96eeaf50b0ba5920f",
    },
}
EXPECTED_HOSTED_TIPS = {
    "refs/heads/archive/composite-v5-rejected-umask-20260818": "062025c3fc283db9bdb105219dbcc82719771175",
    "refs/heads/archive/composite-v5-unqualified-draft-20260818": "f7c6122d25ea098a36fa1fc6d672d78f25b783bb",
    "refs/heads/archive/composite-v6-pre-r11-draft-20260818": "1ef37646e168b645853e1857d0205233a87b68dc",
    "refs/heads/archive/composite-v9-rejected-local-authority-oversize-20260822": "769547a6d6ed70a074707d90bc2f55393fd34fa4",
    "refs/heads/archive/composite-v9-rejected-r14-fixed-point-20260822": "113cbad2e58a9cfa40cf43b1c0ffc260b566aa92",
    "refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821": "0a6ece9c525ad7aad061f55b3edea83554891b42",
    "refs/heads/archive/exact-log-product-verifier-draft-20260828": "60774437488b376d30702146301e76b3186b5dd3",
    "refs/heads/archive/real-r-constructor-v8-public-disposition": "81d37370a21a4b5c9551e2cde7904e5e1ee28e67",
    "refs/heads/codex/primegaps-pid-blueprint-20260819": "9dcdf32f18076eefc768194079b4abf437009737",
    "refs/heads/diagnostic/c3-pdf-capture-20260830": "93edb4983129151ce0db8e58b0aad52cae0f47bc",
    "refs/heads/main": "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9",
    "refs/heads/sepahead/ci-pandoc-toolchain-fix": "b45a7eb2e15364d37ecffc3061bf4f9ac5812b7f",
    "refs/heads/sepahead/documentation-closure-v1": "30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1",
    "refs/heads/sepahead/exact-log-hostile-v1": "80443f9f2fa66452237013c9881cfaeeb984e5c1",
    "refs/heads/sepahead/galadriel-placement-guide-v1": "75a7acaa3f9432dc323be7e49f5eee1f9af781fd",
    "refs/heads/sepahead/galadriel-placement-main-v1": "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9",
    "refs/heads/sepahead/openaction-compat-candidate": "9ed6831d20de43467b1cff8adc8ee421a484f7fd",
    "refs/heads/sepahead/pdf-annotation-portability-corrected": "0af14fc97b7c5fe8c4df0361e37cd9cefaa9c6ba",
    "refs/heads/sepahead/pid-rs-release-integration-r4": "535d7a44e2f8108f806af48cc27b86009239ec4e",
    "refs/heads/sepahead/pid-rs-release-integration-r4-recovered": "008ee7fa615aa8370623566c21eb99862680c7b1",
    "refs/heads/sepahead/pid2-rev4-assurance-v1": "caf8c7be3e2249df8e959c8940632fd22ed09923",
    "refs/heads/sepahead/pid2-rev4-behavior-v1": "03c0980f256c2a66b3d64bff1686a8d116d76138",
    "refs/heads/sepahead/python-custody-m0-v1": "e16a6915262e8bf2fac1752ff959d9d3733c7a7d",
}
EXPECTED_HOSTED_SEMANTICS = {
    "refs/heads/archive/composite-v5-rejected-umask-20260818": (
        "retain_branch_only_history",
        "Rejected composite evidence remains branch-only negative evidence.",
    ),
    "refs/heads/archive/composite-v5-unqualified-draft-20260818": (
        "retain_branch_only_history",
        "Unqualified composite draft remains branch-only historical evidence.",
    ),
    "refs/heads/archive/composite-v6-pre-r11-draft-20260818": (
        "retain_branch_only_history",
        "Pre-revision composite draft remains branch-only historical evidence.",
    ),
    "refs/heads/archive/composite-v9-rejected-local-authority-oversize-20260822": (
        "retain_branch_only_history",
        "Rejected local-authority result remains branch-only negative evidence.",
    ),
    "refs/heads/archive/composite-v9-rejected-r14-fixed-point-20260822": (
        "retain_branch_only_history",
        "Rejected fixed-point result remains branch-only negative evidence.",
    ),
    "refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821": (
        "retain_branch_only_history",
        "Rejected workflow-PDF umask result remains branch-only negative evidence.",
    ),
    "refs/heads/archive/exact-log-product-verifier-draft-20260828": (
        "retain_branch_only_history",
        "The exact-log verifier draft has branch-only history.",
    ),
    "refs/heads/archive/real-r-constructor-v8-public-disposition": (
        "retain_branch_only_history",
        "The Real-R constructor disposition has branch-only history.",
    ),
    "refs/heads/codex/primegaps-pid-blueprint-20260819": (
        "retain_branch_only_history",
        "The PrimeGaps transfer blueprint has branch-only history.",
    ),
    "refs/heads/diagnostic/c3-pdf-capture-20260830": (
        "retain_branch_only_history",
        "The C3 PDF diagnostic capture has branch-only evidence.",
    ),
    "refs/heads/main": (
        "active_main",
        "This was the hosted main tip at the snapshot boundary.",
    ),
    "refs/heads/sepahead/ci-pandoc-toolchain-fix": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/documentation-closure-v1": (
        "conditional_retirement_candidate",
        "This is the pre-documentation candidate; retire only after its successor is exact final "
        "main and all gates pass.",
    ),
    "refs/heads/sepahead/exact-log-hostile-v1": (
        "retain_pending_adjudication",
        "An earlier hostile receipt remains distinct and requires scientific and archival "
        "adjudication.",
    ),
    "refs/heads/sepahead/galadriel-placement-guide-v1": (
        "retain_pending_adjudication",
        "Earlier guide, PDF, and figure variants remain distinct and require adjudication.",
    ),
    "refs/heads/sepahead/galadriel-placement-main-v1": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/openaction-compat-candidate": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/pdf-annotation-portability-corrected": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/pid-rs-release-integration-r4": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/pid-rs-release-integration-r4-recovered": (
        "conditional_retirement_candidate",
        "Retire only after exact final-main publication, hosted gates, and a lease-matched reread.",
    ),
    "refs/heads/sepahead/pid2-rev4-assurance-v1": (
        "retain_pending_adjudication",
        "A distinct earlier assurance document and source-state receipt require adjudication.",
    ),
    "refs/heads/sepahead/pid2-rev4-behavior-v1": (
        "retain_pending_adjudication",
        "A distinct historical behavior source-state receipt requires adjudication.",
    ),
    "refs/heads/sepahead/python-custody-m0-v1": (
        "retain_pending_adjudication",
        "A distinct registry preimage requires explicit retained-preimage adjudication.",
    ),
}
EXPECTED_NONCLAIMS = (
    "The ledger is not permission to delete any ref, branch, or worktree.",
    "The ledger does not cover sibling repositories or their Git registries.",
    "The restricted bundle does not preserve dirty, staged, untracked, or ignored bytes.",
    "A bundle verification result is not an authenticity or independent-custody proof.",
    "Reachability and byte custody do not establish mathematical correctness.",
    "A retained branch is not part of the active release surface merely because it is recorded.",
    "A digest binds observed bytes but is not a signature and does not replace a retrievable "
    "preimage.",
    "This snapshot cannot certify changes made after its completion time.",
)
EXPECTED_HOSTED_MANIFEST_SHA256 = "99cbf8e390aa0e8847aca13fa76f08e4db3293a99aaddb5df8b44f3a0621a735"
EXPECTED_ADVERTISED_MANIFEST_SHA256 = "f2700d0f1a79a64d7798f8bddda7ad4abae4cd0e64ac2cdb524e31f18052b467"
EXPECTED_BUNDLE_SHA256 = "89a751a60cb221e0aa336b348b5873f458417b0947a9d5d7920f9332ec82b7f7"


class LedgerError(RuntimeError):
    """The retirement ledger is malformed, ambiguous, or escalates its scope."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise LedgerError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def reject_constant(value: str) -> Any:
    raise LedgerError(f"non-finite JSON constant is forbidden: {value}")


def parse_json(raw: bytes, *, name: str) -> Any:
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise LedgerError(f"{name} must use LF text and end with one newline")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LedgerError(f"{name} is not UTF-8: {error}") from error
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise LedgerError(f"{name} is invalid JSON: {error}") from error


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise LedgerError(f"invalid UTC timestamp: {value!r}") from error
    return parsed.replace(tzinfo=timezone.utc)


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in all_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in all_strings(child)]
    return []


def check_no_locator_leak(value: Any) -> None:
    forbidden = (
        "/Users/",
        "/home/",
        "/private/",
        "file://",
        "Mobile Documents",
        "CloudDocs",
        "com~apple",
    )
    for item in all_strings(value):
        if any(marker.casefold() in item.casefold() for marker in forbidden):
            raise LedgerError("public ledger exposes an absolute or restricted storage locator")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LedgerError(message)


def stat_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def read_single_link_regular(path: Path) -> bytes:
    """Read one stable regular-file pathname without following symbolic links."""
    try:
        before = os.lstat(path)
    except OSError as error:
        raise LedgerError(f"cannot inspect required file {path}: {error}") from error
    require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        f"required path is not a single-link regular file: {path}",
    )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise LedgerError(f"cannot open required file without following links {path}: {error}") from error
    try:
        opened = os.fstat(descriptor)
        require(
            stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
            f"opened path is not a single-link regular file: {path}",
        )
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        closed = os.fstat(descriptor)
        try:
            after = os.lstat(path)
        except OSError as error:
            raise LedgerError(f"required file disappeared during read: {path}: {error}") from error
        require(
            stat.S_ISREG(after.st_mode)
            and after.st_nlink == 1
            and stat_identity(before)
            == stat_identity(opened)
            == stat_identity(closed)
            == stat_identity(after),
            f"required file identity changed during read: {path}",
        )
        raw = b"".join(chunks)
        require(len(raw) == closed.st_size, f"required file size changed during read: {path}")
        return raw
    except OSError as error:
        raise LedgerError(f"cannot read required file {path}: {error}") from error
    finally:
        os.close(descriptor)


def validate_worktrees(ledger: dict[str, Any]) -> None:
    records = ledger["worktrees"]
    require([item["id"] for item in records] == [
        "primary-review",
        "recovery-c4",
        "ksg-revision-4",
        "m1a-correction",
    ], "worktree order or identity drifted")
    for record in records:
        expected = EXPECTED_WORKTREE_STATE[record["id"]]
        require(record["head"] == expected["head"], f"{record['id']}: head drifted")
        require(record["branch"] == expected["branch"], f"{record['id']}: branch drifted")
        require(record["head_mode"] == expected["head_mode"], f"{record['id']}: HEAD mode drifted")
        require(
            record["custody_status"] == expected["custody_status"],
            f"{record['id']}: custody status drifted",
        )
        require(
            record["disposition"] == expected["disposition"],
            f"{record['id']}: disposition drifted",
        )
        require(record["reason"] == expected["reason"], f"{record['id']}: reason drifted")
        require(record["tracked_change_entries"] == expected["tracked"], f"{record['id']}: tracked count drifted")
        require(record["untracked_leaf_paths"] == expected["untracked"], f"{record['id']}: untracked count drifted")
        require(record["tracked_status_stream_sha256"] == expected["tracked_sha256"], f"{record['id']}: tracked manifest drifted")
        require(record["untracked_path_stream_sha256"] == expected["untracked_sha256"], f"{record['id']}: untracked manifest drifted")
        require(record["deletion_eligible"] is False, f"{record['id']}: deletion eligibility escalated")
        ignored = record["ignored_outputs"]
        if ignored["observed"]:
            counts = (ignored["png_files"], ignored["pdf_files"], ignored["other_files"])
            require(all(isinstance(item, int) for item in counts), f"{record['id']}: observed ignored counts are incomplete")
            require(sum(counts) == ignored["file_count"], f"{record['id']}: ignored file accounting does not sum")
        else:
            require(all(ignored[key] is None for key in ("bytes", "file_count", "other_files", "pdf_files", "png_files")), f"{record['id']}: unobserved ignored state contains invented counts")


def validate_namespaces(ledger: dict[str, Any]) -> bytes:
    namespaces = ledger["local_ref_namespaces"]
    require(tuple(item["prefix"] for item in namespaces) == EXPECTED_NAMESPACE_ORDER, "local namespace order or set drifted")
    all_refs: list[str] = []
    advertised_lines: list[str] = []
    for namespace in namespaces:
        prefix = namespace["prefix"]
        expected_count, expected_digest = EXPECTED_NAMESPACE_STATE[prefix]
        entries = namespace["entries"]
        require(namespace["count"] == expected_count == len(entries), f"{prefix}: ref count drifted")
        require(namespace["manifest_sha256"] == expected_digest, f"{prefix}: manifest binding drifted")
        require(namespace["deletion_eligible"] is False, f"{prefix}: deletion eligibility escalated")
        refs = [item["ref"] for item in entries]
        require(refs == sorted(refs) and len(refs) == len(set(refs)), f"{prefix}: refs are not sorted unique")
        require(all(ref == prefix or ref.startswith(prefix + "/") for ref in refs), f"{prefix}: entry escaped namespace")
        manifest = "".join(f"{item['ref']} {item['object_id']}\n" for item in entries).encode("ascii")
        require(digest(manifest) == namespace["manifest_sha256"], f"{prefix}: recomputed manifest digest differs")
        advertised_lines.extend(f"{item['object_id']} {item['ref']}\n" for item in entries)
        all_refs.extend(refs)
    require(len(all_refs) == len(set(all_refs)) == 67, "proper local refs are not exactly 67 unique names")
    return "".join(advertised_lines).encode("ascii")


def validate_hosted_branches(ledger: dict[str, Any]) -> None:
    records = ledger["hosted_branches"]
    refs = [item["ref"] for item in records]
    require(refs == sorted(refs), "hosted branch ledger is not sorted by ref")
    tips = {item["ref"]: item["object_id"] for item in records}
    require(tips == EXPECTED_HOSTED_TIPS, "hosted branch set or exact tip drifted")
    semantics = {
        item["ref"]: (item["disposition"], item["reason"])
        for item in records
    }
    require(
        semantics == EXPECTED_HOSTED_SEMANTICS,
        "hosted branch disposition/reason identity drifted",
    )
    manifest = "".join(f"{item['ref']} {item['object_id']}\n" for item in records).encode("ascii")
    require(digest(manifest) == ledger["hosted_branches_manifest_sha256"] == EXPECTED_HOSTED_MANIFEST_SHA256, "hosted branch manifest digest drifted")
    dispositions = Counter(item["disposition"] for item in records)
    require(dispositions == Counter({
        "retain_branch_only_history": 10,
        "conditional_retirement_candidate": 7,
        "retain_pending_adjudication": 5,
        "active_main": 1,
    }), "hosted disposition census drifted")
    require(all(item["deletion_eligible"] is False for item in records), "a hosted branch was marked deletion-eligible")


def validate_custody(ledger: dict[str, Any], advertised_prefix: bytes) -> None:
    custody = ledger["restricted_custody"]
    require(custody["record_id"] == "RCR-20260901-01", "restricted record identity drifted")
    require(custody["locator_in_public_ledger"] is False, "restricted locator disclosure escalated")
    require(custody["deletion_authority"] is False, "bundle was promoted to deletion authority")
    bundle = custody["bundle"]
    require(bundle["sha256"] == EXPECTED_BUNDLE_SHA256 and bundle["bytes"] == 32_474_415, "bundle byte identity drifted")
    require(bundle["advertised_heads"] == 71 and bundle["verification_passed"] is True, "bundle verification facts drifted")
    pseudo = custody["pseudo_heads"]
    require([item["name"] for item in pseudo] == [
        "HEAD",
        "worktrees/pid-rs-m1a-ci-fix/HEAD",
        "worktrees/pid-rs-c4-recovery/HEAD",
        "worktrees/pid-rs-ksg-rev4-candidate/HEAD",
    ], "bundle pseudo-head order or set drifted")
    full_manifest = advertised_prefix + "".join(f"{item['object_id']} {item['name']}\n" for item in pseudo).encode("ascii")
    manifest = custody["advertised_head_manifest"]
    require(digest(full_manifest) == manifest["sha256"] == EXPECTED_ADVERTISED_MANIFEST_SHA256, "advertised-head manifest projection drifted")
    require(len(full_manifest) == manifest["bytes"] == 7_354, "advertised-head manifest byte count drifted")
    drill = custody["recovery_drill"]
    require(drill == {
        "advertised_object_ids_checked": 71,
        "advertised_object_ids_missing": 0,
        "proper_refs_restored": 67,
        "temporary_copy_retained": False,
    }, "recovery-drill result drifted")
    require(67 + len(pseudo) == bundle["advertised_heads"], "proper and pseudo head accounting does not close")


def validate_semantics(ledger: dict[str, Any]) -> None:
    require(ledger["scope"]["scope_kind"] == "single_common_git_directory", "scope expanded beyond one common Git directory")
    require(ledger["scope"]["sibling_and_global_registries"] == "explicitly_excluded_and_not_cleared", "sibling/global exclusion was weakened")
    decision = ledger["global_decision"]
    require(decision["cleanup_authorized"] is False and decision["deletion_eligible_count"] == 0, "cleanup authority escalated")
    require(decision["final_main_candidate_established"] is False, "unfinished documentation candidate was declared final")
    require(decision["sibling_and_global_registries"] == "out_of_scope_and_pending_fresh_audit", "global registry work was declared closed")
    state = ledger["repository_state"]
    require(state["local_main"] == state["hosted_main"] == EXPECTED_HOSTED_TIPS["refs/heads/main"], "observed main identities do not agree")
    require(
        state["primary_head"] == EXPECTED_WORKTREE_STATE["primary-review"]["head"],
        "primary worktree HEAD identity drifted",
    )
    require(state["git_state_markers"] == [] and state["lock_file_markers"] == [], "in-progress Git state was hidden")
    require(state["stash_ref_count"] == 0, "stash accounting drifted")
    require(not state["alternate_index_environment_present"] and not state["alternate_object_directory_environment_present"] and not state["alternates_file_present"], "alternate storage state was hidden")
    started = parse_timestamp(ledger["snapshot"]["started_at_utc"])
    completed = parse_timestamp(ledger["snapshot"]["completed_at_utc"])
    created = parse_timestamp(ledger["restricted_custody"]["created_at_utc"])
    reverified = parse_timestamp(ledger["restricted_custody"]["reverified_at_utc"])
    require(created <= started <= completed <= reverified, "snapshot/custody timestamps are inconsistent")
    validate_worktrees(ledger)
    advertised_prefix = validate_namespaces(ledger)
    validate_hosted_branches(ledger)
    validate_custody(ledger, advertised_prefix)
    check_no_locator_leak(ledger)
    require(tuple(ledger["nonclaims"]) == EXPECTED_NONCLAIMS, "nonclaim identity or order drifted")


def validate_record(ledger_raw: bytes, schema_raw: bytes, *, enforce_exact_bytes: bool = True) -> None:
    if enforce_exact_bytes:
        require(digest(ledger_raw) == EXPECTED_LEDGER_SHA256, "ledger exact-byte identity drifted")
        require(digest(schema_raw) == EXPECTED_SCHEMA_SHA256, "ledger schema exact-byte identity drifted")
    ledger = parse_json(ledger_raw, name="retirement ledger")
    schema = parse_json(schema_raw, name="retirement ledger schema")
    try:
        validate_json_schema(ledger, schema, name="retirement ledger")
    except SchemaValidationError as error:
        raise LedgerError(f"schema validation failed: {error}") from error
    if not isinstance(ledger, dict):
        raise LedgerError("retirement ledger root is not an object")
    validate_semantics(ledger)


def main() -> int:
    try:
        validate_record(read_single_link_regular(LEDGER), read_single_link_regular(SCHEMA))
    except (OSError, LedgerError) as error:
        print(f"retirement ledger error: {error}", file=sys.stderr)
        return 1
    print("OK: primary retirement ledger is exact, scope-bounded, custody-bound, and authorizes no deletion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
