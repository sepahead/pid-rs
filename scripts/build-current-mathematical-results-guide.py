"""Build the November guide or verify its source, PDF and navigation profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "MATHEMATICAL_RESULTS_GUIDE_CURRENT.md"
STYLE = ROOT / "audit/formal/latex"
PROFILE_DIR = STYLE / "mathematical-results-guide-current"
COMMITTED = ROOT / "output/pdf/mathematical-results-guide-current.pdf"
BASE = "https://github.com/sepahead/pid-rs/blob/main/"


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a direct regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, *, work=None, env=None):
    result = subprocess.run(args, cwd=work, env=env, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace")[-1800:]
                         + result.stdout.decode(errors="replace")[-2800:])
    return result.stdout.decode(errors="replace")


def inputs(profile):
    for name, expected in profile["inputs"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source differs from the reviewed edition: {name}")


def verify(path, profile):
    if digest(path) != profile["pdf_sha256"]:
        raise ValueError("PDF differs from the reviewed November edition")
    info = command(["pdfinfo", str(path)])
    fields = dict(line.split(":", 1) for line in info.splitlines() if ":" in line)
    for key, wanted in profile["pdfinfo"].items():
        if fields.get(key, "").strip() != wanted:
            raise ValueError(f"unexpected PDF {key}")
    text = command(["pdftotext", "-layout", str(path), "-"])
    pages = text.rstrip("\f").split("\f")
    if len(pages) != len(profile["page_text"]):
        raise ValueError("unexpected number of extracted pages")
    for index, (page, phrases) in enumerate(zip(pages, profile["page_text"]), 1):
        flat = " ".join(page.split())
        for phrase in phrases:
            if phrase not in flat:
                raise ValueError(f"missing reviewed text from page {index}: {phrase}")
    font_rows = command(["pdffonts", str(path)]).splitlines()[2:]
    if len(font_rows) != profile["embedded_font_entries"] or not all(
            re.search(r"\byes\s+yes\s+yes\s+\d+\s+\d+\s*$", row) for row in font_rows):
        raise ValueError("expected only embedded subset fonts with Unicode mappings")
    pdf_links = {line.split()[-1] for line in command(["pdfinfo", "-url", str(path)]).splitlines()[1:]
                 if line.strip()}
    md_links = set(re.findall(r"\[[^\]\n]+\]\(([^)\s]+)\)", SOURCE.read_text(encoding="utf-8")))
    expected = {url if url.startswith("https://") else BASE + url for url in md_links}
    if pdf_links != expected or expected != set(profile["uri_targets"]):
        raise ValueError("PDF, Markdown and reviewed link destinations differ")


def build_figures(work, env):
    """Use the two original SVGs with the guide's embedded Source Sans Pro fonts."""
    font_dir = work / "guide-fonts"
    font_dir.mkdir()
    archive = STYLE / "source-coupling-compression/fonts"
    for name in ("SourceSansPro-Regular.otf", "SourceSansPro-Semibold.otf"):
        shutil.copyfile(archive / name, font_dir / name)
    config = work / "guide-fonts.conf"
    config.write_text(
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">'
        f'<fontconfig><dir>{escape(str(font_dir))}</dir>'
        f'<cachedir>{escape(str(work / "font-cache"))}</cachedir></fontconfig>',
        encoding="utf-8",
    )
    sheet = work / "figure-font.css"
    sheet.write_text('text { font-family: "Source Sans Pro"; }\n', encoding="utf-8")
    render_env = {**env, "FONTCONFIG_FILE": str(config), "PANGOCAIRO_BACKEND": "fc"}
    for study, diagram in (
        ("angular-ray-monotonicity", "angular-ray-thresholds"),
        ("strict-neighbour-count-geometry", "counts-and-distances"),
    ):
        source = ROOT / "audit/research" / study / "figures" / (diagram + ".svg")
        command(["rsvg-convert", "--format=pdf", "--stylesheet", str(sheet),
                 "--output", str(work / (diagram + ".pdf")), str(source)], work=work, env=render_env)


def build(work):
    env = {**os.environ, "TZ": "UTC", "LC_ALL": "C", "SOURCE_DATE_EPOCH": "1795046400",
           "FORCE_SOURCE_DATE": "1", "TEXINPUTS": str(STYLE) + os.pathsep}
    shutil.copyfile(PROFILE_DIR / "publication.tex", work / "publication.tex")
    build_figures(work, env)
    command(["pandoc", str(SOURCE), "--from=markdown", "--to=latex", "--lua-filter",
             str(PROFILE_DIR / "publication.lua"), "--output", "body.tex"], work=work, env=env)
    for _ in range(2):
        command(["lualatex", "--no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
                 "-file-line-error", "publication.tex"], work=work, env=env)
    log = (work / "publication.log").read_text(errors="replace")
    issues = [line for line in log.splitlines() if re.search(
        r"Warning:|Overfull |Underfull |Missing character:|Undefined control sequence", line)]
    if issues:
        raise ValueError("unreviewed typesetting diagnostics:\n" + "\n".join(issues))
    return work / "publication.pdf"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    action = cli.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="typeset and compare the exact shipped artifact")
    action.add_argument("--check-committed", action="store_true", help="qualify the shipped source and PDF")
    action.add_argument("--output", type=Path, help="write a verified reproduction at this PDF path")
    args = cli.parse_args()
    profile = json.loads((PROFILE_DIR / "edition.json").read_text(encoding="utf-8"))
    inputs(profile)
    if args.check_committed:
        verify(COMMITTED, profile)
    else:
        with tempfile.TemporaryDirectory(prefix="pid-results-november-") as tmp:
            generated = build(Path(tmp))
            verify(generated, profile)
            if args.check:
                verify(COMMITTED, profile)
                if generated.read_bytes() != COMMITTED.read_bytes():
                    raise ValueError("rebuilt and committed PDFs differ")
            else:
                dest = args.output.absolute()
                if dest.suffix.lower() != ".pdf" or dest.is_symlink():
                    raise ValueError("output must be a regular PDF path")
                if dest.exists() and digest(dest) != profile["pdf_sha256"]:
                    raise ValueError("output already contains a different file")
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as out:
                    staged = Path(out.name)
                try:
                    shutil.copyfile(generated, staged)
                    staged.chmod(0o644)
                    os.replace(staged, dest)
                finally:
                    staged.unlink(missing_ok=True)
    print("November guide passed " + ("shipped-object checks." if args.check_committed else "canonical reproduction."))


if __name__ == "__main__":
    main()
