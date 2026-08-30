#!/usr/bin/env python3
"""Fail-closed tests for the results-guide PDF wrapper's mode wiring.

This suite does not mock or replay the complete renderer.  It binds exact source
anchors, extracts the two small shell dispatch blocks that select the structure
relation and its command arrays, and executes those blocks in isolation.  The
heavy PDF gate and the font-alpha checker retain responsibility for artifact
semantics; this file checks only that the wrapper cannot route exact artifact
comparison through the cross-toolchain exception.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
from dataclasses import dataclass
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
WRAPPER = ROOT / "scripts/check-mathematical-results-guide-pdf.sh"
GUIDE_BUILDER = ROOT / "scripts/build-mathematical-results-guide-pdf.sh"
SXPID3_WRAPPER = ROOT / "scripts/check-sxpid3-source-marginal-audit-pdf.sh"
SXPID3_BUILDER = ROOT / "scripts/build-sxpid3-source-marginal-audit-pdf.sh"
ALPHA_BASENAME = "check-mathematical-results-guide-pdf-font-alpha-equivalence.py"
ID_VARIANCE_BASENAME = "check-mathematical-results-guide-pdf-id-variance.py"
RETAINED_BASENAME = (
    "mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf"
)


class WiringError(Exception):
    """A deterministic mode-wiring policy failure."""


@dataclass(frozen=True)
class WiringFragments:
    """The three executable wrapper fragments covered by this suite."""

    relation_dispatch: str
    command_dispatch: str
    artifact_dispatch: str


def fail(message: str) -> NoReturn:
    raise SystemExit(
        "Mathematical results guide PDF mode-wiring self-test failed: " + message
    )


def read_direct(path: pathlib.Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise WiringError(f"{label} is absent, non-regular, or symbolic: {path}")
    return path.read_text(encoding="utf-8")


def require_count(source: str, token: str, count: int, label: str) -> None:
    observed = source.count(token)
    if observed != count:
        raise WiringError(f"{label} count is {observed}, expected {count}")


def extract_unique(source: str, start: str, end: str, label: str) -> str:
    require_count(source, start, 1, f"{label} start anchor")
    start_index = source.index(start)
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        raise WiringError(f"{label} end anchor is absent after its start")
    if source.find(end, end_index + len(end)) >= 0:
        raise WiringError(f"{label} end anchor is not unique")
    return source[start_index : end_index + len(end)]


def audit_auxiliary_sources(
    guide_builder: str, sxpid3_wrapper: str, sxpid3_builder: str
) -> None:
    for source, label in (
        (guide_builder, "guide builder"),
        (sxpid3_wrapper, "SxPID3 wrapper"),
        (sxpid3_builder, "SxPID3 builder"),
    ):
        if (
            ALPHA_BASENAME in source
            or "FONT_ALPHA_CHECK" in source
            or RETAINED_BASENAME in source
            or "RETAINED_FONT_ALPHA_FIXTURE" in source
        ):
            raise WiringError(
                f"{label} contains the cross-toolchain font-alpha comparator"
            )


def audit_wrapper(source: str) -> WiringFragments:
    require_count(source, 'MODE="${1:---exact}"', 1, "MODE assignment")
    require_count(
        source,
        'COMMITTED="$ROOT/output/pdf/mathematical-results-guide.pdf"',
        1,
        "COMMITTED assignment",
    )
    require_count(source, 'BUILT="$BUILD_ROOT/built.pdf"', 1, "BUILT assignment")
    require_count(source, "ID_VARIANCE_CHECK=", 1, "trailer-ID checker path assignment")
    require_count(
        source,
        "ID_VARIANCE_CHECK_SHA256="
        "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
        1,
        "trailer-ID checker digest assignment",
    )
    require_count(
        source, ID_VARIANCE_BASENAME, 1, "trailer-ID checker literal basename"
    )
    require_count(source, '"$ID_VARIANCE_CHECK"', 5, "all quoted trailer-ID path uses")
    require_count(
        source,
        '"$ID_VARIANCE_CHECK_SHA256"',
        4,
        "all quoted trailer-ID digest uses",
    )
    require_count(source, "$ID_VARIANCE_CHECK", 9, "all trailer-ID checker expansions")
    require_count(source, "FONT_ALPHA_CHECK=", 1, "font-alpha path assignment")
    require_count(
        source,
        "FONT_ALPHA_CHECK_SHA256="
        "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
        1,
        "font-alpha digest assignment",
    )
    require_count(source, ALPHA_BASENAME, 1, "font-alpha literal basename")
    require_count(source, '"$FONT_ALPHA_CHECK"', 7, "all quoted font-alpha path uses")
    require_count(
        source,
        '"$FONT_ALPHA_CHECK_SHA256"',
        4,
        "all quoted font-alpha digest uses",
    )
    require_count(source, "$FONT_ALPHA_CHECK", 11, "all font-alpha expansions")
    require_count(
        source,
        'RETAINED_FONT_ALPHA_FIXTURE="$ROOT/audit/evidence/' + RETAINED_BASENAME + '"',
        1,
        "retained fixture assignment",
    )
    require_count(source, RETAINED_BASENAME, 1, "retained fixture literal basename")
    require_count(
        source,
        '"$RETAINED_FONT_ALPHA_FIXTURE"',
        5,
        "all quoted retained-fixture uses",
    )
    require_count(
        source,
        "$RETAINED_FONT_ALPHA_FIXTURE",
        5,
        "all retained-fixture expansions",
    )
    required_once = (
        (
            'if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            "closed mode allow-list",
        ),
        (
            'TMP_BASE="$(CDPATH=\'\' cd -- "${TMPDIR:-/tmp}" && pwd -P)"',
            "physical temporary-root canonicalization",
        ),
        (
            'validate_pdf committed "$COMMITTED" strict',
            "strict committed-PDF validation",
        ),
        (
            'validate_pdf built "$BUILT" strict',
            "strict exact built-PDF validation",
        ),
        (
            'validate_pdf built "$BUILT" typed-font-alpha-from-committed',
            "cross-only built-PDF alpha validation",
        ),
        (
            'cmp -s "$BUILT" "$COMMITTED" || {',
            "raw exact artifact comparison",
        ),
        (
            'if ! cmp -s "$observed_urls" "$optimized_urls" \\\n'
            '      || ! cmp -s "$observed_navigation" "$optimized_navigation"; then',
            "normal/optimized projection parity",
        ),
        (
            'if ! cmp -s "$BUILD_ROOT/$label.structure.stdout" \\\n'
            '      "$BUILD_ROOT/$label.structure-optimized.stdout"; then',
            "normal/optimized diagnostic parity",
        ),
        (
            'if [[ -s "$structure_stderr" ]]; then',
            "zero-stderr policy",
        ),
    )
    for token, label in required_once:
        require_count(source, token, 1, label)

    if 'TMP_BASE="${TMPDIR:-/tmp}"' in source:
        raise WiringError("a lexical, nonphysical temporary-root assignment remains")

    relation_start = 'validate_pdf committed "$COMMITTED" strict\n'
    relation_end = '  validate_pdf built "$BUILT" typed-font-alpha-from-committed\nfi'
    relation_dispatch = extract_unique(
        source, relation_start, relation_end, "top-level structure-relation dispatch"
    )
    expected_relation_dispatch = (
        'validate_pdf committed "$COMMITTED" strict\n'
        'if [[ "$MODE" == "--exact" ]]; then\n'
        '  validate_pdf built "$BUILT" strict\n'
        "else\n"
        "  # Cross mode can admit only the retained, source-profiled page-font key relation.\n"
        "  # The pair checker raw-binds COMMITTED and the retained fixture before its typed proof.\n"
        '  validate_pdf built "$BUILT" typed-font-alpha-from-committed\n'
        "fi"
    )
    if relation_dispatch != expected_relation_dispatch:
        raise WiringError("top-level structure-relation dispatch changed")

    command_start = '  case "$structure_relation" in\n'
    command_end = '  esac\n  if ! "${structure_command[@]}"'
    command_with_next_anchor = extract_unique(
        source, command_start, command_end, "per-PDF structure-command dispatch"
    )
    command_dispatch = command_with_next_anchor[
        : -len('\n  if ! "${structure_command[@]}"')
    ]
    if command_dispatch.count('"$FONT_ALPHA_CHECK"') != 2:
        raise WiringError(
            "font-alpha comparator does not occur exactly once per Python mode"
        )
    if command_dispatch.count('"$STRUCTURE_CHECK"') != 2:
        raise WiringError(
            "strict structure checker does not occur exactly once per Python mode"
        )
    if command_dispatch.count('"$RETAINED_FONT_ALPHA_FIXTURE"') != 2:
        raise WiringError(
            "retained fixture does not occur exactly once per alpha Python mode"
        )
    normal_alpha_command = (
        'structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf" \\\n'
        '        "$RETAINED_FONT_ALPHA_FIXTURE" \\\n'
        '        "$observed_urls" "$observed_navigation")'
    )
    optimized_alpha_command = (
        'optimized_structure_command=(python3 -O -I -B "$FONT_ALPHA_CHECK" '
        '"$COMMITTED" "$pdf" \\\n'
        '        "$RETAINED_FONT_ALPHA_FIXTURE" \\\n'
        '        "$optimized_urls" "$optimized_navigation")'
    )
    if command_dispatch.count(normal_alpha_command) != 1:
        raise WiringError(
            "normal font-alpha arguments are not COMMITTED, candidate, retained, outputs"
        )
    if command_dispatch.count(optimized_alpha_command) != 1:
        raise WiringError(
            "optimized font-alpha arguments are not COMMITTED, candidate, retained, outputs"
        )
    if (
        "internal unknown structure relation" not in command_dispatch
        or "exit 1" not in command_dispatch
    ):
        raise WiringError("unknown structure relations do not fail closed")

    artifact_start = (
        'if [[ "$MODE" == "--exact" ]]; then\n  cmp -s "$BUILT" "$COMMITTED" || {'
    )
    artifact_end = 'fi\n\nif ! cmp -s "$BUILD_ROOT/built.observed-urls"'
    artifact_with_next_anchor = extract_unique(
        source, artifact_start, artifact_end, "artifact-comparison dispatch"
    )
    artifact_dispatch = artifact_with_next_anchor[
        : -len('\n\nif ! cmp -s "$BUILD_ROOT/built.observed-urls"')
    ]
    if "FONT_ALPHA" in artifact_dispatch or ALPHA_BASENAME in artifact_dispatch:
        raise WiringError(
            "artifact-comparison dispatch routes exact mode through font-alpha"
        )
    if (
        "committed PDF is stale or not same-toolchain reproducible"
        not in artifact_dispatch
    ):
        raise WiringError("raw exact artifact failure diagnostic is absent")

    if source.index(relation_dispatch) > source.index(artifact_dispatch):
        raise WiringError(
            "artifact comparison precedes the strict/alpha structure dispatch"
        )
    return WiringFragments(relation_dispatch, command_dispatch, artifact_dispatch)


def run_bash(script: pathlib.Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "--noprofile", "--norc", str(script), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def require_clean_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0 or result.stdout or result.stderr:
        raise WiringError(
            f"{label} failed or emitted diagnostics: rc={result.returncode}\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
        )


def exercise_relation_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "relation-dispatch.sh"
    harness.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'MODE="$1"\n'
        'TRACE="$2"\n'
        "COMMITTED=/fixture/committed.pdf\n"
        "BUILT=/fixture/built.pdf\n"
        'validate_pdf() { printf \'%s\\t%s\\t%s\\n\' "$1" "$2" "$3" >>"$TRACE"; }\n'
        + fragment
        + "\n",
        encoding="utf-8",
    )
    expected = {
        "--exact": (
            "committed\t/fixture/committed.pdf\tstrict\n"
            "built\t/fixture/built.pdf\tstrict\n"
        ),
        "--cross-toolchain": (
            "committed\t/fixture/committed.pdf\tstrict\n"
            "built\t/fixture/built.pdf\ttyped-font-alpha-from-committed\n"
        ),
    }
    controls = 0
    for mode, expected_trace in expected.items():
        trace = root / f"relation-{mode.removeprefix('--')}.trace"
        result = run_bash(harness, mode, str(trace))
        require_clean_success(result, f"{mode} relation dispatch")
        if trace.read_text(encoding="utf-8") != expected_trace:
            raise WiringError(f"{mode} relation trace changed")
        controls += 1
    return controls


def read_null_vector(path: pathlib.Path) -> list[str]:
    data = path.read_bytes()
    if not data.endswith(b"\0"):
        raise WiringError(f"command-vector trace is not NUL terminated: {path}")
    return [item.decode("utf-8") for item in data[:-1].split(b"\0")]


def exercise_command_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "command-dispatch.sh"
    harness.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'structure_relation="$1"\n'
        'NORMAL_TRACE="$2"\n'
        'OPTIMIZED_TRACE="$3"\n'
        "CHECK_NAME=fixture\n"
        "STRUCTURE_CHECK=/fixture/structure.py\n"
        "FONT_ALPHA_CHECK=/fixture/alpha.py\n"
        "RETAINED_FONT_ALPHA_FIXTURE=/fixture/retained.pdf\n"
        "COMMITTED=/fixture/committed.pdf\n"
        "pdf=/fixture/built.pdf\n"
        "observed_urls=/out/normal.urls\n"
        "observed_navigation=/out/normal.navigation\n"
        "optimized_urls=/out/optimized.urls\n"
        "optimized_navigation=/out/optimized.navigation\n"
        "dispatch() {\n"
        "  local -a structure_command optimized_structure_command\n" + fragment + "\n"
        '  printf \'%s\\0\' "${structure_command[@]}" >"$NORMAL_TRACE"\n'
        '  printf \'%s\\0\' "${optimized_structure_command[@]}" >"$OPTIMIZED_TRACE"\n'
        "}\n"
        "dispatch\n",
        encoding="utf-8",
    )
    expected = {
        "strict": (
            [
                "python3",
                "-I",
                "-B",
                "/fixture/structure.py",
                "/fixture/built.pdf",
                "/out/normal.urls",
                "/out/normal.navigation",
            ],
            [
                "python3",
                "-O",
                "-I",
                "-B",
                "/fixture/structure.py",
                "/fixture/built.pdf",
                "/out/optimized.urls",
                "/out/optimized.navigation",
            ],
        ),
        "typed-font-alpha-from-committed": (
            [
                "python3",
                "-I",
                "-B",
                "/fixture/alpha.py",
                "/fixture/committed.pdf",
                "/fixture/built.pdf",
                "/fixture/retained.pdf",
                "/out/normal.urls",
                "/out/normal.navigation",
            ],
            [
                "python3",
                "-O",
                "-I",
                "-B",
                "/fixture/alpha.py",
                "/fixture/committed.pdf",
                "/fixture/built.pdf",
                "/fixture/retained.pdf",
                "/out/optimized.urls",
                "/out/optimized.navigation",
            ],
        ),
    }
    controls = 0
    for relation, (expected_normal, expected_optimized) in expected.items():
        normal = root / f"command-{relation}.normal"
        optimized = root / f"command-{relation}.optimized"
        result = run_bash(harness, relation, str(normal), str(optimized))
        require_clean_success(result, f"{relation} command dispatch")
        if read_null_vector(normal) != expected_normal:
            raise WiringError(f"{relation} normal command vector changed")
        if read_null_vector(optimized) != expected_optimized:
            raise WiringError(f"{relation} optimized command vector changed")
        controls += 1

    unknown_normal = root / "command-unknown.normal"
    unknown_optimized = root / "command-unknown.optimized"
    unknown = run_bash(
        harness, "unknown-relation", str(unknown_normal), str(unknown_optimized)
    )
    if (
        unknown.returncode == 0
        or "internal unknown structure relation" not in unknown.stderr
    ):
        raise WiringError("unknown structure relation did not fail closed")
    return controls + 1


def exercise_artifact_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "artifact-dispatch.sh"
    harness.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "MODE=--exact\n"
        'BUILT="$1"\n'
        'COMMITTED="$2"\n'
        "CHECK_NAME=fixture\n" + fragment + "\n",
        encoding="utf-8",
    )
    committed = root / "committed.pdf"
    equal = root / "equal.pdf"
    different = root / "different.pdf"
    committed.write_bytes(b"exact-artifact-control\n")
    equal.write_bytes(committed.read_bytes())
    different.write_bytes(b"different-artifact\n")
    require_clean_success(
        run_bash(harness, str(equal), str(committed)),
        "raw-equal exact artifact dispatch",
    )
    rejected = run_bash(harness, str(different), str(committed))
    if (
        rejected.returncode == 0
        or rejected.stdout
        or "committed PDF is stale or not same-toolchain reproducible"
        not in rejected.stderr
    ):
        raise WiringError(
            "raw-different exact artifacts were not rejected with the fixed diagnostic"
        )
    return 2


def expect_mutation_rejected(source: str, old: str, new: str, label: str) -> None:
    if source.count(old) != 1:
        raise WiringError(f"self-test mutation anchor is not unique for {label}")
    mutated = source.replace(old, new, 1)
    try:
        audit_wrapper(mutated)
    except WiringError:
        return
    raise WiringError(f"hostile wrapper mutation passed: {label}")


def run_mutation_suite(source: str) -> int:
    mutations = (
        (
            'if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            'if [[ "$MODE" != "--exact" ]]; then',
            "widened mode allow-list",
        ),
        (
            'TMP_BASE="$(CDPATH=\'\' cd -- "${TMPDIR:-/tmp}" && pwd -P)"',
            'TMP_BASE="${TMPDIR:-/tmp}"',
            "lexical temporary root",
        ),
        (
            'validate_pdf committed "$COMMITTED" strict',
            'validate_pdf committed "$COMMITTED" typed-font-alpha-from-committed',
            "non-strict committed PDF",
        ),
        (
            'validate_pdf built "$BUILT" strict',
            'validate_pdf built "$BUILT" typed-font-alpha-from-committed',
            "alpha relation in exact mode",
        ),
        (
            'validate_pdf built "$BUILT" typed-font-alpha-from-committed',
            'validate_pdf built "$BUILT" strict',
            "missing cross alpha relation",
        ),
        (
            'structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf"',
            'structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$pdf" "$COMMITTED"',
            "reversed alpha reference and candidate",
        ),
        (
            '        "$RETAINED_FONT_ALPHA_FIXTURE" \\\n'
            '        "$observed_urls" "$observed_navigation")',
            '        "$observed_urls" "$observed_navigation")',
            "missing normal retained fixture argument",
        ),
        (
            '        "$RETAINED_FONT_ALPHA_FIXTURE" \\\n'
            '        "$observed_urls" "$observed_navigation")',
            '        "$COMMITTED" \\\n        "$observed_urls" "$observed_navigation")',
            "wrong normal retained fixture argument",
        ),
        (
            "ID_VARIANCE_CHECK_SHA256="
            "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
            "ID_VARIANCE_CHECK_SHA256=" + "0" * 64,
            "trailer-ID checker digest drift",
        ),
        (
            'python3 -O -I -B "$FONT_ALPHA_CHECK"',
            'python3 -I -B "$FONT_ALPHA_CHECK"',
            "missing optimized alpha route",
        ),
        (
            'cmp -s "$BUILT" "$COMMITTED" || {',
            "true || {",
            "removed raw exact comparison",
        ),
        (
            'if ! cmp -s "$observed_urls" "$optimized_urls" \\\n'
            '      || ! cmp -s "$observed_navigation" "$optimized_navigation"; then',
            "if false; then",
            "removed projection parity",
        ),
        (
            'if ! cmp -s "$BUILD_ROOT/$label.structure.stdout" \\\n'
            '      "$BUILD_ROOT/$label.structure-optimized.stdout"; then',
            "if false; then",
            "removed diagnostic parity",
        ),
        (
            'if [[ -s "$structure_stderr" ]]; then',
            "if false; then",
            "removed zero-stderr policy",
        ),
        (
            (
                '      echo "$CHECK_NAME: internal unknown structure relation: '
                '$structure_relation" >&2'
            ),
            "      :",
            "suppressed unknown-relation diagnostic",
        ),
    )
    for old, new, label in mutations:
        expect_mutation_rejected(source, old, new, label)
    return len(mutations)


def main() -> int:
    try:
        wrapper = read_direct(WRAPPER, "guide PDF wrapper")
        guide_builder = read_direct(GUIDE_BUILDER, "guide PDF builder")
        sxpid3_wrapper = read_direct(SXPID3_WRAPPER, "SxPID3 PDF wrapper")
        sxpid3_builder = read_direct(SXPID3_BUILDER, "SxPID3 PDF builder")
        for path in (WRAPPER, GUIDE_BUILDER, SXPID3_WRAPPER, SXPID3_BUILDER):
            syntax = subprocess.run(
                ["bash", "--noprofile", "--norc", "-n", str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if syntax.returncode != 0 or syntax.stdout or syntax.stderr:
                raise WiringError(
                    f"shell syntax check failed for {path}: "
                    f"{syntax.stdout}{syntax.stderr}"
                )
        audit_auxiliary_sources(guide_builder, sxpid3_wrapper, sxpid3_builder)
        fragments = audit_wrapper(wrapper)
        hostile_count = run_mutation_suite(wrapper)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-guide-mode-wiring-self-test."
        ) as raw:
            temporary_root = pathlib.Path(raw).resolve(strict=True)
            controls = (
                4  # direct inputs plus shell syntax for the four bound shell sources
            )
            controls += exercise_relation_dispatch(
                temporary_root, fragments.relation_dispatch
            )
            controls += exercise_command_dispatch(
                temporary_root, fragments.command_dispatch
            )
            controls += exercise_artifact_dispatch(
                temporary_root, fragments.artifact_dispatch
            )
    except (OSError, UnicodeError, WiringError) as error:
        fail(str(error))
    print(
        "OK: guide PDF mode wiring "
        f"(controls={controls}; hostile_mutations={hostile_count}; "
        "exact_alpha_artifact_invocations=0; cross_alpha_python_modes=2)"
    )
    print(
        "Boundary: source-extracted dispatch and wrapper custody only; "
        "the complete renderer and typed PDF relation are tested by their separate gates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
