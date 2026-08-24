#!/usr/bin/env python3
"""Hostile controls for the terminal composite-v12 preservation checker."""

from __future__ import annotations

import sys


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-m1a-composite-v12-terminal-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import copy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Callable


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER_PATH = ROOT / "scripts/check-ksg-m1a-composite-v12-terminal.py"


class SelfTestError(RuntimeError):
    """A positive control failed or a hostile mutation survived."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_checker():
    name = "pid_rs_ksg_m1a_composite_v12_terminal_self_test_subject"
    specification = importlib.util.spec_from_file_location(name, CHECKER_PATH)
    require(
        specification is not None and specification.loader is not None,
        "checker import specification",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except (RuntimeError, ValueError):
        return
    raise SelfTestError(f"hostile control passed: {label}")


def mutate(
    value: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> dict[str, Any]:
    changed = copy.deepcopy(value)
    operation(changed)
    return changed


def record_controls(checker, record: dict[str, Any]) -> int:
    checker.validate_record_semantics(record)
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "L12 over-adjudicated",
            lambda item: item["qualification"].update(l12="failed"),
        ),
        ("Q12 revived", lambda item: item["qualification"].update(q12=True)),
        ("R12 issued", lambda item: item["qualification"].update(r12="issued")),
        (
            "CI failure promoted",
            lambda item: item["qualification"].update(
                ci12_attempt_1="terminal_success"
            ),
        ),
        (
            "dedicated failure promoted",
            lambda item: item["qualification"].update(
                dedicated12_attempt_1="terminal_success"
            ),
        ),
        (
            "CodeQL result demoted",
            lambda item: item["qualification"].update(
                codeql12_attempt_1="terminal_failure"
            ),
        ),
        (
            "qualification credit granted",
            lambda item: item["qualification"].update(
                hosted_qualification_credit="partial"
            ),
        ),
        (
            "CI retry substituted",
            lambda item: item["hosted_attempt_1"]["repository_ci"].update(
                run_attempt=2
            ),
        ),
        (
            "dedicated run made nonterminal",
            lambda item: item["hosted_attempt_1"]["dedicated_v12"].update(
                status="in_progress"
            ),
        ),
        (
            "CodeQL SHA substituted",
            lambda item: item["hosted_attempt_1"]["codeql"].update(head_sha="0" * 40),
        ),
        (
            "dedicated log digest changed",
            lambda item: item["hosted_attempt_1"]["dedicated_v12"]["failed_jobs"][0][
                "log_retrieval"
            ].update(sha256="0" * 64),
        ),
        (
            "CI log size changed",
            lambda item: item["hosted_attempt_1"]["repository_ci"]["failed_jobs"][0][
                "log_retrieval"
            ].update(size_bytes=15_675),
        ),
        (
            "hosted mode guessed",
            lambda item: item["hosted_attempt_1"]["dedicated_v12"]["failed_jobs"][
                0
            ].update(mode_or_cause_adjudication="mode_0600"),
        ),
        (
            "secret scan pre-adjudicated",
            lambda item: item["hosted_attempt_1"]["repository_ci"]["failed_jobs"][
                3
            ].update(finding_adjudication="false_positive"),
        ),
        (
            "failed job reordered",
            lambda item: item["hosted_attempt_1"]["repository_ci"][
                "failed_jobs"
            ].reverse(),
        ),
        ("C12 tree changed", lambda item: item["subject"].update(c12_tree="0" * 40)),
        (
            "C12 delta changed",
            lambda item: item["subject"]["c12_delta_paths"][0].update(change="A"),
        ),
        (
            "historical checker digest changed",
            lambda item: item["historical_c12_source"]["sources"][1].update(
                sha256="0" * 64
            ),
        ),
        (
            "R12 evidence path removed",
            lambda item: item["custody"]["forbidden_r12_evidence_paths"].pop(),
        ),
        (
            "raw logs falsely retained",
            lambda item: item["custody"].update(raw_logs_retained_in_repository=True),
        ),
        (
            "nonimplication removed",
            lambda item: item["nonimplications"].pop(),
        ),
    ]
    for label, operation in mutations:
        changed = mutate(record, operation)
        expect_rejection(
            lambda changed=changed: checker.validate_record_semantics(changed), label
        )
    return len(mutations)


def schema_controls(checker, schema: dict[str, Any]) -> int:
    checker.validate_schema_semantics(schema)
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "open root",
            lambda item: item.update(additionalProperties=True),
        ),
        (
            "open terminal run",
            lambda item: item["$defs"]["terminalRun"].update(additionalProperties=True),
        ),
        (
            "L12 schema over-adjudicated",
            lambda item: item["properties"]["qualification"]["const"].update(
                l12="failed"
            ),
        ),
        (
            "C12 schema tree changed",
            lambda item: item["properties"]["subject"]["properties"]["c12_tree"].update(
                const="0" * 40
            ),
        ),
        (
            "R12 message schema changed",
            lambda item: item["properties"]["custody"]["properties"][
                "forbidden_r12_message"
            ].update(const="Record replacement\n"),
        ),
        (
            "required root field removed",
            lambda item: item["required"].pop(),
        ),
    ]
    for label, operation in mutations:
        changed = mutate(schema, operation)
        expect_rejection(
            lambda changed=changed: checker.validate_schema_semantics(changed), label
        )
    return len(mutations)


def schema_instance_controls(
    checker, record: dict[str, Any], schema: dict[str, Any]
) -> int:
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "extra CodeQL field",
            lambda item: item["hosted_attempt_1"]["codeql"].update(extra=True),
        ),
        (
            "extra failed-job field",
            lambda item: item["hosted_attempt_1"]["repository_ci"]["failed_jobs"][
                0
            ].update(extra=True),
        ),
        (
            "extra log-retrieval field",
            lambda item: item["hosted_attempt_1"]["dedicated_v12"]["failed_jobs"][0][
                "log_retrieval"
            ].update(extra=True),
        ),
        (
            "missing terminal timestamp",
            lambda item: item["hosted_attempt_1"]["repository_ci"].pop("updated_at"),
        ),
    ]
    for label, operation in mutations:
        changed = mutate(record, operation)
        expect_rejection(
            lambda changed=changed: checker.validate_json_schema(changed, schema), label
        )
    return len(mutations)


def history_controls(checker, record_raw: bytes) -> int:
    original_git = checker.git
    original_git_success = checker.git_success
    original_tree_entry = checker.tree_entry
    introduction = "a" * 40
    descendant = "b" * 40
    expected_oid = "c" * 40
    state = {
        "introductions": [introduction],
        "descendants": [descendant],
        "entries": {
            (introduction, checker.RECORD): ("100644", expected_oid),
            (descendant, checker.RECORD): ("100644", expected_oid),
        },
    }

    def fake_git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
        if arguments[:4] == ("hash-object", "-t", "blob", "--stdin"):
            require(input_bytes == record_raw, "history hash input")
            return (expected_oid + "\n").encode("ascii")
        if arguments[:3] == ("log", "--format=%H", "--diff-filter=A"):
            return (
                "\n".join(state["introductions"])
                + ("\n" if state["introductions"] else "")
            ).encode("ascii")
        if arguments[:2] == ("rev-list", "--ancestry-path"):
            return (
                "\n".join(state["descendants"]) + ("\n" if state["descendants"] else "")
            ).encode("ascii")
        raise SelfTestError(f"unexpected fake Git call: {arguments}")

    try:
        checker.git = fake_git
        checker.git_success = lambda *arguments: True
        checker.tree_entry = lambda commit, path: state["entries"].get((commit, path))
        require(
            checker.verify_record_history(record_raw, descendant)
            == "committed_preservation",
            "committed history positive control",
        )
        rejected = 0

        state["introductions"] = [introduction, "d" * 40]
        expect_rejection(
            lambda: checker.verify_record_history(record_raw, descendant),
            "multiple record introductions",
        )
        rejected += 1

        state["introductions"] = [introduction]
        state["entries"][(descendant, checker.RECORD)] = ("100644", "e" * 40)
        expect_rejection(
            lambda: checker.verify_record_history(record_raw, descendant),
            "changed descendant record",
        )
        rejected += 1

        state["introductions"] = []
        checker.tree_entry = lambda commit, path: None
        expect_rejection(
            lambda: checker.verify_record_history(record_raw, descendant),
            "uncommitted record on descendant",
        )
        rejected += 1

        require(
            checker.verify_record_history(record_raw, checker.C12)
            == "authoring_pending_introduction",
            "exact-C12 authoring positive control",
        )
        return rejected
    finally:
        checker.git = original_git
        checker.git_success = original_git_success
        checker.tree_entry = original_tree_entry


def main() -> int:
    try:
        checker = load_checker()
        record_raw = (ROOT / checker.RECORD).read_bytes()
        schema_raw = (ROOT / checker.SCHEMA).read_bytes()
        record = json.loads(record_raw)
        schema = json.loads(schema_raw)
        record_rejections = record_controls(checker, record)
        schema_rejections = schema_controls(checker, schema)
        schema_instance_rejections = schema_instance_controls(checker, record, schema)
        history_rejections = history_controls(checker, record_raw)
        checker.validate_json_schema(record, schema)
        result = {
            "history_mutations_rejected": history_rejections,
            "record_mutations_rejected": record_rejections,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v12-terminal-self-test/v1",
            "schema_instance_mutations_rejected": schema_instance_rejections,
            "schema_mutations_rejected": schema_rejections,
            "total_mutations_rejected": (
                history_rejections
                + record_rejections
                + schema_instance_rejections
                + schema_rejections
            ),
        }
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
