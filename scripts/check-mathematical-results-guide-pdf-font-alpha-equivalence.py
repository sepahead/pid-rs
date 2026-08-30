#!/usr/bin/env python3
"""Check the one admitted old-toolchain guide-PDF font-name relation.

This source-specific cross-toolchain relation admits only the observed global,
bijective rename of page ``/Font`` resource keys inside the checked typed graph.
The canonical reference and retained legacy fixture are bound by raw size and
SHA-256. A distinct exceptional candidate must be byte-identical to the fixture
or differ from it only in the strict duplicated final-trailer ``/ID`` payload
relation implemented by the separately digest-pinned raw checker. Font identity
is then decided by exact equality of the strict structure checker's complete
typed resource-closure payload, not by a digest. A fail-closed content lexer
substitutes only font-name tokens independently parsed as ``Tf`` operands; all
transformed decoded page content and complete resource roots must be byte-exact.

The raw-bound canonical reference first passes the unchanged strict single-PDF policy.
The candidate passes the same complete object-graph policy with only its two
final source-manifest digest comparisons deferred to this exact pair check.
This is not a generic PDF normalizer, renderer-equivalence claim, or permission
to weaken same-toolchain byte identity.
"""

from __future__ import annotations

import hashlib
import io
import os
import pathlib
import re
import stat
import sys
import tempfile
import types
from dataclasses import dataclass
from typing import Any, NoReturn

from pypdf import PdfReader
from pypdf.generic import ContentStream, DictionaryObject, IndirectObject


CHECK_NAME = "Mathematical results guide typed font-resource alpha-equivalence check"
ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
STRUCTURE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-structure.py"
ID_VARIANCE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-id-variance.py"
MAX_PDF_BYTES = 16 * 1024 * 1024
MAX_DEPENDENCY_BYTES = 1024 * 1024
EXPECTED_STRUCTURE_CHECK_SHA256 = (
    "50a5ba491a299750af65c14488be478481fbd1a9c779a9c4506a4029d9c4c0b2"
)
EXPECTED_ID_VARIANCE_CHECK_SHA256 = (
    "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7"
)
EXPECTED_REFERENCE_BYTES = 581_314
EXPECTED_REFERENCE_SHA256 = (
    "3f8e8196f3dc510eb122926322829f111c1b745fbbf27c920e9606f9a212c200"
)
EXPECTED_RETAINED_BYTES = 581_294
EXPECTED_RETAINED_SHA256 = (
    "08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443"
)
STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)

# This is one frozen source profile, not a general class of toolchain variance.
EXPECTED_PAGES = 16
EXPECTED_TARGETS = 43
EXPECTED_NAVIGATION_RECORDS = 167
EXPECTED_STRUCTURE_RECORDS = 1_699
EXPECTED_STRUCTURE_PAYLOAD_BYTES = 85_381
EXPECTED_VARIANT_RECORDS = 32
EXPECTED_REFERENCE_STRUCTURE_SHA256 = (
    "e9adba3097ffc38de2f7723e448d2bb54265ee201e010c0857e1a7a40db9d99b"
)
EXPECTED_CANDIDATE_STRUCTURE_SHA256 = (
    "f7c9ccce59a51f035a474632c8ab2ef21aa7beea76d809bfe5d542ddb21e7dd3"
)
EXPECTED_REFERENCE_NAVIGATION_SHA256 = (
    "95ca1981ffb665ad4f0b9cb72d2ae508f76ae90814669ca910bc41de55aadcf8"
)
EXPECTED_CANDIDATE_NAVIGATION_SHA256 = (
    "1699fe16fe5aea765f7fdbffb493158f12da0a06e38d23245f70985b86869103"
)
EXPECTED_OPERATIONS = 16_362
EXPECTED_TF_USES = 1_373
EXPECTED_PAGE_FONT_BINDINGS = 122
EXPECTED_GLOBAL_FONT_MAPPINGS = 13
EXPECTED_FONT_NAME_OFFSET = 8
EXPECTED_FONT_NAME_PAIRS = (
    ("/F75", "/F83"),
    ("/F77", "/F85"),
    ("/F93", "/F101"),
    ("/F94", "/F102"),
    ("/F96", "/F104"),
    ("/F99", "/F107"),
    ("/F100", "/F108"),
    ("/F102", "/F110"),
    ("/F103", "/F111"),
    ("/F105", "/F113"),
    ("/F106", "/F114"),
    ("/F108", "/F116"),
    ("/F112", "/F120"),
)
EXPECTED_FONT_MAPPING_SHA256 = (
    "364091c0d0e4a023f1335b58c833383569d0b1968bbec26bd77fa26c4a116488"
)
RAW_VARIANT_PREFIXES = ("page-content\t", "page-resources\t")
FONT_NAME = re.compile(r"/F([1-9][0-9]*)\Z")
FONT_NAME_BYTES = re.compile(rb"/F[1-9][0-9]*\Z")
PDF_NUMBER_BYTES = re.compile(rb"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
PDF_WHITESPACE = frozenset((0x00, 0x09, 0x0A, 0x0C, 0x0D, 0x20))
PDF_DELIMITERS = frozenset(b"()<>[]{}/%")
HEX_DIGITS = frozenset(b"0123456789abcdefABCDEF")


class AlphaEquivalenceError(Exception):
    """A deterministic failure of the closed cross-toolchain relation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class InputSnapshot:
    """One no-follow descriptor and the exact bytes parsed by this check."""

    label: str
    path: pathlib.Path
    descriptor: int
    before: os.stat_result
    data: bytes


@dataclass(frozen=True)
class DependencySnapshot:
    """Exact bytes and filesystem identity for one executable dependency."""

    label: str
    path: pathlib.Path
    before: os.stat_result
    data: bytes
    sha256: str


@dataclass(frozen=True)
class LexicalToken:
    """One bounded token span in a decoded PDF page-content stream."""

    kind: str
    start: int
    end: int
    raw: bytes


@dataclass(frozen=True)
class FontInventory:
    """One page's typed resource root and exact font-closure payloads."""

    resources_value: Any
    fonts: DictionaryObject
    by_name: dict[str, bytes]


@dataclass(frozen=True)
class ContentSurface:
    """The exact decoded bytes plus independently bound ``Tf`` name spans."""

    decoded: bytes
    font_spans: tuple[tuple[int, int, str], ...]
    operation_count: int


@dataclass(frozen=True)
class PairStats:
    """Pinned aggregate measurements for the admitted real pair."""

    pages: int
    operations: int
    tf_uses: int
    page_font_bindings: int
    global_font_mappings: int
    mapping_sha256: str
    font_name_pairs: tuple[tuple[str, str], ...]


def fail(code: str, message: str) -> NoReturn:
    raise AlphaEquivalenceError(code, message)


def same_stat(first: os.stat_result, second: os.stat_result) -> bool:
    return all(
        getattr(first, field) == getattr(second, field) for field in STABLE_FIELDS
    )


def capture_dependency(path: pathlib.Path, label: str) -> DependencySnapshot:
    """Read one canonical dependency through a stable no-follow descriptor."""

    try:
        path_before = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail("dependency", f"cannot inspect {label}: {error}")
    if (
        resolved != path
        or stat.S_ISLNK(path_before.st_mode)
        or not stat.S_ISREG(path_before.st_mode)
        or path_before.st_nlink != 1
    ):
        fail(
            "dependency",
            f"{label} is noncanonical, non-regular, symbolic, or multiply linked",
        )
    if path_before.st_size <= 0 or path_before.st_size > MAX_DEPENDENCY_BYTES:
        fail("dependency", f"{label} size is outside 1..{MAX_DEPENDENCY_BYTES} bytes")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        fail(
            "dependency",
            "this platform cannot open dependencies without following links",
        )
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
    except OSError as error:
        fail("dependency", f"cannot open {label} without following links: {error}")
    try:
        opened = os.fstat(descriptor)
        data = os.pread(descriptor, MAX_DEPENDENCY_BYTES + 1, 0)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail("dependency", f"cannot read {label}: {error}")
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or (path_before.st_dev, path_before.st_ino) != (opened.st_dev, opened.st_ino)
        or not same_stat(opened, descriptor_after)
        or not same_stat(opened, path_after)
        or len(data) != opened.st_size
    ):
        fail("dependency", f"{label} changed while it was read")
    digest = hashlib.sha256(data).hexdigest()
    return DependencySnapshot(label, path, opened, data, digest)


def load_pinned_dependency(
    path: pathlib.Path, expected_sha256: str, module_name: str, label: str
) -> tuple[Any, DependencySnapshot]:
    """Execute only captured dependency bytes with the exact reviewed digest."""

    snapshot = capture_dependency(path, label)
    if snapshot.sha256 != expected_sha256:
        fail(
            "dependency",
            f"{label} digest changed: observed={snapshot.sha256} expected={expected_sha256}",
        )
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(snapshot.data, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except BaseException as error:
        sys.modules.pop(module_name, None)
        fail("dependency", f"cannot load {label}: {type(error).__name__}: {error}")
    return module, snapshot


def recheck_dependency(snapshot: DependencySnapshot) -> None:
    observed = capture_dependency(snapshot.path, snapshot.label)
    if (
        not same_stat(snapshot.before, observed.before)
        or snapshot.data != observed.data
        or snapshot.sha256 != observed.sha256
    ):
        fail("dependency", f"{snapshot.label} changed before the comparison completed")


try:
    STRUCTURE, STRUCTURE_DEPENDENCY = load_pinned_dependency(
        STRUCTURE_CHECK,
        EXPECTED_STRUCTURE_CHECK_SHA256,
        "mathematical_results_guide_pdf_structure_for_font_alpha",
        "strict structure checker",
    )
    ID_VARIANCE, ID_VARIANCE_DEPENDENCY = load_pinned_dependency(
        ID_VARIANCE_CHECK,
        EXPECTED_ID_VARIANCE_CHECK_SHA256,
        "mathematical_results_guide_pdf_id_variance_for_font_alpha",
        "strict trailer-ID variance checker",
    )
except AlphaEquivalenceError as error:
    # Script execution has not reached ``main`` yet. Preserve the same typed,
    # fail-closed diagnostic contract for import-time dependency custody failures.
    if __name__ == "__main__":
        print(f"{CHECK_NAME} failed [{error.code}]: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    raise


def open_input(raw: str, label: str) -> InputSnapshot:
    if not raw or "\n" in raw or "\r" in raw:
        fail("input", f"{label} input path is empty or contains a control character")
    path = pathlib.Path(raw)
    if not path.is_absolute():
        fail("input", f"{label} input must be a canonical absolute path")
    try:
        path_before = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail("input", f"cannot inspect {label} input: {error}")
    if (
        resolved != path
        or stat.S_ISLNK(path_before.st_mode)
        or not stat.S_ISREG(path_before.st_mode)
    ):
        fail(
            "input", f"{label} input is noncanonical, non-regular, or symbolic: {path}"
        )
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        fail(
            "input", "this platform cannot open inputs without following symbolic links"
        )
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
        opened = os.fstat(descriptor)
    except OSError as error:
        fail("input", f"cannot open {label} input without following links: {error}")
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        fail("input", f"{label} input changed to a non-regular file")
    if (path_before.st_dev, path_before.st_ino) != (opened.st_dev, opened.st_ino):
        os.close(descriptor)
        fail("input", f"{label} input identity changed before opening")
    if opened.st_nlink != 1:
        os.close(descriptor)
        fail("input", f"{label} input is not singly linked")
    if opened.st_size <= 0 or opened.st_size > MAX_PDF_BYTES:
        os.close(descriptor)
        fail("input", f"{label} input size is outside 1..{MAX_PDF_BYTES} bytes")
    try:
        data = os.pread(descriptor, MAX_PDF_BYTES + 1, 0)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        os.close(descriptor)
        fail("input", f"cannot read {label} input: {error}")
    if not same_stat(opened, descriptor_after) or not same_stat(opened, path_after):
        os.close(descriptor)
        fail("input", f"{label} input changed while it was read")
    if len(data) != opened.st_size:
        os.close(descriptor)
        fail("input", f"{label} input length changed while it was read")
    return InputSnapshot(label, path, descriptor, opened, data)


def recheck_input(snapshot: InputSnapshot) -> None:
    try:
        descriptor_after = os.fstat(snapshot.descriptor)
        path_after = snapshot.path.lstat()
    except OSError as error:
        fail("input", f"cannot recheck {snapshot.label} input: {error}")
    if not same_stat(snapshot.before, descriptor_after) or not same_stat(
        snapshot.before, path_after
    ):
        fail("input", f"{snapshot.label} input changed before the comparison completed")


def validate_input_identities(inputs: tuple[InputSnapshot, ...]) -> None:
    identities: dict[tuple[int, int], str] = {}
    for snapshot in inputs:
        identity = (snapshot.before.st_dev, snapshot.before.st_ino)
        previous = identities.setdefault(identity, snapshot.label)
        if previous != snapshot.label:
            fail("input", f"{previous} and {snapshot.label} inputs alias the same file")


def require_exact_source_bytes(
    snapshot: InputSnapshot,
    expected_bytes: int,
    expected_sha256: str,
    code: str,
) -> None:
    observed_sha256 = hashlib.sha256(snapshot.data).hexdigest()
    if len(snapshot.data) != expected_bytes or observed_sha256 != expected_sha256:
        fail(
            code,
            f"{snapshot.label} raw bytes changed: "
            f"observed_bytes={len(snapshot.data)} observed_sha256={observed_sha256}; "
            f"expected_bytes={expected_bytes} expected_sha256={expected_sha256}",
        )


def compare_candidate_to_retained_raw(
    retained: InputSnapshot, candidate: InputSnapshot
) -> tuple[str, str]:
    """Admit exact retained bytes or the pinned strict trailer-ID relation only."""

    if candidate.data == retained.data:
        return "byte-exact retained fixture", "exact"
    if len(candidate.data) != len(retained.data):
        fail(
            "font_alpha_raw_profile",
            f"retained/candidate byte lengths differ: {len(retained.data)} != {len(candidate.data)}",
        )
    try:
        retained_normalized, retained_id_text, retained_id = (
            ID_VARIANCE.erase_strict_id(retained.data, "retained fixture")
        )
        candidate_normalized, candidate_id_text, candidate_id = (
            ID_VARIANCE.erase_strict_id(candidate.data, "candidate")
        )
    except SystemExit as error:
        fail(
            "font_alpha_raw_profile",
            f"strict retained/candidate relation failed: {error}",
        )
    except BaseException as error:
        fail(
            "font_alpha_raw_profile",
            f"strict retained/candidate relation raised {type(error).__name__}: {error}",
        )
    if retained_id == candidate_id:
        fail("font_alpha_raw_profile", "decoded trailer /ID values are equal")
    if retained_normalized != candidate_normalized:
        fail(
            "font_alpha_raw_profile",
            "retained and candidate inputs differ outside the strict duplicated trailer /ID payloads",
        )
    diagnostic = (
        f"bytes={len(retained.data)}; "
        f"retained_sha256={hashlib.sha256(retained.data).hexdigest()}; "
        f"candidate_sha256={hashlib.sha256(candidate.data).hexdigest()}; "
        f"retained_id={retained_id_text}; candidate_id={candidate_id_text}"
    )
    return "strict retained-fixture trailer-ID projection", diagnostic


def validate_output_paths(
    outputs: tuple[pathlib.Path, pathlib.Path], inputs: tuple[InputSnapshot, ...]
) -> None:
    resolved_outputs: list[pathlib.Path] = []
    for output in outputs:
        if not output.is_absolute() or "\n" in str(output) or "\r" in str(output):
            fail("output", f"output must be a canonical absolute path: {output}")
        if output.is_symlink():
            fail("output", f"output must not be symbolic: {output}")
        if output.exists() and not output.is_file():
            fail("output", f"existing output is not a regular file: {output}")
        parent = output.parent
        if (
            not parent.is_dir()
            or parent.resolve(strict=True) != parent
            or parent == pathlib.Path("/")
        ):
            fail("output", f"output parent is absent, noncanonical, or root: {parent}")
        resolved = output.resolve(strict=False)
        if resolved != output:
            fail(
                "output",
                f"output path has a symbolic or noncanonical component: {output}",
            )
        for snapshot in inputs:
            if resolved == snapshot.path:
                fail("output", f"output aliases {snapshot.label} input: {output}")
            if output.exists():
                try:
                    if os.path.samefile(output, snapshot.path):
                        fail(
                            "output",
                            f"output hard-links {snapshot.label} input: {output}",
                        )
                except OSError as error:
                    fail("output", f"cannot compare output identity: {error}")
        resolved_outputs.append(resolved)
    if resolved_outputs[0] == resolved_outputs[1]:
        fail("output", "target and navigation outputs must be distinct")
    if outputs[0].exists() and outputs[1].exists():
        try:
            if os.path.samefile(outputs[0], outputs[1]):
                fail("output", "target and navigation outputs are hard-link aliases")
        except OSError as error:
            fail("output", f"cannot compare output identities: {error}")


def manifest_payload_bytes(lines: tuple[str, ...]) -> int:
    return sum(len(line.encode("utf-8")) + 1 for line in lines)


def structure_variant_shape(
    lines: tuple[str, ...], label: str
) -> tuple[tuple[int, str], ...]:
    shape: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        for prefix in RAW_VARIANT_PREFIXES:
            if line.startswith(prefix):
                fields = line.split("\t")
                expected_fields = 4 if prefix == "page-content\t" else 3
                if len(fields) != expected_fields or not fields[1].startswith("page="):
                    fail(
                        "font_alpha_profile", f"{label} raw-variant record is malformed"
                    )
                shape.append((index, f"{prefix}{fields[1]}"))
                break
    expected_labels = tuple(
        label_value
        for page in range(EXPECTED_PAGES)
        for label_value in (
            f"page-content\tpage={page}",
            f"page-resources\tpage={page}",
        )
    )
    if (
        len(shape) != EXPECTED_VARIANT_RECORDS
        or tuple(value for _, value in shape) != expected_labels
    ):
        fail(
            "font_alpha_profile",
            f"{label} lacks the exact {EXPECTED_PAGES} content/resource record pairs",
        )
    return tuple(shape)


def compare_structure_reports(reference: Any, candidate: Any) -> None:
    if (
        len(reference.targets) != EXPECTED_TARGETS
        or reference.targets != candidate.targets
    ):
        fail(
            "font_alpha_profile",
            "hyperlink target tuple or source-profile count differs",
        )
    if len(reference.navigation) != EXPECTED_NAVIGATION_RECORDS or len(
        candidate.navigation
    ) != len(reference.navigation):
        fail(
            "font_alpha_profile",
            "navigation record count differs from the source profile",
        )
    if (
        len(reference.structure_manifest) != EXPECTED_STRUCTURE_RECORDS
        or len(candidate.structure_manifest) != EXPECTED_STRUCTURE_RECORDS
    ):
        fail(
            "font_alpha_profile",
            "tagged-structure record count differs from the source profile",
        )
    if manifest_payload_bytes(
        reference.structure_manifest
    ) != EXPECTED_STRUCTURE_PAYLOAD_BYTES or (
        manifest_payload_bytes(candidate.structure_manifest)
        != EXPECTED_STRUCTURE_PAYLOAD_BYTES
    ):
        fail(
            "font_alpha_profile",
            "tagged-structure payload byte count differs from the source profile",
        )
    if reference.structure_sha256 != EXPECTED_REFERENCE_STRUCTURE_SHA256:
        fail(
            "font_alpha_profile",
            "canonical tagged-structure digest is outside the source profile",
        )
    if candidate.structure_sha256 != EXPECTED_CANDIDATE_STRUCTURE_SHA256:
        fail(
            "font_alpha_profile",
            "candidate tagged-structure digest is outside the source profile",
        )
    if reference.navigation_sha256 != EXPECTED_REFERENCE_NAVIGATION_SHA256:
        fail(
            "font_alpha_profile",
            "canonical navigation digest is outside the source profile",
        )
    if candidate.navigation_sha256 != EXPECTED_CANDIDATE_NAVIGATION_SHA256:
        fail(
            "font_alpha_profile",
            "candidate navigation digest is outside the source profile",
        )

    reference_shape = structure_variant_shape(reference.structure_manifest, "reference")
    candidate_shape = structure_variant_shape(candidate.structure_manifest, "candidate")
    if reference_shape != candidate_shape:
        fail(
            "font_alpha_profile",
            "raw content/resource record positions or page identities differ",
        )
    variant_positions = tuple(index for index, _ in reference_shape)
    observed_differences = tuple(
        index
        for index, (reference_line, candidate_line) in enumerate(
            zip(reference.structure_manifest, candidate.structure_manifest, strict=True)
        )
        if reference_line != candidate_line
    )
    if observed_differences != variant_positions:
        fail(
            "font_alpha_profile",
            "the exact 32 page content/resource records are not the sole structure differences",
        )

    navigation_differences = tuple(
        index
        for index, (reference_line, candidate_line) in enumerate(
            zip(reference.navigation, candidate.navigation, strict=True)
        )
        if reference_line != candidate_line
    )
    if len(navigation_differences) != 1:
        fail(
            "font_alpha_profile",
            "navigation must differ only in one embedded structure digest",
        )
    navigation_index = navigation_differences[0]
    if not reference.navigation[navigation_index].startswith(
        "structure\t"
    ) or not candidate.navigation[navigation_index].startswith("structure\t"):
        fail(
            "font_alpha_profile",
            "the sole navigation difference is not the structure record",
        )


def font_number(name: str, path: str) -> int:
    matched = FONT_NAME.fullmatch(name)
    if matched is None:
        fail(
            "font_alpha_resource_keys",
            f"{path}: font resource key is not canonical /F<number>",
        )
    return int(matched.group(1))


def font_inventory(
    page: Any,
    page_number: int,
    label: str,
    closure_cache: dict[tuple[int, int], bytes],
) -> FontInventory:
    resources_value = STRUCTURE.dictionary_raw(page, "/Resources")
    resources = STRUCTURE.require_dictionary(
        resources_value, f"{label} page {page_number} Resources"
    )
    fonts_value = STRUCTURE.dictionary_raw(resources, "/Font")
    fonts = STRUCTURE.require_dictionary(
        fonts_value, f"{label} page {page_number} Font"
    )
    if not fonts:
        fail(
            "font_alpha_resource_keys",
            f"{label} page {page_number} has no font resources",
        )
    by_name: dict[str, bytes] = {}
    by_payload: dict[bytes, str] = {}
    for raw_name in fonts.keys():
        name = STRUCTURE.require_any_name(
            raw_name, f"{label} page {page_number} font key"
        )
        font_number(name, f"{label} page {page_number} {name}")
        font_value = STRUCTURE.dictionary_raw(fonts, name)
        reference = STRUCTURE.object_reference(font_value)
        if reference is None or not isinstance(font_value, IndirectObject):
            fail(
                "font_alpha_resource_keys",
                f"{label} page {page_number} {name} font resource is not indirect",
            )
        closure = closure_cache.get(reference)
        if closure is None:
            closure = STRUCTURE.resource_closure_payload(
                font_value,
                f"{label} page {page_number} Font/{name.lstrip('/')}",
            )
            closure_cache[reference] = closure
        if closure in by_payload:
            fail(
                "font_alpha_ambiguous",
                f"{label} page {page_number} font keys {by_payload[closure]} and {name} "
                "have identical full typed closures",
            )
        by_name[name] = closure
        by_payload[closure] = name
    return FontInventory(resources_value, fonts, by_name)


def lex_content(data: bytes, path: str) -> tuple[LexicalToken, ...]:
    """Lex PDF content while keeping exact spans and treating strings as opaque."""

    tokens: list[LexicalToken] = []
    length = len(data)
    index = 0
    while index < length:
        byte = data[index]
        if byte in PDF_WHITESPACE:
            index += 1
            continue
        if byte == ord("%"):
            index += 1
            while index < length and data[index] not in (0x0A, 0x0D):
                index += 1
            continue
        start = index
        if byte == ord("("):
            depth = 1
            index += 1
            while index < length and depth:
                current = data[index]
                if current == ord("\\"):
                    index += 1
                    if index >= length:
                        fail(
                            "font_alpha_lex",
                            f"{path}: literal string ends after an escape",
                        )
                    if (
                        data[index] == 0x0D
                        and index + 1 < length
                        and data[index + 1] == 0x0A
                    ):
                        index += 2
                    else:
                        index += 1
                    continue
                if current == ord("("):
                    depth += 1
                elif current == ord(")"):
                    depth -= 1
                index += 1
            if depth:
                fail("font_alpha_lex", f"{path}: unterminated literal string")
            tokens.append(LexicalToken("string", start, index, data[start:index]))
            continue
        if byte == ord("<"):
            if index + 1 < length and data[index + 1] == ord("<"):
                index += 2
                tokens.append(
                    LexicalToken("delimiter", start, index, data[start:index])
                )
                continue
            index += 1
            while index < length and data[index] != ord(">"):
                if data[index] not in PDF_WHITESPACE and data[index] not in HEX_DIGITS:
                    fail("font_alpha_lex", f"{path}: invalid byte in a hex string")
                index += 1
            if index >= length:
                fail("font_alpha_lex", f"{path}: unterminated hex string")
            index += 1
            tokens.append(LexicalToken("hex-string", start, index, data[start:index]))
            continue
        if byte == ord(">"):
            if index + 1 >= length or data[index + 1] != ord(">"):
                fail("font_alpha_lex", f"{path}: unmatched dictionary delimiter")
            index += 2
            tokens.append(LexicalToken("delimiter", start, index, data[start:index]))
            continue
        if byte in b"[]{}":
            index += 1
            tokens.append(LexicalToken("delimiter", start, index, data[start:index]))
            continue
        if byte == ord("/"):
            index += 1
            while (
                index < length
                and data[index] not in PDF_WHITESPACE
                and data[index] not in PDF_DELIMITERS
            ):
                if data[index] == ord("#"):
                    if (
                        index + 2 >= length
                        or data[index + 1] not in HEX_DIGITS
                        or data[index + 2] not in HEX_DIGITS
                    ):
                        fail("font_alpha_lex", f"{path}: malformed name escape")
                    index += 3
                else:
                    index += 1
            if index == start + 1:
                fail("font_alpha_lex", f"{path}: empty PDF name")
            tokens.append(LexicalToken("name", start, index, data[start:index]))
            continue
        while (
            index < length
            and data[index] not in PDF_WHITESPACE
            and data[index] not in PDF_DELIMITERS
        ):
            index += 1
        if index == start:
            fail("font_alpha_lex", f"{path}: unsupported delimiter byte 0x{byte:02x}")
        raw = data[start:index]
        if raw == b"BI":
            fail(
                "font_alpha_inline_image",
                f"{path}: inline-image syntax is outside this profile",
            )
        tokens.append(LexicalToken("word", start, index, raw))
    return tuple(tokens)


def parsed_tf_names(
    content_value: Any, reader: PdfReader, path: str
) -> tuple[int, tuple[str, ...]]:
    try:
        operations = ContentStream(content_value, reader).operations
    except Exception as error:
        fail("font_alpha_tf_shape", f"{path}: pypdf cannot parse operations: {error}")
    names: list[str] = []
    for operation_index, (operands, operator) in enumerate(operations):
        operation_path = f"{path} operation {operation_index}"
        if operator in (b"BI", b"ID", b"EI", b"INLINE IMAGE"):
            fail(
                "font_alpha_inline_image",
                f"{operation_path}: inline-image operation is outside this profile",
            )
        if operator != b"Tf":
            continue
        if len(operands) != 2:
            fail(
                "font_alpha_tf_shape",
                f"{operation_path}: Tf does not have two operands",
            )
        name = STRUCTURE.require_any_name(operands[0], f"{operation_path} Tf name")
        font_number(name, f"{operation_path} Tf name")
        try:
            STRUCTURE.canonical_number(operands[1], f"{operation_path} Tf size")
        except STRUCTURE.PdfStructureError as error:
            fail("font_alpha_tf_shape", f"{operation_path}: invalid Tf size: {error}")
        names.append(name)
    return len(operations), tuple(names)


def content_surface(
    page: Any,
    reader: PdfReader,
    page_number: int,
    label: str,
    font_names: set[str],
) -> ContentSurface:
    content_value = STRUCTURE.dictionary_raw(page, "/Contents")
    content = STRUCTURE.dereference(content_value)
    try:
        decoded = content.get_data()
    except Exception as error:
        fail(
            "font_alpha_content",
            f"{label} page {page_number}: cannot decode content: {error}",
        )
    if not isinstance(decoded, bytes) or not decoded:
        fail(
            "font_alpha_content",
            f"{label} page {page_number}: decoded content is empty",
        )
    tokens = lex_content(decoded, f"{label} page {page_number}")
    spans: list[tuple[int, int, str]] = []
    for index, token in enumerate(tokens):
        if token.kind != "word" or token.raw != b"Tf":
            continue
        if index < 2:
            fail(
                "font_alpha_tf_shape",
                f"{label} page {page_number}: Tf lacks lexical operands",
            )
        name_token = tokens[index - 2]
        size_token = tokens[index - 1]
        if (
            name_token.kind != "name"
            or size_token.kind != "word"
            or not PDF_NUMBER_BYTES.fullmatch(size_token.raw)
        ):
            fail(
                "font_alpha_tf_shape",
                f"{label} page {page_number}: Tf lexical operands are not name and number",
            )
        try:
            name = name_token.raw.decode("ascii")
        except UnicodeDecodeError:
            fail(
                "font_alpha_font_name",
                f"{label} page {page_number}: Tf name is not ASCII",
            )
        font_number(name, f"{label} page {page_number} Tf name")
        spans.append((name_token.start, name_token.end, name))

    operation_count, operation_names = parsed_tf_names(
        content_value, reader, f"{label} page {page_number}"
    )
    lexical_names = tuple(name for _, _, name in spans)
    if lexical_names != operation_names:
        fail(
            "font_alpha_token_binding",
            f"{label} page {page_number}: lexical and pypdf Tf-name sequences differ",
        )
    font_like_tokens = tuple(
        (token.start, token.end, token.raw.decode("ascii"))
        for token in tokens
        if token.kind == "name" and FONT_NAME_BYTES.fullmatch(token.raw)
    )
    if font_like_tokens != tuple(spans):
        fail(
            "font_alpha_token_binding",
            f"{label} page {page_number}: a font-like content name is not a Tf operand",
        )
    used = set(lexical_names)
    if not used <= font_names:
        fail(
            "font_alpha_unbound",
            f"{label} page {page_number}: Tf names an absent font resource",
        )
    if used != font_names:
        fail(
            "font_alpha_unused",
            f"{label} page {page_number}: a font resource is unused",
        )
    return ContentSurface(decoded, tuple(spans), operation_count)


def substitute_font_names(
    data: bytes,
    spans: tuple[tuple[int, int, str], ...],
    mapping: dict[str, str],
    path: str,
) -> bytes:
    output = bytearray()
    cursor = 0
    for start, end, name in spans:
        if start < cursor or end <= start or data[start:end] != name.encode("ascii"):
            fail(
                "font_alpha_token_binding",
                f"{path}: invalid or overlapping Tf token span",
            )
        replacement = mapping.get(name)
        if replacement is None:
            fail("font_alpha_unbound", f"{path}: no global mapping for {name}")
        output.extend(data[cursor:start])
        output.extend(replacement.encode("ascii"))
        cursor = end
    output.extend(data[cursor:])
    return bytes(output)


def compare_page(
    reference_reader: PdfReader,
    candidate_reader: PdfReader,
    page_index: int,
    reference_cache: dict[tuple[int, int], bytes],
    candidate_cache: dict[tuple[int, int], bytes],
    global_mapping: dict[str, str],
    global_reverse: dict[str, str],
    global_payloads: dict[tuple[str, str], bytes],
) -> tuple[int, int, int]:
    page_number = page_index + 1
    reference_page = reference_reader.pages[page_index]
    candidate_page = candidate_reader.pages[page_index]
    reference = font_inventory(
        reference_page, page_number, "reference", reference_cache
    )
    candidate = font_inventory(
        candidate_page, page_number, "candidate", candidate_cache
    )
    reference_by_payload = {
        payload: name for name, payload in reference.by_name.items()
    }
    candidate_by_payload = {
        payload: name for name, payload in candidate.by_name.items()
    }
    if set(reference_by_payload) != set(candidate_by_payload):
        fail(
            "font_alpha_font_closure",
            f"page {page_number}: full typed font-closure sets differ",
        )

    page_mapping: dict[str, str] = {}
    for candidate_name in sorted(
        candidate.by_name, key=lambda name: font_number(name, name)
    ):
        closure = candidate.by_name[candidate_name]
        reference_name = reference_by_payload[closure]
        previous_reference = global_mapping.setdefault(candidate_name, reference_name)
        if previous_reference != reference_name:
            fail(
                "font_alpha_global_binding",
                f"{candidate_name} maps to different canonical names across pages",
            )
        previous_candidate = global_reverse.setdefault(reference_name, candidate_name)
        if previous_candidate != candidate_name:
            fail(
                "font_alpha_global_binding",
                f"{reference_name} maps from different candidate names across pages",
            )
        for side_name, side_label in (
            (candidate_name, "candidate"),
            (reference_name, "reference"),
        ):
            key = (side_label, side_name)
            previous_payload = global_payloads.setdefault(key, closure)
            if previous_payload != closure:
                fail(
                    "font_alpha_global_binding",
                    f"{side_label} font {side_name} has different closures across pages",
                )
        page_mapping[candidate_name] = reference_name

    # Equality is decided from the complete typed payload, after renaming only
    # the candidate page's proven /Font dictionary keys. Digests are diagnostic.
    reference_resources = STRUCTURE.resource_closure_payload(
        reference.resources_value,
        f"reference page {page_number} Resources",
    )
    candidate_resources = STRUCTURE.resource_closure_payload(
        candidate.resources_value,
        f"candidate page {page_number} Resources",
        dictionary_key_aliases={id(candidate.fonts): page_mapping},
    )
    if reference_resources != candidate_resources:
        fail(
            "font_alpha_nonfont",
            f"page {page_number}: resource roots differ beyond the proven font-key rename "
            f"(reference_sha256={hashlib.sha256(reference_resources).hexdigest()}; "
            f"candidate_sha256={hashlib.sha256(candidate_resources).hexdigest()})",
        )

    reference_content = content_surface(
        reference_page,
        reference_reader,
        page_number,
        "reference",
        set(reference.by_name),
    )
    candidate_content = content_surface(
        candidate_page,
        candidate_reader,
        page_number,
        "candidate",
        set(candidate.by_name),
    )
    if reference_content.operation_count != candidate_content.operation_count:
        fail(
            "font_alpha_content", f"page {page_number}: parsed operation counts differ"
        )
    transformed = substitute_font_names(
        candidate_content.decoded,
        candidate_content.font_spans,
        page_mapping,
        f"candidate page {page_number}",
    )
    if transformed != reference_content.decoded:
        fail(
            "font_alpha_content",
            f"page {page_number}: decoded content differs after the sole proven Tf-name rename",
        )
    if len(reference_content.font_spans) != len(candidate_content.font_spans):
        fail("font_alpha_content", f"page {page_number}: Tf-use counts differ")
    return (
        reference_content.operation_count,
        len(reference_content.font_spans),
        len(reference.by_name),
    )


def compare_font_alpha_core(reference_data: bytes, candidate_data: bytes) -> PairStats:
    """Prove only the typed reachable-graph relation, without raw/profile checks.

    This lower layer intentionally says nothing about serialized bytes, trailer
    ownership, unreachable bytes, or the retained source profile. The operational
    CLI calls it only after the raw canonical/fixture relation and complete legacy
    structure profile are established. Keeping the semantic core separate lets
    mutation tests reach the lexer, binding, closure, and exact-content obligations
    instead of failing only at an outer digest pin.
    """

    try:
        reference_reader = PdfReader(io.BytesIO(reference_data), strict=True)
        candidate_reader = PdfReader(io.BytesIO(candidate_data), strict=True)
    except Exception as error:
        fail("pdf_parse", f"strict pair parse failed: {error}")
    page_count = len(reference_reader.pages)
    if page_count < 1 or page_count != len(candidate_reader.pages):
        fail(
            "font_alpha_page_count",
            "font comparison requires equal, nonzero page counts",
        )

    reference_cache: dict[tuple[int, int], bytes] = {}
    candidate_cache: dict[tuple[int, int], bytes] = {}
    global_mapping: dict[str, str] = {}
    global_reverse: dict[str, str] = {}
    global_payloads: dict[tuple[str, str], bytes] = {}
    operations = 0
    tf_uses = 0
    page_font_bindings = 0
    for page_index in range(page_count):
        page_operations, page_tf_uses, page_bindings = compare_page(
            reference_reader,
            candidate_reader,
            page_index,
            reference_cache,
            candidate_cache,
            global_mapping,
            global_reverse,
            global_payloads,
        )
        operations += page_operations
        tf_uses += page_tf_uses
        page_font_bindings += page_bindings

    ordered_pairs = tuple(
        sorted(global_mapping.items(), key=lambda pair: font_number(pair[0], pair[0]))
    )
    if len(global_reverse) != len(global_mapping):
        fail("font_alpha_global_binding", "global font-name mapping is not bijective")

    mapping_lines: list[str] = []
    for candidate_name, reference_name in ordered_pairs:
        closure = global_payloads[("candidate", candidate_name)]
        if closure != global_payloads[("reference", reference_name)]:
            fail(
                "font_alpha_font_closure",
                "a global mapped font closure differs exactly",
            )
        mapping_lines.append(
            f"font\tcandidate={candidate_name}\tcanonical={reference_name}\t"
            f"closure_sha256={hashlib.sha256(closure).hexdigest()}"
        )
    mapping_payload = "".join(f"{line}\n" for line in mapping_lines).encode("ascii")
    mapping_sha256 = hashlib.sha256(mapping_payload).hexdigest()

    return PairStats(
        page_count,
        operations,
        tf_uses,
        page_font_bindings,
        len(global_mapping),
        mapping_sha256,
        ordered_pairs,
    )


def enforce_legacy_font_profile(stats: PairStats) -> None:
    """Bind the semantic core to the one retained TeX Live 2023 observation."""

    if stats.font_name_pairs != EXPECTED_FONT_NAME_PAIRS:
        fail(
            "font_alpha_profile",
            "global font-name mapping differs from the exact source profile",
        )
    for candidate_name, reference_name in stats.font_name_pairs:
        if (
            font_number(reference_name, reference_name)
            - font_number(candidate_name, candidate_name)
            != EXPECTED_FONT_NAME_OFFSET
        ):
            fail(
                "font_alpha_profile",
                "font-name mapping does not have the exact +8 offset",
            )
    observed_profile = (
        stats.pages,
        stats.operations,
        stats.tf_uses,
        stats.page_font_bindings,
        stats.global_font_mappings,
        stats.mapping_sha256,
    )
    expected_profile = (
        EXPECTED_PAGES,
        EXPECTED_OPERATIONS,
        EXPECTED_TF_USES,
        EXPECTED_PAGE_FONT_BINDINGS,
        EXPECTED_GLOBAL_FONT_MAPPINGS,
        EXPECTED_FONT_MAPPING_SHA256,
    )
    if observed_profile != expected_profile:
        fail(
            "font_alpha_profile",
            "font-operation profile changed: "
            f"observed={observed_profile!r} expected={expected_profile!r}",
        )


def write_lines(path: pathlib.Path, lines: tuple[str, ...]) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write("".join(f"{line}\n" for line in lines))
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                pathlib.Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} "
            "REFERENCE.pdf CANDIDATE.pdf RETAINED_OLD.pdf targets.txt navigation.txt",
            file=sys.stderr,
        )
        return 2
    snapshots: list[InputSnapshot] = []
    try:
        reference = open_input(argv[0], "reference")
        snapshots.append(reference)
        candidate = open_input(argv[1], "candidate")
        snapshots.append(candidate)
        retained = open_input(argv[2], "retained old-toolchain fixture")
        snapshots.append(retained)
        inputs = (reference, candidate, retained)
        validate_input_identities(inputs)
        outputs = (pathlib.Path(argv[3]), pathlib.Path(argv[4]))
        validate_output_paths(outputs, inputs)
        require_exact_source_bytes(
            reference,
            EXPECTED_REFERENCE_BYTES,
            EXPECTED_REFERENCE_SHA256,
            "font_alpha_raw_reference",
        )
        require_exact_source_bytes(
            retained,
            EXPECTED_RETAINED_BYTES,
            EXPECTED_RETAINED_SHA256,
            "font_alpha_raw_fixture",
        )
        recheck_dependency(STRUCTURE_DEPENDENCY)
        recheck_dependency(ID_VARIANCE_DEPENDENCY)

        # The reference always passes the unchanged strict canonical policy.
        reference_report = STRUCTURE.validate_bytes(reference.data)
        if candidate.data == reference.data:
            # Cross mode must retain a distinct-file, exact-byte identity
            # control. It does not invoke the exceptional alpha relation.
            candidate_report = STRUCTURE.validate_bytes(candidate.data)
            relation = "exact canonical identity"
            raw_relation = "exact canonical bytes"
            raw_relation_diagnostic = "not invoked"
            stats = None
        else:
            raw_relation, raw_relation_diagnostic = compare_candidate_to_retained_raw(
                retained, candidate
            )
            # Only the legacy candidate's two terminal manifest-digest
            # comparisons are deferred to the exact, source-profiled pair.
            candidate_report = STRUCTURE.validate_bytes(
                candidate.data, enforce_manifest_digests=False
            )
            compare_structure_reports(reference_report, candidate_report)
            stats = compare_font_alpha_core(reference.data, candidate.data)
            enforce_legacy_font_profile(stats)
            relation = "source-profiled typed font-resource alpha-equivalence"

        recheck_input(reference)
        recheck_input(candidate)
        recheck_input(retained)
        recheck_dependency(STRUCTURE_DEPENDENCY)
        recheck_dependency(ID_VARIANCE_DEPENDENCY)
        validate_output_paths(outputs, inputs)
        write_lines(outputs[0], candidate_report.targets)
        # The sole candidate navigation difference embeds its raw structure
        # digest. Canonical navigation is emitted only after the exact pair
        # relation proves all nonvariant records and every permitted rename.
        write_lines(outputs[1], reference_report.navigation)
        recheck_input(reference)
        recheck_input(candidate)
        recheck_input(retained)
        recheck_dependency(STRUCTURE_DEPENDENCY)
        recheck_dependency(ID_VARIANCE_DEPENDENCY)
    except (OSError, AlphaEquivalenceError, STRUCTURE.PdfStructureError) as error:
        code = getattr(error, "code", "io")
        print(f"{CHECK_NAME} failed [{code}]: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"{CHECK_NAME} failed [internal]: {error}", file=sys.stderr)
        return 1
    finally:
        for snapshot in reversed(snapshots):
            try:
                os.close(snapshot.descriptor)
            except OSError:
                pass
    if stats is None:
        details = (
            f"pages={EXPECTED_PAGES}; "
            f"structure_sha256={reference_report.structure_sha256}; "
            f"pdf_sha256={hashlib.sha256(reference.data).hexdigest()}; "
            f"retained_sha256={hashlib.sha256(retained.data).hexdigest()}; "
            f"raw_relation={raw_relation}"
        )
    else:
        details = (
            f"pages={stats.pages}; operations={stats.operations}; Tf_uses={stats.tf_uses}; "
            f"page_font_bindings={stats.page_font_bindings}; "
            f"global_font_mappings={stats.global_font_mappings}; "
            f"mapping_sha256={stats.mapping_sha256}; "
            f"reference_structure_sha256={reference_report.structure_sha256}; "
            f"candidate_structure_sha256={candidate_report.structure_sha256}; "
            f"reference_sha256={hashlib.sha256(reference.data).hexdigest()}; "
            f"candidate_sha256={hashlib.sha256(candidate.data).hexdigest()}; "
            f"retained_sha256={hashlib.sha256(retained.data).hexdigest()}; "
            f"raw_relation={raw_relation}; "
            f"raw_relation_diagnostic={raw_relation_diagnostic}"
        )
    print(f"OK: {relation} ({details})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
