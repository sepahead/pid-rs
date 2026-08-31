#!/usr/bin/env python3
"""Hostile mutation tests for the mathematical-results-guide prose checker."""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-mathematical-results-guide-prose.py"
SOURCE_PATH = ROOT / "MATHEMATICAL_RESULTS_GUIDE.md"


def load_checker():
    spec = importlib.util.spec_from_file_location("mathematical_results_prose_check", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("self-test failed: cannot load prose checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()


def append_block(text: str, block: str) -> str:
    return text.rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n"


def expect_pass(name: str, text: str, expected_census=None) -> None:
    try:
        CHECKER.audit_text(text, expected_census)
    except CHECKER.ProseCheckError as error:
        raise SystemExit(
            f"self-test failed: {name} unexpectedly failed [{error.code}]: {error}"
        ) from error


def expect_fail(name: str, text: str, code: str, expected_census=None) -> None:
    try:
        CHECKER.audit_text(text, expected_census)
    except CHECKER.ProseCheckError as error:
        if error.code != code:
            raise SystemExit(
                f"self-test failed: {name} produced [{error.code}], expected [{code}]"
            ) from error
        return
    raise SystemExit(f"self-test failed: {name} unexpectedly passed")


def main() -> int:
    if not SOURCE_PATH.is_file() or SOURCE_PATH.is_symlink():
        raise SystemExit("self-test failed: canonical guide is absent, non-regular, or symbolic")
    source = CHECKER.decode_source(SOURCE_PATH.read_bytes())
    cases = 0

    expect_pass("canonical baseline", source, CHECKER.EXPECTED_CENSUS)
    cases += 1

    semantic_mutations = (
        (
            "conditional lemma provenance class invented",
            "repository-derived conditional lemma, catalogued as\nproject-defined **[R]**",
            "project-derived conditional lemma **[R]**",
        ),
        (
            "contribution provenance class invented",
            "repository-derived\ncontribution, catalogued as project-defined",
            "project-derived contribution",
        ),
        (
            "Ehrlich manifold lemma falsely attributed",
            "but they do not prove this manifold small-ball lemma.",
            "and they prove this manifold small-ball lemma.",
        ),
        (
            "manifold-only implementation gap widened",
            "Manifold estimator and manifold PID implementation remain open **[O]**",
            "Estimator and PID remain open **[O]**",
        ),
        (
            "boundary counterexample promoted to sharpness",
            "boundary counterexamples **[X]**",
            "sharpness counterexamples **[X]**",
        ),
        (
            "smooth-marginal insufficiency promoted to necessity",
            "Why the displayed smooth marginals do not suffice.",
            "Why the pair-marginal premise is necessary.",
        ),
        (
            "pair-overlap premise deletion",
            "A version of $f_{S_1,S_2}$ is essentially bounded on a neighbourhood of $(s_1,s_2)$.",
            "A version of $f_{S_1,S_2}$ is finite at $(s_1,s_2)$.",
        ),
        (
            "triple-overlap premise deletion",
            "A version of $f_{T,S_1,S_2}$ is essentially bounded on a neighbourhood of $(t,s_1,s_2)$.",
            "A version of $f_{T,S_1,S_2}$ is finite at $(t,s_1,s_2)$.",
        ),
        (
            "positivity weakened to nonnegativity",
            "$f_T(t)$ and both density sums in the following ratio are strictly positive.",
            "$f_T(t)$ and both density sums in the following ratio are nonnegative.",
        ),
        (
            "no-estimator boundary inverted",
            "functional, an estimator, or a scientific-priority claim.",
            "functional and an estimator.",
        ),
        (
            "boundedness promoted to necessity",
            "a convenient sufficient condition, not a necessary one.",
            "a necessary and sufficient condition.",
        ),
        (
            "discarded overlap order weakened",
            "The discarded overlap terms are $O(r^{2d})$ and",
            "The discarded overlap terms are $O(r^d)$ and",
        ),
        (
            "Clayton provenance conflated",
            "reparameterization of\nClayton's 1978 survival-association model:",
            "Clayton's original theta parameterization:",
        ),
        (
            "Clayton survival semantics imported",
            "ordinary\ncopula, with no survival-time semantics.",
            "survival-time copula.",
        ),
        (
            "Clayton density exponent changed",
            r"(u^{-\theta}+v^{-\theta}-1)^{-2-1/\theta}",
            r"(u^{-\theta}+v^{-\theta}-1)^{-1-1/\theta}",
        ),
        (
            "Clayton normalization deleted",
            r"=1-2\varepsilon+C_\theta(\varepsilon,\varepsilon)\longrightarrow1.",
            r"\longrightarrow0.",
        ),
        (
            "signed mixture weight changed",
            r"\frac{1-\alpha}{4}g_1(t)c_\theta(|x|,|y|)",
            r"\frac{\alpha}{4}g_1(t)c_\theta(|x|,|y|)",
        ),
        (
            "source-pair support indicator deleted",
            "f_{S_1,S_2}(x,y)\n"
            r" &=\tfrac{\alpha}{4}\mathbf 1_{\{|x|,|y|<1\}}",
            "f_{S_1,S_2}(x,y)\n" r" &=\tfrac{\alpha}{4}",
        ),
        (
            "essential-unboundedness inference deleted",
            "persists on positive-measure open sets in every neighbourhood.",
            "occurs only on the diagonal.",
        ),
        (
            "source-pair singularity hidden",
            r"2^{-2-1/\theta}r^{-1}",
            r"2^{-2-1/\theta}r",
        ),
        (
            "Clayton first-order overlap weakened",
            r"C_\theta(r,r)\sim\lambda r,\quad \lambda=2^{-1/\theta}>0.",
            r"C_\theta(r,r)=o(r).",
        ),
        (
            "unequal-dimension boundary erased",
            "both\nbranch-one coefficients are positive, branch one dominates.",
            "branch one always dominates.",
        ),
        (
            "vanishing-coefficient rate invented",
            "continuity alone does not determine which branch dominates or its replacement rate.",
            "continuity fixes which branch dominates and its replacement rate.",
        ),
        (
            "gauge overlap premise deleted",
            "$\\Pr(E_{1,r}\\cap E_{2,r})=o(a(r))$ and\n$\\Pr(C_r\\cap E_{1,r}\\cap E_{2,r})=o(w_r a(r))$.",
            "$\\Pr(E_{1,r}\\cap E_{2,r})=O(a(r))$.",
        ),
        (
            "pair-boundedness falsely declared necessary",
            "The example does not prove that pair local boundedness is necessary.",
            "The example proves that pair local boundedness is necessary.",
        ),
        (
            "PID nontransfer promoted",
            "global expectation interchange, PID-atom property, mixed-support result, or software refinement.",
            "global expectation interchange and every PID-atom property.",
        ),
    )
    for name, anchor, replacement in semantic_mutations:
        mutated = source.replace(anchor, replacement, 1)
        if mutated == source:
            raise SystemExit(f"self-test failed: {name} anchor was not found")
        expect_fail(name, mutated, "semantic_contract")
        cases += 1

    long_sentence = " ".join(f"word{i}" for i in range(1, 27)) + "."
    expect_fail(
        "26-word direct sentence",
        append_block(source, long_sentence),
        "word_limit",
    )
    cases += 1
    expect_fail(
        "seven-sentence paragraph",
        append_block(source, "One. Two. Three. Four. Five. Six. Seven."),
        "paragraph_limit",
    )
    cases += 1
    expect_fail(
        "26-word list sentence",
        append_block(source, "- " + long_sentence),
        "word_limit",
    )
    cases += 1

    for name, block in (
        ("direct semicolon", "Visible prose has one clause; it has another clause."),
        ("list semicolon", "- A visible list item has a semicolon; it must fail."),
        ("table semicolon", "| A | B |\n|---|---|\n| visible; text | control |"),
        ("heading semicolon", "## Visible; heading"),
        ("blockquote semicolon", "> Visible prose; in a callout."),
        ("image-alt semicolon", "![Visible; alternative text](figure.svg)"),
    ):
        expect_fail(name, append_block(source, block), "semicolon")
        cases += 1

    url_semicolon = source.replace(
        "https://doi.org/10.1103/PhysRevE.103.032149",
        "https://doi.org/10.1103/PhysRevE.103.032149?a=1;b=2",
        1,
    )
    expect_pass("semicolon in URL destination", url_semicolon)
    cases += 1
    expect_pass(
        "semicolon in inline code and math",
        append_block(source, "The tokens `a;b` and $c;d$ are synthetic."),
    )
    cases += 1
    expect_pass(
        "semicolon in display math",
        append_block(source, "$$\na;b\n$$"),
    )
    cases += 1
    expect_pass(
        "semicolon in fenced code",
        append_block(source, "```text\na;b\n```"),
    )
    cases += 1
    expect_pass(
        "long heading is not prose",
        append_block(source, "## " + " ".join(f"word{i}" for i in range(1, 31))),
    )
    cases += 1
    expect_pass(
        "long table cell is not a paragraph",
        append_block(
            source,
            "| A | B |\n|---|---|\n| "
            + " ".join(f"word{i}" for i in range(1, 31))
            + " | control |",
        ),
    )
    cases += 1
    expect_pass(
        "known dotted forms",
        append_block(source, "The i.i.d. rows use the result of Ehrlich et al. correctly."),
    )
    cases += 1

    expect_fail("unclosed display math", append_block(source, "$$\na+b"), "structure")
    cases += 1
    expect_fail("unclosed fence", append_block(source, "```text\na+b"), "structure")
    cases += 1
    expect_fail(
        "unbalanced inline code",
        append_block(source, "The `token is unbalanced."),
        "inline",
    )
    cases += 1
    expect_fail(
        "unbalanced inline math",
        append_block(source, "The $token is unbalanced."),
        "inline",
    )
    cases += 1
    expect_fail(
        "orphan indentation",
        append_block(source, "    Hidden prose is unsupported."),
        "structure",
    )
    cases += 1
    expect_fail(
        "malformed table",
        append_block(source, "| A | B |\n|--|--|\n| x | y |"),
        "structure",
    )
    cases += 1
    expect_fail(
        "raw HTML",
        append_block(source, "The <em>token</em> is unsupported."),
        "inline",
    )
    cases += 1
    expect_fail(
        "unknown dotted token",
        append_block(source, "The abc.def token is ambiguous."),
        "inline",
    )
    cases += 1
    expect_fail(
        "checked-surface census drift",
        append_block(source, "## Additional heading"),
        "census",
        CHECKER.EXPECTED_CENSUS,
    )
    cases += 1

    reflowed = source.replace(
        "This guide gives a self-contained map of the principal mathematical results and assurance work in\n"
        "pid-rs. Each result card identifies the mathematical object and its assumptions. Each card also\n"
        "gives the central formula, evidence, cost, use, strongest nonclaim, and complete proof or\n"
        "publication artifact.",
        "This guide gives a self-contained map of the principal mathematical results and assurance work in pid-rs. "
        "Each result card identifies the mathematical object and its assumptions. Each card also gives the central "
        "formula, evidence, cost, use, strongest nonclaim, and complete proof or publication artifact.",
        1,
    )
    if reflowed == source:
        raise SystemExit("self-test failed: line-reflow fixture anchor was not found")
    expect_pass("line-reflow invariance", reflowed, CHECKER.EXPECTED_CENSUS)
    cases += 1

    hidden_h1_prose = source.replace(
        "# Mathematical results guide\n\n",
        "# Mathematical results guide\n" + long_sentence + "\n\n",
        1,
    )
    if hidden_h1_prose == source:
        raise SystemExit("self-test failed: H1 fixture anchor was not found")
    expect_fail(
        "H1 continuation with census-preserving hidden prose",
        hidden_h1_prose,
        "structure",
        CHECKER.EXPECTED_CENSUS,
    )
    cases += 1

    first_list_item = "- A target-permutation affine-reflection theorem."
    hidden_lazy_list_prose = source.replace(
        first_list_item,
        first_list_item + "\n" + long_sentence,
        1,
    )
    if hidden_lazy_list_prose == source:
        raise SystemExit("self-test failed: lazy-list fixture anchor was not found")
    expect_fail(
        "lazy-list continuation with census-preserving hidden prose",
        hidden_lazy_list_prose,
        "structure",
        CHECKER.EXPECTED_CENSUS,
    )
    cases += 1

    expect_pass(
        "indented loose-list continuation",
        append_block(
            source,
            "- The list item starts here.\n\n"
            "  The indented loose continuation remains part of that item.",
        ),
    )
    cases += 1
    expect_fail(
        "long indented loose-list continuation remains checked",
        append_block(source, "- The list item starts here.\n\n  " + long_sentence),
        "word_limit",
    )
    cases += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-mathematical-results-guide-prose-self-test."
    ) as temporary_directory:
        symlink_source = pathlib.Path(temporary_directory) / "optional-input.md"
        symlink_source.symlink_to(SOURCE_PATH)
        for label, optimization_flag in (("normal", []), ("optimized", ["-O"])):
            completed = subprocess.run(
                [
                    sys.executable,
                    *optimization_flag,
                    str(CHECKER_PATH),
                    str(symlink_source),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 1 or "[input]" not in completed.stderr:
                raise SystemExit(
                    "self-test failed: optional-input symlink was not rejected "
                    f"in {label} mode: rc={completed.returncode}, "
                    f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
                )
            cases += 1

    if "not ASD-STE100" not in CHECKER.BOUNDARY:
        raise SystemExit("self-test failed: non-conformance boundary is absent")
    print(
        f"Mathematical results guide prose self-test passed: {cases} hostile/control cases."
    )
    print(f"Boundary: {CHECKER.BOUNDARY}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
