#!/usr/bin/env python3
"""Fixed embodied-sensor paper and overview producer; discovery is never adoption."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import datetime as dt
import hashlib
import importlib
import io
import json
import logging
import math
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import time
from types import ModuleType
import warnings
from xml.sax.saxutils import escape

ASSETS = "audit/formal/latex/embodied-sensor-utility/"
MANIFEST = ASSETS + "publication-inputs-v1.json"
RUNTIME = "audit/formal/lean-prefix-mgw-mean/replay-support/runtime.py"
RUNTIME_SHA256 = "bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d"
NATIVE = "audit/formal/latex/embodied-sensor-utility/native-tools-v1.json"
NATIVE_SHA256 = "f3c5c6e1ca5f10b19e6c847fafd5679e4a9489eb2ed019b6283b1a0842b12cda"
READER = "audit/formal/latex/prefix-mgw-bias/reader-source-v2.json"
READER_SHA256 = "5a0474ea26892b04b6ff1c931096ee115bdfdf68adc5945644a849bea064a378"
KINDS = ("full", "overview")
SOURCES = {"full": "audit/research/embodied-sensor-utility/EXPOSITION.md",
           "overview": "audit/research/embodied-sensor-utility/OVERVIEW.md"}
OUTPUTS = {"full": "embodied-sensor-utility", "overview": "embodied-sensor-overview"}
TITLES = {"full": "Sensor information for embodied agents",
          "overview": "Wibral-line PID for physical intelligence"}
TEMPLATES = {kind: ASSETS + "layout/" + kind + ".tex" for kind in KINDS}
FIGURES = {"figures/" + name + ".svg": "audit/research/embodied-sensor-utility/figures/" + name + ".svg"
           for name in ("sensor-data-to-evidence", "signed-atoms-and-sensor-value", "availability-weighted-gain")}
KIND_FIGURES = {"full": tuple(FIGURES), "overview": ("figures/signed-atoms-and-sensor-value.svg",)}
STAGE_COMMON = {
    "layout/publication-filter.lua": ASSETS + "layout/publication-filter.lua",
    "layout/pid-rs-report-tables.sty": "audit/formal/latex/pid-rs-report-tables.sty",
    "layout/pid-rs-workflow-publication.sty": "audit/formal/latex/pid-rs-workflow-publication.sty",
    "check-formal-pdf-log.sh": "scripts/check-formal-pdf-log.sh",
}
SOURCE_OBSERVATIONS = "audit/research/embodied-sensor-utility/SOURCE_OBSERVATIONS.json"
PUBLICATION = "audit/research/embodied-sensor-utility/PUBLICATION.md"
FONT_LICENSES = (
    'audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt',
    'audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt',
    'audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt',
    'audit/formal/latex/mgw-fixed-world/font-licenses/latin-modern-math/GUST-FONT-LICENSE.txt',
    'audit/formal/latex/mgw-fixed-world/font-licenses/latin-modern-math/README-Latin-Modern-Math.txt',
    'audit/formal/latex/mgw-fixed-world/font-licenses/latin-modern-math/MANIFEST-Latin-Modern-Math.txt',
)
INPUTS = frozenset((*SOURCES.values(), *TEMPLATES.values(), *STAGE_COMMON.values(),
                    *FIGURES.values(), SOURCE_OBSERVATIONS, PUBLICATION, *FONT_LICENSES,
                    NATIVE, READER, RUNTIME))
TOOLS = frozenset(("pandoc", "lualatex", "rsvg-convert", "kpsewhich", "fc-cache",
                   "bash", "pdfinfo", "pdffonts", "pdftotext"))
FONT_NAMES = frozenset(("SourceSansPro-Bold.otf",
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
                       "lmroman12-regular.otf"))
# 33 native commands per full build and 31 per overview build; both repeat from fresh inputs.
COMMANDS = {"full": 66, "overview": 62}
MAX_WORK_BYTES = 768 * 1024**2
MAX_DIRECT_BYTES = 32 * 1024**2
FINAL_RESULT_RESERVE = 16 * 1024**2
LOCAL_LINKS = {'../../formal/lean-finite-logscore/PUBLICATION.md': 'audit/formal/lean-finite-logscore/PUBLICATION.md', '../../../MATHEMATICAL_RESULTS_GUIDE.md': 'MATHEMATICAL_RESULTS_GUIDE.md', '../finite-prefix-mgw-gradient/EXPOSITION.md': 'audit/research/finite-prefix-mgw-gradient/EXPOSITION.md', '../support-change-mi-cusp/EXPOSITION.md': 'audit/research/support-change-mi-cusp/EXPOSITION.md', '../../../ECOSYSTEM_CAPABILITIES.md': 'ECOSYSTEM_CAPABILITIES.md', '../../../PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md': 'PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md', '../../../PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md': 'PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md', '../../../crates/pid-core/src/lib.rs': 'crates/pid-core/src/lib.rs', '../../../crates/pid-core/src/sxpid.rs': 'crates/pid-core/src/sxpid.rs', '../../../crates/pid-core/benches/estimators.rs': 'crates/pid-core/benches/estimators.rs', 'EXPOSITION.md': 'output/pdf/embodied-sensor-utility.pdf', 'EXPOSITION.md#13-rust-implementation-and-computational-cost': 'audit/research/embodied-sensor-utility/EXPOSITION.md#13-rust-implementation-and-computational-cost', '../../../audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md': 'audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md', '../../../scripts/check-primegaps-to-pid-transfer-ledger.py': 'scripts/check-primegaps-to-pid-transfer-ledger.py', '../../../PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md': 'PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md', '../../../CITATION.cff': 'CITATION.cff'}
EXTERNAL_LINKS = frozenset(['https://arxiv.org/abs/1510.00831v1', 'https://arxiv.org/abs/2002.03356v5', 'https://arxiv.org/abs/2302.11813', 'https://arxiv.org/abs/2311.06373v3', 'https://doi.org/10.1080/01621459.1963.10500830', 'https://doi.org/10.1103/PhysRevE.103.032149', 'https://doi.org/10.1198/016214506000001437', 'https://proceedings.mlr.press/v270/skand25a.html', 'https://proceedings.mlr.press/v305/almuzairee25a.html'])
BASE_URL = "https://github.com/sepahead/pid-rs/blob/main/"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def same_json_value(actual: object, expected: object) -> bool:
    """Compare finite JSON trees without Python's bool/int/float coercions."""
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return (all(type(key) is str for key in actual)
                and all(type(key) is str for key in expected)
                and actual.keys() == expected.keys()
                and all(same_json_value(actual[key], expected[key]) for key in actual))
    if type(actual) is list:
        return (len(actual) == len(expected)
                and all(same_json_value(a, b) for a, b in zip(actual, expected)))
    if type(actual) is float:
        return math.isfinite(actual) and math.isfinite(expected) and actual == expected
    return type(actual) in (str, int, bool, type(None)) and actual == expected


def check_reference(pdf: bytes, reference: bytes, observation: dict, expected: dict) -> None:
    require(pdf == reference and same_json_value(observation, expected),
            "reference bytes or typed observation differ")


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def direct_directory(path: Path) -> Path:
    path = path.absolute()
    require(path == path.resolve(strict=True) and path.is_dir()
            and not any(c in str(path) for c in ("\n", "\r", os.pathsep)),
            "directory must be canonical and representable")
    return path


def read_direct(path: Path, cap: int = MAX_DIRECT_BYTES) -> bytes:
    direct_directory(path.parent)
    before = path.lstat()
    require(type(cap) is int and 0 <= cap <= 512 * 1024**2
            and stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            and before.st_size <= cap,
            "input must be a direct single-link regular file")
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
                          s.st_mtime_ns, s.st_ctime_ns)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        opened = os.fstat(descriptor)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1
                and opened.st_size <= cap and identity(opened) == identity(before),
                "input changed before read")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(cap + 1)
        require(identity(os.fstat(descriptor)) == identity(before) == identity(path.lstat())
                and len(raw) == before.st_size and len(raw) <= cap, "input changed during read")
        return raw
    finally:
        os.close(descriptor)


def record(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def check_entry(raw: bytes, entry: object, label: str) -> None:
    require(type(entry) is dict and set(entry) == {"bytes", "sha256"}
            and type(entry["bytes"]) is int and entry["bytes"] >= 0
            and type(entry["sha256"]) is str and len(entry["sha256"]) == 64
            and len(raw) == entry["bytes"] and sha(raw) == entry["sha256"],
            "pinned bytes differ: " + label)


def portable(value: object) -> str:
    require(type(value) is str and bool(value), "relative path is absent")
    p = PurePosixPath(value)
    require(bool(p.parts) and not p.is_absolute() and ".." not in p.parts and p.as_posix() == value
            and "\\" not in value and not any(c in value for c in ("\n", "\r", "\x00")),
            "relative path is outside the finite source route")
    return value


def mapped_link(target: str) -> str:
    if target in EXTERNAL_LINKS:
        return target
    require(target in LOCAL_LINKS, "publication link is not enumerated")
    return BASE_URL + LOCAL_LINKS[target]


def tool_selector(name: str, value: object) -> Path:
    require(name in TOOLS and type(value) is str
            and not any(c in value for c in ("\n", "\r", "\x00", os.pathsep)),
            "tool selector is outside the fixed roster")
    selected = Path(value)
    require(selected.is_absolute() and selected.name == name, "tool selector differs")
    return selected


def admit_manifest(value: object, kind: str, exact: bool) -> dict:
    require(kind in KINDS, "unknown publication kind")
    require(type(value) is dict and set(value) == {"schema", "files", "outputs"}
            and value["schema"] == "pid-rs/embodied-sensor-publication-inputs-v1",
            "manifest schema or fields differ")
    require(type(value["files"]) is dict and set(value["files"]) == INPUTS,
            "finite source inventory differs")
    require(type(value["outputs"]) is dict and set(value["outputs"]) == set(KINDS),
            "output kind inventory differs")
    for selected in KINDS:
        output = value["outputs"][selected]
        require(type(output) is dict and set(output) ==
                {"status", "tex", "pdf", "observation", "figure_pdfs"},
                "output fields differ")
        require(output["status"] in ("unbound", "reviewed-reference"), "output status differs")
        if output["status"] == "unbound":
            require(all(output[x] is None for x in ("tex", "pdf", "observation", "figure_pdfs")),
                    "unbound output must not contain invented observations")
        else:
            require(type(output["tex"]) is dict and type(output["pdf"]) is dict
                    and type(output["observation"]) is dict,
                    "reviewed output lacks actual observations")
            require(type(output["figure_pdfs"]) is dict
                    and set(output["figure_pdfs"]) == {str(Path(name).with_suffix(".pdf"))
                                                       for name in KIND_FIGURES[selected]},
                    "figure output differs from selected kind")
    require(not exact or value["outputs"][kind]["status"] == "reviewed-reference",
            "exact mode refuses an unbound reference before production")
    return value


def utc(value: object) -> dt.datetime:
    require(type(value) is str, "time must be text")
    stamp = dt.datetime.fromisoformat(value)
    require(stamp.utcoffset() == dt.timedelta(0), "time must have an explicit UTC offset")
    return stamp


def admit_registration(reg: object, binding: dict, observed: dt.datetime,
                       observed_mono: float) -> dt.datetime:
    fields = {"schema", "status", "kind", "mode", "root", "work_dir", "optimization",
              "registered_utc", "deadline_utc", "stage_started_utc", "stage_deadline_utc",
              "maximum_builds", "maximum_commands", "manifest_sha256", "builder_sha256",
              "python_sha256", "tool_selectors", "reader_directory", "stage_monotonic_deadline"}
    require(type(reg) is dict and set(reg) == fields, "registration fields differ")
    require(reg["schema"] == "pid-rs/embodied-sensor-publication-execution-v1"
            and reg["status"] == "reviewed-source-ready-for-" + binding["mode"],
            "registration status differs")
    for key in ("kind", "mode", "root", "work_dir", "optimization",
                "manifest_sha256", "builder_sha256", "python_sha256", "stage_monotonic_deadline"):
        require(type(reg[key]) is type(binding[key]) and reg[key] == binding[key],
                "registration command/source binding differs: " + key)
    require(type(reg["maximum_builds"]) is int and reg["maximum_builds"] == 2
            and type(reg["maximum_commands"]) is int
            and reg["maximum_commands"] == COMMANDS[binding["kind"]],
            "registration command budget differs")
    require(type(reg["tool_selectors"]) is dict and set(reg["tool_selectors"]) == TOOLS,
            "tool selector inventory differs")
    require(type(reg["reader_directory"]) is str, "reader directory is absent")
    require(type(reg["stage_monotonic_deadline"]) is float
            and math.isfinite(reg["stage_monotonic_deadline"])
            and observed_mono < reg["stage_monotonic_deadline"] <= observed_mono + 5400,
            "original caller monotonic endpoint differs")
    start, end = utc(reg["registered_utc"]), utc(reg["deadline_utc"])
    outer_start, outer_end = utc(reg["stage_started_utc"]), utc(reg["stage_deadline_utc"])
    require(outer_start <= start <= observed < end <= outer_end
            and (end-start).total_seconds() <= 2700
            and (outer_end-outer_start).total_seconds() <= 5400,
            "original registration chronology or budget differs")
    return end


def load_runtime(root: Path) -> ModuleType:
    raw = read_direct(root / RUNTIME)
    require(sha(raw) == RUNTIME_SHA256, "reviewed runtime changed")
    module = ModuleType("reviewed_mgw_note_runtime")
    module.__file__ = str(root / RUNTIME)
    exec(compile(raw, module.__file__, "exec", dont_inherit=True,
                 optimize=sys.flags.optimize), module.__dict__)
    return module


def bounded_snapshot(runtime: ModuleType):
    """Reuse capture persistence/verification while bounding every descriptor read."""
    class BoundedSnapshot(runtime.Snapshot):
        def __init__(self):
            super().__init__()
            self.caps = {}
        def read(self, path):
            path = path.absolute()
            before = path.lstat()
            raw = read_direct(path, self.caps.get(str(path), MAX_DIRECT_BYTES))
            after = path.lstat()
            require(runtime.file_identity(before) == runtime.file_identity(after),
                    "input changed around bounded capture")
            captured = (runtime.file_identity(after), raw)
            previous = self.inputs.get(str(path))
            require(previous is None or previous == captured, "input changed since capture")
            self.inputs[str(path)] = captured
            return raw
    return BoundedSnapshot()


def pinned_reader(source: Path, manifest: dict, snapshot: object, work: Path) -> ModuleType:
    source = direct_directory(source)
    require(manifest["schema"] == "pid-rs/prefix-mgw-bias-pypdf-source-v2"
            and manifest["version"] == "6.16.1" and len(manifest["files"]) == 58,
            "reader source profile differs")
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    require(actual == set(manifest["files"]), "reader source inventory differs")
    copied = work / "reader" / "pypdf"
    copied.mkdir(parents=True)
    for relative, expected in manifest["files"].items():
        portable(relative)
        raw = snapshot.read(source / relative)
        check_entry(raw, expected, "reader/" + relative)
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        snapshot.read(target)
    require(not any(name == "pypdf" or name.startswith("pypdf.") for name in sys.modules),
            "ambient PDF reader is already loaded")
    sys.path.insert(0, str(copied.parent))
    module = importlib.import_module("pypdf")
    require(module.__version__ == "6.16.1"
            and Path(module.__file__).resolve(strict=True) == copied / "__init__.py",
            "reader import identity differs")
    snapshot.verify()
    return module


@contextmanager
def reader_diagnostics():
    class FailHandler(logging.Handler):
        def emit(self, record):
            raise RuntimeError("PDF reader diagnostic: " + record.getMessage())
    logger = logging.getLogger("pypdf")
    old = (logger.handlers[:], logger.propagate, logger.level)
    logger.handlers, logger.propagate, logger.level = [FailHandler()], False, logging.DEBUG
    out, err = io.StringIO(), io.StringIO()
    try:
        with warnings.catch_warnings(), redirect_stdout(out), redirect_stderr(err):
            warnings.simplefilter("error")
            yield
        require(not out.getvalue() and not err.getvalue(), "unexpected PDF reader output")
    finally:
        logger.handlers, logger.propagate, logger.level = old


def reader_text(value: object) -> str:
    """Project reader text to JSON text without coercing non-text values."""
    require(isinstance(value, str), "PDF reader text is not a string")
    # Reader string subclasses carry PDF metadata; preserve their text payload,
    # independently of an overridden __str__, and emit an exact builtin str.
    return str.__str__(value)


def observe_pdf(module: ModuleType, raw: bytes, layout: bytes, bbox: bytes, fonts: str) -> dict:
    require(raw.startswith(b"%PDF-1.7"), "PDF version differs")
    rows = fonts.splitlines()[2:]
    require(rows and "Type 3" not in fonts and "Helvetica" not in fonts
            and all(row.split()[-5:-2] == ["yes", "yes", "yes"] for row in rows),
            "font embedding/subsetting/Unicode profile differs")
    allowed_uris = EXTERNAL_LINKS | frozenset(BASE_URL + value for value in LOCAL_LINKS.values())
    with reader_diagnostics():
        reader = module.PdfReader(io.BytesIO(raw), strict=True)
        require(not reader.is_encrypted and 1 <= len(reader.pages) <= 100,
                "encryption or bounded page inventory differs")
        catalog = reader.trailer["/Root"]
        require(str(catalog.get("/Lang")) == "en", "PDF language differs")
        geometry = []
        for page in reader.pages:
            w, h = float(page.mediabox.width), float(page.mediabox.height)
            require(math.isfinite(w) and math.isfinite(h)
                    and abs(w-595.276) <= .001 and abs(h-841.89) <= .001,
                    "PDF page is not the admitted A4 profile")
            geometry.append([w, h])
        opener = catalog.get("/OpenAction")
        opener = opener.get_object() if opener is not None else None
        first = reader.pages[0].indirect_reference
        require(isinstance(opener, dict) and set(opener) == {"/S", "/D"}
                and str(opener["/S"]) == "/GoTo" and len(opener["/D"]) == 2
                and str(opener["/D"][1]) == "/Fit"
                and opener["/D"][0].idnum == first.idnum
                and opener["/D"][0].generation == first.generation,
                "opener must target its own first page")
        uris, gotos, seen = [], [], set()
        forbidden = {"/JS", "/JavaScript", "/AA", "/Launch", "/EmbeddedFiles", "/EF",
                     "/RichMedia", "/SubmitForm", "/ImportData", "/GoToR", "/XFA"}
        def visit(value):
            if isinstance(value, module.generic.IndirectObject):
                key = ("ref", value.idnum, value.generation)
                if key in seen:
                    return
                seen.add(key)
                value = value.get_object()
            if not isinstance(value, (dict, list)):
                return
            key = ("value", id(value))
            if key in seen:
                return
            seen.add(key)
            require(len(seen) <= 100000, "PDF object budget exceeded")
            if isinstance(value, dict):
                require(not forbidden.intersection(value), "forbidden PDF action/file key")
                action = str(value.get("/S"))
                if action == "/URI":
                    require(set(value) == {"/Type", "/S", "/URI"}
                            and str(value["/Type"]) == "/Action"
                            and str(value["/URI"]) in allowed_uris,
                            "PDF URI is not a finite admitted action")
                    uris.append(str(value["/URI"]))
                elif action == "/GoTo":
                    require(set(value) == {"/S", "/D"}, "GoTo action shape differs")
                    if isinstance(value["/D"], str):
                        gotos.append(str(value["/D"]))
                    else:
                        require(value is opener, "unexpected direct destination")
                elif str(value.get("/Type")) == "/Action":
                    raise RuntimeError("unsupported PDF action")
                if "/A" in value:
                    require(str(value["/A"].get_object().get("/S")) in ("/URI", "/GoTo"),
                            "unsupported annotation or outline action")
                for child in value.values():
                    visit(child)
            else:
                for child in value:
                    visit(child)
        visit(catalog)
        named = reader.named_destinations
        require(all(name in named for name in gotos), "internal action lacks destination")
        headings, outline_seen = [], set()
        def walk(node, level):
            while node is not None:
                node = node.get_object()
                require(id(node) not in outline_seen and len(outline_seen) < 128 and level <= 5,
                        "outline is cyclic or exceeds its finite budget")
                outline_seen.add(id(node))
                action = node["/A"].get_object()
                name = str(action["/D"])
                require(str(action["/S"]) == "/GoTo" and name in named,
                        "outline destination differs")
                point = named[name]
                page = reader.get_destination_page_number(point)
                require(type(page) is int and 0 <= page < len(reader.pages)
                        and point.typ == "/XYZ", "outline page or destination type differs")
                x, y = float(point.left), float(point.top)
                require(math.isfinite(x) and math.isfinite(y), "nonfinite destination")
                headings.append({"title": str(node["/Title"]), "level": level,
                                 "name": name, "page": page+1, "x": x, "y": y})
                if "/First" in node:
                    walk(node["/First"], level+1)
                node = node.get("/Next")
        if "/Outlines" in catalog:
            walk(catalog["/Outlines"].get("/First"), 0)
        texts = [page.extract_text() or "" for page in reader.pages]
        require(all(text.strip() for text in texts), "empty extracted page")
        poppler = layout.decode("utf-8").split("\f")
        if poppler and not poppler[-1].strip():
            poppler.pop()
        require(len(poppler) == len(texts), "independent text page counts differ")
    return {"pages": len(texts), "geometry": geometry, "headings": headings,
            "https_uris": sorted(uris), "gotos": sorted(gotos),
            "named_destinations": sorted(reader_text(name) for name in named),
            "root_keys": sorted(map(str, catalog)),
            "pypdf_text_sha256": [sha(text.encode()) for text in texts],
            "poppler_layout_sha256": sha(layout), "poppler_bbox_sha256": sha(bbox),
            "font_rows": rows, "first_page_fit": True}


def work_bytes(root: Path, reserve: int = 0) -> int:
    total = 0
    for path in root.rglob("*"):
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode), "work tree contains a symbolic link")
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, "work artifact has another hard link")
            total += info.st_size
        else:
            require(stat.S_ISDIR(info.st_mode), "work tree contains a special file")
    require(total <= MAX_WORK_BYTES-reserve, "observed work-byte budget exceeded")
    return total


def finish(path: Path, result: dict, deadline: dt.datetime, mono_end: float) -> None:
    work_bytes(path.parent, FINAL_RESULT_RESERVE)
    late_before_write = now() >= deadline or time.monotonic() >= mono_end
    if late_before_write:
        result.update(status="failed", deadline_exhausted_before_result=True)
    record(path, result)
    work_bytes(path.parent)
    if not late_before_write and now() < deadline and time.monotonic() < mono_end:
        return
    original = read_direct(path)
    with path.with_name("RESULT.before-late-finalization.json").open("xb") as stream:
        stream.write(original)
        stream.flush()
        os.fsync(stream.fileno())
    result.update(status="failed", late_finalization=True, first_result_sha256=sha(original))
    failed = path.with_name("RESULT.failed-finalization.json")
    record(failed, result)
    os.replace(failed, path)
    work_bytes(path.parent)
    raise RuntimeError("original deadline exhausted during result persistence")


def main(argv: list[str] | None = None) -> int:
    entry_utc, entry_mono = now(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=KINDS, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--exact", action="store_true")
    modes.add_argument("--cross-toolchain", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--registration-sha256")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--stage-monotonic-deadline", type=float)
    args = parser.parse_args(argv)
    if args.cross_toolchain:
        print("Embodied sensor PDF: no admitted cross-toolchain relation; status 2 refusal.",
              file=sys.stderr)
        return 2
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.ignore_environment
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires -I -S -B, optionally -O")
    require(args.check and args.registration is not None and args.work_dir is not None
            and type(args.manifest_sha256) is str and type(args.registration_sha256) is str
            and args.stage_monotonic_deadline is not None,
            "requires check, exact external source bindings and fresh registration")
    args.root = direct_directory(args.root)
    args.work_dir = args.work_dir.absolute()
    direct_directory(args.work_dir.parent)
    require(not args.work_dir.exists() and not args.work_dir.is_symlink(),
            "work directory already exists")
    runtime = load_runtime(args.root)
    snapshot = bounded_snapshot(runtime)
    raw_manifest = snapshot.read(args.root / MANIFEST)
    require(sha(raw_manifest) == args.manifest_sha256, "manifest hash differs")
    manifest = admit_manifest(runtime.strict_json(raw_manifest), args.kind, args.exact)
    raw_reg = snapshot.read(args.registration.absolute())
    require(sha(raw_reg) == args.registration_sha256, "registration hash differs")
    reg = runtime.strict_json(raw_reg)
    binding = {"kind": args.kind, "mode": "exact" if args.exact else "discovery",
               "root": str(args.root), "work_dir": str(args.work_dir),
               "optimization": sys.flags.optimize, "manifest_sha256": sha(raw_manifest),
               "builder_sha256": sha(snapshot.read(Path(__file__).absolute())),
               "python_sha256": sha(snapshot.read(Path(sys.executable).resolve(strict=True))),
               "stage_monotonic_deadline": args.stage_monotonic_deadline}
    deadline = admit_registration(reg, binding, now(), time.monotonic())
    mono_end = min(args.stage_monotonic_deadline,
                   entry_mono + (deadline-entry_utc).total_seconds())
    inputs = {}
    for relative, expected in manifest["files"].items():
        portable(relative)
        inputs[relative] = snapshot.read(args.root / relative)
        check_entry(inputs[relative], expected, relative)
    require(sha(inputs[RUNTIME]) == RUNTIME_SHA256 and sha(inputs[NATIVE]) == NATIVE_SHA256
            and sha(inputs[READER]) == READER_SHA256, "shared reviewed identity changed")
    profile = runtime.strict_json(inputs[NATIVE])
    require(os.uname().sysname == profile["platform"]["system"]
            and os.uname().machine == profile["platform"]["machine"]
            and list(sys.version_info[:3]) == profile["python"]["version"],
            "native platform or interpreter differs")
    check_entry(snapshot.read(Path(sys.executable).resolve(strict=True)),
                {k: profile["python"][k] for k in ("bytes", "sha256")}, "Python")
    check_entry(snapshot.read(Path("/bin/ps")),
                {k: profile["process_observer"][k] for k in ("bytes", "sha256")}, "observer")
    selectors, targets = {}, {}
    for name in sorted(TOOLS):
        selector = tool_selector(name, reg["tool_selectors"][name])
        target = selector.resolve(strict=True)
        expected = profile["tools"][name]
        require(target.name == expected["expected_target_leaf"], "tool target leaf differs")
        snapshot.caps[str(target)] = expected["bytes"]
        check_entry(snapshot.read(target), {k: expected[k] for k in ("bytes", "sha256")}, name)
        selectors[name], targets[name] = str(selector), target
    require(set(profile["fonts"]) == FONT_NAMES, "font roster differs")
    expected = manifest["outputs"][args.kind]
    if args.exact:
        reference = snapshot.read(args.root / ("output/pdf/" + OUTPUTS[args.kind] + ".pdf"))
        check_entry(reference, expected["pdf"], "canonical reference")
        reference_tex = snapshot.read(args.root / (ASSETS + args.kind + ".expected.tex"))
        check_entry(reference_tex, expected["tex"], "canonical expected TeX")
        reference_figures = {}
        for name in KIND_FIGURES[args.kind]:
            leaf = str(Path(name).with_suffix(".pdf"))
            reference_figures[leaf] = snapshot.read(args.root / (ASSETS + leaf))
            check_entry(reference_figures[leaf], expected["figure_pdfs"][leaf], "canonical vector derivative")
    require(now() < deadline and time.monotonic() < mono_end, "deadline before work creation")
    args.work_dir.mkdir(mode=0o700)
    result = {"status": "failed", "kind": args.kind, "mode": binding["mode"],
              "started_utc": now().isoformat(), "commands": [], "builds": [],
              "new_formal_results": 0, "adoption": False,
              "original_stage_monotonic_deadline": args.stage_monotonic_deadline,
              "work_byte_scope": "Own work root including final RESULT; outer custody requires owner accounting"}
    try:
        reader = pinned_reader(Path(reg["reader_directory"]), runtime.strict_json(inputs[READER]),
                               snapshot, args.work_dir)
        produced, observations = [], []
        for number in (1, 2):
            attempt = args.work_dir / ("build-" + str(number))
            attempt.mkdir()
            for leaf in ("build", "home", "tmp", "commands", "fonts", "font-cache", "tex-cache"):
                (attempt / leaf).mkdir()
            build = attempt / "build"
            stage = dict(STAGE_COMMON)
            stage["EXPOSITION.md"] = SOURCES[args.kind]
            stage["layout/report.latex"] = TEMPLATES[args.kind]
            for name in KIND_FIGURES[args.kind]:
                stage[name] = FIGURES[name]
            for relative, source in stage.items():
                target = build / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(inputs[source])
                snapshot.read(target)
            environment = {
                "PATH": os.defpath, "LC_ALL": "C", "LANG": "C", "TZ": "UTC",
                "SOURCE_DATE_EPOCH": str(profile["source_date_epoch"]),
                "HOME": str(attempt / "home"), "TMPDIR": str(attempt / "tmp"),
                "TEXINPUTS": str(build / "layout") + os.pathsep,
                "TEXMFVAR": str(attempt / "tex-cache"), "TEXMFCACHE": str(attempt / "tex-cache"),
                "FONTCONFIG_FILE": str(attempt / "fonts.conf"), "FONTCONFIG_PATH": str(attempt),
                "PANGOCAIRO_BACKEND": "fc", "OSFONTDIR": str(attempt / "fonts"),
            }
            record(attempt / "ENVIRONMENT.json", environment)
            runner = runtime.Runner(attempt / "commands", environment, preparation=False)
            def run(name, arguments, label):
                remaining = min((deadline-now()).total_seconds(), mono_end-time.monotonic())
                require(remaining > 0 and len(result["commands"]) < reg["maximum_commands"],
                        "original deadline or command budget exhausted")
                require(Path(selectors[name]).resolve(strict=True) == targets[name],
                        "tool selector changed")
                snapshot.read(targets[name])
                before = len(runner.commands)
                try:
                    return runner.run([selectors[name], *arguments], build, label,
                                      timeout=min(300, remaining), cap=4*1024**2,
                                      memory=4*1024**3, allow_stdout=True)
                finally:
                    if len(runner.commands) > before:
                        result["commands"].append(runner.commands[-1])
                    work_bytes(args.work_dir, FINAL_RESULT_RESERVE)
            def find_input(name, arguments, expected_input):
                value = run("kpsewhich", arguments, name).decode().strip()
                require(len(value.splitlines()) == 1 and Path(value).is_absolute(),
                        "lookup is not one absolute path")
                raw = snapshot.read(Path(value))
                check_entry(raw, {k: expected_input[k] for k in ("bytes", "sha256")}, name)
                return value, raw
            for name in ("pandoc", "lualatex"):
                lines = run(name, ["--version"], name+"-version").decode().splitlines()
                require(lines and lines[0].strip() == profile["expected_versions"][name],
                        "tool version differs")
            lines = run("rsvg-convert", ["--version"], "rsvg-version").decode().splitlines()
            require(lines and lines[0].strip() == profile["expected_versions"]["rsvg-convert"],
                    "SVG converter version differs")
            format_args = ["--engine=luahbtex", "--progname=lualatex", "--must-exist",
                           "--format=fmt", "lualatex.fmt"]
            selected_format, _ = find_input("format-before", format_args, profile["format"])
            for name in sorted(FONT_NAMES):
                _, raw = find_input("font-"+name, ["--must-exist", name], profile["fonts"][name])
                with (attempt / "fonts" / name).open("xb") as stream:
                    stream.write(raw)
                snapshot.read(attempt / "fonts" / name)
            (attempt / "fonts.conf").write_text(
                '<?xml version="1.0"?>\n<fontconfig><dir>' + escape(str(attempt / "fonts"))
                + "</dir><cachedir>" + escape(str(attempt / "font-cache"))
                + "</cachedir><config></config></fontconfig>\n")
            snapshot.read(attempt / "fonts.conf")
            run("fc-cache", ["-f"], "font-cache")
            figures = {}
            for name in KIND_FIGURES[args.kind]:
                leaf = str(Path(name).with_suffix(".pdf"))
                run("rsvg-convert", ["--format=pdf", "--keep-aspect-ratio",
                    "--output=" + leaf, name], "svg-" + Path(name).stem)
                figure = snapshot.read(build / leaf)
                figures[leaf] = {"bytes": len(figure), "sha256": sha(figure)}
                if args.exact:
                    check_entry(figure, expected["figure_pdfs"][leaf], "figure PDF")
                    require(figure == reference_figures[leaf], "vector derivative bytes differ")
            run("pandoc", ["EXPOSITION.md",
                "--from=markdown+tex_math_dollars+tex_math_single_backslash+implicit_figures",
                "--to=latex", "--standalone", "--wrap=none", "--template=layout/report.latex",
                "--lua-filter=layout/publication-filter.lua",
                "--metadata=publication-kind:"+args.kind,
                "--metadata=title:"+TITLES[args.kind], "--output=report.tex"], "pandoc-report")
            tex = snapshot.read(build / "report.tex")
            if args.exact:
                check_entry(tex, expected["tex"], "expected TeX")
                require(tex == reference_tex, "expected TeX bytes differ")
            for pass_number in (1, 2):
                run("lualatex", ["-no-shell-escape", "-interaction=nonstopmode",
                    "-halt-on-error", "-file-line-error", "report.tex"], "lualatex-"+str(pass_number))
            run("bash", [str(build / "check-formal-pdf-log.sh"), str(build / "report.log")], "strict-log")
            pdf = read_direct(build / "report.pdf")
            run("pdfinfo", ["report.pdf"], "pdfinfo")
            fonts = run("pdffonts", ["report.pdf"], "pdffonts").decode()
            run("pdftotext", ["-layout", "report.pdf", "report.layout.txt"], "text-layout")
            run("pdftotext", ["-bbox", "report.pdf", "words.xhtml"], "text-bbox")
            observation = observe_pdf(reader, pdf, read_direct(build / "report.layout.txt"),
                                      read_direct(build / "words.xhtml"), fonts)
            record(build / "PDF_OBSERVATION.json", observation)
            if args.exact:
                check_entry(pdf, expected["pdf"], "expected PDF")
                check_reference(pdf, reference, observation, expected["observation"])
            after_format, _ = find_input("format-after", format_args, profile["format"])
            require(after_format == selected_format, "format lookup changed")
            snapshot.verify()
            require(all(Path(selectors[name]).resolve(strict=True) == targets[name]
                        for name in TOOLS), "tool selectors changed during the build")
            require(read_direct(build / "report.tex") == tex
                    and read_direct(build / "report.pdf") == pdf, "produced artifact changed")
            produced.append(pdf)
            observations.append(observation)
            result["builds"].append({"index": number, "tex": {"bytes": len(tex), "sha256": sha(tex)},
                "pdf": {"bytes": len(pdf), "sha256": sha(pdf)}, "observation": observation,
                "figure_pdfs": figures})
        require(len(result["commands"]) == COMMANDS[args.kind], "actual command count differs")
        require(produced[0] == produced[1] and same_json_value(observations[0], observations[1]),
                "two fresh builds differ")
        require(result["builds"][0]["tex"] == result["builds"][1]["tex"]
                and result["builds"][0]["figure_pdfs"] == result["builds"][1]["figure_pdfs"],
                "two fresh derivatives differ")
        result["status"] = ("two-exact-reference-builds-reproduced" if args.exact
                            else "two-discovery-candidates-produced-no-adoption")
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        try:
            snapshot.verify()
            snapshot.save(args.work_dir)
            result["inputs"] = snapshot.manifest()
            result["observed_work_bytes_before_result"] = work_bytes(args.work_dir, FINAL_RESULT_RESERVE)
        except BaseException as error:
            result.update(status="failed", custody_failure=repr(error))
            raise
        finally:
            result["completed_utc"] = now().isoformat()
            if now() >= deadline or time.monotonic() >= mono_end:
                result.update(status="failed", deadline_exhausted=True)
            finish(args.work_dir / "RESULT.json", result, deadline, mono_end)
    print("Embodied sensor PDF: " + result["status"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print("Embodied sensor PDF failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
