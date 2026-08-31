#!/usr/bin/env python3
"""Hostile tests for the 23-page mathematical-results guide hosted raw v2 profile.

Pass the exact retained CI-matched v2 fixture as the sole argument.  Every subprocess
control and hostile is run under normal and optimized isolated Python.  Direct
API race hostiles run in the interpreter that launches the suite; the outer
gate launches this complete suite under both modes.  The suite also audits the
production source shape so a relaxed manifest call, an unreviewed font-renaming
dependency, or drift in any raw/dependency pin fails closed before fixture
tests begin.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import types
from dataclasses import dataclass
from typing import Any, NoReturn


CHECK_NAME = "Mathematical results guide hosted raw-profile v2 self-test"
ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
CHECKER = ROOT / "scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2.py"
OPERATIONAL_CHECKER = CHECKER
STRUCTURE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-structure-v2.py"
ID_VARIANCE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-id-variance.py"

EXPECTED_CHECKER_SHA256 = (
    "29837b202ad3e5afa59e10f0ef4848b876fb6ef2b6aa3a996f78d7aac2752fcc"
)
EXPECTED_HOSTED_FIXTURE_BYTES = 744_745
EXPECTED_HOSTED_FIXTURE_SHA256 = (
    "b879555d87f696be870483326e2e3158c1f95330d51291d80017c016830907b6"
)
EXPECTED_STRUCTURE_CHECK_SHA256 = (
    "a70d3c78da7040774c5976f2316480501713eed1e9c865822e3024724a0ccf8d"
)
EXPECTED_ID_VARIANCE_CHECK_SHA256 = (
    "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7"
)
EXPECTED_PYPDF_VERSION = "6.15.0"
ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
FINAL_STARTXREF_PATTERN = re.compile(
    rb"startxref[ \t\r\n]+([0-9]+)[ \t\r\n]+%%EOF[ \t\r\n]*\Z"
)
PYTHON_MODES = (
    ("normal", (sys.executable, "-I", "-B")),
    ("optimized", (sys.executable, "-O", "-I", "-B")),
)


class SelfTestError(Exception):
    """A control, hostile disposition, or static invariant failed."""


@dataclass
class Ledger:
    controls: int = 0
    raw_hostiles: int = 0
    identifier_hostiles: int = 0
    input_hostiles: int = 0
    output_hostiles: int = 0
    dependency_hostiles: int = 0
    source_hostiles: int = 0
    stability_hostiles: int = 0

    def total(self) -> int:
        return sum(dataclasses.astuple(self))


EXPECTED_LEDGER = Ledger(
    controls=2,
    raw_hostiles=13,
    identifier_hostiles=6,
    input_hostiles=10,
    output_hostiles=16,
    dependency_hostiles=6,
    source_hostiles=13,
    stability_hostiles=3,
)


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_regular(path: pathlib.Path, label: str, maximum: int) -> bytes:
    try:
        before = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail(f"cannot inspect {label}: {error}")
    require(
        resolved == path
        and stat.S_ISREG(before.st_mode)
        and not stat.S_ISLNK(before.st_mode)
        and before.st_nlink == 1,
        f"{label} is noncanonical, non-regular, symbolic, or multiply linked",
    )
    require(0 < before.st_size <= maximum, f"{label} is outside its byte bound")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    require(nofollow is not None, "platform lacks O_NOFOLLOW")
    require(nonblock is not None, "platform lacks O_NONBLOCK")
    descriptor = os.open(
        path,
        os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        opened = os.fstat(descriptor)
        data = os.pread(descriptor, maximum + 1, 0)
        after = os.fstat(descriptor)
        path_after = path.lstat()
    finally:
        os.close(descriptor)
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    require(
        all(getattr(opened, field) == getattr(after, field) for field in fields)
        and all(
            getattr(opened, field) == getattr(path_after, field) for field in fields
        )
        and len(data) == opened.st_size,
        f"{label} changed while it was read",
    )
    return data


def literal_assignments(tree: ast.AST) -> dict[str, list[Any]]:
    assignments: dict[str, list[Any]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
        assignments.setdefault(target.id, []).append(value)
    return assignments


def source_invariant_errors(source: bytes) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        text = source.decode("utf-8", errors="strict")
        tree = ast.parse(text, filename=str(CHECKER))
    except (UnicodeError, SyntaxError) as error:
        return (f"production checker does not parse exactly: {error}",)
    assignments = literal_assignments(tree)
    expected_assignments = {
        "EXPECTED_HOSTED_FIXTURE_BYTES": EXPECTED_HOSTED_FIXTURE_BYTES,
        "EXPECTED_HOSTED_FIXTURE_SHA256": EXPECTED_HOSTED_FIXTURE_SHA256,
        "EXPECTED_STRUCTURE_CHECK_SHA256": EXPECTED_STRUCTURE_CHECK_SHA256,
        "EXPECTED_ID_VARIANCE_CHECK_SHA256": EXPECTED_ID_VARIANCE_CHECK_SHA256,
        "EXPECTED_PYPDF_VERSION": EXPECTED_PYPDF_VERSION,
    }
    for name, expected in expected_assignments.items():
        if assignments.get(name) != [expected]:
            errors.append(f"{name} is not the sole exact reviewed literal")

    structure_calls: list[ast.Call] = []
    identifier_calls: list[ast.Call] = []
    rollback_calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "rollback_published_output"
        ):
            rollback_calls.append(node)
        if not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if (
            isinstance(owner, ast.Name)
            and owner.id == "STRUCTURE"
            and node.func.attr == "validate_bytes"
        ):
            structure_calls.append(node)
        if (
            isinstance(owner, ast.Name)
            and owner.id == "ID_VARIANCE"
            and node.func.attr == "erase_strict_id"
        ):
            identifier_calls.append(node)
    if len(structure_calls) != 2:
        errors.append("strict structure validation is not called exactly twice")
    for call in structure_calls:
        manifest_values = [
            keyword.value
            for keyword in call.keywords
            if keyword.arg == "enforce_manifest_digests"
        ]
        if not (
            len(manifest_values) == 1
            and isinstance(manifest_values[0], ast.Constant)
            and manifest_values[0].value is True
        ):
            errors.append(
                "a strict structure call does not explicitly enforce manifests"
            )
    if len(identifier_calls) != 2:
        errors.append("strict final-trailer ID extraction is not called exactly twice")
    if len(rollback_calls) != 2:
        errors.append("pair rollback is not called from both failure paths")

    required_fragments = (
        "if fixture_report != candidate_report:",
        'report_payload(candidate_report.targets, "targets")',
        'report_payload(candidate_report.navigation, "navigation")',
        "if candidate.data == fixture.data:",
        "if len(candidate.data) != len(fixture.data):",
        "if fixture_projected != candidate_projected:",
        'regular_read_flags("inputs")',
        'regular_read_flags("dependencies")',
        'regular_read_flags("published outputs")',
        'return os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)',
        "PROTECTED_DEPENDENCIES = (",
        'fail("output", f"existing {label} output is forbidden; output must be fresh")',
        "return StagedOutput(plan, temporary_basename, descriptor, staged, payload)",
        'pathlib.Path(argv[2]), "targets", inputs, PROTECTED_DEPENDENCIES',
        "os.link(",
        "recheck_pypdf_runtime(PYPDF_MODULE, PYPDF_DEPENDENCY)",
        "recheck_output_parent(plans[0])",
        "recheck_output_parent(plans[1])",
        "(targets_payload, navigation_payload),",
    )
    for fragment in required_fragments:
        if text.count(fragment) != 1:
            errors.append(
                f"required closed-profile source fragment changed: {fragment}"
            )
    forbidden_fragments = (
        "enforce_manifest_digests=False",
        "font-alpha-equivalence",
        "font_alpha_equivalence",
        "ALPHA.",
        "PdfReader(",
        "math.isclose",
        "rstrip(",
        "removesuffix(",
        "os.replace(",
        "O_TRUNC",
    )
    lowered = text.lower()
    for fragment in forbidden_fragments:
        if fragment.lower() in lowered:
            errors.append(f"forbidden relaxation or dependency is present: {fragment}")
    return tuple(errors)


def require_static_source(source: bytes) -> None:
    observed_sha256 = sha256_bytes(source)
    require(
        observed_sha256 == EXPECTED_CHECKER_SHA256,
        "production checker digest changed: "
        f"observed={observed_sha256} expected={EXPECTED_CHECKER_SHA256}",
    )
    errors = source_invariant_errors(source)
    require(not errors, "production source invariants failed: " + "; ".join(errors))


def require_source_mutation_rejected(source: bytes, label: str, ledger: Ledger) -> None:
    errors = source_invariant_errors(source)
    require(errors, f"source mutation passed its static audit: {label}")
    ledger.source_hostiles += 1


def replace_once(source: bytes, old: bytes, new: bytes, label: str) -> bytes:
    require(source.count(old) == 1, f"{label} mutation target count changed")
    return source.replace(old, new, 1)


def audit_source_mutations(source: bytes, ledger: Ledger) -> None:
    require_source_mutation_rejected(
        replace_once(
            source,
            b"fixture.data, enforce_manifest_digests=True",
            b"fixture.data, enforce_manifest_digests=False",
            "relaxed fixture validation",
        ),
        "relaxed fixture manifest validation",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b"candidate.data, enforce_manifest_digests=True",
            b"candidate.data, enforce_manifest_digests=False",
            "relaxed candidate validation",
        ),
        "relaxed candidate manifest validation",
        ledger,
    )
    require_source_mutation_rejected(
        source
        + b'\nimport importlib\nimportlib.import_module("check-mathematical-results-guide-pdf-font-alpha-equivalence")\n',
        "font-renaming comparator import",
        ledger,
    )
    require_source_mutation_rejected(
        source + b"\nALPHA.compare_font_alpha_core(b'', b'')\n",
        "font-renaming comparator call",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            f"{EXPECTED_HOSTED_FIXTURE_BYTES:_}".encode("ascii"),
            f"{EXPECTED_HOSTED_FIXTURE_BYTES + 1:_}".encode("ascii"),
            "fixture byte pin",
        ),
        "fixture byte pin drift",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            EXPECTED_HOSTED_FIXTURE_SHA256.encode("ascii"),
            ("0" * 64).encode("ascii"),
            "fixture digest pin",
        ),
        "fixture digest pin drift",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b"if fixture_report != candidate_report:",
            b"if fixture_report.navigation_sha256 != candidate_report.navigation_sha256:",
            "partial report comparison",
        ),
        "partial report comparison",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b"if fixture_projected != candidate_projected:",
            b"if False and fixture_projected != candidate_projected:",
            "raw comparison bypass",
        ),
        "raw projection bypass",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b'return os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)',
            b'return os.O_RDONLY | nofollow | 0 | getattr(os, "O_CLOEXEC", 0)',
            "nonblocking regular-file open",
        ),
        "nonblocking regular-file open bypass",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b'pathlib.Path(argv[2]), "targets", inputs, PROTECTED_DEPENDENCIES',
            b'pathlib.Path(argv[2]), "targets", inputs, ()',
            "protected output sources",
        ),
        "protected output source bypass",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b'fail("output", f"existing {label} output is forbidden; output must be fresh")',
            b"plan.destination_before = destination",
            "fresh-only output",
        ),
        "fresh-only output bypass",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b"os.link(",
            b"os.replace(",
            "no-clobber publication",
        ),
        "no-clobber publication bypass",
        ledger,
    )
    require_source_mutation_rejected(
        replace_once(
            source,
            b"        recheck_output_parent(plans[0])\n"
            b"        recheck_output_parent(plans[1])",
            b"        pass",
            "postpublication parent identity",
        ),
        "postpublication parent-identity bypass",
        ledger,
    )


def load_checker(checker: pathlib.Path, source: bytes) -> Any:
    """Execute the already captured checker bytes with a private canonical path."""

    module_name = "mathematical_results_guide_hosted_raw_profile_for_self_test"
    module = types.ModuleType(module_name)
    module.__file__ = str(checker)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(source, str(checker), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def replace_id(data: bytes, first_hex: bytes, second_hex: bytes) -> bytes:
    matches = list(ID_PATTERN.finditer(data))
    require(len(matches) == 1, "fixture does not have exactly one strict trailer ID")
    require(len(first_hex) == 32 and len(second_hex) == 32, "invalid replacement ID")
    match = matches[0]
    changed = bytearray(data)
    changed[match.start(1) : match.end(1)] = first_hex
    changed[match.start(2) : match.end(2)] = second_hex
    return bytes(changed)


def distinct_id(data: bytes) -> bytes:
    match = ID_PATTERN.search(data)
    require(
        match is not None and match.group(1).lower() == match.group(2).lower(),
        "fixture ID is not duplicated",
    )
    replacement = b"0123456789ABCDEF0123456789ABCDEF"
    if bytes.fromhex(replacement.decode("ascii")) == bytes.fromhex(
        match.group(1).decode("ascii")
    ):
        replacement = b"FEDCBA9876543210FEDCBA9876543210"
    return replace_id(data, replacement, replacement)


def run_one(
    prefix: tuple[str, ...],
    checker: pathlib.Path,
    fixture: pathlib.Path,
    candidate: pathlib.Path,
    targets: pathlib.Path,
    navigation: pathlib.Path,
) -> subprocess.CompletedProcess[str]:
    effective_checker = OPERATIONAL_CHECKER if checker == CHECKER else checker
    return subprocess.run(
        [
            *prefix,
            str(effective_checker),
            str(fixture),
            str(candidate),
            str(targets),
            str(navigation),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )


def fresh_path(root: pathlib.Path, label: str, mode: str, suffix: str) -> pathlib.Path:
    return root / f"{label}-{mode}-{suffix}"


def require_pass_modes(
    root: pathlib.Path,
    checker: pathlib.Path,
    fixture: pathlib.Path,
    candidate: pathlib.Path,
    label: str,
    expected_targets: bytes,
    expected_navigation: bytes,
    ledger: Ledger,
    *,
    preexisting: bool = False,
) -> None:
    outputs: list[tuple[bytes, bytes]] = []
    standard_outputs: list[str] = []
    for mode, prefix in PYTHON_MODES:
        targets = fresh_path(root, label, mode, "targets.txt")
        navigation = fresh_path(root, label, mode, "navigation.txt")
        if preexisting:
            targets.write_bytes(b"partial-old-targets")
            navigation.write_bytes(b"partial-old-navigation")
        result = run_one(prefix, checker, fixture, candidate, targets, navigation)
        require(
            result.returncode == 0
            and "complete strict canonical structure" in result.stdout
            and result.stderr == "",
            f"{label} {mode} control failed:\n{result.stdout}{result.stderr}",
        )
        observed = (targets.read_bytes(), navigation.read_bytes())
        require(
            observed == (expected_targets, expected_navigation),
            f"{label} {mode} emitted noncanonical or incomplete reports",
        )
        outputs.append(observed)
        standard_outputs.append(result.stdout)
    require(outputs[0] == outputs[1], f"{label} normal/-O output bytes differ")
    require(
        standard_outputs[0] == standard_outputs[1],
        f"{label} normal/-O diagnostics differ",
    )
    ledger.controls += 1


def require_failure_modes(
    root: pathlib.Path,
    checker: pathlib.Path,
    fixture: pathlib.Path,
    candidate: pathlib.Path,
    label: str,
    expected: str,
    ledger: Ledger,
    category: str,
    *,
    targets_factory: Any | None = None,
    navigation_factory: Any | None = None,
    sentinels: bool = False,
) -> None:
    diagnostics: list[str] = []
    for mode, prefix in PYTHON_MODES:
        targets = fresh_path(root, label, mode, "targets.txt")
        navigation = fresh_path(root, label, mode, "navigation.txt")
        if targets_factory is not None:
            targets = targets_factory(targets)
        if navigation_factory is not None:
            navigation = navigation_factory(navigation)
        if sentinels:
            targets.write_bytes(b"sentinel-targets\n")
            navigation.write_bytes(b"sentinel-navigation\n")

        def endpoint_state(path: pathlib.Path) -> tuple[str, Any]:
            try:
                observed = path.lstat()
            except FileNotFoundError:
                return ("absent", None)
            if stat.S_ISLNK(observed.st_mode):
                return ("symlink", os.readlink(path))
            if stat.S_ISREG(observed.st_mode):
                return (
                    "regular",
                    ((observed.st_dev, observed.st_ino), path.read_bytes()),
                )
            return ("special", stat.S_IFMT(observed.st_mode))

        states_before = (endpoint_state(targets), endpoint_state(navigation))
        result = run_one(prefix, checker, fixture, candidate, targets, navigation)
        combined = result.stdout + result.stderr
        require(result.returncode != 0, f"{label} {mode} hostile passed")
        require(expected in combined, f"{label} {mode} diagnostic changed:\n{combined}")
        states_after = (endpoint_state(targets), endpoint_state(navigation))
        require(
            states_after == states_before,
            f"{label} {mode} changed or partially emitted a report on failure: "
            f"before={states_before!r} after={states_after!r}",
        )
        diagnostics.append(combined)
        for path in (targets, navigation):
            if path in (fixture, candidate) or path.parent != root:
                continue
            try:
                if (
                    path.is_symlink()
                    or path.is_file()
                    or stat.S_ISFIFO(path.lstat().st_mode)
                ):
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            except FileNotFoundError:
                pass
    require(diagnostics[0] == diagnostics[1], f"{label} normal/-O diagnostics differ")
    setattr(ledger, category, getattr(ledger, category) + 1)


def hostile_bytes_case(
    root: pathlib.Path,
    fixture: pathlib.Path,
    data: bytes,
    label: str,
    expected: str,
    ledger: Ledger,
    category: str = "raw_hostiles",
    *,
    sentinels: bool = False,
) -> None:
    candidate = root / f"{label}-candidate.pdf"
    candidate.write_bytes(data)
    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        label,
        expected,
        ledger,
        category,
        sentinels=sentinels,
    )


def make_nonfinal_identifier(data: bytes, replacement: bytes) -> bytes:
    match = ID_PATTERN.search(data)
    final_startxref = FINAL_STARTXREF_PATTERN.search(data)
    require(
        match is not None and final_startxref is not None,
        "cannot locate final identifier owner",
    )
    strict_token = data[match.start() : match.end()]
    require(len(strict_token) < 180, "strict identifier token is unexpectedly large")
    insertion_start = data.find(b"\n", 8) + 1
    require(
        0 < insertion_start < match.start(),
        "cannot choose a nonfinal identifier window",
    )
    changed = bytearray(replace_id(data, replacement, replacement))
    changed[match.start() : match.end()] = b" " * len(strict_token)
    moved_token = bytes(changed[match.start() : match.end()])
    require(moved_token.strip() == b"", "final identifier neutralization failed")
    varied_token_match = ID_PATTERN.search(replace_id(data, replacement, replacement))
    require(varied_token_match is not None, "cannot build varied identifier token")
    varied_token = replace_id(data, replacement, replacement)[
        varied_token_match.start() : varied_token_match.end()
    ]
    changed[insertion_start : insertion_start + len(varied_token)] = varied_token
    return bytes(changed)


def mutation_window(data: bytes, forbidden: tuple[tuple[int, int], ...]) -> int:
    for index in range(16, min(len(data) - 16, 4096)):
        if any(start <= index < end for start, end in forbidden):
            continue
        if data[index] not in b"\x00\r\n":
            return index
    fail("cannot locate a raw mutation window")


def run_raw_and_identifier_hostiles(
    root: pathlib.Path, fixture: pathlib.Path, data: bytes, ledger: Ledger
) -> None:
    varied = distinct_id(data)
    match = ID_PATTERN.search(data)
    varied_match = ID_PATTERN.search(varied)
    final_startxref = FINAL_STARTXREF_PATTERN.search(data)
    require(
        match is not None and varied_match is not None, "strict identifier disappeared"
    )
    require(final_startxref is not None, "fixture lacks final startxref")

    hostile_bytes_case(
        root, fixture, data + b"x", "length-plus-one", "byte lengths differ", ledger
    )
    hostile_bytes_case(
        root, fixture, data + b"xy", "length-plus-two", "byte lengths differ", ledger
    )
    hostile_bytes_case(
        root, fixture, data[:-1], "length-minus-one", "byte lengths differ", ledger
    )
    hostile_bytes_case(
        root, fixture, data[:-2], "length-minus-two", "byte lengths differ", ledger
    )
    hostile_bytes_case(
        root,
        fixture,
        data + b"\n% trailing comment",
        "trailing-comment",
        "byte lengths differ",
        ledger,
    )
    hostile_bytes_case(
        root, fixture, b"x" + varied, "prepended-byte", "byte lengths differ", ledger
    )

    index = mutation_window(varied, (varied_match.span(1), varied_match.span(2)))
    midstream = bytearray(varied)
    midstream[index] ^= 1
    hostile_bytes_case(
        root,
        fixture,
        bytes(midstream),
        "midstream-byte",
        "differ outside the strict duplicated final-trailer /ID payloads",
        ledger,
    )

    header = bytearray(varied)
    header[1] = ord("Q") if header[1] != ord("Q") else ord("P")
    hostile_bytes_case(
        root,
        fixture,
        bytes(header),
        "identifier-plus-header",
        "candidate input is not a strict readable PDF",
        ledger,
    )

    xref_offset = int(final_startxref.group(1))
    xref_mutation = bytearray(varied)
    xref_index = data.find(b"/XRef", xref_offset, final_startxref.start())
    require(xref_index >= 0, "cannot locate XRef type")
    xref_mutation[xref_index + 2] = ord("Y")
    hostile_bytes_case(
        root,
        fixture,
        bytes(xref_mutation),
        "xref-byte",
        "candidate startxref object is not a typed XRef stream",
        ledger,
    )

    startxref_mutation = bytearray(varied)
    digit_start = final_startxref.start(1)
    startxref_mutation[digit_start] = (
        ord("1") if startxref_mutation[digit_start] != ord("1") else ord("2")
    )
    hostile_bytes_case(
        root,
        fixture,
        bytes(startxref_mutation),
        "startxref-byte",
        "candidate startxref does not select a direct xref-stream object",
        ledger,
    )

    equal_case = match.group(1).swapcase()
    if equal_case == match.group(1):
        equal_case = match.group(1).upper()
    equal_candidate = replace_id(data, equal_case, equal_case)
    require(equal_candidate != data, "cannot create equal decoded-ID lexical drift")
    hostile_bytes_case(
        root,
        fixture,
        equal_candidate,
        "equal-decoded-identifier",
        "decoded trailer /ID values are equal",
        ledger,
        "identifier_hostiles",
    )

    nonduplicated = replace_id(varied, varied_match.group(1), b"A" * 32)
    hostile_bytes_case(
        root,
        fixture,
        nonduplicated,
        "nonduplicated-identifier",
        "trailer /ID pair is not duplicated",
        ledger,
        "identifier_hostiles",
    )

    malformed = bytearray(varied)
    malformed[varied_match.start(1)] = ord("G")
    hostile_bytes_case(
        root,
        fixture,
        bytes(malformed),
        "malformed-identifier",
        "does not contain exactly one strict trailer /ID",
        ledger,
        "identifier_hostiles",
    )

    strict_token = varied[varied_match.start() : varied_match.end()]
    multiple = bytearray(varied)
    insertion_start = data.find(b"\n", 8) + 1
    require(
        insertion_start + len(strict_token) < xref_offset,
        "no multiple-ID insertion window",
    )
    multiple[insertion_start : insertion_start + len(strict_token)] = strict_token
    hostile_bytes_case(
        root,
        fixture,
        bytes(multiple),
        "multiple-identifiers",
        "does not contain exactly one strict trailer /ID",
        ledger,
        "identifier_hostiles",
    )

    replacement = varied_match.group(1)
    nonfinal = make_nonfinal_identifier(data, replacement)
    hostile_bytes_case(
        root,
        fixture,
        nonfinal,
        "nonfinal-identifier",
        "candidate final trailer does not contain exactly one /ID name",
        ledger,
        "identifier_hostiles",
    )

    wrong_owner = bytearray(varied)
    owner_separator = varied_match.start() + len(b"/ID")
    require(
        wrong_owner[owner_separator] in b" \t\r\n",
        "cannot mutate identifier owner separator",
    )
    wrong_owner[owner_separator] = ord("%")
    external_start = data.find(b"\n", 8) + 1
    wrong_owner[external_start : external_start + len(strict_token)] = strict_token
    hostile_bytes_case(
        root,
        fixture,
        bytes(wrong_owner),
        "wrong-owner-identifier",
        "strict /ID is not owned by the final trailer",
        ledger,
        "identifier_hostiles",
    )

    hostile_bytes_case(
        root,
        fixture,
        bytes(midstream),
        "failed-output-preservation",
        "differ outside the strict duplicated final-trailer /ID payloads",
        ledger,
    )


def run_fixture_and_input_hostiles(
    root: pathlib.Path, fixture: pathlib.Path, data: bytes, ledger: Ledger
) -> None:
    varied = distinct_id(data)
    candidate = root / "valid-varied-candidate.pdf"
    candidate.write_bytes(varied)

    changed_fixture = root / "changed-hosted-fixture.pdf"
    changed = bytearray(data)
    changed[1] ^= 1
    changed_fixture.write_bytes(bytes(changed))
    require_failure_modes(
        root,
        CHECKER,
        changed_fixture,
        candidate,
        "fixture-byte-mutation",
        "hosted fixture raw bytes changed",
        ledger,
        "raw_hostiles",
    )

    canonical_mutation = bytearray(varied)
    canonical_mutation[2] ^= 1
    hostile_bytes_case(
        root,
        fixture,
        bytes(canonical_mutation),
        "canonical-candidate-mutation",
        "candidate input is not a strict readable PDF",
        ledger,
    )

    same_path = fixture
    require_failure_modes(
        root,
        CHECKER,
        same_path,
        same_path,
        "same-input-path",
        "inputs alias one file",
        ledger,
        "input_hostiles",
    )

    fixture_symlink = root / "fixture-symlink.pdf"
    fixture_symlink.symlink_to(fixture)
    require_failure_modes(
        root,
        CHECKER,
        fixture_symlink,
        candidate,
        "fixture-symlink",
        "noncanonical, non-regular, or symbolic",
        ledger,
        "input_hostiles",
    )
    candidate_symlink = root / "candidate-symlink.pdf"
    candidate_symlink.symlink_to(candidate)
    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate_symlink,
        "candidate-symlink",
        "noncanonical, non-regular, or symbolic",
        ledger,
        "input_hostiles",
    )

    alias = root / "hardlink-alias.pdf"
    alias.hardlink_to(fixture)
    require_failure_modes(
        root,
        CHECKER,
        fixture,
        alias,
        "hardlink-input-alias",
        "not singly linked",
        ledger,
        "input_hostiles",
    )
    alias.unlink()

    candidate_alias = root / "candidate-extra-hardlink.pdf"
    candidate_alias.hardlink_to(candidate)
    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "candidate-multiply-linked",
        "candidate input is not singly linked",
        ledger,
        "input_hostiles",
    )
    candidate_alias.unlink()

    directory = root / "directory-input.pdf"
    directory.mkdir()
    require_failure_modes(
        root,
        CHECKER,
        directory,
        candidate,
        "directory-input",
        "noncanonical, non-regular, or symbolic",
        ledger,
        "input_hostiles",
    )
    fifo = root / "fifo-input.pdf"
    os.mkfifo(fifo)
    require_failure_modes(
        root,
        CHECKER,
        fifo,
        candidate,
        "fifo-input",
        "noncanonical, non-regular, or symbolic",
        ledger,
        "input_hostiles",
    )
    empty = root / "empty-input.pdf"
    empty.write_bytes(b"")
    require_failure_modes(
        root,
        CHECKER,
        empty,
        candidate,
        "empty-input",
        "input size is outside",
        ledger,
        "input_hostiles",
    )
    oversized = root / "oversized-input.pdf"
    with oversized.open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    require_failure_modes(
        root,
        CHECKER,
        oversized,
        candidate,
        "oversized-input",
        "input size is outside",
        ledger,
        "input_hostiles",
    )


def run_output_hostiles(
    root: pathlib.Path, fixture: pathlib.Path, data: bytes, ledger: Ledger
) -> None:
    candidate = root / "output-hostile-valid-candidate.pdf"
    candidate.write_bytes(distinct_id(data))

    def same_output(path: pathlib.Path) -> pathlib.Path:
        return root / f"same-output-{path.name.split('-')[1]}.txt"

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "same-output-path",
        "outputs must be distinct",
        ledger,
        "output_hostiles",
        targets_factory=same_output,
        navigation_factory=same_output,
    )

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "output-aliases-fixture",
        "output aliases hosted fixture input",
        ledger,
        "output_hostiles",
        targets_factory=lambda _: fixture,
    )
    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "output-aliases-candidate",
        "output aliases candidate input",
        ledger,
        "output_hostiles",
        navigation_factory=lambda _: candidate,
    )

    symlink_target = root / "output-symlink-target.txt"
    symlink_target.write_bytes(b"target")

    def output_symlink(path: pathlib.Path) -> pathlib.Path:
        path.symlink_to(symlink_target)
        return path

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "output-symlink",
        "targets output path is symbolic or noncanonical",
        ledger,
        "output_hostiles",
        targets_factory=output_symlink,
    )

    def output_fifo(path: pathlib.Path) -> pathlib.Path:
        os.mkfifo(path)
        return path

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "output-fifo",
        "existing navigation output is forbidden; output must be fresh",
        ledger,
        "output_hostiles",
        navigation_factory=output_fifo,
    )

    def output_directory(path: pathlib.Path) -> pathlib.Path:
        path.mkdir()
        return path

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "output-directory",
        "existing targets output is forbidden; output must be fresh",
        ledger,
        "output_hostiles",
        targets_factory=output_directory,
    )

    def hardlinked_outputs(path: pathlib.Path) -> pathlib.Path:
        shared = root / f"shared-output-{path.name.split('-')[1]}.txt"
        if not shared.exists():
            shared.write_bytes(b"shared")
        path.hardlink_to(shared)
        return path

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "hardlinked-outputs",
        "existing targets output is forbidden; output must be fresh",
        ledger,
        "output_hostiles",
        targets_factory=hardlinked_outputs,
        navigation_factory=hardlinked_outputs,
    )

    def second_output_fifo(path: pathlib.Path) -> pathlib.Path:
        os.mkfifo(path)
        return path

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "no-partial-first-output",
        "existing navigation output is forbidden; output must be fresh",
        ledger,
        "output_hostiles",
        navigation_factory=second_output_fifo,
    )

    require_failure_modes(
        root,
        CHECKER,
        fixture,
        candidate,
        "preexisting-regular-outputs",
        "existing targets output is forbidden; output must be fresh",
        ledger,
        "output_hostiles",
        sentinels=True,
    )


def copy_checker_tree(
    root: pathlib.Path,
    checker_source: bytes,
    structure_source: bytes,
    identifier_source: bytes,
) -> pathlib.Path:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    checker = scripts / CHECKER.name
    checker.write_bytes(checker_source)
    (scripts / STRUCTURE_CHECK.name).write_bytes(structure_source)
    (scripts / ID_VARIANCE_CHECK.name).write_bytes(identifier_source)
    return checker


def run_dependency_hostiles(
    root: pathlib.Path,
    fixture: pathlib.Path,
    data: bytes,
    checker_source: bytes,
    structure_source: bytes,
    identifier_source: bytes,
    ledger: Ledger,
) -> None:
    candidate = root / "dependency-valid-candidate.pdf"
    candidate.write_bytes(distinct_id(data))

    structure_root = root / "mutated-structure-repo"
    mutated_structure = bytearray(structure_source)
    mutated_structure[-1] ^= 1
    structure_checker = copy_checker_tree(
        structure_root,
        checker_source,
        bytes(mutated_structure),
        identifier_source,
    )
    require_failure_modes(
        root,
        structure_checker,
        fixture,
        candidate,
        "structure-dependency-mutation",
        "strict structure checker digest changed",
        ledger,
        "dependency_hostiles",
    )

    identifier_root = root / "mutated-identifier-repo"
    mutated_identifier = bytearray(identifier_source)
    mutated_identifier[-1] ^= 1
    identifier_checker = copy_checker_tree(
        identifier_root,
        checker_source,
        structure_source,
        bytes(mutated_identifier),
    )
    require_failure_modes(
        root,
        identifier_checker,
        fixture,
        candidate,
        "identifier-dependency-mutation",
        "strict trailer-ID variance checker digest changed",
        ledger,
        "dependency_hostiles",
    )

    linked_root = root / "multiply-linked-dependency-repo"
    linked_checker = copy_checker_tree(
        linked_root,
        checker_source,
        structure_source,
        identifier_source,
    )
    extra_link = linked_root / "scripts/structure-extra-link.py"
    extra_link.hardlink_to(linked_root / f"scripts/{STRUCTURE_CHECK.name}")
    require_failure_modes(
        root,
        linked_checker,
        fixture,
        candidate,
        "multiply-linked-dependency",
        "strict structure checker is noncanonical, non-regular, symbolic, or multiply linked",
        ledger,
        "dependency_hostiles",
    )


def run_protected_output_hostiles(
    root: pathlib.Path,
    fixture: pathlib.Path,
    data: bytes,
    checker: pathlib.Path,
    hosted: Any,
    ledger: Ledger,
) -> None:
    candidate = root / "protected-output-valid-candidate.pdf"
    candidate.write_bytes(distinct_id(data))
    protected = (
        (checker, "checker-source", "hosted raw-profile checker source"),
        (
            checker.parent / STRUCTURE_CHECK.name,
            "structure-source",
            "strict structure checker",
        ),
        (
            checker.parent / ID_VARIANCE_CHECK.name,
            "identifier-source",
            "strict trailer-ID variance checker",
        ),
        (
            hosted.PYPDF_DEPENDENCY.path,
            "pypdf-source",
            "pypdf package initializer",
        ),
    )
    for path, label, expected in protected:
        require_failure_modes(
            root,
            CHECKER,
            fixture,
            candidate,
            f"output-aliases-{label}",
            f"targets output aliases {expected}",
            ledger,
            "output_hostiles",
            targets_factory=lambda _, selected=path: selected,
        )


def run_direct_fifo_hostiles(
    root: pathlib.Path, hosted: Any, data: bytes, ledger: Ledger
) -> None:
    original_open = hosted.os.open

    raced_input = root / "raced-fifo-input.pdf"
    raced_input.write_bytes(data)
    input_swapped = False

    def swap_input(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal input_swapped
        if pathlib.Path(path) == raced_input and not input_swapped:
            input_swapped = True
            raced_input.unlink()
            os.mkfifo(raced_input)
        return original_open(path, flags, *args, **kwargs)

    hosted.os.open = swap_input
    try:
        try:
            hosted.open_input(str(raced_input), "raced FIFO")
        except hosted.HostedRawProfileError as error:
            require(
                "identity or regular-file type changed" in str(error),
                "raced FIFO input diagnostic changed",
            )
        else:
            fail("regular-to-FIFO input race passed")
    finally:
        hosted.os.open = original_open
        raced_input.unlink(missing_ok=True)
    ledger.input_hostiles += 1

    raced_dependency = root / "raced-fifo-dependency.py"
    raced_dependency.write_bytes(b"x = 1\n")
    dependency_swapped = False

    def swap_dependency(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal dependency_swapped
        if pathlib.Path(path) == raced_dependency and not dependency_swapped:
            dependency_swapped = True
            raced_dependency.unlink()
            os.mkfifo(raced_dependency)
        return original_open(path, flags, *args, **kwargs)

    hosted.os.open = swap_dependency
    try:
        try:
            hosted.capture_dependency(raced_dependency, "raced FIFO dependency")
        except hosted.HostedRawProfileError as error:
            require(
                "cannot read raced FIFO dependency" in str(error)
                or "changed while it was read" in str(error),
                "raced FIFO dependency diagnostic changed",
            )
        else:
            fail("regular-to-FIFO dependency race passed")
    finally:
        hosted.os.open = original_open
        raced_dependency.unlink(missing_ok=True)
    ledger.dependency_hostiles += 1


def run_direct_publication_hostiles(
    root: pathlib.Path, hosted: Any, data: bytes, ledger: Ledger
) -> None:
    input_path = root / "publication-hostile-input.pdf"
    input_path.write_bytes(data)
    snapshot = hosted.open_input(str(input_path), "publication hostile")
    targets = root / "rollback-targets.txt"
    navigation = root / "rollback-navigation.txt"
    target_plan = hosted.prepare_output(
        targets,
        "targets",
        (snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    navigation_plan = hosted.prepare_output(
        navigation,
        "navigation",
        (snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    original_link = hosted.os.link
    link_calls = 0

    def fail_second_link(*args: Any, **kwargs: Any) -> None:
        nonlocal link_calls
        link_calls += 1
        if link_calls == 2:
            raise OSError("injected second publication failure")
        original_link(*args, **kwargs)

    hosted.os.link = fail_second_link
    try:
        try:
            hosted.publish_output_pair(
                (target_plan, navigation_plan),
                (b"targets\n", b"navigation\n"),
                (snapshot,),
                hosted.PROTECTED_DEPENDENCIES,
            )
        except hosted.HostedRawProfileError as error:
            require(
                "cannot publish navigation output" in str(error),
                "pair rollback diagnostic changed",
            )
        else:
            fail("injected second publication failure passed")
        require(
            not targets.exists()
            and not navigation.exists()
            and not tuple(root.glob(".*.hosted-profile.*")),
            "pair rollback left a destination or private stage",
        )
    finally:
        hosted.os.link = original_link
        os.close(target_plan.parent_descriptor)
        os.close(navigation_plan.parent_descriptor)
        os.close(snapshot.descriptor)
    ledger.output_hostiles += 1

    stage_input = root / "stage-hostile-input.pdf"
    stage_input.write_bytes(data)
    stage_snapshot = hosted.open_input(str(stage_input), "stage hostile")
    stage_plan = hosted.prepare_output(
        root / "stage-hostile-output.txt",
        "stage hostile",
        (stage_snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    staged = hosted.stage_output(stage_plan, b"stable-payload\n")
    try:
        os.pwrite(staged.descriptor, b"X", 0)
        try:
            hosted.recheck_stage(staged)
        except hosted.HostedRawProfileError as error:
            require("stage changed" in str(error), "stage mutation diagnostic changed")
        else:
            fail("descriptor-visible stage mutation passed")
    finally:
        cleanup_errors = hosted.cleanup_stage(staged)
        os.close(stage_plan.parent_descriptor)
        os.close(stage_snapshot.descriptor)
    require(not cleanup_errors, f"stage hostile cleanup failed: {cleanup_errors!r}")
    ledger.output_hostiles += 1

    parent_path = root / "postpublication-parent"
    detached_path = root / "postpublication-parent-detached"
    parent_path.mkdir()
    parent_input = root / "parent-swap-hostile-input.pdf"
    parent_input.write_bytes(data)
    parent_snapshot = hosted.open_input(str(parent_input), "parent swap hostile")
    parent_targets = parent_path / "targets.txt"
    parent_navigation = parent_path / "navigation.txt"
    parent_targets_plan = hosted.prepare_output(
        parent_targets,
        "targets",
        (parent_snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    parent_navigation_plan = hosted.prepare_output(
        parent_navigation,
        "navigation",
        (parent_snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    original_parent_recheck = hosted.recheck_output_parent
    parent_swapped = False

    def swap_parent_after_publication(plan: Any) -> None:
        nonlocal parent_swapped
        if (
            not parent_swapped
            and parent_targets.exists()
            and parent_navigation.exists()
        ):
            parent_path.rename(detached_path)
            parent_path.mkdir()
            parent_swapped = True
        original_parent_recheck(plan)

    hosted.recheck_output_parent = swap_parent_after_publication
    parent_error = ""
    try:
        try:
            hosted.publish_output_pair(
                (parent_targets_plan, parent_navigation_plan),
                (b"targets\n", b"navigation\n"),
                (parent_snapshot,),
                hosted.PROTECTED_DEPENDENCIES,
            )
        except hosted.HostedRawProfileError as error:
            parent_error = str(error)
        else:
            fail("postpublication output-parent replacement passed")
    finally:
        hosted.recheck_output_parent = original_parent_recheck
        os.close(parent_targets_plan.parent_descriptor)
        os.close(parent_navigation_plan.parent_descriptor)
        os.close(parent_snapshot.descriptor)
    detached_clean = (
        parent_swapped
        and detached_path.is_dir()
        and not (detached_path / "targets.txt").exists()
        and not (detached_path / "navigation.txt").exists()
        and not tuple(detached_path.glob(".*.hosted-profile.*"))
        and parent_path.is_dir()
        and not tuple(parent_path.iterdir())
    )
    if detached_path.is_dir():
        parent_path.rmdir()
        detached_path.rename(parent_path)
    require(
        "output parent identity changed" in parent_error,
        "postpublication parent-swap diagnostic changed",
    )
    require(detached_clean, "postpublication parent-swap rollback was not clean")
    parent_path.rmdir()
    ledger.output_hostiles += 1


def run_direct_pypdf_hostiles(hosted: Any, ledger: Ledger) -> None:
    module = hosted.PYPDF_MODULE
    original_version = module.__version__
    module.__version__ = "0.0-hostile"
    try:
        try:
            hosted.recheck_pypdf_runtime(module, hosted.PYPDF_DEPENDENCY)
        except hosted.HostedRawProfileError as error:
            require(
                "runtime identity changed" in str(error),
                "pypdf version diagnostic changed",
            )
        else:
            fail("mutated pypdf runtime version passed")
    finally:
        module.__version__ = original_version
    ledger.dependency_hostiles += 1

    original_file = module.__file__
    module.__file__ = str(hosted.CHECKER_SOURCE)
    try:
        try:
            hosted.capture_pypdf_runtime()
        except hosted.HostedRawProfileError as error:
            require(
                "inside the repository" in str(error), "pypdf origin diagnostic changed"
            )
        else:
            fail("repository-local pypdf origin passed")
    finally:
        module.__file__ = original_file
    ledger.dependency_hostiles += 1


def run_direct_stability_hostiles(
    root: pathlib.Path, hosted: Any, data: bytes, ledger: Ledger
) -> None:
    unstable_input = root / "unstable-direct-input.pdf"
    unstable_input.write_bytes(data)
    snapshot = hosted.open_input(str(unstable_input), "unstable direct")
    try:
        input_replacement = root / "unstable-direct-input-replacement.pdf"
        input_replacement.write_bytes(data)
        os.replace(input_replacement, unstable_input)
        try:
            hosted.recheck_input(snapshot)
        except hosted.HostedRawProfileError as error:
            require("changed during" in str(error), "unstable input diagnostic changed")
        else:
            fail("unstable input endpoint passed")
    finally:
        os.close(snapshot.descriptor)
    ledger.stability_hostiles += 1

    unstable_dependency = root / "unstable-direct-dependency.py"
    unstable_dependency.write_bytes(b"x = 1\n")
    dependency_snapshot = hosted.capture_dependency(
        unstable_dependency, "unstable direct dependency"
    )
    dependency_replacement = root / "unstable-direct-dependency-replacement.py"
    dependency_replacement.write_bytes(b"x = 2\n")
    os.replace(dependency_replacement, unstable_dependency)
    try:
        hosted.recheck_dependency(dependency_snapshot)
    except hosted.HostedRawProfileError as error:
        require(
            "changed during" in str(error), "unstable dependency diagnostic changed"
        )
    else:
        fail("unstable dependency endpoint passed")
    ledger.stability_hostiles += 1

    output_input = root / "output-plan-input.pdf"
    output_input.write_bytes(data)
    input_snapshot = hosted.open_input(str(output_input), "output-plan input")
    plan = hosted.prepare_output(
        root / "unstable-planned-output.txt",
        "unstable planned",
        (input_snapshot,),
        hosted.PROTECTED_DEPENDENCIES,
    )
    try:
        plan.path.write_bytes(b"arrived after preflight")
        try:
            hosted.recheck_output_plan(plan)
        except hosted.HostedRawProfileError as error:
            require(
                "changed before publication" in str(error),
                "unstable output diagnostic changed",
            )
        else:
            fail("unstable output destination passed")
    finally:
        os.close(plan.parent_descriptor)
        os.close(input_snapshot.descriptor)
    ledger.stability_hostiles += 1


def main(argv: list[str]) -> int:
    global OPERATIONAL_CHECKER
    if len(argv) != 1:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} HOSTED_FIXTURE.pdf",
            file=sys.stderr,
        )
        return 2
    fixture_path = pathlib.Path(argv[0])
    if not fixture_path.is_absolute():
        print(f"{CHECK_NAME} failed: fixture path must be absolute", file=sys.stderr)
        return 1
    ledger = Ledger()
    try:
        checker_source = read_regular(CHECKER, "production checker", 2 * 1024 * 1024)
        structure_source = read_regular(
            STRUCTURE_CHECK, "strict structure checker", 2 * 1024 * 1024
        )
        identifier_source = read_regular(
            ID_VARIANCE_CHECK, "strict trailer-ID checker", 2 * 1024 * 1024
        )
        require_static_source(checker_source)
        require(
            sha256_bytes(structure_source) == EXPECTED_STRUCTURE_CHECK_SHA256,
            "strict structure dependency digest changed",
        )
        require(
            sha256_bytes(identifier_source) == EXPECTED_ID_VARIANCE_CHECK_SHA256,
            "strict trailer-ID dependency digest changed",
        )
        audit_source_mutations(checker_source, ledger)

        fixture_data = read_regular(fixture_path, "hosted fixture", 16 * 1024 * 1024)
        require(
            len(fixture_data) == EXPECTED_HOSTED_FIXTURE_BYTES
            and sha256_bytes(fixture_data) == EXPECTED_HOSTED_FIXTURE_SHA256,
            "hosted fixture bytes are not the exact reviewed profile: "
            f"bytes={len(fixture_data)} sha256={sha256_bytes(fixture_data)}",
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-guide-hosted-raw-profile-self-test."
        ) as raw_root:
            root = pathlib.Path(raw_root).resolve(strict=True)
            private_checker_root = root / "captured-checker-repo"
            private_checker = copy_checker_tree(
                private_checker_root,
                checker_source,
                structure_source,
                identifier_source,
            )
            OPERATIONAL_CHECKER = private_checker
            hosted = load_checker(private_checker, checker_source)
            fixture_report = hosted.STRUCTURE.validate_bytes(
                fixture_data, enforce_manifest_digests=True
            )
            expected_targets = "".join(
                f"{line}\n" for line in fixture_report.targets
            ).encode("utf-8")
            expected_navigation = "".join(
                f"{line}\n" for line in fixture_report.navigation
            ).encode("utf-8")
            fixture = root / "exact-hosted-fixture.pdf"
            fixture.write_bytes(fixture_data)
            exact_candidate = root / "exact-candidate.pdf"
            exact_candidate.write_bytes(fixture_data)
            require_pass_modes(
                root,
                CHECKER,
                fixture,
                exact_candidate,
                "exact-fixture-control",
                expected_targets,
                expected_navigation,
                ledger,
            )
            varied_candidate = root / "identifier-varied-candidate.pdf"
            varied_candidate.write_bytes(distinct_id(fixture_data))
            require_pass_modes(
                root,
                CHECKER,
                fixture,
                varied_candidate,
                "strict-identifier-control",
                expected_targets,
                expected_navigation,
                ledger,
            )
            run_raw_and_identifier_hostiles(root, fixture, fixture_data, ledger)
            run_fixture_and_input_hostiles(root, fixture, fixture_data, ledger)
            run_output_hostiles(root, fixture, fixture_data, ledger)
            run_dependency_hostiles(
                root,
                fixture,
                fixture_data,
                checker_source,
                structure_source,
                identifier_source,
                ledger,
            )
            run_protected_output_hostiles(
                root, fixture, fixture_data, private_checker, hosted, ledger
            )
            run_direct_fifo_hostiles(root, hosted, fixture_data, ledger)
            run_direct_publication_hostiles(root, hosted, fixture_data, ledger)
            run_direct_pypdf_hostiles(hosted, ledger)
            run_direct_stability_hostiles(root, hosted, fixture_data, ledger)
            require(
                read_regular(private_checker, "private checker", 2 * 1024 * 1024)
                == checker_source,
                "private checker bytes changed during operational tests",
            )
            require(
                read_regular(
                    private_checker_root / f"scripts/{STRUCTURE_CHECK.name}",
                    "private structure dependency",
                    2 * 1024 * 1024,
                )
                == structure_source,
                "private structure dependency changed during operational tests",
            )
            require(
                read_regular(
                    private_checker_root / f"scripts/{ID_VARIANCE_CHECK.name}",
                    "private identifier dependency",
                    2 * 1024 * 1024,
                )
                == identifier_source,
                "private identifier dependency changed during operational tests",
            )
        require(
            read_regular(CHECKER, "production checker recheck", 2 * 1024 * 1024)
            == checker_source,
            "production checker changed during the self-test",
        )
        require(
            ledger == EXPECTED_LEDGER,
            f"exact hostile ledger changed: observed={ledger!r} "
            f"expected={EXPECTED_LEDGER!r}",
        )
    except (OSError, subprocess.SubprocessError, SelfTestError) as error:
        print(f"{CHECK_NAME} failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(
            f"{CHECK_NAME} failed [internal]: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 1

    print(
        f"{CHECK_NAME} passed: controls={ledger.controls} "
        f"raw_hostiles={ledger.raw_hostiles} "
        f"identifier_hostiles={ledger.identifier_hostiles} "
        f"input_hostiles={ledger.input_hostiles} "
        f"output_hostiles={ledger.output_hostiles} "
        f"dependency_hostiles={ledger.dependency_hostiles} "
        f"source_hostiles={ledger.source_hostiles} "
        f"stability_hostiles={ledger.stability_hostiles} total={ledger.total()}; "
        "normal/-O operational parity established."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
