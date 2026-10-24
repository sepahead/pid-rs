#!/usr/bin/env python3
"""Retained causal controls for the source-partition PDF leaf and its dispatch.

--dispatch-only needs no PDF parser or producer and grants no native build credit.
Full controls mutate the actual selected PDF; native reproduction remains separate.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build-source-coupling-compression-pdf.py"
GATE = ROOT / "scripts/check-formal-pdf-set.sh"
SOURCE = "audit/research/source-coupling-compression/EXPOSITION.md"
STEM = "source-coupling-compression"
MAX_CONTROL_BYTES = 6 * 1024 * 1024
PREFLIGHT = '''# BEGIN SOURCE COUPLING PREFLIGHT
if [[ "$MODE" == "--exact" ]]; then
  : "${PID_RS_SOURCE_COUPLING_PYTHON:?formal PDF set: source-coupling pinned Python is required}"
  : "${PID_RS_SOURCE_COUPLING_TEX_ROOT:?formal PDF set: source-coupling TeX root is required}"
  : "${PID_RS_SOURCE_COUPLING_WORK_DIR:?formal PDF set: source-coupling fresh work directory is required}"
  : "${PID_RS_SOURCE_COUPLING_DEADLINE:?formal PDF set: source-coupling original deadline is required}"
  : "${PID_RS_SOURCE_COUPLING_CONTROL_NORMAL:?formal PDF set: source-coupling normal control output is required}"
  : "${PID_RS_SOURCE_COUPLING_CONTROL_OPTIMIZED:?formal PDF set: source-coupling optimized control output is required}"
  : "${PID_RS_SOURCE_COUPLING_CONTROL_DEADLINE:?formal PDF set: source-coupling control deadline is required}"
fi
# END SOURCE COUPLING PREFLIGHT'''
EXACT = '''# BEGIN SOURCE COUPLING EXACT DISPATCH
if [[ "$MODE" == "--exact" ]]; then
  "$PID_RS_SOURCE_COUPLING_PYTHON" -I -B scripts/check-source-coupling-compression-pdf-self-test.py --work-dir "$PID_RS_SOURCE_COUPLING_CONTROL_NORMAL" --deadline "$PID_RS_SOURCE_COUPLING_CONTROL_DEADLINE"
  "$PID_RS_SOURCE_COUPLING_PYTHON" -O -I -B scripts/check-source-coupling-compression-pdf-self-test.py --work-dir "$PID_RS_SOURCE_COUPLING_CONTROL_OPTIMIZED" --deadline "$PID_RS_SOURCE_COUPLING_CONTROL_DEADLINE"
  "$PID_RS_SOURCE_COUPLING_PYTHON" -I -B scripts/build-source-coupling-compression-pdf.py --check --tex-root "$PID_RS_SOURCE_COUPLING_TEX_ROOT" --work-dir "$PID_RS_SOURCE_COUPLING_WORK_DIR" --deadline "$PID_RS_SOURCE_COUPLING_DEADLINE"
fi
# END SOURCE COUPLING EXACT DISPATCH'''
CROSS = '''# BEGIN SOURCE COUPLING CROSS REFUSAL
if [[ "$MODE" == "--cross-toolchain" ]]; then
  if python3 -I -S -B scripts/build-source-coupling-compression-pdf.py --cross-toolchain; then
    echo "formal PDF set: source-coupling cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    SOURCE_COUPLING_CROSS_STATUS=$?
  fi
  if [[ "$SOURCE_COUPLING_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: source-coupling refusal returned $SOURCE_COUPLING_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi
# END SOURCE COUPLING CROSS REFUSAL'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def wiring(text: str) -> None:
    for name, block in (("preflight", PREFLIGHT), ("exact dispatch", EXACT), ("cross refusal", CROSS)):
        require(text.count(block) == 1, "source-coupling " + name + " differs")
    require(text.index(PREFLIGHT) < text.index('if [[ "$MODE" == "--inventory-only" ]]; then') <
            text.index(EXACT) < text.index("python3 -I -B scripts/check-publication-links.py"),
            "source-coupling dispatch order differs")
    markdown = text.split("STANDALONE_MARKDOWN_SOURCES=(", 1)[1].split("\n)", 1)[0]
    papers = text.split("STANDALONE_MARKDOWN_PAPERS=(", 1)[1].split("\n)", 1)[0]
    require(markdown.count('"' + SOURCE + '"') == 1 and papers.count('"' + STEM + '"') == 1,
            "source-coupling inventory differs")


class Controls:
    def __init__(self, root: Path, module: dict, deadline: float):
        self.root, self.module, self.deadline = root, module, deadline
        self.cases = []
        self.serial = 0

    def record(self, name: str, kind: str, detail: object = None) -> None:
        self.module["deadline_check"](self.deadline)
        fixture_usage(self.root)
        self.cases.append({"name": name, "kind": kind, "detail": detail})

    def reject(self, name: str, call, expected: str, exception=None) -> None:
        try:
            call()
        except exception or self.module["AdmissionError"] as error:
            require(expected in str(error), f"{name}: noncausal rejection: {error}")
            self.record(name, "rejected", str(error))
        else:
            raise RuntimeError(name + ": mutation was accepted")

    def file(self, name: str, raw: bytes) -> Path:
        path = self.root / name
        require(path.parent == self.root and not path.exists() and not path.is_symlink(), "fixture slot is spent")
        require(fixture_usage(self.root) + len(raw) <= MAX_CONTROL_BYTES, "control materialization cap exceeded")
        with path.open("xb") as stream:
            stream.write(raw)
        return path

    def process(self, name: str, argv: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
        remaining = min(10, self.deadline - time.monotonic())
        require(remaining > 0, "control deadline expired")
        q = subprocess.run(argv, env=env, capture_output=True, timeout=remaining, cwd=self.root)
        require(len(q.stdout) + len(q.stderr) <= 65536, "control output budget exceeded")
        self.file(name + ".stdout", q.stdout)
        self.file(name + ".stderr", q.stderr)
        self.file(name + ".json", (json.dumps({"argv": argv, "exit": q.returncode,
                                               "stdout_sha256": hashlib.sha256(q.stdout).hexdigest(),
                                               "stderr_sha256": hashlib.sha256(q.stderr).hexdigest()},
                                              sort_keys=True, indent=2) + "\n").encode())
        return q

    def fragment(self, block: str, mode: str, *, normal=0, optimized=0, build=0, cross=2, missing=None):
        self.serial += 1
        name = f"dispatch-{self.serial:03d}"
        trace = self.root / (name + ".trace")
        prelude = '''#!/bin/bash
set -euo pipefail
python3() {
  printf '%s\\n' "$*" >> "$TRACE"
  if [[ "$*" == *"build-source-coupling-compression-pdf.py"* ]]; then
    if [[ "$*" == *"--cross-toolchain"* ]]; then return "$CROSS_RESULT"; fi
    return "$BUILD_RESULT"
  fi
  if [[ "$*" == *"-O"* ]]; then return "$OPTIMIZED_RESULT"; fi
  return "$NORMAL_RESULT"
}
'''
        script = self.file(name + ".sh", (prelude + block + "\n").encode())
        env = {"PATH": "/usr/bin:/bin", "MODE": mode, "TRACE": str(trace),
               "NORMAL_RESULT": str(normal), "OPTIMIZED_RESULT": str(optimized),
               "BUILD_RESULT": str(build), "CROSS_RESULT": str(cross),
               "PID_RS_SOURCE_COUPLING_PYTHON": "python3",
               "PID_RS_SOURCE_COUPLING_TEX_ROOT": "/declared/tex",
               "PID_RS_SOURCE_COUPLING_WORK_DIR": "/declared/build",
               "PID_RS_SOURCE_COUPLING_DEADLINE": "123.5",
               "PID_RS_SOURCE_COUPLING_CONTROL_NORMAL": "/declared/normal",
               "PID_RS_SOURCE_COUPLING_CONTROL_OPTIMIZED": "/declared/optimized",
               "PID_RS_SOURCE_COUPLING_CONTROL_DEADLINE": "120.5"}
        if missing is not None:
            env.pop(missing)
        q = self.process(name, ["/bin/bash", str(script)], env)
        calls = trace.read_text().splitlines() if trace.exists() else []
        return q, calls

    def exact_contract(self, block: str) -> None:
        q, calls = self.fragment(block, "--exact")
        require(q.returncode == 0 and not q.stderr and len(calls) == 3, "exact dispatch call count differs")
        require(calls[0].startswith("-I -B scripts/check-") and "--work-dir /declared/normal" in calls[0],
                "normal control dispatch differs")
        require(calls[1].startswith("-O -I -B scripts/check-") and "--work-dir /declared/optimized" in calls[1],
                "optimized control dispatch differs")
        require("--check --tex-root /declared/tex --work-dir /declared/build --deadline 123.5" in calls[2],
                "exact leaf mode or bindings differ")
        for key, count in (("normal", 1), ("optimized", 2), ("build", 3)):
            q, calls = self.fragment(block, "--exact", **{key: 7})
            require(q.returncode == 7 and len(calls) == count, key + " failure was swallowed")
        q, calls = self.fragment(block, "--inventory-only")
        require(q.returncode == 0 and not calls, "inventory mode executed a leaf")

    def cross_contract(self, block: str) -> None:
        q, calls = self.fragment(block, "--cross-toolchain", cross=2)
        require(q.returncode == 0 and not q.stderr and len(calls) == 1 and "--cross-toolchain" in calls[0],
                "cross refusal dispatch differs")
        for status in (0, 1, 7):
            q, calls = self.fragment(block, "--cross-toolchain", cross=status)
            require(q.returncode == 1 and len(calls) == 1 and q.stderr,
                    "cross refusal accepted wrong status")


def dispatch_controls(c: Controls, gate: str) -> None:
    wiring(gate)
    c.record("current inventory and dispatch wiring", "positive")
    c.exact_contract(EXACT)
    c.record("actual exact fragment propagates every child failure and excludes inventory mode", "positive")
    c.cross_contract(CROSS)
    c.record("actual cross fragment admits only status 2 refusal", "positive")
    for suffix in ("PYTHON", "TEX_ROOT", "WORK_DIR", "DEADLINE", "CONTROL_NORMAL", "CONTROL_OPTIMIZED", "CONTROL_DEADLINE"):
        variable = "PID_RS_SOURCE_COUPLING_" + suffix
        q, calls = c.fragment(PREFLIGHT + "\n" + EXACT, "--exact", missing=variable)
        require(q.returncode != 0 and not calls and variable.encode() in q.stderr,
                "missing prerequisite reached execution: " + variable)
        c.record("actual missing prerequisite " + suffix, "rejected")
    for name, old, new, expected in (
        ("missing exact invocation", EXACT.splitlines()[4], "  :", "exact dispatch"),
        ("missing source inventory", '  "' + SOURCE + '"\n', "", "inventory"),
        ("missing PDF inventory", '  "' + STEM + '"\n', "", "inventory"),
        ("missing normal controls", EXACT.splitlines()[2], "  :", "exact dispatch"),
        ("missing optimized controls", EXACT.splitlines()[3], "  :", "exact dispatch"),
        ("wrong exact flag", "--check --tex-root", "--cross-toolchain --tex-root", "exact dispatch"),
        ("swallowed exact error", EXACT.splitlines()[4], EXACT.splitlines()[4] + " || true", "exact dispatch"),
        ("hardcoded cross status", "SOURCE_COUPLING_CROSS_STATUS=$?", "SOURCE_COUPLING_CROSS_STATUS=2", "cross refusal"),
        ("wrong refusal comparison", '"$SOURCE_COUPLING_CROSS_STATUS" -ne 2', '"$SOURCE_COUPLING_CROSS_STATUS" -ne 1', "cross refusal"),
    ):
        require(old in gate, "missing mutation anchor: " + name)
        changed = gate.replace(old, new, 1)
        c.file("wiring-" + str(len(c.cases)) + ".sh", changed.encode())
        c.reject(name, lambda changed=changed: wiring(changed), expected, RuntimeError)
    # Execute changed fragments as well: these controls do not rely only on spelling.
    c.reject("removed dispatch changes actual trace", lambda: c.exact_contract(EXACT.replace(EXACT.splitlines()[4], "  :")),
             "exact dispatch call count", RuntimeError)
    c.reject("swallowed build failure changes actual outcome",
             lambda: c.exact_contract(EXACT.replace(EXACT.splitlines()[4], EXACT.splitlines()[4] + " || true")),
             "build failure was swallowed", RuntimeError)
    c.reject("wrong mode changes actual call",
             lambda: c.exact_contract(EXACT.replace("--check --tex-root", "--cross-toolchain --tex-root")),
             "exact dispatch call count", RuntimeError)
    c.reject("wrong cross status comparison changes actual outcome",
             lambda: c.cross_contract(CROSS.replace('"$SOURCE_COUPLING_CROSS_STATUS" -ne 2',
                                                   '"$SOURCE_COUPLING_CROSS_STATUS" -ne 1')),
             "cross refusal dispatch differs", RuntimeError)
    flags = [sys.executable, *(["-O"] if sys.flags.optimize else []), "-I", "-S", "-B", str(BUILDER)]
    refusal = c.process("early-cross", [*flags, "--cross-toolchain"], {"PATH": ""})
    require(refusal.returncode == 2 and not refusal.stderr and b"zero build credit" in refusal.stdout,
            "early refusal read prerequisites or accepted a build")
    c.record("real leaf cross refusal precedes parser/tools/inputs", "rejected")
    for number, args in enumerate(([], ["--check", "--cross-toolchain"],
                                    ["--cross-toolchain", "--work-dir", "/absent"], ["--wrong-mode"])):
        q = c.process(f"wrong-mode-{number}", [*flags, *args], {"PATH": ""})
        require(q.returncode == 2 and q.stderr and not q.stdout, "invalid mode was not rejected")
        c.record("real leaf invalid mode " + str(number), "rejected")


def controller_controls(c: Controls) -> None:
    m = c.module
    raw = (ROOT / SOURCE).read_bytes()
    pin = m["INPUTS"][SOURCE]
    original = c.file("canonical-source.md", raw)
    require(m["checked_file"](original, pin) == raw, "canonical source control failed")
    c.record("exact source fixture", "positive")
    changed = c.file("changed-source.md", raw.replace(b"Source partitions", b"Source partitionz", 1))
    c.reject("real changed source", lambda: m["checked_file"](changed, pin), "input digest differs")
    symbolic = c.root / "symbolic-source.md"
    symbolic.symlink_to(original.name)
    c.reject("symbolic source", lambda: m["checked_file"](symbolic, pin), "symbolic path")
    c.reject("symbolic output", lambda: m["tree_usage"](c.root), "nonregular output")
    for name, altered in (("boolean size", {**pin, "bytes": True}),
                          ("wrong size", {**pin, "bytes": pin["bytes"] - 1}),
                          ("wrong digest", {**pin, "sha256": "0" * 64})):
        c.reject(name, lambda altered=altered: m["checked_file"](original, altered),
                 "invalid pin size" if name == "boolean size" else "input size differs" if name == "wrong size" else "input digest differs")
    for value in ("../outside", "/absolute", "a/../b", "./a"):
        c.reject("unsafe input " + value, lambda value=value: m["relative_path"](value), "unsafe relative input")
    c.reject("spent work directory", lambda: m["fresh_directory"](c.root), "already exists")
    c.reject("expired deadline", lambda: m["deadline_check"](time.monotonic() - 1), "expired")
    c.reject("infinite deadline", lambda: m["deadline_check"](float("inf")), "nonfinite")
    c.reject("deadline extension", lambda: m["deadline_check"](time.monotonic() + 1000, initial=True), "window")
    for first, second, committed, reason in ((b"a", b"b", b"a", "fresh PDF builds differ"),
                                             (b"a", b"a", b"b", "committed PDF differs")):
        c.reject(reason, lambda first=first, second=second, committed=committed:
                 m["check_pdf_relation"](first, second, committed), reason)
    env = {"PATH": "/usr/bin:/bin"}
    native = c.root / "child-controls"
    native.mkdir()
    for name, code, reason in (
        ("nonzero", "import sys; print('failed'); sys.exit(7)", "exited 7"),
        ("stderr", "import sys; print('warning', file=sys.stderr)", "wrote stderr"),
        ("overflow", "import os; os.write(1, b'x' * 600000)", "log budget exceeded"),
    ):
        c.reject("actual child " + name,
                 lambda name=name, code=code: m["run_child"]([sys.executable, "-I", "-S", "-B", "-c", code],
                                                            native, env, name, native, c.deadline), reason)
        record = json.loads((native / (name + ".json")).read_text())
        require(record["terminal"] and record["failure"], "failed child has no terminal receipt")
    c.reject("actual child deadline", lambda: m["run_child"](
        [sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(5)"], native, env,
        "timeout", native, time.monotonic() + 0.1), "timed out")
    require(json.loads((native / "timeout.json").read_text())["terminal"], "timeout child was not reaped")
    for line in ("LaTeX Warning: bad reference", "Package microtype Warning: bad font",
                 "Underfull \\vbox", "Overfull \\hbox", "Missing character: x", "! Undefined control sequence."):
        require(m["DIAGNOSTIC"].search(line) is not None, "missed final log diagnostic")
        c.record("native log predicate: " + line, "rejected")


def fixture_usage(root: Path) -> int:
    """Count retained hostile links without following them; production scan stays unchanged."""
    total = 0
    for p in root.rglob("*"):
        if p.is_symlink():
            total += len(os.readlink(p).encode())
        elif p.is_file():
            total += p.stat().st_size
    require(total <= MAX_CONTROL_BYTES, "control materialization cap exceeded")
    return total


def pdf_controls(c: Controls) -> None:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, FloatObject, NameObject, TextStringObject

    m = c.module
    raw = (ROOT / m["PDF"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == m["PDF_PIN"]["sha256"], "selected PDF identity differs")
    baseline = m["validate_pdf"](raw)
    c.record("real selected PDF semantics", "positive", baseline)

    def mutate(name: str, change, expected: str):
        writer = PdfWriter(clone_from=io.BytesIO(raw))
        writer.pdf_header = "%PDF-1.7"
        change(writer)
        target = io.BytesIO()
        writer.write(target)
        payload = target.getvalue()
        c.file("pdf-" + name + ".pdf", payload)
        c.reject("real PDF " + name, lambda: m["validate_pdf"](payload), expected)

    for field, expected in (("Author", "author"), ("Title", "title"), ("Subject", "subject"),
                            ("Creator", "creator")):
        mutate(field.lower(), lambda w, field=field: w.add_metadata({"/" + field: "altered"}),
               "PDF " + expected + " differs")
    mutate("producer", lambda w: w.add_metadata({"/Producer": "altered"}), "PDF producer is present")
    mutate("open-action", lambda w: w._root_object.__setitem__(NameObject("/OpenAction"), DictionaryObject({
        NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject("https://example.org/")})),
        "unadmitted open action")
    mutate("metadata-key", lambda w: w.add_metadata({"/Unexpected": "altered"}), "unexpected PDF metadata")
    mutate("page-count", lambda w: w.add_blank_page(width=595.276, height=841.89), "page count differs")
    mutate("page-box", lambda w: w.pages[0].__setitem__(NameObject("/MediaBox"),
           ArrayObject([FloatObject(0), FloatObject(0), FloatObject(612), FloatObject(792)])), "not A4")
    mutate("tagged", lambda w: w._root_object.__setitem__(NameObject("/MarkInfo"),
           DictionaryObject({NameObject("/Marked"): BooleanObject(True)})), "tagging profile differs")

    def first_font(writer):
        for page in writer.pages:
            for font in page["/Resources"].get("/Font", {}).get_object().values():
                font = font.get_object()
                if font.get("/Subtype") == "/Type0":
                    return font
        raise RuntimeError("no Type0 font for mutation")

    mutate("unicode", lambda w: first_font(w).__delitem__("/ToUnicode"), "font has no ToUnicode")

    def remove_embedding(writer):
        descriptor = first_font(writer)["/DescendantFonts"][0].get_object()["/FontDescriptor"].get_object()
        for key in ("/FontFile", "/FontFile2", "/FontFile3"):
            if key in descriptor:
                del descriptor[key]

    mutate("embedding", remove_embedding, "font is not embedded")
    for key in ("/JavaScript", "/AA", "/EmbeddedFiles", "/AcroForm"):
        mutate(key[1:].lower(), lambda w, key=key: w._root_object.__setitem__(NameObject(key), DictionaryObject()),
               "forbidden PDF action or payload key")

    def replace_action(writer, action):
        for page in writer.pages:
            for annotation in page.get("/Annots", []):
                obj = annotation.get_object()
                if "/A" in obj:
                    obj[NameObject("/A")] = action
                    return
        raise RuntimeError("no action available for mutation")

    mutate("launch", lambda w: replace_action(w, DictionaryObject({NameObject("/S"): NameObject("/Launch")})),
           "unadmitted PDF action")
    for name, target, expected in (("file-uri", "file:///private/report.pdf", "private or file URI"),
                                   ("private-uri", "https://example.org/.local/report", "private or file URI"),
                                   ("unknown-uri", "ftp://example.org/report", "unadmitted URI scheme")):
        mutate(name, lambda w, target=target: replace_action(w, DictionaryObject({
            NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject(target)})), expected)
    mutate("broken-destination", lambda w: replace_action(w, DictionaryObject({
        NameObject("/S"): NameObject("/GoTo"), NameObject("/D"): TextStringObject("missing-destination")})),
        "unknown named destination")
    c.file("truncated.pdf", raw[:100])
    try:
        m["validate_pdf"](raw[:100])
    except Exception as error:
        require("EOF" in str(error) or "Stream has ended" in str(error), "truncation failed noncausally")
        c.record("real truncated PDF", "rejected", str(error))
    else:
        raise RuntimeError("truncated PDF was accepted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dispatch-only", action="store_true")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    module = runpy.run_path(str(BUILDER), run_name="source_coupling_controls")
    result = {"schema": "pid-rs-source-coupling-pdf-controls-v1", "accepted": False,
              "optimized": bool(sys.flags.optimize), "dispatch_only": args.dispatch_only,
              "scope": "causal controller/PDF/dispatch fixtures; no native reproduction or scientific acceptance"}
    work = None
    controls = None
    try:
        require(args.dispatch_only or (args.work_dir is not None and args.deadline is not None),
                "full controls require --work-dir and --deadline")
        deadline = args.deadline if args.deadline is not None else time.monotonic() + 60
        module["deadline_check"](deadline, initial=True)
        if args.work_dir is None:
            work = Path(tempfile.mkdtemp(prefix="pid-rs-source-coupling-dispatch-")).resolve()
        else:
            work = module["fresh_directory"](args.work_dir)
        before = BUILDER.read_bytes(), GATE.read_bytes(), Path(__file__).read_bytes()
        require(not any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(before[0]))),
                "production guard uses assert")
        controls = Controls(work, module, deadline)
        dispatch_controls(controls, before[1].decode())
        if not args.dispatch_only:
            module["parser_identity"]()
            controller_controls(controls)
            pdf_controls(controls)
        require(before == (BUILDER.read_bytes(), GATE.read_bytes(), Path(__file__).read_bytes()),
                "controller source changed during controls")
        result.update(accepted=True, cases=controls.cases,
                      work_bytes=fixture_usage(work), controller_sha256=hashlib.sha256(before[0]).hexdigest(),
                      gate_sha256=hashlib.sha256(before[1]).hexdigest())
        print(json.dumps({key: value for key, value in result.items() if key != "cases"}, sort_keys=True))
        return 0
    except Exception as error:
        result.update(failure=f"{type(error).__name__}: {error}", cases=controls.cases if controls else [])
        print("source-coupling PDF controls: " + result["failure"], file=sys.stderr)
        return 1
    finally:
        if work is not None:
            with (work / "result.json").open("x") as stream:
                json.dump(result, stream, sort_keys=True, indent=2)
                stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
