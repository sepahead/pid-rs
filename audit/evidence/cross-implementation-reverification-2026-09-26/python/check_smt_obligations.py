#!/usr/bin/env python3
"""Check the repository's SMT obligations for vacuity and the PID3 lattice order.

Usage: check_smt_obligations.py <source-root>

For every file in audit/formal/z3 and audit/formal/z3-ksg-harmonic under <source-root>:

1. the complete file must be unsat under Z3 4.16.0;
2. the file must contain exactly one top-level assertion of the form (assert (not ...)),
   its negated goal; and
3. the file without that assertion (its background) must be sat, so the unsat result does
   not come from contradictory background assertions.

For audit/formal/z3/pid3-mobius-reconstruction.smt2 it also checks that every zeta sum
`recovered_<antichain>` adds exactly the atoms of the antichains below it in the order of
Makkeh, Gutknecht and Wibral: beta <= alpha when every set in alpha contains a set in beta.
The 18 antichains are enumerated independently. Any failure exits with status 1.
"""

from __future__ import annotations

import itertools
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_Z3 = "Z3 version 4.16.0 - 64 bit"
DIRECTORIES = ("audit/formal/z3", "audit/formal/z3-ksg-harmonic")
EXPECTED_FILES = 9


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def top_level_expressions(text: str) -> list[str]:
    """Split SMT-LIB text into top-level expressions, ignoring ';' comments outside strings."""
    kept, in_string, in_comment = [], False, False
    for char in text:
        if in_comment:
            if char == "\n":
                in_comment = False
                kept.append(char)
            continue
        if char == '"':
            in_string = not in_string
        elif char == ";" and not in_string:
            in_comment = True
            continue
        kept.append(char)
    if in_string:
        fail("unterminated string literal")
    body = "".join(kept)
    expressions, depth, start, in_string = [], 0, None, False
    for index, char in enumerate(body):
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "(":
            if depth == 0:
                start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                fail("unbalanced parentheses")
            if depth == 0:
                expressions.append(body[start : index + 1])
    if depth != 0:
        fail("unbalanced parentheses")
    return expressions


def run_z3(text: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".smt2", delete=False) as handle:
        handle.write(text)
        path = handle.name
    try:
        result = subprocess.run(
            ["z3", "-T:120", path], capture_output=True, text=True, check=False
        )
    finally:
        Path(path).unlink()
    words = result.stdout.split()
    return words[0] if words else "no-output"


def antichain_name(sets: tuple[int, ...]) -> str:
    return "_".join(sorted(format(mask, "03b") for mask in sets))


def check_pid3_order(text: str) -> int:
    recovered: dict[str, list[str]] = {}
    for expression in top_level_expressions(text):
        match = re.match(r"\(define-fun recovered_([01_]+) \(\) Real(.*)\)$", expression, re.S)
        if match:
            recovered[match.group(1)] = sorted(re.findall(r"atom_([01_]+)", match.group(2)))
    masks = [1, 2, 4, 3, 5, 6, 7]
    antichains = []
    for size in range(1, 4):
        for combo in itertools.combinations(masks, size):
            if all(a & b not in (a, b) for a, b in itertools.combinations(combo, 2)):
                antichains.append(combo)
    if len(antichains) != 18:
        fail(f"expected 18 antichains, enumerated {len(antichains)}")
    names = {antichain_name(a) for a in antichains}
    if set(recovered) != names:
        fail("the recovered_* definitions do not name exactly the 18 antichains")

    def below(beta: tuple[int, ...], alpha: tuple[int, ...]) -> bool:
        return all(any(b & a == b for b in beta) for a in alpha)

    for alpha in antichains:
        expected = sorted(antichain_name(beta) for beta in antichains if below(beta, alpha))
        if recovered[antichain_name(alpha)] != expected:
            fail(f"zeta sum for {antichain_name(alpha)} differs from the MGW down-set")
    return len(antichains)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: check_smt_obligations.py <source-root>")
    root = Path(sys.argv[1])
    version = subprocess.run(["z3", "--version"], capture_output=True, text=True, check=False)
    if version.stdout.strip() != EXPECTED_Z3:
        fail(f"expected {EXPECTED_Z3!r}, found {version.stdout.strip()!r}")
    files = sorted(p for d in DIRECTORIES for p in (root / d).glob("*.smt2"))
    if len(files) != EXPECTED_FILES:
        fail(f"expected {EXPECTED_FILES} SMT files, found {len(files)}")
    print(f"solver: {EXPECTED_Z3}")
    print("file | complete file | background without negated goal | assertions")
    for path in files:
        text = path.read_text()
        expressions = top_level_expressions(text)
        asserts = [e for e in expressions if re.match(r"\(\s*assert\b", e)]
        goals = [e for e in asserts if re.match(r"\(\s*assert\s*\(\s*not\b", e)]
        if len(goals) != 1:
            fail(f"{path.name}: expected one negated goal, found {len(goals)}")
        complete = run_z3(text)
        background = run_z3("\n".join(e for e in expressions if e is not goals[0]) + "\n")
        relative = path.relative_to(root).as_posix()
        print(f"{relative} | {complete} | {background} | {len(asserts)}")
        if complete != "unsat":
            fail(f"{relative}: complete file is {complete}, expected unsat")
        if background != "sat":
            fail(f"{relative}: background is {background}, expected sat")
    count = check_pid3_order((root / "audit/formal/z3/pid3-mobius-reconstruction.smt2").read_text())
    print(f"pid3 zeta sums: all {count} match the MGW down-sets")
    print(f"PASS: {len(files)} files unsat with satisfiable backgrounds; PID3 order checked")


if __name__ == "__main__":
    main()
