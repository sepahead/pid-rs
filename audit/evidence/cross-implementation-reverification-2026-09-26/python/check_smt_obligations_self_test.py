#!/usr/bin/env python3
# Author: Sepehr Mahmoudian, 2026.
"""Synthetic/profile controls for the adjacent nine-file SMT checker.

Usage: check_smt_obligations_self_test.py <source-root>

This suite never launches Z3. It reads the current nine proof sources, mutates copies
in memory or a temporary fixture tree, and mocks subprocess results. Real solver
baseline and semantic-mutant checks are separate execution obligations.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_smt_obligations_self_test.py <source-root>")
        return 1
    root = Path(sys.argv[1])
    checker_path = Path(__file__).with_name("check_smt_obligations.py")
    spec = importlib.util.spec_from_file_location("smt_obligations_under_test", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent checker")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    successes = 0
    rejections = 0

    def expect(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(message)

    def accept(name, action):
        nonlocal successes
        value = action()
        successes += 1
        return value

    def reject(name, action):
        nonlocal rejections
        try:
            action()
        except checker.CheckError:
            rejections += 1
            return
        raise RuntimeError(f"false acceptance: {name}")

    def serialize(forms):
        return "\n".join(checker.render(form) for form in forms) + "\n"

    sources = accept("exact nine-source inventory", lambda: checker.read_sources(root))
    parsed = {}
    for relative, text in sources.items():
        parsed[relative] = accept(relative, lambda r=relative, t=text: checker.validate_source(r, t))
    path = checker.PID3_PATH
    forms, goal_index, assertions = parsed[path]
    expect(assertions == 1, "PID3 reconstruction assertion count changed")
    accept("current +1 zeta sums", lambda: checker.check_pid3_order(forms))
    accept("optional final exit", lambda: checker.validate_source(path, serialize(forms[:-1])))
    accept("comments and whitespace", lambda: checker.validate_source(path, "; ( ignored\n" + sources[path] + "\n; ignored )"))

    with_false = forms[:goal_index] + [("assert", "false")] + forms[goal_index:]
    false_profile = accept("contradictory background remains syntactically visible",
                           lambda: checker.validate_source(path, serialize(with_false)))
    background = checker.background_source(false_profile[0], false_profile[1])
    expect(("assert", "false") in checker.parse_smt(background),
           "background transformation discarded false premise")
    expect(forms[goal_index] not in checker.parse_smt(background),
           "background transformation retained negated goal")

    source_mutations = {
        "stray text": sources[path] + "rogue",
        "unclosed parenthesis": sources[path] + "(",
        "extra closing parenthesis": sources[path] + ")",
        "unterminated string": sources[path] + '"broken',
        "quoted identifier": serialize(forms[:3] + [("declare-const", "|quoted|", "Real")] + forms[3:]),
        "non-ASCII": "; \u03bb\n" + sources[path],
        "wrong logic": sources[path].replace("QF_LRA", "QF_NRA", 1),
        "missing goal": serialize(forms[:goal_index] + forms[goal_index + 1:]),
        "duplicate goal": serialize(forms[:goal_index] + [forms[goal_index]] + forms[goal_index:]),
        "goal moved before declarations": serialize(forms[:3] + [forms[goal_index]] + forms[3:goal_index] + forms[goal_index + 1:]),
        "duplicate declaration": serialize(forms[:4] + [forms[3]] + forms[4:]),
        "unknown symbol before exit": sources[path].replace("(exit)", "(assert unknown_audit_symbol)\n(exit)"),
        "form after exit": sources[path] + "(assert false)\n",
        "two queries": sources[path].replace("(check-sat)", "(check-sat)\n(check-sat)"),
        "missing query": sources[path].replace("(check-sat)", ""),
        "argument to query": sources[path].replace("(check-sat)", "(check-sat false)"),
        "reset and additional query": sources[path].replace("(exit)", "(reset)\n(check-sat)\n(exit)"),
        "duplicate exit": sources[path] + "(exit)\n",
    }
    for name, command in {
        "push": ("push", "1"),
        "pop": ("pop", "1"),
        "reset": ("reset",),
        "echo": ("echo", '"sat"'),
        "include": ("include", '"other.smt2"'),
        "solver option": ("set-option", ":print-success", "true"),
        "unknown command": ("unknown_command",),
    }.items():
        source_mutations[name] = serialize(forms[:3] + [command] + forms[3:])
    for name, mutant in source_mutations.items():
        reject(name, lambda m=mutant: checker.validate_source(path, m))

    recovered_index = next(index for index, form in enumerate(forms)
                           if form[:2] == ("define-fun", "recovered_001"))
    recovered = forms[recovered_index]
    terms = recovered[4][1:]

    def changed_zeta(body):
        return forms[:recovered_index] + [recovered[:4] + (body,)] + forms[recovered_index + 1:]

    zeta_mutations = {
        "removed atom": ("+", *terms[1:]),
        "repeated atom": ("+", *terms, terms[0]),
        "wrong atom": ("+", "atom_111", *terms[1:]),
        "negative term": ("+", ("-", terms[0]), *terms[1:]),
        "scaled term": ("+", ("*", "2", terms[0]), *terms[1:]),
        "extra zero constant": ("+", *terms, "0"),
        "subtraction instead of addition": ("-", *terms),
        "nested sum": ("+", ("+", terms[0], terms[1]), *terms[2:]),
    }
    for name, body in zeta_mutations.items():
        reject(name, lambda b=body: checker.check_pid3_order(changed_zeta(b)))
    duplicate_recovered = forms[:recovered_index] + [recovered] + forms[recovered_index:]
    reject("duplicate recovered in source", lambda: checker.validate_source(path, serialize(duplicate_recovered)))
    reject("duplicate recovered in zeta reader", lambda: checker.check_pid3_order(duplicate_recovered))

    def negate_use(node):
        if isinstance(node, str):
            return ("-", node) if node == "atom_001" else node
        return tuple(negate_use(child) for child in node)

    coordinated = []
    for form in forms:
        if form[:2] == ("define-fun", "atom_001"):
            coordinated.append(form[:4] + (("-", "cap_001_110", "cap_001"),))
        elif form[0] == "define-fun" and form[1].startswith("recovered_"):
            coordinated.append(form[:4] + (negate_use(form[4]),))
        else:
            coordinated.append(form)
    accept("coordinated sign mutant remains in the source grammar",
           lambda: checker.validate_source(path, serialize(coordinated)))
    reject("coordinated sign mutant is not a +1 zeta sum", lambda: checker.check_pid3_order(coordinated))

    def process(code=0, stdout=b"unsat\n", stderr=b""):
        return subprocess.CompletedProcess(["synthetic-z3"], code, stdout, stderr)

    accept("clean UNSAT protocol", lambda: checker.require_exact_result(process(), "unsat", "control"))
    accept("clean SAT protocol", lambda: checker.require_exact_result(process(stdout=b"sat\n"), "sat", "control"))
    accept("clean version protocol", lambda: checker.require_exact_result(process(stdout=(checker.EXPECTED_Z3 + "\n").encode()), checker.EXPECTED_Z3, "control"))
    bad_results = {
        "nonzero after expected token": process(code=1),
        "stderr after expected token": process(stderr=b"warning\n"),
        "solver error after expected token": process(stdout=b'unsat\n(error "bad")\n'),
        "additional result": process(stdout=b"unsat\nsat\n"),
        "unknown": process(stdout=b"unknown\n"),
        "empty output": process(stdout=b""),
        "unterminated result line": process(stdout=b"unsat"),
        "leading whitespace": process(stdout=b" unsat\n"),
        "trailing blank line": process(stdout=b"unsat\n\n"),
        "SAT in an UNSAT lane": process(stdout=b"sat\n"),
    }
    for name, result in bad_results.items():
        reject(name, lambda p=result: checker.require_exact_result(p, "unsat", "control"))
    reject("contradictory background UNSAT", lambda: checker.require_exact_result(process(), "sat", "background"))
    reject("version error despite correct line",
           lambda: checker.require_exact_result(process(code=1, stdout=(checker.EXPECTED_Z3 + "\n").encode()), checker.EXPECTED_Z3, "version"))

    for name, error in {
        "wall timeout": subprocess.TimeoutExpired(["z3"], checker.TIMEOUT_SECONDS),
        "missing solver": OSError("synthetic missing solver"),
    }.items():
        with mock.patch.object(checker.subprocess, "run", side_effect=error):
            reject(name, lambda: checker.invoke_z3(["--version"]))

    calls = []

    def fake_run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        expect(kwargs.get("timeout") == checker.TIMEOUT_SECONDS, "wall timeout missing")
        expect(kwargs.get("capture_output") is True and kwargs.get("check") is False,
               "subprocess capture contract changed")
        if arguments == ["z3", "--version"]:
            return process(stdout=(checker.EXPECTED_Z3 + "\n").encode())
        expect(arguments == ["z3", "-T:120", "-smt2", "-in"], "solver arguments changed")
        data = kwargs.get("input")
        expect(isinstance(data, bytes), "solver input must be captured bytes")
        solver_forms = checker.parse_smt(data.decode("ascii"))
        negative = any(form[0] == "assert" and isinstance(form[1], tuple)
                       and form[1] and form[1][0] == "not" for form in solver_forms)
        return process(stdout=b"unsat\n" if negative else b"sat\n")

    output = io.StringIO()
    with mock.patch.object(checker.subprocess, "run", side_effect=fake_run), contextlib.redirect_stdout(output):
        accept("baseline reporting with synthetic solver protocol", lambda: checker.check_root(root))
    # The source root can be an older export without this evidence package.
    # Reporting expectations belong to the adjacent checker, not to that export.
    retained = checker_path.parent.parent / "results/check_smt_obligations.txt"
    expect(output.getvalue() == retained.read_text(), "current nine-file output changed")
    expect(len(calls) == 19, "expected one version check and eighteen solver invocations")

    with tempfile.TemporaryDirectory(prefix="pid-smt-profile-controls-") as temporary:
        fixture = Path(temporary)
        for relative, text in sources.items():
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        accept("copied exact inventory", lambda: checker.read_sources(fixture))
        target = fixture / path
        original = target.read_bytes()
        target.unlink()
        reject("missing declared file", lambda: checker.read_sources(fixture))
        target.write_bytes(original)
        extra = target.with_name("replacement.smt2")
        extra.write_bytes(original)
        reject("extra proof file", lambda: checker.read_sources(fixture))
        target.unlink()
        reject("same-count substituted filename", lambda: checker.read_sources(fixture))
        link_destination = fixture / "linked-proof-preimage.smt2"
        link_destination.write_bytes(original)
        target.symlink_to(link_destination)
        extra.unlink()
        reject("symlinked proof file", lambda: checker.read_sources(fixture))
        target.unlink()
        target.mkdir()
        reject("directory instead of proof file", lambda: checker.read_sources(fixture))
        target.rmdir()
        target.write_bytes(original)
        directory = target.parent
        moved = directory.with_name(directory.name + "-real")
        directory.rename(moved)
        directory.symlink_to(moved.name, target_is_directory=True)
        reject("symlinked proof directory", lambda: checker.read_sources(fixture))

    print(f"PASS: {successes} accepted and {rejections} rejected synthetic/profile controls; no solver execution")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"FAIL: {error}")
        sys.exit(1)
