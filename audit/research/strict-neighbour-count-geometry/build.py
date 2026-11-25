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
TEX_PATH = Path("audit/formal/latex/strict-neighbour-count-geometry")
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
    from hashlib import sha256
    readme = (STUDY / "README.md").read_bytes()
    evidence = (STUDY / "EVIDENCE.md").read_bytes()
    expected = {
        "README.md": "14d7ea471bbe528405d87591737ac5a832193cac384c31a4f827b738fb351705",
        "figures/counts-and-distances.svg": "d819d348446f6d6e0994bac77d7b3e5a4694f934163a4e33f8f9316419818369",
        "figures/counts-and-distances.pdf": "c02d2465a4691e179f30598a68178a8d4f4a905d5743a3fbd301c62937997b34",
    }
    for name, digest in expected.items():
        if sha256((STUDY / name).read_bytes()).hexdigest() != digest:
            raise ValueError("wrong scientific publication input " + name)
    article = readme.decode()
    fields = re.split(r"(?m)^## (.+)\n\n", article)
    intro = fields[0].split("**Sepehr Mahmoudian · 25 November 2026**\n\n", 1)[1].strip()
    sections = dict(zip(fields[1::2], fields[2::2], strict=True))
    titles = list(sections)
    require_titles = [
        "Terms and quantities", "Exact range at one anchor", "When a random sample can give each pair",
        "Several rows on the shell", "Sharp local limits and the sample average",
        "The smallest sample with a negative mean", "A gap for an infinite family of sample sizes",
        "A worked test with two source channels", "Formal statement and finite checks",
        "Rust implementation and computational cost",
    ]
    if titles != require_titles:
        raise ValueError("unexpected scientific sections")

    def headed(title, content=None):
        body = sections[title] if content is None else content
        return "## " + title + "\n\n" + body.strip()

    def split_at(text, start):
        if text.count(start) != 1:
            raise ValueError("missing or repeated page anchor: " + start)
        before, after = text.split(start)
        return before.rstrip(), (start + after).rstrip()

    term_intro, scores = split_at(sections[titles[0]], r"Let $n\ge2$ be the number of rows")
    finite, open_sets = split_at(sections[titles[1]], "An **open set** here")
    local_bounds, sample_bounds = split_at(sections[titles[4]], "If every anchor obeys")
    runtime, citation = split_at(sections[titles[9]], "**Citation.**")
    proof_data = evidence.decode()
    header = "| Declaration | Predicate | Transitive axioms printed by Lean |"
    if proof_data.count(header) != 1:
        raise ValueError("missing or repeated five-theorem axiom table")
    axiom_table = header + proof_data.split(header, 1)[1].split("\n\n", 1)[0]
    if sha256(axiom_table.encode()).hexdigest() != "5f220fad3e26935fccb7f7d236165abe6fa8856cd1475804ac7f2ce4a4cc5229":
        raise ValueError("changed five-theorem axiom table")
    guide = (STUDY / "PUBLICATION.md").read_text(encoding="utf-8")
    instructions = guide.split("<!-- print supplement -->\n", 1)[1].split("<!-- end print supplement -->", 1)[0].strip()
    worked = guide.split("<!-- upper example -->\n", 1)[1].split("<!-- end upper example -->", 1)[0].strip()
    pages = [
        intro + "\n\n" + headed(titles[0], term_intro),
        scores + "\n\n" + headed(titles[1], finite),
        open_sets + "\n\n" + headed(titles[2]),
        headed(titles[3]) + "\n\n" + headed(titles[4], local_bounds),
        headed("When every row attains the upper bound", sample_bounds) + "\n\n" + worked,
        headed(titles[5]) + "\n\n" + headed(titles[6]),
        headed(titles[7]),
        headed(titles[8]) + "\n\n" + axiom_table,
        headed(titles[9], runtime),
        instructions + "\n\n" + citation,
    ]
    source = "\n\n<!-- page -->\n\n".join(pages)
    source = source.replace("The KSG comparator is the stable", "\n\nThe KSG comparator is the stable")
    image_line = re.findall(
        r"^!\[.*?\]\(figures/counts-and-distances\.svg\)$", source, re.MULTILINE
    )
    if len(image_line) != 1:
        raise ValueError("expected exactly one strict-count figure")
    figure = r"\par\smallskip\noindent\makebox[\linewidth][c]{\includegraphics[width=0.98\linewidth]{counts-and-distances.pdf}}\par"
    source = source.replace(image_line[0], figure)

    fragments = []
    for page in source.split("<!-- page -->"):
        result = subprocess.run(
            [
                "pandoc",
                "--from=markdown-implicit_figures-smart+raw_tex+tex_math_dollars",
                "--to=latex",
                "--syntax-highlighting=none",
                "--shift-heading-level-by=-1",
                "--wrap=none",
                "--lua-filter=" + str(STUDY / "link-ast.lua"),
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
    with tempfile.TemporaryDirectory(prefix="strict-count-report-") as temp:
        work = Path(temp)
        for name in ("publication.tex", "body.tex"):
            shutil.copyfile(tex / name, work / name)
        for name in ("pid-rs-workflow-publication.sty", "pid-rs-report-tables.sty"):
            shutil.copyfile(assets / LATEX / name, work / name)
        shutil.copytree(
            assets / LATEX / "source-coupling-compression/fonts", work / "fonts"
        )
        shutil.copyfile(
            STUDY / "figures/counts-and-distances.pdf", work / "counts-and-distances.pdf"
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
        problems = []
        lines = log.splitlines()
        flags = ("Overfull", "Missing character:", "undefined references", "multiply-defined")
        for i, line in enumerate(lines):
            if any(flag in line for flag in flags):
                problems.append("\n".join(lines[i:i+4]))
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
