#!/usr/bin/env python3
"""Causal controls for the publication checker, not mathematical verification."""

from pathlib import Path
import json
import shutil
import subprocess
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "audit/formal/lean-stopped-prefix-probability"
STYLE = "audit/formal/latex/stopped-prefix-probability"
PDF = "output/pdf/stopped-prefix-probability.pdf"
CHECKER = "scripts/check-stopped-prefix-probability-pdf.sh"
BUILDER = "scripts/build-stopped-prefix-probability-pdf.sh"
FONT_MANIFEST = f"{STYLE}/figure-fonts.json"
INPUTS = [
    CHECKER, "scripts/check-markdown-math.py", PDF,
    f"{PACKAGE}/EXPOSITION.md", f"{PACKAGE}/figures/first-hit-and-prefix-return.svg",
    f"{STYLE}/publication.tex", f"{STYLE}/filter.lua", f"{STYLE}/profile.json", FONT_MANIFEST,
    "audit/formal/latex/pid-rs-report-tables.sty",
    "audit/formal/latex/pid-rs-workflow-publication.sty",
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex",
]


def make_fixture(root):
    for relative in INPUTS:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f"missing or symbolic control input: {source}")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(root / PDF, root / "builder-output.pdf")
    # Only the builder is substituted. All production checker, PDF and source bytes remain.
    (root / BUILDER).write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\n'
        'ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"\n'
        '[[ $# -eq 2 && "$1" == "--output" && "$2" == /* ]]\n'
        'cp "$ROOT/builder-output.pdf" "$2"\n'
    )
    (root / BUILDER).chmod(0o755)


def run(root, name, expected_error=None, mode="--exact"):
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", str(root / CHECKER), mode],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    if expected_error is None:
        if result.returncode != 0:
            raise SystemExit(f"positive control failed: {name}\n{output}")
    elif result.returncode == 0 or expected_error not in output:
        raise SystemExit(f"control lacked its specific rejection: {name}\n{output}")
    print(f"ok: {name}", flush=True)


def mutate_pdf(root, mutate):
    source = root / PDF
    reader = PdfReader(source, strict=True)
    writer = PdfWriter(clone_from=reader)
    writer.pdf_header = reader.pdf_header
    # Keep source-bound IDs so a metadata/action control cannot fail only on ID drift.
    writer._ID = reader.trailer["/ID"]
    mutate(writer)
    with source.open("wb") as stream:
        writer.write(stream)
    # Match the mocked rebuild as well: exact-byte comparison cannot cause the rejection.
    shutil.copy2(source, root / "builder-output.pdf")


def mutate_font_manifest(root, mutate):
    path = root / FONT_MANIFEST
    manifest = json.loads(path.read_text())
    mutate(manifest)
    path.write_text(json.dumps(manifest, indent=2) + "\n")


def duplicate_font_key(root):
    path = root / FONT_MANIFEST
    path.write_text(path.read_text().replace('"schema": 1,', '"schema": 1, "schema": 1,', 1))


def wrong_font_digest(root):
    # Exercise the production capture/hash check; the renderer is never reached.
    shutil.copy2(ROOT / BUILDER, root / BUILDER)
    mutate_font_manifest(root, lambda m: m["fonts"][0].__setitem__("sha256", "0" * 64))


def reject_builder_font_config(root):
    # Run the production builder directly so checker preflight cannot mask its rejection.
    shutil.copy2(ROOT / BUILDER, root / BUILDER)
    mutate_font_manifest(root, lambda m: m.__setitem__(
        "fontconfig_template", '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n' + m["fontconfig_template"]
    ))
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", str(root / BUILDER), "--output", str(root / "control.pdf")],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    if result.returncode == 0 or "font configuration changed" not in output:
        raise SystemExit(f"production builder lacked its configuration rejection\n{output}")
    print("ok: production-builder-font-config-dtd", flush=True)


def unsafe_link(writer):
    for page in writer.pages:
        for ref in page.get("/Annots", []):
            annotation = ref.get_object()
            if annotation.get("/A") is not None:
                annotation[NameObject("/A")] = DictionaryObject({
                    NameObject("/S"): NameObject("/Launch"),
                    NameObject("/F"): TextStringObject("forbidden-control"),
                })
                return
    raise SystemExit("unsafe-action control found no link to mutate")


def chained_link(writer):
    for page in writer.pages:
        for ref in page.get("/Annots", []):
            action = ref.get_object().get("/A")
            if action is not None:
                action.get_object()[NameObject("/Next")] = DictionaryObject({
                    NameObject("/S"): NameObject("/Launch"),
                    NameObject("/F"): TextStringObject("forbidden-chained-control"),
                })
                return
    raise SystemExit("chained-action control found no link to mutate")


def undeclared_font(writer):
    for page in writer.pages:
        fonts = page["/Resources"].get_object().get("/Font")
        if fonts is None:
            continue
        for reference in fonts.get_object().values():
            font = reference.get_object()
            font[NameObject("/BaseFont")] = NameObject("/ABCDEF+Helvetica")
            descendants = font.get("/DescendantFonts", [])
            for candidate in [font, *(ref.get_object() for ref in descendants)]:
                candidate[NameObject("/BaseFont")] = NameObject("/ABCDEF+Helvetica")
                descriptor = candidate.get("/FontDescriptor")
                if descriptor is not None:
                    descriptor.get_object()[NameObject("/FontName")] = NameObject("/ABCDEF+Helvetica")
            return
    raise SystemExit("undeclared-font control found no font to mutate")


def main():
    with tempfile.TemporaryDirectory(prefix="pid-rs-stopped-prefix-pdf-controls-") as directory:
        parent = Path(directory)
        positive = parent / "positive"
        make_fixture(positive)
        run(positive, "reviewed PDF and source accepted")
        run(positive, "cross-toolchain mode accepts reviewed layout", mode="--cross-toolchain")
        cases = [
            ("missing-author", lambda root: mutate_pdf(root, lambda w: w.add_metadata({"/Author": ""})), "author metadata changed"),
            ("wrong-title", lambda root: mutate_pdf(root, lambda w: w.add_metadata({"/Title": "Wrong title"})), "title metadata changed"),
            ("chained-link", lambda root: mutate_pdf(root, chained_link), "contains a chained action"),
            ("unsafe-link", lambda root: mutate_pdf(root, unsafe_link), "forbidden or unknown action /Launch"),
            ("missing-page", lambda root: mutate_pdf(root, lambda w: w.remove_page(len(w.pages) - 1)), "metadata omitted: ^Pages:"),
            ("source-drift", lambda root: (root / f"{PACKAGE}/EXPOSITION.md").open("a").write("\nAn added source paragraph.\n"), "trailer ID is not source derived"),
            ("figure-drift", lambda root: (root / f"{PACKAGE}/figures/first-hit-and-prefix-return.svg").open("a").write("\n<!-- source change -->\n"), "trailer ID is not source derived"),
            ("missing-figure", lambda root: (root / f"{PACKAGE}/figures/first-hit-and-prefix-return.svg").unlink(), "required input is absent"),
            ("builder-failure", lambda root: (root / BUILDER).write_text('#!/usr/bin/env bash\necho "CONTROL_BUILD_FAILURE" >&2\nexit 7\n'), "CONTROL_BUILD_FAILURE"),
            ("missing-font-manifest", lambda root: (root / FONT_MANIFEST).unlink(), "required input is absent"),
            ("font-manifest-drift", lambda root: (root / FONT_MANIFEST).write_bytes((root / FONT_MANIFEST).read_bytes() + b"\n"), "trailer ID is not source derived"),
            ("font-manifest-duplicate-key", duplicate_font_key, "duplicate manifest key"),
            ("font-manifest-schema-float", lambda root: mutate_font_manifest(root, lambda m: m.__setitem__("schema", 1.0)), "manifest schema changed"),
            ("font-backend-coretext", lambda root: mutate_font_manifest(root, lambda m: m.__setitem__("pango_backend", "coretext")), "Pango backend must be fc"),
            ("font-config-missing-reset", lambda root: mutate_font_manifest(root, lambda m: m.__setitem__("fontconfig_template", m["fontconfig_template"].replace("  <reset-dirs/>\n", ""))), "font configuration changed"),
            ("production-builder-font-digest", wrong_font_digest, "font digest mismatch"),
            ("undeclared-publication-font", lambda root: mutate_pdf(root, undeclared_font), "undeclared publication font"),
        ]
        for name, mutate, error in cases:
            fixture = parent / name
            make_fixture(fixture)
            mutate(fixture)
            run(fixture, name, error)
        configuration = parent / "production-builder-font-config-dtd"
        make_fixture(configuration)
        reject_builder_font_config(configuration)
    print("OK: 2 positive and 18 causal publication controls; no theorem-check credit")


if __name__ == "__main__":
    main()
