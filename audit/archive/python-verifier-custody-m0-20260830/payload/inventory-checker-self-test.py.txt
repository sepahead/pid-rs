#!/usr/bin/env python3
"""Hostile and worked-fixture tests for the bounded Python custody inventory."""

from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import types


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-python-verifier-custody-inventory.py"


def stat_identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def load_checker_from_exact_source() -> types.ModuleType:
    before = os.lstat(CHECKER)
    source = CHECKER.read_bytes()
    after = os.lstat(CHECKER)
    if stat_identity(before) != stat_identity(after) or len(source) != before.st_size:
        raise SystemExit("custody checker changed during exact-source read")
    module = types.ModuleType("python_verifier_custody_inventory_under_test")
    module.__file__ = str(CHECKER)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    setattr(module, "__cached__", None)
    code = compile(
        source,
        str(CHECKER),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    sys.modules[module.__name__] = module
    exec(code, module.__dict__)
    return module


checker = load_checker_from_exact_source()


def check_isolated_cli_with_hostile_git_environment() -> None:
    arguments = [sys.executable]
    if sys.flags.optimize:
        arguments.append("-O")
    arguments.extend(("-I", "-S", "-B", str(CHECKER)))
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/does/not/exist",
            "GIT_DIR": "/does/not/exist",
            "GIT_NAMESPACE": "hostile",
            "GIT_OBJECT_DIRECTORY": "/does/not/exist",
            "GIT_REPLACE_REF_BASE": "refs/hostile/",
            "GIT_WORK_TREE": "/does/not/exist",
        }
    )
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stderr:
        raise SystemExit(
            "isolated checker did not scrub hostile Git routing: "
            f"{completed.stderr.strip()}"
        )


check_isolated_cli_with_hostile_git_environment()
schema, _ = checker.load_json(checker.DEFAULT_SCHEMA, "registry schema", canonical=True)
registry, _ = checker.load_json(
    checker.DEFAULT_REGISTRY, "Python custody registry", canonical=True
)
expected = checker.build_registry(ROOT)
checker.validate_registry(registry, schema, expected, ROOT)


rejections = 0
semantic_rejections = 0


def reject_exact(label: str, mutation: dict[str, object]) -> None:
    global rejections
    try:
        checker.validate_semantics(mutation)
    except checker.InventoryError:
        rejections += 1
        return
    if checker.canonical_bytes(mutation) != checker.canonical_bytes(expected):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile registry mutation passed")


def reject_semantic(label: str, mutation: dict[str, object]) -> None:
    global semantic_rejections
    try:
        checker.validate_semantics(mutation)
    except checker.InventoryError:
        semantic_rejections += 1
        return
    raise SystemExit(f"{label}: semantic escalation passed")


mutation = copy.deepcopy(registry)
mutation["format"] = "pid-rs/python-verifier-custody-registry/v2"
reject_exact("format escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["review_revision"]["commit"] = "0" * 40
reject_exact("review commit rebind", mutation)

mutation = copy.deepcopy(registry)
mutation["review_revision"]["tree"] = "0" * 40
reject_exact("review tree rebind", mutation)

mutation = copy.deepcopy(registry)
mutation["bootstrap"]["checker_source_binding"] = "closed"
reject_exact("bootstrap placeholder erased", mutation)

mutation = copy.deepcopy(registry)
mutation["bootstrap"]["status"] = "closed"
reject_semantic("bootstrap closure escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["tracked_python_file_count"] -= 1
reject_exact("tracked count drift", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["tracked_python_ast_status_counts"]["parsed"] -= 1
reject_exact("tracked AST-status count drift", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["python_source_paths"].pop()
reject_semantic("path-list truncation", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["python_source_path_list_sha256"] = "0" * 64
reject_semantic("path-list digest rebind", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["dynamic_primitive_counts"]["compile"] += 1
reject_exact("dynamic count inflation", mutation)

mutation = copy.deepcopy(registry)
mutation["inventory"]["operational_roots"][0]["sha256"] = "0" * 64
reject_exact("operational root byte rebind", mutation)

mutation = copy.deepcopy(registry)
mutation["python_sources"][0]["content"]["sha256"] = "0" * 64
reject_exact("source byte rebind", mutation)

mutation = copy.deepcopy(registry)
mutation["python_sources"][0]["status"] = "closed"
reject_semantic("source closure escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["python_sources"][0]["ast"]["other_call_resolution_status"] = "closed"
reject_semantic("unselected-call closure escalation", mutation)

import_source_index = next(
    index
    for index, source in enumerate(registry["python_sources"])
    if source["import_edges"]
)
mutation = copy.deepcopy(registry)
mutation["python_sources"][import_source_index]["import_edges"][0][
    "execution_resolution_status"
] = "closed"
reject_semantic("import resolution escalation", mutation)

dynamic_source_index = next(
    index
    for index, source in enumerate(registry["python_sources"])
    if source["dynamic_edges"]
)
mutation = copy.deepcopy(registry)
mutation["python_sources"][dynamic_source_index]["dynamic_edges"][0][
    "resolution_status"
] = "closed"
reject_semantic("dynamic resolution escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["launch_edges"][0]["execution_custody_status"] = "closed"
reject_semantic("launch custody escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["launch_edges"][0]["source_kind"] = "module_tool"
reject_semantic("launch source-kind mismatch", mutation)

mutation = copy.deepcopy(registry)
mutation["launch_edges"][0]["id"] = "launch-99999"
reject_semantic("launch ordering drift", mutation)

mutation = copy.deepcopy(registry)
mutation["launch_edges"][0]["source_id"] = "file:not-present.py"
reject_semantic("unknown launch source", mutation)

mutation = copy.deepcopy(registry)
mutation["closure_claims"][0]["status"] = "closed"
reject_semantic("official projection closure escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["closure_claims"][1]["status"] = "closed"
reject_semantic("repository projection closure escalation", mutation)

mutation = copy.deepcopy(registry)
mutation["closure_claims"].reverse()
reject_semantic("projection order mutation", mutation)

mutation = copy.deepcopy(registry)
mutation["nonimplications"].pop()
reject_exact("nonimplication erasure", mutation)

mutation = copy.deepcopy(registry)
mutation["unexpected"] = True
reject_exact("unknown top-level field", mutation)

schema_mutation = copy.deepcopy(schema)
schema_mutation["unsupported_assertion"] = True
schema_error, validate_schema = checker.load_schema_validator(ROOT)
try:
    validate_schema(registry, schema_mutation, name="hostile registry schema")
except schema_error:
    rejections += 1
else:
    raise SystemExit("unsupported schema assertion was silently accepted")


fixture_source = b"""\
import json
import json_schema_subset
import numpy as np
import unavailable_name
compile(raw, name, 'exec')
exec(code)
__import__('os')
loader.spec_from_file_location('fixture', path)
loader.module_from_spec(spec)
alias = compile
alias(raw, name, 'exec')
"""
details, imports, dynamics, fixture_tree = checker.ast_details(
    "dynamic_fixture:self-test", "self-test.py", fixture_source
)
if details["status"] != "parsed" or fixture_tree is None:
    raise SystemExit("worked AST fixture did not parse")
classes = {edge["root_name"]: edge["class"] for edge in imports}
expected_classes = {
    "json": "stdlib_profile",
    "json_schema_subset": "local_candidate",
    "numpy": "third_party_declared",
    "unavailable_name": "unresolved_open_blocking",
}
if classes != expected_classes:
    raise SystemExit(f"worked import classes differ: {classes}")
primitive_counts: dict[str, int] = {}
for edge in dynamics:
    primitive_counts[edge["primitive_name"]] = (
        primitive_counts.get(edge["primitive_name"], 0) + 1
    )
if primitive_counts != {
    "__import__": 1,
    "compile": 1,
    "exec": 1,
    "module_from_spec": 1,
    "spec_from_file_location": 1,
}:
    raise SystemExit(f"worked dynamic classes differ: {primitive_counts}")
if (
    details["other_call_count"] != 1
    or details["other_call_resolution_status"] != "open_blocking"
):
    raise SystemExit("aliased dynamic call was not retained as an open call")


command_cases = (
    (
        "python3 scripts/check-method-catalog.py",
        "file",
        "scripts/check-method-catalog.py",
    ),
    ("python3 -c 'import sys'", "inline_argv", None),
    ("python3 -m pytest -q", "module_tool", None),
    ("python3 - <<'PY'", "inline_stdin", None),
    ("python3 $CHECKER", "dynamic_fixture", None),
)
python_paths = set(registry["inventory"]["python_source_paths"])
for fragment, expected_kind, expected_path in command_cases:
    kind, path, _, _ = checker.classify_command_source(fragment, python_paths)
    if (kind, path) != (expected_kind, expected_path):
        raise SystemExit(f"command fixture {fragment!r} classified as {(kind, path)!r}")
if checker.INVOCATION_RE.search("pid-python") is not None:
    raise SystemExit("hyphenated package name was misclassified as a Python command")


native_tree = ast.parse(
    "import subprocess, sys\nsubprocess.run([sys.executable, 'tool.py'])\n"
)
native_call = next(node for node in ast.walk(native_tree) if isinstance(node, ast.Call))
if checker.callable_name(native_call.func) != "subprocess.run":
    raise SystemExit("native subprocess fixture lost its callable name")
if not checker.has_python_runtime_reference(native_call):
    raise SystemExit("native subprocess fixture did not expose sys.executable")


false_positive_tree = ast.parse("obj.spec_from_file_location('x', y)\n")
false_positive_call = next(
    node for node in ast.walk(false_positive_tree) if isinstance(node, ast.Call)
)
_, _, false_positive_dynamics, _ = checker.ast_details(
    "dynamic_fixture:false-positive",
    "false-positive.py",
    b"obj.spec_from_file_location('x', y)\n",
)
if (
    len(false_positive_dynamics) != 1
    or false_positive_dynamics[0]["resolution_status"] != "open_blocking"
):
    raise SystemExit("selected attribute false-positive boundary was not fail-closed")
if checker.callable_name(false_positive_call.func) != "obj.spec_from_file_location":
    raise SystemExit("selected attribute fixture lost its qualified spelling")


observed = registry["inventory"]
expected_dynamic = {
    "__import__": 2,
    "compile": 50,
    "exec": 49,
    "module_from_spec": 32,
    "spec_from_file_location": 32,
}
if observed["tracked_python_file_count"] != 186:
    raise SystemExit("selected-base Python count changed unexpectedly")
if observed["tracked_python_ast_status_counts"] != {"parsed": 186}:
    raise SystemExit("selected-base tracked-file AST status changed unexpectedly")
if observed["ast_status_counts"] != {
    "not_available_open_blocking": 312,
    "parsed": 332,
    "syntax_error_open_blocking": 18,
}:
    raise SystemExit("selected-base all-source AST status census changed unexpectedly")
if observed["tracked_file_import_statement_count"] != 2110:
    raise SystemExit("selected-base import-statement count changed unexpectedly")
if observed["tracked_file_import_edge_count"] != 2295:
    raise SystemExit("selected-base imported-binding count changed unexpectedly")
if observed["tracked_file_third_party_import_statement_count"] != 26:
    raise SystemExit(
        "selected-base third-party import-statement count changed unexpectedly"
    )
if observed["tracked_file_third_party_import_edge_count"] != 65:
    raise SystemExit(
        "selected-base third-party imported-binding count changed unexpectedly"
    )
if observed["tracked_file_third_party_import_file_count"] != 11:
    raise SystemExit(
        "selected-base third-party importing-file count changed unexpectedly"
    )
if observed["tracked_file_dynamic_primitive_counts"] != expected_dynamic:
    raise SystemExit("selected-base dynamic primitive census changed unexpectedly")
if observed["tracked_file_dynamic_edge_count"] != 165:
    raise SystemExit("selected-base dynamic count changed unexpectedly")


print(
    json.dumps(
        {
            "format": "pid-rs/python-verifier-custody-inventory-self-test/v1",
            "hostile_registry_rejections": rejections,
            "semantic_escalation_rejections": semantic_rejections,
            "worked_command_kinds": len(command_cases),
            "worked_dynamic_primitives": sum(primitive_counts.values()),
            "worked_import_classes": len(classes),
            "selected_attribute_false_positive_retained_open": True,
            "selected_base_python_files": observed["tracked_python_file_count"],
            "selected_base_dynamic_edges": observed["tracked_file_dynamic_edge_count"],
            "selected_base_import_edges": observed["tracked_file_import_edge_count"],
            "optimized": bool(sys.flags.optimize),
            "status": "all bounded hostile and worked-fixture checks passed",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
)
