#!/usr/bin/env python3
"""Reproduce the finite target-copy MGW PDF from committed sources.

The command is an exact same-profile build aid. It records no claim of native
dependency hermeticity, independent rendering, formal validity, or estimator
calibration. Run from the repository root with a writable temporary directory.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "audit/evidence/finite-target-copy-mgw-synergy.md"
SVG = ROOT / "audit/formal/latex/figures/mgw-target-copy/event-union.svg"
TEMPLATE = ROOT / "audit/formal/latex/mgw-fixed-world/publication.tex"
FILTER = ROOT / "audit/formal/latex/mgw-target-copy/filter.lua"
PDF = ROOT / "output/pdf/finite-target-copy-mgw-synergy.pdf"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(argv: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(argv, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, timeout=240)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare the rebuilt PDF with the committed PDF")
    ap.add_argument("--cross-toolchain", action="store_true", help="refuse: no reviewed cross-toolchain profile exists")
    ap.add_argument("--work-dir", type=Path)
    args = ap.parse_args()
    if args.cross_toolchain:
        print("finite target-copy MGW: no reviewed cross-toolchain profile; refusing", flush=True)
        return 2
    if not MD.is_file() or not SVG.is_file() or not TEMPLATE.is_file() or not FILTER.is_file():
        raise SystemExit("required committed source or reviewed filter is missing")
    work = args.work_dir or Path(tempfile.mkdtemp(prefix="pid-rs-mgw-target-copy-"))
    work = work.resolve(); work.mkdir(parents=True, exist_ok=True)
    for name in ("fonts", "tmp", "cache", "texmf-var", "texmf-config"):
        (work / name).mkdir(exist_ok=True)
    shutil.copyfile(MD, work / "body.md")
    shutil.copyfile(SVG, work / "event-union.svg")
    shutil.copyfile(FILTER, work / "filter.lua")
    tex = TEMPLATE.read_text()
    tex = tex.replace("Same MGW synergy, different added information", "Finite target-copy identities and entropy bounds for MGW synergy")
    tex = tex.replace("Same synergy, different added information", "Finite target-copy MGW synergy")
    tex = tex.replace("A finite probability proof for categorical MGW shared exclusions", "Finite categorical probability identities and scoped formal proofs")
    tex = tex.replace("9 September 2026", "11 September 2026")
    (work / "publication.tex").write_text(tex)
    for name in ("pid-rs-report-tables.sty", "pid-rs-workflow-publication.sty"):
        shutil.copyfile(ROOT / "audit/formal/latex" / name, work / name)
    profile = json.loads((ROOT / "audit/formal/latex/mgw-fixed-world/publication-inputs-v1.json").read_text())
    tex_root = Path("/usr/local/texlive/2024")
    for name, relative in profile["fonts"].items():
        shutil.copyfile(tex_root / relative, work / "fonts" / name)
    env = os.environ.copy()
    env.update({"TEXINPUTS": str(work) + ":", "TEXMFVAR": str(work/"texmf-var"),
                "TEXMFCONFIG": str(work/"texmf-config"), "TEXMFCACHE": str(work/"cache"),
                "TEXMFOUTPUT": str(work), "TMPDIR": str(work/"tmp"),
                "SOURCE_DATE_EPOCH": "1789084800", "FORCE_SOURCE_DATE": "1"})
    run(["/opt/homebrew/bin/rsvg-convert", "--format=pdf", "--output", str(work/"event-union.pdf"), str(work/"event-union.svg")], work, env)
    run(["/opt/homebrew/bin/pandoc", str(work/"body.md"), "--from=markdown", "--to=latex", "--wrap=none", "--lua-filter", str(work/"filter.lua"), "--resource-path", str(ROOT), "--output", str(work/"body.tex")], work, env)
    for _ in range(2):
        run(["/Library/TeX/texbin/lualatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-jobname=finite-target-copy", "publication.tex"], work, env)
    run(["/opt/homebrew/bin/pdfinfo", str(work/"finite-target-copy.pdf")], work, env)
    run(["/opt/homebrew/bin/pdffonts", str(work/"finite-target-copy.pdf")], work, env)
    run(["/opt/homebrew/bin/pdftotext", "-layout", str(work/"finite-target-copy.pdf"), str(work/"paper.txt")], work, env)
    result = {"source_markdown_sha256": digest(MD), "source_svg_sha256": digest(SVG),
              "rebuilt_pdf_sha256": digest(work/"finite-target-copy.pdf"),
              "rebuilt_pdf_bytes": (work/"finite-target-copy.pdf").stat().st_size,
              "scope": "bounded same-profile source reproduction; native dependency closure and scientific validity are outside scope"}
    if args.check:
        if not PDF.is_file() or digest(PDF) != result["rebuilt_pdf_sha256"]:
            raise SystemExit("committed PDF differs from the rebuilt source result")
        result["committed_match"] = True
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
