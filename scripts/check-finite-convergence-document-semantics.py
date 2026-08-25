#!/usr/bin/env python3
"""Fail closed on high-risk semantic drift in the finite-convergence papers.

This checker binds a small set of publication-critical distinctions across the Markdown,
LaTeX, and method catalog. It is a change detector, not a proof checker or literature review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


DEPENDENCY_MD = Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md")
FINITE_MD = Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md")
DEPENDENCY_TEX = Path("audit/formal/latex/dependency-colored-sxpid-concentration.tex")
FINITE_TEX = Path("audit/formal/latex/finite-alphabet-plugin-convergence.tex")
CATALOG = Path("method-catalog.json")


class SemanticDriftError(RuntimeError):
    """A publication-critical semantic anchor is absent or contradicted."""


REQUIRED_TEXT: dict[Path, tuple[str, ...]] = {
    DEPENDENCY_MD: (
        "Terminology: there is no PID measure called “colored PID.”",
        "## Why a coloring appears, and what it is for",
        "The quantity called $V_n$ below is **not new mathematics from pid-rs**.",
        "Janson's\nRemark 3.3 explicitly retains this cover-specific quantity",
        "### Definition DC-D1 — complete rows, one common row law, and a predeclared coloring",
        (
            "This says that the rows are **identically distributed**. It does not say "
            "they are mutually\nindependent."
        ),
        "### Definition DC-D2 — cumulative-prefix empirical law and class-load factor",
        "### Theorem DC-1 — dependency-colored empirical-law bound",
        "This is a paper-derived specialization and composition, not a new concentration method.",
        "Apply this identity with $Q=\\widehat P_n$.",
        "There is no additional factor of two.",
        "### Definition DC-D3 — one nested infinite sequence and its prefix loads",
        "### Theorem DC-2 — Anytime law envelope for cumulative prefixes",
        "### Corollary DC-2a — fixed-width overlapping windows",
        "### Corollary DC-2b — strong $\\ell$-dependence",
        "### Theorem DC-3 — average-law concentration and explicit reference-law drift",
        "see Rota (1964)",
        "## 7. Counterexamples and invalidated routes",
        "## 8. Formal and executable boundary",
    ),
    FINITE_MD: (
        "It is not\na new PID functional, estimator, or scientific-novelty claim.",
        "## What problem this note solves",
        "not a construction introduced here; see Rota (1964).",
        "### Definition FA-D1 — cumulative-prefix empirical law",
        (
            "The label FA-D1 and the phrase **cumulative-prefix empirical law** are "
            "definitions local to this"
        ),
        "### Theorem FA-1 — Deterministic plug-in implication",
        "### Corollary FA-2 — i.i.d. or stationary ergodic sampling",
        "### Theorem FA-3 — time-uniform i.i.d. cumulative-prefix envelope",
        (
            "The labeled composition is project documentation; no mathematical priority "
            "or\nscientific-novelty claim is made."
        ),
        "## 6. Frozen-transform corollary",
        "Evaluation rows are conditionally i.i.d. given $\\mathcal G$.",
        "It is not generally the same as the quantity of the unconditional mixture.",
        "## 7. Falsification lenses and retained counterexamples",
        "## 9. Formal and numerical evidence boundary",
    ),
    DEPENDENCY_TEX: (
        "There is no measure called ``colored PID'': coloring",
        r"\subsection*{Why the color map exists}",
        "The quantity denoted $V_n$ is not new mathematics from \\texttt{pid-rs}.",
        "cover-specific $T^2$ in the proof of Theorem~2.1, Equations~(3.1)--(3.3)",
        r"\begin{definition}[DC-D1: complete rows, one common row law, and predeclared coloring]",
        "This is identical distribution, not mutual independence.",
        r"\begin{definition}[DC-D2: cumulative-prefix empirical law and class-load factor]",
        r"\begin{theorem}[DC-1: dependency-colored empirical-law bound]",
        "This is a paper-derived specialization and composition, not a new concentration method.",
        "no additional factor of two is required.",
        r"\begin{definition}[DC-D3: one nested infinite sequence and its prefix loads]",
        r"\begin{theorem}[DC-2: Anytime law envelope for cumulative prefixes]",
        r"\begin{corollary}[DC-2a: fixed-width overlapping windows]",
        r"\begin{corollary}[DC-2b: strong $\ell$-dependence]",
        r"\begin{theorem}[DC-3: average-law concentration and explicit reference-law drift]",
        r"finite-poset M{\"o}bius inversion~\cite{rota1964}",
        r"\section{Counterexamples and invalidated routes}",
        r"\section{Formal and executable evidence boundary}",
    ),
    FINITE_TEX: (
        r"\subsection*{What problem this note solves}",
        "finite-poset M{\\\"o}bius\ninversion~\\cite{rota1964}",
        r"\begin{definition}[FA-D1: cumulative-prefix empirical law]",
        (
            "The label FA-D1 and the phrase ``cumulative-prefix empirical law'' are "
            "local to this document."
        ),
        r"\begin{theorem}[FA-1: Deterministic plug-in implication]",
        r"\begin{corollary}[FA-2: i.i.d.\ or stationary ergodic sampling]",
        r"\begin{theorem}[FA-3: time-uniform i.i.d.\ cumulative-prefix envelope]",
        (
            "The\nlabeled composition is project documentation; no mathematical priority "
            "or scientific-novelty\nclaim is made."
        ),
        r"\section{Independent frozen transforms}",
        "Let $W_1,W_2,\\ldots$ be conditionally i.i.d.\\ given $\\mathcal G$",
        "The limit is generally not the same functional evaluated at the unconditional mixture",
        r"\section{Counterexamples and invalid stronger claims}",
        r"\section{Formal and executable evidence boundary}",
    ),
}


FORBIDDEN_TEXT: dict[Path, tuple[str, ...]] = {
    DEPENDENCY_MD: (
        "For the common-law theorem",
        "class-size proxy that is optimal within the declared",
    ),
    FINITE_MD: (
        "Its common-law theorem",
        "Let $Z_1,Z_2,\\ldots$ be observations. Let the prefix empirical law be",
    ),
    DEPENDENCY_TEX: ("class-size proxy that is optimal within the declared",),
    FINITE_TEX: (),
}


def load_text(root: Path, relative: Path) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise SemanticDriftError(f"cannot read {relative}: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SemanticDriftError(message)


def find_method(catalog: dict[str, Any], method_id: str) -> dict[str, Any]:
    for method in catalog.get("methods", []):
        if method.get("id") == method_id:
            return method
    raise SemanticDriftError(f"method catalog is missing {method_id}")


def reference_link(method: dict[str, Any], reference_id: str) -> dict[str, Any]:
    for link in method.get("reference_links", []):
        if link.get("reference_id") == reference_id:
            return link
    raise SemanticDriftError(
        f"{method.get('id')}: missing reference link {reference_id}"
    )


def check_catalog(root: Path) -> int:
    try:
        catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SemanticDriftError(f"cannot parse {CATALOG}: {error}") from error

    dependency = find_method(
        catalog, "validation.dependency-color-sxpid-concentration"
    )
    finite = find_method(catalog, "validation.finite-alphabet-plugin-convergence")

    require(
        dependency.get("definition_origin") == "project-defined",
        "dependency validation row must remain project-defined",
    )
    require(
        dependency.get("scientific_novelty_claim") == "none",
        "dependency validation row must retain no scientific novelty claim",
    )
    require(
        finite.get("definition_origin") == "project-defined",
        "finite convergence row must remain project-defined",
    )
    require(
        finite.get("scientific_novelty_claim") == "none",
        "finite convergence row must retain no scientific novelty claim",
    )

    dependency_provenance = " ".join(dependency.get("constraints", []))
    require(
        "is exactly Janson's cover-specific T^2" in dependency_provenance,
        "dependency catalog row must identify V_n as Janson's published T^2",
    )
    require(
        (
            "Neither V_n, the class-load optimization that yields it, nor that "
            "cover-specific exponent is new in pid-rs."
        )
        in dependency_provenance,
        (
            "dependency catalog row must forbid project-origin claims for Janson's "
            "factor and optimization"
        ),
    )
    require(
        "a common row law, and mutual independence" in dependency_provenance,
        "dependency catalog row must keep identical distribution separate from independence",
    )
    require(
        "w_a=1" in dependency_provenance
        and "c_a=n_{a,n}" in dependency_provenance
        and "Remark 3.3" in dependency_provenance,
        (
            "dependency catalog row must bind Janson's partition substitution and "
            "retained sharp factor"
        ),
    )
    require(
        "There is no PID measure called colored PID." in dependency_provenance,
        "dependency catalog row must not introduce a colored-PID estimand",
    )
    require(
        "Janson-to-Weissman-to-SxPID composition"
        in dependency.get("new_in_pid_rs", ""),
        "dependency catalog row must identify the repository-stated composition",
    )
    finite_constraints = " ".join(finite.get("constraints", []))
    require(
        "not an invoked literature theorem" in finite_constraints,
        "finite catalog row must identify FA-D1 as a local definition",
    )
    require(
        "not a new concentration inequality" in finite_constraints
        and "not a confidence sequence for Rust output" in finite_constraints
        and "not a dependence theorem" in finite_constraints,
        "finite catalog row must retain the FA-3 nonclaims",
    )
    require(
        "not claim as new, classical finite-poset Mobius inversion"
        in finite.get("new_in_pid_rs", ""),
        "finite convergence row must not claim classical Mobius inversion as new",
    )

    janson = reference_link(dependency, "janson-2004")
    require(
        "Theorem 2.1" in janson.get("locator", "")
        and "Equations (3.1)-(3.3)" in janson.get("locator", "")
        and "T^2=V_n" in janson.get("locator", ""),
        "Janson locator must bind the exact theorem, equations, and specialization",
    )
    hoeffding = reference_link(dependency, "hoeffding-1963")
    require(
        "Equation (4.16)" in hoeffding.get("locator", ""),
        "Hoeffding locator must bind the exact moment-bound equation",
    )
    pelekis = reference_link(dependency, "pelekis-ramon-wang-2017")
    require(
        "later supporting" in pelekis.get("locator", "")
        and "not the source" in pelekis.get("locator", ""),
        "Pelekis locator must remain a later supporting route, not V_n provenance",
    )
    weissman = reference_link(dependency, "weissman-2003")
    require(
        "Equations (14)-(16)" in weissman.get("locator", "")
        and "2^K-2" in weissman.get("locator", ""),
        "Weissman locator must bind the exact subset equations and union factor",
    )
    reference_link(dependency, "rota-1964")
    reference_link(finite, "rota-1964")
    finite_hoeffding = reference_link(finite, "hoeffding-1963")
    require(
        "published two-sided bounded-coordinate concentration"
        in finite_hoeffding.get("locator", "")
        and "repository's spending-sequence" in finite_hoeffding.get("locator", ""),
        "finite Hoeffding locator must separate the published bound from FA-3 composition",
    )

    rota = next(
        (
            reference
            for reference in catalog.get("references", [])
            if reference.get("id") == "rota-1964"
        ),
        None,
    )
    require(isinstance(rota, dict), "reference registry is missing rota-1964")
    require(
        rota.get("doi") == "10.1007/BF00531932",
        "Rota reference DOI drifted",
    )
    return 23


def check(root: Path) -> int:
    checked = 0
    for relative, required_fragments in REQUIRED_TEXT.items():
        text = load_text(root, relative)
        for fragment in required_fragments:
            require(
                fragment in text,
                f"{relative}: required semantic anchor is absent: {fragment!r}",
            )
            checked += 1
        for fragment in FORBIDDEN_TEXT[relative]:
            require(
                fragment not in text,
                f"{relative}: obsolete or misleading wording is present: {fragment!r}",
            )
            checked += 1
    return checked + check_catalog(root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (used by isolated mutation tests)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        checked = check(args.root.resolve())
    except SemanticDriftError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "OK: "
        f"{checked} finite-convergence document provenance, theorem-name, assumption, "
        "and evidence-boundary anchors are coherent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
