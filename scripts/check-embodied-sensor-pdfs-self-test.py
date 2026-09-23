#!/usr/bin/env python3
"""Finite inert controls for the two-kind publication source/data boundary.

No renderer, SVG/XML/PDF parser, reader import, native tool or proof is run.
The Lua checks concern literal wiring; they do not execute Pandoc's Lua engine.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import copy
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time
from types import ModuleType

BUILDER = "scripts/build-embodied-sensor-pdfs.py"
MANIFEST = "audit/formal/latex/embodied-sensor-utility/publication-inputs-v1.json"
FILTER = "audit/formal/latex/embodied-sensor-utility/layout/publication-filter.lua"
ROSTER = "audit/formal/latex/embodied-sensor-utility/controls/roster-v1.json"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = path.absolute()
    require(path == path.resolve(strict=True), "noncanonical control input")
    before = path.lstat()
    cap = 32 * 1024**2
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= cap,
            "control input is not a direct single-link file")
    fields = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
                         s.st_mtime_ns, s.st_ctime_ns)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        opened = os.fstat(descriptor)
        require(stat.S_ISREG(opened.st_mode) and opened.st_size <= cap
                and fields(opened) == fields(before), "control input changed before read")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(cap+1)
        require(fields(before) == fields(os.fstat(descriptor)) == fields(path.lstat())
                and len(raw) == before.st_size and len(raw) <= cap,
                "control input changed during read")
        return raw
    finally:
        os.close(descriptor)


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(RuntimeError("nonfinite JSON")))


def main():
    entry_utc, entry_mono = dt.datetime.now(dt.timezone.utc), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--registration-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-monotonic-deadline", type=float, required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.ignore_environment
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "controls require -I -S -B, optionally -O")
    root, output = args.root.absolute(), args.output.absolute()
    require(root == root.resolve(strict=True) and root.is_dir()
            and output.parent == output.parent.resolve(strict=True),
            "control root or output parent is not canonical")
    require(not output.exists() and not output.is_symlink(), "control output exists")
    reg_raw = read(args.registration)
    require(digest(reg_raw) == args.registration_sha256, "registration hash differs")
    reg = strict(reg_raw)
    fields = {"schema", "status", "root", "output", "optimization", "registered_utc",
              "deadline_utc", "builder_sha256", "self_test_sha256", "manifest_sha256",
              "roster_sha256", "python_sha256", "maximum_cases", "stage_monotonic_deadline"}
    require(type(reg) is dict and set(reg) == fields
            and reg["schema"] == "pid-rs/embodied-sensor-publication-controls-v1"
            and reg["status"] == "reviewed-source-ready-for-inert-controls",
            "control registration fields/status differ")
    require(reg["root"] == str(root) and reg["output"] == str(output)
            and type(reg["optimization"]) is int and reg["optimization"] == sys.flags.optimize,
            "control command binding differs")
    start, deadline = (dt.datetime.fromisoformat(reg[key]) for key in ("registered_utc", "deadline_utc"))
    require(start.utcoffset() == dt.timedelta(0) and deadline.utcoffset() == dt.timedelta(0)
            and start <= entry_utc < deadline
            and (deadline-start).total_seconds() <= 1200, "original control deadline differs")
    require(type(reg["stage_monotonic_deadline"]) is float
            and reg["stage_monotonic_deadline"] == args.stage_monotonic_deadline
            and math.isfinite(args.stage_monotonic_deadline)
            and entry_mono < args.stage_monotonic_deadline <= entry_mono+1200,
            "original control monotonic endpoint differs")
    mono_end = min(args.stage_monotonic_deadline,
                   entry_mono + (deadline-entry_utc).total_seconds())
    source, own = read(root / BUILDER), read(Path(__file__).absolute())
    manifest_raw, roster_raw = read(root / MANIFEST), read(root / ROSTER)
    require(digest(source) == reg["builder_sha256"] and digest(own) == reg["self_test_sha256"]
            and digest(manifest_raw) == reg["manifest_sha256"]
            and digest(roster_raw) == reg["roster_sha256"]
            and digest(read(Path(sys.executable).resolve(strict=True))) == reg["python_sha256"],
            "registered control source binding differs")
    b = ModuleType("mgw_note_builder_under_inert_controls")
    b.__file__ = str(root / BUILDER)
    exec(compile(source, b.__file__, "exec", dont_inherit=True,
                 optimize=sys.flags.optimize), b.__dict__)
    manifest, roster = strict(manifest_raw), strict(roster_raw)
    require(type(roster) is dict and set(roster) == {"schema", "cases"}
            and roster["schema"] == "pid-rs/embodied-sensor-publication-control-roster-v1",
            "control roster schema differs")
    b.admit_manifest(manifest, "full", False)
    captured_inputs = {relative: read(root / relative) for relative in manifest["files"]}
    for relative, expected in manifest["files"].items():
        b.check_entry(captured_inputs[relative], expected, relative)
    filter_raw = read(root / FILTER)
    cases = []
    def add(name, call, rejection=None):
        cases.append((name, call, rejection))
    def changed_manifest(key, value):
        result = copy.deepcopy(manifest)
        result[key] = value
        return result
    def unbound():
        result = copy.deepcopy(manifest)
        for kind in b.KINDS:
            result["outputs"][kind] = {"status": "unbound", "tex": None, "pdf": None,
                                       "observation": None, "figure_pdfs": None}
        return result
    add("discovery-full", lambda: b.admit_manifest(unbound(), "full", False))
    add("discovery-overview", lambda: b.admit_manifest(unbound(), "overview", False))
    add("unknown-kind", lambda: b.admit_manifest(unbound(), "other", False), "unknown publication kind")
    add("exact-unbound-full", lambda: b.admit_manifest(unbound(), "full", True), "unbound reference")
    add("exact-unbound-overview", lambda: b.admit_manifest(unbound(), "overview", True), "unbound reference")
    add("wrong-manifest-schema", lambda: b.admit_manifest(
        changed_manifest("schema", "wrong"), "full", False), "manifest schema")
    add("extra-manifest-field", lambda: b.admit_manifest(
        dict(unbound(), extra=1), "full", False), "manifest schema")
    missing = copy.deepcopy(manifest["files"])
    missing.pop(b.FIGURES["figures/sensor-data-to-evidence.svg"])
    add("missing-source", lambda: b.admit_manifest(
        changed_manifest("files", missing), "full", False), "source inventory")
    extra = dict(manifest["files"], unexpected={"bytes": 0, "sha256": "0"*64})
    add("extra-source", lambda: b.admit_manifest(
        changed_manifest("files", extra), "full", False), "source inventory")
    invented = unbound()
    invented["outputs"]["full"]["pdf"] = {"bytes": 0, "sha256": "0"*64}
    add("invented-unbound-output", lambda: b.admit_manifest(
        invented, "full", False), "invented observations")
    partial = unbound()
    partial["outputs"]["full"]["status"] = "reviewed-reference"
    add("partial-reference", lambda: b.admit_manifest(
        partial, "full", True), "lacks actual observations")
    positive = {"bytes": 3, "sha256": digest(b"abc")}
    add("pinned-bytes-positive", lambda: b.check_entry(b"abc", positive, "inert"))
    add("changed-byte", lambda: b.check_entry(b"abd", positive, "inert"), "pinned bytes differ")
    add("changed-length", lambda: b.check_entry(b"ab", positive, "inert"), "pinned bytes differ")
    add("boolean-size", lambda: b.check_entry(
        b"a", {"bytes": True, "sha256": digest(b"a")}, "inert"), "pinned bytes differ")
    add("extra-entry-field", lambda: b.check_entry(b"abc", dict(positive, extra=1), "inert"), "pinned bytes differ")
    add("relative-path-positive", lambda: b.portable("audit/research/note.md"))
    for label, value in (("empty", ""), ("dot", "."), ("absolute", "/tmp/x"), ("parent", "../x"),
                         ("embedded-parent", "a/../b"), ("doubled-slash", "a//b"),
                         ("dot-segment", "a/./b"), ("backslash", "a\\b"), ("newline", "a\nb")):
        add("relative-path-"+label, lambda value=value: b.portable(value), "path")
    add("tool-selector-positive", lambda: b.tool_selector("pandoc", "/bounded/bin/pandoc"))
    for label, name, value in (("unknown", "other", "/bounded/bin/other"),
                               ("relative", "pandoc", "bin/pandoc"),
                               ("wrong-leaf", "pandoc", "/bounded/bin/lualatex"),
                               ("newline", "pandoc", "/bad\n/bin/pandoc"),
                               ("search-separator", "pandoc", "/bad:/bin/pandoc"),
                               ("wrong-type", "pandoc", 7)):
        add("tool-selector-"+label, lambda name=name, value=value: b.tool_selector(name, value), "selector")
    add("local-link-positive", lambda: require(
        b.mapped_link("../../../MATHEMATICAL_RESULTS_GUIDE.md") ==
        "https://github.com/sepahead/pid-rs/blob/main/MATHEMATICAL_RESULTS_GUIDE.md",
        "local link did not map to its canonical source"))
    add("primary-link-positive", lambda: require(
        b.mapped_link("https://doi.org/10.1103/PhysRevE.103.032149") ==
        "https://doi.org/10.1103/PhysRevE.103.032149", "primary link changed"))
    for label, value in (("http", "http://example.org"), ("javascript", "javascript:alert(1)"),
                         ("unlisted-https", "https://example.org"), ("absolute", "/tmp/paper.md"),
                         ("unlisted-parent", "../../../other.md"), ("unlisted-anchor", "#other")):
        add("link-"+label, lambda value=value: b.mapped_link(value), "not enumerated")
    def filter_wiring():
        text = filter_raw.decode()
        local_section = text.split("local local_links = {", 1)[1].split("local external_links = {", 1)[0]
        local = dict(re.findall(r'\["([^"]+)"\] = "([^"]+)"', local_section))
        external = set(re.findall(r'\["([^"]+)"\] = true', text))
        require(local == b.LOCAL_LINKS and external == b.EXTERNAL_LINKS,
                "literal Lua/Python link rosters differ")
        figure_section = text.split("local figure_map = {", 1)[1].split("local kind,", 1)[0]
        figure_map = dict(re.findall(r'\["([^"]+)"\] = "([^"]+)"', figure_section))
        require(figure_map == {name: str(Path(name).with_suffix(".pdf")) for name in b.FIGURES}
                and 'kind == "overview" and element.src ~= "figures/signed-atoms-and-sensor-value.svg"' in text
                and 'kind == "full" and 3 or 1' in text
                and '{Meta = metadata}' in text and '{Pandoc = complete}' in text
                and "pandoc.WriterOptions{wrap_text='none'}" in text
                and "pandoc.write(pandoc.Pandoc({e}),'latex',options)" in text
                and 'Table writer returned a complete document' in text,
                "finite figure or metadata/completion wiring differs")
    add("literal-filter-wiring", filter_wiring)
    fixed = dt.datetime(2026, 9, 13, tzinfo=dt.timezone.utc)
    binding = {"kind": "full", "mode": "discovery", "root": "/owned/root",
               "work_dir": "/owned/run", "optimization": 0, "manifest_sha256": "a"*64,
               "builder_sha256": "b"*64, "python_sha256": "c"*64,
               "stage_monotonic_deadline": 11200.0}
    good_reg = dict(binding, schema="pid-rs/embodied-sensor-publication-execution-v1",
                    status="reviewed-source-ready-for-discovery",
                    registered_utc=fixed.isoformat(),
                    deadline_utc=(fixed+dt.timedelta(seconds=600)).isoformat(),
                    stage_started_utc=fixed.isoformat(),
                    stage_deadline_utc=(fixed+dt.timedelta(seconds=1200)).isoformat(),
                    maximum_builds=2, maximum_commands=66,
                    tool_selectors={name: "/owned/bin/"+name for name in b.TOOLS},
                    reader_directory="/owned/reader")
    add("registration-positive", lambda: b.admit_registration(good_reg, binding, fixed, 10000.0))
    for label, key, value, message in (
        ("source", "builder_sha256", "d"*64, "source binding"),
        ("mode", "optimization", 1, "source binding"),
        ("boolean-mode", "optimization", False, "source binding"),
        ("commands", "maximum_commands", 67, "command budget"),
        ("deadline", "deadline_utc", fixed.isoformat(), "chronology"),
        ("renewed-window", "stage_deadline_utc", (fixed+dt.timedelta(hours=2)).isoformat(), "chronology"),
    ):
        add("registration-"+label, lambda key=key, value=value:
            b.admit_registration(dict(good_reg, **{key: value}), binding, fixed, 10000.0), message)
    add("registration-monotonic-binding", lambda: b.admit_registration(
        dict(good_reg, stage_monotonic_deadline=11800.0), binding, fixed, 10000.0), "source binding")
    add("registration-monotonic-expired", lambda: b.admit_registration(
        good_reg, binding, fixed, 11200.0), "monotonic endpoint")
    def file_input(label, raw, cap):
        target = output / (label+".txt")
        with target.open("xb") as stream:
            stream.write(raw)
        require(b.read_direct(target, cap) == raw, "bounded direct input changed")
    add("bounded-input-positive", lambda: file_input("small", b"abc", 3))
    add("bounded-input-size-refusal", lambda: file_input("oversize", b"abcd", 3), "regular file")
    def fifo_refusal():
        target = output / "inert-fifo"
        os.mkfifo(target, 0o600)
        try:
            b.read_direct(target, 3)
        finally:
            target.unlink()
    add("bounded-input-fifo-refusal", fifo_refusal, "regular file")
    starts = []
    def forbidden(*args, **kwargs):
        starts.append("forbidden production path")
        raise RuntimeError("control attempted external or parser work")
    b.load_runtime = forbidden
    b.pinned_reader = forbidden
    observe_inert = b.observe_pdf
    b.observe_pdf = forbidden
    def cross(kind):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = b.main(["--kind", kind, "--cross-toolchain"])
        require(code == 2 and not out.getvalue() and "status 2 refusal" in err.getvalue()
                and not starts, "cross request entered production")
    add("cross-full-before-admission", lambda: cross("full"))
    add("cross-overview-before-admission", lambda: cross("overview"))
    # Exercise the same combined byte/observation predicate used by exact production.
    # These are inert JSON-shaped fixtures; no PDF parser or native producer runs.
    for kind in b.KINDS:
        # Deliberately inert typed fixture: no real output reference exists yet.
        observation = {"kind": kind, "pages": 1, "first_page_fit": True,
                       "scope": "synthetic control, not an adopted PDF observation"}
        add("reference-"+kind+"-positive", lambda observation=observation:
            b.check_reference(b"same", b"same", observation, copy.deepcopy(observation)))
    observation = {"pages": 13, "first_page_fit": True,
                   "headings": [{"page": 1, "level": 0}],
                   "values": [0.0, "caption", None]}
    add("typed-observation-positive", lambda:
        b.check_reference(b"same", b"same", observation, copy.deepcopy(observation)))
    def changed_observation(path, replacement):
        changed = copy.deepcopy(observation)
        parent = changed
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = replacement
        return changed
    for label, path, replacement in (
        ("page-count-float", ("pages",), 13.0),
        ("first-page-fit-integer", ("first_page_fit",), 1),
        ("nested-level-boolean", ("headings", 0, "level"), False),
        ("nested-page-float", ("headings", 0, "page"), 1.0),
        ("nested-float-integer", ("values", 0), 0),
        ("list-tuple", ("values",), (0.0, "caption", None)),
        ("missing-list-item", ("values",), [0.0, "caption"]),
        ("reordered-list", ("values",), [None, "caption", 0.0]),
        ("changed-string", ("values", 1), "different"),
        ("null-integer", ("values", 2), 0),
    ):
        changed = changed_observation(path, replacement)
        add("typed-observation-"+label, lambda changed=changed:
            b.check_reference(b"same", b"same", observation, changed), "typed observation differ")
    observation_missing = copy.deepcopy(observation)
    del observation_missing["pages"]
    add("typed-observation-missing-key", lambda:
        b.check_reference(b"same", b"same", observation, observation_missing), "typed observation differ")
    add("typed-observation-extra-key", lambda:
        b.check_reference(b"same", b"same", observation, dict(observation, extra=0)),
        "typed observation differ")
    add("reference-pdf-byte-change", lambda:
        b.check_reference(b"changed", b"same", observation, observation), "reference bytes")
    for label, value in (("nan", float("nan")), ("infinity", float("inf")),
                         ("negative-infinity", float("-inf"))):
        add("typed-observation-"+label, lambda value=value:
            b.check_reference(b"same", b"same", {"x": value}, {"x": value}),
            "typed observation differ")
    # Exercise the actual observer through a finite in-memory stub. The fake
    # factory consumes no PDF syntax and cannot import or call a real reader.
    class ReaderText(str):
        pass
    class ReaderName(str):
        pass
    class OverriddenText(str):
        def __str__(self):
            return "different display text"
    class NonText:
        def __str__(self):
            return "alpha"
    class Direct(dict):
        def get_object(self):
            return self
    class Reference:
        idnum, generation = 1, 0
    class Box:
        width, height = 595.276, 841.89
    class Page:
        mediabox = Box()
        indirect_reference = Reference()
        def extract_text(self):
            return "inert text"
    def observed_names(names, mutation=None):
        page = Page()
        catalog = Direct({"/Lang": "en", "/OpenAction": Direct({
            "/S": "/GoTo", "/D": [page.indirect_reference, "/Fit"]})})
        reader = ModuleType("inert_reader_result")
        reader.is_encrypted, reader.pages = False, [page]
        reader.trailer = {"/Root": catalog}
        reader.named_destinations = {name: None for name in names}
        if mutation is not None:
            mutation(reader)
        fake = ModuleType("inert_reader_factory")
        fake.generic = ModuleType("inert_reader_generic")
        fake.generic.IndirectObject = type("UnusedIndirectObject", (), {})
        calls = []
        raw = b"%PDF-1.7\ninert fixture, not a PDF"
        def factory(stream, *, strict):
            require(type(strict) is bool and strict and stream.read() == raw,
                    "inert reader arguments differ")
            calls.append("inert factory")
            return reader
        fake.PdfReader = factory
        observed = observe_inert(fake, raw, b"inert text\n\f", b"inert bbox",
                                 "header\nseparator\nInert CID Type 0 Identity-H yes yes yes 1 0")
        require(calls == ["inert factory"], "inert reader call count differs")
        return observed
    def expected_names(names):
        return {"pages": 1, "geometry": [[595.276, 841.89]], "headings": [],
                "https_uris": [], "gotos": [], "named_destinations": names,
                "root_keys": ["/Lang", "/OpenAction"],
                "pypdf_text_sha256": [digest(b"inert text")],
                "poppler_layout_sha256": digest(b"inert text\n\f"),
                "poppler_bbox_sha256": digest(b"inert bbox"),
                "font_rows": ["Inert CID Type 0 Identity-H yes yes yes 1 0"],
                "first_page_fit": True}
    for label, names, expected in (
        ("native", ["zeta", "alpha"], ["alpha", "zeta"]),
        ("text-subclass", [ReaderText("zeta"), ReaderText("alpha")], ["alpha", "zeta"]),
        ("name-subclass", [ReaderName("/zeta"), ReaderName("/alpha")], ["/alpha", "/zeta"]),
        ("unicode", [ReaderText("α"), ReaderText("é"), ReaderText("e\u0301"), ReaderText("")],
         ["", "e\u0301", "é", "α"]),
        ("overridden-str", [OverriddenText("alpha")], ["alpha"]),
    ):
        add("observer-named-"+label+"-positive", lambda names=names, expected=expected:
            b.check_reference(b"same", b"same", observed_names(names), expected_names(expected)))
    def bypass_text_projection():
        original = b.reader_text
        try:
            b.reader_text = lambda value: value
            observed = observed_names([ReaderText("alpha")])
            require(type(observed["named_destinations"][0]) is ReaderText,
                    "projection bypass did not reach the original representation defect")
            b.check_reference(b"same", b"same", observed, expected_names(["alpha"]))
        finally:
            b.reader_text = original
    add("observer-named-projection-bypass", bypass_text_projection, "typed observation differ")
    for label, value in (("bytes", b"alpha"), ("integer", 1), ("float", 1.0),
                         ("boolean", True), ("null", None), ("object", NonText())):
        add("observer-named-"+label+"-refused", lambda value=value: observed_names([value]),
            "PDF reader text is not a string")
    for label, value in (("list", ["alpha"]), ("dictionary", {"alpha": None})):
        add("reader-text-"+label+"-refused", lambda value=value: b.reader_text(value),
            "PDF reader text is not a string")
    for label, names in (("subclass", [ReaderText("alpha")]), ("integer", [1]),
                         ("tuple", ("alpha",)), ("changed-text", ["changed"])):
        add("observer-expected-"+label+"-refused", lambda names=names:
            b.check_reference(b"same", b"same", observed_names([ReaderText("alpha")]),
                              expected_names(names)), "typed observation differ")
    add("observer-reference-byte-change-refused", lambda:
        b.check_reference(b"changed", b"same", observed_names([ReaderText("alpha")]),
                          expected_names(["alpha"])), "reference bytes")
    add("observer-fresh-typed-equality-positive", lambda: require(
        b.same_json_value(observed_names([ReaderText("alpha")]), observed_names(["alpha"])),
        "fresh typed observer equality differs"))
    # New finite embodiment bindings and action guards; still no real parser/native work.
    add("https-full-pdf-link", lambda: require(b.mapped_link("EXPOSITION.md") ==
        b.BASE_URL + "output/pdf/embodied-sensor-utility.pdf", "full PDF link differs"))
    add("cost-section-anchor", lambda: require(b.mapped_link(
        "EXPOSITION.md#13-rust-implementation-and-computational-cost") ==
        b.BASE_URL + "audit/research/embodied-sensor-utility/EXPOSITION.md#13-rust-implementation-and-computational-cost",
        "cost anchor differs"))
    for leaf in ("src/lib.rs", "src/sxpid.rs", "benches/estimators.rs"):
        add("rust-link-" + leaf.replace("/", "-"), lambda leaf=leaf: require(
            b.mapped_link("../../../crates/pid-core/" + leaf) == b.BASE_URL + "crates/pid-core/" + leaf,
            "Rust link differs"))
    def reviewed_shape():
        value = unbound()
        for kind in b.KINDS:
            value["outputs"][kind] = {"status": "reviewed-reference", "tex": {}, "pdf": {},
                "observation": {}, "figure_pdfs": {str(Path(name).with_suffix(".pdf")): {}
                                                    for name in b.KIND_FIGURES[kind]}}
        return value
    add("three-one-figure-shape", lambda: b.admit_manifest(reviewed_shape(), "full", True))
    wrong_figures = reviewed_shape()
    wrong_figures["outputs"]["full"]["figure_pdfs"].pop("figures/sensor-data-to-evidence.pdf")
    add("missing-full-figure-reference", lambda: b.admit_manifest(wrong_figures, "full", True), "figure output differs")
    extra_figure = reviewed_shape()
    extra_figure["outputs"]["overview"]["figure_pdfs"]["figures/sensor-data-to-evidence.pdf"] = {}
    add("extra-overview-figure-reference", lambda: b.admit_manifest(extra_figure, "overview", True), "figure output differs")
    add("finite-native-command-counts", lambda: require(
        b.same_json_value(b.COMMANDS, {"full": 66, "overview": 62})
        and b.FONT_NAMES == frozenset(["SourceSansPro-Bold.otf","SourceSansPro-Regular.otf","SourceSansPro-RegularIt.otf","SourceSansPro-Semibold.otf","SourceSansPro-SemiboldIt.otf","latinmodern-math.otf","lmmono10-italic.otf","lmmono10-regular.otf","lmmonolt10-bold.otf","lmmonolt10-boldoblique.otf","lmroman10-bold.otf","lmroman10-bolditalic.otf","lmroman10-italic.otf","lmroman10-regular.otf","lmroman12-bold.otf","lmroman12-regular.otf"])
        and set(strict(captured_inputs[b.NATIVE])["fonts"]) == b.FONT_NAMES
        and digest(captured_inputs[b.NATIVE]) == b.NATIVE_SHA256
        and strict(captured_inputs[b.NATIVE])["limits"]["maximum_commands_full"] == 66
        and strict(captured_inputs[b.NATIVE])["limits"]["maximum_commands_overview"] == 62,
        "command counts or controlled font profile differ"))
    def missing_open(reader):
        del reader.trailer["/Root"]["/OpenAction"]
    add("observer-missing-open-action", lambda: observed_names([], missing_open), "opener must target")
    def wrong_first(reader):
        other = Reference(); other.idnum = 2
        reader.trailer["/Root"]["/OpenAction"]["/D"][0] = other
    add("observer-wrong-first-page", lambda: observed_names([], wrong_first), "opener must target")
    def additional_action(reader):
        reader.trailer["/Root"]["/AA"] = Direct({})
    add("observer-additional-action", lambda: observed_names([], additional_action), "forbidden PDF action/file key")
    def remote_action(reader):
        reader.trailer["/Root"]["/A"] = Direct({"/Type": "/Action", "/S": "/GoToR",
                                                "/F": "embodied-sensor-utility.pdf"})
    add("observer-relative-external-pdf", lambda: observed_names([], remote_action), "unsupported annotation or outline action")
    def unlisted_uri(reader):
        reader.trailer["/Root"]["/A"] = Direct({"/Type": "/Action", "/S": "/URI",
                                                "/URI": "https://example.org/other.pdf"})
    add("observer-unlisted-https", lambda: observed_names([], unlisted_uri), "finite admitted action")
    names = [name for name, _, _ in cases]
    require(names == roster["cases"] and len(names) == len(set(names))
            and type(reg["maximum_cases"]) is int and reg["maximum_cases"] == len(names),
            "closed case roster or external case budget differs")
    output.mkdir(mode=0o700)
    result = {"status": "failed", "cases": [], "native_starts": 0, "pdf_parses": 0,
              "reader_imports": 0, "lua_execution": False,
              "scope": "Finite source/data controls; no production, PDF or mathematical acceptance"}
    try:
        for name, call, rejection in cases:
            require(dt.datetime.now(dt.timezone.utc) < deadline and time.monotonic() < mono_end,
                    "original control deadline exhausted")
            caught = None
            try:
                call()
            except (RuntimeError, ValueError, KeyError, TypeError) as error:
                caught = str(error)
            require((rejection is None and caught is None)
                    or (rejection is not None and caught is not None and rejection in caught),
                    name + ": unexpected control disposition: " + str(caught))
            result["cases"].append({"name": name, "expected_rejection": rejection, "observed": caught})
        require(not starts and read(root / BUILDER) == source
                and read(Path(__file__).absolute()) == own
                and read(root / MANIFEST) == manifest_raw and read(root / ROSTER) == roster_raw,
                "control source changed or forbidden work occurred")
        require(all(read(root / relative) == raw for relative, raw in captured_inputs.items()),
                "control input closure changed")
        result["status"] = "finite-inert-controls-passed"
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        result["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        b.finish(output / "RESULT.json", result, deadline, mono_end)
    print("Embodied sensor controls: " + str(len(result["cases"])) + " finite cases passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print("Embodied sensor controls failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
