#!/usr/bin/env python3
"""Fail-closed mutation suite for canonical results-guide figure assets."""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import NoReturn

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    TextStringObject,
)


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
CHECKER = ROOT / "scripts/check-mathematical-results-guide-figure-assets.py"
MANIFEST_RELATIVE = pathlib.Path(
    "audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
)


def fail(message: str) -> NoReturn:
    raise SystemExit(
        f"Mathematical results guide figure-asset self-test failed: {message}"
    )


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checker(
    root: pathlib.Path, optimized: bool = False
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-B", str(CHECKER), str(root)))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def require_failure(root: pathlib.Path, expected: str, label: str) -> None:
    for optimized in (False, True):
        result = run_checker(root, optimized)
        if result.returncode == 0:
            suffix = " under -O" if optimized else ""
            fail(f"{label} passed{suffix}")
        combined = result.stdout + result.stderr
        if expected not in combined:
            suffix = " under -O" if optimized else ""
            fail(f"{label} diagnostic changed{suffix}:\n{combined}")


def load_manifest(root: pathlib.Path) -> dict:
    return json.loads((root / MANIFEST_RELATIVE).read_text(encoding="utf-8"))


def save_manifest(root: pathlib.Path, manifest: dict) -> None:
    (root / MANIFEST_RELATIVE).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def update_derivative_digest(root: pathlib.Path, ordinal: int) -> pathlib.Path:
    manifest = load_manifest(root)
    relative = pathlib.Path(manifest["figures"][ordinal]["derivative"])
    path = root / relative
    manifest["figures"][ordinal]["derivative_sha256"] = digest(path)
    manifest["figures"][ordinal]["pdf_bytes"] = path.stat().st_size
    save_manifest(root, manifest)
    return path


def update_source_digest(root: pathlib.Path, ordinal: int) -> pathlib.Path:
    manifest = load_manifest(root)
    relative = pathlib.Path(manifest["figures"][ordinal]["source"])
    path = root / relative
    manifest["figures"][ordinal]["source_sha256"] = digest(path)
    save_manifest(root, manifest)
    return path


def rewrite_pdf(path: pathlib.Path, mutate) -> None:
    writer = PdfWriter(str(path), incremental=True)
    writer.pdf_header = "%PDF-1.7"
    mutate(writer)
    output = io.BytesIO()
    writer.write(output)
    path.write_bytes(output.getvalue())


def first_font(writer: PdfWriter, subtype: str):
    fonts = writer.pages[0]["/Resources"]["/Font"]
    return next(
        candidate.get_object()
        for candidate in fonts.values()
        if str(candidate.get_object().get("/Subtype")) == subtype
    )


def type1_descriptor(writer: PdfWriter):
    return first_font(writer, "/Type1")["/FontDescriptor"].get_object()


def type0_parts(writer: PdfWriter):
    font = first_font(writer, "/Type0")
    descendant = font["/DescendantFonts"][0].get_object()
    descriptor = descendant["/FontDescriptor"].get_object()
    return font, descendant, descriptor


def main() -> int:
    if not CHECKER.is_file() or CHECKER.is_symlink():
        fail("checker is absent, non-regular, or symbolic")
    manifest = json.loads((ROOT / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    required = [MANIFEST_RELATIVE]
    required.extend(
        pathlib.Path(manifest[field]["path"])
        for field in ("regeneration_contract", "regenerator", "third_party_notice")
    )
    required.extend(
        pathlib.Path(entry["path"]) for entry in manifest["license_artifacts"]
    )
    for entry in manifest["figures"]:
        required.extend(
            (pathlib.Path(entry["source"]), pathlib.Path(entry["derivative"]))
        )

    with tempfile.TemporaryDirectory(prefix="pid-rs-guide-figure-self-test.") as raw:
        fixture = pathlib.Path(raw) / "base"
        for relative in required:
            destination = fixture / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        for optimized in (False, True):
            baseline = run_checker(fixture, optimized)
            if baseline.returncode != 0:
                suffix = " under -O" if optimized else ""
                fail(f"baseline rejected{suffix}:\n{baseline.stdout}{baseline.stderr}")

        case_number = 0

        def case(label: str) -> pathlib.Path:
            nonlocal case_number
            case_number += 1
            path = pathlib.Path(raw) / f"case-{case_number}-{label}"
            shutil.copytree(fixture, path)
            return path

        root_schema = case("root-schema")
        root_schema_manifest = load_manifest(root_schema)
        root_schema_manifest["unexpected"] = None
        save_manifest(root_schema, root_schema_manifest)
        require_failure(
            root_schema, "manifest root schema changed", "root-schema mutation"
        )

        duplicate_key = case("duplicate-key")
        duplicate_path = duplicate_key / MANIFEST_RELATIVE
        duplicate_text = duplicate_path.read_text(encoding="utf-8")
        duplicate_path.write_text(
            duplicate_text.replace("{", '{\n  "format_version": 3,', 1),
            encoding="utf-8",
        )
        require_failure(duplicate_key, "duplicate JSON key", "duplicate-key mutation")

        entry_schema = case("entry-schema")
        entry_schema_manifest = load_manifest(entry_schema)
        entry_schema_manifest["figures"][0]["unexpected"] = None
        save_manifest(entry_schema, entry_schema_manifest)
        require_failure(
            entry_schema, "manifest figure 1 schema changed", "entry-schema mutation"
        )

        font_provenance = case("font-provenance")
        font_provenance_manifest = load_manifest(font_provenance)
        font_provenance_manifest["font_inputs"][0]["sha256"] = "0" * 64
        save_manifest(font_provenance, font_provenance_manifest)
        require_failure(
            font_provenance,
            "manifest font provenance or license inventory changed",
            "font-provenance mutation",
        )

        font_license = case("font-license")
        font_license_manifest = load_manifest(font_license)
        font_license_manifest["font_inputs"][3]["license_identifier"] = "MIT"
        save_manifest(font_license, font_license_manifest)
        require_failure(
            font_license,
            "manifest font provenance or license inventory changed",
            "font-license mutation",
        )

        raw_fonts = case("raw-font-status")
        raw_fonts_manifest = load_manifest(raw_fonts)
        raw_fonts_manifest["raw_font_files_tracked_in_repository"] = True
        save_manifest(raw_fonts, raw_fonts_manifest)
        require_failure(
            raw_fonts,
            "raw font files are not tracked",
            "raw-font-status mutation",
        )

        binding = case("binding")
        binding_manifest = load_manifest(binding)
        binding_manifest["regenerator"]["sha256"] = "0" * 64
        save_manifest(binding, binding_manifest)
        require_failure(
            binding, "manifest regenerator binding changed", "binding mutation"
        )

        receipt_drift = case("receipt-drift")
        receipt_manifest = load_manifest(receipt_drift)
        receipt_path = receipt_drift / receipt_manifest["regeneration_contract"]["path"]
        receipt_path.write_bytes(receipt_path.read_bytes() + b"\n")
        require_failure(
            receipt_drift,
            "bound regeneration_contract digest changed",
            "regeneration-contract custody mutation",
        )

        regenerator_drift = case("regenerator-drift")
        regenerator_manifest = load_manifest(regenerator_drift)
        regenerator_path = (
            regenerator_drift / regenerator_manifest["regenerator"]["path"]
        )
        regenerator_path.write_bytes(regenerator_path.read_bytes() + b"\n")
        require_failure(
            regenerator_drift,
            "bound regenerator digest changed",
            "regenerator custody mutation",
        )

        notice_drift = case("notice-drift")
        notice_manifest = load_manifest(notice_drift)
        notice_path = notice_drift / notice_manifest["third_party_notice"]["path"]
        notice_path.write_bytes(notice_path.read_bytes() + b"\n")
        require_failure(
            notice_drift,
            "bound third_party_notice digest changed",
            "third-party-notice custody mutation",
        )

        license_binding = case("license-binding")
        license_binding_manifest = load_manifest(license_binding)
        license_binding_manifest["license_artifacts"][0]["sha256"] = "0" * 64
        save_manifest(license_binding, license_binding_manifest)
        require_failure(
            license_binding,
            "manifest license-artifact bindings changed",
            "license-artifact manifest binding mutation",
        )

        for ordinal in range(3):
            license_drift = case(f"license-{ordinal + 1}-drift")
            license_drift_manifest = load_manifest(license_drift)
            license_path = (
                license_drift
                / license_drift_manifest["license_artifacts"][ordinal]["path"]
            )
            license_bytes = bytearray(license_path.read_bytes())
            license_bytes[-1] ^= 1
            license_path.write_bytes(license_bytes)
            require_failure(
                license_drift,
                f"bound license artifact {ordinal + 1} digest changed",
                f"license-artifact {ordinal + 1} custody mutation",
            )

        source_digest = case("source-digest")
        source_manifest = load_manifest(source_digest)
        source_path = source_digest / source_manifest["figures"][0]["source"]
        source_path.write_bytes(source_path.read_bytes() + b"\n<!-- hostile -->\n")
        require_failure(
            source_digest, "source digest changed", "source digest mutation"
        )

        source_fallback = case("source-fallback")
        source_fallback_manifest = load_manifest(source_fallback)
        source_fallback_path = (
            source_fallback / source_fallback_manifest["figures"][0]["source"]
        )
        source_fallback_text = source_fallback_path.read_text(encoding="utf-8")
        source_fallback_path.write_text(
            source_fallback_text.replace(
                'font-family: "Source Sans Pro"',
                'font-family: "Source Sans Pro", Arial, sans-serif',
                1,
            ),
            encoding="utf-8",
        )
        update_source_digest(source_fallback, 0)
        require_failure(
            source_fallback,
            "forbidden fallback/proprietary family",
            "source CSS fallback mutation",
        )

        source_family = case("source-family")
        source_family_manifest = load_manifest(source_family)
        source_family_path = (
            source_family / source_family_manifest["figures"][2]["source"]
        )
        source_family_text = source_family_path.read_text(encoding="utf-8")
        source_family_path.write_text(
            source_family_text.replace("'Latin Modern Sans'", "'Source Sans Pro'", 1),
            encoding="utf-8",
        )
        update_source_digest(source_family, 2)
        require_failure(
            source_family,
            "does not use only the exact 'Latin Modern Sans' CSS family",
            "source exact-family mutation",
        )

        source_weight = case("source-weight")
        source_weight_manifest = load_manifest(source_weight)
        source_weight_path = (
            source_weight / source_weight_manifest["figures"][0]["source"]
        )
        source_weight_text = source_weight_path.read_text(encoding="utf-8")
        source_weight_path.write_text(
            source_weight_text.replace("font-weight: 600", "font-weight: 500"),
            encoding="utf-8",
        )
        update_source_digest(source_weight, 0)
        require_failure(
            source_weight,
            "CSS font-weight inventory changed",
            "source weight mutation",
        )

        derivative_digest = case("derivative-digest")
        derivative_manifest = load_manifest(derivative_digest)
        derivative_path = (
            derivative_digest / derivative_manifest["figures"][0]["derivative"]
        )
        derivative_path.write_bytes(derivative_path.read_bytes() + b"hostile")
        require_failure(
            derivative_digest, "derivative digest changed", "derivative digest mutation"
        )

        self_authorized = case("self-authorized")
        self_authorized_manifest = load_manifest(self_authorized)
        self_authorized_path = (
            self_authorized / self_authorized_manifest["figures"][0]["derivative"]
        )
        self_authorized_path.write_bytes(self_authorized_path.read_bytes() + b"\n")
        update_derivative_digest(self_authorized, 0)
        require_failure(
            self_authorized,
            "canonical byte contract changed",
            "manifest self-authorization mutation",
        )

        oversize = case("oversize")
        oversize_manifest = load_manifest(oversize)
        oversize_path = oversize / oversize_manifest["figures"][0]["derivative"]
        oversize_path.write_bytes(b"%PDF-1.7\n" + b"0" * (1024 * 1024))
        require_failure(oversize, "exceeds the 1048576-byte bound", "size-cap mutation")

        scripted = case("javascript")
        scripted_path = scripted / load_manifest(scripted)["figures"][0]["derivative"]

        def add_javascript(writer: PdfWriter) -> None:
            writer.root_object[NameObject("/OpenAction")] = DictionaryObject(
                {
                    NameObject("/S"): NameObject("/JavaScript"),
                    NameObject("/JS"): TextStringObject("app.alert('hostile')"),
                }
            )

        rewrite_pdf(scripted_path, add_javascript)
        update_derivative_digest(scripted, 0)
        require_failure(scripted, "catalog keys changed", "catalog-key mutation")

        page_action = case("page-action")
        page_action_path = (
            page_action / load_manifest(page_action)["figures"][0]["derivative"]
        )

        def add_page_action(writer: PdfWriter) -> None:
            writer.pages[0][NameObject("/AA")] = DictionaryObject(
                {NameObject("/S"): NameObject("/JavaScript")}
            )

        rewrite_pdf(page_action_path, add_page_action)
        update_derivative_digest(page_action, 0)
        require_failure(
            page_action, "forbidden key /AA", "nested active-content mutation"
        )

        annotated = case("annotation")
        annotated_path = (
            annotated / load_manifest(annotated)["figures"][0]["derivative"]
        )

        def add_annotation(writer: PdfWriter) -> None:
            annotation = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Text"),
                    NameObject("/Rect"): ArrayObject(
                        [
                            FloatObject(0),
                            FloatObject(0),
                            FloatObject(10),
                            FloatObject(10),
                        ]
                    ),
                }
            )
            writer.pages[0][NameObject("/Annots")] = ArrayObject([annotation])

        rewrite_pdf(annotated_path, add_annotation)
        update_derivative_digest(annotated, 0)
        require_failure(annotated, "contains annotations", "annotation mutation")

        multipage = case("multipage")
        multipage_path = (
            multipage / load_manifest(multipage)["figures"][0]["derivative"]
        )

        def add_page(writer: PdfWriter) -> None:
            writer.add_blank_page(width=100, height=100)

        rewrite_pdf(multipage_path, add_page)
        update_derivative_digest(multipage, 0)
        require_failure(multipage, "has 2 pages instead of one", "page-count mutation")

        media_box = case("media-box")
        media_box_path = (
            media_box / load_manifest(media_box)["figures"][0]["derivative"]
        )

        def change_media_box(writer: PdfWriter) -> None:
            box = writer.pages[0]["/MediaBox"]
            box[2] = FloatObject(float(box[2]) + 1.0)

        rewrite_pdf(media_box_path, change_media_box)
        update_derivative_digest(media_box, 0)
        require_failure(media_box, "MediaBox tokens changed", "MediaBox mutation")

        no_type1_tounicode = case("no-type1-tounicode")
        no_type1_tounicode_path = (
            no_type1_tounicode
            / load_manifest(no_type1_tounicode)["figures"][0]["derivative"]
        )

        def strip_type1_tounicode(writer: PdfWriter) -> None:
            first_font(writer, "/Type1").pop(NameObject("/ToUnicode"))

        rewrite_pdf(no_type1_tounicode_path, strip_type1_tounicode)
        update_derivative_digest(no_type1_tounicode, 0)
        require_failure(
            no_type1_tounicode, "lacks /ToUnicode", "Type1 ToUnicode mutation"
        )

        no_type0_tounicode = case("no-type0-tounicode")
        no_type0_tounicode_path = (
            no_type0_tounicode
            / load_manifest(no_type0_tounicode)["figures"][0]["derivative"]
        )

        def strip_type0_tounicode(writer: PdfWriter) -> None:
            first_font(writer, "/Type0").pop(NameObject("/ToUnicode"))

        rewrite_pdf(no_type0_tounicode_path, strip_type0_tounicode)
        update_derivative_digest(no_type0_tounicode, 0)
        require_failure(
            no_type0_tounicode, "lacks /ToUnicode", "Type0 ToUnicode mutation"
        )

        no_type1_program = case("no-type1-program")
        no_type1_program_path = (
            no_type1_program
            / load_manifest(no_type1_program)["figures"][0]["derivative"]
        )

        def strip_type1_program(writer: PdfWriter) -> None:
            type1_descriptor(writer).pop(NameObject("/FontFile3"))

        rewrite_pdf(no_type1_program_path, strip_type1_program)
        update_derivative_digest(no_type1_program, 0)
        require_failure(
            no_type1_program,
            "must contain only an embedded FontFile3",
            "Type1 embedding mutation",
        )

        wrong_type1_program = case("wrong-type1-program")
        wrong_type1_program_path = (
            wrong_type1_program
            / load_manifest(wrong_type1_program)["figures"][0]["derivative"]
        )

        def change_type1_program_subtype(writer: PdfWriter) -> None:
            stream = type1_descriptor(writer)["/FontFile3"].get_object()
            stream[NameObject("/Subtype")] = NameObject("/OpenType")

        rewrite_pdf(wrong_type1_program_path, change_type1_program_subtype)
        update_derivative_digest(wrong_type1_program, 0)
        require_failure(
            wrong_type1_program,
            "/FontFile3 subtype is not /Type1C",
            "Type1 FontFile3 subtype mutation",
        )

        no_type0_program = case("no-type0-program")
        no_type0_program_path = (
            no_type0_program
            / load_manifest(no_type0_program)["figures"][0]["derivative"]
        )

        def strip_type0_program(writer: PdfWriter) -> None:
            type0_parts(writer)[2].pop(NameObject("/FontFile3"))

        rewrite_pdf(no_type0_program_path, strip_type0_program)
        update_derivative_digest(no_type0_program, 0)
        require_failure(
            no_type0_program,
            "must contain only an embedded FontFile3",
            "Type0 embedding mutation",
        )

        wrong_type0_program = case("wrong-type0-program")
        wrong_type0_program_path = (
            wrong_type0_program
            / load_manifest(wrong_type0_program)["figures"][0]["derivative"]
        )

        def change_type0_program_subtype(writer: PdfWriter) -> None:
            stream = type0_parts(writer)[2]["/FontFile3"].get_object()
            stream[NameObject("/Subtype")] = NameObject("/OpenType")

        rewrite_pdf(wrong_type0_program_path, change_type0_program_subtype)
        update_derivative_digest(wrong_type0_program, 0)
        require_failure(
            wrong_type0_program,
            "/FontFile3 subtype is not /CIDFontType0C",
            "Type0 FontFile3 subtype mutation",
        )

        type3 = case("type3")
        type3_path = type3 / load_manifest(type3)["figures"][0]["derivative"]

        def change_to_type3(writer: PdfWriter) -> None:
            first_font(writer, "/Type1")[NameObject("/Subtype")] = NameObject("/Type3")

        rewrite_pdf(type3_path, change_to_type3)
        update_derivative_digest(type3, 0)
        require_failure(type3, "unsupported font subtype /Type3", "Type3 mutation")

        truetype = case("truetype")
        truetype_path = truetype / load_manifest(truetype)["figures"][0]["derivative"]

        def change_to_truetype(writer: PdfWriter) -> None:
            first_font(writer, "/Type1")[NameObject("/Subtype")] = NameObject(
                "/TrueType"
            )

        rewrite_pdf(truetype_path, change_to_truetype)
        update_derivative_digest(truetype, 0)
        require_failure(
            truetype, "unsupported font subtype /TrueType", "TrueType mutation"
        )

        proprietary_name = case("proprietary-name")
        proprietary_name_path = (
            proprietary_name
            / load_manifest(proprietary_name)["figures"][0]["derivative"]
        )

        def change_to_proprietary_name(writer: PdfWriter) -> None:
            first_font(writer, "/Type1")[NameObject("/BaseFont")] = NameObject(
                "/ABCDEF+HelveticaNeue"
            )

        rewrite_pdf(proprietary_name_path, change_to_proprietary_name)
        update_derivative_digest(proprietary_name, 0)
        require_failure(
            proprietary_name,
            "unapproved, generic, or proprietary font",
            "proprietary BaseFont mutation",
        )

        generic_name = case("generic-name")
        generic_name_path = (
            generic_name / load_manifest(generic_name)["figures"][0]["derivative"]
        )

        def change_to_generic_name(writer: PdfWriter) -> None:
            first_font(writer, "/Type1")[NameObject("/BaseFont")] = NameObject(
                "/ABCDEF+Sans"
            )

        rewrite_pdf(generic_name_path, change_to_generic_name)
        update_derivative_digest(generic_name, 0)
        require_failure(
            generic_name,
            "unapproved, generic, or proprietary font",
            "generic BaseFont mutation",
        )

        descriptor_name = case("descriptor-name")
        descriptor_name_path = (
            descriptor_name / load_manifest(descriptor_name)["figures"][0]["derivative"]
        )

        def mismatch_descriptor_name(writer: PdfWriter) -> None:
            type1_descriptor(writer)[NameObject("/FontName")] = NameObject(
                "/ABCDEF+SourceSansPro-Regular"
            )

        rewrite_pdf(descriptor_name_path, mismatch_descriptor_name)
        update_derivative_digest(descriptor_name, 0)
        require_failure(
            descriptor_name,
            "FontName does not match BaseFont",
            "descriptor-name mutation",
        )

        descendant_subtype = case("descendant-subtype")
        descendant_subtype_path = (
            descendant_subtype
            / load_manifest(descendant_subtype)["figures"][0]["derivative"]
        )

        def change_descendant_subtype(writer: PdfWriter) -> None:
            type0_parts(writer)[1][NameObject("/Subtype")] = NameObject("/CIDFontType2")

        rewrite_pdf(descendant_subtype_path, change_descendant_subtype)
        update_derivative_digest(descendant_subtype, 0)
        require_failure(
            descendant_subtype,
            "descendant is not CIDFontType0",
            "Type0 descendant mutation",
        )

        manifest_inventory = case("manifest-inventory")
        manifest_inventory_data = load_manifest(manifest_inventory)
        manifest_inventory_data["figures"][0]["font_inventory"][0][
            "postscript_name"
        ] = "SourceSansPro-Regular"
        save_manifest(manifest_inventory, manifest_inventory_data)
        require_failure(
            manifest_inventory,
            "manifest figure 1 font inventory changed",
            "manifest font-inventory mutation",
        )

        symbolic = case("symbolic")
        symbolic_manifest = load_manifest(symbolic)
        symbolic_path = symbolic / symbolic_manifest["figures"][0]["derivative"]
        target_path = symbolic / symbolic_manifest["figures"][1]["derivative"]
        symbolic_path.unlink()
        symbolic_path.symlink_to(target_path)
        require_failure(
            symbolic, "absent, non-regular, or symbolic", "symlink mutation"
        )

        bound_symbolic = case("bound-symbolic")
        bound_symbolic_manifest = load_manifest(bound_symbolic)
        bound_symbolic_path = (
            bound_symbolic / bound_symbolic_manifest["third_party_notice"]["path"]
        )
        bound_symbolic_path.unlink()
        bound_symbolic_path.symlink_to(
            bound_symbolic / bound_symbolic_manifest["regeneration_contract"]["path"]
        )
        require_failure(
            bound_symbolic,
            "absent, non-regular, or symbolic",
            "bound-file symlink mutation",
        )

        missing_boundary = case("missing-boundary")
        boundary_manifest = load_manifest(missing_boundary)
        boundary_manifest["claim_boundary"] = ""
        save_manifest(missing_boundary, boundary_manifest)
        require_failure(
            missing_boundary,
            "claim_boundary lost a required nonclaim",
            "claim-boundary mutation",
        )

        missing_closure = case("missing-closure")
        closure_manifest = load_manifest(missing_closure)
        closure_manifest["closure_limitation"] = ""
        save_manifest(missing_closure, closure_manifest)
        require_failure(
            missing_closure,
            "closure_limitation lost a required nonclaim",
            "closure-boundary mutation",
        )

        missing_accessibility = case("missing-accessibility")
        accessibility_manifest = load_manifest(missing_accessibility)
        accessibility_manifest["accessibility_boundary"] = ""
        save_manifest(missing_accessibility, accessibility_manifest)
        require_failure(
            missing_accessibility,
            "accessibility_boundary lost a required nonclaim",
            "accessibility-boundary mutation",
        )

        overclaim = case("overclaim")
        overclaim_manifest = load_manifest(overclaim)
        overclaim_manifest["claim_boundary"] = (
            "The command proves reproducibility, equivalence, accessibility, and font rights."
        )
        save_manifest(overclaim, overclaim_manifest)
        require_failure(
            overclaim, "claim_boundary lost a required nonclaim", "overclaim mutation"
        )

    print(
        "Mathematical results guide figure-asset self-test passed: "
        f"baseline_modes=2 hostile_mutations={case_number} modes_per_mutation=2."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
