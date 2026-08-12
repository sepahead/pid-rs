#!/usr/bin/env python3
"""Kernel-check the scoped KSG positive-integer harmonic obligations in pinned Lean.

The revision-4 extension defines exact rational harmonic finite sums and proves recurrence,
monotonicity, four-term cancellation under an explicit positive-integer digamma premise, the
min/max range identity, exact rational and real full-tail bounds, source symmetry, and the
exclusive/inclusive count-index consequences. The checker separately preserves the exact
revision-2 source bytes at both historical paths; the unversioned path is not a revision-4 mirror.
It does not prove the digamma premise, neighbor-count geometry, estimator properties, support
assumptions, PID semantics, floating-point behavior, or Rust refinement.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = ROOT / "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean"
UNVERSIONED_RETAINED_V2_SOURCE = (
    ROOT / "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean"
)
RETAINED_V2_SOURCE = (
    ROOT / "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean"
)
EXPECTED_SOURCE_SHA256 = (
    "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4"
)
EXPECTED_V2_SOURCE_SHA256 = (
    "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943"
)
EXPECTED_MANIFEST_SHA256 = (
    "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af"
)
EXPECTED_TOOLCHAIN_SHA256 = (
    "302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b"
)
EXPECTED_LAKEFILE_SHA256 = (
    "ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0"
)
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.33.0"
EXPECTED_LEAN_VERSION = "4.33.0"
EXPECTED_LEAN_COMMIT = "d8b18978322de05a8f3dba51ef03cf5461676c17"
EXPECTED_LEAN_BUILD = "Release"
EXPECTED_IMPORTS = (
    "import Mathlib.Data.Rat.BigOperators",
    "import Mathlib.Data.Real.Basic",
    "import Mathlib.Algebra.BigOperators.Group.Finset.Basic",
    "import Mathlib.Tactic.Linarith",
    "import Mathlib.Tactic.Positivity",
    "import Mathlib.Tactic.Ring",
)
THEOREMS = (
    "PidKsgIntegerHarmonic.harmonic_zero",
    "PidKsgIntegerHarmonic.harmonic_succ",
    "PidKsgIntegerHarmonic.harmonic_monotone",
    "PidKsgIntegerHarmonic.direct_eq_symmetric_range",
    "PidKsgIntegerHarmonic.direct_source_swap",
    "PidKsgIntegerHarmonic.symmetric_range_source_swap",
    "PidKsgIntegerHarmonic.symmetric_range_term_cast",
    "PidKsgIntegerHarmonic.symmetric_range_components_bounded",
    "PidKsgIntegerHarmonic.symmetric_range_term_bounded",
    "PidKsgIntegerHarmonic.digamma_four_term_cancellation",
    "PidKsgIntegerHarmonic.digamma_four_term_symmetric_range_bounded",
    "PidKsgIntegerHarmonic.exclusive_argument_predecessor",
    "PidKsgIntegerHarmonic.exclusive_argument_bounds",
    "PidKsgIntegerHarmonic.inclusive_argument_identity",
    "PidKsgIntegerHarmonic.inclusive_argument_bounds",
    "PidKsgIntegerHarmonic.exclusive_direct_index_map",
    "PidKsgIntegerHarmonic.exclusive_symmetric_range",
    "PidKsgIntegerHarmonic.inclusive_direct_index_map",
    "PidKsgIntegerHarmonic.inclusive_symmetric_range",
)
PERMITTED_AXIOMS = frozenset(("propext", "Classical.choice", "Quot.sound"))
PROHIBITED_SOURCE = re.compile(
    r"\b(sorry|sorryAx|admit|axiom|constant|native_decide|unsafe)\b"
)
REQUIRED_SCOPE_SENTINELS = (
    "special-function bridge is deliberately a typed premise",
    "does not construct the analytic digamma function",
    "does not formalize neighbor geometry",
    "shared-exclusions event semantics",
    "Rust refinement",
)
LEAN_VERSION_LINE = re.compile(
    r"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    r"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
    r"commit (?P<commit>[0-9a-f]{40}), "
    r"(?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)"
)
TIMEOUT_SECONDS = 240


class LeanKsgHarmonicError(RuntimeError):
    """The source, environment, compilation, or axiom audit failed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanKsgHarmonicError(message)


def parse_lean_version_probe(probe: subprocess.CompletedProcess[str]) -> str:
    """Validate the exact release identity and one-line process transport."""

    require(
        probe.returncode == 0,
        f"Lean version probe exited unsuccessfully: {probe.returncode}",
    )
    require(
        probe.stderr == "",
        f"Lean version probe emitted unexpected stderr: {probe.stderr!r}",
    )
    require(
        probe.stdout.endswith("\n"),
        "Lean version probe stdout lacks its final newline",
    )
    line = probe.stdout[:-1]
    require(
        "\n" not in line and "\r" not in line,
        "Lean version probe did not emit exactly one LF line",
    )
    matched = LEAN_VERSION_LINE.fullmatch(line)
    require(matched is not None, f"unexpected Lean version output: {probe.stdout!r}")
    identity = (
        matched.group("version"),
        matched.group("commit"),
        matched.group("build"),
    )
    expected = (EXPECTED_LEAN_VERSION, EXPECTED_LEAN_COMMIT, EXPECTED_LEAN_BUILD)
    require(
        identity == expected,
        f"unexpected Lean portable identity: expected {expected!r}, found {identity!r}",
    )
    return line


def mask_lean_comments_and_strings(text: str) -> str:
    masked = list(text)
    index = 0
    block_depth = 0
    in_string = False
    while index < len(text):
        if block_depth:
            if text.startswith("/-", index):
                masked[index : index + 2] = (" ", " ")
                block_depth += 1
                index += 2
            elif text.startswith("-/", index):
                masked[index : index + 2] = (" ", " ")
                block_depth -= 1
                index += 2
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
        elif in_string:
            if text[index] == "\\":
                masked[index] = " "
                index += 1
                if index < len(text):
                    if text[index] != "\n":
                        masked[index] = " "
                    index += 1
            elif text[index] == '"':
                masked[index] = " "
                in_string = False
                index += 1
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
        elif text.startswith("/-", index):
            masked[index : index + 2] = (" ", " ")
            block_depth = 1
            index += 2
        elif text.startswith("--", index):
            while index < len(text) and text[index] != "\n":
                masked[index] = " "
                index += 1
        elif text[index] == '"':
            masked[index] = " "
            in_string = True
            index += 1
        else:
            index += 1
    require(block_depth == 0, "Lean source contains an unterminated block comment")
    require(not in_string, "Lean source contains an unterminated string")
    return "".join(masked)


def parse_axiom_inventory(output: str) -> dict[str, frozenset[str]]:
    pattern = re.compile(
        r"'([^']+)' (?:depends on axioms: \[(.*?)\]|does not depend on any axioms)",
        re.DOTALL,
    )
    inventory: dict[str, frozenset[str]] = {}
    for match in pattern.finditer(output):
        payload = match.group(2)
        axioms = (
            frozenset()
            if payload is None
            else frozenset(part.strip() for part in payload.split(",") if part.strip())
        )
        inventory[match.group(1)] = axioms
    return inventory


def run_lean(lake: str, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [lake, "env", "lean", str(source)],
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=TIMEOUT_SECONDS,
    )


def verify_dependency_checkouts() -> None:
    manifest = json.loads((PROJECT / "lake-manifest.json").read_text(encoding="utf-8"))
    packages = manifest.get("packages")
    require(
        isinstance(packages, list)
        and packages
        and all(isinstance(package, dict) for package in packages),
        "pinned Lake package manifest is malformed",
    )
    git = shutil.which("git")
    require(git is not None, "git is not available for Lean dependency custody")
    isolated_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    isolated_environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    for package in packages:
        name = package.get("name")
        revision = package.get("rev")
        origin = package.get("url")
        require(
            isinstance(name, str)
            and name
            and isinstance(revision, str)
            and revision
            and isinstance(origin, str)
            and origin,
            "Lake package pin is incomplete",
        )
        checkout = PROJECT / ".lake/packages" / name
        require(
            checkout.is_dir() and not checkout.is_symlink(),
            f"Lean dependency checkout is absent or symlinked: {name}",
        )

        def git_output(arguments: list[str], label: str) -> str:
            process = subprocess.run(
                [git, "-C", str(checkout), *arguments],
                env=isolated_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=60,
            )
            require(
                process.returncode == 0 and process.stderr == "",
                f"{name} {label} failed: {process.stderr}",
            )
            return process.stdout.strip()

        root = Path(
            git_output(["rev-parse", "--show-toplevel"], "root check")
        ).resolve()
        require(root == checkout.resolve(), f"Lean dependency root mismatch: {name}")
        actual_revision = git_output(
            ["rev-parse", "--verify", "HEAD"], "revision check"
        )
        require(
            actual_revision == revision,
            f"Lean dependency revision mismatch for {name}: {actual_revision}",
        )
        actual_origin = git_output(
            ["config", "--local", "--get", "remote.origin.url"], "origin check"
        )
        require(
            actual_origin.rstrip("/") == origin.rstrip("/"),
            f"Lean dependency origin mismatch for {name}: {actual_origin}",
        )
        require(
            git_output(["status", "--porcelain=v1", "--untracked-files=all"], "clean check")
            == "",
            f"Lean dependency checkout is dirty: {name}",
        )


def verify_environment_and_source() -> tuple[str, str]:
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Lean source digest drifted")
    require(
        sha256(UNVERSIONED_RETAINED_V2_SOURCE) == EXPECTED_V2_SOURCE_SHA256,
        "unversioned historical Lean source digest drifted",
    )
    require(
        sha256(RETAINED_V2_SOURCE) == EXPECTED_V2_SOURCE_SHA256,
        "retained revision-2 Lean source digest drifted",
    )
    require(
        UNVERSIONED_RETAINED_V2_SOURCE.read_bytes()
        == RETAINED_V2_SOURCE.read_bytes(),
        "unversioned historical Lean source is not the exact retained revision-2 source",
    )
    require(
        sha256(PROJECT / "lake-manifest.json") == EXPECTED_MANIFEST_SHA256,
        "pinned Lake manifest digest drifted",
    )
    require(
        sha256(PROJECT / "lean-toolchain") == EXPECTED_TOOLCHAIN_SHA256,
        "Lean toolchain file digest drifted",
    )
    require(
        sha256(PROJECT / "lakefile.toml") == EXPECTED_LAKEFILE_SHA256,
        "Lake configuration digest drifted",
    )
    require(
        (PROJECT / "lean-toolchain").read_text(encoding="utf-8").strip()
        == EXPECTED_TOOLCHAIN,
        "Lean toolchain identifier drifted",
    )
    verify_dependency_checkouts()

    source_text = SOURCE.read_text(encoding="utf-8")
    imports = tuple(
        line for line in source_text.splitlines() if line.startswith("import ")
    )
    require(imports == EXPECTED_IMPORTS, f"Lean import inventory drifted: {imports}")
    source_code = mask_lean_comments_and_strings(source_text)
    require(
        PROHIBITED_SOURCE.search(source_code) is None,
        "Lean source contains a prohibited proof escape",
    )
    for sentinel in REQUIRED_SCOPE_SENTINELS:
        require(sentinel in source_text, f"Lean scope sentinel is absent: {sentinel}")
    for theorem in THEOREMS:
        short_name = theorem.rsplit(".", maxsplit=1)[1]
        require(
            len(re.findall(rf"\btheorem\s+{re.escape(short_name)}\b", source_code))
            == 1,
            f"Lean theorem declaration is absent or ambiguous: {theorem}",
        )

    lake = shutil.which("lake")
    require(lake is not None, "lake is not available")
    version = subprocess.run(
        [lake, "env", "lean", "--version"],
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=60,
    )
    return lake, parse_lean_version_probe(version)


def main() -> int:
    try:
        lake, version = verify_environment_and_source()
        source_text = SOURCE.read_text(encoding="utf-8")
        query = (
            source_text
            + "\n"
            + "\n".join(f"#print axioms {theorem}" for theorem in THEOREMS)
            + "\n"
        )
        with tempfile.TemporaryDirectory(prefix="pid-ksg-harmonic-lean-") as directory:
            query_path = Path(directory) / "PidKsgIntegerHarmonicCheck.lean"
            query_path.write_text(query, encoding="utf-8")
            checked = run_lean(lake, query_path)
        require(checked.returncode == 0, f"Lean kernel check failed: {checked.stderr}")
        require(
            not checked.stderr.strip(),
            f"Lean emitted unexpected stderr: {checked.stderr}",
        )

        inventory = parse_axiom_inventory(checked.stdout)
        require(set(inventory) == set(THEOREMS), "Lean theorem axiom inventory changed")
        for theorem, axioms in inventory.items():
            require(
                axioms <= PERMITTED_AXIOMS,
                f"theorem {theorem} uses unapproved axioms: {sorted(axioms)}",
            )

        result = {
            "schema": "pid-rs/lean-ksg-integer-harmonic-check/v2",
            "status": "passed",
            "source_revision": 4,
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "unversioned_historical_source_sha256": EXPECTED_V2_SOURCE_SHA256,
            "retained_v2_source_sha256": EXPECTED_V2_SOURCE_SHA256,
            "unversioned_historical_equals_retained_v2": True,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "lake_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "lean_toolchain": EXPECTED_TOOLCHAIN,
            "lean_version": version,
            "theorems_kernel_checked": len(THEOREMS),
            "permitted_axioms": sorted(PERMITTED_AXIOMS),
            "axiom_inventory": {
                theorem: sorted(inventory[theorem]) for theorem in THEOREMS
            },
            "typed_unproved_premise": (
                "PositiveIntegerDigammaPremise: for each positive integer m used, "
                "psi(m)=H_(m-1)-eulerConstant"
            ),
            "boundary": (
                "Exact finite-sum/monotonicity/cancellation/index/range/symmetry, rational-tail "
                "bounds, and the explicit rational-to-real bounded-combination theorem only. "
                "The analytic digamma premise, count geometry, binary64, estimators, support, "
                "PID semantics, Rust refinement, calibration, and consumers remain outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        LeanKsgHarmonicError,
    ) as error:
        print(f"Lean KSG integer-harmonic check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
