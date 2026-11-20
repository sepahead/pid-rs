"""Build the worked A4 reader or inspect the shipped artifact under its registered checks."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STEM = "two-source-synergy-bound-example"
TITLE = "How the support count changes a synergy bound"
SHARED = Path("audit/research/three-source-alphabet-counts/build_pdf.py")
STYLES = Path("audit/formal/latex")
LEAF = Path("audit/research") / STEM
SOURCE_FILES = [
    *(LEAF / name for name in ("README.md", "counts.json", "example.py", "verify_numbers.py",
                                "publication.lua", "publication.tex", "support-bounds.svg", "build_pdf.py")),
    SHARED, STYLES / "pid-rs-report-tables.sty", STYLES / "pid-rs-workflow-publication.sty",
]

def sha(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected a direct regular file: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()

def profile(repo):
    record = json.loads((HERE / "publication.json").read_text(encoding="utf-8"))
    if record["schema"] != 1:
        raise ValueError("unexpected publication profile")
    sources = {str(p): sha(repo / p) for p in SOURCE_FILES}
    if sources != record["source_sha256"]:
        raise ValueError("publication source roster or digest changed")
    return record

def verify(pdf, repo):
    shared_spec = importlib.util.spec_from_file_location("finite_study_publication", repo / SHARED)
    shared = importlib.util.module_from_spec(shared_spec)
    shared_spec.loader.exec_module(shared)
    shared.verify(pdf, title=TITLE, pages=3)
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True, timeout=30)
    flat = " ".join(text.split())
    for phrase in ("Figure 1.", "3.968825682", "4.346307242", "4.648109919",
                   "rounded to three decimal places", "--check", "--write", "--output",
                   "Conditions for each calculation", "Rust implementation and computational cost"):
        if phrase not in flat:
            raise ValueError("missing publication text: " + phrase)
    urls = set(re.findall(r"https://\S+", subprocess.check_output(["pdfinfo", "-url", str(pdf)],
                                                                 text=True, timeout=30)))
    return urls

def publish(source, dest):
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as out:
        temp = Path(out.name)
    try:
        shutil.copyfile(source, temp)
        temp.chmod(0o644)
        os.replace(temp, dest)
    finally:
        temp.unlink(missing_ok=True)

def build(output, repo, figure=None):
    styles = repo / STYLES
    env = dict(os.environ, SOURCE_DATE_EPOCH="1795132800", FORCE_SOURCE_DATE="1", TZ="UTC",
               LC_ALL="C", TEXINPUTS=str(styles) + os.pathsep)
    with tempfile.TemporaryDirectory(prefix=STEM + "-") as directory:
        work = Path(directory)
        def run(args, timeout):
            subprocess.run(args, cwd=work, env=env, check=True, timeout=timeout)
        run([sys.executable, "-I", "-S", "-B", str(HERE / "example.py"), "--check"], 30)
        run(["rsvg-convert", "--format=pdf", "--output=support-bounds.pdf", str(HERE / "support-bounds.svg")], 60)
        run(["pandoc", "--from=markdown", "--to=latex", "--standalone", "--syntax-highlighting=none",
             "--template", str(HERE/"publication.tex"), "--lua-filter", str(HERE/"publication.lua"),
             "--output=report.tex", str(HERE/"README.md")], 60)
        for _ in range(2):
            run(["lualatex", "--no-shell-escape", "--halt-on-error", "--file-line-error",
                 "--interaction=nonstopmode", "report.tex"], 120)
        log = (work / "report.log").read_text(errors="replace")
        errors = [s for s in log.splitlines() if "Overfull " in s or "Missing character:" in s]
        if errors:
            raise ValueError("\n".join(errors))
        verify(work / "report.pdf", repo)
        publish(work / "report.pdf", output)
        if figure is not None:
            publish(work / "support-bounds.pdf", figure)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository root for the two shared styles and PDF checks")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="build a standalone reader to this destination")
    mode.add_argument("--check", action="store_true", help="compare a fresh build with the shipped PDF byte by byte")
    mode.add_argument("--check-committed", action="store_true", help="inspect the shipped sources and PDF without typesetting")
    parser.add_argument("--figure", type=Path, help="also export the vector figure with --output")
    args = parser.parse_args()
    if args.figure and args.output is None:
        parser.error("--figure requires --output")
    repo = args.repo.resolve()
    if args.output is not None:
        build(args.output, repo, args.figure)
        return
    shipped = repo / "output/pdf" / (STEM + ".pdf")
    record = profile(repo)
    if sha(shipped) != record["pdf_sha256"] or verify(shipped, repo) != set(record["pdf_urls"]):
        raise ValueError("shipped PDF bytes or external link targets changed")
    if args.check:
        with tempfile.TemporaryDirectory(prefix=STEM + "-check-") as directory:
            rebuilt = Path(directory) / shipped.name
            build(rebuilt, repo)
            if rebuilt.read_bytes() != shipped.read_bytes():
                raise ValueError("fresh PDF differs from the shipped artifact")
    print("verified " + ("same-toolchain source-to-PDF bytes" if args.check else "committed sources, PDF profile and links"))

if __name__ == "__main__":
    main()
