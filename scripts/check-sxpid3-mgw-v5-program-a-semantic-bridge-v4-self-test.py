#!/usr/bin/env python3
"""Hostile tests for the MGW-v5 SxPID3 Program-A semantic bridge.

The suite uses isolated temporary repository shapes.  It checks both normal and
optimized Python, including the seven false-green classes preserved from the
historical v1/v2 correspondence checkers.  One deliberately accepted coherent
prose/record/checker reseal demonstrates the stated human-review boundary; it
receives no source-correspondence or independent-review credit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Final


if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py "
        "requires CPython 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CHECKER_REL: Final[Path] = Path(
    "scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py"
)
DOCUMENT_REL: Final[Path] = Path(
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/source-correspondence-v4.md"
)
RECORD_REL: Final[Path] = Path(
    "audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json"
)
CONVENTIONS_REL: Final[Path] = Path(
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
)
PRIMARY_ROUTE_REL: Final[Path] = Path(
    "scripts/check-sxpid3-bounded-full-coordinates.py"
)
INDEPENDENT_ROUTE_REL: Final[Path] = Path("scripts/check-sxpid3-all108-independent.py")
EXPECTED_CHECKER_SHA256: Final[str] = (
    "394361524372710179aea41f95f4ddf9559700082a80e02ac0d0a34fbe08ce4a"
)
EXPECTED_CHECKER_BYTES: Final[int] = 41_953
EXPECTED_PASS_STDOUT: Final[bytes] = (
    b"SxPID3 MGW-v5 Program-A semantic bridge v4: PASS "
    b"(18 nodes, 129 order pairs, 324 zeta entries, 65 nonzero Mobius entries, "
    b"6 source permutations; 3 frozen-registry compatibility files; "
    b"Program A partial/open; Programs closed 0/5)\n"
)
EXPECTED_HISTORICAL_FALSE_GREEN_IDS: Final[tuple[str, ...]] = (
    "V1-FG-INPUT-ROUTE",
    "V1-FG-SCOPE-CUTS",
    "V1-FG-ANCHOR-SEMANTICS",
    "V1-FG-CLAIM-SEMANTICS",
    "V1-FG-ROLE-TITLE",
    "V2-FG-INPUT-ROUTE-VIA-SOURCE-RECORD",
    "V2-FG-SCOPE-CUTS-VIA-SOURCE-RECORD",
)


class SelfTestError(RuntimeError):
    """A positive control failed or a hostile mutation survived unexpectedly."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_regular(path: Path) -> bytes:
    require(path.is_file(), f"missing source: {path.relative_to(ROOT)}")
    require(
        not path.is_symlink(), f"symbolic source rejected: {path.relative_to(ROOT)}"
    )
    return path.read_bytes()


def python_command(
    script: Path, *, optimized: bool, arguments: tuple[str, ...] = ()
) -> list[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", str(script), *arguments))
    return command


def run(
    script: Path, *, optimized: bool, arguments: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        python_command(script, optimized=optimized, arguments=arguments),
        cwd=script.parents[1],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def require_pass(result: subprocess.CompletedProcess[bytes], label: str) -> None:
    require(
        result.returncode == 0,
        f"{label} returned {result.returncode}: {result.stderr!r}",
    )
    require(
        result.stdout == EXPECTED_PASS_STDOUT,
        f"{label} stdout changed: {result.stdout!r}",
    )
    require(result.stderr == b"", f"{label} wrote stderr: {result.stderr!r}")


def require_reject(
    result: subprocess.CompletedProcess[bytes], expected: bytes, label: str
) -> None:
    require(result.returncode == 1, f"{label} returned {result.returncode}, not 1")
    require(result.stdout == b"", f"{label} wrote stdout: {result.stdout!r}")
    require(
        expected in result.stderr,
        f"{label} rejected for the wrong reason: {result.stderr!r}",
    )


def copy_fixture(destination: Path) -> None:
    for relative in (
        CHECKER_REL,
        DOCUMENT_REL,
        RECORD_REL,
        CONVENTIONS_REL,
        PRIMARY_ROUTE_REL,
        INDEPENDENT_ROUTE_REL,
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def replace_once(path: Path, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    require(raw.count(old) == 1, f"mutation preimage count is not one for {old!r}")
    path.write_bytes(raw.replace(old, new, 1))


def load_record(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "test record root is not an object")
    return value


def write_record(path: Path, value: dict[str, object]) -> None:
    path.write_bytes(
        json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )


def reseal_record(checker: Path, record: Path) -> None:
    raw = record.read_bytes()
    checker_raw = checker.read_bytes()
    old_hash = b"dbc43a78e88d5e35cce5e01ec69f676eef8c68bda2f5eae5994f61d21fe5db24"
    new_hash = sha256_bytes(raw).encode("ascii")
    require(checker_raw.count(old_hash) == 1, "record digest literal is not unique")
    checker_raw = checker_raw.replace(old_hash, new_hash, 1)
    old_size = b"EXPECTED_RECORD_BYTES: Final[int] = 17_458"
    new_size = f"EXPECTED_RECORD_BYTES: Final[int] = {len(raw)}".encode("ascii")
    require(checker_raw.count(old_size) == 1, "record-size literal is not unique")
    checker.write_bytes(checker_raw.replace(old_size, new_size, 1))


def reseal_document(checker: Path, document: Path) -> None:
    raw = document.read_bytes()
    checker_raw = checker.read_bytes()
    old_hash = b"b4e6fbcdc289e7a8e6c3af42509b568606e61b8908b59661b895bd9ca5eb72cb"
    new_hash = sha256_bytes(raw).encode("ascii")
    require(checker_raw.count(old_hash) == 1, "document digest literal is not unique")
    checker_raw = checker_raw.replace(old_hash, new_hash, 1)
    old_size = b"EXPECTED_DOCUMENT_BYTES: Final[int] = 33_942"
    new_size = f"EXPECTED_DOCUMENT_BYTES: Final[int] = {len(raw)}".encode("ascii")
    require(checker_raw.count(old_size) == 1, "document-size literal is not unique")
    checker.write_bytes(checker_raw.replace(old_size, new_size, 1))


RecordMutation = Callable[[dict[str, object]], None]


def record_mutation(
    name: str,
    mutate: RecordMutation,
    expected: bytes,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"pid-rs-sxpid3-a-{name}-") as temporary:
        fixture = Path(temporary) / "repo"
        copy_fixture(fixture)
        record_path = fixture / RECORD_REL
        record = load_record(record_path)
        mutate(record)
        write_record(record_path, record)
        reseal_record(fixture / CHECKER_REL, record_path)
        for optimized in (False, True):
            result = run(fixture / CHECKER_REL, optimized=optimized)
            require_reject(result, expected, f"{name}/optimize={int(optimized)}")


def source_mutation(name: str, old: bytes, new: bytes, expected: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix=f"pid-rs-sxpid3-a-{name}-") as temporary:
        fixture = Path(temporary) / "repo"
        copy_fixture(fixture)
        checker = fixture / CHECKER_REL
        replace_once(checker, old, new)
        for optimized in (False, True):
            result = run(checker, optimized=optimized)
            require_reject(result, expected, f"{name}/optimize={int(optimized)}")


def main() -> int:
    require(len(sys.argv) == 1, "self-test accepts no arguments")
    checker_raw = require_regular(ROOT / CHECKER_REL)
    require(
        len(checker_raw) == EXPECTED_CHECKER_BYTES,
        "production checker byte length changed",
    )
    require(
        sha256_bytes(checker_raw) == EXPECTED_CHECKER_SHA256,
        "production checker digest changed",
    )
    require_regular(ROOT / DOCUMENT_REL)
    record = load_record(ROOT / RECORD_REL)
    validation = record.get("validation")
    require(isinstance(validation, dict), "record validation contract is absent")
    historical_coverage = validation.get("historical_false_green_coverage")
    require(
        isinstance(historical_coverage, list),
        "historical false-green coverage is absent",
    )
    observed_historical_ids = tuple(
        entry.get("id") if isinstance(entry, dict) else None
        for entry in historical_coverage
    )
    require(
        observed_historical_ids == EXPECTED_HISTORICAL_FALSE_GREEN_IDS,
        "historical false-green identifier registry changed",
    )
    for required in (
        b"multiply(mobius, zeta) == matrix_identity",
        b"multiply(zeta, mobius) == matrix_identity",
        b"canonical checker accepts no alternate input paths or arguments",
        b"paper_semantics_are_human_read_not_machine_interpreted",
        b"derived Mobius inverse differs from conventions",
        b'programs_closed": 0',
    ):
        require(
            required in checker_raw,
            f"production checker lost structural token: {required!r}",
        )

    for optimized in (False, True):
        require_pass(
            run(ROOT / CHECKER_REL, optimized=optimized),
            f"baseline/optimize={int(optimized)}",
        )

    historical_controls_executed: list[str] = []

    # Historical v1/v2 false-green input routes: the canonical checker has no override option.
    for option, historical_id in (
        ("--record", "V1-FG-INPUT-ROUTE"),
        ("--source-record", "V2-FG-INPUT-ROUTE-VIA-SOURCE-RECORD"),
    ):
        for optimized in (False, True):
            result = run(
                ROOT / CHECKER_REL,
                optimized=optimized,
                arguments=(option, "/tmp/untrusted-alternate.json"),
            )
            require_reject(
                result,
                b"canonical checker accepts no alternate input paths or arguments",
                f"alternate-input-{option}/optimize={int(optimized)}",
            )
        historical_controls_executed.append(historical_id)

    def drop_boundary(record: dict[str, object]) -> None:
        boundaries = record["boundaries"]
        require(isinstance(boundaries, list), "boundaries test precondition")
        boundaries.pop()

    def change_anchor(record: dict[str, object]) -> None:
        anchors = record["anchors"]
        require(
            isinstance(anchors, list) and isinstance(anchors[1], dict),
            "anchor test precondition",
        )
        anchors[1]["local_role"] = "OR within and AND across"

    def close_claim(record: dict[str, object]) -> None:
        status = record["status"]
        require(isinstance(status, dict), "status test precondition")
        status["complete_target"] = "verified"

    def change_title(record: dict[str, object]) -> None:
        source = record["primary_source"]
        require(isinstance(source, dict), "source test precondition")
        source["title"] = "A different paper"

    def close_program(record: dict[str, object]) -> None:
        status = record["status"]
        require(isinstance(status, dict), "program status test precondition")
        status["programs_closed"] = 1

    def change_units(record: dict[str, object]) -> None:
        scope = record["scope"]
        require(isinstance(scope, dict), "scope test precondition")
        scope["units"] = "bits and nats treated as identical"

    def claim_independent_review(record: dict[str, object]) -> None:
        status = record["status"]
        require(isinstance(status, dict), "review status test precondition")
        status["h1_independent_human_custody"] = "closed"

    def add_same_reviewer(record: dict[str, object]) -> None:
        record["reviewers"] = [{"pre": "same-person", "post": "same-person"}]

    def add_unexecuted_control(record: dict[str, object]) -> None:
        record["positive_control"] = {"executed": False, "status": "passed"}

    def change_derived_count(record: dict[str, object]) -> None:
        derivation = record["derivation"]
        require(isinstance(derivation, dict), "derivation test precondition")
        counts = derivation["counts"]
        require(isinstance(counts, dict), "counts test precondition")
        counts["order_pairs"] = 128

    def drop_historical_control(record: dict[str, object]) -> None:
        validation = record["validation"]
        require(isinstance(validation, dict), "validation test precondition")
        coverage = validation["historical_false_green_coverage"]
        require(isinstance(coverage, list), "historical coverage test precondition")
        coverage.pop()

    record_mutation("v1-fg-scope-cuts", drop_boundary, b"evidence boundaries changed")
    historical_controls_executed.append("V1-FG-SCOPE-CUTS")
    record_mutation(
        "v1-fg-anchor-semantics", change_anchor, b"source-anchor map changed"
    )
    historical_controls_executed.append("V1-FG-ANCHOR-SEMANTICS")
    record_mutation(
        "v1-fg-claim-semantics", close_claim, b"claim/program status changed"
    )
    historical_controls_executed.append("V1-FG-CLAIM-SEMANTICS")
    record_mutation(
        "v1-fg-role-title", change_title, b"primary-source identity changed"
    )
    historical_controls_executed.append("V1-FG-ROLE-TITLE")
    record_mutation("v2-fg-scope-cuts", drop_boundary, b"evidence boundaries changed")
    historical_controls_executed.append("V2-FG-SCOPE-CUTS-VIA-SOURCE-RECORD")
    record_mutation(
        "program-count-escalation", close_program, b"claim/program status changed"
    )
    record_mutation("unit-conflation", change_units, b"scope changed")
    record_mutation(
        "independent-review-escalation",
        claim_independent_review,
        b"claim/program status changed",
    )
    record_mutation("same-reviewer-field", add_same_reviewer, b"record keys changed")
    record_mutation(
        "unexecuted-positive-control", add_unexecuted_control, b"record keys changed"
    )
    record_mutation(
        "derived-count-reseal",
        change_derived_count,
        b"recorded exact derivation changed",
    )
    record_mutation(
        "historical-control-deletion",
        drop_historical_control,
        b"validation contract changed",
    )
    require(
        len(historical_controls_executed) == len(EXPECTED_HISTORICAL_FALSE_GREEN_IDS)
        and set(historical_controls_executed)
        == set(EXPECTED_HISTORICAL_FALSE_GREEN_IDS),
        "not every historical false-green class reached its current control",
    )

    source_mutation(
        "within-mask-or",
        b"return all(selected)",
        b"return any(selected)",
        b"semantic mutant has no distinguishing witness",
    )
    source_mutation(
        "across-branch-and",
        b"return any(mask_matches(mask, match) for mask in antichain)",
        b"return all(mask_matches(mask, match) for mask in antichain)",
        b"semantic mutant has no distinguishing witness",
    )
    source_mutation(
        "omit-target-intersection",
        b"intersection = event and target_match",
        b"intersection = event or target_match",
        b"target intersection exceeds",
    )
    source_mutation(
        "transpose-zeta",
        b"antichain_le(column, row)",
        b"antichain_le(row, column)",
        b"derived digest registry changed",
    )
    source_mutation(
        "drop-mask-seven",
        b"masks = tuple(range(1, 1 << len(SOURCE_BITS)))",
        b"masks = tuple(range(1, (1 << len(SOURCE_BITS)) - 1))",
        b"generated Fin-3 antichain carrier changed",
    )
    source_mutation(
        "wrong-source-permutation",
        b"result[new_index] = match[old_index]",
        b"result[old_index] = match[new_index]",
        b"source permutation did not preserve event truth",
    )

    # The semantic reconstruction is separately tied to the three frozen registry files. A byte
    # change in any one is rejected before its content can be treated as compatible evidence.
    for relative in (CONVENTIONS_REL, PRIMARY_ROUTE_REL, INDEPENDENT_ROUTE_REL):
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-sxpid3-a-compatibility-drift-"
        ) as temporary:
            fixture = Path(temporary) / "repo"
            copy_fixture(fixture)
            bound_file = fixture / relative
            bound_file.write_bytes(bound_file.read_bytes() + b"\n")
            expected = f"compatibility byte length changed: {relative}".encode("utf-8")
            for optimized in (False, True):
                require_reject(
                    run(fixture / CHECKER_REL, optimized=optimized),
                    expected,
                    f"compatibility-drift-{relative.name}/optimize={int(optimized)}",
                )

    # Plain document drift is rejected by its exact-byte binding.
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-a-document-drift-"
    ) as temporary:
        fixture = Path(temporary) / "repo"
        copy_fixture(fixture)
        document = fixture / DOCUMENT_REL
        replace_once(
            document,
            b"AND within a mask, OR across antichain branches",
            b"OR within a mask, OR across antichain branches",
        )
        for optimized in (False, True):
            require_reject(
                run(fixture / CHECKER_REL, optimized=optimized),
                b"source-correspondence document byte length changed",
                f"document-drift/optimize={int(optimized)}",
            )

    # Accepted limitation: a coordinated owner can rewrite prose and reseal all owner-controlled
    # bindings.  This diagnostic must continue to pass, because the checker does not pretend to
    # interpret natural language.  Git/external review is the remaining control.
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-a-coherent-reseal-"
    ) as temporary:
        fixture = Path(temporary) / "repo"
        copy_fixture(fixture)
        checker = fixture / CHECKER_REL
        document = fixture / DOCUMENT_REL
        record_path = fixture / RECORD_REL
        replace_once(
            document,
            b"AND within a mask, OR across antichain branches",
            b"OR within a mask, OR across antichain branches",
        )
        record = load_record(record_path)
        document_binding = record["document"]
        require(
            isinstance(document_binding, dict), "document binding test precondition"
        )
        document_raw = document.read_bytes()
        document_binding["bytes"] = len(document_raw)
        document_binding["sha256"] = sha256_bytes(document_raw)
        write_record(record_path, record)
        reseal_document(checker, document)
        reseal_record(checker, record_path)
        for optimized in (False, True):
            require_pass(
                run(checker, optimized=optimized),
                f"accepted-coordinated-reseal-boundary/optimize={int(optimized)}",
            )

    print(
        "SxPID3 MGW-v5 Program-A semantic bridge v4 self-test: PASS "
        "(2 baseline executions; 4 alternate-input rejections; "
        "24 record-reseal rejections; 12 semantic-source rejections; "
        "6 compatibility-drift rejections; 2 document-drift rejections; "
        "2 accepted coordinated-reseal boundary diagnostics)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SelfTestError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(
            f"ERROR: SxPID3 MGW-v5 Program-A semantic bridge v4 self-test: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
