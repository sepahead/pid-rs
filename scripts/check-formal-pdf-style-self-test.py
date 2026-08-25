#!/usr/bin/env python3
"""Mutation-test the formal-PDF visual-system checker."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-formal-pdf-style.py"
LATEX_RELATIVE = Path("audit/formal/latex")


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def mutate(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if before not in text:
        raise RuntimeError(f"mutation anchor is absent from {path}: {before!r}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def require_failure(
    pristine: Path,
    name: str,
    relative: Path,
    before: str,
    after: str,
    expected: str,
) -> None:
    fixture = pristine.parent / name
    shutil.copytree(pristine, fixture)
    mutate(fixture / relative, before, after)
    result = run(fixture)
    if result.returncode == 0 or expected not in result.stderr:
        raise RuntimeError(
            f"mutation {name!r} did not fail closed for {expected!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-pdf-style-self-test.") as raw:
        base = Path(raw)
        pristine = base / "pristine"
        (pristine / LATEX_RELATIVE.parent).mkdir(parents=True)
        shutil.copytree(ROOT / LATEX_RELATIVE, pristine / LATEX_RELATIVE)

        baseline = run(pristine)
        if baseline.returncode != 0:
            raise RuntimeError(
                f"baseline visual-system fixture failed\n{baseline.stdout}\n{baseline.stderr}"
            )

        finite = LATEX_RELATIVE / "finite-alphabet-plugin-convergence.tex"
        workflow = LATEX_RELATIVE / "mathematical-problem-solving-workflow.tex"
        style = LATEX_RELATIVE / "pid-rs-report-tables.sty"
        require_failure(
            pristine,
            "missing-header-band",
            finite,
            "\\toprule\n\\PidTableHeaderRow",
            "\\toprule\n",
            "must be followed immediately",
        )
        require_failure(
            pristine,
            "duplicate-header-band",
            finite,
            "\\toprule\n\\PidTableHeaderRow",
            "\\toprule\n\\PidTableHeaderRow\n\\PidTableHeaderRow",
            "duplicate adjacent table-header band",
        )
        require_failure(
            pristine,
            "toprule-redefinition",
            finite,
            "\\begin{document}",
            "\\renewcommand{\\toprule}{}\n\\begin{document}",
            "must not redefine",
        )
        require_failure(
            pristine,
            "missing-markdown-hook",
            workflow,
            "\\def\\markdownLaTeXTopRule{\\toprule\\PidTableHeaderRow}%",
            "\\def\\markdownLaTeXTopRule{\\toprule}%",
            "Markdown-generated table-header hook",
        )
        require_failure(
            pristine,
            "vertical-rule",
            finite,
            "\\midrule",
            "\\hline",
            "vertical/legacy table rule",
        )
        require_failure(
            pristine,
            "palette-drift",
            style,
            "\\definecolor{PidTableStripe}{HTML}{E5EDF2}",
            "\\definecolor{PidTableStripe}{HTML}{FFFFFF}",
            "required style marker",
        )

        fragment = (
            LATEX_RELATIVE
            / "pid-discovery-verification-and-durability-blueprint-header.tex"
        )

        missing_fragment = base / "missing-renderer-fragment"
        shutil.copytree(pristine, missing_fragment)
        (missing_fragment / fragment).unlink()
        missing_result = run(missing_fragment)
        if (
            missing_result.returncode == 0
            or "formal LaTeX inventory differs" not in missing_result.stderr
        ):
            raise RuntimeError(
                "missing renderer fragment did not fail closed\n"
                f"stdout:\n{missing_result.stdout}\nstderr:\n{missing_result.stderr}"
            )

        unexpected_source = base / "unexpected-tex-source"
        shutil.copytree(pristine, unexpected_source)
        (unexpected_source / LATEX_RELATIVE / "unexpected-helper.tex").write_text(
            "% hostile extra source\n", encoding="utf-8"
        )
        unexpected_result = run(unexpected_source)
        if (
            unexpected_result.returncode == 0
            or "formal LaTeX inventory differs" not in unexpected_result.stderr
        ):
            raise RuntimeError(
                "unexpected TeX source did not fail closed\n"
                f"stdout:\n{unexpected_result.stdout}\nstderr:\n{unexpected_result.stderr}"
            )

        require_failure(
            pristine,
            "standalone-fragment-conflation",
            fragment,
            "\\usepackage{xcolor}",
            "\\documentclass{article}\n\\usepackage{xcolor}",
            "renderer fragment must not become a standalone document",
        )
        require_failure(
            pristine,
            "missing-fragment-role-marker",
            fragment,
            "\\makeatletter",
            "% removed make-at-letter role marker",
            "renderer-fragment marker must occur once",
        )

        symbolic_fragment = base / "symbolic-renderer-fragment"
        shutil.copytree(pristine, symbolic_fragment)
        fragment_path = symbolic_fragment / fragment
        target = symbolic_fragment / "fragment-target.tex"
        fragment_path.rename(target)
        fragment_path.symlink_to(target)
        symbolic_result = run(symbolic_fragment)
        if (
            symbolic_result.returncode == 0
            or "direct regular file" not in symbolic_result.stderr
        ):
            raise RuntimeError(
                "symbolic renderer fragment did not fail closed\n"
                f"stdout:\n{symbolic_result.stdout}\nstderr:\n{symbolic_result.stderr}"
            )

    print("OK: eleven formal-PDF visual-system and role mutations fail closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
