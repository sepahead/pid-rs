#!/usr/bin/env python3
"""Replay the separate Lean 4.33 SxPID3 informative-invariance lane.

This checker deliberately does not alter or extend the frozen aggregate
PidFiniteConvergence root. It binds one standalone source and its two local
source dependencies, reuses the immutable aggregate checker's environment
custody helpers, compiles the standalone source, and audits every named theorem's
axiom basis.

The result is an arbitrary-finite algebraic theorem about source-only events and
one supplied fixed linear transform. It is not a paper-correspondence theorem,
an executable-refinement theorem, a minus/net invariance theorem, or evidence
covered by the historical r12/v7 aggregate receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-lean-sxpid3-informative-invariance.py requires "
        "Python 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = (
    ROOT
    / "audit/formal/lean-sxpid3-informative-invariance"
    / "PidSxPid3InformativeInvariance.lean"
)
LANE_DIRECTORY = SOURCE.parent
BASE_CHECKER = ROOT / "scripts/check-lean-finite-convergence.py"
AGGREGATE_ROOT = PROJECT / "PidFiniteConvergence.lean"

EXPECTED_SOURCE_SHA256 = (
    "db597daac0c33fc941908571a72a6787b88fe610ace9360aeca9b4f9916a1dbb"
)
EXPECTED_BASE_CHECKER_SHA256 = (
    "3ea61295232a03b08522a10257f82865038e760fe47eda34b7f470d2f8f268a0"
)
EXPECTED_AGGREGATE_ROOT_SHA256 = (
    "3b99c57000d6bf14077e8caf4de2f86d27f9654a8d984c9fc59d720947de84f8"
)
EXPECTED_LOCAL_DEPENDENCIES = {
    "PidFiniteConvergence/Deterministic.lean": (
        "e9dbd7c5b4578aabf92b76c0b8b684db4c1c1038dcdb033239b0076685c41610"
    ),
    "PidFiniteConvergence/SxEventBridge.lean": (
        "cfedf974c73e11e56041013a47797462100f4b896235d6c4185c9ca0a232d77e"
    ),
}
EXPECTED_OPERATIONAL_WIRING = {
    ".github/workflows/sxpid3-informative-invariance.yml": (
        "f6b13f3d0e9d0c28b2d5bc234035f23570e8c9359558e9daa2b46664bbf07be1"
    ),
    "audit/formal/lean-sxpid3-informative-invariance/AGENTS.md": (
        "57caa77b6549116094081155406f44bf58d65505de71efb9a0a8327d1f533304"
    ),
    "justfile.sxpid3-informative-invariance": (
        "78e4bc8421438171e786f654a8b6ca1cd34a76e01f6758c91b309bd517e59cce"
    ),
}
EXPECTED_IMPORTS = (
    "import Mathlib.Analysis.Calculus.Deriv.Basic",
    "import PidFiniteConvergence.SxEventBridge",
)
EXPECTED_DECLARATIONS = (
    "abbrev CategoricalSourceKey",
    "def categoricalSourceMarginal",
    "def sourceOnlyBranchEvent",
    "def sxSourceOnlyEvent",
    "theorem sx_source_event_eq_source_only_product",
    "theorem finite_event_mass_source_product_eq_marginal_mass",
    "theorem sx_source_event_mass_eq_source_marginal_mass",
    "def averagedInformativeCumulative",
    "def averagedInformativeCumulativeFromSourceMarginal",
    "theorem averaged_informative_cumulative_eq_source_marginal_sum",
    "theorem averaged_informative_cumulative_factors_through_source_marginal",
    "theorem averaged_informative_cumulative_invariant_of_source_marginal_eq",
    "theorem averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target",
    "theorem averaged_informative_cumulative_constant_on_fixed_source_marginal",
    "theorem averaged_informative_cumulative_hasDerivAt_zero_of_fixed_source_marginal",
    "def positiveCategoricalSupport",
    "def IsCategoricalProbabilityLaw",
    "def averagedInformativeCumulativeOnPositiveSupport",
    "theorem averaged_informative_on_positive_support_eq_full",
    "theorem probability_averaged_informative_invariant_of_source_marginal_eq",
    "theorem probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target",
    "def fixedLinearTransform",
    "theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq",
    "theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target",
    "theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq",
    "theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target",
)
EXPECTED_THEOREMS = tuple(
    declaration.split(" ", 1)[1]
    for declaration in EXPECTED_DECLARATIONS
    if declaration.startswith("theorem ")
)
EXPECTED_SCOPE_SENTINELS = (
    "even when their finite target alphabets differ",
    "a separately justified Mobius inverse",
    "does not prove that a supplied collection family is the Makkeh--Gutknecht--Wibral redundancy",
    "or that any misinformative, signed-net, continuous, sampling, causal,",
    "Exact constancy along a fixed-source-marginal path is the primary result",
)
FORBIDDEN_SCOPE_CLAIMS = (
    "formally verifies the Rust",
    "proves paper correspondence",
    "proves misinformative invariance",
    "proves net invariance",
    "is covered by r12",
)
PROHIBITED_CODE = re.compile(
    r"\b(?:admit|axiom|constant|native_decide|sorry|sorryAx|unsafe)\b"
)
AGGREGATE_IMPORT = "import PidFiniteConvergence.InformativeInvariance"


class InformativeInvarianceError(RuntimeError):
    """The source, separate-lane custody, compilation, or axiom audit failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InformativeInvarianceError(message)


def sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise InformativeInvarianceError(f"required regular file is missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_exact_module(path: Path, expected_sha256: str, name: str) -> ModuleType:
    require(
        path.is_file() and not path.is_symlink(),
        f"required regular Python source is missing: {path}",
    )
    source = path.read_bytes()
    require(
        hashlib.sha256(source).hexdigest() == expected_sha256,
        f"Python source digest drifted: {path}",
    )
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    code = compile(
        source,
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


def load_base_checker() -> ModuleType:
    try:
        return compile_exact_module(
            BASE_CHECKER,
            EXPECTED_BASE_CHECKER_SHA256,
            "pid_finite_convergence_c7_checker",
        )
    except InformativeInvarianceError as error:
        if "Python source digest drifted" in str(error):
            raise InformativeInvarianceError(
                "immutable aggregate checker digest drifted"
            ) from error
        raise


def check_source(base: ModuleType) -> str:
    require(
        sha256(SOURCE) == EXPECTED_SOURCE_SHA256,
        "standalone Lean source digest drifted",
    )
    require(
        sha256(AGGREGATE_ROOT) == EXPECTED_AGGREGATE_ROOT_SHA256,
        "frozen aggregate Lean root digest drifted",
    )
    root_text = base.read_regular_text(AGGREGATE_ROOT)
    require(
        AGGREGATE_IMPORT not in root_text,
        "standalone theorem must not be imported by the frozen aggregate root",
    )
    for relative, expected_digest in EXPECTED_LOCAL_DEPENDENCIES.items():
        require(
            sha256(PROJECT / relative) == expected_digest,
            f"local Lean dependency digest drifted: {relative}",
        )
    for relative, expected_digest in EXPECTED_OPERATIONAL_WIRING.items():
        require(
            sha256(ROOT / relative) == expected_digest,
            f"separate-lane operational wiring digest drifted: {relative}",
        )

    source_text = base.read_regular_text(SOURCE)
    lane_sources = {path.absolute() for path in LANE_DIRECTORY.rglob("*.lean")}
    require(
        lane_sources == {SOURCE.absolute()},
        "standalone Lean lane source manifest must contain exactly the pinned source",
    )
    lines = source_text.splitlines()
    require(
        tuple(lines[: len(EXPECTED_IMPORTS)]) == EXPECTED_IMPORTS,
        "standalone Lean import roster drifted",
    )
    require(
        all(
            not line.startswith("import ")
            for line in lines[len(EXPECTED_IMPORTS) :]
        ),
        "standalone Lean source contains an unpinned later import",
    )
    require(
        "set_option autoImplicit false\n" in source_text
        and "set_option warningAsError true\n" in source_text,
        "standalone Lean source must retain strict options",
    )
    masked = base.mask_lean_comments_and_strings(source_text, SOURCE)
    prohibited = PROHIBITED_CODE.search(masked)
    require(
        prohibited is None,
        "standalone Lean source contains prohibited proof code",
    )
    declarations = base.source_declaration_inventory(source_text, SOURCE)
    require(
        declarations == EXPECTED_DECLARATIONS,
        f"standalone Lean declaration roster drifted: {declarations!r}",
    )
    require(len(EXPECTED_DECLARATIONS) == 26, "internal declaration count drifted")
    require(len(EXPECTED_THEOREMS) == 16, "internal theorem count drifted")
    for sentinel in EXPECTED_SCOPE_SENTINELS:
        require(sentinel in source_text, f"scope sentinel is absent: {sentinel!r}")
    widening = next(
        (claim for claim in FORBIDDEN_SCOPE_CLAIMS if claim in source_text), None
    )
    require(widening is None, f"forbidden scope-widening claim is present: {widening}")
    return source_text


def theorem_axiom_audit_source(source_text: str) -> str:
    lean_quote = chr(96) * 2
    declarations = "\n".join(
        "    "
        + lean_quote
        + "PidFiniteConvergence."
        + theorem
        + ","
        for theorem in EXPECTED_THEOREMS
    )
    return (
        "import Lean.Util.CollectAxioms\n"
        + source_text
        + "\nopen Lean\n\n"
        + "run_cmd do\n"
        + "  let allowed :=\n"
        + "    ({} : NameSet)\n"
        + "      |>.insert "
        + lean_quote
        + "propext\n"
        + "      |>.insert "
        + lean_quote
        + "Classical.choice\n"
        + "      |>.insert "
        + lean_quote
        + "Quot.sound\n"
        + "  let declarations : Array Name := #[\n"
        + declarations
        + "\n  ]\n"
        + f"  unless declarations.size == {len(EXPECTED_THEOREMS)} do\n"
        + "    throwError m!\"informative theorem inventory size drifted\"\n"
        + "  for declaration in declarations do\n"
        + "    let used ← collectAxioms declaration\n"
        + "    for assumption in used do\n"
        + "      unless allowed.contains assumption do\n"
        + "        throwError m!\"unexpected logical assumption {assumption} used by {declaration}\"\n"
    )


def portable_identity(base: ModuleType, version_line: str) -> dict[str, str]:
    matched = base.LEAN_VERSION_LINE.fullmatch(version_line)
    require(matched is not None, "validated Lean version line could not be reparsed")
    return {
        "version": matched.group("version"),
        "commit": matched.group("commit"),
        "build": matched.group("build"),
    }


def run_strict(
    base: ModuleType,
    command: list[str],
    description: str,
    *,
    input_text: str | None = None,
    allow_stdout: bool = False,
) -> None:
    environment = os.environ.copy()
    for key in base.REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    arguments: dict[str, object] = {
        "cwd": PROJECT,
        "env": environment,
        "capture_output": True,
        "text": True,
        "timeout": base.TIMEOUT_SECONDS,
        "check": False,
    }
    if input_text is None:
        arguments["stdin"] = subprocess.DEVNULL
    else:
        arguments["input"] = input_text
    try:
        process = subprocess.run(command, **arguments)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InformativeInvarianceError(f"{description} failed: {error}") from error
    require(
        process.returncode == 0,
        f"{description} failed with exit {process.returncode}: "
        f"stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    require(
        process.stderr == "",
        f"{description} emitted unexpected stderr: {process.stderr!r}",
    )
    require(
        allow_stdout or process.stdout == "",
        f"{description} emitted unexpected stdout: {process.stdout!r}",
    )


def run() -> dict[str, object]:
    base = load_base_checker()
    base.check_toolchain()
    base.check_lakefile()
    base.check_manifest()
    source_text = check_source(base)

    lake = base.find_lake()
    git = base.find_git()
    version_line = base.check_version(lake)
    base.check_dependency_checkouts(git)

    run_strict(
        base,
        [str(lake), "build", "PidFiniteConvergence.SxEventBridge"],
        "pinned local dependency build",
        # Lake's successful build-progress transport is environment/cache dependent.
        # It is deliberately not an evidence digest; successful stderr is forbidden.
        allow_stdout=True,
    )
    run_strict(
        base,
        [
            str(lake),
            "env",
            "leanchecker",
            "--fresh",
            "PidFiniteConvergence.SxEventBridge",
        ],
        "pinned local dependency fresh-kernel replay",
    )
    run_strict(
        base,
        [str(lake), "env", "lean", "-t", "0", str(SOURCE)],
        "standalone informative-invariance compilation",
    )
    run_strict(
        base,
        [str(lake), "env", "lean", "-t", "0", "--stdin"],
        "standalone informative-invariance axiom audit",
        input_text=theorem_axiom_audit_source(source_text),
    )

    return {
        "schema": "pid-rs/lean-sxpid3-informative-invariance-check/v1",
        "status": "passed",
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "local_dependency_sha256": dict(sorted(EXPECTED_LOCAL_DEPENDENCIES.items())),
        "aggregate_root_sha256": EXPECTED_AGGREGATE_ROOT_SHA256,
        "base_checker_sha256": EXPECTED_BASE_CHECKER_SHA256,
        "checker_source_sha256": sha256(Path(__file__).resolve()),
        "operational_wiring_sha256": dict(sorted(EXPECTED_OPERATIONAL_WIRING.items())),
        "lake_manifest_sha256": base.EXPECTED_MANIFEST_SHA256,
        "lakefile_sha256": hashlib.sha256(
            base.EXPECTED_LAKEFILE.encode("utf-8")
        ).hexdigest(),
        "lean_toolchain_sha256": hashlib.sha256(
            f"{base.TOOLCHAIN}\n".encode("utf-8")
        ).hexdigest(),
        "lean_portable_identity": portable_identity(base, version_line),
        "dependency_checkout_count": len(base.EXPECTED_PACKAGE_PINS),
        "dependency_checkout_revisions": {
            name: pin[1] for name, pin in sorted(base.EXPECTED_PACKAGE_PINS.items())
        },
        "declaration_count": len(EXPECTED_DECLARATIONS),
        "theorem_count": len(EXPECTED_THEOREMS),
        "permitted_axioms": ["Classical.choice", "Quot.sound", "propext"],
        "dependency_build_transport": (
            "Lake build required exit zero and empty stderr; cache-dependent stdout "
            "progress was accepted but is not an evidence digest. Every direct Lean and "
            "leanchecker replay required empty stdout and stderr."
        ),
        "aggregate_boundary": (
            "Separate append-only lane: it neither changes nor is covered by the frozen "
            "PidFiniteConvergence aggregate, r12 receipt, toolchain-freeze r12, or composite v7."
        ),
        "evidence_ceiling": (
            "Arbitrary-finite algebra for supplied source-only events and any one supplied "
            "fixed finite linear transform. No MGW 18-node correspondence, Mobius-coefficient "
            "identity, Rust/count/binary64 refinement, misinformative/net invariance, changing "
            "source alphabet or lattice, continuous estimation, sampling-to-population inference, "
            "calibration, causal, authenticity, or scientific-priority conclusion. Source hashes, "
            "a fresh replay, "
            "and a portable version probe do not establish source-to-olean authenticity or "
            "reuse the r12 executable/archive identity."
        ),
    }


def main() -> int:
    try:
        result = run()
    except (OSError, UnicodeError, ImportError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
