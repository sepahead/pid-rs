#!/usr/bin/env python3
"""Validate the results guide's digest-bound static open-font figures.

This source-specific gate binds the reviewed derivatives, exact SVG font-family
contracts, regeneration authority, font provenance, and third-party notice. It
also rejects active content and unsupported PDF font representations. These
checks do not establish visual equivalence, accessibility, legal compliance in
every distribution scenario, or hermetic cross-host reproducibility.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any, NoReturn

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject


EXPECTED_FIGURES = (
    {
        "source": "audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg",
        "source_sha256": "e79ef4f3290f094efc1f786977800f4d4bd8a101760f57ed528c988d6d621042",
        "derivative": "audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf",
        "derivative_sha256": "7d873332c3eb890d35457cd66d3dea9574d164d90826c6911e77019d9490dc61",
        "pdf_bytes": 82732,
        "media_box_tokens": ["0", "0", "453.543307", "328.818898"],
        "css_family": "Source Sans Pro",
        "css_weights": {400, 600, 700},
        "font_inventory": [
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Bold"},
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Regular"},
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Semibold"},
            {"subtype": "Type0", "postscript_name": "SourceSansPro-Regular"},
        ],
    },
    {
        "source": "audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg",
        "source_sha256": "bb315a5282dce90a25988f92ab7b5ecf6a8fe530d33de1ddaef8a81ca2e1a775",
        "derivative": "audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf",
        "derivative_sha256": "41d591a7e75b4d1fb44dad06671cf6a21256dc1fcf958b304419012fcc30a3c8",
        "pdf_bytes": 138292,
        "media_box_tokens": ["0", "0", "510.23622", "419.527559"],
        "css_family": "Source Sans Pro",
        "css_weights": {400, 600, 700},
        "font_inventory": [
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Bold"},
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Regular"},
            {"subtype": "Type1", "postscript_name": "SourceSansPro-Semibold"},
            {"subtype": "Type0", "postscript_name": "SourceSansPro-Semibold"},
        ],
    },
    {
        "source": (
            "audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/"
            "audit-coordinate-crosswalk.svg"
        ),
        "source_sha256": "5619f118cf53a11f16524c906f1d4542e22ebea685161998aade8acc5bae469a",
        "derivative": (
            "audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/"
            "audit-coordinate-crosswalk.pdf"
        ),
        "derivative_sha256": "6cfa13f06f20b6240abb3b28e4aca60611b410fa88c9eb7a0074f2985bf1aa02",
        "pdf_bytes": 77858,
        "media_box_tokens": ["0", "0", "900", "517.5"],
        "css_family": "Latin Modern Sans",
        "css_weights": {400, 700},
        "font_inventory": [
            {"subtype": "Type1", "postscript_name": "LMSans10-Bold"},
            {"subtype": "Type1", "postscript_name": "LMSans10-Regular"},
            {"subtype": "Type0", "postscript_name": "LMSans10-Regular"},
        ],
    },
)
EXPECTED_BINDINGS = {
    "regeneration_contract": {
        "path": (
            "audit/formal/latex/mathematical-results-guide/"
            "open-font-figure-regeneration-v1.json"
        ),
        "sha256": "73255547d47a3f64ae690d51a99b3e1c62d5de049f1edb59487ed1b0f75fbd80",
    },
    "regenerator": {
        "path": "scripts/regenerate-mathematical-results-guide-open-font-figures.py",
        "sha256": "bc28bc80313907ec44d51db212f1a497513131f35134e5e8297fe90d64f0fbd5",
    },
    "third_party_notice": {
        "path": "THIRD_PARTY_NOTICES.md",
        "sha256": "4279f2628c79bfdc9c226d05c55bf7c643e70b14fa3b03033290f5d91d54ff0d",
    },
}
EXPECTED_LICENSE_ARTIFACTS = [
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "source-sans-pro-ofl-1.1-tex-live-2024.txt"
        ),
        "bytes": 4529,
        "sha256": "4a4a4179a96b5ef6786186d199f0d049b151352f460b8d2f3c00083792f37dd9",
        "role": (
            "Exact installed TeX Live 2024 Source Sans Pro package license evidence; "
            "its generic 2010/2012 header does not replace the accepted OTF programs' "
            "2010-2019 metadata."
        ),
    },
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "gust-font-license-1.0-tex-live-2024.txt"
        ),
        "bytes": 1377,
        "sha256": "49ea6cb9257bbee0a3979c48a774cd221550ac1c20c95549efe45fc99cc18050",
        "role": "Exact installed TeX Live 2024 GUST Font License 1.0 evidence.",
    },
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "manifest-latin-modern-2.004-tex-live-2024.txt"
        ),
        "bytes": 52635,
        "sha256": "402c79f4ede8548a6fe6f82f42f0288cb0243ba2403dfdeeaadf55d189a46fae",
        "role": (
            "Exact installed TeX Live 2024 Latin Modern v2.004 package manifest "
            "evidence; this is distinct from the GUST license text."
        ),
    },
]
EXPECTED_FONT_INPUTS = [
    {
        "filename": "SourceSansPro-Regular.otf",
        "family": "Source Sans Pro",
        "style": "Regular",
        "postscript_name": "SourceSansPro-Regular",
        "version": "3.006",
        "sha256": "7134d229b15cdd0827376d8a24f6f531f616eb1b3fecd16e1cf8a86d0bf6bc51",
        "bytes": 293200,
        "license": "SIL Open Font License 1.1",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "SourceSansPro-Semibold.otf",
        "family": "Source Sans Pro",
        "style": "Semibold",
        "postscript_name": "SourceSansPro-Semibold",
        "version": "3.006",
        "sha256": "aa53ed4fc17334a0c2ee8412c1e4e728bfb732a96b119164f7354343dad8f2f2",
        "bytes": 295952,
        "license": "SIL Open Font License 1.1",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "SourceSansPro-Bold.otf",
        "family": "Source Sans Pro",
        "style": "Bold",
        "postscript_name": "SourceSansPro-Bold",
        "version": "3.006",
        "sha256": "daccddbe3dd60fe10f6e8a785eda187925da6b611141024dffa43626998dfc7c",
        "bytes": 298076,
        "license": "SIL Open Font License 1.1",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "lmsans10-regular.otf",
        "family": "Latin Modern Sans",
        "style": "10 Regular",
        "postscript_name": "LMSans10-Regular",
        "version": "2.004",
        "sha256": "d431b786b9b603662718e79cfe9b441f47a8b0b3e854dde89d5acb3ed7cfd682",
        "bytes": 95128,
        "license": "GUST Font License 1.0",
        "license_identifier": "LicenseRef-GUST-Font-License-1.0",
    },
    {
        "filename": "lmsans10-bold.otf",
        "family": "Latin Modern Sans",
        "style": "10 Bold",
        "postscript_name": "LMSans10-Bold",
        "version": "2.004",
        "sha256": "a597b710326c1a8a2c7238d808e5d38711638a72a32383478db4829d63afd687",
        "bytes": 107448,
        "license": "GUST Font License 1.0",
        "license_identifier": "LicenseRef-GUST-Font-License-1.0",
    },
]
EXPECTED_RENDERER = {
    "command": "rsvg-convert --format=pdf --keep-aspect-ratio --output=DERIVATIVE SOURCE",
    "rsvg_convert": "2.62.3",
    "cairo": "1.18.4",
    "pango": "1.57.1",
    "harfbuzz": "14.2.1",
    "fontconfig": "2.18.1",
    "reviewed_platform": "Darwin arm64",
}
EXPECTED_MANIFEST_KEYS = {
    "format_version",
    "purpose",
    "source_date_epoch",
    "regeneration_status",
    "renderer",
    "regeneration_contract",
    "regenerator",
    "third_party_notice",
    "license_artifacts",
    "raw_font_files_tracked_in_repository",
    "font_inputs",
    "closure_limitation",
    "accessibility_boundary",
    "claim_boundary",
    "figures",
}
EXPECTED_FIGURE_KEYS = {
    "source",
    "source_sha256",
    "derivative",
    "derivative_sha256",
    "pdf_bytes",
    "pdf_header",
    "media_box_tokens",
    "font_resources",
    "font_inventory",
}
ALLOWED_POSTSCRIPT_NAMES = {font["postscript_name"] for font in EXPECTED_FONT_INPUTS}
FORBIDDEN_KEYS = {
    "/A",
    "/AA",
    "/AcroForm",
    "/AF",
    "/Collection",
    "/EmbeddedFiles",
    "/EF",
    "/ImportData",
    "/JavaScript",
    "/JS",
    "/Launch",
    "/Movie",
    "/OpenAction",
    "/RichMedia",
    "/Sound",
    "/SubmitForm",
    "/XFA",
}
FORBIDDEN_ACTION_NAMES = {
    "/GoToE",
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Movie",
    "/Rendition",
    "/RichMediaExecute",
    "/Sound",
    "/SubmitForm",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SUBSET_FONT_RE = re.compile(r"/(?P<prefix>[A-Z]{6})\+(?P<name>[A-Za-z0-9_.-]+)\Z")
FONT_FAMILY_DECL_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.IGNORECASE)
FONT_FAMILY_ATTR_RE = re.compile(r"\bfont-family\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)
FONT_SHORTHAND_RE = re.compile(r"(?<![-\w])font\s*:\s*([^;}]+)", re.IGNORECASE)
FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([0-9]+)", re.IGNORECASE)
FONT_WEIGHT_ATTR_RE = re.compile(
    r"\bfont-weight\s*=\s*['\"]([0-9]+)['\"]", re.IGNORECASE
)
FONT_SHORTHAND_WEIGHT_RE = re.compile(
    r"(?<![-\w])font\s*:\s*([0-9]+)\s+", re.IGNORECASE
)
FORBIDDEN_SVG_FONT_RE = re.compile(
    r"(?:helvetica|arial|calibri|sans-serif|system-ui|-apple-system|"
    r"blinkmacsystemfont|times(?:\s+new\s+roman)?|"
    r"\b(?:serif|monospace|cursive|fantasy|emoji|math|fangsong)\b)",
    re.IGNORECASE,
)
MAX_PDF_BYTES = 1024 * 1024


def fail(message: str) -> NoReturn:
    raise SystemExit(f"Mathematical results guide figure-asset check failed: {message}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json_no_duplicates(path: pathlib.Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        fail(f"cannot read manifest: {error}")


def exact_regular(root: pathlib.Path, relative: str) -> pathlib.Path:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        fail(f"absent, non-regular, or symbolic path: {relative}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail(f"cannot resolve {relative}: {error}")
    if root not in resolved.parents:
        fail(f"path escapes repository root: {relative}")
    return resolved


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_required(dictionary: DictionaryObject, key: str, label: str) -> Any:
    if key not in dictionary:
        fail(f"{label} lacks {key}")
    return dictionary.raw_get(key)


def dereference(value: Any) -> Any:
    seen: set[tuple[int, int]] = set()
    while isinstance(value, IndirectObject):
        key = (value.idnum, value.generation)
        if key in seen:
            fail(f"indirect-object cycle at {key[0]} {key[1]}")
        seen.add(key)
        value = value.get_object()
    return value


def reject_active_content(value: Any, label: str) -> None:
    seen_indirect: set[tuple[int, int]] = set()
    seen_direct: set[int] = set()

    def walk(current: Any, route: str) -> None:
        if isinstance(current, IndirectObject):
            key = (current.idnum, current.generation)
            if key in seen_indirect:
                return
            seen_indirect.add(key)
            walk(current.get_object(), f"{route}->{key[0]} {key[1]} R")
            return
        if isinstance(current, DictionaryObject):
            identity = id(current)
            if identity in seen_direct:
                return
            seen_direct.add(identity)
            for key in current.keys():
                key_name = str(key)
                if key_name in FORBIDDEN_KEYS:
                    fail(f"{label} contains forbidden key {key_name} at {route}")
                raw = current.raw_get(key)
                if key_name == "/S" and str(dereference(raw)) in FORBIDDEN_ACTION_NAMES:
                    fail(f"{label} contains forbidden action {raw} at {route}")
                walk(raw, f"{route}/{key_name.lstrip('/')}")
            return
        if isinstance(current, ArrayObject):
            identity = id(current)
            if identity in seen_direct:
                return
            seen_direct.add(identity)
            for index, item in enumerate(current):
                walk(item, f"{route}[{index}]")

    walk(value, "catalog")


def require_embedded_stream(
    value: Any, label: str, subtype: str | None = None
) -> StreamObject:
    if not isinstance(value, IndirectObject):
        fail(f"{label} is not an indirect stream")
    stream = dereference(value)
    if not isinstance(stream, StreamObject):
        fail(f"{label} is not a stream")
    if subtype is not None and str(stream.get("/Subtype")) != subtype:
        fail(f"{label} subtype is not {subtype}")
    try:
        data = stream.get_data()
    except Exception as error:
        fail(f"{label} cannot be decoded: {error}")
    if not isinstance(data, bytes) or not data:
        fail(f"{label} is empty")
    return stream


def normalized_subset_name(value: Any, label: str) -> str:
    token = str(value)
    match = SUBSET_FONT_RE.fullmatch(token)
    if match is None:
        fail(f"{label} is not a six-uppercase-letter subset font name")
    name = match.group("name")
    if name not in ALLOWED_POSTSCRIPT_NAMES:
        fail(f"{label} names an unapproved, generic, or proprietary font: {name}")
    return name


def require_descriptor(
    value: Any, expected_font_name: str, label: str, stream_subtype: str
) -> None:
    descriptor = dereference(value)
    if not isinstance(descriptor, DictionaryObject):
        fail(f"{label} is not a FontDescriptor dictionary")
    descriptor_name = str(descriptor.get("/FontName"))
    if descriptor_name != expected_font_name:
        fail(f"{label} FontName does not match BaseFont")
    program_keys = {
        str(key) for key in descriptor.keys() if str(key).startswith("/FontFile")
    }
    if program_keys != {"/FontFile3"}:
        fail(f"{label} must contain only an embedded FontFile3")
    require_embedded_stream(
        descriptor.raw_get("/FontFile3"), f"{label} /FontFile3", stream_subtype
    )


def validate_font(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, IndirectObject):
        fail(f"{label} is not an indirect font resource")
    font = dereference(value)
    if not isinstance(font, DictionaryObject) or str(font.get("/Type")) != "/Font":
        fail(f"{label} is not a Font dictionary")
    require_embedded_stream(
        raw_required(font, "/ToUnicode", label), f"{label} /ToUnicode"
    )
    subtype = str(font.get("/Subtype"))
    base_font = str(font.get("/BaseFont"))
    postscript_name = normalized_subset_name(base_font, f"{label} /BaseFont")
    if subtype == "/Type1":
        if str(font.get("/Encoding")) != "/WinAnsiEncoding":
            fail(f"{label} Type1 encoding is not WinAnsiEncoding")
        require_descriptor(
            raw_required(font, "/FontDescriptor", label),
            base_font,
            f"{label} /FontDescriptor",
            "/Type1C",
        )
        return {"subtype": "Type1", "postscript_name": postscript_name}
    if subtype == "/Type0":
        if str(font.get("/Encoding")) != "/Identity-H":
            fail(f"{label} Type0 encoding is not Identity-H")
        descendants = dereference(raw_required(font, "/DescendantFonts", label))
        if not isinstance(descendants, ArrayObject) or len(descendants) != 1:
            fail(f"{label} does not have exactly one descendant font")
        descendant = dereference(list.__getitem__(descendants, 0))
        if (
            not isinstance(descendant, DictionaryObject)
            or str(descendant.get("/Type")) != "/Font"
            or str(descendant.get("/Subtype")) != "/CIDFontType0"
        ):
            fail(f"{label} descendant is not CIDFontType0")
        if str(descendant.get("/BaseFont")) != base_font:
            fail(f"{label} descendant BaseFont does not match parent BaseFont")
        require_descriptor(
            raw_required(descendant, "/FontDescriptor", f"{label} descendant"),
            base_font,
            f"{label} descendant /FontDescriptor",
            "/CIDFontType0C",
        )
        return {"subtype": "Type0", "postscript_name": postscript_name}
    fail(f"{label} has unsupported font subtype {subtype}")


def validate_svg_font_contract(
    path: pathlib.Path, relative: str, expected: dict[str, Any]
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail(f"cannot read SVG {relative}: {error}")
    if any(
        token in text.lower()
        for token in ("<!doctype", "<!entity", "@font-face", "@import")
    ):
        fail(f"{relative} contains an external or embedded font-resolution directive")
    forbidden = FORBIDDEN_SVG_FONT_RE.search(text)
    if forbidden is not None:
        fail(
            f"{relative} contains forbidden fallback/proprietary family {forbidden.group(0)!r}"
        )

    expected_family = expected["css_family"]
    observed_families: list[str] = []
    for raw_value in FONT_FAMILY_DECL_RE.findall(text):
        value = raw_value.strip()
        if "," in value:
            fail(f"{relative} contains a font-family fallback list")
        observed_families.append(value.strip("\"'"))
    for _, raw_value in FONT_FAMILY_ATTR_RE.findall(text):
        value = raw_value.strip()
        if "," in value:
            fail(f"{relative} contains a font-family fallback list")
        observed_families.append(value)
    for raw_value in FONT_SHORTHAND_RE.findall(text):
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", raw_value)
        if len(quoted) != 1 or "," in raw_value:
            fail(f"{relative} font shorthand does not name one exact quoted family")
        observed_families.append(quoted[0])
    if not observed_families or any(
        family != expected_family for family in observed_families
    ):
        fail(f"{relative} does not use only the exact {expected_family!r} CSS family")

    observed_weights = {
        int(value)
        for value in FONT_WEIGHT_RE.findall(text)
        + FONT_WEIGHT_ATTR_RE.findall(text)
        + FONT_SHORTHAND_WEIGHT_RE.findall(text)
    }
    if observed_weights != expected["css_weights"]:
        fail(f"{relative} CSS font-weight inventory changed")


def validate_pdf(path: pathlib.Path, relative: str, entry: dict[str, Any]) -> None:
    size = path.stat().st_size
    if size > MAX_PDF_BYTES:
        fail(f"{relative} exceeds the {MAX_PDF_BYTES}-byte bound")
    if size != entry["pdf_bytes"]:
        fail(f"{relative} byte length changed")
    expected_header = entry["pdf_header"].encode("ascii")
    with path.open("rb") as stream:
        if stream.read(len(expected_header)) != expected_header:
            fail(f"{relative} PDF header changed")
    try:
        reader = PdfReader(path, strict=True)
    except Exception as error:
        fail(f"{relative} is not a strict readable PDF: {error}")
    if reader.is_encrypted:
        fail(f"{relative} is encrypted")
    if len(reader.pages) != 1:
        fail(f"{relative} has {len(reader.pages)} pages instead of one")
    root = dereference(reader.trailer.raw_get("/Root"))
    if not isinstance(root, DictionaryObject):
        fail(f"{relative} catalog is not a dictionary")
    if {str(key) for key in root.keys()} != {"/Type", "/Pages"}:
        fail(f"{relative} catalog keys changed")
    reject_active_content(root, relative)
    page = reader.pages[0]
    if page.get("/Annots") is not None:
        fail(f"{relative} contains annotations")
    if int(page.get("/Rotate", 0)) != 0:
        fail(f"{relative} page rotation is not zero")
    media_box = dereference(page.raw_get("/MediaBox"))
    if not isinstance(media_box, ArrayObject) or len(media_box) != 4:
        fail(f"{relative} MediaBox is not a four-element array")
    media_box_tokens = [str(list.__getitem__(media_box, index)) for index in range(4)]
    if media_box_tokens != entry["media_box_tokens"]:
        fail(f"{relative} MediaBox tokens changed")
    resources = dereference(page.raw_get("/Resources"))
    if not isinstance(resources, DictionaryObject) or not resources:
        fail(f"{relative} has no page resources")
    fonts = dereference(raw_required(resources, "/Font", f"{relative} resources"))
    if not isinstance(fonts, DictionaryObject) or len(fonts) != entry["font_resources"]:
        fail(f"{relative} font-resource inventory changed")
    inventory = [
        validate_font(fonts.raw_get(name), f"{relative} font {name}")
        for name in sorted(fonts.keys(), key=str)
    ]
    order = {"Type1": 0, "Type0": 1}
    inventory.sort(key=lambda item: (order[item["subtype"]], item["postscript_name"]))
    if inventory != entry["font_inventory"]:
        fail(f"{relative} normalized font inventory changed")
    content = page.get_contents()
    if content is None:
        fail(f"{relative} has no page content stream")
    try:
        if not content.get_data():
            fail(f"{relative} has an empty page content stream")
    except Exception as error:
        fail(f"{relative} page content cannot be decoded: {error}")


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        fail(
            "usage: check-mathematical-results-guide-figure-assets.py [repository-root]"
        )
    root = (
        pathlib.Path(argv[1]).resolve(strict=True)
        if len(argv) == 2
        else pathlib.Path(__file__).resolve(strict=True).parent.parent
    )
    manifest_relative = (
        "audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
    )
    manifest = load_json_no_duplicates(exact_regular(root, manifest_relative))
    if not isinstance(manifest, dict) or set(manifest) != EXPECTED_MANIFEST_KEYS:
        fail("manifest root schema changed")
    if manifest.get("format_version") != 3:
        fail("manifest format_version is not exactly 3")
    if manifest.get("purpose") != (
        "Digest-bound canonical open-font PDF derivatives used by the mathematical results guide build"
    ):
        fail("manifest purpose changed")
    if manifest.get("source_date_epoch") != 1787875200:
        fail("manifest source_date_epoch changed")
    if manifest.get("regeneration_status") != (
        "reviewed-host isolated-font repeat byte-equality; cross-host closure incomplete"
    ):
        fail("manifest regeneration status changed")
    if manifest.get("renderer") != EXPECTED_RENDERER:
        fail("manifest renderer observations changed")
    if manifest.get("raw_font_files_tracked_in_repository") is not False:
        fail("manifest must state that raw font files are not tracked")
    if manifest.get("font_inputs") != EXPECTED_FONT_INPUTS:
        fail("manifest font provenance or license inventory changed")

    for field, expected_binding in EXPECTED_BINDINGS.items():
        if manifest.get(field) != expected_binding:
            fail(f"manifest {field} binding changed")
        bound_path = exact_regular(root, expected_binding["path"])
        if sha256(bound_path) != expected_binding["sha256"]:
            fail(f"bound {field} digest changed")

    if manifest.get("license_artifacts") != EXPECTED_LICENSE_ARTIFACTS:
        fail("manifest license-artifact bindings changed")
    for ordinal, artifact in enumerate(EXPECTED_LICENSE_ARTIFACTS, 1):
        artifact_path = exact_regular(root, artifact["path"])
        if artifact_path.stat().st_size != artifact["bytes"]:
            fail(f"bound license artifact {ordinal} byte length changed")
        if sha256(artifact_path) != artifact["sha256"]:
            fail(f"bound license artifact {ordinal} digest changed")

    required_boundaries = {
        "closure_limitation": (
            "exact byte hashes",
            "byte-identically on the reviewed macOS host",
            "same-host evidence only",
            "not a hermetic or cross-host reproducibility proof",
            "authenticated acquisition chains are not captured",
        ),
        "accessibility_boundary": (
            "no Figure structure roles or Alt entries",
            "do not survive",
            "Neither these derivatives nor their inclusion prove PDF/UA",
        ),
        "claim_boundary": (
            "do not by themselves prove visual or semantic equivalence",
            "legal compliance in every redistribution scenario",
            "source-font authenticity",
            "supply-chain integrity",
            "input programs are not tracked",
            "exact local license/manifest evidence are recorded and digest-bound",
            "without authenticating a package, download, or upstream history",
            "without making a legal determination",
            "human visual review",
            "early raw derivative byte cap only",
            "not a hostile-input resource sandbox or decoded-stream-size bound",
        ),
    }
    for field, phrases in required_boundaries.items():
        text = manifest.get(field)
        if not isinstance(text, str) or any(phrase not in text for phrase in phrases):
            fail(f"manifest {field} lost a required nonclaim")

    figures = manifest.get("figures")
    if not isinstance(figures, list) or len(figures) != len(EXPECTED_FIGURES):
        fail("manifest figure inventory changed")
    for ordinal, (entry, expected) in enumerate(zip(figures, EXPECTED_FIGURES), 1):
        if not isinstance(entry, dict) or set(entry) != EXPECTED_FIGURE_KEYS:
            fail(f"manifest figure {ordinal} schema changed")
        if (entry.get("source"), entry.get("derivative")) != (
            expected["source"],
            expected["derivative"],
        ):
            fail(f"manifest figure {ordinal} source/derivative relation changed")
        if entry.get("font_inventory") != expected["font_inventory"]:
            fail(f"manifest figure {ordinal} font inventory changed")
        if entry.get("font_resources") != len(expected["font_inventory"]):
            fail(f"manifest figure {ordinal} font-resource count changed")
        if (
            entry.get("pdf_header") != "%PDF-1.7"
            or not isinstance(entry.get("pdf_bytes"), int)
            or not 0 < entry["pdf_bytes"] <= MAX_PDF_BYTES
            or not isinstance(entry.get("media_box_tokens"), list)
            or len(entry["media_box_tokens"]) != 4
            or not all(isinstance(token, str) for token in entry["media_box_tokens"])
        ):
            fail(f"manifest figure {ordinal} PDF contract changed")
        for role in ("source", "derivative"):
            digest = entry.get(f"{role}_sha256")
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                fail(
                    f"manifest figure {ordinal} {role} digest is not lowercase SHA-256"
                )
            path = exact_regular(root, entry[role])
            if role == "source":
                validate_svg_font_contract(path, entry[role], expected)
            elif path.stat().st_size > MAX_PDF_BYTES:
                fail(f"{entry[role]} exceeds the {MAX_PDF_BYTES}-byte bound")
            actual = sha256(path)
            if actual != digest:
                fail(
                    f"manifest figure {ordinal} {role} digest changed: "
                    f"expected {digest}, observed {actual}"
                )
        validate_pdf(
            exact_regular(root, entry["derivative"]), entry["derivative"], entry
        )
        canonical_fields = {
            "source_sha256",
            "derivative_sha256",
            "pdf_bytes",
            "media_box_tokens",
        }
        if any(entry[field] != expected[field] for field in canonical_fields):
            fail(f"manifest figure {ordinal} canonical byte contract changed")

    print(
        "Mathematical results guide figure-asset check passed: "
        "3 digest-bound static one-page open-font CFF derivatives; "
        "regeneration closure remains declared cross-host incomplete."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
