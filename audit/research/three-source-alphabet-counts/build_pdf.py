"""Build a finite study from its Markdown and repository-local publication design."""
import argparse
import datetime as dt
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TITLE = "three-source-alphabet-counts"
STYLE = ROOT / "audit/formal/latex"


def build(output, *, study_root=HERE, stem=TITLE):
    source = study_root / "README.md"
    profile = study_root / "print"
    epoch = int(dt.datetime(2026, 11, 19, tzinfo=dt.timezone.utc).timestamp())
    env = dict(os.environ, TZ="UTC", LC_ALL="C", SOURCE_DATE_EPOCH=str(epoch),
               FORCE_SOURCE_DATE="1", TEXINPUTS=str(STYLE) + os.pathsep)
    with tempfile.TemporaryDirectory(prefix=stem + "-") as directory:
        work = Path(directory)
        shutil.copyfile(profile / "publication.tex", work / "publication.tex")
        subprocess.run(["pandoc", str(source), "--from=markdown", "--to=latex", "--syntax-highlighting=none",
                        "--lua-filter", str(profile / "publication.lua"), "--output", "body.tex"],
                       cwd=work, env=env, check=True, timeout=60)
        for _ in range(2):
            result = subprocess.run(["lualatex", "--no-shell-escape", "--interaction=nonstopmode",
                                     "--halt-on-error", "--file-line-error", "publication.tex"],
                                    cwd=work, env=env, capture_output=True, timeout=120)
            if result.returncode:
                raise RuntimeError(result.stdout.decode(errors="replace")[-4500:])
        log = (work / "publication.log").read_text(errors="replace")
        problems = [line for line in log.splitlines() if "Overfull " in line or "Missing character:" in line]
        if problems:
            raise ValueError("\n".join(problems))
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as final:
            staged = Path(final.name)
        try:
            shutil.copyfile(work / "publication.pdf", staged)
            staged.chmod(0o644)
            os.replace(staged, output)
        finally:
            staged.unlink(missing_ok=True)


def verify(pdf, *, title="Weighted event counts for three categorical sources", pages=6):
    def inspect(*args):
        return subprocess.check_output([*args, str(pdf)], text=True, timeout=30)

    info = inspect("pdfinfo")
    fields = dict(line.split(":", 1) for line in info.splitlines() if ":" in line)
    if (fields["Author"].strip() != "Sepehr Mahmoudian"
            or fields["Title"].strip() != title
            or fields["Pages"].strip() != str(pages) or "A4" not in fields["Page size"]
            or fields["PDF version"].strip() != "1.7"):
        raise ValueError("PDF metadata or expected A4 page profile differs")
    fonts = inspect("pdffonts").splitlines()[2:]
    if not fonts or any(line.split()[-5] != "yes" or line.split()[-3] != "yes" for line in fonts):
        raise ValueError("PDF requires embedded fonts with Unicode mappings")
    urls = inspect("pdfinfo", "-url").splitlines()[1:]
    if not urls or any(not re.search(r"\shttps://", line) for line in urls):
        raise ValueError("PDF contains an unexpected external link action")


def command_line(study_root, stem, title, pages):
    committed_pdf = ROOT / "output/pdf" / (stem + ".pdf")
    parser = argparse.ArgumentParser(description="Build and check " + title)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--output", type=Path, help="build to this destination")
    mode.add_argument("--check", action="store_true", help="verify a fresh build against the shipped PDF")
    mode.add_argument("--check-committed", action="store_true", help="inspect the shipped PDF on another toolchain without a typesetting claim")
    args = parser.parse_args()
    if args.check_committed:
        verify(committed_pdf, title=title, pages=pages)
    elif args.check:
        with tempfile.TemporaryDirectory(prefix=stem + "-check-") as directory:
            check_pdf = Path(directory) / committed_pdf.name
            build(check_pdf, study_root=study_root, stem=stem)
            verify(check_pdf, title=title, pages=pages)
            if check_pdf.read_bytes() != committed_pdf.read_bytes():
                raise ValueError("fresh PDF differs from the shipped artifact")
    else:
        output = (args.output or committed_pdf).resolve()
        build(output, study_root=study_root, stem=stem)
        verify(output, title=title, pages=pages)


if __name__ == "__main__":
    command_line(HERE, TITLE, "Weighted event counts for three categorical sources", 6)
