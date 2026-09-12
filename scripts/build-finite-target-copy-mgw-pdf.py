#!/usr/bin/env python3
"""Rebuild the finite target-copy MGW PDF with checked selected inputs.

Two fresh builds must agree. Exact checking also requires the committed PDF.
Executable/font/selected TeX hashes are a bounded input snapshot, not native
loader hermeticity, historical execution evidence, or scientific validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = "audit/formal/latex/mgw-target-copy/"
PROFILE = ASSETS + "publication-inputs-v1.json"
PROFILE_SHA = "3b7a9384e266a6ebd789d91c5d904012eeba088bcebd748dfea2c00e880cf2d3"
MD = "audit/evidence/finite-target-copy-mgw-synergy.md"
SVG = "audit/formal/latex/figures/mgw-target-copy/event-union.svg"
PDF = "output/pdf/finite-target-copy-mgw-synergy.pdf"
WARNINGS = re.compile(
    r"^(?:(?:LaTeX|Package[ \t]|Class[ \t]|Lua(?:HB)?TeX|pdfTeX).*?\bwarning\b"
    r"|warning\b|(?:Over|Under)full|Missing character:|!)", re.I | re.M)


class BuildError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BuildError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate profile key: {key}")
        result[key] = value
    return result


def checked_bytes(path: Path, pin: dict) -> bytes:
    before = path.stat()
    require(stat.S_ISREG(before.st_mode), f"input is not a regular file: {path.name}")
    require(type(pin["bytes"]) is int and 0 <= pin["bytes"] <= 512 * 1024 * 1024,
            "invalid input byte bound")
    require(before.st_size == pin["bytes"], f"input size differs: {path.name}")
    with path.open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    require(len(raw) == pin["bytes"] and digest(raw) == pin["sha256"],
            f"input digest differs: {path.name}")
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    require(all(getattr(before, field) == getattr(after, field) for field in fields),
            f"input changed during read: {path.name}")
    return raw


def new_work_directory(selected: Path | None) -> Path:
    if selected is None:
        return Path(tempfile.mkdtemp(prefix="pid-rs-mgw-target-copy-")).resolve()
    # Resolve the parent only. Resolving the leaf first would accept an existing
    # symlink and direct writes into its target.
    parent = selected.absolute().parent.resolve(strict=True)
    path = parent / selected.name
    require(not path.exists() and not path.is_symlink(), "work directory must not already exist")
    path.mkdir(mode=0o700)
    return path


def tool_path(name: str) -> str:
    selected = shutil.which(name)
    require(selected is not None, f"missing tool: {name}")
    # Child commands change cwd. Preserve the invocation basename (lualatex
    # selects a format through its name), while making a relative PATH absolute.
    return os.path.abspath(selected)


def run(argv: list[str], cwd: Path, env: dict[str, str], label: str,
        *, allow_stderr: bool = False) -> bytes:
    stdout_path, stderr_path = cwd / (label + ".stdout"), cwd / (label + ".stderr")
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            child = subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                   timeout=240, check=False)
        except subprocess.TimeoutExpired as error:
            raise BuildError(f"{label} timed out; retained logs in {cwd}") from error
    stdout, stderr = stdout_path.read_bytes(), stderr_path.read_bytes()
    require(child.returncode == 0, f"{label} exited {child.returncode}; retained logs in {cwd}")
    require(allow_stderr or not stderr, f"{label} wrote stderr; retained logs in {cwd}")
    return stdout + (stderr if allow_stderr else b"")


def build(work: Path, sources: dict[str, bytes], fonts: dict[str, bytes],
          tools: dict[str, str], tex_root: Path, epoch: int) -> bytes:
    work.mkdir(mode=0o700)
    for name in ("fonts", "tmp", "cache", "texmf-var", "texmf-config", "texmf-home"):
        (work / name).mkdir()
    files = {"body.md": sources[MD], "event-union.svg": sources[SVG],
             "filter.lua": sources[ASSETS + "filter.lua"],
             "publication.tex": sources[ASSETS + "publication.tex"]}
    for name in ("pid-rs-report-tables.sty", "pid-rs-workflow-publication.sty"):
        files[name] = sources["audit/formal/latex/" + name]
    for name, raw in files.items():
        (work / name).write_bytes(raw)
    for name, raw in fonts.items():
        (work / "fonts" / name).write_bytes(raw)
    env = {
        "PATH": os.pathsep.join(dict.fromkeys(str(Path(p).parent) for p in tools.values())),
        "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
        "TEXINPUTS": str(work) + ":", "TEXMFVAR": str(work / "texmf-var"),
        "TEXMFCONFIG": str(work / "texmf-config"), "TEXMFHOME": str(work / "texmf-home"),
        "TEXMFCACHE": str(work / "cache"), "TEXMFOUTPUT": str(work),
        "TMPDIR": str(work / "tmp"), "SOURCE_DATE_EPOCH": str(epoch), "FORCE_SOURCE_DATE": "1",
    }
    run([tools["rsvg-convert"], "--format=pdf", "--output", str(work / "event-union.pdf"),
         str(work / "event-union.svg")], work, env, "figure")
    run([tools["pandoc"], str(work / "body.md"), "--from=markdown", "--to=latex",
         "--wrap=none", "--lua-filter", str(work / "filter.lua"), "--resource-path", str(work),
         "--output", str(work / "body.tex")], work, env, "pandoc")
    for index in (1, 2):
        run([tools["lualatex"], "-no-shell-escape", "-interaction=nonstopmode",
             "-halt-on-error", "-file-line-error", "-jobname=finite-target-copy",
             "-fmt=" + str(tex_root / "texmf-var/web2c/luahbtex/lualatex.fmt"),
             "publication.tex"], work, env, f"tex-{index}")
    log = (work / "finite-target-copy.log").read_text(errors="strict")
    require(not WARNINGS.search(log), f"final TeX log has a warning; retained logs in {work}")
    produced = work / "finite-target-copy.pdf"
    info = run([tools["pdfinfo"], str(produced)], work, env, "pdfinfo")
    font_info = run([tools["pdffonts"], str(produced)], work, env, "pdffonts")
    font_rows = font_info.decode().splitlines()[2:]
    require(font_rows and all(len(row.split()) >= 5 and row.split()[-5] == "yes"
                              for row in font_rows), "PDF contains an unembedded font")
    require(re.search(rb"Pages:\s+11\b", info) is not None and b"(A4)" in info,
            "unexpected page count or page size")
    run([tools["pdftotext"], "-layout", str(produced), str(work / "paper.txt")],
        work, env, "pdftotext")
    require((work / "paper.txt").stat().st_size > 1000, "PDF text extraction is empty")
    return produced.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="require exact committed PDF bytes")
    mode.add_argument("--cross-toolchain", action="store_true", help="refuse unreviewed alternate profiles")
    parser.add_argument("--tex-root", type=Path, help="selected TeX Live 2024 root")
    parser.add_argument("--work-dir", type=Path, help="new directory under an existing parent")
    args = parser.parse_args()
    if args.cross_toolchain:
        print("finite target-copy MGW: no reviewed cross-toolchain profile; refusing")
        return 2
    try:
        require(args.tex_root is not None, "--tex-root is required")
        tex_root = args.tex_root.resolve(strict=True)
        raw_profile = (ROOT / PROFILE).read_bytes()
        require(digest(raw_profile) == PROFILE_SHA, "frozen publication profile differs")
        profile = json.loads(raw_profile, object_pairs_hook=unique_object)
        require(profile["schema"] == "pid-rs-target-copy-pdf-inputs-v1", "unexpected profile schema")
        sources = {path: checked_bytes(ROOT / path, pin) for path, pin in profile["files"].items()}
        for path, pin in profile["tex_files"].items():
            checked_bytes(tex_root / path, pin)
        fonts = {name: checked_bytes(tex_root / relative, profile["tex_files"][relative])
                 for name, relative in profile["fonts"].items()}
        tools = {}
        for name, pin in profile["tools"].items():
            selected = tool_path(name)
            checked_bytes(Path(selected), pin)
            tools[name] = selected
        require(Path(tools["lualatex"]).resolve().is_relative_to(tex_root),
                "lualatex executable is outside the selected TeX tree")
        committed = checked_bytes(ROOT / PDF, profile["expected_pdf"]) if args.check else None
        work = new_work_directory(args.work_dir)
        for name, pin in profile["tools"].items():
            raw = run([tools[name], *pin["version_args"]], work,
                      {"PATH": os.pathsep.join(str(Path(p).parent) for p in tools.values()),
                       "LANG": "C", "LC_ALL": "C"}, "version-" + name, allow_stderr=True)
            require(raw.decode().splitlines()[0] == pin["version_first_line"],
                    f"tool version differs: {name}")
        first = build(work / "first", sources, fonts, tools, tex_root, profile["source_epoch"])
        second = build(work / "second", sources, fonts, tools, tex_root, profile["source_epoch"])
        require(first == second, "fresh builds differ")
        require(committed is None or first == committed, "committed PDF differs from rebuilt bytes")
        for path, pin in profile["files"].items():
            require(checked_bytes(ROOT / path, pin) == sources[path], "source changed during builds")
        for path, pin in profile["tex_files"].items():
            checked_bytes(tex_root / path, pin)
        for name, pin in profile["tools"].items():
            checked_bytes(Path(tools[name]), pin)
        require((ROOT / PROFILE).read_bytes() == raw_profile, "profile changed during builds")
        print(json.dumps({"source_markdown_sha256": digest(sources[MD]),
                          "source_svg_sha256": digest(sources[SVG]),
                          "rebuilt_pdf_sha256": digest(first), "rebuilt_pdf_bytes": len(first),
                          "repeated_builds": 2, "committed_match": committed is not None,
                          "profile_sha256": PROFILE_SHA,
                          "scope": "same-profile source reproduction; no native closure or scientific validity"},
                         indent=2, sort_keys=True))
        return 0
    except (BuildError, OSError, UnicodeError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"finite target-copy MGW: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
