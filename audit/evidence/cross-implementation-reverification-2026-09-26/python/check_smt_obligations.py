#!/usr/bin/env python3
# Author: Sepehr Mahmoudian, 2026.
"""Check nine declared SMT files and their nonvacuous backgrounds with Z3 4.16.0.

Usage: check_smt_obligations.py <source-root>

This is a closed source-profile checker, not a general SMT-LIB parser or sort checker.
It accepts the ASCII, unquoted-symbol, quantifier-free syntax used by the nine files.
Each file has one terminal negated goal and one query, with an optional final exit.
Solver success requires zero status, empty stderr and exactly the expected result line.
The PID3 zeta check requires direct sums of distinct bare atoms with coefficient +1;
it does not normalize arbitrary algebraically equivalent expressions.
"""

from __future__ import annotations

import itertools
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_Z3 = "Z3 version 4.16.0 - 64 bit"
TIMEOUT_SECONDS = 120
MAX_SOURCE_BYTES = 1_000_000
MAX_TOKENS = 100_000
MAX_DEPTH = 128
EXPECTED_PATHS = (
    "audit/formal/z3/pid2-reconstruction.smt2",
    "audit/formal/z3/pid2-self-redundancy-mobius.smt2",
    "audit/formal/z3/pid2-source-swap.smt2",
    "audit/formal/z3/pid3-mobius-reconstruction.smt2",
    "audit/formal/z3/pid3-source-permutation.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2",
)
PID3_PATH = "audit/formal/z3/pid3-mobius-reconstruction.smt2"
SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\Z")
NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")
TOKEN = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_.-]*|:[A-Za-z][A-Za-z0-9_-]*|[0-9]+(?:\.[0-9]+)?|[+*/<>=-]+)\Z")
SORTS = {"Bool", "Int", "Real"}
OPERATORS = {"+", "-", "=", "<=", ">=", "<", ">", "and", "not", "ite"}


class CheckError(Exception):
    """An input or subprocess failed the closed acceptance predicate."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def tokenize(text: str) -> list[str]:
    require(text.isascii(), "SMT source must be ASCII")
    require(len(text) <= MAX_SOURCE_BYTES, "SMT source exceeds size bound")
    tokens: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in " \t\r\n":
            index += 1
            continue
        if char == ";":
            end = text.find("\n", index)
            index = len(text) if end < 0 else end + 1
            continue
        start = index
        if char in "()":
            index += 1
        elif char == '"':
            index += 1
            while index < len(text):
                current = text[index]
                require(current not in "\\\r\n" and ord(current) >= 32,
                        "unsupported character in string")
                if current == '"':
                    if index + 1 < len(text) and text[index + 1] == '"':
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            else:
                raise CheckError("unterminated string")
        else:
            while index < len(text) and text[index] not in " \t\r\n();":
                index += 1
            require(TOKEN.fullmatch(text[start:index]) is not None,
                    "unsupported SMT token")
        tokens.append(text[start:index])
        require(len(tokens) <= MAX_TOKENS, "SMT token limit exceeded")
    return tokens


def parse_smt(text: str) -> list[tuple]:
    tokens = tokenize(text)
    cursor = 0

    def parse_node(depth: int):
        nonlocal cursor
        require(depth <= MAX_DEPTH, "SMT nesting limit exceeded")
        require(cursor < len(tokens), "unterminated expression")
        token = tokens[cursor]
        cursor += 1
        if token == "(":
            children = []
            while cursor < len(tokens) and tokens[cursor] != ")":
                children.append(parse_node(depth + 1))
            require(cursor < len(tokens), "unterminated expression")
            cursor += 1
            return tuple(children)
        require(token != ")", "unexpected closing parenthesis")
        return token

    forms = []
    while cursor < len(tokens):
        node = parse_node(0)
        require(isinstance(node, tuple) and bool(node),
                "every top-level form must be a nonempty list")
        forms.append(node)
    return forms


def render(node) -> str:
    if isinstance(node, str):
        return node
    return "(" + " ".join(render(item) for item in node) + ")"


def require_expression(node, symbols: set[str]) -> None:
    if isinstance(node, str):
        require(node in symbols or node in {"true", "false"}
                or NUMBER.fullmatch(node) is not None,
                f"unsupported or undeclared expression atom: {node}")
        return
    require(bool(node) and isinstance(node[0], str), "invalid expression head")
    require(node[0] in OPERATORS or node[0] in symbols,
            f"unsupported or undeclared expression operator: {node[0]}")
    for child in node[1:]:
        require_expression(child, symbols)


def validate_source(relative: str, text: str) -> tuple[list[tuple], int, int]:
    require(relative in EXPECTED_PATHS, "undeclared proof path")
    forms = parse_smt(text)
    logic = "QF_LRA" if relative.startswith("audit/formal/z3/") else "QF_UFLIRA"
    required_prefix = [
        ("set-info", ":smt-lib-version", "2.6"),
        ("set-info", ":category", '"crafted"'),
        ("set-logic", logic),
    ]
    require(forms[:3] == required_prefix, "unexpected metadata or logic prefix")
    end = len(forms) - 1 if forms and forms[-1] == ("exit",) else len(forms)
    require(end >= 5 and forms[end - 1] == ("check-sat",),
            "one terminal check-sat is required before optional exit")
    goal_index = end - 2
    symbols: set[str] = set()
    assertions = 0
    goals = []
    for index, form in enumerate(forms[3:end - 1], 3):
        head = form[0]
        require(isinstance(head, str), "command head must be a symbol")
        if head in {"declare-const", "declare-fun", "define-fun"}:
            expected_arity = {"declare-const": 3, "declare-fun": 4, "define-fun": 5}[head]
            require(len(form) == expected_arity, f"invalid {head} arity")
            name = form[1]
            require(isinstance(name, str) and SYMBOL.fullmatch(name) is not None,
                    "declaration name is outside the supported symbol profile")
            require(name not in symbols, f"duplicate declaration: {name}")
            if head == "declare-const":
                require(form[2] in SORTS, "unsupported constant sort")
            elif head == "declare-fun":
                require(isinstance(form[2], tuple)
                        and all(isinstance(sort, str) and sort in SORTS for sort in form[2])
                        and isinstance(form[3], str) and form[3] in SORTS,
                        "unsupported function signature")
            else:
                require(form[2] == () and isinstance(form[3], str) and form[3] in SORTS,
                        "only nullary definitions of declared sorts are supported")
                require_expression(form[4], symbols)
            symbols.add(name)
        elif head == "assert":
            require(len(form) == 2, "invalid assertion arity")
            require_expression(form[1], symbols)
            assertions += 1
            body = form[1]
            if isinstance(body, tuple) and body and body[0] == "not":
                require(len(body) == 2, "invalid terminal negation")
                goals.append(index)
        else:
            raise CheckError(f"unsupported or nonterminal command: {head}")
    require(goals == [goal_index], "exactly one terminal negated goal is required")
    return forms, goal_index, assertions


def background_source(forms: list[tuple], goal_index: int) -> str:
    return "\n".join(render(form) for index, form in enumerate(forms)
                     if index != goal_index) + "\n"


def antichain_name(sets: tuple[int, ...]) -> str:
    return "_".join(sorted(format(mask, "03b") for mask in sets))


def check_pid3_order(forms: list[tuple]) -> int:
    recovered: dict[str, list[str]] = {}
    for form in forms:
        if form[0] != "define-fun" or not str(form[1]).startswith("recovered_"):
            continue
        require(len(form) == 5 and form[2:4] == ((), "Real"),
                "invalid recovered definition signature")
        name = form[1][len("recovered_"):]
        require(name not in recovered, f"duplicate recovered definition: {name}")
        body = form[4]
        if isinstance(body, str):
            terms = [body]
        else:
            require(len(body) >= 3 and body[0] == "+",
                    f"zeta sum {name} must be a flat sum of bare atoms")
            terms = list(body[1:])
        require(all(isinstance(term, str)
                    and re.fullmatch(r"atom_[01_]+", term) is not None for term in terms),
                f"zeta sum {name} contains a coefficient, operator or non-atom term")
        require(len(set(terms)) == len(terms), f"zeta sum {name} repeats an atom")
        recovered[name] = sorted(term[len("atom_"):] for term in terms)
    masks = [1, 2, 4, 3, 5, 6, 7]
    antichains = [combo for size in range(1, 4)
                  for combo in itertools.combinations(masks, size)
                  if all(a & b not in (a, b) for a, b in itertools.combinations(combo, 2))]
    require(len(antichains) == 18, "expected 18 enumerated antichains")
    require(set(recovered) == {antichain_name(a) for a in antichains},
            "recovered definitions must name exactly the 18 antichains")
    for alpha in antichains:
        expected = sorted(antichain_name(beta) for beta in antichains
                          if all(any(b & a == b for b in beta) for a in alpha))
        require(recovered[antichain_name(alpha)] == expected,
                f"zeta sum for {antichain_name(alpha)} differs from the MGW down-set")
    return len(antichains)


def read_sources(root: Path) -> dict[str, str]:
    require(root.is_dir() and not root.is_symlink(), "source root must be a real directory")
    directories = {str(Path(relative).parent) for relative in EXPECTED_PATHS}
    for relative_dir in sorted(directories):
        directory = root
        for part in Path(relative_dir).parts:
            directory = directory / part
            require(directory.is_dir() and not directory.is_symlink(),
                    f"proof directory is absent or symlinked: {directory}")
        expected = {Path(relative).name for relative in EXPECTED_PATHS
                    if str(Path(relative).parent) == relative_dir}
        require({entry.name for entry in directory.iterdir()} == expected,
                f"proof inventory differs in {relative_dir}")
    sources = {}
    for relative in EXPECTED_PATHS:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"not a regular proof file: {relative}")
        require(path.stat().st_size <= MAX_SOURCE_BYTES, f"proof too large: {relative}")
        raw = path.read_bytes()
        require(len(raw) <= MAX_SOURCE_BYTES, f"proof too large: {relative}")
        try:
            sources[relative] = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise CheckError(f"proof is not ASCII: {relative}") from error
    return sources


def require_exact_result(process: subprocess.CompletedProcess, expected: str, label: str) -> None:
    require(process.returncode == 0 and process.stderr == b""
            and process.stdout == (expected + "\n").encode("ascii"),
            f"{label}: expected clean {expected!r}; exit={process.returncode}, "
            f"stdout={process.stdout!r}, stderr={process.stderr!r}")


def invoke_z3(arguments: list[str], source: bytes | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["z3", *arguments], input=source, capture_output=True,
                              timeout=TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CheckError(f"Z3 execution failed: {error}") from error


def require_version() -> None:
    require_exact_result(invoke_z3(["--version"]), EXPECTED_Z3, "solver version")


def run_z3(text: str, expected: str, label: str) -> str:
    process = invoke_z3(["-T:120", "-smt2", "-in"], text.encode("ascii"))
    require_exact_result(process, expected, label)
    return expected


def check_root(root: Path) -> None:
    sources = read_sources(root)
    parsed = {relative: validate_source(relative, text) for relative, text in sources.items()}
    count = check_pid3_order(parsed[PID3_PATH][0])
    require_version()
    print(f"solver: {EXPECTED_Z3}")
    print("file | complete file | background without negated goal | assertions")
    for relative, text in sources.items():
        forms, goal_index, assertions = parsed[relative]
        complete = run_z3(text, "unsat", relative + " complete")
        background = run_z3(background_source(forms, goal_index), "sat", relative + " background")
        print(f"{relative} | {complete} | {background} | {assertions}")
    print(f"pid3 zeta sums: all {count} match the MGW down-sets")
    print(f"PASS: {len(sources)} files unsat with satisfiable backgrounds; PID3 order checked")


def main() -> int:
    try:
        require(len(sys.argv) == 2, "usage: check_smt_obligations.py <source-root>")
        check_root(Path(sys.argv[1]))
    except (CheckError, OSError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
