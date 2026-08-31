#!/usr/bin/env python3
"""Check an exact-rational enclosure of the contextual rare-tail counterexample.

This checker proves a narrow conditional statement about the displayed analytical
activation formulas.  It does not validate a thesis, a PID measure, or any displayed
contextual atom table, and it does not attribute a defect to a Wibral-coauthored paper.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
from typing import Any, Final, NoReturn


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE: Final[Path] = ROOT / "audit/evidence/contextual-rare-tail-counterexample-v1.json"
FORMAT: Final[str] = "/pid-rs/contextual-rare-tail-counterexample/v1"

Q: Final[Fraction] = Fraction(222_493, 250_000)
SOURCE_CELL_MASS: Final[Fraction] = Q / 2
R: Final[Fraction] = Fraction(2)
C: Final[Fraction] = Fraction(2)
E4_TERMS: Final[int] = 80
E2_TERMS: Final[int] = 70
NESTED_EXP_TERMS: Final[int] = 180
MODULATORY_LOWER: Final[Fraction] = Fraction(317, 10**27)
MODULATORY_UPPER: Final[Fraction] = Fraction(319, 10**27)
COMBINED_LOWER: Final[Fraction] = Fraction(429, 10**28)
COMBINED_UPPER: Final[Fraction] = Fraction(431, 10**28)
HALF_GAP_BELOW_ONE: Final[Fraction] = Fraction(1, 2**54)


class CheckError(RuntimeError):
    """Fail-closed evidence or proof error."""


def fail(message: str) -> NoReturn:
    raise CheckError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    fail(f"non-finite JSON number forbidden: {value}")


def read_regular(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode), "evidence must be a regular file")
        require(before.st_nlink == 1, "evidence may not be a hard link")
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"cannot safely open evidence: {error}")
    try:
        opened = os.fstat(descriptor)
        raw_buffer = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            raw_buffer.extend(chunk)
        closed = os.fstat(descriptor)
    except OSError as error:
        fail(f"cannot read evidence: {error}")
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        fail(f"cannot restat evidence: {error}")

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

    require(
        identity(before) == identity(opened) == identity(closed) == identity(after),
        "evidence changed during read",
    )
    require(len(raw_buffer) == after.st_size, "short or overlong evidence read")
    return bytes(raw_buffer)


def exp_bounds_nonnegative(x: Fraction, terms: int) -> tuple[Fraction, Fraction]:
    """Return rigorous Taylor lower/upper bounds for exp(x), x >= 0.

    The partial sum through ``terms`` is a lower bound.  Starting at the next
    term, all successive ratios are bounded by x/(terms+2), so a geometric
    majorant bounds the positive tail.
    """

    require(x >= 0, "exp enclosure requires a nonnegative argument")
    require(terms >= 1, "exp enclosure requires a positive term count")
    term = Fraction(1)
    partial = term
    for index in range(1, terms + 1):
        term = term * x / index
        partial += term
    next_term = term * x / (terms + 1)
    ratio_bound = x / (terms + 2)
    require(ratio_bound < 1, "Taylor tail ratio must be below one")
    remainder_upper = next_term / (1 - ratio_bound)
    return partial, partial + remainder_upper


def hash_integer(digest: Any, value: int) -> None:
    require(value >= 0, "interval digest accepts nonnegative integers only")
    encoded = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)


def interval_digest(intervals: list[tuple[Fraction, Fraction]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"pid-rs/contextual-rare-tail-exact-intervals/v1\0")
    for lower, upper in intervals:
        require(Fraction(0) < lower < upper, "invalid positive interval")
        for value in (lower, upper):
            hash_integer(digest, value.numerator)
            hash_integer(digest, value.denominator)
    return digest.hexdigest()


def derive() -> dict[str, Any]:
    e4_lower, e4_upper = exp_bounds_nonnegative(R * C, E4_TERMS)
    e2_lower, e2_upper = exp_bounds_nonnegative(C, E2_TERMS)

    # At r=c=2, A_m=(r/2)(1+exp(rc))=1+exp(4).
    activation_lower = 1 + e4_lower
    activation_upper = 1 + e4_upper
    exp_activation_lower, _ = exp_bounds_nonnegative(activation_lower, NESTED_EXP_TERMS)
    _, exp_activation_upper = exp_bounds_nonnegative(activation_upper, NESTED_EXP_TERMS)

    modulatory_tail_lower = 1 / (1 + exp_activation_upper)
    modulatory_tail_upper = 1 / (1 + exp_activation_lower)
    modulatory_joint_lower = SOURCE_CELL_MASS * modulatory_tail_lower
    modulatory_joint_upper = SOURCE_CELL_MASS * modulatory_tail_upper

    # A_b=A_m+c and exp(A_b)=exp(A_m)exp(2), so no approximate subtraction occurs.
    exp_combined_lower = exp_activation_lower * e2_lower
    exp_combined_upper = exp_activation_upper * e2_upper
    combined_tail_lower = 1 / (1 + exp_combined_upper)
    combined_tail_upper = 1 / (1 + exp_combined_lower)
    combined_joint_lower = SOURCE_CELL_MASS * combined_tail_lower
    combined_joint_upper = SOURCE_CELL_MASS * combined_tail_upper

    require(
        MODULATORY_LOWER < modulatory_joint_lower < modulatory_joint_upper < MODULATORY_UPPER,
        "modulatory joint cell escaped the declared exact interval",
    )
    require(
        COMBINED_LOWER < combined_joint_lower < combined_joint_upper < COMBINED_UPPER,
        "combined joint cell escaped the declared exact interval",
    )
    require(modulatory_tail_lower > 0, "modulatory analytical tail is not positive")
    require(combined_tail_lower > 0, "combined analytical tail is not positive")
    require(modulatory_tail_upper < HALF_GAP_BELOW_ONE, "modulatory tail is not below the binary64 half-gap")
    require(combined_tail_upper < HALF_GAP_BELOW_ONE, "combined tail is not below the binary64 half-gap")

    float_activation_modulatory = 0.5 * 2.0 * (1.0 + math.exp(4.0))
    float_activation_combined = float_activation_modulatory + 2.0
    float_p_modulatory = 1.0 / (1.0 + math.exp(-float_activation_modulatory))
    float_p_combined = 1.0 / (1.0 + math.exp(-float_activation_combined))
    require(float_p_modulatory == 1.0, "binary64 modulatory logistic observation changed")
    require(float_p_combined == 1.0, "binary64 combined logistic observation changed")
    require(1.0 - float_p_modulatory == 0.0, "binary64 modulatory subtraction did not erase the tail")
    require(1.0 - float_p_combined == 0.0, "binary64 combined subtraction did not erase the tail")

    intervals = [
        (e4_lower, e4_upper),
        (activation_lower, activation_upper),
        (exp_activation_lower, exp_activation_upper),
        (modulatory_tail_lower, modulatory_tail_upper),
        (modulatory_joint_lower, modulatory_joint_upper),
        (e2_lower, e2_upper),
        (exp_combined_lower, exp_combined_upper),
        (combined_tail_lower, combined_tail_upper),
        (combined_joint_lower, combined_joint_upper),
    ]

    return {
        "claim": {
            "logical_effect": "refutes",
            "refuted_claim": "For the stated finite contextual law at r=c=2, forming the zero-response probability as binary64 1.0 - p preserves the positive analytical support.",
            "scope": "The rational q=0.889972 source cell and the stated modulatory and combined activation formulas at r=c=2 under IEEE-754 binary64 round-to-nearest, ties-to-even.",
            "does_not_refute": "The analytical contextual law, categorical MGW SxPID, BROJA, the rounded headline atom values, or support-change continuity.",
        },
        "format": FORMAT,
        "inputs": {
            "combined_activation": "A_b(r,c)=(r/2)(1+exp(rc))+c",
            "modulatory_activation": "A_m(r,c)=(r/2)(1+exp(rc))",
            "q": "222493/250000",
            "r": "2",
            "c": "2",
            "source_cell_mass": "222493/500000",
        },
        "proof": {
            "arithmetic": "exact positive rationals",
            "combined_joint_cell_open_interval": ["4.29e-26", "4.31e-26"],
            "e2_taylor_terms": E2_TERMS,
            "e4_taylor_terms": E4_TERMS,
            "exact_interval_digest": interval_digest(intervals),
            "modulatory_joint_cell_open_interval": ["3.17e-25", "3.19e-25"],
            "nested_exp_taylor_terms": NESTED_EXP_TERMS,
            "rounding_boundary": "Both exact conditional zero-response tails are positive and strictly below 2^-54, the halfway distance from 1 to the next binary64 value below 1.",
            "taylor_tail_bound": "After the retained partial sum, the positive tail is bounded by the next term divided by 1-x/(n+2).",
        },
        "runtime_observation": {
            "binary64_combined_p_x1": "1.0",
            "binary64_combined_one_minus_p_x1": "0.0",
            "binary64_modulatory_p_x1": "1.0",
            "binary64_modulatory_one_minus_p_x1": "0.0",
            "status": "reproduced",
        },
        "source_observations": {
            "attribution_boundary": "This is an implementation-level counterexample for the observed local generator bytes. It is not a defect claim about a Wibral-coauthored paper, the MGW categorical definition, the Schick-Poland measure-theoretic construction, the Ehrlich continuous construction, or BROJA.",
            "boundary": "Hash-only observations of dirty external thesis working bytes; the mathematical proof above is conditional on the formulas it states and does not authenticate the authorship, publication status, or provenance of those external bytes.",
            "contextual_chapter_sha256": "2889d25ef39b5a568b0faf2dd1dfafe2cbc8c8f0fec2233c21d061e98bd1582f",
            "contextual_replication_generator_sha256": "a342c61f96eff5270107daacc3148d536a409ac7192c91e404767c208434c5db",
            "target_correct_broja_generator_sha256": "0e28ffed2ca51aa72e35e42a748bdf0934b22aaa40cfff0e6db4cbaaa8975f6d",
        },
        "status": "established conditional mathematical counterexample plus reproduced binary64 observation",
        "units": "probability mass; not bits or nats",
    }


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def validate_evidence(path: Path, expected: dict[str, Any]) -> None:
    raw = read_regular(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"evidence is not UTF-8: {error}")
    try:
        value = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (json.JSONDecodeError, CheckError) as error:
        fail(f"invalid evidence JSON: {error}")
    require(isinstance(value, dict), "evidence root must be an object")
    require(raw == canonical_bytes(value), "evidence JSON is not in exact canonical form")
    require(value == expected, "evidence content differs from exact reconstruction")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--emit", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    arguments = parse_args(argv)
    try:
        result = derive()
        if arguments.emit:
            sys.stdout.buffer.write(canonical_bytes(result))
        else:
            validate_evidence(arguments.evidence, result)
            print(
                "OK: exact contextual rare-tail counterexample; positive analytical cells are erased by the binary64 1.0 - p route"
            )
    except CheckError as error:
        print(f"ERROR: contextual rare-tail counterexample rejected: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
