#!/usr/bin/env python3
"""Fail-closed mutation suite for the guide PDF font-alpha comparator.

The operational comparator binds the exact canonical guide and retained TeX
Live 2023 fixture. It admits either a distinct-file byte-identical canonical
copy or an exceptional candidate that is byte-exact to the fixture or differs
only in its strict duplicated final-trailer ID payloads. This suite tests that
raw outer contract with retained artifacts and hostile files. It also calls the
production semantic core with small generated PDFs so mutations can reach the
typed font closure, resource graph, content lexer, and global binding checks
instead of being masked by the outer source-profile and raw-file pins.

The semantic-core hook is not a production bypass: the comparator CLI invokes
it only after the candidate passes the complete relaxed-terminal structure
policy and the exact legacy structure profile, and then applies every pinned
legacy operation and mapping constant before it publishes evidence.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import io
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, Callable, NoReturn

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)


CHECK_NAME = "Mathematical results guide font-alpha comparator self-test"
ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py"
STRUCTURE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-structure.py"
ID_VARIANCE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-id-variance.py"


class SelfTestError(Exception):
    """A test fixture, expected disposition, or custody invariant failed."""


@dataclass
class Ledger:
    """Exact test counts, separated by the obligation each case exercises."""

    controls: int = 0
    semantic_hostiles: int = 0
    profile_hostiles: int = 0
    raw_boundary_hostiles: int = 0
    structure_hostiles: int = 0
    custody_hostiles: int = 0
    dependency_hostiles: int = 0
    static_guards: int = 0

    def total(self) -> int:
        return sum(dataclasses.astuple(self))


@dataclass(frozen=True)
class FontSpec:
    """Typed font-closure inputs for one generated test resource."""

    base_font: str
    encoding_base: str
    encoding_glyph: str
    descriptor_ascent: int
    descriptor_flags: int
    program: bytes
    to_unicode: bytes
    width: int


@dataclass(frozen=True)
class PageSpec:
    """One generated page's complete resource and decoded-content surface."""

    fonts: tuple[tuple[str, FontSpec], ...]
    content: bytes
    xobject_name: str = "/X1"
    xobject_data: bytes = b"q 1 0 0 1 0 0 cm Q\n"
    procset: tuple[str, ...] = ("/PDF", "/Text")


FONT_A = FontSpec(
    base_font="/SelfTestAlpha",
    encoding_base="/WinAnsiEncoding",
    encoding_glyph="/A",
    descriptor_ascent=700,
    descriptor_flags=32,
    program=b"self-test-font-program-alpha\x00\x01",
    to_unicode=b"/CIDInit /ProcSet findresource begin\n% alpha cmap\nend\n",
    width=500,
)
FONT_B = FontSpec(
    base_font="/SelfTestBeta",
    encoding_base="/MacRomanEncoding",
    encoding_glyph="/B",
    descriptor_ascent=710,
    descriptor_flags=4,
    program=b"self-test-font-program-beta\x02\x03",
    to_unicode=b"/CIDInit /ProcSet findresource begin\n% beta cmap\nend\n",
    width=510,
)
FONT_C = FontSpec(
    base_font="/SelfTestGamma",
    encoding_base="/WinAnsiEncoding",
    encoding_glyph="/C",
    descriptor_ascent=720,
    descriptor_flags=64,
    program=b"self-test-font-program-gamma\x04\x05",
    to_unicode=b"/CIDInit /ProcSet findresource begin\n% gamma cmap\nend\n",
    width=520,
)


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_checker() -> Any:
    if not CHECK.is_file() or CHECK.is_symlink():
        fail(f"production comparator is absent or symbolic: {CHECK}")
    specification = importlib.util.spec_from_file_location(
        "mathematical_results_guide_font_alpha_for_self_test",
        CHECK,
    )
    if specification is None or specification.loader is None:
        fail("cannot load the production comparator")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


ALPHA = load_checker()


def content(
    first: str,
    second: str,
    *,
    first_size: bytes = b"12",
    second_size: bytes = b"9",
    literal: bytes = b"(Hello)",
    hex_string: bytes = b"<4869>",
    comment: bytes = b"% stable self-test comment with opaque /F777 1 Tf\n",
    first_text_operator: bytes = b"Tj",
) -> bytes:
    """Create a small exact content stream with two used font resources."""

    return (
        b"q\n"
        + comment
        + b"BT\n"
        + first.encode("ascii")
        + b" "
        + first_size
        + b" Tf\n"
        + literal
        + b" "
        + first_text_operator
        + b"\n"
        + second.encode("ascii")
        + b" "
        + second_size
        + b" Tf\n"
        + hex_string
        + b" Tj\nET\n"
        + b"/X1 Do\nQ\n"
    )


def add_font(writer: PdfWriter, specification: FontSpec) -> Any:
    """Add one indirect font closure, including descriptor and program bytes."""

    program = DecodedStreamObject()
    program.set_data(specification.program)
    program_reference = writer._add_object(program)

    descriptor = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/FontDescriptor"),
            NameObject("/FontName"): NameObject(specification.base_font),
            NameObject("/Flags"): NumberObject(specification.descriptor_flags),
            NameObject("/FontBBox"): ArrayObject(
                [
                    NumberObject(0),
                    NumberObject(-200),
                    NumberObject(1000),
                    NumberObject(900),
                ]
            ),
            NameObject("/ItalicAngle"): NumberObject(0),
            NameObject("/Ascent"): NumberObject(specification.descriptor_ascent),
            NameObject("/Descent"): NumberObject(-200),
            NameObject("/CapHeight"): NumberObject(680),
            NameObject("/StemV"): NumberObject(80),
            NameObject("/FontFile2"): program_reference,
        }
    )
    descriptor_reference = writer._add_object(descriptor)

    to_unicode = DecodedStreamObject()
    to_unicode.set_data(specification.to_unicode)
    to_unicode_reference = writer._add_object(to_unicode)

    encoding = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Encoding"),
            NameObject("/BaseEncoding"): NameObject(specification.encoding_base),
            NameObject("/Differences"): ArrayObject(
                [NumberObject(65), NameObject(specification.encoding_glyph)]
            ),
        }
    )
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/TrueType"),
            NameObject("/BaseFont"): NameObject(specification.base_font),
            NameObject("/Encoding"): encoding,
            NameObject("/FirstChar"): NumberObject(65),
            NameObject("/LastChar"): NumberObject(65),
            NameObject("/Widths"): ArrayObject([NumberObject(specification.width)]),
            NameObject("/FontDescriptor"): descriptor_reference,
            NameObject("/ToUnicode"): to_unicode_reference,
        }
    )
    return writer._add_object(font)


def build_pdf(pages: tuple[PageSpec, ...]) -> bytes:
    """Build deterministic, parseable PDFs used only by the semantic-core tests."""

    writer = PdfWriter()
    for page_specification in pages:
        page = writer.add_blank_page(width=300, height=200)
        fonts = DictionaryObject()
        for name, font_specification in page_specification.fonts:
            fonts[NameObject(name)] = add_font(writer, font_specification)

        xobject = DecodedStreamObject()
        xobject.set_data(page_specification.xobject_data)
        xobject[NameObject("/Type")] = NameObject("/XObject")
        xobject[NameObject("/Subtype")] = NameObject("/Form")
        xobject[NameObject("/BBox")] = ArrayObject(
            [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
        )
        xobject_reference = writer._add_object(xobject)

        resources = DictionaryObject(
            {
                NameObject("/Font"): fonts,
                NameObject("/XObject"): DictionaryObject(
                    {NameObject(page_specification.xobject_name): xobject_reference}
                ),
                NameObject("/ProcSet"): ArrayObject(
                    [NameObject(name) for name in page_specification.procset]
                ),
            }
        )
        page[NameObject("/Resources")] = resources

        page_content = DecodedStreamObject()
        page_content.set_data(page_specification.content)
        page[NameObject("/Contents")] = writer._add_object(page_content)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def standard_pair(
    *,
    reference_fonts: tuple[tuple[str, FontSpec], ...] | None = None,
    candidate_fonts: tuple[tuple[str, FontSpec], ...] | None = None,
    reference_content: bytes | None = None,
    candidate_content: bytes | None = None,
    reference_xobject: bytes = b"q 1 0 0 1 0 0 cm Q\n",
    candidate_xobject: bytes = b"q 1 0 0 1 0 0 cm Q\n",
    reference_xobject_name: str = "/X1",
    candidate_xobject_name: str = "/X1",
    reference_procset: tuple[str, ...] = ("/PDF", "/Text"),
    candidate_procset: tuple[str, ...] = ("/PDF", "/Text"),
) -> tuple[bytes, bytes]:
    """Return a two-font reference/candidate pair with only key/Tf renaming."""

    reference_fonts = reference_fonts or (("/F10", FONT_A), ("/F20", FONT_B))
    candidate_fonts = candidate_fonts or (("/F1", FONT_A), ("/F2", FONT_B))
    reference_content = reference_content or content("/F10", "/F20")
    candidate_content = candidate_content or content("/F1", "/F2")
    reference = build_pdf(
        (
            PageSpec(
                reference_fonts,
                reference_content,
                reference_xobject_name,
                reference_xobject,
                reference_procset,
            ),
        )
    )
    candidate = build_pdf(
        (
            PageSpec(
                candidate_fonts,
                candidate_content,
                candidate_xobject_name,
                candidate_xobject,
                candidate_procset,
            ),
        )
    )
    return reference, candidate


def strict_id_match(data: bytes) -> Any:
    matches = list(ALPHA.ID_VARIANCE.ID_PATTERN.finditer(data))
    require(len(matches) == 1, "raw self-test fixture lacks one strict trailer /ID")
    return matches[0]


def replace_trailer_id(data: bytes, replacement: bytes) -> bytes:
    """Replace both strict trailer-ID payloads without changing any other byte."""

    require(
        len(replacement) == 32
        and all(byte in b"0123456789abcdefABCDEF" for byte in replacement),
        "replacement trailer ID is not 32 hexadecimal bytes",
    )
    match = strict_id_match(data)
    require(
        match.group(1).lower() == match.group(2).lower(),
        "raw self-test fixture trailer ID is not duplicated",
    )
    require(
        match.group(1).lower() != replacement.lower(),
        "replacement trailer ID equals the fixture ID",
    )
    mutated = bytearray(data)
    for group in (1, 2):
        start, end = match.span(group)
        mutated[start:end] = replacement
    return bytes(mutated)


def mutate_non_id_header_byte(data: bytes) -> bytes:
    """Make one fixed same-length raw change outside the final trailer ID."""

    require(data.startswith(b"%PDF-1.7\n"), "raw self-test PDF header changed")
    mutated = bytearray(data)
    mutated[8] = ord(" ")
    return bytes(mutated)


def move_id_outside_final_owner(data: bytes) -> bytes:
    """Relocate the sole raw ID token so the strict owner check must reject it."""

    match = strict_id_match(data)
    raw_id = match.group(0)
    require(
        match.start() > 128 and len(raw_id) < 128, "raw ID relocation bounds changed"
    )
    mutated = bytearray(data)
    mutated[match.start() : match.start() + 3] = b"/IX"
    insertion = 20
    mutated[insertion : insertion + len(raw_id)] = raw_id
    return bytes(mutated)


def expect_alpha_failure(
    ledger: Ledger,
    category: str,
    label: str,
    operation: Callable[[], Any],
    accepted_codes: set[str],
) -> None:
    """Require one lower-layer hostile to fail with an admitted typed code."""

    try:
        operation()
    except ALPHA.AlphaEquivalenceError as error:
        if error.code not in accepted_codes:
            fail(f"{label}: unexpected failure code {error.code!r}: {error}")
    except Exception as error:
        fail(f"{label}: leaked non-contract exception {type(error).__name__}: {error}")
    else:
        fail(f"{label}: hostile mutation was accepted")
    setattr(ledger, category, getattr(ledger, category) + 1)


def record_control(ledger: Ledger, label: str, operation: Callable[[], Any]) -> Any:
    try:
        result = operation()
    except Exception as error:
        fail(f"{label}: control failed with {type(error).__name__}: {error}")
    ledger.controls += 1
    return result


def run_semantic_tests(ledger: Ledger) -> None:
    """Exercise typed equality, binding, lexical, and exact-content obligations."""

    reference, candidate = standard_pair()
    stats = record_control(
        ledger,
        "synthetic two-font alpha-equivalence",
        lambda: ALPHA.compare_font_alpha_core(reference, candidate),
    )
    require(stats.pages == 1, "synthetic control page count changed")
    require(stats.tf_uses == 2, "synthetic control Tf-use count changed")
    require(
        stats.page_font_bindings == 2, "synthetic control font-binding count changed"
    )
    require(
        stats.global_font_mappings == 2,
        "synthetic control global mapping count changed",
    )
    require(
        stats.font_name_pairs == (("/F1", "/F10"), ("/F2", "/F20")),
        "synthetic control mapping changed",
    )

    identity_stats = record_control(
        ledger,
        "synthetic exact-name semantic identity",
        lambda: ALPHA.compare_font_alpha_core(reference, reference),
    )
    require(
        identity_stats.font_name_pairs == (("/F10", "/F10"), ("/F20", "/F20")),
        "semantic identity mapping changed",
    )

    opaque_reference, opaque_candidate = standard_pair(
        reference_content=content(
            "/F10",
            "/F20",
            literal=b"(opaque /F1 88 Tf and \\(nested\\))",
            hex_string=b"<2f4631203838205466>",
        ),
        candidate_content=content(
            "/F1",
            "/F2",
            literal=b"(opaque /F1 88 Tf and \\(nested\\))",
            hex_string=b"<2f4631203838205466>",
        ),
    )
    record_control(
        ledger,
        "font-looking bytes in literal and hex strings remain opaque",
        lambda: ALPHA.compare_font_alpha_core(opaque_reference, opaque_candidate),
    )

    two_page_reference = build_pdf(
        (
            PageSpec((("/F10", FONT_A),), b"BT\n/F10 12 Tf\n(A) Tj\nET\n"),
            PageSpec((("/F20", FONT_B),), b"BT\n/F20 9 Tf\n(B) Tj\nET\n"),
        )
    )
    two_page_candidate = build_pdf(
        (
            PageSpec((("/F1", FONT_A),), b"BT\n/F1 12 Tf\n(A) Tj\nET\n"),
            PageSpec((("/F2", FONT_B),), b"BT\n/F2 9 Tf\n(B) Tj\nET\n"),
        )
    )
    record_control(
        ledger,
        "consistent global mapping across pages",
        lambda: ALPHA.compare_font_alpha_core(two_page_reference, two_page_candidate),
    )

    def core_failure(
        label: str,
        pair: tuple[bytes, bytes],
        *codes: str,
    ) -> None:
        expect_alpha_failure(
            ledger,
            "semantic_hostiles",
            label,
            lambda: ALPHA.compare_font_alpha_core(pair[0], pair[1]),
            set(codes),
        )

    core_failure(
        "font dictionary renamed without matching Tf operands",
        standard_pair(
            candidate_fonts=(("/F3", FONT_A), ("/F4", FONT_B)),
            candidate_content=content("/F1", "/F2"),
        ),
        "font_alpha_unbound",
    )
    core_failure(
        "Tf operands renamed without matching font dictionary",
        standard_pair(candidate_content=content("/F3", "/F4")),
        "font_alpha_unbound",
    )
    core_failure(
        "closures swapped under unchanged candidate Tf names",
        standard_pair(candidate_fonts=(("/F1", FONT_B), ("/F2", FONT_A))),
        "font_alpha_content",
    )
    core_failure(
        "duplicate candidate font closures are ambiguous",
        standard_pair(candidate_fonts=(("/F1", FONT_A), ("/F2", FONT_A))),
        "font_alpha_ambiguous",
    )
    core_failure(
        "duplicate reference font closures are ambiguous",
        standard_pair(reference_fonts=(("/F10", FONT_A), ("/F20", FONT_A))),
        "font_alpha_ambiguous",
    )
    core_failure(
        "unused font resources are rejected",
        standard_pair(
            reference_fonts=(("/F10", FONT_A), ("/F20", FONT_B), ("/F30", FONT_C)),
            candidate_fonts=(("/F1", FONT_A), ("/F2", FONT_B), ("/F3", FONT_C)),
        ),
        "font_alpha_unused",
    )

    inconsistent_candidate = build_pdf(
        (
            PageSpec((("/F1", FONT_A),), b"BT\n/F1 12 Tf\n(A) Tj\nET\n"),
            PageSpec((("/F1", FONT_B),), b"BT\n/F1 9 Tf\n(B) Tj\nET\n"),
        )
    )
    core_failure(
        "one candidate key cannot map to two canonical keys across pages",
        (two_page_reference, inconsistent_candidate),
        "font_alpha_global_binding",
    )
    reverse_collision_reference = build_pdf(
        (
            PageSpec((("/F10", FONT_A),), b"BT\n/F10 12 Tf\n(A) Tj\nET\n"),
            PageSpec((("/F10", FONT_B),), b"BT\n/F10 9 Tf\n(B) Tj\nET\n"),
        )
    )
    core_failure(
        "two candidate keys cannot map to one canonical key across pages",
        (reverse_collision_reference, two_page_candidate),
        "font_alpha_global_binding",
    )

    closure_mutations = (
        ("BaseFont", dataclasses.replace(FONT_A, base_font="/MutatedBaseFont")),
        (
            "ToUnicode",
            dataclasses.replace(FONT_A, to_unicode=FONT_A.to_unicode + b"% changed\n"),
        ),
        (
            "Encoding",
            dataclasses.replace(FONT_A, encoding_base="/MacExpertEncoding"),
        ),
        (
            "encoding Differences",
            dataclasses.replace(FONT_A, encoding_glyph="/Z"),
        ),
        (
            "FontDescriptor",
            dataclasses.replace(FONT_A, descriptor_ascent=701),
        ),
        (
            "descriptor flags",
            dataclasses.replace(FONT_A, descriptor_flags=33),
        ),
        (
            "embedded font program",
            dataclasses.replace(FONT_A, program=FONT_A.program + b"mutation"),
        ),
        ("width array", dataclasses.replace(FONT_A, width=501)),
    )
    for label, mutation in closure_mutations:
        core_failure(
            f"full typed font closure detects {label} mutation",
            standard_pair(candidate_fonts=(("/F1", mutation), ("/F2", FONT_B))),
            "font_alpha_font_closure",
        )

    original_sha256 = ALPHA.hashlib.sha256

    class ConstantHash:
        def __init__(self, _data: bytes = b"") -> None:
            pass

        def update(self, _data: bytes) -> None:
            pass

        def digest(self) -> bytes:
            return b"\x00" * 32

        def hexdigest(self) -> str:
            return "0" * 64

    try:
        ALPHA.hashlib.sha256 = ConstantHash
        core_failure(
            "typed font closure equality is not delegated to SHA-256",
            standard_pair(
                candidate_fonts=(
                    (
                        "/F1",
                        dataclasses.replace(
                            FONT_A, program=b"digest-collision-simulation"
                        ),
                    ),
                    ("/F2", FONT_B),
                )
            ),
            "font_alpha_font_closure",
        )
    finally:
        ALPHA.hashlib.sha256 = original_sha256

    core_failure(
        "non-font XObject bytes cannot drift",
        standard_pair(candidate_xobject=b"q 2 0 0 2 0 0 cm Q\n"),
        "font_alpha_nonfont",
    )
    core_failure(
        "non-font XObject resource names cannot be alpha-renamed",
        standard_pair(candidate_xobject_name="/X2"),
        "font_alpha_nonfont",
    )
    core_failure(
        "non-font ProcSet entries cannot drift",
        standard_pair(candidate_procset=("/PDF", "/Text", "/ImageC")),
        "font_alpha_nonfont",
    )

    content_mutations: tuple[tuple[str, bytes, set[str]], ...] = (
        (
            "Tf size",
            content("/F1", "/F2", first_size=b"13"),
            {"font_alpha_content"},
        ),
        (
            "literal text",
            content("/F1", "/F2", literal=b"(Hallo)"),
            {"font_alpha_content"},
        ),
        (
            "hex text",
            content("/F1", "/F2", hex_string=b"<486a>"),
            {"font_alpha_content"},
        ),
        (
            "text operator",
            content("/F1", "/F2", first_text_operator=b"TJ"),
            {"font_alpha_content"},
        ),
        (
            "comment bytes",
            content("/F1", "/F2", comment=b"% changed comment\n"),
            {"font_alpha_content"},
        ),
        (
            "whitespace",
            content("/F1", "/F2").replace(b"BT\n", b"BT  \n", 1),
            {"font_alpha_content"},
        ),
        (
            "operation order",
            content("/F1", "/F2").replace(
                b"(Hello) Tj\n/F2 9 Tf\n<4869> Tj",
                b"/F2 9 Tf\n<4869> Tj\n(Hello) Tj",
                1,
            ),
            {"font_alpha_content"},
        ),
        (
            "opaque literal-string bytes",
            content("/F1", "/F2", literal=b"(opaque /F2 88 Tf)"),
            {"font_alpha_content"},
        ),
        (
            "opaque hex-string bytes",
            content("/F1", "/F2", hex_string=b"<2f4632203838205466>"),
            {"font_alpha_content"},
        ),
        (
            "bare font-looking non-Tf name",
            content("/F1", "/F2") + b"/F1 gs\n",
            {"font_alpha_token_binding"},
        ),
        (
            "nonnumeric Tf size",
            content("/F1", "/F2").replace(b"/F1 12 Tf", b"/F1 nope Tf", 1),
            {"font_alpha_tf_shape"},
        ),
        (
            "extra Tf operand",
            content("/F1", "/F2").replace(b"/F1 12 Tf", b"/F1 12 13 Tf", 1),
            {"font_alpha_tf_shape"},
        ),
        (
            "inline image syntax",
            content("/F1", "/F2") + b"BI /W 1 /H 1 /BPC 8 /CS /G ID x EI\n",
            {"font_alpha_inline_image"},
        ),
        (
            "unterminated literal string",
            content("/F1", "/F2", literal=b"(unterminated"),
            {"font_alpha_lex", "font_alpha_tf_shape"},
        ),
        (
            "invalid hex string",
            content("/F1", "/F2", hex_string=b"<48xz>"),
            {"font_alpha_lex"},
        ),
        (
            "escaped font resource name",
            content("/F#31", "/F2"),
            {"font_alpha_resource_keys", "font_alpha_unbound"},
        ),
    )
    for label, mutated_content, codes in content_mutations:
        core_failure(
            f"decoded content detects {label} mutation",
            standard_pair(candidate_content=mutated_content),
            *sorted(codes),
        )


def file_state(path: pathlib.Path) -> tuple[Any, ...]:
    """Capture enough identity and content to prove a failed call wrote nothing."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return ("missing",)
    if stat.S_ISLNK(metadata.st_mode):
        target = path.resolve(strict=False)
        try:
            target_metadata = target.lstat()
        except FileNotFoundError:
            target_state: tuple[Any, ...] = ("missing-target",)
        else:
            if stat.S_ISREG(target_metadata.st_mode):
                target_state = (
                    "regular-target",
                    target_metadata.st_dev,
                    target_metadata.st_ino,
                    target_metadata.st_nlink,
                    target_metadata.st_size,
                    sha256_path(target),
                )
            else:
                target_state = ("nonregular-target", target_metadata.st_mode)
        return (
            "symlink",
            os.readlink(path),
            metadata.st_ino,
            metadata.st_nlink,
            target_state,
        )
    if stat.S_ISREG(metadata.st_mode):
        return (
            "regular",
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_size,
            sha256_path(path),
        )
    if stat.S_ISDIR(metadata.st_mode):
        return (
            "directory",
            metadata.st_dev,
            metadata.st_ino,
            tuple(sorted(os.listdir(path))),
        )
    return ("other", metadata.st_dev, metadata.st_ino, metadata.st_mode)


def python_command(script: pathlib.Path) -> list[str]:
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-O")
    command.extend(("-I", "-B", str(script)))
    return command


def run_cli(
    script: pathlib.Path,
    reference: str,
    candidate: str,
    retained: str,
    targets: str,
    navigation: str,
    *,
    cwd: pathlib.Path,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "LC_ALL": "C",
            "LANG": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    )
    environment.pop("PYTHONOPTIMIZE", None)
    return subprocess.run(
        python_command(script) + [reference, candidate, retained, targets, navigation],
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )


def expect_cli_failure(
    ledger: Ledger,
    category: str,
    label: str,
    script: pathlib.Path,
    reference: str,
    candidate: str,
    retained: str,
    targets: str,
    navigation: str,
    cwd: pathlib.Path,
    expected_stderr: str | None = None,
) -> None:
    """Require nonzero exit and byte/identity preservation of both output paths."""

    target_path = pathlib.Path(targets)
    navigation_path = pathlib.Path(navigation)
    before = (file_state(target_path), file_state(navigation_path))
    completed = run_cli(
        script, reference, candidate, retained, targets, navigation, cwd=cwd
    )
    if completed.returncode == 0:
        fail(f"{label}: hostile CLI call succeeded: {completed.stdout.strip()}")
    if expected_stderr is not None and expected_stderr not in completed.stderr:
        fail(f"{label}: failure lacks {expected_stderr!r}: stderr={completed.stderr!r}")
    after = (file_state(target_path), file_state(navigation_path))
    if before != after:
        fail(
            f"{label}: failed CLI call changed an output: before={before!r} after={after!r}"
        )
    setattr(ledger, category, getattr(ledger, category) + 1)


def successful_cli_control(
    ledger: Ledger,
    label: str,
    reference: pathlib.Path,
    candidate: pathlib.Path,
    retained: pathlib.Path,
    directory: pathlib.Path,
    expected_targets: tuple[str, ...],
    expected_navigation: tuple[str, ...],
    expected_stdout_fragment: str,
) -> None:
    targets = directory / f"{label}-targets.txt"
    navigation = directory / f"{label}-navigation.txt"
    targets.write_bytes(b"sentinel targets\n")
    navigation.write_bytes(b"sentinel navigation\n")
    completed = run_cli(
        CHECK,
        str(reference),
        str(candidate),
        str(retained),
        str(targets),
        str(navigation),
        cwd=directory,
    )
    if completed.returncode != 0:
        fail(
            f"{label}: CLI control failed ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    require(
        expected_stdout_fragment in completed.stdout and not completed.stderr,
        f"{label}: CLI relation diagnostic changed: "
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}",
    )
    observed_targets = tuple(targets.read_text(encoding="utf-8").splitlines())
    observed_navigation = tuple(navigation.read_text(encoding="utf-8").splitlines())
    require(observed_targets == expected_targets, f"{label}: published targets differ")
    require(observed_navigation == expected_navigation, f"{label}: navigation differs")
    require(
        not tuple(directory.glob(f".{targets.name}.*")),
        f"{label}: target temporary file leaked",
    )
    require(
        not tuple(directory.glob(f".{navigation.name}.*")),
        f"{label}: navigation temporary file leaked",
    )
    ledger.controls += 1


def run_profile_and_structure_tests(
    ledger: Ledger,
    canonical: pathlib.Path,
    retained: pathlib.Path,
    directory: pathlib.Path,
) -> None:
    """Replay the actual pair and mutate every frozen profile/report dimension."""

    canonical_data = canonical.read_bytes()
    retained_data = retained.read_bytes()
    strict_report = ALPHA.STRUCTURE.validate_bytes(canonical_data)
    retained_report = ALPHA.STRUCTURE.validate_bytes(
        retained_data, enforce_manifest_digests=False
    )
    record_control(
        ledger,
        "retained outer structure profile",
        lambda: ALPHA.compare_structure_reports(strict_report, retained_report),
    )
    retained_stats = record_control(
        ledger,
        "retained typed font-alpha semantic core",
        lambda: ALPHA.compare_font_alpha_core(canonical_data, retained_data),
    )
    record_control(
        ledger,
        "retained exact legacy operation/mapping profile",
        lambda: ALPHA.enforce_legacy_font_profile(retained_stats),
    )

    profile_mutations = (
        (
            "page count",
            dataclasses.replace(retained_stats, pages=retained_stats.pages + 1),
        ),
        (
            "operation count",
            dataclasses.replace(
                retained_stats, operations=retained_stats.operations + 1
            ),
        ),
        (
            "Tf-use count",
            dataclasses.replace(retained_stats, tf_uses=retained_stats.tf_uses + 1),
        ),
        (
            "page font-binding count",
            dataclasses.replace(
                retained_stats,
                page_font_bindings=retained_stats.page_font_bindings + 1,
            ),
        ),
        (
            "global mapping count",
            dataclasses.replace(
                retained_stats,
                global_font_mappings=retained_stats.global_font_mappings + 1,
            ),
        ),
        (
            "mapping digest",
            dataclasses.replace(retained_stats, mapping_sha256="0" * 64),
        ),
        (
            "mapping pair identity",
            dataclasses.replace(
                retained_stats,
                font_name_pairs=(
                    (("/F74", "/F82"),) + retained_stats.font_name_pairs[1:]
                ),
            ),
        ),
        (
            "mapping offset",
            dataclasses.replace(
                retained_stats,
                font_name_pairs=(
                    (("/F75", "/F84"),) + retained_stats.font_name_pairs[1:]
                ),
            ),
        ),
    )
    for label, mutation in profile_mutations:
        expect_alpha_failure(
            ledger,
            "profile_hostiles",
            f"legacy profile rejects {label} drift",
            lambda mutation=mutation: ALPHA.enforce_legacy_font_profile(mutation),
            {"font_alpha_profile"},
        )

    def structure_failure(label: str, reference: Any, candidate: Any) -> None:
        expect_alpha_failure(
            ledger,
            "structure_hostiles",
            label,
            lambda: ALPHA.compare_structure_reports(reference, candidate),
            {"font_alpha_profile"},
        )

    structure_failure(
        "target tuple drift",
        strict_report,
        dataclasses.replace(
            retained_report,
            targets=retained_report.targets[:-1] + ("mutated-target",),
        ),
    )
    structure_failure(
        "target count drift",
        strict_report,
        dataclasses.replace(retained_report, targets=retained_report.targets[:-1]),
    )
    structure_failure(
        "reference structure digest drift",
        dataclasses.replace(strict_report, structure_sha256="0" * 64),
        retained_report,
    )
    structure_failure(
        "candidate structure digest drift",
        strict_report,
        dataclasses.replace(retained_report, structure_sha256="0" * 64),
    )
    structure_failure(
        "reference navigation digest drift",
        dataclasses.replace(strict_report, navigation_sha256="0" * 64),
        retained_report,
    )
    structure_failure(
        "candidate navigation digest drift",
        strict_report,
        dataclasses.replace(retained_report, navigation_sha256="0" * 64),
    )
    mutated_manifest = list(retained_report.structure_manifest)
    nonvariant_index = next(
        index
        for index, line in enumerate(mutated_manifest)
        if not line.startswith(ALPHA.RAW_VARIANT_PREFIXES)
    )
    mutated_manifest[nonvariant_index] += "-mutation"
    structure_failure(
        "nonvariant structure record drift even under pinned digest metadata",
        strict_report,
        dataclasses.replace(
            retained_report, structure_manifest=tuple(mutated_manifest)
        ),
    )
    structure_failure(
        "structure record-count drift",
        strict_report,
        dataclasses.replace(
            retained_report,
            structure_manifest=retained_report.structure_manifest[:-1],
        ),
    )
    mutated_navigation = list(retained_report.navigation)
    navigation_index = next(
        index
        for index, line in enumerate(mutated_navigation)
        if not line.startswith("structure\t")
    )
    mutated_navigation[navigation_index] += "-mutation"
    structure_failure(
        "navigation record drift even under pinned digest metadata",
        strict_report,
        dataclasses.replace(retained_report, navigation=tuple(mutated_navigation)),
    )
    structure_failure(
        "navigation record-count drift",
        strict_report,
        dataclasses.replace(
            retained_report, navigation=retained_report.navigation[:-1]
        ),
    )

    canonical_copy = directory / "canonical-copy.pdf"
    retained_copy = directory / "retained-copy.pdf"
    retained_second_copy = directory / "retained-second-copy.pdf"
    retained_id_variant = directory / "retained-id-variant.pdf"
    canonical_copy.write_bytes(canonical_data)
    retained_copy.write_bytes(retained_data)
    retained_second_copy.write_bytes(retained_data)
    retained_id_variant.write_bytes(
        replace_trailer_id(retained_data, b"0123456789abcdef0123456789abcdef")
    )
    successful_cli_control(
        ledger,
        "identity",
        canonical,
        canonical_copy,
        retained,
        directory,
        strict_report.targets,
        strict_report.navigation,
        "OK: exact canonical identity",
    )
    successful_cli_control(
        ledger,
        "retained",
        canonical,
        retained_copy,
        retained,
        directory,
        strict_report.targets,
        strict_report.navigation,
        "raw_relation=byte-exact retained fixture",
    )
    successful_cli_control(
        ledger,
        "retained-copy",
        canonical,
        retained_second_copy,
        retained,
        directory,
        strict_report.targets,
        strict_report.navigation,
        "raw_relation=byte-exact retained fixture",
    )
    successful_cli_control(
        ledger,
        "retained-id-variant",
        canonical,
        retained_id_variant,
        retained,
        directory,
        strict_report.targets,
        strict_report.navigation,
        "raw_relation=strict retained-fixture trailer-ID projection",
    )

    expect_cli_failure(
        ledger,
        "profile_hostiles",
        "legacy/canonical direction cannot be reversed",
        CHECK,
        str(retained),
        str(canonical),
        str(retained_copy),
        str(directory / "reverse-targets.txt"),
        str(directory / "reverse-navigation.txt"),
        directory,
    )


def run_raw_boundary_tests(
    ledger: Ledger,
    canonical: pathlib.Path,
    retained: pathlib.Path,
    directory: pathlib.Path,
) -> None:
    """Exercise the CLI's raw canonical, fixture, and candidate relation."""

    canonical_data = canonical.read_bytes()
    retained_data = retained.read_bytes()
    changed_id = replace_trailer_id(retained_data, b"fedcba9876543210fedcba9876543210")

    def hostile(
        label: str,
        reference_data: bytes,
        candidate_data: bytes,
        fixture_data: bytes,
        expected_code: str,
    ) -> None:
        case_root = directory / f"raw-{label}"
        case_root.mkdir()
        reference = case_root / "reference.pdf"
        candidate = case_root / "candidate.pdf"
        fixture = case_root / "retained.pdf"
        reference.write_bytes(reference_data)
        candidate.write_bytes(candidate_data)
        fixture.write_bytes(fixture_data)
        expect_cli_failure(
            ledger,
            "raw_boundary_hostiles",
            label,
            CHECK,
            str(reference),
            str(candidate),
            str(fixture),
            str(case_root / "targets.txt"),
            str(case_root / "navigation.txt"),
            case_root,
            expected_stderr=f"[{expected_code}]",
        )

    hostile(
        "canonical trailing newline",
        canonical_data + b"\n",
        canonical_data,
        retained_data,
        "font_alpha_raw_reference",
    )
    hostile(
        "canonical same-size raw drift",
        mutate_non_id_header_byte(canonical_data),
        canonical_data,
        retained_data,
        "font_alpha_raw_reference",
    )
    hostile(
        "retained fixture trailing newline",
        canonical_data,
        retained_data,
        retained_data + b"\n",
        "font_alpha_raw_fixture",
    )
    hostile(
        "retained fixture valid ID drift",
        canonical_data,
        retained_data,
        changed_id,
        "font_alpha_raw_fixture",
    )
    hostile(
        "candidate trailing newline",
        canonical_data,
        retained_data + b"\n",
        retained_data,
        "font_alpha_raw_profile",
    )
    hostile(
        "candidate trailing comment",
        canonical_data,
        retained_data + b"\n% raw suffix must fail\n",
        retained_data,
        "font_alpha_raw_profile",
    )
    hostile(
        "candidate non-ID drift with a changed ID",
        canonical_data,
        mutate_non_id_header_byte(changed_id),
        retained_data,
        "font_alpha_raw_profile",
    )
    malformed_id = bytearray(changed_id)
    malformed_match = strict_id_match(changed_id)
    malformed_id[malformed_match.start(1)] = ord("G")
    hostile(
        "candidate malformed trailer ID",
        canonical_data,
        bytes(malformed_id),
        retained_data,
        "font_alpha_raw_profile",
    )
    hostile(
        "candidate trailer ID has the wrong owner",
        canonical_data,
        move_id_outside_final_owner(changed_id),
        retained_data,
        "font_alpha_raw_profile",
    )
    hostile(
        "candidate raw drift keeps the same ID",
        canonical_data,
        mutate_non_id_header_byte(retained_data),
        retained_data,
        "font_alpha_raw_profile",
    )


def run_custody_tests(
    ledger: Ledger,
    canonical: pathlib.Path,
    retained: pathlib.Path,
    directory: pathlib.Path,
) -> None:
    """Exercise input/output identity, canonicality, size, and no-write policy."""

    canonical_data = canonical.read_bytes()

    def hostile(
        label: str,
        reference: str,
        candidate: str,
        targets: str | None = None,
        navigation: str | None = None,
        retained_input: str | None = None,
    ) -> None:
        expect_cli_failure(
            ledger,
            "custody_hostiles",
            label,
            CHECK,
            reference,
            candidate,
            retained_input or str(retained),
            targets or str(directory / f"{label}-targets.txt"),
            navigation or str(directory / f"{label}-navigation.txt"),
            directory,
        )

    hostile("same input alias", str(canonical), str(canonical))

    canonical_identity_copy = directory / "custody-canonical-copy.pdf"
    canonical_identity_copy.write_bytes(canonical_data)
    hostile(
        "candidate aliases retained fixture",
        str(canonical),
        str(retained),
        retained_input=str(retained),
    )
    hostile(
        "reference aliases retained fixture",
        str(canonical),
        str(canonical_identity_copy),
        retained_input=str(canonical),
    )

    retained_symlink = directory / "retained-symlink.pdf"
    retained_symlink.symlink_to(retained)
    hostile(
        "symbolic retained fixture",
        str(canonical),
        str(canonical_identity_copy),
        retained_input=str(retained_symlink),
    )

    retained_hardlink = directory / "retained-hardlink.pdf"
    retained_hardlink_peer = directory / "retained-hardlink-peer.pdf"
    retained_hardlink.write_bytes(retained.read_bytes())
    os.link(retained_hardlink, retained_hardlink_peer)
    hostile(
        "multiply linked retained fixture",
        str(canonical),
        str(canonical_identity_copy),
        retained_input=str(retained_hardlink),
    )

    symlink_input = directory / "input-symlink.pdf"
    symlink_input.symlink_to(canonical)
    hostile("symbolic input", str(canonical), str(symlink_input))

    hardlink_input = directory / "hardlink-input.pdf"
    hardlink_peer = directory / "hardlink-peer.pdf"
    hardlink_input.write_bytes(canonical_data)
    os.link(hardlink_input, hardlink_peer)
    hostile("multiply linked input", str(canonical), str(hardlink_input))

    zero_input = directory / "zero.pdf"
    zero_input.write_bytes(b"")
    hostile("zero-size input", str(canonical), str(zero_input))

    oversized_input = directory / "oversized.pdf"
    with oversized_input.open("wb") as stream:
        stream.truncate(ALPHA.MAX_PDF_BYTES + 1)
    hostile("oversized input", str(canonical), str(oversized_input))

    malformed_input = directory / "malformed.pdf"
    malformed_input.write_bytes(b"not a PDF")
    hostile("malformed PDF input", str(canonical), str(malformed_input))

    truncated_input = directory / "truncated.pdf"
    truncated_input.write_bytes(canonical_data[: len(canonical_data) // 2])
    hostile("truncated PDF input", str(canonical), str(truncated_input))

    candidate = directory / "custody-candidate.pdf"
    candidate.write_bytes(canonical_data)
    noncanonical_parent = directory / "noncanonical"
    noncanonical_parent.mkdir()
    noncanonical_input = str(noncanonical_parent / ".." / candidate.name)
    hostile("noncanonical input path", str(canonical), noncanonical_input)
    hostile("relative input path", str(canonical), candidate.name)
    hostile("input path with newline", str(canonical), str(candidate) + "\n")

    output_sentinel = directory / "output-sentinel.txt"
    output_sentinel.write_bytes(b"sentinel must remain unchanged\n")
    output_symlink = directory / "output-symlink.txt"
    output_symlink.symlink_to(output_sentinel)
    hostile(
        "symbolic output",
        str(canonical),
        str(candidate),
        targets=str(output_symlink),
        navigation=str(directory / "symbolic-output-navigation.txt"),
    )

    output_directory = directory / "output-directory"
    output_directory.mkdir()
    hostile(
        "directory output",
        str(canonical),
        str(candidate),
        targets=str(output_directory),
        navigation=str(directory / "directory-output-navigation.txt"),
    )

    hostile(
        "output aliases reference input",
        str(canonical),
        str(candidate),
        targets=str(canonical),
        navigation=str(directory / "alias-output-navigation.txt"),
    )
    hostile(
        "output aliases candidate input",
        str(canonical),
        str(candidate),
        targets=str(candidate),
        navigation=str(directory / "candidate-alias-navigation.txt"),
    )
    hostile(
        "output aliases retained fixture",
        str(canonical),
        str(candidate),
        targets=str(retained),
        navigation=str(directory / "retained-alias-navigation.txt"),
    )

    hostile(
        "identical output paths",
        str(canonical),
        str(candidate),
        targets=str(directory / "same-output.txt"),
        navigation=str(directory / "same-output.txt"),
    )

    hardlinked_output_a = directory / "hardlinked-output-a.txt"
    hardlinked_output_b = directory / "hardlinked-output-b.txt"
    hardlinked_output_a.write_bytes(b"hardlinked outputs remain unchanged\n")
    os.link(hardlinked_output_a, hardlinked_output_b)
    hostile(
        "hardlinked output paths",
        str(canonical),
        str(candidate),
        targets=str(hardlinked_output_a),
        navigation=str(hardlinked_output_b),
    )

    candidate_with_output_hardlink = directory / "candidate-with-output-hardlink.pdf"
    candidate_with_output_hardlink.write_bytes(canonical_data)
    input_hardlinked_output = directory / "input-hardlinked-output.txt"
    os.link(candidate_with_output_hardlink, input_hardlinked_output)
    hostile(
        "output hard-links candidate input",
        str(canonical),
        str(candidate_with_output_hardlink),
        targets=str(input_hardlinked_output),
        navigation=str(directory / "input-hardlink-navigation.txt"),
    )

    missing_parent = directory / "missing-parent"
    hostile(
        "absent output parent",
        str(canonical),
        str(candidate),
        targets=str(missing_parent / "targets.txt"),
        navigation=str(directory / "missing-parent-navigation.txt"),
    )

    symbolic_parent = directory / "symbolic-parent"
    real_parent = directory / "real-parent"
    real_parent.mkdir()
    symbolic_parent.symlink_to(real_parent, target_is_directory=True)
    hostile(
        "symbolic output parent",
        str(canonical),
        str(candidate),
        targets=str(symbolic_parent / "targets.txt"),
        navigation=str(directory / "symbolic-parent-navigation.txt"),
    )

    output_subdirectory = directory / "output-subdirectory"
    output_subdirectory.mkdir()
    hostile(
        "noncanonical output path",
        str(canonical),
        str(candidate),
        targets=str(output_subdirectory / ".." / "noncanonical-output.txt"),
        navigation=str(directory / "noncanonical-output-navigation.txt"),
    )
    hostile(
        "relative output path",
        str(canonical),
        str(candidate),
        targets="relative-targets.txt",
        navigation=str(directory / "relative-output-navigation.txt"),
    )
    hostile(
        "output path with newline",
        str(canonical),
        str(candidate),
        targets=str(directory / "newline-output.txt") + "\n",
        navigation=str(directory / "newline-output-navigation.txt"),
    )
    hostile(
        "root output parent",
        str(canonical),
        str(candidate),
        targets="/font-alpha-self-test-must-not-exist.txt",
        navigation=str(directory / "root-output-navigation.txt"),
    )


def run_dependency_tests(
    ledger: Ledger,
    canonical: pathlib.Path,
    retained: pathlib.Path,
    directory: pathlib.Path,
) -> None:
    """Prove both pinned executable dependencies fail closed under drift."""

    check_bytes = CHECK.read_bytes()
    dependency_sources = {
        "structure": STRUCTURE_CHECK,
        "id-variance": ID_VARIANCE_CHECK,
    }

    def isolated_case(label: str, target: str, mutation: str) -> None:
        root = directory / label
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        isolated_check = scripts / CHECK.name
        isolated_check.write_bytes(check_bytes)
        for dependency_label, dependency_source in dependency_sources.items():
            dependency_target = scripts / dependency_source.name
            if dependency_label != target:
                dependency_target.write_bytes(dependency_source.read_bytes())
                continue
            if mutation == "symlink":
                dependency_target.symlink_to(dependency_source)
            elif mutation == "stub":
                dependency_target.write_text(
                    '"""Deliberately incomplete dependency."""\n',
                    encoding="utf-8",
                )
            elif mutation == "syntax":
                dependency_target.write_text(
                    "this is not valid Python !!!\n", encoding="utf-8"
                )
            elif mutation == "hardlink":
                dependency_target.write_bytes(dependency_source.read_bytes())
                os.link(dependency_target, scripts / f"{dependency_source.name}.peer")
            elif mutation != "absent":
                fail(f"unknown dependency fixture {mutation}")
        candidate = root / "candidate.pdf"
        candidate.write_bytes(canonical.read_bytes())
        expect_cli_failure(
            ledger,
            "dependency_hostiles",
            f"{label} dependency",
            isolated_check,
            str(canonical),
            str(candidate),
            str(retained),
            str(root / "targets.txt"),
            str(root / "navigation.txt"),
            root,
            expected_stderr="[dependency]",
        )

    for dependency_label in dependency_sources:
        for mutation in ("absent", "symlink", "stub", "syntax", "hardlink"):
            isolated_case(f"{dependency_label}-{mutation}", dependency_label, mutation)


def run_static_guards(ledger: Ledger) -> None:
    """Guard the sequencing that keeps the lower semantic hook non-operational."""

    source = CHECK.read_text(encoding="utf-8")
    guards = (
        (
            "canonical reference is always strict",
            "reference_report = STRUCTURE.validate_bytes(reference.data)" in source,
        ),
        (
            "canonical reference has exact raw size and digest pins",
            "EXPECTED_REFERENCE_BYTES" in source
            and "EXPECTED_REFERENCE_SHA256" in source
            and source.index('"font_alpha_raw_reference"')
            < source.index(
                "reference_report = STRUCTURE.validate_bytes(reference.data)"
            ),
        ),
        (
            "retained fixture has exact raw size and digest pins",
            "EXPECTED_RETAINED_BYTES" in source
            and "EXPECTED_RETAINED_SHA256" in source
            and source.index('"font_alpha_raw_fixture"')
            < source.index(
                "reference_report = STRUCTURE.validate_bytes(reference.data)"
            ),
        ),
        (
            "identity requires byte equality",
            "if candidate.data == reference.data:" in source,
        ),
        (
            "exceptional candidate raw relation precedes typed relaxation",
            source.index(
                "raw_relation, raw_relation_diagnostic = compare_candidate_to_retained_raw"
            )
            < source.index("candidate.data, enforce_manifest_digests=False"),
        ),
        (
            "raw relation reuses captured bytes through the pinned ID parser",
            source.count("ID_VARIANCE.erase_strict_id(") == 2
            and "ID_VARIANCE.main(" not in source
            and "subprocess" not in source,
        ),
        (
            "both executable dependencies have exact digest pins",
            ALPHA.EXPECTED_STRUCTURE_CHECK_SHA256 in source
            and ALPHA.EXPECTED_ID_VARIANCE_CHECK_SHA256 in source,
        ),
        (
            "relaxed terminal digests occur only on candidate",
            "candidate.data, enforce_manifest_digests=False" in source,
        ),
        (
            "structure profile precedes semantic core",
            source.index(
                "compare_structure_reports(reference_report, candidate_report)"
            )
            < source.index(
                "stats = compare_font_alpha_core(reference.data, candidate.data)"
            ),
        ),
        (
            "semantic core precedes legacy pins",
            source.index(
                "stats = compare_font_alpha_core(reference.data, candidate.data)"
            )
            < source.index("enforce_legacy_font_profile(stats)"),
        ),
        (
            "typed payload equality is explicit",
            "if reference_resources != candidate_resources:" in source,
        ),
        (
            "transformed decoded bytes are exact",
            "if transformed != reference_content.decoded:" in source,
        ),
        (
            "font mapping is globally bijective",
            "if len(global_reverse) != len(global_mapping):" in source,
        ),
        (
            "all font resources must be used",
            "if used != font_names:" in source,
        ),
        (
            "inline images are outside the admitted profile",
            source.count("font_alpha_inline_image") >= 2,
        ),
        (
            "outputs follow three input and two dependency rechecks",
            source.index(
                "recheck_input(candidate)\n"
                "        recheck_input(retained)\n"
                "        recheck_dependency(STRUCTURE_DEPENDENCY)\n"
                "        recheck_dependency(ID_VARIANCE_DEPENDENCY)"
            )
            < source.index("write_lines(outputs[0], candidate_report.targets)"),
        ),
        (
            "no assert-dependent enforcement",
            "assert " not in source and "assert(" not in source,
        ),
        (
            "no environment bypass",
            "getenv" not in source and "environ" not in source,
        ),
        (
            "no floating tolerance",
            "isclose" not in source and "tolerance" not in source.lower(),
        ),
        (
            "complete typed closure is documented as equality oracle",
            "Font identity\nis then decided by exact equality" in source,
        ),
    )
    for label, condition in guards:
        require(condition, f"static guard failed: {label}")
        ledger.static_guards += 1


def validate_argument(raw: str, label: str) -> pathlib.Path:
    if not raw or "\n" in raw or "\r" in raw:
        fail(f"{label} path is empty or contains a control character")
    path = pathlib.Path(raw).expanduser().resolve(strict=True)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        fail(f"{label} is not a regular nonsymbolic file: {path}")
    if metadata.st_nlink != 1:
        fail(f"{label} must be singly linked: {path}")
    return path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} CANONICAL.pdf RETAINED_OLD.pdf",
            file=sys.stderr,
        )
        return 2
    try:
        canonical = validate_argument(argv[0], "canonical")
        retained = validate_argument(argv[1], "retained old-toolchain artifact")
        if os.path.samefile(canonical, retained):
            fail("canonical and retained inputs alias the same file")
        canonical_before = sha256_path(canonical)
        retained_before = sha256_path(retained)

        ledger = Ledger()
        run_semantic_tests(ledger)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-font-alpha-self-test-"
        ) as raw_directory:
            directory = pathlib.Path(raw_directory).resolve(strict=True)
            run_profile_and_structure_tests(ledger, canonical, retained, directory)
            run_raw_boundary_tests(ledger, canonical, retained, directory)
            run_custody_tests(ledger, canonical, retained, directory)
            run_dependency_tests(ledger, canonical, retained, directory)
        run_static_guards(ledger)

        require(
            sha256_path(canonical) == canonical_before,
            "canonical input changed during self-test",
        )
        require(
            sha256_path(retained) == retained_before,
            "retained input changed during self-test",
        )
    except (OSError, SelfTestError, subprocess.SubprocessError) as error:
        print(f"{CHECK_NAME} failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(
            f"{CHECK_NAME} failed with internal {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 1

    counts = dataclasses.asdict(ledger)
    print(
        "OK: font-alpha comparator fail-closed mutation suite "
        f"(total={ledger.total()}; "
        + "; ".join(f"{name}={value}" for name, value in counts.items())
        + f"; max_pdf_bytes={ALPHA.MAX_PDF_BYTES}; expected_pages={ALPHA.EXPECTED_PAGES}; "
        f"expected_operations={ALPHA.EXPECTED_OPERATIONS}; expected_Tf_uses={ALPHA.EXPECTED_TF_USES}; "
        f"expected_font_bindings={ALPHA.EXPECTED_PAGE_FONT_BINDINGS}; "
        f"expected_global_mappings={ALPHA.EXPECTED_GLOBAL_FONT_MAPPINGS}; "
        f"selftest_sha256={sha256_path(pathlib.Path(__file__).resolve(strict=True))}; "
        f"checker_sha256={sha256_path(CHECK)}; structure_sha256={sha256_path(STRUCTURE_CHECK)}; "
        f"id_variance_sha256={sha256_path(ID_VARIANCE_CHECK)}; "
        f"canonical_sha256={canonical_before}; retained_sha256={retained_before})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
