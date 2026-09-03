#!/usr/bin/env python3
"""Validate the bounded active-content and navigation policy for the results-guide PDF.

This is a source-specific artifact policy. Typed numerical records use pypdf's represented-
binary64 values; the separate exact-build gate binds raw same-toolchain bytes. This is not a
generic malware detector, a PDF/UA validator, or a proof that an arbitrary PDF viewer is safe.
"""

from __future__ import annotations

import hashlib
import io
import logging
import math
import os
import pathlib
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from typing import Any

from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    ContentStream,
    DictionaryObject,
    EncodedStreamObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    StreamObject,
    TextStringObject,
)


EXPECTED_ROOT_KEYS = {
    "/Lang",
    "/MarkInfo",
    "/Metadata",
    "/Names",
    "/OpenAction",
    "/Outlines",
    "/PageLabels",
    "/PageMode",
    "/Pages",
    "/StructTreeRoot",
    "/Type",
}
EXPECTED_NAMED_DESTINATIONS = {
    "Doc-Start": 0,
    "Item.1": 20,
    "Item.10": 21,
    "Item.11": 21,
    "Item.12": 21,
    "Item.13": 21,
    "Item.14": 21,
    "Item.2": 20,
    "Item.3": 20,
    "Item.4": 20,
    "Item.5": 20,
    "Item.6": 21,
    "Item.7": 21,
    "Item.8": 21,
    "Item.9": 21,
    "figure.caption.4": 3,
    "figure.caption.7": 6,
    "none.1": 2,
    "none.2": 2,
    "none.3": 5,
    "none.4": 16,
    "page.1": 1,
    "page.10": 10,
    "page.11": 11,
    "page.12": 12,
    "page.13": 13,
    "page.14": 14,
    "page.15": 15,
    "page.16": 16,
    "page.17": 17,
    "page.18": 18,
    "page.19": 19,
    "page.2": 2,
    "page.20": 20,
    "page.21": 21,
    "page.22": 22,
    "page.3": 3,
    "page.4": 4,
    "page.5": 5,
    "page.6": 6,
    "page.7": 7,
    "page.8": 8,
    "page.9": 9,
    "section*.1": 2,
    "section*.12": 10,
    "section*.15": 12,
    "section*.19": 16,
    "section*.6": 5,
    "section*.8": 7,
    "subsection*.10": 7,
    "subsection*.11": 9,
    "subsection*.13": 10,
    "subsection*.14": 11,
    "subsection*.16": 12,
    "subsection*.17": 13,
    "subsection*.18": 15,
    "subsection*.2": 2,
    "subsection*.20": 16,
    "subsection*.3": 2,
    "subsection*.5": 3,
    "subsection*.9": 7,
    "subsubsection*.21": 17,
    "subsubsection*.22": 20,
    "subsubsection*.23": 21,
    "subsubsection*.24": 21,
}
EXPECTED_OUTLINE = [
    (0, 2, "1. Reading conventions and semantic firewall", "section*.1"),
    (1, 2, "Evidence labels", "subsection*.2"),
    (1, 2, "Five distinct lanes", "subsection*.3"),
    (1, 3, "Lattice positions versus audit coordinates", "subsection*.5"),
    (0, 5, "2. Result map", "section*.6"),
    (0, 7, "3. Categorical-Sx theory", "section*.8"),
    (1, 7, "3.1 Foundational semantic audit", "subsection*.9"),
    (1, 7, "3.2 Fixed finite-alphabet plug-in convergence", "subsection*.10"),
    (1, 9, "3.3 Support-change-tolerant averaged-Sx continuity", "subsection*.11"),
    (0, 10, "4. Sampling and exact finite-table assurance", "section*.12"),
    (1, 10, "4.1 Dependency-color concentration", "subsection*.13"),
    (1, 11, "4.2 Exact two-source categorical-Sx assurance", "subsection*.14"),
    (0, 12, "5. Higher-source, numerical, and continuous-estimator assurance", "section*.15"),
    (1, 12, "5.1 SxPID3 source-marginal factorization and bounded audit", "subsection*.16"),
    (1, 13, "5.2 Represented-binary64 and quantizer assurance", "subsection*.17"),
    (1, 15, "5.3 KSG positive-integer harmonic arithmetic", "subsection*.18"),
    (0, 16, "6. Estimator choice, global nonclaims, and further reading", "section*.19"),
    (1, 16, "6.1 Wibral-line roadmap for high dimension and non-Euclidean geometry", "subsection*.20"),
]
EXPECTED_ACTION_COUNTS = Counter({"/GoTo": 37, "/URI": 89})
EXPECTED_LINK_COUNTS = Counter({"/GoTo": 18, "/URI": 89})
# This v2 profile binds all 217 navigation records and 53,391 payload bytes of the expanded
# 23-page guide. The digest is a source-specific artifact census, not a mathematical or
# accessibility claim.
EXPECTED_NAVIGATION_SHA256 = "b0d32c762b6d7366037ef5cf3bc2cf39095d785470d51bee7af097eeca67ce7d"
EXPECTED_STRUCTURE_ELEMENTS = 1059
# This v2 profile binds 2,266 semantic structure records and 116,012 payload bytes. It covers the
# tagged hierarchy, page resources, content, MCIDs, ParentTree ownership, and OBJR topology.
EXPECTED_STRUCTURE_SHA256 = "7718c629f2d795c865ce0170c59916d692a47ae7218a7ede85f58044ab889755"

FORBIDDEN_KEYS = {
    "/AA",
    "/AcroForm",
    "/AF",
    "/Collection",
    "/EF",
    "/EmbeddedFiles",
    "/JavaScript",
    "/JS",
    "/Perms",
    "/RichMediaContent",
    "/RichMediaSettings",
    "/XFA",
}
NONDECLARED_ACTIONS = {
    "/GoToE",
    "/GoTo3DView",
    "/Hide",
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Movie",
    "/Named",
    "/Rendition",
    "/ResetForm",
    "/RichMedia",
    "/SetOCGState",
    "/Sound",
    "/SubmitForm",
    "/Thread",
    "/Trans",
}
DECLARED_ACTIONS = {"/GoTo", "/URI"}
KNOWN_ACTIONS = DECLARED_ACTIONS | NONDECLARED_ACTIONS
FORBIDDEN_ANNOTATIONS = {
    "/3D",
    "/FileAttachment",
    "/Movie",
    "/Redact",
    "/RichMedia",
    "/Screen",
    "/Sound",
    "/TrapNet",
    "/Watermark",
    "/Widget",
}


class PdfStructureError(Exception):
    """A deterministic artifact-policy failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class StructureReport:
    targets: tuple[str, ...]
    navigation: tuple[str, ...]
    navigation_sha256: str
    structure_manifest: tuple[str, ...]
    structure_sha256: str


@dataclass(frozen=True)
class XyzDestination:
    """One fully typed, normalized XYZ destination in the artifact coordinate frame."""

    page: int
    left: str
    top: str
    zoom: str

    def payload(self) -> str:
        return f"{self.page}\t/XYZ\t{self.left}\t{self.top}\t{self.zoom}"


@dataclass
class StructureIndex:
    """Validated tagged-PDF structure needed to bind accessible navigation semantics."""

    document_reference: tuple[int, int]
    path_by_reference: dict[tuple[int, int], str]
    role_by_reference: dict[tuple[int, int], str]
    id_to_reference: dict[str, tuple[int, int]]
    mcr_parents: dict[tuple[int, int], tuple[int, int]]
    objr_records: dict[tuple[int, int], tuple[int, tuple[int, int], str]]
    semantic_lines: list[str]


@dataclass(frozen=True)
class ActionOwner:
    """One explicitly validated catalog, outline, or link-annotation action edge."""

    path: str
    container: Any
    key: str
    action: Any
    kind: str


def fail(code: str, message: str) -> None:
    raise PdfStructureError(code, message)


def dereference(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def object_reference(value: Any) -> tuple[int, int] | None:
    if isinstance(value, IndirectObject):
        return value.idnum, value.generation
    reference = getattr(value, "indirect_reference", None)
    if isinstance(reference, IndirectObject):
        return reference.idnum, reference.generation
    return None


def object_identity(value: Any) -> tuple[str, int, int] | tuple[str, int]:
    reference = object_reference(value)
    if reference is not None:
        return "indirect", reference[0], reference[1]
    return "direct", id(dereference(value))


def key_set(value: DictionaryObject) -> set[str]:
    return {str(key) for key in value.keys()}


def dictionary_raw(value: DictionaryObject, key: str) -> Any:
    try:
        return value.raw_get(key)
    except KeyError:
        return None


def array_raw(value: ArrayObject, index: int) -> Any:
    return list.__getitem__(value, index)


def require_dictionary(value: Any, path: str) -> DictionaryObject:
    resolved = dereference(value)
    if not isinstance(resolved, DictionaryObject) or isinstance(resolved, StreamObject):
        fail("dictionary_shape", f"{path}: expected a non-stream dictionary")
    return resolved


def require_array(value: Any, length: int, path: str) -> ArrayObject:
    resolved = dereference(value)
    if not isinstance(resolved, ArrayObject) or len(resolved) != length:
        fail("array_shape", f"{path}: expected an array of length {length}")
    return resolved


def require_name(value: Any, expected: str, path: str) -> None:
    resolved = dereference(value)
    if not isinstance(resolved, NameObject) or str(resolved) != expected:
        fail("typed_name", f"{path}: expected the name {expected}")


def require_any_name(value: Any, path: str) -> str:
    resolved = dereference(value)
    if not isinstance(resolved, NameObject):
        fail("typed_name", f"{path}: expected a name")
    text = str(resolved)
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in text):
        fail("manifest_control", f"{path}: name contains a control character")
    return text


def require_text(value: Any, path: str) -> str:
    resolved = dereference(value)
    if not isinstance(resolved, TextStringObject):
        fail("typed_text", f"{path}: expected a text string")
    text = str(resolved)
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in text):
        fail("manifest_control", f"{path}: text contains a control character")
    return text


def require_ascii_text(value: Any, path: str) -> str:
    """Require the canonical raw encoding used by byte-sensitive identifiers and targets."""

    resolved = dereference(value)
    text = require_text(resolved, path)
    try:
        canonical_bytes = text.encode("ascii")
    except UnicodeEncodeError:
        fail("text_encoding", f"{path}: text is outside the declared ASCII navigation schema")
    try:
        original_bytes = resolved.original_bytes
    except Exception as error:
        fail("text_encoding", f"{path}: original string bytes are unavailable: {error}")
    if original_bytes != canonical_bytes:
        fail("text_encoding", f"{path}: string bytes are not canonical ASCII")
    return text


def require_utf16be_text(value: Any, path: str) -> str:
    """Require the canonical UTF-16BE-with-BOM encoding used by file-specification /UF."""

    resolved = dereference(value)
    text = require_text(resolved, path)
    canonical_bytes = b"\xfe\xff" + text.encode("utf-16-be")
    try:
        original_bytes = resolved.original_bytes
    except Exception as error:
        fail("text_encoding", f"{path}: original string bytes are unavailable: {error}")
    if original_bytes != canonical_bytes:
        fail("text_encoding", f"{path}: string bytes are not canonical UTF-16BE")
    return text


def require_integer(value: Any, expected: int | None, path: str) -> int:
    resolved = dereference(value)
    if not isinstance(resolved, NumberObject) or isinstance(resolved, BooleanObject):
        fail("typed_integer", f"{path}: expected an integer")
    observed = int(resolved)
    if expected is not None and observed != expected:
        fail("typed_integer", f"{path}: expected integer {expected}")
    return observed


def canonical_number(value: Any, path: str) -> tuple[float, str]:
    resolved = dereference(value)
    if not isinstance(resolved, (FloatObject, NumberObject)) or isinstance(
        resolved, BooleanObject
    ):
        fail("typed_number", f"{path}: expected a PDF number")
    number = float(resolved)
    if not math.isfinite(number):
        fail("typed_number", f"{path}: number is not finite")
    if isinstance(resolved, FloatObject):
        token = f"real:{number.hex()}"
    else:
        token = f"int:{int(resolved)}"
    return number, token


def require_null(value: Any, path: str) -> str:
    if not isinstance(dereference(value), NullObject):
        fail("typed_null", f"{path}: expected null")
    return "null"


def require_true(value: Any, path: str) -> None:
    resolved = dereference(value)
    if not isinstance(resolved, BooleanObject) or resolved.value is not True:
        fail("typed_boolean", f"{path}: expected true")


def page_number_for_reference(reader: PdfReader, value: Any, path: str) -> int:
    reference = object_reference(value)
    if reference is None:
        fail("page_reference", f"{path}: expected an indirect page reference")
    for page_number, page in enumerate(reader.pages):
        if object_reference(page) == reference:
            return page_number
    fail("page_reference", f"{path}: page reference is outside the page tree")
    raise RuntimeError("unreachable")


def validate_xyz_array(reader: PdfReader, value: Any, path: str) -> XyzDestination:
    destination = require_array(value, 5, path)
    page = page_number_for_reference(reader, array_raw(destination, 0), f"{path}[0]")
    require_name(array_raw(destination, 1), "/XYZ", f"{path}[1]")
    left, left_token = canonical_number(array_raw(destination, 2), f"{path}[2]")
    top, top_token = canonical_number(array_raw(destination, 3), f"{path}[3]")
    zoom_token = require_null(array_raw(destination, 4), f"{path}[4]")
    if not 0.0 <= left <= 595.276 or not 0.0 <= top <= 841.89:
        fail("destination_geometry", f"{path}: XYZ coordinate is outside A4")
    return XyzDestination(page, left_token, top_token, zoom_token)


def validate_structure_tree(reader: PdfReader, root: DictionaryObject) -> StructureIndex:
    """Validate the complete tagged hierarchy and its ID index without trusting object numbers."""

    structure_value = dictionary_raw(root, "/StructTreeRoot")
    structure_reference = object_reference(structure_value)
    if structure_reference is None:
        fail("structure_tree", "catalog StructTreeRoot must be indirect")
    structure = require_dictionary(structure_value, "catalog StructTreeRoot")
    if key_set(structure) != {"/Type", "/K", "/IDTree", "/ParentTree", "/RoleMap"}:
        fail("structure_tree", "catalog StructTreeRoot changed shape")
    require_name(dictionary_raw(structure, "/Type"), "/StructTreeRoot", "StructTreeRoot /Type")

    role_map_value = dictionary_raw(structure, "/RoleMap")
    if object_reference(role_map_value) is None:
        fail("structure_tree", "StructTreeRoot /RoleMap must be indirect")
    role_map = require_dictionary(role_map_value, "StructTreeRoot /RoleMap")
    if len(role_map) != 39:
        fail("structure_tree", "StructTreeRoot /RoleMap entry count changed")
    semantic_lines = ["structure-root\t/StructTreeRoot"]
    for key in sorted(role_map.keys(), key=str):
        role = require_any_name(key, "StructTreeRoot /RoleMap key")
        standard = require_any_name(
            dictionary_raw(role_map, str(key)), f"StructTreeRoot /RoleMap {role}"
        )
        semantic_lines.append(f"role-map\t{role}\t{standard}")

    path_by_reference: dict[tuple[int, int], str] = {}
    role_by_reference: dict[tuple[int, int], str] = {}
    id_to_reference: dict[str, tuple[int, int]] = {}
    mcr_parents: dict[tuple[int, int], tuple[int, int]] = {}
    objr_records: dict[tuple[int, int], tuple[int, tuple[int, int], str]] = {}
    seen_k_containers: set[tuple[int, int] | tuple[str, int]] = set()

    def container_identity(value: Any, resolved: Any) -> tuple[int, int] | tuple[str, int]:
        reference = object_reference(value)
        return reference if reference is not None else ("direct", id(resolved))

    def visit_k(value: Any, parent_reference: tuple[int, int], path: str) -> None:
        resolved = dereference(value)
        if isinstance(resolved, ArrayObject):
            identity = container_identity(value, resolved)
            if identity in seen_k_containers:
                fail("structure_tree", f"{path}: shared or cyclic structure-child array")
            seen_k_containers.add(identity)
            semantic_lines.append(f"structure-array\t{path}\t{len(resolved)}")
            for index in range(len(resolved)):
                visit_k(array_raw(resolved, index), parent_reference, f"{path}[{index}]")
            return
        if not isinstance(resolved, DictionaryObject) or isinstance(resolved, StreamObject):
            fail("structure_tree", f"{path}: unsupported structure child")
        child_type = require_any_name(dictionary_raw(resolved, "/Type"), f"{path} /Type")
        if child_type == "/StructElem":
            visit_element(value, parent_reference, path)
            return
        identity = container_identity(value, resolved)
        if identity in seen_k_containers:
            fail("structure_tree", f"{path}: shared or cyclic marked-content record")
        seen_k_containers.add(identity)
        if child_type == "/MCR":
            if key_set(resolved) != {"/Type", "/Pg", "/MCID"}:
                fail("structure_tree", f"{path}: marked-content record changed shape")
            page = page_number_for_reference(reader, dictionary_raw(resolved, "/Pg"), f"{path} /Pg")
            mcid = require_integer(dictionary_raw(resolved, "/MCID"), None, f"{path} /MCID")
            if mcid < 0 or (page, mcid) in mcr_parents:
                fail("structure_tree", f"{path}: negative or duplicate page MCID")
            mcr_parents[(page, mcid)] = parent_reference
            semantic_lines.append(f"mcr\t{path}\tpage={page}\tmcid={mcid}")
            return
        if child_type == "/OBJR":
            if key_set(resolved) != {"/Type", "/Pg", "/Obj"}:
                fail("structure_tree", f"{path}: object-reference record changed shape")
            page = page_number_for_reference(reader, dictionary_raw(resolved, "/Pg"), f"{path} /Pg")
            object_reference_value = object_reference(dictionary_raw(resolved, "/Obj"))
            if object_reference_value is None or object_reference_value in objr_records:
                fail("structure_tree", f"{path}: object reference is direct or duplicated")
            objr_records[object_reference_value] = (page, parent_reference, path)
            return
        fail("structure_tree", f"{path}: unsupported structure-child type {child_type}")

    def visit_element(value: Any, parent_reference: tuple[int, int], path: str) -> None:
        reference = object_reference(value)
        if reference is None or reference in path_by_reference:
            fail("structure_tree", f"{path}: structure element is direct, shared, or cyclic")
        element = require_dictionary(value, path)
        if key_set(element) != {"/Type", "/S", "/P", "/K", "/ID"}:
            fail("structure_tree", f"{path}: structure element changed shape")
        require_name(dictionary_raw(element, "/Type"), "/StructElem", f"{path} /Type")
        role = require_any_name(dictionary_raw(element, "/S"), f"{path} /S")
        identifier = require_ascii_text(dictionary_raw(element, "/ID"), f"{path} /ID")
        if object_reference(dictionary_raw(element, "/P")) != parent_reference:
            fail("structure_tree", f"{path}: structure parent link changed")
        if identifier in id_to_reference:
            fail("structure_tree", f"{path}: duplicate structure ID {identifier!r}")
        path_by_reference[reference] = path
        role_by_reference[reference] = role
        id_to_reference[identifier] = reference
        semantic_lines.append(f"structure-element\t{path}\t{identifier}\t{role}")
        visit_k(dictionary_raw(element, "/K"), reference, f"{path}/K")

    document_value = dictionary_raw(structure, "/K")
    document_reference = object_reference(document_value)
    if document_reference is None:
        fail("structure_tree", "StructTreeRoot /K must be one indirect document element")
    visit_element(document_value, structure_reference, "Document")
    document = require_dictionary(document_value, "Document")
    require_name(dictionary_raw(document, "/S"), "/Document", "Document /S")
    if len(path_by_reference) != EXPECTED_STRUCTURE_ELEMENTS:
        fail(
            "structure_tree",
            f"expected {EXPECTED_STRUCTURE_ELEMENTS} structure elements, "
            f"observed {len(path_by_reference)}",
        )

    id_tree_value = dictionary_raw(structure, "/IDTree")
    if object_reference(id_tree_value) is None:
        fail("structure_tree", "StructTreeRoot /IDTree must be indirect")
    id_tree = require_dictionary(id_tree_value, "StructTreeRoot /IDTree")
    if key_set(id_tree) != {"/Kids"}:
        fail("structure_tree", "IDTree root changed shape")
    kids = dereference(dictionary_raw(id_tree, "/Kids"))
    if not isinstance(kids, ArrayObject) or len(kids) != 22:
        fail("structure_tree", "IDTree root does not have the declared 22 leaves")
    id_entries: list[tuple[str, tuple[int, int]]] = []
    seen_id_nodes: set[tuple[int, int] | tuple[str, int]] = set()
    for leaf_index in range(len(kids)):
        leaf_value = array_raw(kids, leaf_index)
        leaf = require_dictionary(leaf_value, f"IDTree/Kids[{leaf_index}]")
        identity = container_identity(leaf_value, leaf)
        if identity in seen_id_nodes:
            fail("structure_tree", "IDTree contains a shared leaf")
        seen_id_nodes.add(identity)
        if key_set(leaf) != {"/Limits", "/Names"}:
            fail("structure_tree", f"IDTree/Kids[{leaf_index}]: leaf changed shape")
        names = dereference(dictionary_raw(leaf, "/Names"))
        if not isinstance(names, ArrayObject) or not names or len(names) % 2:
            fail("structure_tree", f"IDTree/Kids[{leaf_index}]: Names is empty or odd")
        leaf_entries: list[tuple[str, tuple[int, int]]] = []
        for index in range(0, len(names), 2):
            identifier = require_ascii_text(
                array_raw(names, index), f"IDTree/Kids[{leaf_index}]/Names[{index}]"
            )
            reference = object_reference(array_raw(names, index + 1))
            if reference is None:
                fail("structure_tree", "IDTree maps an ID to a direct object")
            leaf_entries.append((identifier, reference))
        if [item[0] for item in leaf_entries] != sorted(item[0] for item in leaf_entries):
            fail("structure_tree", f"IDTree/Kids[{leaf_index}]: IDs are not ordered")
        limits = require_array(dictionary_raw(leaf, "/Limits"), 2, f"IDTree/Kids[{leaf_index}]/Limits")
        observed_limits = [
            require_ascii_text(
                array_raw(limits, 0), f"IDTree/Kids[{leaf_index}]/Limits[0]"
            ),
            require_ascii_text(
                array_raw(limits, 1), f"IDTree/Kids[{leaf_index}]/Limits[1]"
            ),
        ]
        if observed_limits != [leaf_entries[0][0], leaf_entries[-1][0]]:
            fail("structure_tree", f"IDTree/Kids[{leaf_index}]: Limits changed")
        semantic_lines.append(
            f"id-tree-leaf\t{leaf_index}\t{observed_limits[0]}\t{observed_limits[1]}"
            f"\tcount={len(leaf_entries)}"
        )
        id_entries.extend(leaf_entries)
    if [item[0] for item in id_entries] != sorted(id_to_reference):
        fail("structure_tree", "IDTree IDs differ from the structure hierarchy")
    for identifier, reference in id_entries:
        if id_to_reference.get(identifier) != reference:
            fail("structure_tree", f"IDTree target for {identifier!r} changed")

    return StructureIndex(
        document_reference=document_reference,
        path_by_reference=path_by_reference,
        role_by_reference=role_by_reference,
        id_to_reference=id_to_reference,
        mcr_parents=mcr_parents,
        objr_records=objr_records,
        semantic_lines=semantic_lines,
    )


def validate_open_action(
    reader: PdfReader,
    root: DictionaryObject,
    structure_index: StructureIndex,
) -> tuple[str, Any]:
    action_value = dictionary_raw(root, "/OpenAction")
    action = require_dictionary(action_value, "catalog OpenAction")
    if key_set(action) != {"/S", "/D", "/SD"}:
        fail("catalog_open_action", "catalog OpenAction is not the declared benign GoTo action")
    require_name(dictionary_raw(action, "/S"), "/GoTo", "catalog OpenAction /S")
    destination = require_array(dictionary_raw(action, "/D"), 2, "catalog OpenAction /D")
    structure_destination = require_array(
        dictionary_raw(action, "/SD"), 2, "catalog OpenAction /SD"
    )
    require_name(array_raw(destination, 1), "/Fit", "catalog OpenAction /D[1]")
    require_name(array_raw(structure_destination, 1), "/Fit", "catalog OpenAction /SD[1]")
    if page_number_for_reference(reader, array_raw(destination, 0), "catalog OpenAction /D[0]") != 0:
        fail("catalog_open_action", "catalog OpenAction does not target the first page")
    if object_reference(array_raw(structure_destination, 0)) != structure_index.document_reference:
        fail("catalog_open_action", "catalog OpenAction does not target StructTreeRoot /K")
    return "catalog\t/UseOutlines\tOpenAction\t0\t/Fit\tDocument\t/Fit", action_value


def validate_named_destinations(
    reader: PdfReader,
    root: DictionaryObject,
) -> tuple[dict[str, XyzDestination], list[str]]:
    names_value = dictionary_raw(root, "/Names")
    if object_reference(names_value) is None:
        fail("name_tree", "catalog Names must be indirect")
    names = require_dictionary(names_value, "catalog Names")
    if key_set(names) != {"/Dests"}:
        fail("name_tree", "catalog Names must contain only the destination name tree")
    seen_nodes: set[tuple[int, int] | tuple[str, int]] = set()
    seen_wrappers: set[tuple[int, int] | tuple[str, int]] = set()

    def visit(
        node_value: Any,
        path: str,
        expected_leaf_count: int | None,
    ) -> list[tuple[str, XyzDestination]]:
        node = require_dictionary(node_value, path)
        identity: tuple[int, int] | tuple[str, int]
        reference = object_reference(node_value)
        identity = reference if reference is not None else ("direct", id(node))
        if identity in seen_nodes:
            fail("name_tree", f"{path}: destination name tree has a cycle or shared node")
        seen_nodes.add(identity)
        keys = key_set(node)
        if expected_leaf_count is not None:
            if keys != {"/Limits", "/Names"}:
                fail("name_tree", f"{path}: destination leaf changed shape")
            entries = dereference(dictionary_raw(node, "/Names"))
            if not isinstance(entries, ArrayObject):
                fail("name_tree", f"{path}: leaf /Names must be an array")
            if not entries:
                fail("name_tree", f"{path}: leaf /Names array is empty")
            if len(entries) % 2 != 0:
                fail(
                    "name_tree",
                    f"{path}: leaf /Names has an odd item count: {len(entries)}",
                )
            observed_leaf_count = len(entries) // 2
            if observed_leaf_count != expected_leaf_count:
                fail(
                    "name_tree",
                    f"{path}: canonical destination leaf pair count changed: "
                    f"expected {expected_leaf_count}, found {observed_leaf_count}",
                )
            result: list[tuple[str, XyzDestination]] = []
            for index in range(0, len(entries), 2):
                name = require_ascii_text(array_raw(entries, index), f"{path}/Names[{index}]")
                wrapper_value = array_raw(entries, index + 1)
                wrapper = require_dictionary(wrapper_value, f"{path}/{name}")
                wrapper_identity = object_reference(wrapper_value) or ("direct", id(wrapper))
                if wrapper_identity in seen_wrappers:
                    fail("name_tree", f"{path}/{name}: destination wrapper is shared")
                seen_wrappers.add(wrapper_identity)
                if key_set(wrapper) != {"/D"}:
                    fail("name_tree", f"{path}/{name}: destination wrapper changed shape")
                result.append(
                    (
                        name,
                        validate_xyz_array(
                            reader, dictionary_raw(wrapper, "/D"), f"{path}/{name}/D"
                        ),
                    )
                )
        else:
            if keys != {"/Kids", "/Limits"}:
                fail("name_tree", f"{path}: destination root changed shape")
            kids = dereference(dictionary_raw(node, "/Kids"))
            if not isinstance(kids, ArrayObject) or len(kids) != 3:
                fail("name_tree", f"{path}: expected exactly three destination leaves")
            result = []
            for index, leaf_count in enumerate((32, 32, 1)):
                child = array_raw(kids, index)
                if object_reference(child) is None:
                    fail("name_tree", f"{path}/Kids[{index}]: destination leaf is direct")
                result.extend(visit(child, f"{path}/Kids[{index}]", leaf_count))

        ordered_names = [name for name, _ in result]
        if ordered_names != sorted(ordered_names) or len(ordered_names) != len(set(ordered_names)):
            fail("name_tree", f"{path}: destination names are not strictly ordered and unique")
        limits = require_array(dictionary_raw(node, "/Limits"), 2, f"{path}/Limits")
        lower = require_ascii_text(array_raw(limits, 0), f"{path}/Limits[0]")
        upper = require_ascii_text(array_raw(limits, 1), f"{path}/Limits[1]")
        if [lower, upper] != [ordered_names[0], ordered_names[-1]]:
            fail("name_tree", f"{path}: Limits do not match the first and last name")
        return result

    destinations_value = dictionary_raw(names, "/Dests")
    if object_reference(destinations_value) is None:
        fail("name_tree", "destination name-tree root must be indirect")
    entries = visit(destinations_value, "catalog Names/Dests", None)
    destinations = dict(entries)
    if set(destinations) != set(EXPECTED_NAMED_DESTINATIONS):
        fail("name_tree", "named-destination names changed")
    for name, page in EXPECTED_NAMED_DESTINATIONS.items():
        if destinations[name].page != page:
            fail("name_tree", f"named destination {name!r} changed page")
    lines = [f"named\t{name}\t{destinations[name].payload()}" for name in sorted(destinations)]
    return destinations, lines


def validate_internal_goto_action(
    action_value: Any,
    named_destinations: dict[str, XyzDestination],
    structure_index: StructureIndex,
    path: str,
) -> tuple[str, str]:
    action = require_dictionary(action_value, path)
    if key_set(action) != {"/S", "/D", "/SD"}:
        fail("annotation_action", f"{path}: internal GoTo action changed shape")
    require_name(dictionary_raw(action, "/S"), "/GoTo", f"{path} /S")
    target = require_ascii_text(dictionary_raw(action, "/D"), f"{path} /D")
    if target not in named_destinations:
        fail("annotation_action", f"{path}: internal GoTo destination is unresolved")
    structure_destination = require_array(
        dictionary_raw(action, "/SD"), 5, f"{path} /SD"
    )
    structure_reference = object_reference(array_raw(structure_destination, 0))
    if structure_reference not in structure_index.path_by_reference:
        fail("annotation_action", f"{path}: structure destination is outside StructTreeRoot /K")
    require_name(array_raw(structure_destination, 1), "/XYZ", f"{path} /SD[1]")
    _, left_token = canonical_number(array_raw(structure_destination, 2), f"{path} /SD[2]")
    _, top_token = canonical_number(array_raw(structure_destination, 3), f"{path} /SD[3]")
    zoom_token = require_null(array_raw(structure_destination, 4), f"{path} /SD[4]")
    named = named_destinations[target]
    if (left_token, top_token, zoom_token) != (named.left, named.top, named.zoom):
        fail("annotation_action", f"{path}: structure and named destination payloads differ")
    structure_path = structure_index.path_by_reference[structure_reference]
    return target, f"{named.payload()}\tstructure={structure_path}"


def validate_outlines(
    root: DictionaryObject,
    named_destinations: dict[str, XyzDestination],
    structure_index: StructureIndex,
    action_owners: list[ActionOwner],
) -> tuple[list[tuple[int, int, str, str]], list[str]]:
    outlines_value = dictionary_raw(root, "/Outlines")
    outlines = require_dictionary(outlines_value, "catalog Outlines")
    if key_set(outlines) != {"/Count", "/First", "/Last", "/Type"}:
        fail("outline", "catalog Outlines dictionary changed shape")
    require_name(outlines.get("/Type"), "/Outlines", "catalog Outlines /Type")
    seen_nodes: set[tuple[int, int]] = set()
    observed: list[tuple[int, int, str, str]] = []
    lines: list[str] = []

    def visit_chain(first: Any, last: Any, parent: Any, depth: int, path: str) -> int:
        current = first
        previous_reference: tuple[int, int] | None = None
        final_reference: tuple[int, int] | None = None
        count = 0
        while current is not None:
            current_reference = object_reference(current)
            if current_reference is None or current_reference in seen_nodes:
                fail("outline", f"{path}: outline node is direct, shared, or cyclic")
            seen_nodes.add(current_reference)
            node = require_dictionary(current, f"{path}[{count}]")
            next_value = dictionary_raw(node, "/Next")
            child_first = dictionary_raw(node, "/First")
            child_last = dictionary_raw(node, "/Last")
            child_count_value = dictionary_raw(node, "/Count")
            has_children = any(key in node for key in ("/First", "/Last", "/Count"))
            if has_children and not all(key in node for key in ("/First", "/Last", "/Count")):
                fail("outline", f"{path}[{count}]: incomplete child topology")
            expected_keys = {"/A", "/Parent", "/Title"}
            if previous_reference is not None:
                expected_keys.add("/Prev")
            if next_value is not None:
                expected_keys.add("/Next")
            if has_children:
                expected_keys.update({"/Count", "/First", "/Last"})
            if key_set(node) != expected_keys:
                fail("outline", f"{path}[{count}]: outline node changed shape")
            if object_reference(dictionary_raw(node, "/Parent")) != object_reference(parent):
                fail("outline", f"{path}[{count}]: parent link changed")
            if previous_reference is not None and object_reference(
                dictionary_raw(node, "/Prev")
            ) != previous_reference:
                fail("outline", f"{path}[{count}]: previous link changed")
            title = require_utf16be_text(
                dictionary_raw(node, "/Title"), f"{path}[{count}]/Title"
            )
            action_value = dictionary_raw(node, "/A")
            target, destination_payload = validate_internal_goto_action(
                action_value,
                named_destinations,
                structure_index,
                f"{path}[{count}]/A",
            )
            action_owners.append(
                ActionOwner(f"{path}[{count}]/A", node, "/A", action_value, "/GoTo")
            )
            page = named_destinations[target].page
            observed.append((depth, page, title, target))
            line_index = len(lines)
            lines.append("")
            child_count = 0
            if has_children:
                child_count = visit_chain(
                    child_first,
                    child_last,
                    current,
                    depth + 1,
                    f"{path}[{count}]/Kids",
                )
                if require_integer(
                    child_count_value, None, f"{path}[{count}]/Count"
                ) != -child_count:
                    fail("outline", f"{path}[{count}]: collapsed child count changed")
            lines[line_index] = (
                f"outline\t{depth}\t{page}\t{title}\t{target}\t{destination_payload}"
                f"\tchildren={child_count}"
            )
            count += 1
            final_reference = current_reference
            previous_reference = current_reference
            current = next_value
        if final_reference != object_reference(last):
            fail("outline", f"{path}: Last does not identify the final sibling")
        return count

    top_count = visit_chain(
        dictionary_raw(outlines, "/First"),
        dictionary_raw(outlines, "/Last"),
        outlines_value,
        0,
        "catalog Outlines/Items",
    )
    if require_integer(
        dictionary_raw(outlines, "/Count"), None, "catalog Outlines /Count"
    ) != top_count:
        fail("outline", "catalog Outlines count changed")
    if observed != EXPECTED_OUTLINE:
        fail("outline", "outline titles, hierarchy, targets, or destinations changed")
    return observed, lines


def validate_file_specification(value: Any, path: str) -> str:
    specification = require_dictionary(value, f"{path} /F")
    expected_keys = {"/Type", "/AFRelationship", "/Subtype", "/F", "/UF"}
    if key_set(specification) != expected_keys:
        fail("file_specification", f"{path}: remote-GoTo file specification changed shape")
    require_name(dictionary_raw(specification, "/Type"), "/Filespec", f"{path} /F /Type")
    require_name(
        dictionary_raw(specification, "/AFRelationship"),
        "/Unspecified",
        f"{path} /F /AFRelationship",
    )
    require_name(
        dictionary_raw(specification, "/Subtype"),
        "/application/pdf",
        f"{path} /F /Subtype",
    )
    target = require_utf16be_text(dictionary_raw(specification, "/UF"), f"{path} /F /UF")
    if target != require_ascii_text(dictionary_raw(specification, "/F"), f"{path} /F /F"):
        fail("file_specification", f"{path}: remote-GoTo F and UF targets differ")
    validate_target(target, path)
    return target


def validate_target(target: str, path: str) -> None:
    if not target or any(character in target for character in ("\n", "\r", "\x00")):
        fail("link_target", f"{path}: malformed link target")


def validate_link_action(
    action_value: Any,
    named_destinations: dict[str, XyzDestination],
    structure_index: StructureIndex,
    path: str,
) -> tuple[str, str, str]:
    action = require_dictionary(action_value, f"{path} /A")
    kind = require_any_name(dictionary_raw(action, "/S"), f"{path} /A /S")
    if kind == "/GoTo":
        target, payload = validate_internal_goto_action(
            action_value, named_destinations, structure_index, f"{path} /A"
        )
        return kind, target, payload
    if kind == "/URI":
        if key_set(action) != {"/Type", "/S", "/URI"}:
            fail("annotation_action", f"{path}: URI action changed shape")
        require_name(dictionary_raw(action, "/Type"), "/Action", f"{path} /A /Type")
        target = require_ascii_text(dictionary_raw(action, "/URI"), f"{path} /A /URI")
        validate_target(target, path)
        return kind, target, f"uri={target}"
    if kind == "/GoToR":
        if key_set(action) != {"/Type", "/S", "/F", "/D"}:
            fail("annotation_action", f"{path}: remote GoTo action changed shape")
        require_name(dictionary_raw(action, "/Type"), "/Action", f"{path} /A /Type")
        destination = require_array(dictionary_raw(action, "/D"), 2, f"{path} /A /D")
        require_integer(array_raw(destination, 0), 0, f"{path} /A /D[0]")
        require_name(array_raw(destination, 1), "/Fit", f"{path} /A /D[1]")
        target = validate_file_specification(dictionary_raw(action, "/F"), f"{path} /A")
        return kind, target, f"file={target}\tpage=0\t/Fit"
    fail("annotation_action", f"{path}: unsupported link action {kind or 'missing'}")
    raise RuntimeError("unreachable")


def validate_page_tree(reader: PdfReader, root: DictionaryObject) -> None:
    pages_value = dictionary_raw(root, "/Pages")
    pages_reference = object_reference(pages_value)
    if pages_reference is None:
        fail("page_tree", "catalog Pages must be indirect")
    pages = require_dictionary(pages_value, "catalog Pages")
    if key_set(pages) != {"/Type", "/Count", "/Kids"}:
        fail("page_tree", "catalog Pages root changed shape")
    require_name(dictionary_raw(pages, "/Type"), "/Pages", "catalog Pages /Type")
    require_integer(dictionary_raw(pages, "/Count"), 23, "catalog Pages /Count")
    kids = require_array(dictionary_raw(pages, "/Kids"), 3, "catalog Pages /Kids")
    expected_group_counts = (10, 10, 3)
    expected_page = 0
    seen_groups: set[tuple[int, int]] = set()
    seen_pages: set[tuple[int, int]] = set()
    for group_index, expected_count in enumerate(expected_group_counts):
        group_value = array_raw(kids, group_index)
        group_reference = object_reference(group_value)
        if group_reference is None or group_reference in seen_groups:
            fail("page_tree", "page group is direct, shared, or cyclic")
        seen_groups.add(group_reference)
        group = require_dictionary(group_value, f"catalog Pages/Kids[{group_index}]")
        if key_set(group) != {"/Type", "/Parent", "/Count", "/Kids"}:
            fail("page_tree", f"page group {group_index} changed shape")
        require_name(dictionary_raw(group, "/Type"), "/Pages", f"page group {group_index} /Type")
        if object_reference(dictionary_raw(group, "/Parent")) != pages_reference:
            fail("page_tree", f"page group {group_index} parent changed")
        require_integer(
            dictionary_raw(group, "/Count"), expected_count, f"page group {group_index} /Count"
        )
        leaves = require_array(
            dictionary_raw(group, "/Kids"), expected_count, f"page group {group_index} /Kids"
        )
        for leaf_index in range(len(leaves)):
            leaf_value = array_raw(leaves, leaf_index)
            leaf_reference = object_reference(leaf_value)
            if leaf_reference is None or leaf_reference in seen_pages:
                fail("page_tree", "page leaf is direct or repeated")
            seen_pages.add(leaf_reference)
            if leaf_reference != object_reference(reader.pages[expected_page]):
                fail("page_tree", f"page group {group_index} leaf order changed")
            leaf = require_dictionary(leaf_value, f"page {expected_page + 1}")
            if object_reference(dictionary_raw(leaf, "/Parent")) != group_reference:
                fail("page_tree", f"page {expected_page + 1} parent changed")
            expected_page += 1
    if expected_page != len(reader.pages):
        fail("page_tree", "page tree does not cover every page exactly once")


def resource_closure_payload(
    value: Any,
    path: str,
    *,
    dictionary_key_aliases: dict[int, dict[str, str]] | None = None,
) -> bytes:
    """Encode one typed resource closure, including decoded bytes and reference topology.

    ``dictionary_key_aliases`` is used only by the separate, source-profiled
    cross-toolchain font-resource comparator.  The strict single-PDF policy
    never supplies aliases.  Returning the complete typed payload lets that
    pair comparator decide equality from bytes; SHA-256 remains a compact
    manifest/report representation, not its equality oracle.
    """

    closure = bytearray()
    seen_references: dict[tuple[int, int], int] = {}
    active_direct: set[int] = set()
    aliases_by_identity = dictionary_key_aliases or {}

    def token(kind: str, payload: bytes = b"") -> None:
        encoded_kind = kind.encode("ascii")
        encoded_length = str(len(payload)).encode("ascii")
        closure.extend(encoded_kind)
        closure.extend(b":")
        closure.extend(encoded_length)
        closure.extend(b":")
        closure.extend(payload)
        closure.extend(b";")

    def encode(item: Any, item_path: str, follow_reference: bool = True) -> None:
        if follow_reference and isinstance(item, IndirectObject):
            reference = (item.idnum, item.generation)
            if reference in seen_references:
                token("seen-ref", str(seen_references[reference]).encode("ascii"))
                return
            ordinal = len(seen_references)
            seen_references[reference] = ordinal
            token("new-ref", str(ordinal).encode("ascii"))
            try:
                encode(item.get_object(), item_path, False)
            except Exception as error:
                fail("resource_graph", f"{item_path}: resource reference cannot be resolved: {error}")
            return
        if isinstance(item, NameObject):
            token("name", require_any_name(item, item_path).encode("utf-8"))
            return
        if isinstance(item, TextStringObject):
            token("text", require_text(item, item_path).encode("utf-8"))
            return
        if isinstance(item, ByteStringObject):
            token("bytes", bytes(item))
            return
        if isinstance(item, BooleanObject):
            token("bool", b"true" if item.value else b"false")
            return
        if isinstance(item, NullObject):
            token("null")
            return
        if isinstance(item, FloatObject):
            _, number = canonical_number(item, item_path)
            token("real", number.encode("ascii"))
            return
        if isinstance(item, NumberObject):
            _, number = canonical_number(item, item_path)
            token("integer", number.encode("ascii"))
            return
        if isinstance(item, ArrayObject):
            identity = id(item)
            if identity in active_direct:
                fail("resource_graph", f"{item_path}: direct resource-array cycle")
            active_direct.add(identity)
            token("array", str(len(item)).encode("ascii"))
            for index in range(len(item)):
                encode(array_raw(item, index), f"{item_path}[{index}]")
            active_direct.remove(identity)
            token("array-end")
            return
        if isinstance(item, DictionaryObject):
            identity = id(item)
            if identity in active_direct:
                fail("resource_graph", f"{item_path}: direct resource-dictionary cycle")
            active_direct.add(identity)
            token("stream" if isinstance(item, StreamObject) else "dictionary")
            key_names = [require_any_name(key, f"{item_path} key") for key in item.keys()]
            key_aliases = aliases_by_identity.get(identity, {})
            if set(key_aliases) - set(key_names):
                fail("resource_graph", f"{item_path}: resource-key alias names are absent")
            effective_names = [key_aliases.get(name, name) for name in key_names]
            if len(set(effective_names)) != len(effective_names):
                fail("resource_graph", f"{item_path}: resource-key aliases are not injective")
            for key_name in sorted(key_names, key=lambda name: key_aliases.get(name, name)):
                effective_name = key_aliases.get(key_name, key_name)
                token("key", effective_name.encode("utf-8"))
                encode(dictionary_raw(item, key_name), f"{item_path}/{key_name.lstrip('/')}")
            if isinstance(item, StreamObject):
                try:
                    data = item.get_data()
                except Exception as error:
                    fail("resource_graph", f"{item_path}: resource stream cannot be decoded: {error}")
                if not isinstance(data, bytes):
                    fail("resource_graph", f"{item_path}: decoded resource stream is not bytes")
                token("decoded-stream", data)
            active_direct.remove(identity)
            token("dictionary-end")
            return
        fail("resource_graph", f"{item_path}: unsupported PDF object {type(item).__name__}")

    encode(value, path)
    return bytes(closure)


def resource_closure_sha256(
    value: Any,
    path: str,
    *,
    dictionary_key_aliases: dict[int, dict[str, str]] | None = None,
) -> str:
    """Hash the exact typed resource-closure payload used by the strict manifest."""

    payload = resource_closure_payload(
        value,
        path,
        dictionary_key_aliases=dictionary_key_aliases,
    )
    return hashlib.sha256(payload).hexdigest()


def validate_marked_content(
    reader: PdfReader,
    content_value: Any,
    page: int,
    structure_index: StructureIndex,
) -> str:
    """Bind BMC/BDC/EMC nesting and each page MCID/tag to the declared structure hierarchy."""

    try:
        operations = ContentStream(content_value, reader).operations
    except Exception as error:
        fail("marked_content", f"page {page + 1}: content operations cannot be parsed: {error}")
    stack: list[str] = []
    observed_mcids: list[int] = []
    tag_counts: Counter[str] = Counter()
    artifact_count = 0
    for operation_index, (operands, operator) in enumerate(operations):
        path = f"page {page + 1} operation {operation_index}"
        if operator == b"BMC":
            if len(operands) != 1:
                fail("marked_content", f"{path}: BMC operand count changed")
            require_name(operands[0], "/Artifact", f"{path} BMC tag")
            stack.append("/Artifact")
            artifact_count += 1
        elif operator == b"BDC":
            if len(operands) != 2:
                fail("marked_content", f"{path}: BDC operand count changed")
            tag = require_any_name(operands[0], f"{path} BDC tag")
            properties = require_dictionary(operands[1], f"{path} BDC properties")
            if key_set(properties) != {"/MCID"}:
                fail("marked_content", f"{path}: BDC properties changed shape")
            mcid = require_integer(
                dictionary_raw(properties, "/MCID"), None, f"{path} BDC /MCID"
            )
            parent_reference = structure_index.mcr_parents.get((page, mcid))
            if parent_reference is None:
                fail("marked_content", f"{path}: MCID is absent from the structure hierarchy")
            if structure_index.role_by_reference[parent_reference] != tag:
                fail("marked_content", f"{path}: BDC tag and structure role differ")
            observed_mcids.append(mcid)
            tag_counts[tag] += 1
            stack.append(tag)
        elif operator == b"EMC":
            if operands or not stack:
                fail("marked_content", f"{path}: unmatched or malformed EMC")
            stack.pop()
    if stack:
        fail("marked_content", f"page {page + 1}: marked-content scopes are unclosed")
    expected_mcids = sorted(
        mcid for candidate_page, mcid in structure_index.mcr_parents if candidate_page == page
    )
    if observed_mcids != expected_mcids or observed_mcids != list(range(len(observed_mcids))):
        fail("marked_content", f"page {page + 1}: MCIDs are not exact, unique, and sequential")
    return (
        f"marked-content\tpage={page}\tartifacts={artifact_count}\tmcids={len(observed_mcids)}"
        f"\ttext={tag_counts['/text']}\tlinks={tag_counts['/Link']}"
    )


def validate_pages_and_links(
    reader: PdfReader,
    named_destinations: dict[str, XyzDestination],
    structure_index: StructureIndex,
    action_owners: list[ActionOwner],
) -> tuple[
    set[str],
    list[str],
    Counter[str],
    dict[int, int],
    dict[tuple[int, int], tuple[int, int, int | None]],
]:
    if len(reader.pages) != 23:
        fail("page_count", f"expected 23 pages, observed {len(reader.pages)}")
    targets: set[str] = set()
    navigation: list[str] = []
    counts: Counter[str] = Counter()
    total_links = 0
    page_struct_parents: dict[int, int] = {}
    annotation_locations: dict[tuple[int, int], tuple[int, int, int | None]] = {}
    seen_content_streams: set[tuple[int, int]] = set()
    seen_resource_roots: set[tuple[int, int]] = set()
    expected_page_base = {
        "/Contents",
        "/MediaBox",
        "/Parent",
        "/Resources",
        "/StructParents",
        "/Tabs",
        "/Type",
    }
    expected_annotation_base = {"/A", "/Border", "/C", "/H", "/Rect", "/Subtype", "/Type"}

    for page_number, page in enumerate(reader.pages, 1):
        allowed_page_keys = (
            expected_page_base
            | ({"/Annots"} if "/Annots" in page else set())
            | ({"/Rotate"} if page_number == 7 else set())
        )
        if key_set(page) != allowed_page_keys:
            fail("page_keys", f"page {page_number}: page dictionary keys changed")
        require_name(dictionary_raw(page, "/Type"), "/Page", f"page {page_number} /Type")
        require_name(dictionary_raw(page, "/Tabs"), "/S", f"page {page_number} /Tabs")
        rotation = "none"
        if page_number == 7:
            require_integer(dictionary_raw(page, "/Rotate"), 90, "page 7 /Rotate")
            rotation = "90"
        struct_parent = require_integer(
            dictionary_raw(page, "/StructParents"), page_number - 1, f"page {page_number} /StructParents"
        )
        if struct_parent in page_struct_parents:
            fail("structure_tree", f"page {page_number}: duplicate StructParents key")
        page_struct_parents[struct_parent] = page_number - 1
        box = require_array(
            dictionary_raw(page, "/MediaBox"), 4, f"page {page_number} /MediaBox"
        )
        values_and_tokens = [
            canonical_number(array_raw(box, index), f"page {page_number} /MediaBox[{index}]")
            for index in range(4)
        ]
        values = [item[0] for item in values_and_tokens]
        if values != [0.0, 0.0, 595.276, 841.89]:
            fail("page_geometry", f"page {page_number}: MediaBox is not exact A4")
        geometry_tokens = [item[1] for item in values_and_tokens]
        navigation.append(
            f"page\t{page_number}\tStructParents={struct_parent}\t"
            f"MediaBox={','.join(geometry_tokens)}\tRotate={rotation}"
        )
        content_value = dictionary_raw(page, "/Contents")
        content_reference = object_reference(content_value)
        if content_reference is None or content_reference in seen_content_streams:
            fail("structure_tree", f"page {page_number}: content stream is direct or shared")
        seen_content_streams.add(content_reference)
        content = dereference(content_value)
        if not isinstance(content, EncodedStreamObject) or key_set(content) != {"/Filter"}:
            fail("structure_tree", f"page {page_number}: content stream shape changed")
        require_name(
            dictionary_raw(content, "/Filter"),
            "/FlateDecode",
            f"page {page_number} content /Filter",
        )
        decoded_content = content.get_data()
        if not isinstance(decoded_content, bytes) or not decoded_content:
            fail("structure_tree", f"page {page_number}: decoded content is empty or invalid")
        structure_index.semantic_lines.append(
            f"page-content\tpage={page_number - 1}\tbytes={len(decoded_content)}\t"
            f"sha256={hashlib.sha256(decoded_content).hexdigest()}"
        )
        structure_index.semantic_lines.append(
            validate_marked_content(
                reader,
                content_value,
                page_number - 1,
                structure_index,
            )
        )
        resources_value = dictionary_raw(page, "/Resources")
        resources_reference = object_reference(resources_value)
        if resources_reference is None or resources_reference in seen_resource_roots:
            fail("resource_graph", f"page {page_number}: resource root is direct or shared")
        seen_resource_roots.add(resources_reference)
        structure_index.semantic_lines.append(
            f"page-resources\tpage={page_number - 1}\t"
            f"sha256={resource_closure_sha256(resources_value, f'page {page_number} Resources')}"
        )

        annotations_value = dictionary_raw(page, "/Annots")
        annotations = dereference(annotations_value) if annotations_value is not None else ArrayObject()
        if not isinstance(annotations, ArrayObject):
            fail("annotation_shape", f"page {page_number}: Annots is not an array")
        for ordinal in range(1, len(annotations) + 1):
            reference = array_raw(annotations, ordinal - 1)
            total_links += 1
            annotation_reference = object_reference(reference)
            if annotation_reference is None or annotation_reference in annotation_locations:
                fail("annotation_shape", f"page {page_number} annotation {ordinal}: direct or repeated")
            annotation = require_dictionary(reference, f"page {page_number} annotation {ordinal}")
            path = f"page {page_number} annotation {ordinal}"
            keys = key_set(annotation)
            if keys not in (expected_annotation_base, expected_annotation_base | {"/Contents", "/StructParent"}):
                fail("annotation_keys", f"{path}: link annotation keys changed")
            try:
                require_name(dictionary_raw(annotation, "/Subtype"), "/Link", f"{path} /Subtype")
                require_name(dictionary_raw(annotation, "/Type"), "/Annot", f"{path} /Type")
            except PdfStructureError as error:
                if error.code == "typed_name":
                    fail("annotation_subtype", f"{path}: only typed Link annotations are permitted")
                raise
            require_name(dictionary_raw(annotation, "/H"), "/I", f"{path} /H")
            border = require_array(dictionary_raw(annotation, "/Border"), 3, f"{path} /Border")
            border_values_and_tokens = [
                canonical_number(array_raw(border, index), f"{path} /Border[{index}]")
                for index in range(3)
            ]
            if [item[0] for item in border_values_and_tokens] != [0.0, 0.0, 0.0]:
                fail("annotation_shape", f"{path}: visible annotation border is not permitted")
            color = require_array(dictionary_raw(annotation, "/C"), 3, f"{path} /C")
            color_values_and_tokens = [
                canonical_number(array_raw(color, index), f"{path} /C[{index}]")
                for index in range(3)
            ]
            if any(not 0.0 <= item[0] <= 1.0 for item in color_values_and_tokens):
                fail("annotation_shape", f"{path}: annotation color is invalid")
            rectangle = require_array(dictionary_raw(annotation, "/Rect"), 4, f"{path} /Rect")
            coordinate_values_and_tokens = [
                canonical_number(array_raw(rectangle, index), f"{path} /Rect[{index}]")
                for index in range(4)
            ]
            coordinates = [item[0] for item in coordinate_values_and_tokens]
            left, bottom, right, top = coordinates
            width, height = right - left, top - bottom
            if (
                left < -0.01
                or bottom < -0.01
                or right > 595.286
                or top > 841.90
                or width <= 0.0
                or height <= 0.0
                or width > 400.0
                or height > 20.0
            ):
                fail("annotation_rectangle", f"{path}: annotation rectangle is invalid or oversized")
            action_value = dictionary_raw(annotation, "/A")
            kind, target, action_payload = validate_link_action(
                action_value, named_destinations, structure_index, path
            )
            action_owners.append(ActionOwner(f"{path} /A", annotation, "/A", action_value, kind))
            contents = dictionary_raw(annotation, "/Contents")
            if kind == "/GoTo" and require_ascii_text(contents, f"{path} /Contents") != "ref":
                fail("annotation_shape", f"{path}: internal-link contents changed")
            if kind == "/URI" and require_utf16be_text(contents, f"{path} /Contents") != target:
                fail("annotation_shape", f"{path}: URI contents and target differ")
            if kind == "/GoToR" and contents is not None:
                fail("annotation_shape", f"{path}: remote link gained unexpected contents")
            annotation_struct_parent: int | None = None
            if "/StructParent" in annotation:
                annotation_struct_parent = require_integer(
                    dictionary_raw(annotation, "/StructParent"), None, f"{path} /StructParent"
                )
                if annotation_struct_parent < 0:
                    fail("structure_tree", f"{path}: negative StructParent")
            if (contents is None) != (annotation_struct_parent is None):
                fail("annotation_shape", f"{path}: Contents and StructParent presence diverged")
            annotation_locations[annotation_reference] = (
                page_number - 1,
                ordinal,
                annotation_struct_parent,
            )
            counts[kind] += 1
            if kind != "/GoTo":
                targets.add(target)
            rectangle_text = ",".join(item[1] for item in coordinate_values_and_tokens)
            color_text = ",".join(item[1] for item in color_values_and_tokens)
            border_text = ",".join(item[1] for item in border_values_and_tokens)
            struct_parent_text = (
                "none" if annotation_struct_parent is None else str(annotation_struct_parent)
            )
            navigation.append(
                f"link\t{page_number}\t{ordinal}\t{kind}\t{target}\tRect={rectangle_text}"
                f"\tBorder={border_text}\tColor={color_text}\tStructParent={struct_parent_text}"
                f"\t{action_payload}"
            )

    if total_links != 107 or counts != EXPECTED_LINK_COUNTS:
        fail("link_count", f"link action counts changed: {dict(counts)}")
    if len(targets) != 57:
        fail("link_count", f"expected 57 distinct external HTTPS targets, observed {len(targets)}")
    return targets, navigation, counts, page_struct_parents, annotation_locations


def validate_page_labels(root: DictionaryObject) -> list[str]:
    labels = require_dictionary(dictionary_raw(root, "/PageLabels"), "catalog PageLabels")
    if key_set(labels) != {"/Nums"}:
        fail("page_labels", "catalog PageLabels changed shape")
    numbers = require_array(dictionary_raw(labels, "/Nums"), 4, "catalog PageLabels /Nums")
    lines: list[str] = []
    for entry, expected_start in enumerate((0, 1)):
        start = require_integer(
            array_raw(numbers, 2 * entry), expected_start, f"PageLabels /Nums[{2 * entry}]"
        )
        specification = require_dictionary(
            array_raw(numbers, 2 * entry + 1), f"PageLabels /Nums[{2 * entry + 1}]"
        )
        if key_set(specification) != {"/S"}:
            fail("page_labels", "page-label specification changed shape")
        require_name(
            dictionary_raw(specification, "/S"),
            "/D",
            f"PageLabels /Nums[{2 * entry + 1}] /S",
        )
        lines.append(f"page-label\tstart={start}\tstyle=/D")
    return lines


def validate_parent_tree(
    root: DictionaryObject,
    structure_index: StructureIndex,
    page_struct_parents: dict[int, int],
    annotation_locations: dict[tuple[int, int], tuple[int, int, int | None]],
    *,
    enforce_manifest_digest: bool = True,
) -> tuple[str, str]:
    structure = require_dictionary(dictionary_raw(root, "/StructTreeRoot"), "StructTreeRoot")
    parent_tree_value = dictionary_raw(structure, "/ParentTree")
    if object_reference(parent_tree_value) is None:
        fail("structure_tree", "StructTreeRoot /ParentTree must be indirect")
    parent_tree = require_dictionary(parent_tree_value, "StructTreeRoot /ParentTree")
    if key_set(parent_tree) != {"/Nums"}:
        fail("structure_tree", "ParentTree changed shape")
    numbers = dereference(dictionary_raw(parent_tree, "/Nums"))
    if not isinstance(numbers, ArrayObject) or len(numbers) % 2:
        fail("structure_tree", "ParentTree /Nums is not an even array")
    mappings: dict[int, Any] = {}
    for index in range(0, len(numbers), 2):
        key = require_integer(array_raw(numbers, index), None, f"ParentTree /Nums[{index}]")
        if key < 0 or key in mappings:
            fail("structure_tree", "ParentTree keys are negative or duplicated")
        mappings[key] = array_raw(numbers, index + 1)
    if list(mappings) != sorted(mappings):
        fail("structure_tree", "ParentTree keys are not strictly ordered")

    annotations_by_parent: dict[int, list[tuple[tuple[int, int], int, int]]] = {}
    for reference, (page, ordinal, struct_parent) in annotation_locations.items():
        if struct_parent is not None:
            annotations_by_parent.setdefault(struct_parent, []).append((reference, page, ordinal))
    expected_keys = set(page_struct_parents) | set(annotations_by_parent)
    if set(mappings) != expected_keys or len(mappings) != 121:
        fail("structure_tree", "ParentTree keys differ from page and annotation ownership")

    consumed_mcr: set[tuple[int, int]] = set()
    for parent_key, page in sorted(page_struct_parents.items()):
        parents = dereference(mappings[parent_key])
        if not isinstance(parents, ArrayObject) or not parents:
            fail("structure_tree", f"ParentTree page key {parent_key}: expected a nonempty array")
        expected_mcids = [mcid for candidate_page, mcid in structure_index.mcr_parents if candidate_page == page]
        if not expected_mcids or len(parents) != max(expected_mcids) + 1:
            fail("structure_tree", f"ParentTree page key {parent_key}: MCID extent changed")
        parent_paths: list[str] = []
        for mcid in range(len(parents)):
            value = array_raw(parents, mcid)
            expected_parent = structure_index.mcr_parents.get((page, mcid))
            if expected_parent is None:
                require_null(value, f"ParentTree page key {parent_key} MCID {mcid}")
                parent_paths.append("null")
                continue
            if object_reference(value) != expected_parent:
                fail("structure_tree", f"ParentTree page key {parent_key} MCID {mcid} changed")
            consumed_mcr.add((page, mcid))
            parent_paths.append(structure_index.path_by_reference[expected_parent])
        parent_payload = "\n".join(parent_paths).encode("utf-8")
        structure_index.semantic_lines.append(
            f"parent-page\tkey={parent_key}\tpage={page}\tentries={len(parents)}\t"
            f"sha256={hashlib.sha256(parent_payload).hexdigest()}"
        )
    if consumed_mcr != set(structure_index.mcr_parents):
        fail("structure_tree", "ParentTree does not account for every marked-content record")

    objr_by_parent_key: dict[int, tuple[int, int]] = {}
    for object_reference_value, (page, parent_reference, objr_path) in structure_index.objr_records.items():
        location = annotation_locations.get(object_reference_value)
        if location is None:
            fail("structure_tree", f"{objr_path}: OBJR does not target a declared link annotation")
        annotation_page, ordinal, parent_key = location
        if parent_key is None or annotation_page != page:
            fail("structure_tree", f"{objr_path}: OBJR page or StructParent changed")
        if parent_key in objr_by_parent_key:
            fail("structure_tree", f"{objr_path}: multiple OBJR records use one StructParent")
        objr_by_parent_key[parent_key] = parent_reference
        structure_index.semantic_lines.append(
            f"objr\t{objr_path}\tpage={page}\tannotation={ordinal}\t"
            f"parent={structure_index.path_by_reference[parent_reference]}"
        )
    if set(objr_by_parent_key) != set(annotations_by_parent):
        fail("structure_tree", "OBJR coverage differs from the distinct annotation StructParents")

    for parent_key, locations in sorted(annotations_by_parent.items()):
        parent_reference = object_reference(mappings[parent_key])
        if parent_reference is None or parent_reference not in structure_index.path_by_reference:
            fail("structure_tree", f"ParentTree annotation key {parent_key} is not a structure element")
        if objr_by_parent_key[parent_key] != parent_reference:
            fail("structure_tree", f"ParentTree annotation key {parent_key} disagrees with OBJR")
        cluster = ",".join(f"{page + 1}:{ordinal}" for _, page, ordinal in locations)
        structure_index.semantic_lines.append(
            f"parent-link\tkey={parent_key}\tparent="
            f"{structure_index.path_by_reference[parent_reference]}\tannotations={cluster}"
        )

    payload = "".join(f"{line}\n" for line in structure_index.semantic_lines).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if enforce_manifest_digest and digest != EXPECTED_STRUCTURE_SHA256:
        fail("structure_digest", f"tagged-structure manifest changed: {digest}")
    return (
        (
            f"structure\telements={len(structure_index.path_by_reference)}\t"
            f"mcr={len(structure_index.mcr_parents)}\tobjr={len(structure_index.objr_records)}\t"
            f"sha256={digest}"
        ),
        digest,
    )


def validate_action_owners(
    owners: list[ActionOwner],
) -> dict[
    tuple[tuple[str, int, int] | tuple[str, int], str],
    tuple[tuple[str, int, int] | tuple[str, int], str, str],
]:
    if len(owners) != 126:
        fail("action_count", f"expected 126 explicit action owners, observed {len(owners)}")
    edges: dict[
        tuple[tuple[str, int, int] | tuple[str, int], str],
        tuple[tuple[str, int, int] | tuple[str, int], str, str],
    ] = {}
    action_identities: set[tuple[str, int, int] | tuple[str, int]] = set()
    counts: Counter[str] = Counter()
    for owner in owners:
        edge = (object_identity(owner.container), owner.key)
        action_identity = object_identity(owner.action)
        if edge in edges:
            fail("action_owner", f"duplicate action owner edge at {owner.path}")
        if action_identity in action_identities:
            fail("action_alias", f"action dictionary is shared at {owner.path}")
        edges[edge] = (action_identity, owner.kind, owner.path)
        action_identities.add(action_identity)
        counts[owner.kind] += 1
    if counts != EXPECTED_ACTION_COUNTS:
        fail("action_count", f"explicit action-owner counts changed: {dict(counts)}")
    return edges


def scan_reachable_graph(
    root: DictionaryObject,
    allowed_edges: dict[
        tuple[tuple[str, int, int] | tuple[str, int], str],
        tuple[tuple[str, int, int] | tuple[str, int], str, str],
    ],
) -> Counter[str]:
    seen_indirect: set[tuple[int, int]] = set()
    seen_direct: set[int] = set()
    seen_edges: set[tuple[tuple[str, int, int] | tuple[str, int], str]] = set()
    actions: Counter[str] = Counter()

    def validate_action(value: DictionaryObject, path: str, expected_kind: str) -> None:
        kind = require_any_name(dictionary_raw(value, "/S"), f"{path} /S")
        if kind != expected_kind or kind not in DECLARED_ACTIONS:
            fail("active_content", f"{path}: action kind differs from its validated owner")
        expected_keys = {
            "/GoTo": {"/S", "/D", "/SD"},
            "/URI": {"/Type", "/S", "/URI"},
            "/GoToR": {"/Type", "/S", "/F", "/D"},
        }[kind]
        if key_set(value) != expected_keys:
            fail("active_content", f"{path}: declared {kind} action changed shape")
        if kind in {"/URI", "/GoToR"}:
            require_name(dictionary_raw(value, "/Type"), "/Action", f"{path} /Type")

    def visit(
        value: Any,
        path: str,
        expected_action: tuple[
            tuple[str, int, int] | tuple[str, int], str, str
        ]
        | None = None,
    ) -> None:
        already_seen = False
        reference = object_reference(value)
        if reference is not None:
            identity: tuple[str, int, int] | tuple[str, int] = (
                "indirect",
                reference[0],
                reference[1],
            )
            already_seen = reference in seen_indirect
            if isinstance(value, IndirectObject):
                try:
                    value = value.get_object()
                except Exception as error:
                    fail("object_graph", f"{path}: indirect object cannot be resolved: {error}")
            if not already_seen:
                seen_indirect.add(reference)
        elif isinstance(value, (DictionaryObject, ArrayObject)):
            direct_identity = id(value)
            identity = ("direct", direct_identity)
            already_seen = direct_identity in seen_direct
            if not already_seen:
                seen_direct.add(direct_identity)
        else:
            return

        if isinstance(value, DictionaryObject):
            keys = key_set(value)
            forbidden = sorted(keys & FORBIDDEN_KEYS)
            if forbidden:
                fail("active_content", f"{path}: forbidden keys {', '.join(forbidden)}")
            action_name_value = dictionary_raw(value, "/S")
            action_name = (
                str(dereference(action_name_value))
                if isinstance(dereference(action_name_value), NameObject)
                else ""
            )
            type_value = dictionary_raw(value, "/Type")
            type_name = (
                str(dereference(type_value))
                if isinstance(dereference(type_value), NameObject)
                else ""
            )
            is_action = (
                expected_action is not None or type_name == "/Action" or action_name in KNOWN_ACTIONS
            )
            if expected_action is None and is_action:
                fail("active_content", f"{path}: action dictionary is outside a validated owner edge")
            if expected_action is not None:
                expected_identity, expected_kind, owner_path = expected_action
                if identity != expected_identity:
                    fail("active_content", f"{path}: action identity differs from {owner_path}")
                validate_action(value, path, expected_kind)
                actions[expected_kind] += 1
            subtype_value = dictionary_raw(value, "/Subtype")
            subtype = (
                str(dereference(subtype_value))
                if isinstance(dereference(subtype_value), NameObject)
                else ""
            )
            if subtype in FORBIDDEN_ANNOTATIONS:
                fail("active_content", f"{path}: forbidden annotation subtype {subtype}")
            if already_seen:
                return
            container_identity = identity
            for key in value.keys():
                key_name = str(key)
                child = dictionary_raw(value, key_name)
                child_expected = None
                if key_name in {"/A", "/OpenAction"}:
                    edge = (container_identity, key_name)
                    child_expected = allowed_edges.get(edge)
                    if child_expected is None:
                        fail("active_content", f"{path}/{key_name.lstrip('/')}: unvalidated action owner")
                    seen_edges.add(edge)
                visit(child, f"{path}/{key_name.lstrip('/')}", child_expected)
        elif isinstance(value, ArrayObject):
            if already_seen:
                return
            for index in range(len(value)):
                visit(array_raw(value, index), f"{path}[{index}]")

    visit(root, "catalog")
    if seen_edges != set(allowed_edges):
        fail("action_owner", "not every explicit action-owner edge is reachable from the catalog")
    if actions != EXPECTED_ACTION_COUNTS:
        fail("action_count", f"reachable action counts changed: {dict(actions)}")
    return actions


def validate_reader(reader: PdfReader, *, enforce_manifest_digests: bool = True) -> StructureReport:
    if reader.is_encrypted:
        fail("encryption", "encrypted PDFs are not permitted")
    if str(getattr(reader, "pdf_header", "")) != "%PDF-1.7":
        fail("pdf_version", f"expected PDF 1.7, observed {getattr(reader, 'pdf_header', 'missing')}")
    root_value = dictionary_raw(reader.trailer, "/Root")
    if object_reference(root_value) is None:
        fail("catalog_keys", "catalog must be indirect")
    root = require_dictionary(root_value, "catalog")
    if key_set(root) != EXPECTED_ROOT_KEYS:
        fail("catalog_keys", "catalog dictionary keys changed")
    try:
        require_name(dictionary_raw(root, "/Type"), "/Catalog", "catalog /Type")
        require_name(dictionary_raw(root, "/PageMode"), "/UseOutlines", "catalog /PageMode")
    except PdfStructureError as error:
        if error.code == "typed_name":
            fail("catalog_keys", "catalog type or page mode changed")
        raise
    if require_ascii_text(dictionary_raw(root, "/Lang"), "catalog /Lang") != "en-US":
        fail("catalog_keys", "catalog language changed")
    mark_info = require_dictionary(dictionary_raw(root, "/MarkInfo"), "catalog MarkInfo")
    if key_set(mark_info) != {"/Marked"}:
        fail("catalog_keys", "catalog MarkInfo changed shape")
    require_true(dictionary_raw(mark_info, "/Marked"), "catalog MarkInfo /Marked")

    validate_page_tree(reader, root)
    structure_index = validate_structure_tree(reader, root)
    open_action_line, open_action_value = validate_open_action(reader, root, structure_index)
    action_owners = [
        ActionOwner(
            "catalog/OpenAction",
            root,
            "/OpenAction",
            open_action_value,
            "/GoTo",
        )
    ]
    page_label_lines = validate_page_labels(root)
    named_destinations, named_lines = validate_named_destinations(reader, root)
    _, outline_lines = validate_outlines(
        root, named_destinations, structure_index, action_owners
    )
    (
        targets,
        page_and_link_navigation,
        _,
        page_struct_parents,
        annotation_locations,
    ) = validate_pages_and_links(reader, named_destinations, structure_index, action_owners)
    structure_line, structure_digest = validate_parent_tree(
        root,
        structure_index,
        page_struct_parents,
        annotation_locations,
        enforce_manifest_digest=enforce_manifest_digests,
    )
    allowed_edges = validate_action_owners(action_owners)
    scan_reachable_graph(root, allowed_edges)

    navigation = [open_action_line]
    navigation.extend(page_label_lines)
    navigation.append(structure_line)
    navigation.extend(named_lines)
    navigation.extend(outline_lines)
    navigation.extend(page_and_link_navigation)

    payload = "".join(f"{line}\n" for line in navigation).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if enforce_manifest_digests and digest != EXPECTED_NAVIGATION_SHA256:
        fail("navigation_digest", f"navigation manifest changed: {digest}")
    return StructureReport(
        tuple(sorted(targets)),
        tuple(navigation),
        digest,
        tuple(structure_index.semantic_lines),
        structure_digest,
    )


def validate_pdf_source(source: Any, *, enforce_manifest_digests: bool = True) -> StructureReport:
    records: list[logging.LogRecord] = []

    class DiagnosticCollector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.WARNING:
                records.append(record)

    logger = logging.getLogger("pypdf")
    previous_level = logger.level
    previous_disabled = logger.disabled
    previous_global_disable = logging.root.manager.disable
    collector = DiagnosticCollector()
    logger.disabled = False
    logging.disable(logging.NOTSET)
    logger.addHandler(collector)
    if previous_level == logging.NOTSET or previous_level > logging.WARNING:
        logger.setLevel(logging.WARNING)
    try:
        reader = PdfReader(source, strict=True)
        report = validate_reader(reader, enforce_manifest_digests=enforce_manifest_digests)
        if records:
            rendered = "; ".join(record.getMessage() for record in records[:3])
            fail("pdf_parse_diagnostic", f"strict PDF parse emitted a warning: {rendered}")
        return report
    except PdfStructureError:
        raise
    except Exception as error:
        fail("pdf_parse", f"strict PDF parse failed: {error}")
    finally:
        logger.removeHandler(collector)
        logger.setLevel(previous_level)
        logger.disabled = previous_disabled
        logging.disable(previous_global_disable)
    raise RuntimeError("unreachable")


def validate_bytes(data: bytes, *, enforce_manifest_digests: bool = True) -> StructureReport:
    if not isinstance(data, bytes) or not data:
        fail("input", "PDF byte input is empty or not bytes")
    return validate_pdf_source(
        io.BytesIO(data), enforce_manifest_digests=enforce_manifest_digests
    )


def validate_path(
    path: pathlib.Path, *, enforce_manifest_digests: bool = True
) -> StructureReport:
    if not path.is_file() or path.is_symlink():
        fail("input", f"PDF is absent, non-regular, or symbolic: {path}")
    return validate_pdf_source(path, enforce_manifest_digests=enforce_manifest_digests)


def validate_output_paths(
    input_path: pathlib.Path,
    targets_path: pathlib.Path,
    navigation_path: pathlib.Path,
) -> None:
    try:
        input_resolved = input_path.resolve(strict=True)
    except OSError as error:
        fail("input", f"cannot resolve input PDF: {error}")
    outputs = (targets_path, navigation_path)
    resolved_outputs: list[pathlib.Path] = []
    for output in outputs:
        if output.is_symlink():
            fail("output", f"output must not be symbolic: {output}")
        if output.exists() and not output.is_file():
            fail("output", f"existing output is not a regular file: {output}")
        parent = output.parent if str(output.parent) else pathlib.Path(".")
        if not parent.is_dir():
            fail("output", f"output parent is not a directory: {parent}")
        resolved = output.resolve(strict=False)
        if resolved == input_resolved:
            fail("output", f"output aliases input PDF: {output}")
        if output.exists():
            try:
                if os.path.samefile(output, input_path):
                    fail("output", f"output hard-links input PDF: {output}")
            except OSError as error:
                fail("output", f"cannot compare output identity: {error}")
        resolved_outputs.append(resolved)
    if resolved_outputs[0] == resolved_outputs[1]:
        fail("output", "target and navigation outputs must be distinct")
    if targets_path.exists() and navigation_path.exists():
        try:
            if os.path.samefile(targets_path, navigation_path):
                fail("output", "target and navigation outputs are hard-link aliases")
        except OSError as error:
            fail("output", f"cannot compare output identities: {error}")


def write_lines(path: pathlib.Path, lines: tuple[str, ...]) -> None:
    parent = path.parent if str(path.parent) else pathlib.Path(".")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            dir=parent,
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
    if len(argv) != 3:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} input.pdf targets.txt navigation.txt",
            file=sys.stderr,
        )
        return 2
    pdf_path, targets_path, navigation_path = map(pathlib.Path, argv)
    try:
        validate_output_paths(pdf_path, targets_path, navigation_path)
        input_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        report = validate_path(pdf_path)
        write_lines(targets_path, report.targets)
        write_lines(navigation_path, report.navigation)
        if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != input_hash:
            fail("input", "input PDF changed while writing structure reports")
    except (OSError, PdfStructureError) as error:
        code = error.code if isinstance(error, PdfStructureError) else "io"
        print(f"Mathematical results guide PDF structure check failed [{code}]: {error}", file=sys.stderr)
        return 1
    print(
        "Mathematical results guide PDF structure check passed: "
        f"targets={len(report.targets)} navigation_records={len(report.navigation)} "
        f"navigation_sha256={report.navigation_sha256}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
