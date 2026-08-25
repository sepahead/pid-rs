#!/usr/bin/env python3
"""Prove that the finite-convergence semantic drift checker fails closed."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-finite-convergence-document-semantics.py"
FILES = (
    Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md"),
    Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md"),
    Path("audit/formal/latex/dependency-colored-sxpid-concentration.tex"),
    Path("audit/formal/latex/finite-alphabet-plugin-convergence.tex"),
    Path("method-catalog.json"),
)


class SelfTestError(RuntimeError):
    """The checker accepted a registered semantic mutation or rejected baseline."""


def copy_fixture(destination: Path) -> None:
    for relative in FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-S", str(CHECKER), "--root", str(root)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def replace_once(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise SelfTestError(
            f"mutation anchor must occur exactly once in {path}: {before!r}"
        )
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def mutate_catalog(path: Path, mutation: str) -> None:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    methods = {method["id"]: method for method in catalog["methods"]}
    dependency = methods["validation.dependency-color-sxpid-concentration"]
    finite = methods["validation.finite-alphabet-plugin-convergence"]
    if mutation == "origin":
        dependency["definition_origin"] = "paper-derived"
    elif mutation == "novelty":
        dependency["scientific_novelty_claim"] = "new-mathematical-result"
    elif mutation == "janson-locator":
        next(
            link
            for link in dependency["reference_links"]
            if link["reference_id"] == "janson-2004"
        )["locator"] = "partly dependent sums"
    elif mutation == "finite-rota-link":
        finite["reference_links"] = [
            link
            for link in finite["reference_links"]
            if link["reference_id"] != "rota-1964"
        ]
    elif mutation == "finite-hoeffding-locator":
        next(
            link
            for link in finite["reference_links"]
            if link["reference_id"] == "hoeffding-1963"
        )["locator"] = "new project-defined time-uniform concentration theorem"
    elif mutation == "rota-doi":
        next(
            reference
            for reference in catalog["references"]
            if reference["id"] == "rota-1964"
        )["doi"] = "10.1007/incorrect"
    else:
        raise SelfTestError(f"unknown catalog mutation: {mutation}")
    path.write_text(
        json.dumps(catalog, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    mutations = (
        (
            "dependency-janson-origin",
            Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md"),
            "The quantity called $V_n$ below is **not new mathematics from pid-rs**.",
            "The quantity called $V_n$ below is new mathematics from pid-rs.",
        ),
        (
            "dependency-common-law-conflation",
            Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md"),
            (
                "This says that the rows are **identically distributed**. It does not "
                "say they are mutually\nindependent."
            ),
            "This says that the rows are mutually independent.",
        ),
        (
            "dependency-extra-tail-factor",
            Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md"),
            "There is no additional factor of two.",
            "Add another factor of two for the opposite sign.",
        ),
        (
            "dependency-obsolete-theorem-name",
            Path("DEPENDENCY_COLORED_SXPID_CONCENTRATION.md"),
            "## Result map",
            "For the common-law theorem\n\n## Result map",
        ),
        (
            "finite-transform-target",
            Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md"),
            "It is not generally the same as the quantity of the unconditional mixture.",
            "It equals the same quantity of the unconditional mixture.",
        ),
        (
            "finite-classical-provenance",
            Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md"),
            "not a construction introduced here; see Rota (1964).",
            "a construction introduced here.",
        ),
        (
            "dependency-tex-janson-origin",
            Path("audit/formal/latex/dependency-colored-sxpid-concentration.tex"),
            "The quantity denoted $V_n$ is not new mathematics from \\texttt{pid-rs}.",
            "The quantity denoted $V_n$ is new mathematics from \\texttt{pid-rs}.",
        ),
        (
            "dependency-tex-common-law-conflation",
            Path("audit/formal/latex/dependency-colored-sxpid-concentration.tex"),
            "This is identical distribution, not mutual independence.",
            "This premise is mutual independence.",
        ),
        (
            "dependency-tex-janson-locator",
            Path("audit/formal/latex/dependency-colored-sxpid-concentration.tex"),
            "cover-specific $T^2$ in the proof of Theorem~2.1, Equations~(3.1)--(3.3)",
            "project-defined class-size proxy",
        ),
        (
            "finite-prefix-name-origin",
            Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md"),
            (
                "The label FA-D1 and the phrase **cumulative-prefix empirical law** are "
                "definitions local to this"
            ),
            "The cumulative-prefix empirical law is a published theorem and is new here",
        ),
        (
            "finite-composition-priority",
            Path("FINITE_ALPHABET_PLUGIN_CONVERGENCE.md"),
            (
                "The labeled composition is project documentation; no mathematical "
                "priority or\nscientific-novelty claim is made."
            ),
            "The labeled composition is a new concentration inequality.",
        ),
        (
            "finite-tex-conditional-target",
            Path("audit/formal/latex/finite-alphabet-plugin-convergence.tex"),
            "The limit is generally not the same functional evaluated at the unconditional mixture",
            "The limit is the same functional evaluated at the unconditional mixture",
        ),
        (
            "finite-tex-prefix-name-origin",
            Path("audit/formal/latex/finite-alphabet-plugin-convergence.tex"),
            (
                "The label FA-D1 and the phrase ``cumulative-prefix empirical law'' are "
                "local to this document."
            ),
            "The cumulative-prefix empirical law is an invoked literature theorem.",
        ),
        (
            "finite-tex-composition-priority",
            Path("audit/formal/latex/finite-alphabet-plugin-convergence.tex"),
            (
                "labeled composition is project documentation; no mathematical priority "
                "or scientific-novelty\nclaim is made."
            ),
            "labeled composition is a new concentration inequality.",
        ),
    )
    catalog_mutations = (
        "origin",
        "novelty",
        "janson-locator",
        "finite-rota-link",
        "finite-hoeffding-locator",
        "rota-doi",
    )

    with tempfile.TemporaryDirectory(prefix="pid-rs-finite-doc-semantics-") as raw:
        temporary = Path(raw)
        baseline = temporary / "baseline"
        copy_fixture(baseline)
        process = run_checker(baseline)
        if process.returncode != 0:
            raise SelfTestError(
                "baseline semantic fixture failed\n"
                f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
            )

        killed = 0
        for name, relative, before, after in mutations:
            fixture = temporary / name
            copy_fixture(fixture)
            replace_once(fixture / relative, before, after)
            process = run_checker(fixture)
            if process.returncode == 0:
                raise SelfTestError(f"semantic mutation survived: {name}")
            killed += 1

        for mutation in catalog_mutations:
            fixture = temporary / f"catalog-{mutation}"
            copy_fixture(fixture)
            mutate_catalog(fixture / "method-catalog.json", mutation)
            process = run_checker(fixture)
            if process.returncode == 0:
                raise SelfTestError(f"catalog semantic mutation survived: {mutation}")
            killed += 1

    print(f"OK: {killed} finite-convergence semantic mutations fail closed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
