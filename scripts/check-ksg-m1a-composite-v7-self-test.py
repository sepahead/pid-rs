#!/usr/bin/env python3
"""Hostile mutation suite for the append-only composite-v7 checker."""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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
        "ERROR: check-ksg-m1a-composite-v7-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v7.py"
specification = importlib.util.spec_from_file_location("pid_rs_composite_v7_checker_self_test", CHECKER)
if specification is None or specification.loader is None:
    print("ERROR: cannot load composite-v7 checker", file=sys.stderr)
    raise SystemExit(2)
V7 = importlib.util.module_from_spec(specification)
sys.modules[specification.name] = V7
try:
    specification.loader.exec_module(V7)
except Exception:
    print("ERROR: cannot load composite-v7 checker", file=sys.stderr)
    raise SystemExit(2) from None


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise V7.ContractError(message)


def expect_rejection(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except (V7.ContractError, OSError, SyntaxError, UnicodeError):
        return
    raise V7.ContractError(f"hostile mutation was accepted: {label}")


def replace_once(raw: bytes, before: bytes, after: bytes, label: str) -> bytes:
    require(raw.count(before) == 1, f"self-test fixture is not unique: {label}")
    return raw.replace(before, after, 1)


def workflow_hostiles() -> int:
    ci = (ROOT / V7.CI_RELATIVE).read_bytes()
    successor = (ROOT / V7.V7_WORKFLOW_RELATIVE).read_bytes()
    retired = (ROOT / V7.V6_WORKFLOW_RELATIVE).read_bytes()
    V7.validate_rg_dependency(ci, "ci")
    V7.validate_rg_dependency(successor, "v7")
    V7.validate_workflows(ci, successor, retired)
    rejected = 0
    ripgrep = b"            ripgrep \\\n"
    for label, raw, lane in (
        ("CI", ci, "ci"),
        ("v7", successor, "v7"),
    ):
        for mutation_label, candidate in (
            ("deleted", replace_once(raw, ripgrep, b"", f"{label} deleted ripgrep")),
            (
                "commented",
                replace_once(raw, ripgrep, b"            # ripgrep \\\n", f"{label} commented ripgrep"),
            ),
            (
                "moved",
                replace_once(raw, ripgrep, b"", f"{label} moved ripgrep") + ripgrep,
            ),
        ):
            expect_rejection(
                lambda candidate=candidate, lane=lane: V7.validate_rg_dependency(candidate, lane),
                f"{label} {mutation_label} ripgrep",
            )
            rejected += 1

    probe_mutations = (
        (
            "CI runtime probe removed",
            replace_once(ci, V7.RG_PROBE, b"", "CI runtime probe"),
            "ci",
        ),
        (
            "v7 runtime probe removed",
            successor.replace(V7.RG_PROBE, b"", 1),
            "v7",
        ),
        (
            "CI executable equality bypassed",
            replace_once(
                ci,
                b'test "$(command -v rg)" = "/usr/bin/rg"',
                b"command -v rg >/dev/null",
                "CI command-v equality",
            ),
            "ci",
        ),
        (
            "v7 executable version bypassed",
            successor.replace(
                b"/usr/bin/rg --version >/dev/null",
                b"rg --version >/dev/null",
                1,
            ),
            "v7",
        ),
        (
            "CI PDF gate omitted",
            replace_once(
                ci,
                b"bash --noprofile --norc scripts/check-formal-pdf-set.sh --cross-toolchain",
                b"true # omitted formal PDF gate",
                "CI formal PDF gate",
            ),
            "ci",
        ),
    )
    for label, candidate, lane in probe_mutations:
        expect_rejection(lambda candidate=candidate, lane=lane: V7.validate_rg_dependency(candidate, lane), label)
        rejected += 1

    gate_line = b"          scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --cross-toolchain\n"
    bypassed = replace_once(
        successor,
        V7.RG_PROBE + gate_line,
        gate_line + V7.RG_PROBE,
        "v7 gate-before-probe",
    )
    expect_rejection(lambda: V7.validate_rg_dependency(bypassed, "v7"), "v7 gate before probe")
    rejected += 1
    moved = replace_once(successor, gate_line, b"", "v7 moved gate")
    first_step = b"      - name: Recheck retained C6 operational surfaces\n"
    moved = replace_once(moved, first_step, first_step + gate_line, "v7 unprobed gate destination")
    expect_rejection(lambda: V7.validate_rg_dependency(moved, "v7"), "v7 gate moved to other step")
    rejected += 1

    publication_gate = (
        b"          scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --cross-toolchain\n"
    )
    omitted_publication = replace_once(
        successor, publication_gate, b"          true # omitted v7 publication gate\n", "v7 publication gate"
    )
    expect_rejection(
        lambda: V7.validate_rg_dependency(omitted_publication, "v7"),
        "v7 publication gate omitted",
    )
    rejected += 1
    publication_block = V7.step_block(
        successor, b"Validate the composite-v7 publication family and hostile suite"
    )
    replay_block = V7.step_block(successor, b"Validate fresh replay and current-source custody")
    reordered = successor.replace(publication_block + replay_block, replay_block + publication_block, 1)
    require(reordered != successor, "workflow step-order hostile did not change the fixture")
    expect_rejection(
        lambda: V7.validate_workflows(ci, reordered, retired),
        "v7 publication step moved after replay",
    )
    rejected += 1
    for label, hostile_ci, hostile_v7 in (
        (
            "v7 static command bypassed",
            ci,
            replace_once(
                successor,
                b"          python3 -I -S -B scripts/check-ksg-m1a-composite-v7.py --validate-static > \"${RUNNER_TEMP}/ksg-m1a-composite-v7-static.json\"\n",
                b"          true # v7 static command bypassed\n",
                "v7 static command",
            ),
        ),
        (
            "v7 replay command bypassed",
            ci,
            replace_once(
                successor,
                b"          python3 -I -S -B scripts/check-lean-toolchain-freeze.py\n",
                b"          true # replay command bypassed\n",
                "v7 replay command",
            ),
        ),
        (
            "CI workspace test bypassed",
            replace_once(
                ci,
                b"      - run: cargo test --locked --workspace --exclude pid-python\n",
                b"      - run: true # workspace test bypassed\n",
                "CI workspace test",
            ),
            successor,
        ),
    ):
        expect_rejection(
            lambda hostile_ci=hostile_ci, hostile_v7=hostile_v7: V7.validate_workflows(
                hostile_ci, hostile_v7, retired
            ),
            label,
        )
        rejected += 1

    require(
        V7.certified_job_digest(ci)
        == "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda",
        "certified job positive fixture changed",
    )
    certified_mutation = replace_once(
        ci,
        b"  certified-sxpid-reference:\n",
        b"  certified-sxpid-reference-mutated:\n",
        "certified job name",
    )
    expect_rejection(lambda: V7.certified_job_digest(certified_mutation), "certified job-section mutation")
    return rejected + 1


def justfile_hostiles() -> int:
    raw = (ROOT / V7.JUSTFILE_RELATIVE).read_bytes()
    V7.validate_justfile_values(raw, require_publication=True)
    recipe = V7.just_recipe(raw, b"ksg-composite-v7")

    def mutate_recipe(before: bytes, after: bytes, label: str) -> bytes:
        candidate_recipe = replace_once(recipe, before, after, label)
        return replace_once(raw, recipe, candidate_recipe, f"{label} recipe splice")

    mutations = [
        mutate_recipe(b"    set -euo pipefail\n", b"    set -eu\n", "shell fail-closed flags"),
        mutate_recipe(b"    command -v rg >/dev/null\n", b"    true # rg route bypassed\n", "local rg route"),
        mutate_recipe(
            b"    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > \"$result_root/local.optimized.json\"\n",
            b"",
            "optimized local self-test",
        ),
        mutate_recipe(
            b"    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact\n",
            b"    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --cross-toolchain\n",
            "retained v6 exact lane",
        ),
        mutate_recipe(
            V7.JUST_V7_PUBLICATION_FINAL,
            b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact\n"
            b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact\n",
            "v7 publication order",
        ),
        mutate_recipe(
            b"    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > \"$result_root/local.json\"\n",
            b"    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --output /tmp/record.json\n",
            "recursive real local capture",
        ),
    ]
    release_line = next(line for line in raw.splitlines(keepends=True) if line.startswith(b"release-audit:"))
    mutations.append(
        replace_once(
            raw,
            release_line,
            release_line.replace(b" ksg-composite-v7 ", b" ksg-composite-v6 "),
            "release audit composite route",
        )
    )
    retained_v6_static = b"    python3 -I -S -B scripts/check-ksg-m1a-composite-v6.py --validate-static > \"$result_root/static.json\"\n"
    mutations.append(
        replace_once(
            raw,
            retained_v6_static,
            b"    true # retained v6 static command bypassed\n",
            "retained v6 static command",
        )
    )
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(
            lambda candidate=candidate: V7.validate_justfile_values(
                candidate, require_publication=True
            ),
            f"justfile mutation {index}",
        )
    return len(mutations)


def local_source_hostiles() -> int:
    raw = (ROOT / V7.LOCAL_TOOL_RELATIVE).read_bytes()
    V7.validate_local_repair_source(raw)
    mutations = (
        replace_once(
            raw,
            b"MAX_AUTHORITY_STREAM_BYTES = 2 * 1024 * 1024",
            b"MAX_AUTHORITY_STREAM_BYTES = 4 * 1024 * 1024",
            "authority bound",
        ),
        replace_once(
            raw,
            b"MAX_VERSION_STREAM_BYTES = 64 * 1024",
            b"MAX_VERSION_STREAM_BYTES = 65 * 1024",
            "version bound",
        ),
        replace_once(
            raw,
            b"V6.C5_COMMIT = C6_COMMIT",
            b"V6.MAX_VERSION_STREAM_BYTES = MAX_AUTHORITY_STREAM_BYTES\nV6.C5_COMMIT = C6_COMMIT",
            "immutable v6 bound mutation",
        ),
        replace_once(
            raw,
            b"committed = git_authority_output(git_path, environment, head, relative)",
            b"committed = V6.git_output(git_path, environment, 'show', f'{head}:{relative}')",
            "generic Git authority route",
        ),
        replace_once(
            raw,
            b"generic v6 Git output accepted a 65,537-byte authority",
            b"generic negative control removed",
            "generic oversize negative control",
        ),
        replace_once(
            raw,
            b"MAX_COMMAND_STREAM_BYTES = 8 * 1024 * 1024",
            b"MAX_COMMAND_STREAM_BYTES = 9 * 1024 * 1024",
            "command bound",
        ),
        replace_once(
            raw,
            b"MAX_RECORD_BYTES = 32 * 1024 * 1024",
            b"MAX_RECORD_BYTES = 33 * 1024 * 1024",
            "record bound",
        ),
        replace_once(
            raw,
            b"MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024",
            b"MAX_EXECUTABLE_BYTES = 257 * 1024 * 1024",
            "executable bound",
        ),
        replace_once(
            raw,
            b"COMMAND_TIMEOUT_SECONDS = 14_400",
            b"COMMAND_TIMEOUT_SECONDS = 14_401",
            "command timeout",
        ),
        replace_once(
            raw,
            b'COMMAND_ARGV = ("just", "ksg-composite-v7")',
            b'COMMAND_ARGV = ("just", "ksg-composite-v6")',
            "fixed command",
        ),
        replace_once(
            raw,
            b'SCHEMA_RELATIVE: "local_l7_closure_schema",',
            b'SCHEMA_RELATIVE: "wrong_local_role",',
            "authority role",
        ),
        replace_once(
            raw,
            b'    V6_CHECKER_RELATIVE: "retained_v6_oversize_semantic_gate_authority",\n',
            b"",
            "authority row deletion",
        ),
        replace_once(
            raw,
            b'V6.TOOL_SPECS = dict(V6.TOOL_SPECS) | {"rg": ("--version",)}',
            b'V6.TOOL_SPECS = {"rg": ("--version",)}',
            "reviewed executable roster replacement",
        ),
        replace_once(
            raw,
            b"V6.C5_COMMIT = C6_COMMIT",
            b"V6.C5_COMMIT = '0' * 40",
            "subject parent rebind",
        ),
        replace_once(
            raw,
            b"V6.C5_COMMIT = C6_COMMIT",
            b"V6.UNREVIEWED_GLOBAL = True\nV6.C5_COMMIT = C6_COMMIT",
            "extra immutable-module mutation",
        ),
        replace_once(
            raw,
            b'and value["schema_revision"] == 2',
            b'and value["schema_revision"] == 3',
            "schema revision",
        ),
        replace_once(
            raw,
            b"The separate authority-stream bound fixes one exact C6 contradiction",
            b"The authority stream proves generic closure for C6",
            "local nonimplication",
        ),
        replace_once(
            raw,
            b'"command_stream_bytes": MAX_COMMAND_STREAM_BYTES,',
            b'"command_stream_bytes": MAX_AUTHORITY_STREAM_BYTES,',
            "limits projection",
        ),
        replace_once(
            raw,
            b'{"rg": ("--version",)}',
            b'{"rg": ("-V",)}',
            "ripgrep argv",
        ),
        replace_once(
            raw,
            b'C6_COMMIT = "0c3afa0ab5b264370072a18d24655df35b90574c"',
            b'C6_COMMIT = "0000000000000000000000000000000000000000"',
            "C6 subject literal",
        ),
        replace_once(
            raw,
            b'C7_MESSAGE = "Repair KSG M1a composite v7 contract\\n"',
            b'C7_MESSAGE = "Wrong v7 message\\n"',
            "C7 message literal",
        ),
        replace_once(
            raw,
            b'SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v7.schema.json"',
            b'SCHEMA_RELATIVE = "audit/schemas/wrong-v7.schema.json"',
            "local schema path literal",
        ),
        replace_once(
            raw,
            b'V6_SHA256 = "5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a"',
            b'V6_SHA256 = "0000000000000000000000000000000000000000000000000000000000000000"',
            "v6 primitive digest literal",
        ),
        replace_once(
            raw,
            b"    V6.reject_ambient_secrets(dict(os.environ))",
            b"    pass # ambient secret rejection bypassed",
            "ambient secret rejection",
        ),
        replace_once(
            raw,
            b'require(not timed_out and code == 0, "local closure command did not complete successfully")',
            b'require(True, "local closure command did not complete successfully")',
            "command success gate",
        ),
        replace_once(
            raw,
            b'            V6.reject_sensitive_output(stdout, private_prefixes, "local command stdout")',
            b"            pass # stdout sensitive-output scan bypassed",
            "stdout sensitive scan",
        ),
        replace_once(
            raw,
            b"                MAX_COMMAND_STREAM_BYTES,\n            )",
            b"                MAX_RECORD_BYTES,\n            )",
            "actual command drain bound",
        ),
    )
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(lambda candidate=candidate: V7.validate_local_repair_semantics(candidate), f"local source {index}")
    return len(mutations)


def capture_source_hostiles() -> int:
    raw = (ROOT / V7.CAPTURE_TOOL_RELATIVE).read_bytes()
    V7.validate_capture_source(raw)
    mutations = (
        replace_once(raw, b'return "CI", ".github/workflows/ci.yml", "push"', b'return "Evil", ".github/workflows/evil.yml", "push"', "CI route"),
        replace_once(raw, b'return "Push on main", "dynamic/github-code-scanning/codeql", "dynamic"', b'return "Evil", "dynamic/evil", "dynamic"', "CodeQL route"),
        replace_once(raw, b'return (\n        "KSG M1a composite v7",', b'return (\n        "KSG M1a composite v6",', "successor contract route"),
        replace_once(raw, b'if role == "successor_ci":\n        return {\n            "coverage-lcov",', b'if role == "successor_ci":\n        return {\n            "wrong-artifact",', "successor CI artifacts"),
        replace_once(raw, b'V6.workflow_identity = workflow_identity', b'V6.unreviewed = True\nV6.workflow_identity = workflow_identity', "extra v6 rebind"),
        replace_once(raw, b'C6_TREE = "ad28fd5ec3eed76fca1315b24c2e047fb5e6cff4"', b'C6_TREE = "0000000000000000000000000000000000000000"', "C6 tree"),
        replace_once(raw, b"C6_CI_RUN = 32_139_920_717", b"C6_CI_RUN = 0", "terminal C6 CI run"),
        replace_once(raw, b'SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v7.py"', b'SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v8.py"', "capture tool path"),
        replace_once(raw, b'    "predecessor_contract": "failure",', b'    "predecessor_contract": "success",', "predecessor conclusion"),
        replace_once(raw, b'    "SSLKEYLOGFILE",\n', b"", "TLS key-log environment"),
        replace_once(raw, b"for repetition in (1, 2):", b"for repetition in (1,):", "retrieval repetitions"),
        replace_once(raw, b"len(captures) <= V6.MAX_CAPTURE_ROWS", b"True", "capture row bound"),
    )
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(lambda candidate=candidate: V7.validate_capture_source_semantics(candidate), f"capture source {index}")
    return len(mutations)


def counterexample_hostiles() -> int:
    _commit, entries = V7.c6_anchor()
    schema_raw = (ROOT / V7.COUNTEREXAMPLE_SCHEMA_RELATIVE).read_bytes()
    evidence_raw = (ROOT / V7.COUNTEREXAMPLE_RELATIVE).read_bytes()
    V7.validate_counterexample_pair_bytes(schema_raw, evidence_raw, entries)
    evidence = json.loads(evidence_raw)
    V7.validate_counterexample_value(evidence, entries)
    mutations: list[dict[str, Any]] = []
    changed = copy.deepcopy(evidence)
    changed["authorities"][3]["size_bytes"] += 1
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["authorities"][3], changed["authorities"][4] = changed["authorities"][4], changed["authorities"][3]
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["counterexamples"][0]["excess_over_stream_bound_bytes"] += 1
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["conclusion"]["first_blocking_path"] = V7.V6_CHECKER_RELATIVE
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["source_anchors"][0]["sha256"] = "0" * 64
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["subject"]["tree_object_sha1"] = "0" * 40
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["route"]["internal_command_bound_argument"] = "MAX_AUTHORITY_STREAM_BYTES"
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["rederivation"]["content_command_template"][2] = "HEAD:<PATH>"
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["derivation"]["authority_count"] += 1
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["nonimplications"].pop()
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["bounds"]["largest_complete_stdout_accepted_bytes"] += 1
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["counterexamples"][0]["complete_stdout_accepted_by_run_bounded"] = True
    mutations.append(changed)
    changed = copy.deepcopy(evidence)
    changed["source_anchors"][0]["id"] = "self_selected_slice"
    mutations.append(changed)
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(
            lambda candidate=candidate: V7.validate_counterexample_value(candidate, entries),
            f"counterexample cross-file mutation {index}",
        )
    for label, hostile_schema, hostile_evidence in (
        ("schema byte", schema_raw.replace(b'"$schema"', b'"$schema_"', 1), evidence_raw),
        ("evidence byte", schema_raw, evidence_raw.replace(b'"repository"', b'"repository_"', 1)),
    ):
        expect_rejection(
            lambda hostile_schema=hostile_schema, hostile_evidence=hostile_evidence: V7.validate_counterexample_pair_bytes(
                hostile_schema, hostile_evidence, entries
            ),
            f"counterexample {label} mutation",
        )
    return len(mutations) + 2


def policy_hostiles() -> int:
    policy = json.loads((ROOT / V7.POLICY_RELATIVE).read_text(encoding="utf-8"))
    V7.validate_policy_value(policy)
    mutations: list[dict[str, Any]] = []
    for revision in (4, 5, 6):
        changed = copy.deepcopy(policy)
        changed["base"][f"r{revision}_status"] = "issued"
        mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["reserved_absent_paths"]["legacy_receipts"].pop()
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["local_recorder"]["machine_counterexample_state"] = "reserved_absent"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["local_recorder"]["machine_counterexample_state"] = "present_unfrozen"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["local_recorder"]["machine_counterexample"]["sha256"] = "0" * 64
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["repository_ci_attempt_1"]["conclusion"] = "pending_terminal_roster"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["repository_ci_attempt_1"]["failed_step"]["number"] = 12
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["repository_ci_attempt_1"]["terminal_at"] = "2026-08-18T14:48:11Z"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c6_disposition"]["predecessor_capture"]["sha256"] = "0" * 64
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["reserved_absent_paths"]["publication"].append(
        "output/pdf/ksg-m1a-composite-v7-boundary.pdf"
    )
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["delta"].pop()
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["delta"].append(copy.deepcopy(changed["c7"]["delta"][-1]))
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["delta"][0]["role"] = "wrong_role"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["r7"]["delta"].append(copy.deepcopy(changed["r7"]["delta"][-1]))
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["r7"]["delta"][0], changed["r7"]["delta"][1] = (
        changed["r7"]["delta"][1],
        changed["r7"]["delta"][0],
    )
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["r7"]["message"] = "Record KSG M1a composite v6 receipt\n"
    mutations.append(changed)
    for field, value in (
        ("path", "audit/evidence/wrong.json"),
        ("status", "M"),
        ("mode", "100755"),
        ("role", "wrong_role"),
    ):
        changed = copy.deepcopy(policy)
        changed["r7"]["delta"][1][field] = value
        mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["unexpected"] = True
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["base"]["message"] = V7.C7_MESSAGE
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["tree"] = "0" * 40
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["tree_state"] = "unresolved_until_c7_commit"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["c7"]["delta_state"] = "unresolved_until_terminal_capture_publication_and_r12"
    mutations.append(changed)
    changed = copy.deepcopy(policy)
    changed["nonimplications"][0] = "This draft policy is intentionally nonfinal."
    mutations.append(changed)
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(lambda candidate=candidate: V7.validate_policy_value(candidate), f"policy mutation {index}")
    require(
        "scripts/generate-lean-4.33-replay.py" in V7.DRAFT_ALLOWED_PATHS
        and "scripts/generate-lean-toolchain-freeze.py" not in V7.DRAFT_ALLOWED_PATHS,
        "r12 generator draft-scope route changed",
    )
    V7.validate_allowed_draft_paths_v7({V7.CURRENT_SOURCE_RELATIVE})
    expect_rejection(
        lambda: V7.validate_allowed_draft_paths_v7(
            {V7.CURRENT_SOURCE_RELATIVE},
            V7.DRAFT_ALLOWED_PATHS - {V7.CURRENT_SOURCE_RELATIVE},
        ),
        "current-source omitted from approved C7 draft scope",
    )
    return len(mutations) + 2


def capture_schema_fixture(phase: str, path: str) -> dict[str, Any]:
    body = b"{}"
    predecessor = phase == "predecessor_failure"
    return {
        "capture_tool": binding(V7.CAPTURE_TOOL_RELATIVE),
        "captures": [
            {
                "body_base64": "e30=",
                "body_sha256": V7.sha256(body),
                "body_size_bytes": len(body),
                "logical_request": "predecessor_ci_run" if predecessor else "successor_ci_run",
                "media_type": "application/json",
                "page": 0,
                "path": path,
                "redirect": None,
                "repetition": 1,
                "response_kind": "json",
                "status_code": 200,
            }
        ],
        "immutable_v6_primitives": binding(V7.V6_CAPTURE_PRIMITIVE["path"]),
        "nonimplications": V7.CAPTURE_NONIMPLICATIONS,
        "phase": phase,
        "repository": V7.REPOSITORY,
        "retry_events": [],
        "runs": (
            {"predecessor_ci": 1, "predecessor_codeql": 2, "predecessor_contract": 3}
            if predecessor
            else {"successor_ci": 4, "successor_codeql": 5, "successor_contract": 6}
        ),
        "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v7",
        "schema_revision": 7,
        "subject": (
            {"predecessor_commit": V7.C6_COMMIT, "predecessor_tree": V7.C6_TREE}
            if predecessor
            else {
                "predecessor_commit": V7.C6_COMMIT,
                "predecessor_tree": V7.C6_TREE,
                "successor_commit": "3" * 40,
                "successor_tree": "4" * 40,
            }
        ),
    }


def schema_hostiles() -> int:
    schemas = {
        relative: json.loads((ROOT / relative).read_text(encoding="utf-8"))
        for relative in (V7.CAPTURE_SCHEMA_RELATIVE, V7.LOCAL_SCHEMA_RELATIVE, V7.RECEIPT_SCHEMA_RELATIVE)
    }
    rejected = 0
    for relative, schema in schemas.items():
        V7.validate_schema_value(schema, relative, relative)
        hostile = copy.deepcopy(schema)
        hostile["$id"] = f"https://evil.invalid/{relative}"
        expect_rejection(
            lambda hostile=hostile, relative=relative: V7.validate_schema_value(hostile, relative, relative),
            f"schema canonical ID {relative}",
        )
        rejected += 1
    schema = schemas[V7.CAPTURE_SCHEMA_RELATIVE]
    paths = (
        f"/repos/{V7.REPOSITORY}/actions/runs/1",
        f"/repos/{V7.REPOSITORY}/actions/runs/1/attempts/1/jobs?per_page=100&page=1",
        f"/repos/{V7.REPOSITORY}/actions/artifacts/1/zip",
        f"/repos/{V7.REPOSITORY}/actions/jobs/1/logs",
    )
    for path in paths:
        fixture = capture_schema_fixture("predecessor_failure", path)
        V7.validate_schema_instance(fixture, schema, "hosted capture real-path fixture")
    predecessor = capture_schema_fixture("predecessor_failure", paths[0])
    successor = capture_schema_fixture("successor_qualification", paths[0])
    mixtures = []
    changed = copy.deepcopy(predecessor)
    changed["runs"] = successor["runs"]
    mixtures.append(changed)
    changed = copy.deepcopy(predecessor)
    changed["subject"] = successor["subject"]
    mixtures.append(changed)
    changed = copy.deepcopy(successor)
    changed["runs"] = predecessor["runs"]
    mixtures.append(changed)
    changed = copy.deepcopy(successor)
    changed["subject"] = predecessor["subject"]
    mixtures.append(changed)
    for index, hostile in enumerate(mixtures, start=1):
        expect_rejection(
            lambda hostile=hostile: V7.validate_schema_instance(hostile, schema, "cross-phase hosted capture"),
            f"hosted schema cross-phase mixture {index}",
        )
        rejected += 1
    for path in (
        "/repos/other/pid-rs/actions/runs/1",
        f"/repos/{V7.REPOSITORY}/actions/runs/1\n",
    ):
        hostile = capture_schema_fixture("predecessor_failure", path)
        expect_rejection(
            lambda hostile=hostile: V7.validate_schema_instance(hostile, schema, "hostile hosted path"),
            "hosted schema path pattern",
        )
        rejected += 1
    return rejected


def receipt_derivation_guard_hostiles() -> int:
    domains = [
        {
            "analysis_ids": [401],
            "artifact_ids": [301],
            "job_ids": [201],
            "repository_id": 101,
            "run_id": 1,
        },
        {
            "analysis_ids": [402],
            "artifact_ids": [302],
            "job_ids": [202],
            "repository_id": 101,
            "run_id": 2,
        },
    ]
    V7.validate_identifier_domains_v7(domains)
    mutations: list[list[dict[str, Any]]] = []
    for field in ("repository_id", "run_id", "job_ids", "artifact_ids", "analysis_ids"):
        candidate = copy.deepcopy(domains)
        candidate[1][field] = (
            999
            if field == "repository_id"
            else candidate[0][field]
            if field == "run_id"
            else list(candidate[0][field])
        )
        mutations.append(candidate)
    rejected = 0
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(
            lambda candidate=candidate: V7.validate_identifier_domains_v7(candidate),
            f"receipt identifier-domain mutation {index}",
        )
        rejected += 1

    def byte_binding(raw: bytes) -> dict[str, Any]:
        return {
            "body_base64": base64.b64encode(raw).decode("ascii"),
            "sha256": V7.sha256(raw),
            "size_bytes": len(raw),
        }

    V7.decode_local_public_binding_v7(byte_binding(b"benign output\n"), "benign", 1024)
    for label, raw in (
        ("credential", b"Authorization: Bearer abcdefghijklmnopqrstuvwxyz"),
        ("private path", b"/private/tmp/pid-rs-private/record"),
    ):
        expect_rejection(
            lambda raw=raw: V7.decode_local_public_binding_v7(
                byte_binding(raw), f"hostile {label}", 1024
            ),
            f"local output {label}",
        )
        rejected += 1

    jobs = [
        {"conclusion": "failure", "job_id": V7.C6_CI_FAILED_JOB},
        {"conclusion": "success", "job_id": V7.C6_CI_FAILED_JOB + 1},
    ]
    V7.validate_predecessor_job_dispositions_v7(
        jobs, "predecessor_ci", {V7.C6_CI_FAILED_JOB}
    )
    hostile_jobs = copy.deepcopy(jobs)
    hostile_jobs[1]["conclusion"] = "cancelled"
    expect_rejection(
        lambda: V7.validate_predecessor_job_dispositions_v7(
            hostile_jobs, "predecessor_ci", {V7.C6_CI_FAILED_JOB}
        ),
        "predecessor extra non-success job",
    )
    rejected += 1

    terminal_run = {
        "created_at": V7.C6_CI_CREATED_AT,
        "repository_id": V7.C6_REPOSITORY_ID,
        "run_started_at": V7.C6_CI_CREATED_AT,
        "updated_at": V7.C6_CI_UPDATED_AT,
    }
    V7.validate_c6_ci_terminal_run_v7(terminal_run)
    for field, value in (
        ("repository_id", V7.C6_REPOSITORY_ID + 1),
        ("updated_at", "2026-08-18T14:48:11Z"),
    ):
        hostile_run = dict(terminal_run)
        hostile_run[field] = value
        expect_rejection(
            lambda hostile_run=hostile_run: V7.validate_c6_ci_terminal_run_v7(
                hostile_run
            ),
            f"predecessor terminal run {field}",
        )
        rejected += 1

    failed_job = {
        "name": "Formal LaTeX / PDF inventory and cross-toolchain structure",
        "steps": [
            {
                "conclusion": "failure",
                "name": "Rebuild papers and check cross-toolchain text, geometry, fonts, and workflow renders",
                "number": 11,
            }
        ],
    }
    V7.validate_required_failure_identity_v7(
        "predecessor_ci", V7.C6_CI_FAILED_JOB, failed_job
    )
    hostile_job = copy.deepcopy(failed_job)
    hostile_job["steps"][0]["number"] = 12
    expect_rejection(
        lambda: V7.validate_required_failure_identity_v7(
            "predecessor_ci", V7.C6_CI_FAILED_JOB, hostile_job
        ),
        "predecessor failed-step number",
    )
    rejected += 1

    log_digest, log_size = V7.PREDECESSOR_REQUIRED_LOG_BINDINGS[
        "predecessor_ci"
    ][V7.C6_CI_FAILED_JOB]
    V7.validate_required_failed_log_binding_v7(
        "predecessor_ci", V7.C6_CI_FAILED_JOB, log_digest, log_size
    )
    expect_rejection(
        lambda: V7.validate_required_failed_log_binding_v7(
            "predecessor_ci", V7.C6_CI_FAILED_JOB, "0" * 64, log_size
        ),
        "predecessor failed-log digest",
    )
    rejected += 1

    diagnostic = V7.C6_MISSING_RG_DIAGNOSTIC.encode("ascii")
    marker_fixture = b"\n".join((*V7.C6_CI_PRIOR_PDF_GATE_MARKERS, diagnostic))
    V7.validate_c6_ci_prior_pdf_markers_v7(marker_fixture)
    expect_rejection(
        lambda: V7.validate_c6_ci_prior_pdf_markers_v7(
            marker_fixture.replace(V7.C6_CI_PRIOR_PDF_GATE_MARKERS[0], b"", 1)
        ),
        "predecessor prior PDF marker removed",
    )
    rejected += 1
    reordered_markers = b"\n".join(
        (
            V7.C6_CI_PRIOR_PDF_GATE_MARKERS[1],
            V7.C6_CI_PRIOR_PDF_GATE_MARKERS[0],
            *V7.C6_CI_PRIOR_PDF_GATE_MARKERS[2:],
            diagnostic,
        )
    )
    expect_rejection(
        lambda: V7.validate_c6_ci_prior_pdf_markers_v7(reordered_markers),
        "predecessor prior PDF marker order",
    )
    rejected += 1
    return rejected


def receipt_fd_hostiles() -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-c7-fd-self-test-") as temporary:
        path = Path(temporary) / "input.json"
        create_fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(create_fd, b"{}\n")
        finally:
            os.close(create_fd)
        readonly_fd = os.open(path, os.O_RDONLY)
        try:
            raw, _identity = V7.bounded_regular_fd_v7(
                readonly_fd, "readonly positive fixture", 1024
            )
            require(raw == b"{}\n", "readonly FD positive fixture changed")
        finally:
            os.close(readonly_fd)
        rejected = 0
        for label in ("local", "successor"):
            readwrite_fd = os.open(path, os.O_RDWR)
            try:
                expect_rejection(
                    lambda readwrite_fd=readwrite_fd, label=label: V7.bounded_regular_fd_v7(
                        readwrite_fd, f"{label} read-write hostile", 1024
                    ),
                    f"{label} O_RDWR evidence descriptor",
                )
                rejected += 1
            finally:
                os.close(readwrite_fd)
        nonzero_fd = os.open(path, os.O_RDONLY)
        try:
            os.lseek(nonzero_fd, 1, os.SEEK_SET)
            expect_rejection(
                lambda: V7.bounded_regular_fd_v7(nonzero_fd, "nonzero-offset hostile", 1024),
                "nonzero evidence descriptor offset",
            )
            rejected += 1
        finally:
            os.close(nonzero_fd)
        mode_path = Path(temporary) / "mode.json"
        mode_create_fd = os.open(mode_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(mode_create_fd, b"{}\n")
        finally:
            os.close(mode_create_fd)
        os.chmod(mode_path, 0o640)
        mode_fd = os.open(mode_path, os.O_RDONLY)
        try:
            expect_rejection(
                lambda: V7.bounded_regular_fd_v7(mode_fd, "wrong-mode hostile", 1024),
                "non-0600 evidence file",
            )
            rejected += 1
        finally:
            os.close(mode_fd)
        hardlink_path = Path(temporary) / "hardlink.json"
        os.link(path, hardlink_path)
        hardlink_fd = os.open(path, os.O_RDONLY)
        try:
            expect_rejection(
                lambda: V7.bounded_regular_fd_v7(hardlink_fd, "hardlink hostile", 1024),
                "multiply-linked evidence file",
            )
            rejected += 1
        finally:
            os.close(hardlink_fd)
        os.unlink(hardlink_path)
        pipe_read, pipe_write = os.pipe()
        try:
            expect_rejection(
                lambda: V7.bounded_regular_fd_v7(pipe_read, "pipe hostile", 1024),
                "nonregular evidence descriptor",
            )
            rejected += 1
        finally:
            os.close(pipe_read)
            os.close(pipe_write)
        size_fd = os.open(path, os.O_RDONLY)
        try:
            expect_rejection(
                lambda: V7.bounded_regular_fd_v7(size_fd, "oversize hostile", 2),
                "evidence descriptor size bound",
            )
            rejected += 1
        finally:
            os.close(size_fd)
        expect_rejection(
            lambda: V7.require_distinct_fd_numbers_v7(7, 7),
            "same evidence descriptor number",
        )
        rejected += 1
        alias_fd = os.open(path, os.O_RDONLY)
        duplicate_fd = os.dup(alias_fd)
        try:
            require(alias_fd != duplicate_fd, "duplicate FD fixture numbers overlap")
            alias_identity = (os.fstat(alias_fd).st_dev, os.fstat(alias_fd).st_ino)
            duplicate_identity = (
                os.fstat(duplicate_fd).st_dev,
                os.fstat(duplicate_fd).st_ino,
            )
            expect_rejection(
                lambda: V7.require_distinct_fd_identities_v7(
                    alias_identity, duplicate_identity
                ),
                "distinct evidence descriptors alias one inode",
            )
            rejected += 1
        finally:
            os.close(duplicate_fd)
            os.close(alias_fd)
        snapshot_fd = os.open(path, os.O_RDONLY)
        try:
            before = V7.fd_snapshot_v7(os.fstat(snapshot_fd))
            after = (*before[:-1], before[-1] + 1)
            expect_rejection(
                lambda: V7.require_stable_fd_snapshot_v7(
                    before, after, "drifting hostile"
                ),
                "evidence descriptor stability",
            )
            rejected += 1
        finally:
            os.close(snapshot_fd)
    return rejected


def topology_guard_hostiles() -> int:
    ordinary_oid = "1" * 40
    c7 = "2" * 40
    r7 = "3" * 40
    V7.validate_forbidden_state_v7(set(), "ordinary earlier commit\n", ordinary_oid, c7, r7)
    mutations = (
        ({V7.FORBIDDEN_EVIDENCE_PATHS[0]}, "ordinary earlier commit\n", "earlier forbidden path"),
        (set(), "Record KSG M1a composite v5 receipt\n", "earlier forbidden message"),
    )
    rejected = 0
    for paths, message, label in mutations:
        expect_rejection(
            lambda paths=paths, message=message: V7.validate_forbidden_state_v7(
                paths, message, ordinary_oid, c7, r7
            ),
            label,
        )
        rejected += 1
    rows = (("path", "M", "100644", "role"),)
    V7.validate_exact_c7_delta_v7((("path", "M", "100644"),), rows)
    expect_rejection(
        lambda: V7.validate_exact_c7_delta_v7(
            (("path", "A", "100644"),), rows
        ),
        "actual C7 delta changed while policy rows stayed fixed",
    )
    rejected += 1
    exact_entries = {"retained": object()}
    V7.validate_pre_c7_reachable_state_v7(
        V7.C6_COMMIT, V7.C6_TREE, exact_entries, exact_entries
    )
    hostile_entries = dict(exact_entries)
    hostile_entries["side-branch-extra"] = object()
    expect_rejection(
        lambda: V7.validate_pre_c7_reachable_state_v7(
            ordinary_oid, V7.C6_TREE, hostile_entries, exact_entries
        ),
        "pre-C7 merge side commit with extra path and stale source manifest",
    )
    return rejected + 1


def binding(path: str) -> dict[str, Any]:
    return {"path": path, "sha256": "1" * 64, "size_bytes": 1}


def role(role_name: str, run_id: int, conclusion: str, workflow_path: str) -> dict[str, Any]:
    failed = [run_id + 1000] if conclusion == "failure" else []
    return {
        "artifact_names": [],
        "conclusion": conclusion,
        "failed_job_ids": failed,
        "job_count": 1,
        "jobs_sha256": "2" * 64,
        "role": role_name,
        "run_id": run_id,
        "workflow_path": workflow_path,
    }


def receipt_fixture() -> dict[str, Any]:
    c7_commit = "3" * 40
    c7_tree = "4" * 40
    predecessor_roles = [
        role("predecessor_ci", V7.C6_CI_RUN, "failure", V7.CI_RELATIVE),
        role(
            "predecessor_codeql",
            V7.C6_CODEQL_RUN,
            "success",
            "dynamic/github-code-scanning/codeql",
        ),
        role("predecessor_contract", V7.C6_CONTRACT_RUN, "failure", V7.V6_WORKFLOW_RELATIVE),
    ]
    predecessor_roles[0]["failed_job_ids"] = [V7.C6_CI_FAILED_JOB]
    predecessor_roles[2]["failed_job_ids"] = [V7.C6_CONTRACT_FAILED_JOB]
    successor_roles = [
        role("successor_ci", 201, "success", V7.CI_RELATIVE),
        role("successor_codeql", 202, "success", "dynamic/github-code-scanning/codeql"),
        role("successor_contract", 203, "success", V7.V7_WORKFLOW_RELATIVE),
    ]
    return {
        "capture_bindings": [
            {**binding(V7.PREDECESSOR_CAPTURE_RELATIVE), "phase": "predecessor_failure"},
            {**binding(V7.SUCCESSOR_CAPTURE_RELATIVE), "phase": "successor_qualification"},
        ],
        "contract_authorities": [
            {**binding(V7.CHECKER_RELATIVE), "role": "composite_v7_semantic_gate"}
        ],
        "defects": [
            {
                "evidence": [binding(V7.PREDECESSOR_CAPTURE_RELATIVE)],
                "id": "c6_hosted_missing_rg",
                "scope": "hosted_dependency_closure",
                "status": "failed_zero_credit",
            },
            {
                "evidence": [binding(V7.COUNTEREXAMPLE_RELATIVE)],
                "id": "c6_local_authority_bound_contradiction",
                "scope": "immutable_local_recorder",
                "status": "impossible_zero_credit",
            },
        ],
        "local_qualification": {
            "authorities_sha256": "5" * 64,
            "command": {
                "argv": ["just", "ksg-composite-v7"],
                "elapsed_monotonic_ns": 1,
                "exit_code": 0,
                "stderr_sha256": "6" * 64,
                "stderr_size_bytes": 0,
                "stdout_sha256": "7" * 64,
                "stdout_size_bytes": 1,
                "timed_out": False,
            },
            "platform": {
                "architecture": "arm64",
                "operating_system": "Darwin",
                "python_implementation": "CPython",
            },
            "record_binding": binding(V7.LOCAL_RECORD_RELATIVE),
            "reviewed_executables_sha256": "8" * 64,
            "subject": {"c7_commit": c7_commit, "c7_tree": c7_tree},
        },
        "nonimplications": V7.RECEIPT_NONIMPLICATIONS,
        "observations": [
            {
                "capture_sha256": "9" * 64,
                "normalized_sha256": "a" * 64,
                "phase": "predecessor_failure",
                "roles": predecessor_roles,
            },
            {
                "capture_sha256": "b" * 64,
                "normalized_sha256": "c" * 64,
                "phase": "successor_qualification",
                "roles": successor_roles,
            },
        ],
        "publication": {
            **{field: binding(path) for field, path in V7.PUBLICATION_FIELDS.items()},
            "status": "validated",
        },
        "replay": {
            "current_r12": binding(V7.R12_RELATIVE),
            "current_source": binding(V7.CURRENT_SOURCE_RELATIVE),
            "predicate": "fresh_post_c6_r12_and_current_source_match_c7",
            "retained_r11": binding(V7.R11_RELATIVE),
        },
        "repository": V7.REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v7",
        "schema_revision": 7,
        "subject": {
            "c6_commit": V7.C6_COMMIT,
            "c6_tree": V7.C6_TREE,
            "c7_commit": c7_commit,
            "c7_tree": c7_tree,
        },
        "verdict": {
            "c6_hosted_qualification": "failed_zero_credit",
            "c6_local_qualification": "impossible_zero_credit",
            "c6_publication": "published_unchanged",
            "c7_bounded_repair": "pass",
            "c7_hosted_observation": "pass",
            "c7_local_qualification": "pass",
            "r4_receipt_issued": False,
            "r5_receipt_issued": False,
            "r6_receipt_issued": False,
            "r7_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
    }


def receipt_hostiles() -> int:
    schema = V7.validate_schema_file(V7.RECEIPT_SCHEMA_RELATIVE, V7.RECEIPT_SCHEMA_RELATIVE)
    fixture = receipt_fixture()
    V7.validate_schema_instance(fixture, schema, "self-test v7 receipt")
    V7.validate_receipt_semantics(fixture)
    mutations: list[dict[str, Any]] = []
    changed = copy.deepcopy(fixture)
    changed["defects"][1]["status"] = "failed_zero_credit"
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["verdict"]["r6_receipt_issued"] = True
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["observations"][0]["roles"][0], changed["observations"][0]["roles"][1] = (
        changed["observations"][0]["roles"][1],
        changed["observations"][0]["roles"][0],
    )
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["publication"]["boundary_pdf"]["path"] = "output/pdf/wrong.pdf"
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["replay"]["current_r12"]["path"] = V7.R11_RELATIVE
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["observations"][1]["roles"][2]["conclusion"] = "failure"
    changed["observations"][1]["roles"][2]["failed_job_ids"] = [999]
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["observations"][0]["roles"][1]["conclusion"] = "failure"
    changed["observations"][0]["roles"][1]["failed_job_ids"] = [998]
    mutations.append(changed)
    changed = copy.deepcopy(fixture)
    changed["unexpected"] = True
    mutations.append(changed)
    for index, candidate in enumerate(mutations, start=1):
        expect_rejection(
            lambda candidate=candidate: (
                V7.validate_schema_instance(candidate, schema, "hostile v7 receipt"),
                V7.validate_receipt_semantics(candidate),
            ),
            f"receipt mutation {index}",
        )
    return len(mutations)


def lean_r12_cut_hostiles() -> int:
    projection_placeholder = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    scalar_placeholder = (
        'EXPECTED_COMPOSITE_V7_CHECKER_OPERATIONAL_SHA256 = "0" * 64'
    )
    operational_placeholder = (
        '    "scripts/check-ksg-m1a-composite-v7.py": "0" * 64,'
    )
    normalized_lean = (
        projection_placeholder
        + "\n"
        + scalar_placeholder
        + "\n"
        + operational_placeholder
        + "\n"
    ).encode("utf-8")
    normalized_digest = V7.sha256(normalized_lean)
    checker_raw = (
        'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "' + normalized_digest + '"\n'
    ).encode("utf-8")

    def replay_lean(checker: bytes) -> bytes:
        checker_digest = V7.sha256(checker)
        return normalized_lean.replace(
            scalar_placeholder.encode("utf-8"),
            (
                'EXPECTED_COMPOSITE_V7_CHECKER_OPERATIONAL_SHA256 = "'
                + checker_digest
                + '"'
            ).encode("utf-8"),
            1,
        ).replace(
            operational_placeholder.encode("utf-8"),
            (
                '    "scripts/check-ksg-m1a-composite-v7.py": "'
                + checker_digest
                + '",'
            ).encode("utf-8"),
            1,
        )

    def fixture(
        checker: bytes = checker_raw,
        *,
        custody_in_operational: bool = False,
        custody_in_scientific: bool = False,
    ) -> tuple[bytes, dict[str, Any], dict[str, Any], str]:
        checker_digest = V7.sha256(checker)
        replay_raw = replay_lean(checker)
        self_test_digest = V7.sha256(b"self-test fixture\n")
        scientific = {"scripts/check-scientific-fixture.py": "d" * 64}
        r11 = {"checker_sha256": dict(scientific)}
        if custody_in_scientific:
            scientific[V7.LEAN_SELF_TEST_RELATIVE] = "e" * 64
            r11["checker_sha256"] = dict(scientific)
        operational = {V7.CHECKER_RELATIVE: checker_digest}
        if custody_in_operational:
            operational[V7.LEAN_CHECKER_RELATIVE] = "f" * 64
        r12 = {
            "checker_sha256": scientific,
            "custody_gate_sha256": {
                V7.LEAN_SELF_TEST_RELATIVE: self_test_digest,
                V7.LEAN_CHECKER_RELATIVE: "0" * 64,
            },
            "operational_wiring_sha256": operational,
            "prior_replay_preservation_sha256": {V7.R11_RELATIVE: "b" * 64},
            "prior_replay_schema": {
                V7.R11_RELATIVE: "pid-rs/lean-current-project-replay/v2"
            },
            "replay_custody_gate_sha256": {
                V7.LEAN_SELF_TEST_RELATIVE: self_test_digest,
                V7.LEAN_CHECKER_RELATIVE: V7.sha256(replay_raw),
            },
            "schema": "pid-rs/lean-current-project-replay/v2",
            "status": "passed",
        }
        projection = V7.lean_replay_projection_sha256_v7(r12)
        final_raw = replay_raw.replace(
            projection_placeholder.encode("utf-8"),
            (
                'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
                + projection
                + '"'
            ).encode("utf-8"),
            1,
        )
        r12["custody_gate_sha256"][V7.LEAN_CHECKER_RELATIVE] = V7.sha256(
            final_raw
        )
        return final_raw, r11, r12, projection

    lean_raw, r11, r12, projection = fixture()
    V7.validate_lean_r12_checksum_cut_v7(checker_raw, lean_raw)
    V7.validate_lean_r12_receipt_cuts_v7(
        checker_raw, lean_raw, b"self-test fixture\n", r11, r12, projection
    )

    mismatched_checker = checker_raw.replace(
        normalized_digest.encode("ascii"), b"3" * 64, 1
    )
    placeholder_checker = checker_raw.replace(
        normalized_digest.encode("ascii"), b"0" * 64, 1
    )
    checksum_mutations = (
        (checker_raw + b"# post-seal drift\n", lean_raw, "v7 checker causal drift"),
        (
            checker_raw,
            lean_raw.replace(
                V7.sha256(checker_raw).encode("ascii"), b"2" * 64, 1
            ),
            "v7 scalar cut",
        ),
        (
            checker_raw,
            lean_raw.replace(
                V7.sha256(checker_raw).encode("ascii"), b"2" * 64, 2
            ),
            "v7 operational cut",
        ),
        (mismatched_checker, fixture(mismatched_checker)[0], "normalized Lean cut"),
        (placeholder_checker, fixture(placeholder_checker)[0], "normalized placeholder"),
        (
            checker_raw + checker_raw,
            fixture(checker_raw + checker_raw)[0],
            "duplicate normalized cut",
        ),
        (checker_raw, lean_raw + b"# normalized-source drift\n", "Lean source drift"),
    )
    for changed_checker, changed_lean, label in checksum_mutations:
        expect_rejection(
            lambda changed_checker=changed_checker, changed_lean=changed_lean: (
                V7.validate_lean_r12_checksum_cut_v7(changed_checker, changed_lean)
            ),
            label,
        )

    receipt_mutations: list[tuple[bytes, dict[str, Any], dict[str, Any], str, str]] = []
    changed = copy.deepcopy(r12)
    changed["operational_wiring_sha256"][V7.CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 v7 map"))
    changed = copy.deepcopy(r12)
    changed["checker_sha256"]["scripts/check-scientific-fixture.py"] = "0" * 64
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 scientific set"))
    changed = copy.deepcopy(r12)
    changed["custody_gate_sha256"][V7.LEAN_CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 final custody"))
    changed = copy.deepcopy(r12)
    changed["replay_custody_gate_sha256"][V7.LEAN_CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 replay custody"))
    receipt_mutations.append((lean_raw, r11, r12, "2" * 64, "r12 projection"))
    changed = copy.deepcopy(r12)
    changed["custody_gate_sha256"].pop(V7.LEAN_SELF_TEST_RELATIVE)
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 missing custody"))
    changed = copy.deepcopy(r12)
    changed["replay_custody_gate_sha256"]["scripts/unreviewed.py"] = "4" * 64
    receipt_mutations.append((lean_raw, r11, changed, projection, "r12 extra replay custody"))
    for changed_lean, changed_r11, changed_r12, changed_projection, label in receipt_mutations:
        expect_rejection(
            lambda changed_lean=changed_lean, changed_r11=changed_r11, changed_r12=changed_r12, changed_projection=changed_projection: (
                V7.validate_lean_r12_receipt_cuts_v7(
                    checker_raw,
                    changed_lean,
                    b"self-test fixture\n",
                    changed_r11,
                    changed_r12,
                    changed_projection,
                )
            ),
            label,
        )

    for label, custody_in_operational, custody_in_scientific in (
        ("r12 custody in operational map", True, False),
        ("r12 custody in scientific map", False, True),
    ):
        hostile_lean, hostile_r11, hostile_r12, hostile_projection = fixture(
            custody_in_operational=custody_in_operational,
            custody_in_scientific=custody_in_scientific,
        )
        expect_rejection(
            lambda hostile_lean=hostile_lean, hostile_r11=hostile_r11, hostile_r12=hostile_r12, hostile_projection=hostile_projection: (
                V7.validate_lean_r12_receipt_cuts_v7(
                    checker_raw,
                    hostile_lean,
                    b"self-test fixture\n",
                    hostile_r11,
                    hostile_r12,
                    hostile_projection,
                )
            ),
            label,
        )
    return len(checksum_mutations) + len(receipt_mutations) + 2


def main() -> int:
    try:
        workflow_count = workflow_hostiles()
        capture_source_count = capture_source_hostiles()
        local_count = local_source_hostiles()
        justfile_count = justfile_hostiles()
        counterexample_count = counterexample_hostiles()
        policy_count = policy_hostiles()
        receipt_count = receipt_hostiles()
        receipt_derivation_count = receipt_derivation_guard_hostiles()
        receipt_fd_count = receipt_fd_hostiles()
        schema_count = schema_hostiles()
        topology_count = topology_guard_hostiles()
        lean_cut_count = lean_r12_cut_hostiles()
        result = {
            "counterexample_mutations_rejected": counterexample_count,
            "hosted_capture_source_mutations_rejected": capture_source_count,
            "local_repair_mutations_rejected": local_count,
            "local_recipe_mutations_rejected": justfile_count,
            "lean_checksum_cut_mutations_rejected": lean_cut_count,
            "path_policy_mutations_rejected": policy_count,
            "receipt_mutations_rejected": receipt_count,
            "receipt_derivation_guard_mutations_rejected": receipt_derivation_count,
            "receipt_fd_mutations_rejected": receipt_fd_count,
            "schema_mutations_rejected": schema_count,
            "topology_guard_mutations_rejected": topology_count,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v7-self-test/v1",
            "workflow_dependency_mutations_rejected": workflow_count,
        }
        sys.stdout.buffer.write(V7.canonical_json(result, pretty=False))
        return 0
    except (V7.ContractError, OSError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
