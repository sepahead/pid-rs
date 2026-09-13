#!/usr/bin/env python3
"""Build the mean exposition once its HTTPS-link PDF successor is reviewed.

No cross-toolchain profile is admitted. Every build retains its commands and streams.
The accepted Lean replay package and its manifest are read-only historical inputs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

MANIFEST = "audit/formal/latex/prefix-mgw-mean/publication-inputs-v1.json"
MANIFEST_SHA = '6f181dcb87d6398075a568ce0156df17081ea14fe68305f7b267f819c2a59ffa'
UNIT = "audit/formal/lean-prefix-mgw-mean/"
ASSETS = "audit/formal/latex/prefix-mgw-mean/"
TITLE = "# From categorical exclusion events to MGW atom expectations\n\n"
PDF_SHA = '93ff18e21f56e4770b12b7405d57b003bf7839cef5c4207ed98a56cd6f96f58f'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def record(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def strict_json(data: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON number: " + value)
    result = json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(result) is dict, "manifest is not an object")
    return result


def direct_directory(path: Path) -> Path:
    path = path.absolute()
    require(path == path.resolve(strict=True) and path.is_dir(),
            "directory must be canonical and free of symlink components")
    return path


def capture(path: Path) -> tuple[bytes, tuple]:
    direct_directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "source must be a direct single-link regular file: " + str(path))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        require((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino),
                "source changed while opening")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(after) == identity(path.lstat()),
            "source changed while reading")
    return data, identity(after)


def transform_markdown(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    require(text.startswith(TITLE) and text.count(TITLE) == 1, "title boundary changed")
    text = text[len(TITLE):]
    old = "](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/RESULTS.md)"
    new = "](https://github.com/sepahead/pid-rs/blob/main/audit/evidence/prefix-mgw-mean-formal-verification-2026-09-08/RESULTS.md)"
    require(text.count(old) == 1, "verification-link boundary changed")
    require(text.count("](retained-rank.svg)") == 1, "figure-link boundary changed")
    companion = "](../lean-prefix-mgw-bias/EXPOSITION.md)"
    published_companion = "](https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean-prefix-mgw-bias/EXPOSITION.md)"
    require(text.count(companion) == 1, "bias-companion-link boundary changed")
    return text.replace(old, new).replace(companion, published_companion).replace("](retained-rank.svg)", "](retained-rank.pdf)").encode()


def transform_latex(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    require(text.count("\\section{") == 9, "section inventory changed")
    text = text.replace("\\section{", "\\PidMeanSection{")
    for heading in (
        "7. A sensor with no target information can give a positive short-prefix mean",
        "8. Edge cases and permitted interpretations",
    ):
        needle = "\\PidMeanSection{" + heading + "}"
        require(text.count(needle) == 1, "page-flow boundary changed")
    return text.encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--work-dir", type=Path,
                        help="fresh directory; retained after success or failure")
    parser.add_argument("--output", type=Path,
                        help="optional new output file; existing files are never overwritten")
    parser.add_argument("--check", action="store_true", help="make two fresh exact builds")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--exact", action="store_true")
    modes.add_argument("--cross-toolchain", action="store_true")
    args = parser.parse_args()
    if args.cross_toolchain:
        print("Mean exposition: no reviewed cross-toolchain relation; status 2 refusal.", file=sys.stderr)
        return 2
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires Python 3.11+ -I -S -B, optionally -O")
    require(PDF_SHA is not None and MANIFEST_SHA is not None,
            "mean PDF successor profile is unresolved; no build or acceptance admitted")
    require(args.work_dir is not None, "exact builds require an explicit fresh --work-dir")
    root = direct_directory(args.root)
    work = args.work_dir.absolute()
    direct_directory(work.parent)
    require(not work.exists() and not work.is_symlink(), "work directory already exists")
    work.mkdir(mode=0o700)
    snapshots = {}
    commands = []
    produced = []
    result = {"started_utc": now(), "status": "failed", "commands": commands,
              "scope": "exact finite publication profile; no new theorem or accessibility credit"}
    try:
        raw, identity = capture(root / MANIFEST)
        require(sha(raw) == MANIFEST_SHA, "publication manifest changed")
        snapshots[MANIFEST] = (raw, identity)
        manifest = strict_json(raw)
        require(manifest["schema"] == "pid-rs/prefix-mgw-mean-publication-inputs-v1"
                and type(manifest["expected_pages"]) is int
                and manifest["expected_pages"] == 9
                and manifest["expected_pdf_sha256"] == PDF_SHA, "publication profile changed")
        for relative, expected in manifest["files"].items():
            require(type(relative) is str and not Path(relative).is_absolute()
                    and ".." not in Path(relative).parts, "unsafe source path")
            data, source_identity = capture(root / relative)
            require(type(expected["bytes"]) is int and len(data) == expected["bytes"]
                    and sha(data) == expected["sha256"], "publication source changed: " + relative)
            snapshots[relative] = (data, source_identity)
        tools = {}
        tool_targets = {}
        for name in ("pandoc", "lualatex", "bash"):
            selected = shutil.which(name)
            require(selected is not None, "missing command: " + name)
            require(Path(selected).is_absolute(), "tool selector must be absolute")
            selected_path = Path(selected).resolve(strict=True)
            data, source_identity = capture(selected_path)
            snapshots[str(selected_path)] = (data, source_identity)
            # Preserve lualatex's selector name: executing its resolved luahbtex
            # leaf under a different argv[0] can select a different format.
            tools[name] = selected
            tool_targets[selected] = selected_path
        environment = {"PATH": os.defpath, "LC_ALL": "C", "LANG": "C", "TZ": "UTC",
                       "HOME": str(work / "home"), "TMPDIR": str(work / "tmp")}
        (work / "home").mkdir(mode=0o700)
        (work / "tmp").mkdir(mode=0o700)
        record(work / "INPUTS.json", {key: {"sha256": sha(value[0]), "bytes": len(value[0])}
                                      for key, value in snapshots.items()})
        record(work / "ENVIRONMENT.json", environment)

        def run(argv: list[str], directory: Path, label: str) -> bytes:
            require(Path(argv[0]).resolve(strict=True) == tool_targets[argv[0]],
                    "tool selector changed before launch")
            row = {"argv": argv, "cwd": str(directory), "started_utc": now()}
            commands.append(row)
            record(directory / (label + ".START.json"), row)
            # An external registered stage supervisor remains required for aggregate limits.
            with (directory / (label + ".stdout")).open("xb") as stdout, \
                 (directory / (label + ".stderr")).open("xb") as stderr:
                try:
                    completed = subprocess.run(argv, cwd=directory, env=environment,
                                               stdout=stdout, stderr=stderr, timeout=300, check=False)
                    row["returncode"] = completed.returncode
                except subprocess.TimeoutExpired:
                    row["timed_out"] = True
                    raise
                finally:
                    row["completed_utc"] = now()
                    row["stdout_sha256"] = sha((directory / (label + ".stdout")).read_bytes())
                    row["stderr_sha256"] = sha((directory / (label + ".stderr")).read_bytes())
                    record(directory / (label + ".RESULT.json"), row)
            require(completed.returncode == 0, label + " failed")
            require(not (directory / (label + ".stderr")).read_bytes(), label + " emitted stderr")
            return (directory / (label + ".stdout")).read_bytes()

        version = run([tools["pandoc"], "--version"], work, "pandoc-version")
        require(version.decode().splitlines()[0] == "pandoc 3.10.2", "Pandoc version differs")
        version = run([tools["lualatex"], "--version"], work, "lualatex-version")
        require(version.decode().splitlines()[0].strip()
                == "This is LuaHBTeX, Version 1.18.0 (TeX Live 2024)", "LuaLaTeX version differs")
        for index in range(2 if args.check else 1):
            build = work / ("build-" + str(index + 1))
            build.mkdir(mode=0o700)
            for source, leaf in (
                (ASSETS + "prefix-mgw-mean.tex", "prefix-mgw-mean.tex"),
                (ASSETS + "retained-rank.pdf", "retained-rank.pdf"),
                ("audit/formal/latex/pid-rs-report-tables.sty", "pid-rs-report-tables.sty"),
                ("audit/formal/latex/pid-rs-workflow-publication.sty", "pid-rs-workflow-publication.sty"),
            ):
                (build / leaf).write_bytes(snapshots[source][0])
            body = transform_markdown(snapshots[UNIT + "EXPOSITION.current.md"][0])
            require(body == snapshots[ASSETS + "body.expected.md"][0], "derived Markdown differs")
            (build / "body.md").write_bytes(body)
            run([tools["pandoc"], "--from=markdown", "--to=latex", "--shift-heading-level-by=-1",
                 "--wrap=none", "--output=body.tex", "body.md"], build, "pandoc")
            raw_body = (build / "body.tex").read_bytes()
            (build / "body.pandoc.raw.tex").write_bytes(raw_body)
            body_tex = transform_latex(raw_body)
            require(body_tex == snapshots[ASSETS + "body.expected.tex"][0], "derived TeX differs")
            (build / "body.tex").write_bytes(body_tex)
            for pass_number in (1, 2):
                run([tools["lualatex"], "-no-shell-escape", "-interaction=nonstopmode",
                     "-halt-on-error", "-file-line-error", "prefix-mgw-mean.tex"],
                    build, "latex-" + str(pass_number))
            run([tools["bash"], str(root / "scripts/check-formal-pdf-log.sh"),
                 str(build / "prefix-mgw-mean.log")], build, "log-check")
            pdf = (build / "prefix-mgw-mean.pdf").read_bytes()
            require(sha(pdf) == PDF_SHA and pdf == snapshots["output/pdf/prefix-mgw-mean.pdf"][0],
                    "rebuilt PDF is not the exact reviewed prototype; no normalization admitted")
            produced.append(pdf)
        for relative, observed in snapshots.items():
            source = Path(relative) if Path(relative).is_absolute() else root / relative
            require(capture(source) == observed, "source/tool changed during build: " + relative)
        require(all(Path(selector).resolve(strict=True) == target
                    for selector, target in tool_targets.items()), "tool selector changed during build")
        require(all(pdf == produced[0] for pdf in produced), "fresh repeated builds differ")
        if args.output is not None:
            output = args.output.absolute()
            direct_directory(output.parent)
            require(output != root / "output/pdf/prefix-mgw-mean.pdf",
                    "canonical reviewed PDF is an input; use a new output path")
            with output.open("xb") as stream:
                stream.write(produced[0])
                stream.flush()
                os.fsync(stream.fileno())
        result.update(status="exact_reviewed_pdf_reproduced", build_count=len(produced),
                      pdf_sha256=PDF_SHA, bytes=len(produced[0]), source_and_tools_unchanged=True)
        print("OK: mean exposition exact reviewed PDF reproduced; builds=" + str(len(produced)))
        return 0
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        result["completed_utc"] = now()
        record(work / "RESULT.json", result)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print("Mean publication build failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
