#!/usr/bin/env python3
"""Hostiles for C9's binding, fixture, and exact-CPython operational repairs."""

from __future__ import annotations

import sys


if not (
    sys.implementation.name == "cpython"
    and sys.version_info == (3, 14, 6, "final", 0)
    and sys._is_gil_enabled()
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v9-self-test.py requires GIL-enabled CPython 3.14.6 -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)

import ast
import copy
import hashlib
import os
from pathlib import Path
import re
import types
from typing import Any, Callable


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v9.py"
checker_raw = CHECKER.read_bytes()
CHECKER_SHA256 = hashlib.sha256(checker_raw).hexdigest()
CHECKER_SIZE_BYTES = len(checker_raw)


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(2)


def validate_checker_bootstrap(raw: bytes) -> None:
    """Independently reject direct pre-validation success exits in checker source."""

    try:
        module = ast.parse(raw, filename=os.fspath(CHECKER), mode="exec")
    except (SyntaxError, ValueError) as error:
        print(f"ERROR: cannot parse composite-v9 checker: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    expected_footer = ast.parse(
        'if __name__ == "__main__":\n    raise SystemExit(main())'
    ).body[0]
    expected_guard = ast.parse(
        """if not (
    sys.implementation.name == "cpython"
    and sys.version_info == (3, 14, 6, "final", 0)
    and sys._is_gil_enabled()
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v9.py requires GIL-enabled CPython 3.14.6 -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)"""
    ).body[0]
    footer = module.body[-1] if module.body else None
    direct_tries = [node for node in module.body if isinstance(node, ast.Try)]
    direct_controls = [
        node
        for node in module.body
        if isinstance(
            node,
            (
                ast.If,
                ast.Try,
                ast.TryStar,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.With,
                ast.AsyncWith,
                ast.Match,
                ast.Raise,
            ),
        )
    ]
    bootstrap_require(
        len(module.body) > 4
        and ast.dump(module.body[3], include_attributes=False)
        == ast.dump(expected_guard, include_attributes=False)
        and isinstance(footer, ast.If)
        and ast.dump(footer, include_attributes=False)
        == ast.dump(expected_footer, include_attributes=False)
        and direct_controls == [module.body[3], *direct_tries, footer]
        and len(direct_tries) == 1
        and [node for node in module.body if isinstance(node, ast.Expr)]
        == [module.body[0]],
        "composite-v9 checker bootstrap control-flow changed",
    )

    raises: list[ast.Raise] = []
    exit_calls: list[ast.Call] = []
    main_calls: list[ast.Call] = []
    call_roster: list[str] = []
    import_roster: list[str] = []

    def dotted_name(node: ast.AST) -> str | None:
        parts: list[str] = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if not isinstance(current, ast.Name):
            return None
        parts.append(current.id)
        return ".".join(reversed(parts))

    class ModuleExecution(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            for decorator in node.decorator_list:
                self.visit(decorator)
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

        def visit_Raise(self, node: ast.Raise) -> None:
            raises.append(node)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            name = dotted_name(node.func)
            call_roster.append(name or "<computed>")
            if name in {"SystemExit", "sys.exit", "exit", "quit", "os._exit"}:
                exit_calls.append(node)
            if name == "main":
                main_calls.append(node)
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            import_roster.append(
                "import:"
                + ",".join(
                    alias.name + (f" as {alias.asname}" if alias.asname else "")
                    for alias in node.names
                )
            )

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            import_roster.append(
                f"from:{node.level}:{node.module}:"
                + ",".join(
                    alias.name + (f" as {alias.asname}" if alias.asname else "")
                    for alias in node.names
                )
            )

    execution = ModuleExecution()
    for statement in module.body:
        execution.visit(statement)
    footer_raise = footer.body[0]
    failure_call = ast.parse("SystemExit(2)", mode="eval").body
    bootstrap_require(
        all(
            node is footer_raise
            or (
                isinstance(node.exc, ast.Call)
                and ast.dump(node.exc, include_attributes=False)
                == ast.dump(failure_call, include_attributes=False)
                and (
                    node.cause is None
                    or (
                        isinstance(node.cause, ast.Constant)
                        and node.cause.value is None
                    )
                )
            )
            for node in raises
        )
        and {id(node) for node in exit_calls}
        == {id(node.exc) for node in raises if isinstance(node.exc, ast.Call)}
        and main_calls == [footer_raise.exc.args[0]],
        "composite-v9 checker bootstrap terminal route changed",
    )
    bootstrap_require(
        import_roster
        == [
            "from:0:__future__:annotations",
            "import:sys",
            "import:argparse",
            "import:ast",
            "from:0:collections:defaultdict",
            "import:fcntl",
            "import:hashlib",
            "import:json",
            "import:os",
            "from:0:pathlib:Path",
            "import:re",
            "import:stat",
            "import:types",
            "from:0:typing:Any,Final",
        ]
        and call_roster
        == [
            "sys._is_gil_enabled",
            "print",
            "SystemExit",
            "Path",
            "os.path.abspath",
            "os.fspath",
            "Path",
            "sorted",
            "re.compile",
            "re.compile",
            "read_bound_v8",
            "load_bound_v8",
            "print",
            "SystemExit",
            "print",
            "SystemExit",
            "dict",
            "tuple",
            "sorted",
            "tuple",
            "frozenset",
            "SystemExit",
            "main",
        ],
        "composite-v9 checker bootstrap import or executable-call roster changed",
    )


validate_checker_bootstrap(checker_raw)
C9 = types.ModuleType("pid_rs_composite_v9_checker_self_test")
C9.__file__ = os.fspath(CHECKER)
C9.__package__ = ""
sys.modules[C9.__name__] = C9
try:
    compiled_checker = compile(
        checker_raw,
        os.fspath(CHECKER),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(compiled_checker, C9.__dict__)
except BaseException:
    print("ERROR: cannot load composite-v9 checker", file=sys.stderr)
    raise SystemExit(2) from None


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise C9.ContractError(message)


def expect_rejection(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except (C9.ContractError, OSError, SyntaxError, UnicodeError):
        return
    raise C9.ContractError(f"hostile mutation was accepted: {label}")


def replace_once(raw: bytes, before: bytes, after: bytes, label: str) -> bytes:
    require(raw.count(before) == 1, f"self-test fixture is not unique: {label}")
    return raw.replace(before, after, 1)


def semantic_workflow_validation(ci: bytes, retired: bytes, successor: bytes) -> None:
    def step_digest(raw: bytes, marker: bytes, fallback: str) -> str:
        if raw.count(marker) != 1:
            return fallback
        start = raw.index(marker)
        end = raw.find(b"      - name: ", start + len(marker))
        if end == -1:
            return fallback
        return C9.sha256(raw[start:end])

    runtime_marker = (
        b"      - name: Require the reviewed GIL-enabled CPython 3.14.6 lane\n"
    )
    workflow_pdf_marker = b"      - name: Validate the corrected fixture and unchanged C8 mathematical-workflow publication\n"
    names = (
        "CI_SHA256",
        "CI_SIZE_BYTES",
        "RETIRED_V8_WORKFLOW_SHA256",
        "RETIRED_V8_WORKFLOW_SIZE_BYTES",
        "V9_WORKFLOW_SHA256",
        "V9_WORKFLOW_SIZE_BYTES",
        "EXPECTED_V9_RUNTIME_PREFLIGHT_STEP_SHA256",
        "EXPECTED_V9_WORKFLOW_PDF_STEP_SHA256",
    )
    original = tuple(getattr(C9, name) for name in names)
    values = (
        C9.sha256(ci),
        len(ci),
        C9.sha256(retired),
        len(retired),
        C9.sha256(successor),
        len(successor),
        step_digest(
            successor,
            runtime_marker,
            C9.EXPECTED_V9_RUNTIME_PREFLIGHT_STEP_SHA256,
        ),
        step_digest(
            successor,
            workflow_pdf_marker,
            C9.EXPECTED_V9_WORKFLOW_PDF_STEP_SHA256,
        ),
    )
    try:
        for name, value in zip(names, values, strict=True):
            setattr(C9, name, value)
        C9.validate_workflow_bytes(ci, retired, successor)
    finally:
        for name, value in zip(names, original, strict=True):
            setattr(C9, name, value)


def semantic_justfile_validation(raw: bytes) -> None:
    original = C9.EXPECTED_V9_JUST_RECIPE_SHA256
    try:
        C9.EXPECTED_V9_JUST_RECIPE_SHA256 = C9.sha256(
            C9.recipe_block(raw, b"ksg-composite-v9")
        )
        C9.validate_justfile_bytes(raw)
    finally:
        C9.EXPECTED_V9_JUST_RECIPE_SHA256 = original


def semantic_workflow_fixture_validation(predecessor: bytes, successor: bytes) -> None:
    names = (
        "PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SHA256",
        "PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SIZE_BYTES",
        "WORKFLOW_PDF_SELF_TEST_SHA256",
        "WORKFLOW_PDF_SELF_TEST_SIZE_BYTES",
    )
    original = tuple(getattr(C9, name) for name in names)
    values = (
        C9.sha256(predecessor),
        len(predecessor),
        C9.sha256(successor),
        len(successor),
    )
    try:
        for name, value in zip(names, values, strict=True):
            setattr(C9, name, value)
        C9.validate_workflow_pdf_fixture_correction(predecessor, successor)
    finally:
        for name, value in zip(names, original, strict=True):
            setattr(C9, name, value)


def workflow_fixture_reconstruction_hostiles() -> int:
    predecessor = C9.tree_blob(
        C9.parse_tree(C9.C8_TREE), C9.WORKFLOW_PDF_SELF_TEST_RELATIVE
    )
    successor = (ROOT / C9.WORKFLOW_PDF_SELF_TEST_RELATIVE).read_bytes()
    C9.validate_workflow_pdf_fixture_correction(predecessor, successor)
    mutations = (
        (
            "report destinations retain restrictive fixture mode",
            b"  chmod 0644 \\\n",
            b"  chmod 0600 \\\n",
        ),
        (
            "receipt destination omitted from fixture normalization",
            b'    "$directory/root/output/pdf/workflow.pdf" \\\n'
            b'    "$directory/root/output/pdf/workflow.tsv"\n',
            b'    "$directory/root/output/pdf/workflow.pdf"\n',
        ),
        (
            "figure destinations retain restrictive fixture mode",
            b'    chmod 0644 "$directory/root/$figure_directory/$stem.pdf"\n',
            b'    chmod 0600 "$directory/root/$figure_directory/$stem.pdf"\n',
        ),
        (
            "unreviewed fifth figure fixture added",
            b"    invalidation-publication-state-machine\n  )\n",
            b"    invalidation-publication-state-machine\n"
            b"    unreviewed-fifth-stem\n  )\n",
        ),
        (
            "unrelated hostile-suite byte changed",
            b"# Refresh writer: exercise descriptor-relative success, cross-binding, object-type rejection,\n",
            b"# Refresh writer: unrelated semantic change.\n",
        ),
    )
    for label, before, after in mutations:
        hostile = replace_once(successor, before, after, label)
        expect_rejection(
            lambda hostile=hostile: semantic_workflow_fixture_validation(
                predecessor, hostile
            ),
            label,
        )
    return len(mutations)


def workflow_hostiles() -> int:
    ci = (ROOT / C9.CI_RELATIVE).read_bytes()
    retired = (ROOT / C9.RETIRED_V8_WORKFLOW_RELATIVE).read_bytes()
    successor = (ROOT / C9.V9_WORKFLOW_RELATIVE).read_bytes()
    semantic_workflow_validation(ci, retired, successor)
    mutations: list[tuple[str, bytes, bytes, bytes]] = []

    def add_ci(label: str, before: bytes, after: bytes) -> None:
        mutations.append(
            (label, replace_once(ci, before, after, label), retired, successor)
        )

    def add_retired(label: str, before: bytes, after: bytes) -> None:
        mutations.append(
            (label, ci, replace_once(retired, before, after, label), successor)
        )

    def add_successor(label: str, before: bytes, after: bytes) -> None:
        mutations.append(
            (label, ci, retired, replace_once(successor, before, after, label))
        )

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
    upload_good = b"actions/upload-artifact@" + C9.GOOD_UPLOAD_PIN.encode("ascii")
    require(ci.count(upload_good) == 3, "CI upload-pin fixture count changed")
    mutations.append(
        (
            "CI upload pin truncated",
            ci.replace(
                upload_good,
                b"actions/upload-artifact@" + C9.BAD_UPLOAD_PIN.encode("ascii"),
                1,
            ),
            retired,
            successor,
        )
    )
    add_retired(
        "retired v8 CI log binding removed",
        C9.C8_CI_RAW_LOG_SHA256.encode("ascii"),
        b"0" * 64,
    )
    add_retired(
        "retired v8 CI comparator marker removed",
        C9.CERTIFIED_FAILURE_MARKER,
        b"certified SxPID2 failure marker omitted",
    )
    add_retired(
        "retired v8 artifact absence removed",
        b"later PDF, static-contract, and artifact-upload steps were skipped",
        b"later-step disposition unknown",
    )
    add_retired(
        "retired causal-limit caveat inverted",
        b"without establishing unique counterfactual necessity or order",
        b"thereby proving unique counterfactual necessity and order",
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
        "successor fixture/publication boundary conflated",
        b"Validate the corrected fixture and unchanged C8 mathematical-workflow publication",
        b"Validate the repaired mathematical-workflow PDF publication",
    )
    add_successor(
        "successor workflow fixture restrictive umask weakened",
        b"          umask 077\n",
        b"          umask 022\n",
    )
    add_successor(
        "successor workflow fixture restrictive umask overridden later",
        b"          umask 077\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
        b"          umask 077\n"
        b"          umask 022\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
    )
    add_successor(
        "successor workflow fixture restrictive umask overridden by builtin",
        b"          umask 077\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
        b"          umask 077\n"
        b"          builtin umask 022\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
    )
    add_successor(
        "successor workflow fixture restrictive umask isolated in subshell",
        b"          set -euo pipefail\n"
        b"          umask 077\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
        b"          set -euo pipefail\n"
        b"          (\n"
        b"          umask 077\n"
        b"          )\n"
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"',
    )
    add_successor(
        "successor workflow CPython minor weakened",
        b'          python-version: "3.14.6"',
        b'          python-version: "3.11"',
    )
    add_successor(
        "successor workflow selects free-threaded CPython",
        b'          python-version: "3.14.6"',
        b'          python-version: "3.14.6"\n          freethreaded: true',
    )
    add_successor(
        "successor hosted runtime preflight omitted",
        b"Require the reviewed GIL-enabled CPython 3.14.6 lane",
        b"Omit the reviewed runtime preflight",
    )
    add_successor(
        "successor hosted runtime preflight patch weakened",
        b'sys.version_info == (3, 14, 6, "final", 0)',
        b'sys.version_info == (3, 14, 5, "final", 0)',
    )
    add_successor(
        "successor hosted runtime preflight implementation changed",
        b'sys.implementation.name == "cpython"',
        b'sys.implementation.name == "pypy"',
    )
    add_successor(
        "successor hosted runtime preflight admits a prerelease",
        b'sys.version_info == (3, 14, 6, "final", 0)',
        b'sys.version_info == (3, 14, 6, "candidate", 0)',
    )
    add_successor(
        "successor hosted runtime preflight admits a nonzero release serial",
        b'sys.version_info == (3, 14, 6, "final", 0)',
        b'sys.version_info == (3, 14, 6, "final", 1)',
    )
    add_successor(
        "successor hosted runtime preflight GIL predicate removed",
        b" and sys._is_gil_enabled() else 1)",
        b" else 1)",
    )
    add_successor(
        "successor hosted runtime preflight stranded by early exit",
        b"          set -euo pipefail\n"
        b"          python3 -I -S -B -c 'import sys; raise SystemExit",
        b"          set -euo pipefail\n"
        b"          exit 0\n"
        b"          python3 -I -S -B -c 'import sys; raise SystemExit",
    )
    add_successor(
        "successor hosted runtime preflight moved to next step",
        b"          python3 -I -S -B -c 'import sys; raise SystemExit(0 if ",
        b"          true # runtime preflight moved out of its named step\n"
        b"      - name: Illegally moved runtime preflight\n"
        b"        run: |\n"
        b"          python3 -I -S -B -c 'import sys; raise SystemExit(0 if ",
    )
    add_successor(
        "successor PDF dependency routed through an unverified alias",
        b"          python3 -m pip install \\\n",
        b"          python -m pip install \\\n",
    )
    add_successor(
        "successor workflow PDF command split into a fresh shell step",
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"\n'
        b'          gate_tmp="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-tmp"',
        b'          gate_home="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-home"\n'
        b"      - name: Illegally split the workflow-PDF commands\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          gate_tmp="$RUNNER_TEMP/pid-rs-v9-workflow-pdf-tmp"',
    )
    add_successor(
        "successor workflow PDF self-test short-circuited",
        b"          /usr/bin/env -i \\\n"
        b'            "PATH=$workflow_path" \\\n'
        b'            "HOME=$gate_home" \\\n'
        b'            "TMPDIR=$gate_tmp" \\\n'
        b"            LC_ALL=C \\\n"
        b"            LANG=C \\\n"
        b"            TZ=UTC \\\n"
        b"            bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh\n",
        b"          true || /usr/bin/env -i \\\n"
        b'            "PATH=$workflow_path" \\\n'
        b'            "HOME=$gate_home" \\\n'
        b'            "TMPDIR=$gate_tmp" \\\n'
        b"            LC_ALL=C \\\n"
        b"            LANG=C \\\n"
        b"            TZ=UTC \\\n"
        b"            bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh\n",
    )
    add_successor(
        "successor optimized action-pin self-test omitted",
        b"python3 -O -I -S -B scripts/check-github-action-pins-self-test.py",
        b"true # omitted optimized action-pin self-test",
    )
    add_successor(
        "successor upload pin truncated",
        b"actions/upload-artifact@" + C9.GOOD_UPLOAD_PIN.encode("ascii"),
        b"actions/upload-artifact@" + C9.BAD_UPLOAD_PIN.encode("ascii"),
    )
    for label, hostile_ci, hostile_retired, hostile_successor in mutations:
        expect_rejection(
            lambda a=hostile_ci, b=hostile_retired, c=hostile_successor: (
                semantic_workflow_validation(a, b, c)
            ),
            label,
        )
    return len(mutations)


def justfile_hostiles() -> int:
    raw = (ROOT / C9.JUSTFILE_RELATIVE).read_bytes()
    semantic_justfile_validation(raw)
    block = C9.recipe_block(raw, b"ksg-composite-v9")
    python_guard = (
        b"    python3 -I -S -B -c 'import sys; raise SystemExit(0 if "
        b'sys.implementation.name == "cpython" and sys.version_info == (3, 14, 6, "final", 0) '
        b"and sys._is_gil_enabled() else 1)'\n"
    )
    clean_python_guard = (
        b'    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" '
        b"HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC python3 -I -S -B -c "
        b'\'import sys; raise SystemExit(0 if sys.implementation.name == "cpython" '
        b'and sys.version_info == (3, 14, 6, "final", 0) and sys._is_gil_enabled() else 1)\'\n'
    )
    mutations = (
        (
            "local restrictive umask weakened",
            b"    umask 077\n",
            b"    umask 022\n",
        ),
        (
            "local restrictive umask overridden later",
            python_guard
            + b'    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v9.XXXXXX")"',
            python_guard + b"    umask 022\n"
            b'    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v9.XXXXXX")"',
        ),
        (
            "local restrictive umask overridden by builtin",
            python_guard
            + b'    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v9.XXXXXX")"',
            python_guard + b"    builtin umask 022\n"
            b'    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v9.XXXXXX")"',
        ),
        (
            "local restrictive umask isolated in subshell",
            b"    set -euo pipefail\n    umask 077\n" + python_guard,
            b"    set -euo pipefail\n    (\n    umask 077\n    )\n" + python_guard,
        ),
        (
            "local CPython minor weakened",
            python_guard,
            python_guard.replace(b'(3, 14, 6, "final", 0)', b'(3, 13, 7, "final", 0)'),
        ),
        (
            "local Python implementation changed",
            python_guard,
            python_guard.replace(b'== "cpython"', b'== "pypy"'),
        ),
        (
            "local CPython prerelease admitted",
            python_guard,
            python_guard.replace(b'"final", 0', b'"candidate", 0'),
        ),
        (
            "local CPython nonzero release serial admitted",
            python_guard,
            python_guard.replace(b'"final", 0', b'"final", 1'),
        ),
        (
            "local GIL predicate removed",
            python_guard,
            python_guard.replace(b" and sys._is_gil_enabled()", b""),
        ),
        (
            "local clean PDF route preflight omitted",
            clean_python_guard,
            b"    true # omitted clean PDF-route runtime preflight\n",
        ),
        (
            "local clean PDF route implementation changed",
            clean_python_guard,
            clean_python_guard.replace(b'== "cpython"', b'== "pypy"'),
        ),
        (
            "local clean PDF route patch version changed",
            clean_python_guard,
            clean_python_guard.replace(
                b'(3, 14, 6, "final", 0)', b'(3, 14, 5, "final", 0)'
            ),
        ),
        (
            "local clean PDF route GIL predicate removed",
            clean_python_guard,
            clean_python_guard.replace(b" and sys._is_gil_enabled()", b""),
        ),
        (
            "local clean PDF route CPython prerelease admitted",
            clean_python_guard,
            clean_python_guard.replace(b'"final", 0', b'"candidate", 0'),
        ),
        (
            "local clean PDF route nonzero release serial admitted",
            clean_python_guard,
            clean_python_guard.replace(b'"final", 0', b'"final", 1'),
        ),
        (
            "local workflow PDF self-test short-circuited",
            b"    /usr/bin/env -i "
            b'PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" '
            b"HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc "
            b"scripts/check-mathematical-workflow-pdf-self-test.sh\n",
            b"    true || /usr/bin/env -i "
            b'PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" '
            b"HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc "
            b"scripts/check-mathematical-workflow-pdf-self-test.sh\n",
        ),
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
            b"python3 -I -S -B scripts/capture-ksg-m1a-composite-v9-local-closure.py --self-test",
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
        expect_rejection(
            lambda hostile=hostile: semantic_justfile_validation(hostile), label
        )
    release_hostile = replace_once(
        raw,
        b" ksg-composite-v9 ",
        b" ksg-composite-v8 ",
        "release audit selects v8",
    )
    expect_rejection(
        lambda: semantic_justfile_validation(release_hostile),
        "release audit selects v8",
    )
    return len(mutations) + 1


def bounded_block_custody_hostiles() -> int:
    ci = (ROOT / C9.CI_RELATIVE).read_bytes()
    retired = (ROOT / C9.RETIRED_V8_WORKFLOW_RELATIVE).read_bytes()
    successor = (ROOT / C9.V9_WORKFLOW_RELATIVE).read_bytes()
    raw_just = (ROOT / C9.JUSTFILE_RELATIVE).read_bytes()
    runtime_hostile = replace_once(
        successor,
        b"      - name: Require the reviewed GIL-enabled CPython 3.14.6 lane\n",
        b"      - name: Require the reviewed GIL-enabled CPython 3.14.6 lane\n"
        b"        # runtime-step custody hostile\n",
        "runtime-step byte custody",
    )
    workflow_hostile = replace_once(
        successor,
        b"      - name: Validate the corrected fixture and unchanged C8 mathematical-workflow publication\n",
        b"      - name: Validate the corrected fixture and unchanged C8 mathematical-workflow publication\n"
        b"        # workflow-step custody hostile\n",
        "workflow-step byte custody",
    )
    just_block = C9.recipe_block(raw_just, b"ksg-composite-v9")
    just_hostile_block = just_block.replace(
        b"ksg-composite-v9:\n",
        b"ksg-composite-v9:\n    # recipe custody hostile\n",
        1,
    )
    just_hostile = replace_once(
        raw_just, just_block, just_hostile_block, "recipe byte custody"
    )
    for label, hostile in (
        ("runtime-step byte custody", runtime_hostile),
        ("workflow-step byte custody", workflow_hostile),
    ):
        names = (
            "CI_SHA256",
            "CI_SIZE_BYTES",
            "RETIRED_V8_WORKFLOW_SHA256",
            "RETIRED_V8_WORKFLOW_SIZE_BYTES",
            "V9_WORKFLOW_SHA256",
            "V9_WORKFLOW_SIZE_BYTES",
        )
        originals = tuple(getattr(C9, name) for name in names)
        values = (
            C9.sha256(ci),
            len(ci),
            C9.sha256(retired),
            len(retired),
            C9.sha256(hostile),
            len(hostile),
        )
        try:
            for name, value in zip(names, values, strict=True):
                setattr(C9, name, value)
            expect_rejection(
                lambda hostile=hostile: C9.validate_workflow_bytes(
                    ci, retired, hostile
                ),
                label,
            )
        finally:
            for name, value in zip(names, originals, strict=True):
                setattr(C9, name, value)
    expect_rejection(
        lambda: C9.validate_justfile_bytes(just_hostile), "recipe byte custody"
    )
    return 3


def semantic_capture_source_validation(hosted: bytes, local: bytes) -> None:
    hosted_module = C9.parse_source_ast(hosted, "semantic hosted capture")
    local_module = C9.parse_source_ast(local, "semantic local capture")
    names = (
        "EXPECTED_HOSTED_CAPTURE_MAIN_SOURCE_SHA256",
        "EXPECTED_LOCAL_AUTHORITY_SOURCE_SHA256",
        "EXPECTED_LOCAL_DESCRIPTOR_SOURCE_SHA256",
        "EXPECTED_LOCAL_CAPTURE_SOURCE_SHA256",
        "EXPECTED_LOCAL_AUTHORITY_ROSTER_SELF_TEST_SOURCE_SHA256",
        "EXPECTED_LOCAL_AUTHORITY_ROSTER_VALIDATOR_SOURCE_SHA256",
        "EXPECTED_LOCAL_OFFLINE_SELF_TEST_SOURCE_SHA256",
        "EXPECTED_LOCAL_PARSE_TIMESTAMP_SOURCE_SHA256",
        "EXPECTED_LOCAL_RECORD_VALIDATOR_SOURCE_SHA256",
        "EXPECTED_LOCAL_MAIN_SOURCE_SHA256",
    )
    original = tuple(getattr(C9, name) for name in names)
    nodes = (
        C9.exact_function(hosted_module, "main", "semantic hosted capture"),
        C9.exact_function(
            local_module, "authority_descriptors", "semantic local capture"
        ),
        C9.exact_function(local_module, "descriptor", "semantic local capture"),
        C9.exact_function(
            local_module, "capture_under_fixed_umask", "semantic local capture"
        ),
        C9.exact_function(
            local_module, "authority_roster_self_test", "semantic local capture"
        ),
        C9.exact_function(
            local_module, "validate_authority_roster", "semantic local capture"
        ),
        C9.exact_function(local_module, "offline_self_test", "semantic local capture"),
        C9.exact_function(local_module, "parse_timestamp", "semantic local capture"),
        C9.exact_function(
            local_module, "validate_record_value", "semantic local capture"
        ),
        C9.exact_function(local_module, "main", "semantic local capture"),
    )
    values = list(
        C9.sha256(C9.exact_source_slice(raw, node, label))
        for raw, node, label in (
            (hosted, nodes[0], "semantic hosted main"),
            (local, nodes[1], "semantic local authority"),
            (local, nodes[2], "semantic local descriptor"),
            (local, nodes[3], "semantic local capture"),
            (local, nodes[4], "semantic local authority-roster self-test"),
            (local, nodes[5], "semantic local authority-roster validator"),
            (local, nodes[6], "semantic local offline self-test"),
            (local, nodes[7], "semantic local timestamp parser"),
            (local, nodes[8], "semantic local record validator"),
            (local, nodes[9], "semantic local main"),
        )
    )
    live_local = (ROOT / C9.LOCAL_TOOL_RELATIVE).read_bytes()
    live_local_module = C9.parse_source_ast(live_local, "live local capture")
    for index, function_name, label in (
        (7, "parse_timestamp", "live local timestamp parser"),
        (8, "validate_record_value", "live local record validator"),
    ):
        live_node = C9.exact_function(live_local_module, function_name, label)
        live_digest = C9.sha256(C9.exact_source_slice(live_local, live_node, label))
        if values[index] != live_digest:
            values[index] = original[index]
    try:
        for name, value in zip(names, values, strict=True):
            setattr(C9, name, value)
        C9.validate_capture_source_routes(hosted, local)
    finally:
        for name, value in zip(names, original, strict=True):
            setattr(C9, name, value)


def capture_ast_hostiles() -> int:
    hosted = (ROOT / C9.CAPTURE_TOOL_RELATIVE).read_bytes()
    local = (ROOT / C9.LOCAL_TOOL_RELATIVE).read_bytes()
    semantic_capture_source_validation(hosted, local)
    mutations: list[tuple[str, bytes, bytes]] = []

    def hosted_mutation(
        label: str, before: bytes, after: bytes, suffix: bytes = b""
    ) -> None:
        mutations.append(
            (label, replace_once(hosted, before, after, label) + suffix, local)
        )

    def local_mutation(
        label: str, before: bytes, after: bytes, suffix: bytes = b""
    ) -> None:
        mutations.append(
            (label, hosted, replace_once(local, before, after, label) + suffix)
        )

    repetition_start = hosted.index(b"        for repetition in (1, 2):\n")
    repetition_end = hosted.index(
        b"        require(\n            len(repository_ids) == len(runs) * 2",
        repetition_start,
    )
    repetition_block = hosted[repetition_start:repetition_end]
    dead_repetition = b"        if False:\n" + b"".join(
        b"    " + line for line in repetition_block.splitlines(keepends=True)
    )
    mutations.append(
        (
            "hosted repetition loop moved behind a dead branch",
            hosted[:repetition_start] + dead_repetition + hosted[repetition_end:],
            local,
        )
    )

    hosted_mutation(
        "hosted workflow rebind redirected behind dead string",
        b"V8.V7.V6.workflow_identity = workflow_identity",
        b"REDIRECT.workflow_identity = workflow_identity",
        b'\nDEAD_WORKFLOW_REBIND = "V8.V7.V6.workflow_identity = workflow_identity"\n',
    )
    hosted_mutation(
        "hosted capture freshness limitation omitted",
        b"A newly emitted capture binds the current capture-tool descriptor and repeated response bytes, but freshness is controlled operator process rather than authenticated collection time; the format cannot distinguish live collection from manual reconstruction of identical public response bytes plus a changed descriptor.",
        b"Freshness is guaranteed by the capture document.",
    )
    hosted_mutation(
        "hosted TLS environment guard roster emptied",
        b"""FORBIDDEN_TLS_ENVIRONMENT = (
    "CURL_CA_BUNDLE",
    "OPENSSL_CONF",
    "PYTHONHTTPSVERIFY",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SSLKEYLOGFILE",
)""",
        b"FORBIDDEN_TLS_ENVIRONMENT = ()",
    )
    hosted_mutation(
        "hosted extra primitive rebind",
        b"V8.V7.V6.expected_successor_artifact_names = expected_successor_artifact_names",
        b"V8.V7.V6.expected_successor_artifact_names = expected_successor_artifact_names\nV8.V7.V6.read_token = workflow_identity",
    )
    hosted_mutation(
        "hosted run call redirected behind dead string",
        b"V8.V7.V6.capture_run(\n",
        b"REDIRECT.capture_run(\n",
        b'\nDEAD_CAPTURE_RUN = "V8.V7.V6.capture_run("\n',
    )
    hosted_mutation(
        "hosted operational artifact call redirected",
        b"                V8.V7.V6.capture_artifacts(\n",
        b"                REDIRECT.capture_artifacts(\n",
    )
    hosted_mutation(
        "hosted failed-log call redirected",
        b"                    V8.V7.V6.capture_failed_logs(\n",
        b"                    REDIRECT.capture_failed_logs(\n",
    )
    hosted_mutation(
        "hosted CodeQL call redirected",
        b"                    V8.V7.V6.capture_codeql(\n",
        b"                    REDIRECT.capture_codeql(\n",
    )
    local_mutation(
        "local primitive assignment redirected behind dead string",
        b"PRIMITIVES = V8.PRIMITIVES\n",
        b"PRIMITIVES = REDIRECT.PRIMITIVES\n",
        b'\nDEAD_PRIMITIVE_BINDING = "PRIMITIVES = V8.PRIMITIVES"\n',
    )
    local_mutation(
        "local subject rebind changed",
        b"PRIMITIVES.C6_MESSAGE = C9_MESSAGE",
        b"PRIMITIVES.C6_MESSAGE = C8_COMMIT",
    )
    local_mutation(
        "local record bound diverged",
        b"MAX_RECORD_BYTES = 32 * 1024 * 1024",
        b"MAX_RECORD_BYTES = 42 * 1024 * 1024",
    )
    local_mutation(
        "local fixed command constant redirected",
        b'COMMAND_ARGV = ("just", "ksg-composite-v9")',
        b'COMMAND_ARGV = ("just", "--version")',
    )
    local_mutation(
        "local command timeout constant weakened",
        b"COMMAND_TIMEOUT_SECONDS = 14_400",
        b"COMMAND_TIMEOUT_SECONDS = 14",
    )
    local_mutation(
        "local caveat ledger weakened",
        b"A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
        b"A local closure pass proves every scientific and operational claim.",
    )
    local_mutation(
        "local global authority descriptor forges live size classes",
        b'    return {"path": path, "role": role, "sha256": sha256(raw), "size_bytes": len(raw)}\n',
        b'    return {"path": path, "role": role, "sha256": sha256(raw), '
        b'"size_bytes": len(raw) if path == "authority.bin" else 1}\n',
    )
    local_mutation(
        "local Git authority reader compares real paths to themselves",
        b"    _code, stdout, stderr = run_internal(\n",
        b'    if relative != "authority.bin":\n'
        b"        return PRIMITIVES.read_regular(\n"
        b"            ROOT / relative, MAX_AUTHORITY_STREAM_BYTES, AUTHORITY_MODES[relative]\n"
        b"        )\n"
        b"    _code, stdout, stderr = run_internal(\n",
    )
    local_mutation(
        "local authority builder shadows committed Git reader through a default",
        b"def authority_descriptors(\n"
        b"    git_path: Path, environment: dict[str, str], head: str\n"
        b") -> list[dict[str, Any]]:\n",
        b"def authority_descriptors(\n"
        b"    git_path: Path, environment: dict[str, str], head: str,\n"
        b"    git_authority_output=lambda *_args: b''\n"
        b") -> list[dict[str, Any]]:\n",
    )
    local_mutation(
        "local bounded internal authority runner redirected",
        b"    code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n"
        b"        argv,\n"
        b"        executable,\n",
        b"    code, stdout, stderr, timed_out = REDIRECT.run_bounded(\n"
        b"        argv,\n"
        b"        executable,\n",
    )
    local_mutation(
        "local negative expectation helper made a no-op",
        b"def expect_capture_error(operation: Any, label: str) -> None:\n",
        b"def expect_capture_error(operation: Any, label: str) -> None:\n    return\n",
    )
    local_mutation(
        "local bound expectation helper made a no-op",
        b"def expect_bound(size: int, bound: int, accepted: bool) -> None:\n",
        b"def expect_bound(size: int, bound: int, accepted: bool) -> None:\n"
        b"    return\n",
    )
    local_mutation(
        "local sized-output fixture ignores requested size",
        b"        f\"import sys; sys.stdout.buffer.write(b'x' * {size})\",\n",
        b"        \"import sys; sys.stdout.buffer.write(b'x')\",\n",
    )
    local_mutation(
        "local named-oversize roster omits the C9 self-test",
        b"""EXPECTED_OVERSIZED_AUTHORITY_PATHS = sorted(
    {
        CHECKER_RELATIVE,
        SCRIPT_README_RELATIVE,
        SELF_TEST_RELATIVE,
        V8_CHECKER_RELATIVE,""",
        b"""EXPECTED_OVERSIZED_AUTHORITY_PATHS = sorted(
    {
        CHECKER_RELATIVE,
        SCRIPT_README_RELATIVE,
        V8_CHECKER_RELATIVE,""",
    )
    local_mutation(
        "local named-oversize validator equality weakened",
        b"        oversized == EXPECTED_OVERSIZED_AUTHORITY_PATHS,\n",
        b"        set(oversized).issubset(EXPECTED_OVERSIZED_AUTHORITY_PATHS),\n",
    )
    local_mutation(
        "local authority validator exact-path roster removed",
        b'        and [item.get("path") for item in authorities] == sorted(AUTHORITY_ROLES)\n',
        b"",
    )
    local_mutation(
        "local named-oversize hostile loop truncated",
        b"    for relative in EXPECTED_OVERSIZED_AUTHORITY_PATHS:\n",
        b"    for relative in EXPECTED_OVERSIZED_AUTHORITY_PATHS[:1]:\n",
    )
    local_mutation(
        "local roster hostile assertion helper lexically shadowed",
        b"def authority_roster_self_test() -> int:\n    baseline = [\n",
        b"def authority_roster_self_test() -> int:\n"
        b"    expect_capture_error = lambda *_args: None\n"
        b"    baseline = [\n",
    )
    local_mutation(
        "local offline live authority validation bypassed",
        b"    validate_authority_roster(live_authorities)\n"
        b"    route = authority_route_self_test()\n",
        b"    (lambda _authorities: None)(live_authorities)\n"
        b"    route = authority_route_self_test()\n",
    )
    local_mutation(
        "local offline authority validator lexically shadowed",
        b"    live_authorities = [\n",
        b"    validate_authority_roster = lambda _authorities: None\n"
        b"    live_authorities = [\n",
    )
    local_mutation(
        "local offline authority descriptor lexically shadowed",
        b"    live_authorities = [\n",
        b"    descriptor = lambda path, role, _raw: {\n"
        b'        "path": path, "role": role, "sha256": "0" * 64, "size_bytes": 1\n'
        b"    }\n"
        b"    live_authorities = [\n",
    )
    local_mutation(
        "local offline authority suites lexically shadowed",
        b"    route = authority_route_self_test()\n",
        b"    authority_route_self_test = lambda: {\n"
        b'        "hostiles_rejected": 13, "oversize_committed_authorities_accepted": 1\n'
        b"    }\n"
        b"    authority_roster_self_test = lambda: 22\n"
        b"    route = authority_route_self_test()\n",
    )
    local_mutation(
        "local offline bound expectation helper lexically shadowed",
        b"    expect_bound(MAX_VERSION_STREAM_BYTES, MAX_VERSION_STREAM_BYTES, True)\n",
        b"    expect_bound = lambda *_args: None\n"
        b"    expect_bound(MAX_VERSION_STREAM_BYTES, MAX_VERSION_STREAM_BYTES, True)\n",
    )
    local_mutation(
        "local production authority validation removed",
        b"            validate_authority_roster(authorities)\n"
        b"            started_at = utc_now()\n",
        b"            pass  # authority validation removed\n"
        b"            started_at = utc_now()\n",
    )
    local_mutation(
        "local production authority validator lexically shadowed",
        b"            authorities = authority_descriptors(\n",
        b"            validate_authority_roster = lambda _authorities: None\n"
        b"            authorities = authority_descriptors(\n",
    )
    local_mutation(
        "local production authority descriptor builder lexically shadowed",
        b"            authorities = authority_descriptors(\n",
        b"            authority_descriptors = lambda *_args: []\n"
        b"            authorities = authority_descriptors(\n",
    )
    move_label = "local production authority validation moved after command"
    moved_validation = replace_once(
        local,
        b"            validate_authority_roster(authorities)\n",
        b"",
        f"{move_label} removal",
    )
    moved_validation = replace_once(
        moved_validation,
        b"            monotonic_end = time.monotonic_ns()\n",
        b"            monotonic_end = time.monotonic_ns()\n"
        b"            validate_authority_roster(authorities)\n",
        f"{move_label} insertion",
    )
    mutations.append((move_label, hosted, moved_validation))
    local_mutation(
        "local timestamp parser short-circuited",
        b"def parse_timestamp(value: Any, label: str) -> datetime:\n",
        b"def parse_timestamp(value: Any, label: str) -> datetime:\n"
        b"    return datetime(2026, 1, 1, tzinfo=timezone.utc)\n",
    )
    local_mutation(
        "local record validator short-circuited",
        b"def validate_record_value(value: Any) -> None:\n",
        b"def validate_record_value(value: Any) -> None:\n    return\n",
    )
    local_mutation(
        "local platform precondition bypassed",
        b"""    require(
        platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"}
        and platform.python_implementation() == "CPython"
        and platform.python_version() == "3.14.6"
        and sys._is_gil_enabled(),
        "local closure capture requires the reviewed Darwin arm64 GIL-enabled CPython 3.14.6 lane",
    )""",
        b"""    require(
        True,
        "local closure capture requires the reviewed Darwin arm64 GIL-enabled CPython 3.14.6 lane",
    )""",
    )
    local_mutation(
        "local platform observation hard-coded",
        b"""                    "architecture": platform.machine(),
                    "gil_enabled": sys._is_gil_enabled(),
                    "operating_system": platform.system(),
                    "operating_system_release": platform.release(),
                    "python_implementation": platform.python_implementation(),
                    "python_version": platform.python_version(),""",
        b"""                    "architecture": "arm64",
                    "gil_enabled": True,
                    "operating_system": "Darwin",
                    "operating_system_release": "reviewed",
                    "python_implementation": "CPython",
                    "python_version": "3.14.6",""",
    )
    for alias in (b"CaptureError", b"require", b"sha256", b"canonical_json"):
        hosted_mutation(
            f"hosted inherited {alias.decode()} alias rebound",
            b'if __name__ == "__main__":\n',
            alias
            + b" = lambda *args, **kwargs: None\n\n"
            + b'if __name__ == "__main__":\n',
        )
        local_mutation(
            f"local inherited {alias.decode()} alias rebound",
            b'if __name__ == "__main__":\n',
            alias
            + b" = lambda *args, **kwargs: None\n\n"
            + b'if __name__ == "__main__":\n',
        )
    hosted_mutation(
        "hosted module acquires a successful terminal alias",
        b'if __name__ == "__main__":\n',
        b"TERMINAL = os._exit\n\n" + b'if __name__ == "__main__":\n',
    )
    local_mutation(
        "local module acquires a successful terminal alias",
        b'if __name__ == "__main__":\n',
        b"TERMINAL = os.execl\n\n" + b'if __name__ == "__main__":\n',
    )
    hosted_mutation(
        "hosted module dictionary rebinds require",
        b'if __name__ == "__main__":\n',
        b'sys.modules["__main__"].require = lambda *_args, **_kwargs: None\n\n'
        + b'if __name__ == "__main__":\n',
    )
    local_mutation(
        "local module dictionary rebinds require",
        b'if __name__ == "__main__":\n',
        b'sys.modules["__main__"].require = lambda *_args, **_kwargs: None\n\n'
        + b'if __name__ == "__main__":\n',
    )
    local_mutation(
        "local evidence-critical len builtin shadowed",
        b'if __name__ == "__main__":\n',
        b"len = lambda _value: 1\n\n" + b'if __name__ == "__main__":\n',
    )
    local_mutation(
        "local extra top-level primitive rebind",
        b"PRIMITIVES.C5_COMMIT = C8_COMMIT",
        b"PRIMITIVES.C5_COMMIT = C8_COMMIT\nPRIMITIVES.read_regular = byte_binding",
    )
    local_mutation(
        "local bounded runner redirected",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n                COMMAND_ARGV,",
        b"            code, stdout, stderr, timed_out = REDIRECT.run_bounded(\n                COMMAND_ARGV,",
    )
    local_mutation(
        "local bounded command argv redirected",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n"
        b"                COMMAND_ARGV,",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n"
        b'                ("just", "--version"),',
    )
    local_mutation(
        "local command constant shadowed before execution",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
        b'            COMMAND_ARGV = ("just", "--version")\n'
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
    )
    local_mutation(
        "local repository root shadowed before execution",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
        b'            ROOT = Path("/tmp/redirected")\n'
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
    )
    local_mutation(
        "local reviewed executable mapping redirected",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
        b'            executables["just"] = Path("/usr/bin/printf")\n'
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
    )
    local_mutation(
        "local command environment mutated",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
        b'            environment["PATH"] = "/tmp/redirected"\n'
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
    )
    local_mutation(
        "local primitive runner monkey-patched",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
        b"            PRIMITIVES.run_bounded = lambda *_args, **_kwargs: (0, b'forged', b'', False)\n"
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n",
    )
    local_mutation(
        "local post-state overwritten through mutating methods",
        b"            after_state = PRIMITIVES.repository_snapshot(\n"
        b'                executables["git"], environment\n'
        b"            )\n",
        b"            after_state = PRIMITIVES.repository_snapshot(\n"
        b'                executables["git"], environment\n'
        b"            )\n"
        b"            after_state.clear()\n"
        b"            after_state.update(before_state)\n",
    )
    local_mutation(
        "local capture converted to an unconsumed generator",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n"
        b"    if False:\n        yield None\n",
    )
    hosted_mutation(
        "hosted computed terminal dispatch inserted",
        b'        if arguments.phase == "predecessor_failure":\n'
        b"            require(\n"
        b'                failed_by_role["predecessor_ci"] == [C8_CI_FAILED_JOB]\n',
        b'        terminal = getattr(os, "_" + "exit")\n'
        b"        terminal(0)\n"
        b'        if arguments.phase == "predecessor_failure":\n'
        b"            require(\n"
        b'                failed_by_role["predecessor_ci"] == [C8_CI_FAILED_JOB]\n',
    )
    local_mutation(
        "local fixed-umask entry redirected",
        b"""            PRIMITIVES.under_fixed_umask(
                lambda: capture_under_fixed_umask(arguments.output)
            )""",
        b"""            REDIRECT.under_fixed_umask(
                lambda: capture_under_fixed_umask(arguments.output)
            )""",
    )
    hosted_mutation(
        "hosted role loop short-circuited before operational calls",
        b"            for role in sorted(runs):\n"
        b"                artifacts, failed_job_ids, repository_id = V8.V7.V6.capture_run(",
        b"            for role in sorted(runs):\n"
        b"                continue\n"
        b"                artifacts, failed_job_ids, repository_id = V8.V7.V6.capture_run(",
    )
    hosted_mutation(
        "hosted capture main exits successfully before validation",
        b"def main() -> int:\n    arguments = parse_arguments()",
        b"def main() -> int:\n    return 0\n    arguments = parse_arguments()",
    )
    hostile_hosted = replace_once(
        hosted,
        b"def main() -> int:\n    arguments = parse_arguments()\n    try:\n",
        b"def main() -> int:\n    arguments = parse_arguments()\n    try:\n        return 0\n",
        "hosted early try return",
    )
    hostile_hosted = replace_once(
        hostile_hosted,
        b"        sys.stdout.buffer.write(rendered)\n        return 0\n",
        b"        sys.stdout.buffer.write(rendered)\n        pass\n",
        "hosted displaced operational return",
    )
    mutations.append(
        (
            "hosted return count preserved while operational route is stranded",
            hostile_hosted,
            local,
        )
    )
    local_mutation(
        "local capture main exits successfully before validation",
        b"def main() -> int:\n    arguments = parse_arguments()",
        b"def main() -> int:\n    return 0\n    arguments = parse_arguments()",
    )
    local_mutation(
        "local capture self-test branch made unconditional",
        b"def main() -> int:\n    arguments = parse_arguments()\n    try:\n"
        b"        if arguments.self_test:\n",
        b"def main() -> int:\n    arguments = parse_arguments()\n    try:\n"
        b"        if True:\n",
    )
    local_mutation(
        "local fixed-umask wrapper no longer invokes capture",
        b"            PRIMITIVES.under_fixed_umask(\n"
        b"                lambda: capture_under_fixed_umask(arguments.output)\n"
        b"            )",
        b"            PRIMITIVES.under_fixed_umask(lambda: None)",
    )
    local_mutation(
        "local fixed-umask call moved behind a dead branch",
        b"            PRIMITIVES.under_fixed_umask(\n"
        b"                lambda: capture_under_fixed_umask(arguments.output)\n"
        b"            )",
        b"            if False:\n"
        b"                PRIMITIVES.under_fixed_umask(lambda: None)\n"
        b"            REDIRECT.under_fixed_umask(\n"
        b"                lambda: capture_under_fixed_umask(arguments.output)\n"
        b"            )",
    )
    local_mutation(
        "local bounded command call moved behind a dead branch",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n"
        b"                COMMAND_ARGV,",
        b"            if False:\n"
        b"                PRIMITIVES.run_bounded()\n"
        b"            code, stdout, stderr, timed_out = REDIRECT.run_bounded(\n"
        b"                COMMAND_ARGV,",
    )
    local_mutation(
        "local bounded command call moved behind a dead loop",
        b"            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(\n"
        b"                COMMAND_ARGV,",
        b"            for _never in ():\n"
        b"                PRIMITIVES.run_bounded()\n"
        b"            code, stdout, stderr, timed_out = REDIRECT.run_bounded(\n"
        b"                COMMAND_ARGV,",
    )
    local_mutation(
        "local bounded capture returns before command execution",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n    return\n",
    )
    local_mutation(
        "local bounded capture exits successfully before command execution",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n",
        b"def capture_under_fixed_umask(output_path: str) -> None:\n"
        b"    raise SystemExit(0)\n",
    )
    local_mutation(
        "local command success predicate replaced by a tautology",
        b"                not timed_out and code == 0,\n",
        b"                True,\n",
    )
    local_mutation(
        "local record semantic validation bypassed",
        b"            validate_record_value(value)\n",
        b"            (lambda _value: None)(value)\n",
    )
    local_mutation(
        "local post-command repository snapshot replaced by the pre-state",
        b"            after_state = PRIMITIVES.repository_snapshot(\n"
        b'                executables["git"], environment\n'
        b"            )",
        b"            if False:\n"
        b'                PRIMITIVES.repository_snapshot(executables["git"], environment)\n'
        b"            after_state = before_state",
    )
    local_mutation(
        "local authority read moved behind a dead branch",
        b"    for relative, role in sorted(AUTHORITY_ROLES.items()):\n"
        b"        raw = PRIMITIVES.read_regular(",
        b"    for relative, role in sorted(AUTHORITY_ROLES.items()):\n"
        b"        if False:\n"
        b"            PRIMITIVES.read_regular()\n"
        b"        raw = REDIRECT.read_regular(",
    )
    local_mutation(
        "local authority loop made empty",
        b"    for relative, role in sorted(AUTHORITY_ROLES.items()):\n",
        b"    for relative, role in ():\n",
    )
    local_mutation(
        "local authority loop returns before committed-byte comparison",
        b"        committed = git_authority_output(git_path, environment, head, relative)\n",
        b"        return []\n",
    )
    local_mutation(
        "local authority equality replaced by a tautology",
        b'        require(raw == committed, "local authority differs from the C9 tree")\n',
        b'        require(True, "local authority differs from the C9 tree")\n',
    )
    hosted_mutation(
        "hosted failure handler invokes an aliased process exit",
        b"    except (CaptureError, OSError) as error:\n"
        b'        print(f"ERROR: {error}", file=sys.stderr)\n',
        b"    except (CaptureError, OSError) as error:\n"
        b"        terminal = os._exit\n"
        b"        terminal(0)\n"
        b'        print(f"ERROR: {error}", file=sys.stderr)\n',
    )
    local_mutation(
        "local failure handler returns success",
        b"    except (CaptureError, OSError, subprocess.SubprocessError):\n"
        b'        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)\n'
        b"        return 1\n",
        b"    except (CaptureError, OSError, subprocess.SubprocessError):\n"
        b'        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)\n'
        b"        return 0\n",
    )
    local_mutation(
        "local failure handler invokes an aliased process exit",
        b"    except (CaptureError, OSError, subprocess.SubprocessError):\n"
        b'        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)\n',
        b"    except (CaptureError, OSError, subprocess.SubprocessError):\n"
        b"        terminal = os._exit\n"
        b"        terminal(0)\n"
        b'        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)\n',
    )
    mutations.extend(
        (
            (
                "hosted capture main rebound after reviewed definition",
                hosted + b"\nmain = lambda: 0\n",
                local,
            ),
            (
                "local capture main rebound after reviewed definition",
                hosted,
                local + b"\nmain = lambda: 0\n",
            ),
            (
                "hosted capture star import can shadow reviewed functions",
                hosted + b"\nfrom attacker_controlled import *\n",
                local,
            ),
            (
                "local capture star import can shadow reviewed functions",
                hosted,
                local + b"\nfrom attacker_controlled import *\n",
            ),
        )
    )
    for label, hostile_hosted, hostile_local in mutations:
        expect_rejection(
            lambda a=hostile_hosted, b=hostile_local: (
                semantic_capture_source_validation(a, b)
            ),
            label,
        )
    custody_mutations = (
        (
            "hosted main complete-source custody",
            replace_once(
                hosted,
                b"def main() -> int:\n",
                b"def main() -> int:\n    # custody hostile\n",
                "hosted main custody",
            ),
            local,
        ),
        (
            "local authority complete-source custody",
            hosted,
            replace_once(
                local,
                b"def authority_descriptors(\n",
                b"def authority_descriptors(\n    # custody hostile\n",
                "local authority custody",
            ),
        ),
        (
            "local authority descriptor complete-source custody",
            hosted,
            replace_once(
                local,
                b"def descriptor(path: str, role: str, raw: bytes) -> dict[str, Any]:\n",
                b"def descriptor(path: str, role: str, raw: bytes) -> dict[str, Any]:\n"
                b"    # custody hostile\n",
                "local authority descriptor custody",
            ),
        ),
        (
            "local bounded capture complete-source custody",
            hosted,
            replace_once(
                local,
                b"def capture_under_fixed_umask(output_path: str) -> None:\n",
                b"def capture_under_fixed_umask(output_path: str) -> None:\n    # custody hostile\n",
                "local capture custody",
            ),
        ),
        (
            "local authority-roster self-test complete-source custody",
            hosted,
            replace_once(
                local,
                b"def authority_roster_self_test() -> int:\n",
                b"def authority_roster_self_test() -> int:\n    # custody hostile\n",
                "local authority-roster self-test custody",
            ),
        ),
        (
            "local authority-route self-test complete-source custody",
            hosted,
            replace_once(
                local,
                b"def authority_route_self_test() -> dict[str, int]:\n",
                b"def authority_route_self_test() -> dict[str, int]:\n"
                b"    # custody hostile\n",
                "local authority-route self-test custody",
            ),
        ),
        (
            "local authority-roster validator complete-source custody",
            hosted,
            replace_once(
                local,
                b"def validate_authority_roster(authorities: Any) -> None:\n",
                b"def validate_authority_roster(authorities: Any) -> None:\n"
                b"    # custody hostile\n",
                "local authority-roster validator custody",
            ),
        ),
        (
            "local offline self-test complete-source custody",
            hosted,
            replace_once(
                local,
                b"def offline_self_test() -> dict[str, Any]:\n",
                b"def offline_self_test() -> dict[str, Any]:\n    # custody hostile\n",
                "local offline self-test custody",
            ),
        ),
        (
            "local main complete-source custody",
            hosted,
            replace_once(
                local,
                b"def main() -> int:\n",
                b"def main() -> int:\n    # custody hostile\n",
                "local main custody",
            ),
        ),
    )
    for label, hostile_hosted, hostile_local in custody_mutations:
        expect_rejection(
            lambda a=hostile_hosted, b=hostile_local: C9.validate_capture_source_routes(
                a, b
            ),
            label,
        )
    return len(mutations) + len(custody_mutations)


def runtime_guard_hostiles() -> int:
    paths = (
        C9.CHECKER_RELATIVE,
        C9.SELF_TEST_RELATIVE,
        C9.CAPTURE_TOOL_RELATIVE,
        C9.LOCAL_TOOL_RELATIVE,
    )
    guard_mutations = (
        (
            "implementation",
            b'sys.implementation.name == "cpython"',
            b'sys.implementation.name == "pypy"',
        ),
        (
            "patch version",
            b'sys.version_info == (3, 14, 6, "final", 0)',
            b'sys.version_info == (3, 14, 5, "final", 0)',
        ),
        (
            "release level",
            b'"final", 0',
            b'"candidate", 0',
        ),
        (
            "release serial",
            b'"final", 0',
            b'"final", 1',
        ),
        (
            "GIL",
            b"and sys._is_gil_enabled()",
            b"and True",
        ),
        (
            "isolation",
            b"sys.flags.isolated == 1",
            b"sys.flags.isolated == 0",
        ),
    )
    count = 0
    for path in paths:
        raw = (ROOT / path).read_bytes()
        expected_top_level_tries = (
            2 if path in {C9.CAPTURE_TOOL_RELATIVE, C9.LOCAL_TOOL_RELATIVE} else 1
        )
        expected_top_level_expressions = (
            ("validate_checker_bootstrap(checker_raw)",)
            if path == C9.SELF_TEST_RELATIVE
            else ()
        )
        execution_profile = {
            C9.CHECKER_RELATIVE: "checker",
            C9.SELF_TEST_RELATIVE: "self_test",
            C9.CAPTURE_TOOL_RELATIVE: "hosted_capture",
            C9.LOCAL_TOOL_RELATIVE: "local_capture",
        }[path]
        C9.validate_runtime_guard_source(
            raw,
            path,
            expected_top_level_tries,
            expected_top_level_expressions,
            execution_profile,
        )
        guard_start = raw.index(b"if not (\n")
        guard_end = raw.index(b"    raise SystemExit(2)\n", guard_start) + len(
            b"    raise SystemExit(2)\n"
        )
        guard = raw[guard_start:guard_end]
        for field, before, after in guard_mutations:
            hostile_guard = replace_once(
                guard, before, after, f"{path} {field} bootstrap guard"
            )
            hostile = raw[:guard_start] + hostile_guard + raw[guard_end:]
            expect_rejection(
                lambda hostile=hostile, path=path, tries=expected_top_level_tries, expressions=expected_top_level_expressions, profile=execution_profile: (
                    C9.validate_runtime_guard_source(
                        hostile, path, tries, expressions, profile
                    )
                ),
                f"{path} {field} guard weakened",
            )
            count += 1
        prefix = raw[:guard_start]
        suffix = raw[guard_start:]
        for field, hostile_prefix in (
            (
                "sys import alias",
                replace_once(
                    prefix,
                    b"import sys\n",
                    b"import attacker_controlled as sys\n",
                    f"{path} sys import alias",
                ),
            ),
            (
                "star import",
                replace_once(
                    prefix,
                    b"import sys\n",
                    b"import sys\nfrom attacker_controlled import *\n",
                    f"{path} star import",
                ),
            ),
            (
                "nonstar executable import before guard",
                replace_once(
                    prefix,
                    b"import sys\n",
                    b"import sys\nimport attacker_controlled\n",
                    f"{path} executable import before guard",
                ),
            ),
        ):
            hostile = hostile_prefix + suffix
            expect_rejection(
                lambda hostile=hostile, path=path, tries=expected_top_level_tries, expressions=expected_top_level_expressions, profile=execution_profile: (
                    C9.validate_runtime_guard_source(
                        hostile, path, tries, expressions, profile
                    )
                ),
                f"{path} {field} accepted",
            )
            count += 1
        footer = b'if __name__ == "__main__":\n    raise SystemExit(main())\n'
        hostile = replace_once(
            raw,
            footer,
            b"if False:\n    raise SystemExit(main())\n",
            f"{path} disabled CLI footer",
        )
        expect_rejection(
            lambda hostile=hostile, path=path, tries=expected_top_level_tries, expressions=expected_top_level_expressions, profile=execution_profile: (
                C9.validate_runtime_guard_source(
                    hostile, path, tries, expressions, profile
                )
            ),
            f"{path} disabled CLI footer accepted",
        )
        count += 1
        hostile = raw[:guard_end] + b"\nraise SystemExit(0)\n" + raw[guard_end:]
        expect_rejection(
            lambda hostile=hostile, path=path, tries=expected_top_level_tries, expressions=expected_top_level_expressions, profile=execution_profile: (
                C9.validate_runtime_guard_source(
                    hostile, path, tries, expressions, profile
                )
            ),
            f"{path} successful pre-footer exit accepted",
        )
        count += 1
        hostile = (
            raw[:guard_end]
            + b'\nBOOTSTRAP_SUCCESS = getattr(__import__("os"), "_exit")(0)\n'
            + raw[guard_end:]
        )
        expect_rejection(
            lambda hostile=hostile, path=path, tries=expected_top_level_tries, expressions=expected_top_level_expressions, profile=execution_profile: (
                C9.validate_runtime_guard_source(
                    hostile, path, tries, expressions, profile
                )
            ),
            f"{path} computed process exit accepted",
        )
        count += 1
    return count


def self_test_loader_hostiles() -> int:
    raw = (ROOT / C9.SELF_TEST_RELATIVE).read_bytes()
    C9.validate_v9_self_test_loader_source(raw)

    def expect_bootstrap_rejection(hostile: bytes, label: str) -> None:
        try:
            validate_checker_bootstrap(hostile)
        except SystemExit as error:
            require(
                error.code == 2,
                f"bootstrap hostile did not fail with status 2: {label}",
            )
            return
        raise C9.ContractError(f"bootstrap hostile was accepted: {label}")

    guard_start = checker_raw.index(b"if not (\n")
    guard_end = checker_raw.index(b"    raise SystemExit(2)\n", guard_start) + len(
        b"    raise SystemExit(2)\n"
    )
    direct_bootstrap_hostiles = (
        (
            "independent bootstrap accepts a weakened runtime guard",
            replace_once(
                checker_raw,
                b"if not (\n",
                b"if False and not (\n",
                "weakened checker runtime guard",
            ),
        ),
        (
            "independent bootstrap accepts computed getattr process exit",
            checker_raw[:guard_end]
            + b'\nBOOTSTRAP_SUCCESS = getattr(os, "_exit")(0)\n'
            + checker_raw[guard_end:],
        ),
        (
            "independent bootstrap accepts computed import process exit",
            checker_raw[:guard_end]
            + b'\nBOOTSTRAP_SUCCESS = __import__("os")._exit(0)\n'
            + checker_raw[guard_end:],
        ),
    )
    for label, hostile in direct_bootstrap_hostiles:
        expect_bootstrap_rejection(hostile, label)
    module = C9.parse_source_ast(raw, "v9 self-test loader hostile")
    candidates = [node for node in module.body if isinstance(node, C9.ast.Try)]
    require(len(candidates) == 1, "v9 self-test loader hostile fixture changed")
    loader = C9.exact_source_slice(raw, candidates[0], "v9 self-test loader hostile")
    mutations = (
        (
            "self-test loader rereads checker after custody hash",
            b"        checker_raw,\n        os.fspath(CHECKER),",
            b"        CHECKER.read_bytes(),\n        os.fspath(CHECKER),",
        ),
        (
            "self-test loader inherits compiler flags",
            b"        dont_inherit=True,",
            b"        dont_inherit=False,",
        ),
        (
            "self-test loader ignores current optimization mode",
            b"        optimize=sys.flags.optimize,",
            b"        optimize=0,",
        ),
        (
            "self-test loader restored pyc-capable import machinery",
            b"    exec(compiled_checker, C9.__dict__)",
            b"    specification.loader.exec_module(C9)",
        ),
        (
            "self-test loader no longer catches checker SystemExit",
            b"except BaseException:",
            b"except Exception:",
        ),
    )
    for label, before, after in mutations:
        hostile_loader = replace_once(loader, before, after, label)
        hostile = replace_once(raw, loader, hostile_loader, f"{label} loader splice")
        expect_rejection(
            lambda hostile=hostile: C9.validate_v9_self_test_loader_source(hostile),
            label,
        )
    insertion = b"sys.modules[C9.__name__] = C9\n"
    binding_mutations = (
        (
            "self-test checker bytes rebound after hashing",
            b'checker_raw = b"raise SystemExit(0)"\n',
        ),
        (
            "self-test compile primitive rebound",
            b"compile = lambda *args, **kwargs: None\n",
        ),
        (
            "self-test exec primitive rebound",
            b"exec = lambda *args, **kwargs: None\n",
        ),
        (
            "self-test checker module rebound before execution",
            b'C9 = types.ModuleType("redirected")\n',
        ),
    )
    for label, payload in binding_mutations:
        hostile = replace_once(raw, insertion, insertion + payload, label)
        expect_rejection(
            lambda hostile=hostile: C9.validate_v9_self_test_loader_source(hostile),
            label,
        )
    main_label = "self-test main rebound to emit a spoof success"
    footer = b'if __name__ == "__main__":\n    raise SystemExit(main())\n'
    hostile = replace_once(
        raw,
        footer,
        b'main = lambda: (sys.stdout.write(\'{"result":"pass"}\\n\'), 0)[1]\n\n'
        + footer,
        main_label,
    )
    expect_rejection(
        lambda hostile=hostile: C9.validate_v9_self_test_loader_source(hostile),
        main_label,
    )
    call_label = "self-test independent checker bootstrap call omitted"
    hostile = replace_once(
        raw,
        b"validate_checker_bootstrap(checker_raw)\n",
        b"pass  # omitted independent checker bootstrap validation\n",
        call_label,
    )
    expect_rejection(
        lambda hostile=hostile: C9.validate_v9_self_test_loader_source(hostile),
        call_label,
    )
    bootstrap_node = C9.exact_function(
        module, "validate_checker_bootstrap", "v9 self-test bootstrap hostile"
    )
    bootstrap_source = C9.exact_source_slice(
        raw, bootstrap_node, "v9 self-test bootstrap hostile"
    )
    scan_label = "self-test independent checker process-exit scan weakened"
    hostile_bootstrap = replace_once(
        bootstrap_source, b'"os._exit"', b'"os.safe_exit"', scan_label
    )
    hostile = replace_once(
        raw, bootstrap_source, hostile_bootstrap, f"{scan_label} source splice"
    )
    expect_rejection(
        lambda hostile=hostile: C9.validate_v9_self_test_loader_source(hostile),
        scan_label,
    )
    return len(mutations) + len(binding_mutations) + 3 + len(direct_bootstrap_hostiles)


def schema_hostiles() -> int:
    values: dict[str, dict[str, Any]] = {}
    for relative in (
        C9.CAPTURE_SCHEMA_RELATIVE,
        C9.LOCAL_SCHEMA_RELATIVE,
        C9.RECEIPT_SCHEMA_RELATIVE,
    ):
        raw = (ROOT / relative).read_bytes()
        values[relative] = C9.validate_schema_bytes(raw, relative)
    mutations: list[tuple[str, str, dict[str, Any]]] = []
    hosted = copy.deepcopy(values[C9.CAPTURE_SCHEMA_RELATIVE])
    hosted["type"] = "object"
    mutations.append(("hosted root type bypass", C9.CAPTURE_SCHEMA_RELATIVE, hosted))
    hosted = copy.deepcopy(values[C9.CAPTURE_SCHEMA_RELATIVE])
    hosted["$defs"]["predecessorDocument"]["additionalProperties"] = True
    mutations.append(
        ("hosted predecessor root opened", C9.CAPTURE_SCHEMA_RELATIVE, hosted)
    )
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["additionalProperties"] = True
    mutations.append(("local root opened", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["limits"]["properties"]["record_bytes"]["const"] += 10_000_000
    mutations.append(("local record bound diverged", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["invocation"]["properties"]["argv"]["const"] = [
        "just",
        "--version",
    ]
    mutations.append(
        ("local fixed command redirected", C9.LOCAL_SCHEMA_RELATIVE, local)
    )
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["invocation"]["properties"]["timeout_seconds"]["const"] = 14
    mutations.append(
        ("local command timeout weakened", C9.LOCAL_SCHEMA_RELATIVE, local)
    )
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["invocation"]["properties"]["umask"]["const"] = "0022"
    mutations.append(("local umask claim weakened", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["platform"]["properties"]["operating_system"]["const"] = "Linux"
    mutations.append(
        ("local operating system drifted", C9.LOCAL_SCHEMA_RELATIVE, local)
    )
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["platform"]["properties"]["architecture"]["enum"] = ["x86_64"]
    mutations.append(("local architecture drifted", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["platform"]["properties"]["python_implementation"]["const"] = (
        "PyPy"
    )
    mutations.append(("local implementation drifted", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["platform"]["properties"]["python_version"]["const"] = "3.14.5"
    mutations.append(("local runtime patch weakened", C9.LOCAL_SCHEMA_RELATIVE, local))
    local = copy.deepcopy(values[C9.LOCAL_SCHEMA_RELATIVE])
    local["properties"]["platform"]["properties"]["gil_enabled"]["const"] = False
    mutations.append(
        ("local GIL requirement inverted", C9.LOCAL_SCHEMA_RELATIVE, local)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defects"]["items"] = {}
    mutations.append(
        ("receipt defect tail opened", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defects"]["prefixItems"][0]["properties"][
        "stale_binding_count"
    ]["const"] = 4
    mutations.append(
        ("receipt stale-binding count weakened", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defects"]["prefixItems"][0]["properties"]["stale_bindings"][
        "const"
    ].pop()
    mutations.append(
        ("receipt stale-binding ledger truncated", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["defect"] = receipt["properties"].pop("defects")
    receipt["required"][receipt["required"].index("defects")] = "defect"
    receipt["required"].sort()
    mutations.append(
        ("receipt singular defect restored", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["platform"][
        "properties"
    ]["python_version"]["const"] = "3.14.5"
    mutations.append(
        ("receipt runtime patch weakened", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["platform"][
        "properties"
    ]["gil_enabled"]["const"] = False
    mutations.append(
        ("receipt GIL requirement inverted", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["command"]["properties"][
        "argv"
    ]["const"] = ["just", "--version"]
    mutations.append(
        ("receipt fixed command redirected", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["platform"][
        "properties"
    ]["operating_system"]["const"] = "Linux"
    mutations.append(
        ("receipt operating system drifted", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["platform"][
        "properties"
    ]["architecture"]["enum"] = ["x86_64"]
    mutations.append(
        ("receipt architecture drifted", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    receipt = copy.deepcopy(values[C9.RECEIPT_SCHEMA_RELATIVE])
    receipt["properties"]["local_qualification"]["properties"]["platform"][
        "properties"
    ]["python_implementation"]["const"] = "PyPy"
    mutations.append(
        ("receipt implementation drifted", C9.RECEIPT_SCHEMA_RELATIVE, receipt)
    )
    for label, relative, hostile in mutations:
        raw = C9.canonical_json(hostile, pretty=True)
        expect_rejection(
            lambda raw=raw, relative=relative: C9.validate_schema_bytes(raw, relative),
            label,
        )
    return len(mutations)


def rebind_difference_guard_hostiles() -> int:
    relative = "scripts/check-certified-sxpid2-claim-self-test.py"
    raw = (ROOT / relative).read_bytes()
    certified = (ROOT / "scripts/check-certified-sxpid2-claim.py").read_bytes()
    ci = (ROOT / ".github/workflows/ci.yml").read_bytes()
    justfile = (ROOT / C9.JUSTFILE_RELATIVE).read_bytes()
    certified_tool_readme = (
        ROOT / "audit/tools/certified-sxpid/README.md"
    ).read_bytes()
    scripts_readme = (ROOT / "scripts/README.md").read_bytes()
    formal_pdf_set = (ROOT / C9.FORMAL_PDF_SET_RELATIVE).read_bytes()

    def bounded_block(
        source: bytes, start_line: bytes, next_top_level: re.Pattern[bytes]
    ) -> bytes:
        lines = source.splitlines(keepends=True)
        starts = [index for index, line in enumerate(lines) if line == start_line]
        require(len(starts) == 1, "certified live block start is not unique")
        start = starts[0]
        end = next(
            (
                index
                for index in range(start + 1, len(lines))
                if next_top_level.fullmatch(lines[index]) is not None
            ),
            len(lines),
        )
        return b"".join(lines[start:end])

    def validate(candidate: bytes) -> None:
        C9.validate_certified_rebind_difference_guard_source(
            raw,
            candidate,
            ci,
            justfile,
            certified_tool_readme,
            scripts_readme,
            formal_pdf_set,
        )

    validate(certified)
    hostile = replace_once(
        raw,
        b"execution-container:.github/workflows/ci.yml",
        b"execution-container:.github/workflows/release.yml",
        "certified rebind-difference guard path redirected",
    )
    expect_rejection(
        lambda: C9.validate_certified_rebind_difference_guard_source(
            hostile,
            certified,
            ci,
            justfile,
            certified_tool_readme,
            scripts_readme,
            formal_pdf_set,
        ),
        "certified rebind-difference guard path redirected",
    )
    hostile = replace_once(
        raw,
        b"binding_differences == EXPECTED_C8_FAILURE_BINDING_DIFFERENCES",
        b"binding_differences == binding_differences",
        "certified rebind-difference equality disconnected",
    )
    expect_rejection(
        lambda: C9.validate_certified_rebind_difference_guard_source(
            hostile,
            certified,
            ci,
            justfile,
            certified_tool_readme,
            scripts_readme,
            formal_pdf_set,
        ),
        "certified rebind-difference equality disconnected",
    )
    hostile = replace_once(
        raw,
        b'        "TMPDIR": "/tmp",',
        b'        "TMPDIR": "/var/tmp",',
        "certified isolated Git temporary route changed",
    )
    expect_rejection(
        lambda: C9.validate_certified_rebind_difference_guard_source(
            hostile,
            certified,
            ci,
            justfile,
            certified_tool_readme,
            scripts_readme,
            formal_pdf_set,
        ),
        "certified isolated Git temporary route changed",
    )
    stale_certified = replace_once(
        certified,
        C9.sha256(justfile).encode("ascii"),
        b"0" * 64,
        "certified retained justfile binding stale after candidate wiring",
    )
    expect_rejection(
        lambda: validate(stale_certified),
        "certified retained justfile binding stale after candidate wiring",
    )
    for live_raw, replacement, label in (
        (
            ci,
            b"1" * 64,
            "certified retained CI binding stale after candidate wiring",
        ),
        (
            scripts_readme,
            b"2" * 64,
            "certified retained documentation binding stale after candidate wiring",
        ),
        (
            formal_pdf_set,
            b"3" * 64,
            "certified retained support-gate binding stale after candidate wiring",
        ),
    ):
        stale_certified = replace_once(
            certified,
            C9.sha256(live_raw).encode("ascii"),
            replacement,
            label,
        )
        expect_rejection(lambda candidate=stale_certified: validate(candidate), label)
    release_lines = [
        line
        for line in justfile.splitlines(keepends=True)
        if line.startswith(b"release-audit:")
    ]
    require(len(release_lines) == 1, "live release-audit line is not unique")
    label = "certified retained release-audit-line binding stale after candidate wiring"
    stale_certified = replace_once(
        certified,
        C9.sha256(release_lines[0]).encode("ascii"),
        b"4" * 64,
        label,
    )
    expect_rejection(lambda: validate(stale_certified), label)
    for block, replacement, label in (
        (
            bounded_block(
                ci,
                b"  certified-sxpid-reference:\n",
                re.compile(rb"  [A-Za-z0-9_-]+:\n"),
            ),
            b"5" * 64,
            "certified retained CI job binding stale after candidate wiring",
        ),
        (
            bounded_block(
                justfile,
                b"certified-sxpid:\n",
                re.compile(rb"\S.*\n"),
            ),
            b"6" * 64,
            "certified retained just recipe binding stale after candidate wiring",
        ),
    ):
        stale_certified = replace_once(
            certified,
            C9.sha256(block).encode("ascii"),
            replacement,
            label,
        )
        expect_rejection(lambda candidate=stale_certified: validate(candidate), label)
    return 10


def narrative_semantic_hostiles() -> int:
    documents = {path: (ROOT / path).read_bytes() for path in C9.C9_NARRATIVE_PATHS}
    C9.validate_c9_narrative_boundaries(documents)
    for path in C9.C9_NARRATIVE_PATHS:
        hostile = dict(documents)
        hostile[path] = b"No L8 record was run.\n" + hostile[path]
        expect_rejection(
            lambda hostile=hostile: C9.validate_c9_narrative_boundaries(hostile),
            f"unsupported L8 operator-history claim accepted: {path}",
        )
    hostile = dict(documents)
    path = "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md"
    hostile[path] = b"Retain the failed C8 publication family.\n" + hostile[path]
    expect_rejection(
        lambda: C9.validate_c9_narrative_boundaries(hostile),
        "C8 publication/hosted-failure conflation accepted",
    )
    targeted = (
        (C9.REJECTED_C9_COMMIT.encode("ascii"), b"0" * 40, "rejected commit"),
        (C9.REJECTED_C9_TREE.encode("ascii"), b"1" * 40, "rejected tree"),
        (
            C9.REJECTED_C9_R14_SHA256.encode("ascii"),
            b"2" * 64,
            "rejected r14",
        ),
        (
            C9.REJECTED_C9_ARCHIVE_REF.encode("ascii"),
            b"refs/heads/archive/redirected",
            "archive ref",
        ),
        (
            C9.REJECTED_FIXED_POINT_C9_COMMIT.encode("ascii"),
            b"3" * 40,
            "rejected fixed-point commit",
        ),
        (
            C9.REJECTED_FIXED_POINT_C9_TREE.encode("ascii"),
            b"4" * 40,
            "rejected fixed-point tree",
        ),
        (
            C9.REJECTED_FIXED_POINT_C9_R14_SHA256.encode("ascii"),
            b"5" * 64,
            "rejected fixed-point r14",
        ),
        (
            C9.REJECTED_FIXED_POINT_C9_R14_PROVISIONAL_SHA256.encode("ascii"),
            b"6" * 64,
            "rejected fixed-point provisional r14",
        ),
        (
            C9.REJECTED_FIXED_POINT_C9_ARCHIVE_REF.encode("ascii"),
            b"refs/heads/archive/fixed-point-redirected",
            "rejected fixed-point archive ref",
        ),
        (
            C9.REJECTED_FIXED_POINT_CERTIFIED_STDERR_SHA256.encode("ascii"),
            b"7" * 64,
            "rejected fixed-point certified stderr",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_COMMIT.encode("ascii"),
            b"8" * 40,
            "rejected local-authority commit",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_TREE.encode("ascii"),
            b"9" * 40,
            "rejected local-authority tree",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_ARCHIVE_REF.encode("ascii"),
            b"refs/heads/archive/local-authority-redirected",
            "rejected local-authority archive ref",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_R14_SHA256.encode("ascii"),
            b"a" * 64,
            "rejected local-authority final r14",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_R14_PROVISIONAL_RECONSTRUCTION_SHA256.encode(
                "ascii"
            ),
            b"b" * 64,
            "rejected local-authority provisional reconstruction",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_R14_FINAL_LEAN_CUSTODY_SHA256.encode(
                "ascii"
            ),
            b"c" * 64,
            "rejected local-authority final Lean custody",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_R14_REPLAY_LEAN_CUSTODY_SHA256.encode(
                "ascii"
            ),
            b"d" * 64,
            "rejected local-authority replay Lean custody",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_CURRENT_SOURCE_SHA256.encode("ascii"),
            b"e" * 64,
            "rejected local-authority current source",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_RECORDER_STDERR_SHA256.encode("ascii"),
            b"f" * 64,
            "rejected local-authority generic recorder stderr",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_STDOUT_SHA256.encode("ascii"),
            b"0" * 64,
            "rejected local-authority command stdout",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_STDERR_SHA256.encode("ascii"),
            b"1" * 64,
            "rejected local-authority command stderr",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_DIAGNOSTIC_SHA256.encode("ascii"),
            b"2" * 64,
            "rejected local-authority substitution diagnostic",
        ),
        (
            C9.REJECTED_LOCAL_AUTHORITY_C9_SELF_TEST_SHA256.encode("ascii"),
            b"3" * 64,
            "rejected local-authority self-test",
        ),
    )
    boundary = C9.BOUNDARY_RELATIVE
    for before, after, label in targeted:
        hostile = dict(documents)
        hostile[boundary] = replace_once(hostile[boundary], before, after, label)
        expect_rejection(
            lambda hostile=hostile: C9.validate_c9_narrative_boundaries(hostile),
            f"{label} narrative binding changed",
        )
    semantic_tokens = (
        (
            b"refresh destination mode drifted: ",
            b"destination mode warning: ",
            "failure prefix",
        ),
        (b"/root/output/pdf/workflow.pdf", b"/tmp/other.pdf", "failure path suffix"),
        (b"whole-run digest", b"run checksum", "whole-run digest limit"),
        (b"documentary only", b"qualification evidence", "documentary scope"),
        (b"not checker-replayed", b"checker-replayed", "checker replay status"),
        (
            b"zero qualification credit",
            b"qualification credit",
            "zero qualification credit",
        ),
        (
            b"not observed accepted or published on `main` as C9",
            b"never accepted or published on `main` as C9",
            "bounded main observation",
        ),
        (
            b"does not query provider\narchive, main, or workflow-run endpoints",
            b"does not query the provider archive endpoint",
            "endpoint non-query scope",
        ),
        (b"sibling commit object", b"related object", "sibling object limitation"),
        (
            b"checkout-normalizer",
            b"checkout helper",
            "runner-Python normalizer carve-out",
        ),
        (b"3.11.13", b"3.11", "documentary 3.11 patch"),
        (b"3.12.11", b"3.12", "documentary 3.12 patch"),
        (b"3.13.7", b"3.13", "documentary 3.13 patch"),
        (
            C9.CERTIFIED_FAILURE_MARKER,
            b"certified checker failed: changed digest",
            "exact C8 failure marker",
        ),
        (b"contains 32 paths", b"contains 33 paths", "fresh path-set cardinality"),
        (b"contained 31", b"contained 32", "rejected path-set cardinality"),
        (
            b"sole path-set membership difference",
            b"one path difference",
            "path-set membership boundary",
        ),
        (
            b"set-membership statement",
            b"whole-delta statement",
            "shared-path byte nonimplication",
        ),
        (
            b"finite regression evidence",
            b"complete proof evidence",
            "finite regression scope",
        ),
        (
            b"semantic soundness",
            b"semantic equivalence",
            "semantic-soundness non-proof",
        ),
        (
            b"Dynamic namespace",
            b"Every namespace",
            "dynamic-namespace limitation",
        ),
        (
            b"Exact whole-file",
            b"Selected file",
            "authoritative custody boundary",
        ),
        (
            b"`66fdc640aad886c6de25a3a544a24ba016f4f2e73989abe5319f562da1c08919`; all 39 receipt records\ncarry `exit_code: 0`",
            b"`66fdc640aad886c6de25a3a544a24ba016f4f2e73989abe5319f562da1c08919`; all replay commands succeeded",
            "receipt-record exit-code boundary",
        ),
        (
            b"exact argv roster contains zero\nrecords for the certified baseline",
            b"stdout contains no certified baseline output",
            "exact argv versus stdout boundary",
        ),
        (
            b"ten other named self-test command records are present",
            b"zero self-test command records are present",
            "other self-test record count",
        ),
        (
            b"stream payloads retain only byte-count/SHA-256 descriptors",
            b"stream payloads retain raw stdout and stderr",
            "stream payload representation",
        ),
        (
            b"not a raw-stdout absence claim",
            b"a raw-stdout absence proof",
            "raw-stdout nonimplication",
        ),
        (
            b"At a separate generator call site, the same validator implementation",
            b"At a separate generator call site, an independent validator implementation",
            "shared validator implementation",
        ),
        (
            b"live-cut predicate once before the replay command sequence",
            b"before every replay command",
            "generator predicate frequency",
        ),
        (
            b"correlated, common-mode endpoint checks",
            b"independent per-command checks",
            "generator common-mode boundary",
        ),
        (
            b"2f163d400569a0897533ef5f5bdae357bd97962d0888ac2bbf68cfa5fe753351",
            b"8" * 64,
            "certified self-test stdout digest",
        ),
        (
            b"a77c6d4634ad134975d9a42520a4dc16cd696d51879614a1a4f711eab8ce9f93",
            b"9" * 64,
            "Lean outer self-test stdout digest",
        ),
        (
            b"e94271b9e1c1b7e885fb78d1839b2d8dacebf79aa6a72e6233db5773ded93ade",
            b"a" * 64,
            "post-rejection fail-fast stderr digest",
        ),
        (
            b"not an observed or retained provisional artifact",
            b"an observed and retained provisional artifact",
            "third provisional reconstruction scope",
        ),
        (
            b"neither the failure stage nor the production command streams",
            b"the failure stage and production command streams",
            "third generic recorder error scope",
        ),
        (
            b"not local-recorder invocation or stream custody",
            b"local-recorder invocation and stream custody",
            "third direct-command diagnostic scope",
        ),
        (
            b"It is not production execution or custody",
            b"It is production execution and custody",
            "third substituted diagnostic scope",
        ),
        (
            b"named-roster classification defect, not authority-size exhaustion",
            b"authority-size exhaustion",
            "third threshold-versus-maximum distinction",
        ),
    )
    for before, after, label in semantic_tokens:
        hostile = dict(documents)
        hostile[boundary] = replace_once(hostile[boundary], before, after, label)
        expect_rejection(
            lambda hostile=hostile: C9.validate_c9_narrative_boundaries(hostile),
            f"{label} narrative boundary changed",
        )
    for overclaim in (
        b"The candidate was never accepted or published.\n",
        b"The separate run was diagnostic only.\n",
        b"The replay transcript preserves live-pre-replay-ready.\n",
        b"The generator checks the predicate before every replay command.\n",
        b"The production recorder failed before its command.\n",
        b"The direct `just` runs issued L9.\n",
        b"The substituted call was the recorder-owned command.\n",
        b"The provisional artifact was observed.\n",
    ):
        hostile = dict(documents)
        hostile[boundary] = overclaim + hostile[boundary]
        expect_rejection(
            lambda hostile=hostile: C9.validate_c9_narrative_boundaries(hostile),
            "narrative overclaim accepted",
        )
    return len(C9.C9_NARRATIVE_PATHS) + 1 + len(targeted) + len(semantic_tokens) + 8


def policy_hostiles() -> int:
    raw = (ROOT / C9.POLICY_RELATIVE).read_bytes()
    value = C9.parse_json(raw, "composite-v9 self-test policy")
    C9.validate_policy_value(value)
    mutations: list[tuple[str, dict[str, Any]]] = []
    hostile = copy.deepcopy(value)
    hostile["c8_disposition"]["repository_ci_attempt_1"]["conclusion"] = "success"
    mutations.append(("C8 CI failure erased", hostile))
    hostile = copy.deepcopy(value)
    hostile["c8_disposition"]["extra_defect"] = "unsupported"
    mutations.append(("C8 disposition extra field", hostile))
    hostile = copy.deepcopy(value)
    hostile["base"]["r6_status"] = "issued"
    mutations.append(("R6 resurrected", hostile))
    hostile = copy.deepcopy(value)
    hostile["publication"]["c9_new_pdf"] = "created"
    mutations.append(("C9 PDF invented", hostile))
    hostile = copy.deepcopy(value)
    hostile["nonimplications"].pop()
    mutations.append(("policy nonimplication omitted", hostile))
    hostile = copy.deepcopy(value)
    hostile["nonimplications"][-1] = (
        "C9 operational evidence proves mathematical correctness."
    )
    mutations.append(("policy nonimplication inverted", hostile))
    hostile = copy.deepcopy(value)
    hostile["diagnosis"]["evidence_scope"] = "unique_counterfactual_necessity_proved"
    mutations.append(("policy diagnosis overclaimed necessity", hostile))
    hostile = copy.deepcopy(value)
    hostile["c9"]["delta"] = [
        item
        for item in hostile["c9"]["delta"]
        if item["path"] != "scripts/check-certified-sxpid2-claim.py"
    ]
    mutations.append(("retained operational repin omitted", hostile))
    hostile = copy.deepcopy(value)
    hostile["fixture_correction"]["destination_count"] = 5
    mutations.append(("workflow fixture destination count reduced", hostile))
    hostile = copy.deepcopy(value)
    hostile["fixture_correction"]["successor"]["sha256"] = "0" * 64
    mutations.append(("workflow fixture successor binding changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["commit"] = "0" * 40
    mutations.append(("rejected candidate identity changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["r14"]["sha256"] = "0" * 64
    mutations.append(("rejected r14 archive binding changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["archive_ref"] += "-redirected"
    mutations.append(("rejected candidate archive ref redirected", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["credit"] = "accepted"
    mutations.append(("rejected candidate received acceptance credit", hostile))
    hostile = copy.deepcopy(value)
    hostile["interpreter_correction"]["scope"] = "entire_hosted_workflow"
    mutations.append(("interpreter scope swallowed pre-setup bootstrap", hostile))
    hostile = copy.deepcopy(value)
    hostile["interpreter_correction"]["hosted_pre_setup_bootstrap"] = (
        "runner_python_bootstrap_outside_exact_3_14_6_scope"
    )
    mutations.append(("interpreter pre-setup call roster collapsed", hostile))
    hostile = copy.deepcopy(value)
    hostile["interpreter_correction"]["successor_selection"] = (
        "local_and_hosted_cpython_3_14_5_without_gil_check"
    )
    mutations.append(("interpreter patch or GIL boundary weakened", hostile))
    hostile = copy.deepcopy(value)
    hostile["fixture_correction"]["diagnostic_umask_022_rollback_observation"] = (
        "required_umask_077_restored_exact_original_inode_and_mode_0644"
    )
    mutations.append(("diagnostic rollback scope conflated with required run", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["publication_status"] = (
        "never_accepted_or_published_on_main_as_c9"
    )
    mutations.append(("bounded publication observation made absolute", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_candidate"]["qualification"]["github_actions_workflow_runs"][
        "count"
    ] = 1
    mutations.append(("rejected candidate workflow-run count changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["commit"] = "0" * 40
    mutations.append(("rejected fixed-point candidate identity changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["r14"]["sha256"] = "0" * 64
    mutations.append(("rejected fixed-point r14 binding changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["credit"] = "accepted"
    mutations.append(("rejected fixed-point candidate received credit", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["documentation_review"][
        "r14_canonical_receipt_literal_live_marker_occurrences"
    ] = 1
    mutations.append(("rejected r14 invented named self-test output", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"][
        "certified_sxpid2_baseline"
    ]["normal_result"] = "success"
    mutations.append(("rejected retained baseline failure erased", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["documentation_review"][
        "r14_canonical_receipt_literal_live_marker_occurrences"
    ] = False
    mutations.append(("rejected r14 Boolean masqueraded as zero count", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["r14_replay"][
        "command_record_count"
    ] = 39.0
    mutations.append(("rejected r14 float masqueraded as integer count", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["documentation_review"][
        "generator_guard"
    ] = "equivalent_live_cut_predicate_enforced_before_every_replay_command_and_publication"
    mutations.append(("rejected generator endpoint checks made per-command", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["documentation_review"][
        "r14_other_named_self_test_command_records"
    ] = 0
    mutations.append(("rejected r14 other self-test records erased", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"]["documentation_review"][
        "r14_absent_exact_command_paths"
    ].pop()
    mutations.append(("rejected r14 absent exact command roster weakened", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"][
        "certified_sxpid2_baseline"
    ]["self_test_evidence_scope"] = "r14_command_and_stdout_custody"
    mutations.append(("rejected certified self-test custody scope inverted", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_fixed_point_candidate"]["qualification"][
        "post_rejection_recovery_review"
    ]["stderr_sha256"] = "0" * 64
    mutations.append(("post-rejection fail-fast edge evidence changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["commit"] = "0" * 40
    mutations.append(("rejected local-authority candidate identity changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["tree"] = "1" * 40
    mutations.append(("rejected local-authority candidate tree changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["archive_ref"] += "-redirected"
    mutations.append(("rejected local-authority archive ref redirected", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["credit"] = "accepted"
    mutations.append(("rejected local-authority candidate received credit", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"][
        "github_main_observed_target_after_archive"
    ] = "2" * 40
    mutations.append(("rejected local-authority unchanged-main fact changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["publication_status"] = (
        "accepted_on_main_as_c9"
    )
    mutations.append(("rejected local-authority bounded publication changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "github_actions_workflow_runs"
    ]["count"] = 1
    mutations.append(("rejected local-authority workflow run invented", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"]["l9_record"] = (
        "issued"
    )
    mutations.append(("rejected local-authority L9 invented", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["current_source"]["sha256"] = "3" * 64
    mutations.append(("rejected local-authority current-source changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "production_local_recorder"
    ]["generic_stderr_scope"] = "proves_pre_command_failure_and_stream_absence"
    mutations.append(("generic recorder error scope overclaimed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "direct_and_sanitized_command_diagnostics"
    ]["direct"]["stdout_sha256"] = "4" * 64
    mutations.append(("direct command diagnostic stream changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"]["source_order"][
        "evidence_scope"
    ] = "production_execution_and_stream_custody"
    mutations.append(("source ordering promoted to execution custody", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "substituted_postcondition_diagnostic"
    ]["evidence_scope"] = "production_execution_and_custody"
    mutations.append(
        ("substitution diagnostic promoted to production custody", hostile)
    )
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "local_authority_size_classification"
    ]["classification_threshold_bytes"] = 2_097_152
    mutations.append(
        ("authority classification threshold conflated with maximum", hostile)
    )
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "local_authority_size_classification"
    ]["authority_stream_maximum_bytes"] = 65_536
    mutations.append(
        ("authority maximum conflated with classification threshold", hostile)
    )
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"][
        "local_authority_size_classification"
    ]["capture_tool_sha256"] = "5" * 64
    mutations.append(("defective local capture tool binding changed", hostile))
    hostile = copy.deepcopy(value)
    hostile["rejected_local_authority_candidate"]["qualification"]["r14_replay"][
        "provisional_reconstruction"
    ]["evidence_scope"] = "observed_retained_provisional_artifact"
    mutations.append(("provisional reconstruction promoted to observation", hostile))
    hostile = copy.deepcopy(value)
    hostile["replay"]["predicate"] = (
        "fresh_post_c8_r14_excluding_only_two_rejected_artifacts"
    )
    mutations.append(("third rejected replay exclusion omitted", hostile))
    for label, candidate in mutations:
        expect_rejection(
            lambda candidate=candidate: C9.validate_policy_value(candidate), label
        )
    return len(mutations)


def lean_cut_hostiles() -> int:
    lean_raw = (ROOT / C9.LEAN_CHECKER_RELATIVE).read_bytes()
    projection_placeholder = b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    scalar_placeholder = b'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "0" * 64'
    operational_placeholder = b'    "scripts/check-ksg-m1a-composite-v9.py": "0" * 64,'
    live_pre_replay_cut = False
    if projection_placeholder in lean_raw:
        scalar_prefix = b"EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "
        operational_prefix = b'    "scripts/check-ksg-m1a-composite-v9.py": '
        require(
            lean_raw.count(projection_placeholder) == 1,
            "Lean projection fixture changed",
        )
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
            live_scalar = scalar_prefix + b'"' + live_checker_digest + b'"'
            live_operational = operational_prefix + b'"' + live_checker_digest + b'",'
            require(
                lean_raw.count(scalar_prefix) == 1
                and lean_raw.count(operational_prefix) == 1
                and lean_raw.count(live_scalar) == 1
                and lean_raw.count(live_operational) == 1,
                "Lean pre-r14 finalized checker cuts changed",
            )
            normalized = replace_once(
                lean_raw,
                live_scalar,
                scalar_placeholder,
                "pre-r14 Lean scalar normalization",
            )
            normalized = replace_once(
                normalized,
                live_operational,
                operational_placeholder,
                "pre-r14 Lean operational normalization",
            )
            live_pre_replay_cut = True
    else:
        _projection, _scalar, _operational, normalized = C9.lean_r14_source_cuts(
            lean_raw
        )
    normalized_digest = C9.sha256(normalized)
    if live_pre_replay_cut:
        require(
            C9.normalized_lean_checker_cut(checker_raw) == normalized_digest,
            "live pre-replay normalized-Lean cut changed",
        )
    normalized_line = (
        b'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "'
        + normalized_digest.encode("ascii")
        + b'"\n'
    )
    synthetic_checker = normalized_line
    checker_digest = C9.sha256(synthetic_checker)
    projection = "1" * 64
    scalar_final = (
        b'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "'
        + checker_digest.encode("ascii")
        + b'"'
    )
    operational_final = (
        b'    "scripts/check-ksg-m1a-composite-v9.py": "'
        + checker_digest.encode("ascii")
        + b'",'
    )
    final_lean = replace_once(
        normalized,
        projection_placeholder,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + projection.encode("ascii")
        + b'"',
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
    multiline_checker = replace_once(
        synthetic_checker,
        normalized_line,
        b"EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = (\n"
        + b'    "'
        + normalized_digest.encode("ascii")
        + b'"\n)\n',
        "multiline normalized-Lean checker fixture",
    )
    multiline_digest = C9.sha256(multiline_checker).encode("ascii")
    multiline_scalar = (
        b'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "'
        + multiline_digest
        + b'"'
    )
    multiline_operational = (
        b'    "scripts/check-ksg-m1a-composite-v9.py": "' + multiline_digest + b'",'
    )
    multiline_lean = replace_once(
        final_lean,
        scalar_final,
        multiline_scalar,
        "multiline checker scalar rebind",
    )
    multiline_lean = replace_once(
        multiline_lean,
        operational_final,
        multiline_operational,
        "multiline checker operational rebind",
    )
    require(
        C9.validate_lean_r14_checksum_cut(synthetic_checker, final_lean) == projection,
        "positive Lean checksum cut changed",
    )

    mutations = (
        (
            "Lean scalar mismatch",
            synthetic_checker,
            replace_once(
                final_lean,
                scalar_final,
                b'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "'
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
                b'    "scripts/check-ksg-m1a-composite-v9.py": "' + b"3" * 64 + b'",',
                "Lean operational mismatch fixture",
            ),
        ),
        (
            "normalized Lean digest mismatch",
            b'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "' + b"4" * 64 + b'"\n',
            final_lean,
        ),
        (
            "normalized Lean binding parenthesized multiline",
            multiline_checker,
            multiline_lean,
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
            lambda a=hostile_checker, b=hostile_lean: C9.validate_lean_r14_checksum_cut(
                a, b
            ),
            label,
        )

    lean_self_test = (ROOT / C9.LEAN_SELF_TEST_RELATIVE).read_bytes()
    replay_lean = replace_once(
        final_lean,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + projection.encode("ascii")
        + b'"',
        projection_placeholder,
        "synthetic Lean replay reconstruction",
    )
    r13 = {"checker_sha256": {"scientific": "retained"}}
    r14 = {
        "checker_sha256": dict(r13["checker_sha256"]),
        "custody_gate_sha256": {
            C9.LEAN_SELF_TEST_RELATIVE: C9.sha256(lean_self_test),
            C9.LEAN_CHECKER_RELATIVE: C9.sha256(final_lean),
        },
        "operational_wiring_sha256": {C9.CHECKER_RELATIVE: checker_digest},
        "replay_custody_gate_sha256": {
            C9.LEAN_SELF_TEST_RELATIVE: C9.sha256(lean_self_test),
            C9.LEAN_CHECKER_RELATIVE: C9.sha256(replay_lean),
        },
    }
    receipt_projection = C9.lean_replay_projection_sha256(r14)
    receipt_lean = replace_once(
        final_lean,
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + projection.encode("ascii")
        + b'"',
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + receipt_projection.encode("ascii")
        + b'"',
        "synthetic final receipt projection",
    )
    r14["custody_gate_sha256"][C9.LEAN_CHECKER_RELATIVE] = C9.sha256(receipt_lean)
    C9.validate_lean_r14_receipt_cuts(
        synthetic_checker,
        receipt_lean,
        lean_self_test,
        r13,
        r14,
        receipt_projection,
    )
    receipt_mutations: list[tuple[str, dict[str, Any], str]] = []
    hostile = copy.deepcopy(r14)
    hostile["checker_sha256"] = {"scientific": "changed"}
    receipt_mutations.append(
        ("r14 scientific inventory drift", hostile, receipt_projection)
    )
    hostile = copy.deepcopy(r14)
    hostile["operational_wiring_sha256"][C9.CHECKER_RELATIVE] = "5" * 64
    receipt_mutations.append(
        ("r14 operational checker drift", hostile, receipt_projection)
    )
    hostile = copy.deepcopy(r14)
    del hostile["operational_wiring_sha256"][C9.CHECKER_RELATIVE]
    receipt_mutations.append(
        ("r14 operational checker missing", hostile, receipt_projection)
    )
    hostile = copy.deepcopy(r14)
    hostile["custody_gate_sha256"][C9.LEAN_CHECKER_RELATIVE] = "6" * 64
    receipt_mutations.append(("r14 final custody drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r14)
    hostile["replay_custody_gate_sha256"][C9.LEAN_CHECKER_RELATIVE] = "7" * 64
    receipt_mutations.append(("r14 replay custody drift", hostile, receipt_projection))
    hostile = copy.deepcopy(r14)
    hostile["custody_gate_sha256"]["scripts/unreviewed-custody.py"] = "9" * 64
    receipt_mutations.append(("r14 custody extra path", hostile, receipt_projection))
    hostile = copy.deepcopy(r14)
    del hostile["custody_gate_sha256"][C9.LEAN_CHECKER_RELATIVE]
    receipt_mutations.append(("r14 custody missing path", hostile, receipt_projection))
    hostile = copy.deepcopy(r14)
    hostile["operational_wiring_sha256"][C9.LEAN_CHECKER_RELATIVE] = C9.sha256(
        receipt_lean
    )
    receipt_mutations.append(
        ("r14 custody leaked into operational map", hostile, receipt_projection)
    )
    hostile = copy.deepcopy(r14)
    hostile["replay_custody_gate_sha256"][C9.LEAN_SELF_TEST_RELATIVE] = "a" * 64
    receipt_mutations.append(
        ("r14 replay self-test custody drift", hostile, receipt_projection)
    )
    receipt_mutations.append(("r14 projection mismatch", copy.deepcopy(r14), "8" * 64))
    for label, hostile, hostile_projection in receipt_mutations:
        expect_rejection(
            lambda value=hostile, cut=hostile_projection: (
                C9.validate_lean_r14_receipt_cuts(
                    synthetic_checker,
                    receipt_lean,
                    lean_self_test,
                    r13,
                    value,
                    cut,
                )
            ),
            label,
        )
    return len(mutations) + len(receipt_mutations)


def rejected_replay_hostiles() -> int:
    fresh_raw = b"synthetic-fresh-r14"
    fresh = {"prior_replay_preservation_sha256": {C9.R13_RELATIVE: "0" * 64}}
    C9.validate_rejected_r14_exclusion(fresh_raw, fresh)
    artifacts = (
        ("REJECTED_C9_R14_SHA256", "REJECTED_C9_R14_SIZE_BYTES"),
        (
            "REJECTED_FIXED_POINT_C9_R14_SHA256",
            "REJECTED_FIXED_POINT_C9_R14_SIZE_BYTES",
        ),
        (
            "REJECTED_LOCAL_AUTHORITY_C9_R14_SHA256",
            "REJECTED_LOCAL_AUTHORITY_C9_R14_SIZE_BYTES",
        ),
    )
    for index, (digest_name, size_name) in enumerate(artifacts):
        original = (getattr(C9, digest_name), getattr(C9, size_name))
        try:
            setattr(C9, digest_name, C9.sha256(fresh_raw))
            setattr(C9, size_name, len(fresh_raw))
            expect_rejection(
                lambda: C9.validate_rejected_r14_exclusion(fresh_raw, fresh),
                f"rejected r14 artifact {index} bytes reused as current",
            )
        finally:
            setattr(C9, digest_name, original[0])
            setattr(C9, size_name, original[1])
        hostile = copy.deepcopy(fresh)
        hostile["prior_replay_preservation_sha256"][f"rejected_same_slot_{index}"] = (
            getattr(C9, digest_name)
        )
        expect_rejection(
            lambda hostile=hostile: C9.validate_rejected_r14_exclusion(
                fresh_raw, hostile
            ),
            f"rejected r14 artifact {index} entered prior replay map",
        )
    return len(artifacts) * 2


ROUTE_SOURCE_BINDINGS = (
    (
        "EXPECTED_VALIDATE_FRESH_REPLAY_SOURCE_SHA256",
        "validate_fresh_replay",
    ),
    (
        "EXPECTED_VALIDATE_C9_SOURCES_SOURCE_SHA256",
        "validate_c9_sources",
    ),
    (
        "EXPECTED_PUBLICATION_BINDING_SOURCE_SHA256",
        "publication_binding",
    ),
    (
        "EXPECTED_VALIDATE_DRAFT_SOURCE_SHA256",
        "validate_draft",
    ),
)


def expect_route_rejection_after_source_reseal(
    raw: bytes, validator: Callable[[bytes], None], label: str
) -> None:
    module = C9.parse_source_ast(raw, f"{label} hostile")
    originals = {
        constant: getattr(C9, constant) for constant, _function in ROUTE_SOURCE_BINDINGS
    }
    try:
        for constant, function_name in ROUTE_SOURCE_BINDINGS:
            function = C9.exact_function(module, function_name, f"{label} hostile")
            setattr(
                C9,
                constant,
                C9.sha256(C9.exact_source_slice(raw, function, f"{label} hostile")),
            )
        expect_rejection(lambda: validator(raw), label)
    finally:
        for constant, value in originals.items():
            setattr(C9, constant, value)


def route_source_custody_hostiles() -> int:
    raw = checker_raw
    mutations = (
        (
            "fresh replay complete-source custody",
            b"def validate_fresh_replay(\n",
            C9.validate_fresh_replay_source_routes,
        ),
        (
            "C9 source validation complete-source custody",
            b"def validate_c9_sources(\n",
            C9.validate_fresh_replay_source_routes,
        ),
        (
            "publication binding complete-source custody",
            b"def publication_binding(\n",
            C9.validate_workflow_fixture_source_routes,
        ),
        (
            "draft validation complete-source custody",
            b"def validate_draft() -> dict[str, Any]:\n",
            C9.validate_workflow_fixture_source_routes,
        ),
    )
    for label, marker, validator in mutations:
        hostile = replace_once(raw, marker, marker + b"    # custody hostile\n", label)
        expect_rejection(
            lambda hostile=hostile, validator=validator: validator(hostile), label
        )
    decorated = tuple(
        (
            f"{label} decorator custody",
            marker,
            validator,
        )
        for label, marker, validator in mutations
    )
    for label, marker, validator in decorated:
        hostile = replace_once(raw, marker, b"@staticmethod\n" + marker, label)
        expect_rejection(
            lambda hostile=hostile, validator=validator: validator(hostile), label
        )
    return len(mutations) + len(decorated)


def critical_binding_hostiles() -> int:
    raw = checker_raw
    mutations: list[tuple[str, bytes]] = [
        (
            f"critical function later rebound: {name}",
            raw + f"\n{name} = lambda *args, **kwargs: None\n".encode("ascii"),
        )
        for name in C9.CRITICAL_CHECKER_FUNCTIONS
    ]
    mutations.extend(
        (
            (
                "critical function annotated rebound",
                raw + b"\nvalidate_fresh_replay: object = object()\n",
            ),
            (
                "critical function augmented rebound",
                raw + b"\nvalidate_fresh_replay += object()\n",
            ),
            (
                "critical function import alias rebound",
                raw + b"\nimport types as validate_fresh_replay\n",
            ),
            (
                "critical function deleted",
                raw + b"\ndel validate_fresh_replay\n",
            ),
            (
                "critical function roster exposed to nested star import",
                raw + b"\nif True:\n    from attacker_controlled import *\n",
            ),
            (
                "critical function roster emptied after reviewed assignment",
                raw + b"\nCRITICAL_CHECKER_FUNCTIONS = ()\n",
            ),
            (
                "critical inherited require primitive rebound",
                raw + b"\nrequire = lambda *_args, **_kwargs: None\n",
            ),
            (
                "critical inherited sha256 primitive rebound",
                raw + b'\nsha256 = lambda _raw: "0" * 64\n',
            ),
            (
                "critical inherited parse_json primitive rebound",
                raw + b"\nparse_json = lambda *_args, **_kwargs: {}\n",
            ),
            (
                "critical inherited tree_blob primitive rebound",
                raw + b'\ntree_blob = lambda *_args, **_kwargs: b""\n',
            ),
            (
                "checker module dictionary rebinds main",
                raw + b'\nsys.modules["__main__"].main = lambda: 0\n',
            ),
            (
                "checker class body rebinds main",
                raw
                + b'\nclass _Bypass:\n    sys.modules["__main__"].main = lambda: 0\n',
            ),
        )
    )
    for label, hostile in mutations:
        expect_rejection(
            lambda hostile=hostile, label=label: C9.validate_checker_critical_bindings(
                C9.parse_source_ast(hostile, label), label
            ),
            label,
        )
    return len(mutations)


def replay_route_hostiles() -> int:
    raw = checker_raw
    C9.validate_fresh_replay_source_routes(raw)
    mutations = (
        (
            "rejected r14 exclusion call redirected",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b"    validate_rejected_r14_exclusion(r14_raw, r14)",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b"    REDIRECT.validate_rejected_r14_exclusion(r14_raw, r14)",
        ),
        (
            "rejected r14 exclusion stranded by early return",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b"    validate_rejected_r14_exclusion(r14_raw, r14)",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b"    return\n"
            b"    validate_rejected_r14_exclusion(r14_raw, r14)",
        ),
        (
            "rejected r14 exclusion stranded by early raise",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b"    validate_rejected_r14_exclusion(r14_raw, r14)",
            b'    r14 = parse_json(r14_raw, "current r14", canonical=False)\n'
            b'    raise RuntimeError("stranded")\n'
            b"    validate_rejected_r14_exclusion(r14_raw, r14)",
        ),
        (
            "r14 checksum call redirected",
            b"    projection = validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)\n    validate_lean_r14_receipt_cuts(",
            b"    projection = REDIRECT.validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)\n    validate_lean_r14_receipt_cuts(",
        ),
        (
            "r14 receipt call redirected",
            b"    projection = validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)\n    validate_lean_r14_receipt_cuts(\n        v9_checker_raw,",
            b"    projection = validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)\n    REDIRECT.validate_lean_r14_receipt_cuts(\n        v9_checker_raw,",
        ),
        (
            "rejected current-source exclusion inverted",
            b"        != (\n"
            b"            REJECTED_LOCAL_AUTHORITY_C9_CURRENT_SOURCE_SHA256,\n",
            b"        == (\n"
            b"            REJECTED_LOCAL_AUTHORITY_C9_CURRENT_SOURCE_SHA256,\n",
        ),
        (
            "r14 generator excluded from operational custody",
            b"        LEAN_SELF_TEST_RELATIVE,\n    }\n    operational_c9_paths",
            b'        LEAN_SELF_TEST_RELATIVE,\n        "scripts/generate-lean-4.33-replay.py",\n    }\n    operational_c9_paths',
        ),
        (
            "r14 source-route validator omitted",
            b"    checker_source = tree_blob(c9_entries, CHECKER_RELATIVE)\n"
            b"    validate_fresh_replay_source_routes(checker_source)\n"
            b"    validate_workflow_fixture_source_routes(checker_source)",
            b"    pass  # omitted r14 source-route validator\n"
            b"    validate_workflow_fixture_source_routes(checker_source)",
        ),
        (
            "r14 operational validator redirected",
            b"    publication_binding(c8_entries, c9_entries)\n    validate_fresh_replay(c8_entries, c9_entries)",
            b"    publication_binding(c8_entries, c9_entries)\n    REDIRECT.validate_fresh_replay(c8_entries, c9_entries)",
        ),
        (
            "r14 operational comparison loop omitted",
            b'    for path in operational_c9_paths:\n        require(\n            operational.get(path) == sha256(tree_blob(c9_entries, path)),\n            f"r14 does not bind exact C9 operational source: {path}",\n        )\n    active_claims',
            b"    pass  # omitted r14 operational-source comparison\n    active_claims",
        ),
        (
            "C9 source replay route stranded by early return",
            b"def validate_c9_sources(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n",
            b"def validate_c9_sources(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n"
            b"    return {}, {}, {}\n",
        ),
        (
            "C9 source replay route stranded by early raise",
            b"def validate_c9_sources(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n",
            b"def validate_c9_sources(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n"
            b'    raise RuntimeError("stranded")\n',
        ),
        (
            "fresh replay validation truncated after rejected exclusion",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n"
            b"    r13_raw = tree_blob(c8_entries, R13_RELATIVE)",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n"
            b"    return\n"
            b"    r13_raw = tree_blob(c8_entries, R13_RELATIVE)",
        ),
        (
            "C9 source validation truncated after replay prefix",
            b"    policy_raw = tree_blob(c9_entries, POLICY_RELATIVE)",
            b"    return {}, {}, {}\n"
            b"    policy_raw = tree_blob(c9_entries, POLICY_RELATIVE)",
        ),
        (
            "fresh replay converted to an unconsumed generator",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n"
            b"    if False:\n        yield None\n",
        ),
        (
            "fresh replay replaced the process image",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n",
            b"    validate_rejected_r14_exclusion(r14_raw, r14)\n"
            b'    os.execl("/usr/bin/true", "true")\n',
        ),
        (
            "fresh replay helper shadowed by a default parameter",
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n) -> None:\n",
            b"    c8_entries: dict[str, Any],\n"
            b"    c9_entries: dict[str, Any],\n"
            b"    validate_rejected_r14_exclusion=lambda *_args: None,\n"
            b") -> None:\n",
        ),
        (
            "C9 source validators shadowed by default parameters",
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n",
            b"    c8_entries: dict[str, Any],\n"
            b"    c9_entries: dict[str, Any],\n"
            b"    c9: str,\n"
            b"    c9_tree: str,\n"
            b"    publication_binding=lambda *_args: None,\n"
            b"    validate_fresh_replay=lambda *_args: None,\n"
            b") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n",
        ),
    )
    for label, before, after in mutations:
        hostile = replace_once(raw, before, after, label)
        expect_route_rejection_after_source_reseal(
            hostile, C9.validate_fresh_replay_source_routes, label
        )
    return len(mutations)


def workflow_fixture_route_hostiles() -> int:
    raw = checker_raw
    C9.validate_workflow_fixture_source_routes(raw)
    mutations = (
        (
            "publication fixture proof redirected",
            b"    validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"    )\n"
            b"    values = {",
            b"    REDIRECT.validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"    )\n"
            b"    values = {",
        ),
        (
            "draft fixture proof redirected",
            b"    validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        read_file(WORKFLOW_PDF_SELF_TEST_RELATIVE, mode=0o755),\n"
            b"    )",
            b"    REDIRECT.validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        read_file(WORKFLOW_PDF_SELF_TEST_RELATIVE, mode=0o755),\n"
            b"    )",
        ),
        (
            "publication fixture proof made unreachable",
            b"def publication_binding(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n"
            b") -> dict[str, Any]:\n",
            b"def publication_binding(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n"
            b") -> dict[str, Any]:\n"
            b"    return {}\n",
        ),
        (
            "draft fixture proof made unreachable",
            b"def validate_draft() -> dict[str, Any]:\n",
            b"def validate_draft() -> dict[str, Any]:\n    return {}\n",
        ),
        (
            "publication fixture proof stranded by early raise",
            b"def publication_binding(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n"
            b") -> dict[str, Any]:\n",
            b"def publication_binding(\n"
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n"
            b") -> dict[str, Any]:\n"
            b'    raise RuntimeError("stranded")\n',
        ),
        (
            "draft fixture proof stranded by early raise",
            b"def validate_draft() -> dict[str, Any]:\n",
            b"def validate_draft() -> dict[str, Any]:\n"
            b'    raise RuntimeError("stranded")\n',
        ),
        (
            "publication validation truncated after fixture proof",
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"    )\n"
            b"    values = {",
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"    )\n"
            b"    return {}\n"
            b"    values = {",
        ),
        (
            "draft validation truncated after fixture proof",
            b"        read_file(WORKFLOW_PDF_SELF_TEST_RELATIVE, mode=0o755),\n"
            b"    )\n"
            b"    for path in (",
            b"        read_file(WORKFLOW_PDF_SELF_TEST_RELATIVE, mode=0o755),\n"
            b"    )\n"
            b"    return {}\n"
            b"    for path in (",
        ),
        (
            "publication helper shadowed by a default parameter",
            b"    c8_entries: dict[str, Any], c9_entries: dict[str, Any]\n"
            b") -> dict[str, Any]:\n",
            b"    c8_entries: dict[str, Any],\n"
            b"    c9_entries: dict[str, Any],\n"
            b"    validate_workflow_pdf_fixture_correction=lambda *_args: None,\n"
            b") -> dict[str, Any]:\n",
        ),
        (
            "draft helper shadowed by a default parameter",
            b"def validate_draft() -> dict[str, Any]:\n",
            b"def validate_draft(\n"
            b"    validate_workflow_pdf_fixture_correction=lambda *_args: None,\n"
            b") -> dict[str, Any]:\n",
        ),
        (
            "publication converted to an unconsumed generator",
            b"    validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n",
            b"    if False:\n        yield None\n"
            b"    validate_workflow_pdf_fixture_correction(\n"
            b"        tree_blob(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n"
            b"        tree_blob(c9_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE),\n",
        ),
        (
            "draft replaced the process image",
            b"def validate_draft() -> dict[str, Any]:\n",
            b"def validate_draft() -> dict[str, Any]:\n"
            b'    os.execl("/usr/bin/true", "true")\n',
        ),
    )
    for label, before, after in mutations:
        hostile = replace_once(raw, before, after, label)
        expect_route_rejection_after_source_reseal(
            hostile, C9.validate_workflow_fixture_source_routes, label
        )
    return len(mutations)


def main() -> int:
    try:
        groups = {
            "bounded_block_custody_hostiles_rejected": bounded_block_custody_hostiles(),
            "capture_ast_hostiles_rejected": capture_ast_hostiles(),
            "critical_binding_hostiles_rejected": critical_binding_hostiles(),
            "rebind_difference_guard_hostiles_rejected": rebind_difference_guard_hostiles(),
            "justfile_hostiles_rejected": justfile_hostiles(),
            "lean_cut_hostiles_rejected": lean_cut_hostiles(),
            "narrative_semantic_hostiles_rejected": narrative_semantic_hostiles(),
            "policy_hostiles_rejected": policy_hostiles(),
            "rejected_replay_hostiles_rejected": rejected_replay_hostiles(),
            "replay_route_hostiles_rejected": replay_route_hostiles(),
            "route_source_custody_hostiles_rejected": route_source_custody_hostiles(),
            "runtime_guard_hostiles_rejected": runtime_guard_hostiles(),
            "self_test_loader_hostiles_rejected": self_test_loader_hostiles(),
            "schema_hostiles_rejected": schema_hostiles(),
            "workflow_fixture_reconstruction_hostiles_rejected": workflow_fixture_reconstruction_hostiles(),
            "workflow_fixture_route_hostiles_rejected": workflow_fixture_route_hostiles(),
            "workflow_hostiles_rejected": workflow_hostiles(),
        }
        require(
            groups
            == {
                "bounded_block_custody_hostiles_rejected": 3,
                "capture_ast_hostiles_rejected": 99,
                "critical_binding_hostiles_rejected": 57,
                "rebind_difference_guard_hostiles_rejected": 10,
                "justfile_hostiles_rejected": 21,
                "lean_cut_hostiles_rejected": 19,
                "narrative_semantic_hostiles_rejected": 77,
                "policy_hostiles_rejected": 50,
                "rejected_replay_hostiles_rejected": 6,
                "replay_route_hostiles_rejected": 18,
                "route_source_custody_hostiles_rejected": 8,
                "runtime_guard_hostiles_rejected": 48,
                "self_test_loader_hostiles_rejected": 15,
                "schema_hostiles_rejected": 22,
                "workflow_fixture_reconstruction_hostiles_rejected": 5,
                "workflow_fixture_route_hostiles_rejected": 12,
                "workflow_hostiles_rejected": 31,
            },
            "composite-v9 hostile family counts changed",
        )
        result = {
            "checker": {
                "path": "scripts/check-ksg-m1a-composite-v9.py",
                "sha256": CHECKER_SHA256,
                "size_bytes": CHECKER_SIZE_BYTES,
            },
            **groups,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v9-self-test/v1",
            "total_hostiles_rejected": sum(groups.values()),
        }
        sys.stdout.buffer.write(C9.canonical_json(result, pretty=False))
        return 0
    except (C9.ContractError, OSError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
