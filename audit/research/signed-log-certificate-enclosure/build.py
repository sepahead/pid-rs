"""Build the native report in a temporary directory. Requires Pandoc and LuaLaTeX."""

import argparse
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile


STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[2]
TEX_PATH = Path("audit/formal/latex/signed-log-certificate-enclosure")
LATEX = Path("audit/formal/latex")
ENV = dict(
    os.environ,
    SOURCE_DATE_EPOCH="1795564800",
    TZ="UTC",
    LC_ALL="C",
    max_print_line="800",
)


def latex_body():
    """Use local links in Markdown and public HTTPS destinations in the PDF."""
    source = (
        (STUDY / "EXPOSITION.md")
        .read_text(encoding="utf-8")
        .split("<!-- body -->\n", 1)[1]
    )
    image_line = re.findall(
        r"^!\[.*?\]\(figures/intervals\.svg\)$", source, re.MULTILINE
    )
    if len(image_line) != 1:
        raise ValueError("expected one logarithm figure")
    figure = r"\par\smallskip\noindent\makebox[\linewidth][c]{\includegraphics[width=0.94\linewidth]{intervals.pdf}}\par"
    source = source.replace(image_line[0], figure)

    fragments = []
    for page in source.split("<!-- page -->"):
        result = subprocess.run(
            [
                "pandoc",
                "--from=markdown-implicit_figures-smart+raw_tex+tex_math_dollars",
                "--to=latex",
                "--shift-heading-level-by=-1",
                "--wrap=none",
                "--lua-filter=" + str(STUDY / "links.lua"),
            ],
            input=page.strip(),
            capture_output=True,
            text=True,
            check=True,
            env=ENV,
        ).stdout
        for match in re.finditer(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", result, re.DOTALL):
            formula = match.group(1) if match.group(1) is not None else match.group(2)
            if "https://" in formula or "http://" in formula or r"\href" in formula:
                raise ValueError("unexpected URL inside a printed formula")
        fragments.append(result.rstrip())
    return ("\n\n\\clearpage\n\n".join(fragments) + "\n").encode()


def build(output, assets):
    tex = ROOT / TEX_PATH
    body = latex_body()
    if body != (tex / "body.tex").read_bytes():
        raise ValueError("native body differs from the Markdown rendering")
    with tempfile.TemporaryDirectory(prefix="signed-log-report-") as temp:
        work = Path(temp)
        for name in ("publication.tex", "body.tex"):
            shutil.copyfile(tex / name, work / name)
        for name in ("pid-rs-workflow-publication.sty", "pid-rs-report-tables.sty"):
            shutil.copyfile(assets / LATEX / name, work / name)
        shutil.copytree(
            assets / LATEX / "source-coupling-compression/fonts", work / "fonts"
        )
        shutil.copyfile(
            STUDY / "figures/intervals.pdf", work / "intervals.pdf"
        )
        before = None
        for run in range(3):
            proc = subprocess.run(
                [
                    "lualatex",
                    "-no-shell-escape",
                    "-halt-on-error",
                    "-interaction=nonstopmode",
                    "-file-line-error",
                    "-recorder",
                    "publication.tex",
                ],
                cwd=work,
                capture_output=True,
                env=ENV,
            )
            if proc.returncode:
                raise RuntimeError(proc.stdout.decode(errors="replace")[-5000:])
            pdf = (work / "publication.pdf").read_bytes()
            if run == 2 and pdf != before:
                raise ValueError("last two PDF passes differ")
            before = pdf
        log = (work / "publication.log").read_text(errors="replace")
        problems = [
            line
            for line in log.splitlines()
            if any(
                flag in line
                for flag in (
                    "Overfull",
                    "Missing character:",
                    "undefined references",
                    "multiply-defined",
                )
            )
        ]
        if problems:
            raise ValueError("\n".join(problems))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pdf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write the standalone report here")
    parser.add_argument(
        "--write-body",
        action="store_true",
        help="regenerate the tracked native body from Markdown",
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=ROOT,
        help="repository containing the shared styles and fonts",
    )
    args = parser.parse_args()
    if args.write_body:
        (ROOT / TEX_PATH / "body.tex").write_bytes(latex_body())
    if args.output:
        build(args.output.resolve(), args.assets_root.resolve())
    if not args.write_body and not args.output:
        parser.error("supply --output or --write-body")


if __name__ == "__main__":
    main()
