#!/usr/bin/env python3
"""Hostile mutation suite for the two-defect composite-v8 checker."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v8-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v8.py"
checker_raw = CHECKER.read_bytes()
CHECKER_SHA256 = hashlib.sha256(checker_raw).hexdigest()
CHECKER_SIZE_BYTES = len(checker_raw)


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(2)


specification = importlib.util.spec_from_file_location(
    "pid_rs_composite_v8_checker_self_test", CHECKER
)
bootstrap_require(
    specification is not None and specification.loader is not None,
    "cannot load composite-v8 checker",
)
C8 = importlib.util.module_from_spec(specification)
sys.modules[specification.name] = C8
try:
    specification.loader.exec_module(C8)
except Exception:
    print("ERROR: cannot load composite-v8 checker", file=sys.stderr)
    raise SystemExit(2) from None


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise C8.ContractError(message)


def expect_rejection(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except (C8.ContractError, OSError, SyntaxError, UnicodeError):
        return
    raise C8.ContractError(f"hostile mutation was accepted: {label}")


def replace_once(raw: bytes, before: bytes, after: bytes, label: str) -> bytes:
    require(raw.count(before) == 1, f"self-test fixture is not unique: {label}")
    return raw.replace(before, after, 1)


def semantic_workflow_validation(ci: bytes, retired: bytes, successor: bytes) -> None:
    names = (
        "CI_SHA256",
        "CI_SIZE_BYTES",
        "RETIRED_V7_WORKFLOW_SHA256",
        "RETIRED_V7_WORKFLOW_SIZE_BYTES",
        "V8_WORKFLOW_SHA256",
        "V8_WORKFLOW_SIZE_BYTES",
    )
    original = tuple(getattr(C8, name) for name in names)
    values = (
        C8.sha256(ci),
        len(ci),
        C8.sha256(retired),
        len(retired),
        C8.sha256(successor),
        len(successor),
    )
    try:
        for name, value in zip(names, values, strict=True):
            setattr(C8, name, value)
        C8.validate_workflow_bytes(ci, retired, successor)
    finally:
        for name, value in zip(names, original, strict=True):
            setattr(C8, name, value)


def workflow_hostiles() -> int:
    ci = (ROOT / C8.CI_RELATIVE).read_bytes()
    retired = (ROOT / C8.RETIRED_V7_WORKFLOW_RELATIVE).read_bytes()
    successor = (ROOT / C8.V8_WORKFLOW_RELATIVE).read_bytes()
    semantic_workflow_validation(ci, retired, successor)
    mutations: list[tuple[str, bytes, bytes, bytes]] = []

    def add_ci(label: str, before: bytes, after: bytes) -> None:
        mutations.append((label, replace_once(ci, before, after, label), retired, successor))

    def add_retired(label: str, before: bytes, after: bytes) -> None:
        mutations.append((label, ci, replace_once(retired, before, after, label), successor))

    def add_successor(label: str, before: bytes, after: bytes) -> None:
        mutations.append((label, ci, retired, replace_once(successor, before, after, label)))

    add_ci(
        "CI normal pin checker omitted",
        b"python3 -I -S -B scripts/check-github-action-pins.py",
        b"true # omitted normal action-pin checker",
    )
    add_ci(
        "CI formal PDF mode weakened",
        b"scripts/check-formal-pdf-set.sh --cross-toolchain",
        b"scripts/check-formal-pdf-set.sh --exact",
    )
    upload_good = b"actions/upload-artifact@" + C8.GOOD_UPLOAD_PIN.encode("ascii")
    require(ci.count(upload_good) == 3, "CI upload-pin fixture count changed")
    mutations.append(
        (
            "CI upload pin truncated",
            ci.replace(
                upload_good,
                b"actions/upload-artifact@" + C8.BAD_UPLOAD_PIN.encode("ascii"),
                1,
            ),
            retired,
            successor,
        )
    )
    add_retired(
        "retired v7 CI log binding removed",
        C8.C7_CI_RAW_LOG_SHA256.encode("ascii"),
        b"0" * 64,
    )
    add_retired(
        "retired v7 CI comparator marker removed",
        C8.CI_RAW_LOG_ERROR,
        b"workflow PDF comparator marker omitted",
    )
    add_retired(
        "retired v7 artifact absence removed",
        b"it retained no generated workflow PDF, extracted text, or text diff",
        b"artifact retention unknown",
    )
    add_successor(
        "successor refusal renamed",
        b"Refuse retries and non-main qualification events",
        b"Continue retries and non-main qualification events",
    )
    add_successor(
        "successor luaotfload stage omitted",
        b'/usr/bin/install -m 0755 "$luaotfload_source" "$formal_tool_stage"',
        b"true # omitted luaotfload staging",
    )
    add_successor(
        "successor PDF self-test omitted",
        b"bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh",
        b"true # omitted workflow PDF self-test",
    )
    add_successor(
        "successor PDF cross mode changed",
        b"scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
        b"scripts/check-mathematical-workflow-pdf.sh --exact",
    )
    add_successor(
        "successor optimized action-pin self-test omitted",
        b"python3 -O -I -S -B scripts/check-github-action-pins-self-test.py",
        b"true # omitted optimized action-pin self-test",
    )
    add_successor(
        "successor upload pin truncated",
        b"actions/upload-artifact@" + C8.GOOD_UPLOAD_PIN.encode("ascii"),
        b"actions/upload-artifact@" + C8.BAD_UPLOAD_PIN.encode("ascii"),
    )
    for label, hostile_ci, hostile_retired, hostile_successor in mutations:
        expect_rejection(
            lambda a=hostile_ci, b=hostile_retired, c=hostile_successor: semantic_workflow_validation(
                a, b, c
            ),
            label,
        )
    return len(mutations)


def justfile_hostiles() -> int:
    raw = (ROOT / C8.JUSTFILE_RELATIVE).read_bytes()
    C8.validate_justfile_bytes(raw)
    block = C8.recipe_block(raw, b"ksg-composite-v8")
    mutations = (
        (
            "local workflow PDF self-test omitted",
            b"bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh",
            b"true # omitted local workflow PDF self-test",
        ),
        (
            "local workflow PDF mode changed",
            b"scripts/check-mathematical-workflow-pdf.sh --exact",
            b"scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
        ),
        (
            "local closure self-test omitted",
            b"python3 -I -S -B scripts/capture-ksg-m1a-composite-v8-local-closure.py --self-test",
            b"true # omitted local closure self-test",
        ),
        (
            "optimized pin checker omitted",
            b"python3 -O -I -S -B scripts/check-github-action-pins.py",
            b"true # omitted optimized pin checker",
        ),
    )
    for label, before, after in mutations:
        hostile_block = replace_once(block, before, after, label)
        hostile = replace_once(raw, block, hostile_block, f"{label} recipe splice")
        expect_rejection(lambda hostile=hostile: C8.validate_justfile_bytes(hostile), label)
    release_hostile = replace_once(
        raw,
        b" ksg-composite-v8 ",
        b" ksg-composite-v7 ",
        "release audit selects v7",
    )
    expect_rejection(
        lambda: C8.validate_justfile_bytes(release_hostile),
        "release audit selects v7",
    )
    return len(mutations) + 1


def capture_ast_hostiles() -> int:
    hosted = (ROOT / C8.CAPTURE_TOOL_RELATIVE).read_bytes()
    local = (ROOT / C8.LOCAL_TOOL_RELATIVE).read_bytes()
    C8.validate_capture_source_routes(hosted, local)
    mutations: list[tuple[str, bytes, bytes]] = []

    def hosted_mutation(label: str, before: bytes, after: bytes, suffix: bytes = b"") -> None:
        mutations.append((label, replace_once(hosted, before, after, label) + suffix, local))

    def local_mutation(label: str, before: bytes, after: bytes, suffix: bytes = b"") -> None:
        mutations.append((label, hosted, replace_once(local, before, after, label) + suffix))

    hosted_mutation(
        "hosted workflow rebind redirected behind dead string",
        b"V7.V6.workflow_identity = workflow_identity",
        b"REDIRECT.workflow_identity = workflow_identity",
        b'\nDEAD_WORKFLOW_REBIND = "V7.V6.workflow_identity = workflow_identity"\n',
    )
    hosted_mutation(
        "hosted extra primitive rebind",
        b"V7.V6.expected_successor_artifact_names = expected_successor_artifact_names",
        b"V7.V6.expected_successor_artifact_names = expected_successor_artifact_names\nV7.V6.read_token = workflow_identity",
    )
    hosted_mutation(
        "hosted run call redirected behind dead string",
        b"V7.V6.capture_run(\n",
        b"REDIRECT.capture_run(\n",
        b'\nDEAD_CAPTURE_RUN = "V7.V6.capture_run("\n',
    )
    hosted_mutation(
        "hosted operational artifact call redirected",
        b"                V7.V6.capture_artifacts(\n",
        b"                REDIRECT.capture_artifacts(\n",
    )
    hosted_mutation(
        "hosted failed-log call redirected",
        b"                    V7.V6.capture_failed_logs(\n",
        b"                    REDIRECT.capture_failed_logs(\n",
    )
    hosted_mutation(
        "hosted CodeQL call redirected",
        b"                    V7.V6.capture_codeql(\n",
        b"                    REDIRECT.capture_codeql(\n",
    )
    local_mutation(
        "local primitive assignment redirected behind dead string",
        b"PRIMITIVES = V7.V6\n",
        b"PRIMITIVES = REDIRECT.V6\n",
        b'\nDEAD_PRIMITIVE_BINDING = "PRIMITIVES = V7.V6"\n',
    )
    local_mutation(
        "local subject rebind changed",
        b"PRIMITIVES.C6_MESSAGE = C8_MESSAGE",
        b"PRIMITIVES.C6_MESSAGE = C7_COMMIT",
    )
    local_mutation(
        "local extra top-level primitive rebind",
        b"PRIMITIVES.C5_COMMIT = C7_COMMIT",
        b"PRIMITIVES.C5_COMMIT = C7_COMMIT\nPRIMITIVES.read_regular = byte_binding",
    )
    local_mutation(
        "local bounded runner redirected",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n                COMMAND_ARGV,",
        b"            code, stdout, stderr, timed_out = REDIRECT.run_bounded(\n                COMMAND_ARGV,",
    )
    local_mutation(
        "local fixed-umask entry redirected",
        b"            PRIMITIVES.under_fixed_umask(lambda: capture_under_fixed_umask(arguments.output))",
        b"            REDIRECT.under_fixed_umask(lambda: capture_under_fixed_umask(arguments.output))",
    )
    for label, hostile_hosted, hostile_local in mutations:
        expect_rejection(
            lambda a=hostile_hosted, b=hostile_local: C8.validate_capture_source_routes(a, b),
            label,
        )
    return len(mutations)


def schema_hostiles() -> int:
    values: dict[str, dict[str, Any]] = {}
    for relative in (
        C8.CAPTURE_SCHEMA_RELATIVE,
        C8.LOCAL_SCHEMA_RELATIVE,
        C8.RECEIPT_SCHEMA_RELATIVE,
    ):
        raw = (ROOT / relative).read_bytes()
        values[relative] = C8.validate_schema_bytes(raw, relative)
    mutations: list[tuple[str, str, dict[str, Any]]] = []
    hosted = copy.deepcopy(values[C8.CAPTURE_SCHEMA_RELATIVE])
    hosted["type"] = "object"
    mutations.append(("hosted root type bypass", C8.CAPTURE_SCHEMA_RELATIVE, hosted))
    hosted = copy.deepcopy(values[C8.CAPTURE_SCHEMA_RELATIVE])
    hosted["$defs"]["predecessorDocument"]["additionalProperties"] = True
    mutations.append(("hosted predecessor root opened", C8.CAPTURE_SCHEMA_RELATIVE, hosted))
    local = copy.deepcopy(values[C8.LOCAL_SCHEMA_RELATIVE])
    local["additionalProperties"] = True
    mutations.append(("local root opened", C8.LOCAL_SCHEMA_RELATIVE, local))
    receipt = copy.deepcopy(values[C8.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defects"]["items"] = {}
    mutations.append(("receipt defect tail opened", C8.RECEIPT_SCHEMA_RELATIVE, receipt))
    receipt = copy.deepcopy(values[C8.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defects"]["prefixItems"].reverse()
    mutations.append(("receipt defect order reversed", C8.RECEIPT_SCHEMA_RELATIVE, receipt))
    receipt = copy.deepcopy(values[C8.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defect"] = receipt["properties"].pop("defects")
    receipt["required"][receipt["required"].index("defects")] = "defect"
    receipt["required"].sort()
    mutations.append(("receipt singular defect restored", C8.RECEIPT_SCHEMA_RELATIVE, receipt))
    for label, relative, hostile in mutations:
        raw = C8.canonical_json(hostile, pretty=True)
        expect_rejection(
            lambda raw=raw, relative=relative: C8.validate_schema_bytes(raw, relative),
            label,
        )
    return len(mutations)


def policy_hostiles() -> int:
    raw = (ROOT / C8.POLICY_RELATIVE).read_bytes()
    value = C8.parse_json(raw, "composite-v8 self-test policy")
    C8.validate_policy_value(value)
    mutations: list[tuple[str, dict[str, Any]]] = []
    hostile = copy.deepcopy(value)
    hostile["c7_disposition"]["repository_ci_attempt_1"]["conclusion"] = "success"
    mutations.append(("C7 CI failure erased", hostile))
    hostile = copy.deepcopy(value)
    hostile["c7_disposition"]["extra_defect"] = "unsupported"
    mutations.append(("C7 disposition extra field", hostile))
    hostile = copy.deepcopy(value)
    hostile["base"]["r6_status"] = "issued"
    mutations.append(("R6 resurrected", hostile))
    hostile = copy.deepcopy(value)
    hostile["publication"]["c8_new_pdf"] = "created"
    mutations.append(("C8 PDF invented", hostile))
    hostile = copy.deepcopy(value)
    hostile["nonimplications"].pop()
    mutations.append(("policy nonimplication omitted", hostile))
    hostile = copy.deepcopy(value)
    hostile["c8"]["delta"] = [
        item
        for item in hostile["c8"]["delta"]
        if item["path"] != C8.WORKFLOW_PDF_GATE_RELATIVE
    ]
    mutations.append(("workflow PDF authority omitted", hostile))
    for label, candidate in mutations:
        expect_rejection(lambda candidate=candidate: C8.validate_policy_value(candidate), label)
    return len(mutations)


def lean_cut_hostiles() -> int:
    lean_raw = (ROOT / C8.LEAN_CHECKER_RELATIVE).read_bytes()
    projection_placeholder = b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    scalar_placeholder = b'EXPECTED_COMPOSITE_V8_CHECKER_OPERATIONAL_SHA256 = "0" * 64'
    operational_placeholder = b'    "scripts/check-ksg-m1a-composite-v8.py": "0" * 64,'
    if projection_placeholder in lean_raw:
        scalar_prefix = b"EXPECTED_COMPOSITE_V8_CHECKER_OPERATIONAL_SHA256 = "
        operational_prefix = b'    "scripts/check-ksg-m1a-composite-v8.py": '
        require(lean_raw.count(projection_placeholder) == 1, "Lean projection fixture changed")
        if scalar_placeholder in lean_raw or operational_placeholder in lean_raw:
            require(
                lean_raw.count(scalar_prefix) == 1
                and lean_raw.count(operational_prefix) == 1
                and lean_raw.count(scalar_placeholder) == 1
                and lean_raw.count(operational_placeholder) == 1,
                "Lean all-placeholder cut fixture changed",
            )
            normalized = lean_raw
        else:
            live_checker_digest = CHECKER_SHA256.encode("ascii")
            live_scalar = (
                scalar_prefix + b'"' + live_checker_digest + b'"'
            )
            live_operational = (
                operational_prefix + b'"' + live_checker_digest + b'",'
            )
            require(
                lean_raw.count(scalar_prefix) == 1
                and lean_raw.count(operational_prefix) == 1
                and lean_raw.count(live_scalar) == 1
                and lean_raw.count(live_operational) == 1,
                "Lean pre-r13 finalized checker cuts changed",
            )
            normalized = replace_once(
                lean_raw,
                live_scalar,
                scalar_placeholder,
                "pre-r13 Lean scalar normalization",
            )
            normalized = replace_once(
                normalized,
                live_operational,
                operational_placeholder,
                "pre-r13 Lean operational normalization",
            )
    else:
        _projection, _scalar, _operational, normalized = C8.lean_r13_source_cuts(
            lean_raw
        )
    normalized_digest = C8.sha256(normalized)
    synthetic_checker = (
        b'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "'
        + normalized_digest.encode("ascii")
        + b'"\n'
    )
    checker_digest = C8.sha256(synthetic_checker)
    projection = "1" * 64
    scalar_final = (
        b'EXPECTED_COMPOSITE_V8_CHECKER_OPERATIONAL_SHA256 = "'
        + checker_digest.encode("ascii")
        + b'"'
    )
    operational_final = (
        b'    "scripts/check-ksg-m1a-composite-v8.py": "'
        + checker_digest.encode("ascii")
        + b'",'
    )
    final_lean = replace_once(
        normalized,
        projection_placeholder,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + projection.encode("ascii") + b'"',
        "synthetic Lean projection cut",
    )
    final_lean = replace_once(
        final_lean,
        scalar_placeholder,
        scalar_final,
        "synthetic Lean scalar cut",
    )
    final_lean = replace_once(
        final_lean,
        operational_placeholder,
        operational_final,
        "synthetic Lean operational cut",
    )
    require(
        C8.validate_lean_r13_checksum_cut(synthetic_checker, final_lean) == projection,
        "positive Lean checksum cut changed",
    )

    mutations = (
        (
            "Lean scalar mismatch",
            synthetic_checker,
            replace_once(
                final_lean,
                scalar_final,
                b'EXPECTED_COMPOSITE_V8_CHECKER_OPERATIONAL_SHA256 = "'
                + b"2" * 64
                + b'"',
                "Lean scalar mismatch fixture",
            ),
        ),
        (
            "Lean operational mismatch",
            synthetic_checker,
            replace_once(
                final_lean,
                operational_final,
                b'    "scripts/check-ksg-m1a-composite-v8.py": "'
                + b"3" * 64
                + b'",',
                "Lean operational mismatch fixture",
            ),
        ),
        (
            "normalized Lean digest mismatch",
            b'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "' + b"4" * 64 + b'"\n',
            final_lean,
        ),
        (
            "Lean projection cut duplicated",
            synthetic_checker,
            final_lean
            + b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
            + projection.encode("ascii")
            + b'"\n',
        ),
        (
            "normalized Lean binding duplicated",
            synthetic_checker
            + b'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "'
            + normalized_digest.encode("ascii")
            + b'"\n',
            final_lean,
        ),
        (
            "Lean scalar cut missing",
            synthetic_checker,
            replace_once(
                final_lean,
                scalar_final,
                b"# synthetic scalar cut removed",
                "Lean scalar missing fixture",
            ),
        ),
        (
            "Lean scalar cut duplicated",
            synthetic_checker,
            final_lean + scalar_final + b"\n",
        ),
        (
            "Lean projection cut left placeholder",
            synthetic_checker,
            replace_once(
                final_lean,
                b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
                + projection.encode("ascii")
                + b'"',
                projection_placeholder,
                "Lean projection placeholder fixture",
            ),
        ),
    )
    for label, hostile_checker, hostile_lean in mutations:
        expect_rejection(
            lambda a=hostile_checker, b=hostile_lean: C8.validate_lean_r13_checksum_cut(a, b),
            label,
        )

    lean_self_test = (ROOT / C8.LEAN_SELF_TEST_RELATIVE).read_bytes()
    replay_lean = replace_once(
        final_lean,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + projection.encode("ascii") + b'"',
        projection_placeholder,
        "synthetic Lean replay reconstruction",
    )
    r12 = {"checker_sha256": {"scientific": "retained"}}
    r13 = {
        "checker_sha256": dict(r12["checker_sha256"]),
        "custody_gate_sha256": {
            C8.LEAN_SELF_TEST_RELATIVE: C8.sha256(lean_self_test),
            C8.LEAN_CHECKER_RELATIVE: C8.sha256(final_lean),
        },
        "operational_wiring_sha256": {C8.CHECKER_RELATIVE: checker_digest},
        "replay_custody_gate_sha256": {
            C8.LEAN_SELF_TEST_RELATIVE: C8.sha256(lean_self_test),
            C8.LEAN_CHECKER_RELATIVE: C8.sha256(replay_lean),
        },
    }
    receipt_projection = C8.lean_replay_projection_sha256(r13)
    receipt_lean = replace_once(
        final_lean,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + projection.encode("ascii") + b'"',
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + receipt_projection.encode("ascii")
        + b'"',
        "synthetic final receipt projection",
    )
    r13["custody_gate_sha256"][C8.LEAN_CHECKER_RELATIVE] = C8.sha256(receipt_lean)
    C8.validate_lean_r13_receipt_cuts(
        synthetic_checker,
        receipt_lean,
        lean_self_test,
        r12,
        r13,
        receipt_projection,
    )
    receipt_mutations: list[tuple[str, dict[str, Any], str]] = []
    hostile = copy.deepcopy(r13)
    hostile["checker_sha256"] = {"scientific": "changed"}
    receipt_mutations.append(("r13 scientific inventory drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["operational_wiring_sha256"][C8.CHECKER_RELATIVE] = "5" * 64
    receipt_mutations.append(("r13 operational checker drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    del hostile["operational_wiring_sha256"][C8.CHECKER_RELATIVE]
    receipt_mutations.append(("r13 operational checker missing", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["custody_gate_sha256"][C8.LEAN_CHECKER_RELATIVE] = "6" * 64
    receipt_mutations.append(("r13 final custody drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["replay_custody_gate_sha256"][C8.LEAN_CHECKER_RELATIVE] = "7" * 64
    receipt_mutations.append(("r13 replay custody drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["custody_gate_sha256"]["scripts/unreviewed-custody.py"] = "9" * 64
    receipt_mutations.append(("r13 custody extra path", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    del hostile["custody_gate_sha256"][C8.LEAN_CHECKER_RELATIVE]
    receipt_mutations.append(("r13 custody missing path", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["operational_wiring_sha256"][C8.LEAN_CHECKER_RELATIVE] = C8.sha256(
        receipt_lean
    )
    receipt_mutations.append(("r13 custody leaked into operational map", hostile, receipt_projection))
    hostile = copy.deepcopy(r13)
    hostile["replay_custody_gate_sha256"][C8.LEAN_SELF_TEST_RELATIVE] = "a" * 64
    receipt_mutations.append(("r13 replay self-test custody drift", hostile, receipt_projection))
    receipt_mutations.append(("r13 projection mismatch", copy.deepcopy(r13), "8" * 64))
    for label, hostile, hostile_projection in receipt_mutations:
        expect_rejection(
            lambda value=hostile, cut=hostile_projection: C8.validate_lean_r13_receipt_cuts(
                synthetic_checker,
                receipt_lean,
                lean_self_test,
                r12,
                value,
                cut,
            ),
            label,
        )
    return len(mutations) + len(receipt_mutations)


def replay_route_hostiles() -> int:
    raw = checker_raw
    C8.validate_fresh_replay_source_routes(raw)
    mutations = (
        (
            "r13 checksum call redirected",
            b"    projection = validate_lean_r13_checksum_cut(v8_checker_raw, lean_checker_raw)\n    validate_lean_r13_receipt_cuts(",
            b"    projection = REDIRECT.validate_lean_r13_checksum_cut(v8_checker_raw, lean_checker_raw)\n    validate_lean_r13_receipt_cuts(",
        ),
        (
            "r13 receipt call redirected",
            b"    projection = validate_lean_r13_checksum_cut(v8_checker_raw, lean_checker_raw)\n    validate_lean_r13_receipt_cuts(\n        v8_checker_raw,",
            b"    projection = validate_lean_r13_checksum_cut(v8_checker_raw, lean_checker_raw)\n    REDIRECT.validate_lean_r13_receipt_cuts(\n        v8_checker_raw,",
        ),
        (
            "r13 generator excluded from operational custody",
            b"        LEAN_SELF_TEST_RELATIVE,\n    }\n    operational_c8_paths",
            b'        LEAN_SELF_TEST_RELATIVE,\n        "scripts/generate-lean-4.33-replay.py",\n    }\n    operational_c8_paths',
        ),
        (
            "r13 source-route validator omitted",
            b"    validate_fresh_replay_source_routes(tree_blob(c8_entries, CHECKER_RELATIVE))\n    schemas = schemas_from_tree(c8_entries)",
            b"    pass  # omitted r13 source-route validator\n    schemas = schemas_from_tree(c8_entries)",
        ),
        (
            "r13 operational validator redirected",
            b"    publication_binding(c7_entries, c8_entries)\n    validate_fresh_replay(c7_entries, c8_entries)",
            b"    publication_binding(c7_entries, c8_entries)\n    REDIRECT.validate_fresh_replay(c7_entries, c8_entries)",
        ),
        (
            "r13 operational comparison loop omitted",
            b"    for path in operational_c8_paths:\n        require(\n            operational.get(path) == sha256(tree_blob(c8_entries, path)),\n            f\"r13 does not bind exact C8 operational source: {path}\",\n        )\n    active_claims",
            b"    pass  # omitted r13 operational-source comparison\n    active_claims",
        ),
    )
    for label, before, after in mutations:
        hostile = replace_once(raw, before, after, label)
        expect_rejection(
            lambda hostile=hostile: C8.validate_fresh_replay_source_routes(hostile),
            label,
        )
    return len(mutations)


def main() -> int:
    try:
        groups = {
            "capture_ast_hostiles_rejected": capture_ast_hostiles(),
            "justfile_hostiles_rejected": justfile_hostiles(),
            "lean_cut_hostiles_rejected": lean_cut_hostiles(),
            "policy_hostiles_rejected": policy_hostiles(),
            "replay_route_hostiles_rejected": replay_route_hostiles(),
            "schema_hostiles_rejected": schema_hostiles(),
            "workflow_hostiles_rejected": workflow_hostiles(),
        }
        require(groups == {
            "capture_ast_hostiles_rejected": 11,
            "justfile_hostiles_rejected": 5,
            "lean_cut_hostiles_rejected": 18,
            "policy_hostiles_rejected": 6,
            "replay_route_hostiles_rejected": 6,
            "schema_hostiles_rejected": 6,
            "workflow_hostiles_rejected": 12,
        }, "composite-v8 hostile family counts changed")
        result = {
            "checker": {
                "path": "scripts/check-ksg-m1a-composite-v8.py",
                "sha256": CHECKER_SHA256,
                "size_bytes": CHECKER_SIZE_BYTES,
            },
            **groups,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v8-self-test/v1",
            "total_hostiles_rejected": sum(groups.values()),
        }
        sys.stdout.buffer.write(C8.canonical_json(result, pretty=False))
        return 0
    except (C8.ContractError, OSError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
