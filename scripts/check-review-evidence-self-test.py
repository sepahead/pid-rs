#!/usr/bin/env python3
"""Mutation tests for the bounded assurance, task-disposition, and file-inventory gate."""

from __future__ import annotations

import copy
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-review-evidence.py"
spec = importlib.util.spec_from_file_location("check_review_evidence", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load review-evidence checker")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

checker.require_release_boundary()
assurance_raw = checker.ASSURANCE_REGISTRY.read_bytes()
tasks_raw = checker.TASK_DISPOSITIONS.read_bytes()
ledger_raw = checker.FILE_REVIEW_LEDGER.read_bytes()
checker.validate_assurance_registry(assurance_raw)
checker.validate_task_dispositions(tasks_raw)
checker.validate_file_review_ledger(ledger_raw)

assurance = json.loads(assurance_raw)
tasks = json.loads(tasks_raw)
mutations_rejected = 0


def record_rejection() -> None:
    global mutations_rejected
    mutations_rejected += 1


def expect_assurance_rejected(label: str, value: object) -> None:
    try:
        checker.validate_assurance_registry(checker.canonical_json_bytes(value))
    except (checker.ReviewEvidenceError, checker.SchemaValidationError):
        record_rejection()
        return
    raise SystemExit(f"{label} assurance mutation unexpectedly passed")


def expect_tasks_rejected(label: str, value: object) -> None:
    try:
        checker.validate_task_dispositions(checker.canonical_json_bytes(value))
    except (checker.ReviewEvidenceError, checker.SchemaValidationError):
        record_rejection()
        return
    raise SystemExit(f"{label} task mutation unexpectedly passed")


def ledger_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=checker.LEDGER_COLUMNS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def expect_ledger_rejected(label: str, rows: list[dict[str, str]]) -> None:
    try:
        checker.validate_file_review_ledger(ledger_bytes(rows))
    except checker.ReviewEvidenceError:
        record_rejection()
        return
    raise SystemExit(f"{label} file-inventory mutation unexpectedly passed")


def assurance_family(value: dict[str, object], family_id: str) -> dict[str, object]:
    families = value["families"]
    if not isinstance(families, list):
        raise SystemExit("assurance family list changed shape")
    matches = [
        family
        for family in families
        if isinstance(family, dict) and family.get("family_id") == family_id
    ]
    if len(matches) != 1:
        raise SystemExit(f"assurance family lookup changed for {family_id!r}")
    return matches[0]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{label}: expected exactly one mutation target, found {count}"
        )
    return text.replace(old, new, 1)


with (
    tempfile.TemporaryDirectory(
        prefix=".review-evidence-tracking-",
        dir=ROOT,
    ) as tracking_directory,
    tempfile.TemporaryDirectory(
        prefix="pid-rs-review-evidence-index-",
    ) as index_directory,
):
    probe = Path(tracking_directory) / "probe.txt"
    probe.write_text("indexed bytes\n", encoding="utf-8")
    relative_probe = probe.relative_to(ROOT).as_posix()
    isolated_index = Path(index_directory) / "index"
    environment = dict(os.environ)
    environment["GIT_INDEX_FILE"] = str(isolated_index)
    subprocess.run(
        ["git", "read-tree", "HEAD"],
        cwd=ROOT,
        env=environment,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    previous_index = os.environ.get("GIT_INDEX_FILE")
    os.environ["GIT_INDEX_FILE"] = str(isolated_index)
    try:
        try:
            checker.safe_repo_file(relative_probe)
        except checker.ReviewEvidenceError as error:
            if "not tracked in the Git index" not in str(error):
                raise SystemExit(
                    f"untracked evidence path failed for the wrong reason: {error}"
                ) from error
            record_rejection()
        else:
            raise SystemExit("untracked evidence path unexpectedly passed")
        subprocess.run(
            ["git", "add", "--force", "--", relative_probe],
            cwd=ROOT,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        checker.safe_repo_file(relative_probe)
        probe.write_text("changed after indexing\n", encoding="utf-8")
        try:
            checker.safe_repo_file(relative_probe)
        except checker.ReviewEvidenceError as error:
            if "bytes differ from the indexed Git blob" not in str(error):
                raise SystemExit(
                    f"dirty evidence path failed for the wrong reason: {error}"
                ) from error
            record_rejection()
        else:
            raise SystemExit("dirty evidence path unexpectedly passed")
    finally:
        if previous_index is None:
            os.environ.pop("GIT_INDEX_FILE", None)
        else:
            os.environ["GIT_INDEX_FILE"] = previous_index


mutation = copy.deepcopy(assurance)
mutation["families"].pop()
expect_assurance_rejected("missing family", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][1] = copy.deepcopy(mutation["families"][0])
expect_assurance_rejected("duplicate family", mutation)

mutation = copy.deepcopy(assurance)
del mutation["families"][0]["layers"]["definition"]
expect_assurance_rejected("missing correctness layer", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][14]["layers"]["exact_algebra"]["assurance"]["status"] = "TESTED"
expect_assurance_rejected("unproved-layer escalation", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][0]["layers"]["definition"]["assumptions"] = []
expect_assurance_rejected("missing assumption", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][0]["layers"]["definition"]["gaps"][0]["disposition"] = (
    "NOT_CLAIMED"
)
expect_assurance_rejected("gap disposition", mutation)

mutation = copy.deepcopy(assurance)
mutation["release_boundary"]["v1_0_qualification_status"] = "GO"
expect_assurance_rejected("qualification escalation", mutation)

mutation = copy.deepcopy(assurance)
mutation["release_boundary"]["final_decision_claimed"] = True
expect_assurance_rejected("final-decision inference", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "at most 8 * f64::EPSILON nats; exactly 40 rows",
    "at most 32 * f64::EPSILON nats; exactly 40 rows",
    "KSG rounded-reference maximum",
)
expect_assurance_rejected("KSG rounded-reference maximum loosening", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "6,920 exhaustive rectangular-arithmetic outer-box rows",
    "6,920 exhaustive runtime-realizable rows",
    "KSG outer-box scope",
)
expect_assurance_rejected("KSG outer-box runtime promotion", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "exactly 40 rows attain that maximum",
    "exactly 41 rows attain that maximum",
    "KSG rounded-reference tie count",
)
expect_assurance_rejected("KSG rounded-reference tie mutation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "Two finite-corpus comparators are intentionally distinct.",
    "The two observations are one interchangeable comparator.",
    "KSG comparator separation",
)
expect_assurance_rejected("KSG comparator conflation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "zero-based row 7,673 with tuple (4,096, 4, 2,049, 2,049)",
    "zero-based row 7,598 with tuple (4,096, 1, 2,048, 2,048)",
    "KSG exact-rational maximum row",
)
expect_assurance_rejected("KSG exact-rational maximum row mutation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "strictly below 9.761311 * f64::EPSILON nats",
    "strictly below 8 * f64::EPSILON nats",
    "KSG exact-rational strict bound",
)
expect_assurance_rejected("KSG eight-versus-exact-bound conflation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "stored prefix text on 6,509 rows",
    "stored prefix text on 5,934 rows",
    "KSG textual mismatch count",
)
expect_assurance_rejected("KSG textual mismatch count mutation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "differs numerically on 5,934 rows",
    "differs numerically on 6,509 rows",
    "KSG numeric mismatch count",
)
expect_assurance_rejected("KSG numeric mismatch count mutation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "all 8,198 binary64 conversions agree",
    "one binary64 conversion differs",
    "KSG binary64 conversion count",
)
expect_assurance_rejected("KSG binary64 conversion mutation", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "rejects 29 of 29 load-bearing mutations in each mode",
    "rejects 28 of 29 load-bearing mutations in each mode",
    "KSG exact-enclosure mutation total",
)
expect_assurance_rejected("KSG exact-enclosure mutation-total weakening", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "rejects 28 of 28 registered faults in normal and -O modes",
    "rejects 26 of 28 registered faults in normal and -O modes",
    "KSG modular-certificate mutation total",
)
expect_assurance_rejected("KSG modular mutation-total weakening", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "passes in normal and -O modes",
    "passes in normal mode only",
    "KSG exact-enclosure optimization coverage",
)
expect_assurance_rejected("KSG optimized exact-enclosure erasure", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "share the digest-bound fixture and row order",
    "share no reviewed cuts",
    "KSG shared-cut statement",
)
expect_assurance_rejected("KSG shared-cut erasure", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "does not inspect Rust source or a compiled binary",
    "proves Rust source and compiled-binary conformance",
    "KSG Rust-conformance boundary",
)
expect_assurance_rejected("KSG Rust-conformance promotion", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_numerical = ksg["layers"]["floating_point_numerical_behavior"]["assurance"]
ksg_numerical["claim"] = replace_once(
    ksg_numerical["claim"],
    "Neither observation is a ULP count, universal or cross-platform bound",
    "Both observations are universal eight-ULP cross-platform bounds",
    "KSG ULP/universal boundary",
)
expect_assurance_rejected("KSG ULP/universal promotion", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg["layers"]["floating_point_numerical_behavior"]["assurance"]["evidence"].remove(
    "scripts/check-ksg-harmonic-exact-enclosure-self-test.py"
)
expect_assurance_rejected("KSG exact-enclosure evidence erasure", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg["layers"]["exact_algebra"]["assurance"]["evidence"].remove(
    "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean"
)
expect_assurance_rejected("KSG formal-evidence erasure", mutation)

mutation = copy.deepcopy(assurance)
ksg_pipeline = assurance_family(
    mutation, "pid-core.experimental.pipelines.pid3-permutation"
)
ksg_pipeline["layers"]["floating_point_numerical_behavior"]["assurance"][
    "evidence"
].remove(
    "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    "ksg-harmonic-modular-certificate-v1.json"
)
expect_assurance_rejected("KSG transitive certificate erasure", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg_exact = ksg["layers"]["exact_algebra"]["assurance"]
ksg_exact["claim"] = ksg_exact["claim"].replace(
    "under the typed positive-integer digamma identity",
    "after proving the positive-integer digamma identity",
)
expect_assurance_rejected("KSG analytic-premise promotion", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
ksg["estimator_revision"] = "strict-unique-shell-report-v3"
expect_assurance_rejected("KSG estimator-revision rollback", mutation)

mutation = copy.deepcopy(assurance)
ksg = assurance_family(mutation, "pid-core.stable.continuous")
for layer in ksg["layers"].values():
    evidence = layer["assurance"]["evidence"]
    evidence[evidence.index("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md")] = (
        "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md"
    )
expect_assurance_rejected("KSG stale active-claim substitution", mutation)

mutation = copy.deepcopy(assurance)
ksg_config = assurance_family(
    mutation, "pid-core.experimental.continuous.shared-ksg-config"
)
ksg_config["estimator_revision"] = "ksg-chebyshev-integer-harmonic-config-v2"
expect_assurance_rejected("KSG configuration over-bump", mutation)

mutation = copy.deepcopy(assurance)
ksg_config = assurance_family(
    mutation, "pid-core.experimental.continuous.shared-ksg-config"
)
ksg_config_claim = ksg_config["layers"]["floating_point_numerical_behavior"][
    "assurance"
]
ksg_config_claim["claim"] = ksg_config_claim["claim"].replace(
    "emits no scientific scalar",
    "emits one scientifically validated scalar",
)
expect_assurance_rejected("KSG configuration scalar promotion", mutation)

mutation = copy.deepcopy(assurance)
ksg_config = assurance_family(
    mutation, "pid-core.experimental.continuous.shared-ksg-config"
)
ksg_config["layers"]["floating_point_numerical_behavior"]["assurance"][
    "evidence"
].remove("scripts/check-ksg-harmonic-revision-self-test.py")
expect_assurance_rejected(
    "KSG configuration negative-control evidence erasure", mutation
)

mutation = copy.deepcopy(assurance)
protected = assurance_family(mutation, "pid-core.infrastructure")
protected["layers"]["rust_refinement"]["assurance"]["claim"] = (
    "changed protected family"
)
expect_assurance_rejected("non-KSG protected-family drift", mutation)

try:
    checker.validate_assurance_registry(
        assurance_raw.replace(
            b'{\n  "families":',
            b'{\n  "schema": "pid-rs/assurance-registry",\n  "families":',
            1,
        )
    )
except checker.ReviewEvidenceError:
    record_rejection()
else:
    raise SystemExit("duplicate assurance JSON key unexpectedly passed")

mutation = copy.deepcopy(tasks)
mutation["tasks"].pop()
expect_tasks_rejected("missing task", mutation)

mutation = copy.deepcopy(tasks)
mutation["tasks"][1] = copy.deepcopy(mutation["tasks"][0])
expect_tasks_rejected("duplicate task", mutation)

mutation = copy.deepcopy(tasks)
mutation["tasks"][0], mutation["tasks"][1] = (
    mutation["tasks"][1],
    mutation["tasks"][0],
)
expect_tasks_rejected("reordered task", mutation)

mutation = copy.deepcopy(tasks)
blocked = next(
    task for task in mutation["tasks"] if task["v1_0_disposition"] == "BLOCKED_EXTERNAL"
)
blocked["v1_0_disposition"] = "OPEN_LOCAL"
expect_tasks_rejected("external blocker removal", mutation)

mutation = copy.deepcopy(tasks)
mutation["summary"]["qualified_complete"] = 1
expect_tasks_rejected("task completion escalation", mutation)

mutation = copy.deepcopy(tasks)
mutation["release_boundary"]["v0_9_source_review_status"] = "QUALIFIED"
expect_tasks_rejected("source-review qualification escalation", mutation)

mutation = copy.deepcopy(tasks)
milestone = next(task for task in mutation["tasks"] if task["task_id"] == "T145")
milestone["implementation_state"] = "NOT_ESTABLISHED_BY_THIS_ARTIFACT"
expect_tasks_rejected("milestone implementation erasure", mutation)

mutation = copy.deepcopy(tasks)
task_156 = next(task for task in mutation["tasks"] if task["task_id"] == "T156")
task_156["v1_0_disposition"] = "CLAIM_REMOVED"
expect_tasks_rejected("cross-repository task closure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = "bounded evidence exists"
expect_tasks_rejected("oracle-scope truncation", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "6,920 exhaustive rectangular-arithmetic outer-box rows",
    "6,920 exhaustive runtime-realizable rows",
    "T138 outer-box scope",
)
expect_tasks_rejected("T138 outer-box runtime promotion", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = task_138["scope_note"].replace(
    "494 nonempty binary SxPID2 count tables",
    "493 nonempty binary SxPID2 count tables",
)
expect_tasks_rejected("T138 protected SxPID2 scope drift", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["evidence"].remove("scripts/generate-sxpid2-exhaustive-oracle.py")
expect_tasks_rejected("T138 protected SxPID2 evidence erasure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["evidence"].remove("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md")
expect_tasks_rejected("T138 active KSG claim erasure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["evidence"].remove(
    "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    "ksg-harmonic-modular-certificate-v1.json"
)
expect_tasks_rejected("T138 modular-certificate erasure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["evidence"].remove("scripts/check-ksg-harmonic-exact-enclosure-self-test.py")
expect_tasks_rejected("T138 exact-enclosure evidence erasure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "strictly below 9.761311 * f64::EPSILON nats",
    "strictly below 8 * f64::EPSILON nats",
    "T138 exact-rational strict bound",
)
expect_tasks_rejected("T138 eight-versus-exact-bound conflation", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "rejects 29 of 29 load-bearing mutations in each mode",
    "rejects 28 of 29 load-bearing mutations in each mode",
    "T138 exact-enclosure mutation total",
)
expect_tasks_rejected("T138 exact-enclosure mutation-total weakening", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "rejects 28 registered faults",
    "rejects 26 registered faults",
    "T138 modular-certificate mutation total",
)
expect_tasks_rejected("T138 modular mutation-total weakening", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "without an asserted final mutation total",
    "with a final total of 100 mutations",
    "T138 main-checker mutation-total boundary",
)
expect_tasks_rejected("T138 invented main-checker mutation total", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = replace_once(
    task_138["scope_note"],
    "Repository/publication integration remains NO-GO",
    "Repository/publication integration is GO",
    "T138 integration disposition",
)
expect_tasks_rejected("T138 integration promotion", mutation)

mutation = copy.deepcopy(tasks)
protected_task = next(task for task in mutation["tasks"] if task["task_id"] == "T137")
protected_task["scope_note"] = "changed protected task"
expect_tasks_rejected("non-T138 protected-task drift", mutation)

original_ksg_evidence = checker.KSG_INTEGER_HARMONIC_EVIDENCE
original_ksg_evidence_sha256 = checker.EXPECTED_KSG_EVIDENCE_SHA256
inventory_mutations = (
    ("unreviewed extension", "README.md", False),
    (
        "hash-rebased out-of-scope extension",
        "claims/UNRELATED-LATER-WAVE/claim.md",
        True,
    ),
    (
        "hash-rebased same-count substitution",
        "claims/UNRELATED-LATER-WAVE/claim.md",
        True,
    ),
)
try:
    for index, (label, path, rebase_hash) in enumerate(inventory_mutations):
        checker.KSG_INTEGER_HARMONIC_EVIDENCE = (
            original_ksg_evidence + (path,)
            if index < 2
            else original_ksg_evidence[:-1] + (path,)
        )
        checker.EXPECTED_KSG_EVIDENCE_SHA256 = (
            checker.semantic_sha256(list(checker.KSG_INTEGER_HARMONIC_EVIDENCE))
            if rebase_hash
            else original_ksg_evidence_sha256
        )
        try:
            checker.validate_ksg_evidence_inventory()
        except checker.ReviewEvidenceError:
            record_rejection()
        else:
            raise SystemExit(f"{label} unexpectedly passed")
finally:
    checker.KSG_INTEGER_HARMONIC_EVIDENCE = original_ksg_evidence
    checker.EXPECTED_KSG_EVIDENCE_SHA256 = original_ksg_evidence_sha256

original_handoff_commit = checker.HANDOFF_LEDGER_DECLARED_COMMIT
checker.HANDOFF_LEDGER_DECLARED_COMMIT = checker.TAGGED_COMMIT
try:
    checker.require_release_boundary()
except checker.ReviewEvidenceError:
    record_rejection()
else:
    raise SystemExit("ancestor handoff-commit mutation unexpectedly passed")
finally:
    checker.HANDOFF_LEDGER_DECLARED_COMMIT = original_handoff_commit

intake = json.loads(checker.HANDOFF_INTAKE.read_bytes())
original_intake_path = checker.HANDOFF_INTAKE
with tempfile.TemporaryDirectory(prefix="pid-rs-review-evidence-") as directory:
    mutation = copy.deepcopy(intake)
    mutation["pid_ledger"]["sha256"] = "0" * 64
    checker.HANDOFF_INTAKE = Path(directory) / "handoff-intake.json"
    checker.HANDOFF_INTAKE.write_bytes(checker.canonical_json_bytes(mutation))
    try:
        checker.load_handoff_intake()
    except checker.ReviewEvidenceError:
        record_rejection()
    else:
        raise SystemExit("handoff ledger identity mutation unexpectedly passed")
checker.HANDOFF_INTAKE = original_intake_path

reader = csv.DictReader(io.StringIO(ledger_raw.decode("utf-8"), newline=""))
baseline_rows = list(reader)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["sha256"] = "0" * 64
expect_ledger_rejected("blob digest", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows[:-1])
expect_ledger_rejected("missing tagged file", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["reviewer"] = "named person"
expect_ledger_rejected("reviewer inference", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["review_status"] = "REVIEWED"
expect_ledger_rejected("review completion inference", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["completed_at"] = "2026-07-14"
expect_ledger_rejected("completion timestamp", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["generated"] = "true"
mutation_rows[0]["generator"] = "not applicable"
expect_ledger_rejected("missing generator", mutation_rows)

expected_mutations = 68
if mutations_rejected != expected_mutations:
    raise SystemExit(
        "review-evidence mutation inventory changed: "
        f"{mutations_rejected} != {expected_mutations}"
    )
print(
    f"OK: {mutations_rejected} family/layer, KSG-boundary, task/status, "
    "tag-inventory, digest, generator, review-claim, and index-binding mutations "
    "were rejected"
)
