#!/usr/bin/env python3
"""Build the fixed recorded-sensor document; discovery is not reference adoption.

Uses the existing bounded Runner/Snapshot without proof or preparation hooks.
Native dependencies are a named recorded profile, not a hermetic closure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
from types import ModuleType
from xml.sax.saxutils import escape

ASSETS = "audit/formal/latex/real-occupancy-sensors/"
FIGURES = "audit/formal/latex/figures/real-occupancy-sensors/"
EVIDENCE = "audit/evidence/real-occupancy-sensors-example-2026-09-08/"
MARKDOWN = EVIDENCE[:-1] + ".md"
PDF = "output/pdf/recorded-office-sensors.pdf"
MANIFEST = ASSETS + "publication-inputs-v1.json"
MANIFEST_SHA = "e00e54756a3d801b1d17447c9d5a0b6735c4c340fd3946b9951f875490233c5d"
RUNTIME = "audit/formal/lean-prefix-mgw-mean/replay-support/runtime.py"
RUNTIME_SHA = "bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d"
SOURCE_FILES = frozenset({
    MARKDOWN, "crates/pid-core/examples/occupancy_sensors.rs", "METHODS.md", RUNTIME,
    "scripts/check-formal-pdf-log.sh",
    "audit/formal/latex/pid-rs-report-tables.sty",
    "audit/formal/latex/pid-rs-workflow-publication.sty",
    *(ASSETS + name for name in ("publication.tex", "filter.lua", "body.expected.tex")),
    *(EVIDENCE + name + ".json" for name in (
        "data-facts", "descriptive-comparisons", "humidity-ratio-negative-witnesses",
        "future-co2-alignment", "runtime-results", "definition-check")),
    *(FIGURES + name + suffix for name in ("recording-roles", "signed-cancellation")
      for suffix in (".svg", ".pdf")),
})
HEX = re.compile(r"[0-9a-f]{64}\Z")
PRIMARY_SECONDS = 120
TOTAL_SECONDS = 900
STREAM_BYTES = 4 * 1024**2
RSS_BYTES = 4 * 1024**3
DISK_KIB = 2 * 1024**2


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def record(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def direct_directory(path: Path) -> Path:
    path = path.absolute()
    require(path == path.resolve(strict=True) and path.is_dir(),
            "directory must be canonical and free of symlink components")
    return path


def bootstrap(path: Path) -> bytes:
    """Capture the one pinned runtime before executing its module definitions."""
    direct_directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "runtime must be a direct single-link regular file")
    require(before.st_size <= 128 * 1024, "runtime source exceeds bootstrap bound")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(opened) == identity(after)
            == identity(path.lstat()) and len(raw) == before.st_size,
            "runtime changed during capture")
    require(sha(raw) == RUNTIME_SHA, "runtime digest changed")
    return raw


def load_runtime(path: Path) -> ModuleType:
    raw = bootstrap(path)
    module = ModuleType("recorded_sensor_publication_runtime")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True,
                 optimize=sys.flags.optimize), module.__dict__)
    return module


def relative_path(value: object) -> str:
    require(type(value) is str and bool(value) and "\\" not in value,
            "unsafe profile path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts
            and str(path) == value and ":" not in value,
            "unsafe profile path")
    return value


def validate_pin(pin: object, label: str) -> None:
    require(type(pin) is dict and set(pin) == {"sha256", "bytes", "mode"}
            and type(pin["bytes"]) is int and pin["bytes"] >= 0
            and type(pin["sha256"]) is str and HEX.fullmatch(pin["sha256"])
            and type(pin["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", pin["mode"]),
            "malformed pin: " + label)


def check_pin(raw: bytes, pin: object, label: str, path: Path) -> None:
    validate_pin(pin, label)
    require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"],
            "input digest changed: " + label)
    require(oct(stat.S_IMODE(path.lstat().st_mode)) == pin["mode"],
            "input mode changed: " + label)


def read_pinned(snapshot: object, path: Path, pin: object, label: str) -> bytes:
    validate_pin(pin, label)
    before = path.lstat()
    require(before.st_size == pin["bytes"], "input size changed: " + label)
    require(oct(stat.S_IMODE(before.st_mode)) == pin["mode"], "input mode changed: " + label)
    raw = snapshot.read(path)
    check_pin(raw, pin, label, path)
    return raw


def verify_recorder(build: Path, tex_root: Path, profile: dict, snapshot: object) -> None:
    """Reject undeclared external recorder inputs; owned cache is generated state."""
    allowed_local = {"publication.tex", "body.tex", "recording-roles.pdf",
                     "signed-cancellation.pdf", "pid-rs-report-tables.sty",
                     "pid-rs-workflow-publication.sty", "recorded-office-sensors.aux",
                     "recorded-office-sensors.out", "recorded-office-sensors.toc"}
    for line in (build / "recorded-office-sensors.fls").read_text().splitlines():
        if not line.startswith("INPUT "):
            continue
        path = Path(line[6:])
        path = path if path.is_absolute() else build / path
        path = path.resolve(strict=True)
        if path.is_relative_to(tex_root):
            relative = str(path.relative_to(tex_root))
            require(relative in profile["tex_files"], "undeclared TeX input: " + relative)
            read_pinned(snapshot, path, profile["tex_files"][relative], relative)
        elif path.is_relative_to(build):
            relative = path.relative_to(build)
            require(str(relative) in allowed_local
                    or relative.parts[0] in {"cache", "fonts", "texmf-var"},
                    "undeclared local TeX input: " + str(relative))
        else:
            raise RuntimeError("TeX recorder input outside captured roots: " + str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--work-dir", type=Path, help="fresh, retained directory")
    parser.add_argument("--output", type=Path, help="new output; never the canonical reference")
    parser.add_argument("--tex-root", type=Path, help="canonical selected TeX Live root")
    parser.add_argument("--check", action="store_true", help="make two fresh builds")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--exact", action="store_true")
    modes.add_argument("--cross-toolchain", action="store_true")
    args = parser.parse_args(argv)
    if args.cross_toolchain:
        print("Recorded sensors: no reviewed cross-toolchain relation; status 2 refusal.",
              file=sys.stderr)
        return 2
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires Python 3.11+ -I -S -B, optionally -O")
    require(args.work_dir is not None and args.tex_root is not None,
            "build requires --work-dir and --tex-root")
    work = args.work_dir.absolute()
    direct_directory(work.parent)
    require(not work.exists() and not work.is_symlink(), "work directory already exists")
    work.mkdir(mode=0o700)
    started, started_ns = now(), time.monotonic_ns()
    deadline, deadline_ns = started + dt.timedelta(seconds=TOTAL_SECONDS), started_ns + TOTAL_SECONDS * 10**9
    result = {"status": "failed", "started_utc": started.isoformat(),
              "start_monotonic_ns": started_ns, "deadline_utc": deadline.isoformat(),
              "deadline_monotonic_ns": deadline_ns, "mode": "exact" if args.exact else "discovery",
              "scope": "document bytes only; no scientific or visual adoption",
              "disk_policy": "pre/post samples; no hard quota or cadence guarantee"}
    snapshot = None
    runners = []
    disk_count = 0
    try:
        root, tex_root = direct_directory(args.root), direct_directory(args.tex_root)
        output = None if args.output is None else args.output.absolute()
        if output is not None:
            direct_directory(output.parent)
            require(output != work and output != root / PDF
                    and not output.exists() and not output.is_symlink(),
                    "output must be a new path distinct from work and the canonical reference")
        runtime = load_runtime(root / RUNTIME)
        snapshot = runtime.Snapshot()
        require(sha(snapshot.read(root / RUNTIME)) == RUNTIME_SHA, "runtime changed after load")
        snapshot.read(Path(__file__).absolute())
        require((root / MANIFEST).lstat().st_size <= 1024**2, "publication manifest exceeds source bound")
        manifest_raw = snapshot.read(root / MANIFEST)
        require(sha(manifest_raw) == MANIFEST_SHA, "publication manifest digest changed")
        profile = runtime.strict_json(manifest_raw)
        require(type(profile) is dict and profile["schema"] == "pid-rs/recorded-office-sensors-publication-v1"
                and set(profile["files"]) == SOURCE_FILES,
                "publication source roster changed")
        require(profile["profile"] == "darwin-arm64-texlive-2024-pandoc-3.10.2"
                and profile["source_epoch"] == "1788912000", "unsupported publication profile")
        reference = profile["reference"]
        require(type(reference) is dict and set(reference) == {"status", "sha256"}
                and reference["status"] in {"pending", "admitted"}, "invalid reference state")
        if args.exact:
            require(reference["status"] == "admitted"
                    and type(reference["sha256"]) is str and HEX.fullmatch(reference["sha256"]),
                    "exact reference is pending; use discovery without adoption credit")
            reference_bytes = snapshot.read(root / PDF)
            require(sha(reference_bytes) == reference["sha256"], "admitted reference changed")
        else:
            reference_bytes = None
        sources = {}
        for relative, pin in profile["files"].items():
            data = read_pinned(snapshot, root / relative_path(relative), pin, relative)
            sources[relative] = data
        require(type(profile["tex_files"]) is dict and bool(profile["tex_files"]),
                "missing recorded TeX profile")
        for relative, pin in profile["tex_files"].items():
            path = tex_root / relative_path(relative)
            read_pinned(snapshot, path, pin, relative)
        require(set(profile["fonts"]) == {
                "SourceSansPro-Bold.otf",
                "SourceSansPro-Regular.otf",
                "SourceSansPro-RegularIt.otf",
                "SourceSansPro-Semibold.otf",
                "SourceSansPro-SemiboldIt.otf",
                "latinmodern-math.otf",
                "lmmono10-italic.otf",
                "lmmono10-regular.otf",
                "lmmonolt10-bold.otf",
                "lmmonolt10-boldoblique.otf",
                "lmroman10-bold.otf",
                "lmroman10-bolditalic.otf",
                "lmroman10-italic.otf",
                "lmroman10-regular.otf",
                "lmroman12-bold.otf",
                "lmroman12-regular.otf",
                }, "controlled font roster changed")
        for relative in profile["fonts"].values():
            require(relative_path(relative) in profile["tex_files"], "unbound controlled font")
        require(set(profile["tools"]) == {"pandoc", "lualatex", "bash", "python", "du", "ps"},
                "tool roster changed")
        selectors = {"python": sys.executable, "bash": "/bin/bash", "du": "/usr/bin/du", "ps": "/bin/ps"}
        for name in ("pandoc", "lualatex"):
            selected = shutil.which(name)
            require(selected is not None and Path(selected).is_absolute(), "missing tool: " + name)
            selectors[name] = selected
        targets = {name: Path(path).resolve(strict=True) for name, path in selectors.items()}
        for name, path in targets.items():
            read_pinned(snapshot, path, profile["tools"][name], "tool " + name)
        snapshot.save(work)
        record(work / "INPUTS.json", snapshot.manifest())

        build_snapshot = None

        def guard() -> None:
            require(now() < deadline - dt.timedelta(seconds=15)
                    and time.monotonic_ns() < deadline_ns - 15 * 10**9,
                    "publication original deadline exhausted")
            snapshot.verify()
            if build_snapshot is not None:
                build_snapshot.verify()
            require(all(Path(selectors[name]).resolve(strict=True) == target
                        for name, target in targets.items()), "tool selector changed")
            require(now() < deadline - dt.timedelta(seconds=15)
                    and time.monotonic_ns() < deadline_ns - 15 * 10**9,
                    "publication original deadline exhausted during input checks")

        def disk(phase: str) -> None:
            nonlocal disk_count
            disk_count += 1
            require(disk_count <= 20, "disk observation roster exceeded")
            completed = subprocess.run([selectors["du"], "-sk", str(work)],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=5, check=False,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
            row = {"phase": phase, "utc": now().isoformat(), "monotonic_ns": time.monotonic_ns(),
                   "returncode": completed.returncode, "stdout": completed.stdout.decode(),
                   "stderr": completed.stderr.decode()}
            record(work / ("DISK-%02d.json" % disk_count), row)
            require(completed.returncode == 0 and not completed.stderr, "disk observation failed")
            require(int(completed.stdout.split()[0]) <= DISK_KIB, "sampled disk limit exceeded")

        produced = []
        for index in range(2 if args.check else 1):
            guard()
            build = work / ("build-" + str(index + 1))
            build.mkdir(mode=0o700)
            for name in ("tmp", "cache", "texmf-var", "texmf-config", "fonts", "font-cache", "execution"):
                (build / name).mkdir(mode=0o700)
            (build / "cache/luatex-cache/generic/names").mkdir(parents=True)
            (build / "cache/luatex-cache/generic/fonts/otl").mkdir(parents=True)
            for name, relative in profile["fonts"].items():
                (build / "fonts" / name).write_bytes(snapshot.read(tex_root / relative))
            for relative, name in (
                (ASSETS + "publication.tex", "publication.tex"), (ASSETS + "filter.lua", "filter.lua"),
                (MARKDOWN, "body.md"),
                (FIGURES + "recording-roles.pdf", "recording-roles.pdf"),
                (FIGURES + "signed-cancellation.pdf", "signed-cancellation.pdf"),
                ("audit/formal/latex/pid-rs-report-tables.sty", "pid-rs-report-tables.sty"),
                ("audit/formal/latex/pid-rs-workflow-publication.sty", "pid-rs-workflow-publication.sty"),
            ):
                (build / name).write_bytes(sources[relative])
            (build / "fonts.conf").write_text(
                '<?xml version="1.0"?>\n<fontconfig><dir>' + escape(str(build / "fonts"))
                + '</dir><cachedir>' + escape(str(build / "font-cache"))
                + '</cachedir><alias><family>Arial</family><prefer><family>Source Sans Pro</family>'
                  '</prefer></alias><alias><family>sans-serif</family><prefer><family>Source Sans Pro'
                  '</family></prefer></alias><config></config></fontconfig>\n')
            environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TEXINPUTS": str(build) + ":", "TEXMFVAR": str(build / "texmf-var"),
                "TEXMFCONFIG": str(build / "texmf-config"), "TEXMFCACHE": str(build / "cache"),
                "TEXMFOUTPUT": str(build), "SOURCE_DATE_EPOCH": profile["source_epoch"],
                "FORCE_SOURCE_DATE": "1", "FONTCONFIG_FILE": str(build / "fonts.conf"),
                "FONTCONFIG_PATH": str(build), "PANGOCAIRO_BACKEND": "fc",
                "OSFONTDIR": str(build / "fonts"), "TMPDIR": str(build / "tmp")}
            record(build / "ENVIRONMENT.json", environment)
            build_snapshot = runtime.Snapshot()
            for name in ("publication.tex", "filter.lua", "body.md", "recording-roles.pdf",
                         "signed-cancellation.pdf", "pid-rs-report-tables.sty",
                         "pid-rs-workflow-publication.sty", "fonts.conf"):
                build_snapshot.read(build / name)
            for name in profile["fonts"]:
                build_snapshot.read(build / "fonts" / name)
            record(build / "COPY_INPUTS.json", build_snapshot.manifest())
            runner = runtime.Runner(build / "execution", environment, preparation=False)
            runners.append(runner)

            def run(command: list[str], label: str) -> None:
                guard()
                disk(label + " before")
                remaining = (deadline_ns - time.monotonic_ns()) / 10**9 - 15
                require(remaining > 0, "publication original deadline exhausted")
                runner.run(command, build, label, timeout=min(PRIMARY_SECONDS, remaining),
                           cap=STREAM_BYTES, memory=RSS_BYTES, allow_stdout=True)
                guard()
                disk(label + " after")

            run([selectors["pandoc"], str(build / "body.md"), "--from=markdown", "--to=latex",
                 "--wrap=none", "--lua-filter", str(build / "filter.lua"),
                 "--output", str(build / "body.tex")], "pandoc")
            require(build_snapshot.read(build / "body.tex") == sources[ASSETS + "body.expected.tex"],
                    "generated TeX differs from the pinned canonical projection")
            record(build / "BODY_INPUT.json", {"body.tex": {
                "sha256": sha(sources[ASSETS + "body.expected.tex"]),
                "bytes": len(sources[ASSETS + "body.expected.tex"])}})
            for number in (1, 2):
                run([selectors["lualatex"], "-no-shell-escape", "-interaction=nonstopmode",
                     "-halt-on-error", "-file-line-error", "-recorder",
                     "-jobname=recorded-office-sensors", "publication.tex"], "lualatex-" + str(number))
                verify_recorder(build, tex_root, profile, snapshot)
                log_command = [selectors["bash"], str(root / "scripts/check-formal-pdf-log.sh")]
                if number == 1:
                    log_command.append("--intermediate")
                run(log_command + [str(build / "recorded-office-sensors.log")], "log-" + str(number))
            pdf = (build / "recorded-office-sensors.pdf").read_bytes()
            require(pdf.startswith(b"%PDF-") and b"%%EOF" in pdf[-1024:], "missing or incomplete PDF")
            if reference_bytes is not None:
                require(pdf == reference_bytes, "rebuilt PDF differs from the admitted reference")
            produced.append(pdf)
        guard()
        require(all(pdf == produced[0] for pdf in produced), "fresh repeated PDFs differ")
        if output is not None:
            direct_directory(output.parent)
            with output.open("xb") as stream:
                stream.write(produced[0])
                stream.flush()
                os.fsync(stream.fileno())
        guard()
        result.update(status="exact_reference_reproduced" if args.exact else "discovery_requires_artifact_review",
                      builds=len(produced), pdf_sha256=sha(produced[0]), pdf_bytes=len(produced[0]),
                      sources_and_tools_unchanged=True,
                      link_review="existing staged publication-link gate required; no new reader executed",
                      visual_review="separate actual page/font/navigation review required")
        print("OK: recorded sensors " + result["status"] + "; builds=" + str(len(produced)))
        return 0
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        completed, completed_ns = now(), time.monotonic_ns()
        late = completed >= deadline or completed_ns >= deadline_ns
        successful_body = result["status"] != "failed"
        if late and successful_body:
            result.update(status="failed", failure="deadline exhausted before final receipt")
        result["completed_utc"] = completed.isoformat()
        result["completed_monotonic_ns"] = completed_ns
        result["commands"] = [command for runner in runners for command in runner.commands]
        result["disk_observations"] = disk_count
        record(work / "RESULT.json", result)
        if successful_body:
            require(not late and now() < deadline and time.monotonic_ns() < deadline_ns,
                    "publication deadline exhausted at final receipt; actual outer exit is required")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print("Recorded-sensor publication failed: " + str(error), file=sys.stderr)
        print(json.dumps({"status": "failed", "failure": str(error),
              "receipt_scope": "RESULT.json only after ownership of fresh work; retain this actual outer stderr"}),
              file=sys.stderr)
        raise SystemExit(1)
