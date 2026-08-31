#!/usr/bin/env python3
"""Hostile mutation tests for the results-guide PDF structure policy."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    RectangleObject,
    TextStringObject,
    create_string_object,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-mathematical-results-guide-pdf-structure-v2.py"
DEFAULT_PDF = ROOT / "output/pdf/mathematical-results-guide.pdf"


def load_checker():
    specification = importlib.util.spec_from_file_location(
        "mathematical_results_guide_pdf_structure", CHECKER_PATH
    )
    if specification is None or specification.loader is None:
        raise SystemExit("PDF structure self-test failed: cannot load checker")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


CHECKER = load_checker()


def utf16_text(text: str) -> TextStringObject:
    value = create_string_object(b"\xfe\xff" + text.encode("utf-16-be"))
    if not isinstance(value, TextStringObject):
        raise SystemExit("PDF structure self-test failed: UTF-16 fixture is not text")
    return value


def new_writer(source: pathlib.Path) -> PdfWriter:
    # Incremental mutation preserves the canonical page/name/structure topology.  A full clone
    # flattens the page tree and would make every hostile case fail for the same irrelevant reason.
    writer = PdfWriter(str(source), incremental=True)
    writer.pdf_header = "%PDF-1.7"
    return writer


def first_annotation(writer: PdfWriter):
    for page in writer.pages:
        annotations = CHECKER.dereference(page.get("/Annots"))
        if isinstance(annotations, ArrayObject) and annotations:
            return annotations, CHECKER.dereference(annotations[0])
    raise SystemExit("PDF structure self-test failed: source has no annotation")


def first_outline_action(writer: PdfWriter):
    outlines = CHECKER.dereference(writer.root_object.get("/Outlines"))
    first = CHECKER.dereference(outlines.get("/First"))
    action = CHECKER.dereference(first.get("/A"))
    if not isinstance(action, DictionaryObject):
        raise SystemExit("PDF structure self-test failed: source has no first outline action")
    return action


def first_two_annotations(writer: PdfWriter):
    for page in writer.pages:
        annotations = CHECKER.dereference(page.get("/Annots"))
        if isinstance(annotations, ArrayObject) and len(annotations) >= 2:
            first = CHECKER.dereference(annotations[0])
            second = CHECKER.dereference(annotations[1])
            return first, second
    raise SystemExit("PDF structure self-test failed: source has fewer than two annotations")


def annotations_with_action(writer: PdfWriter, kind: str):
    result = []
    for page in writer.pages:
        annotations = CHECKER.dereference(page.get("/Annots"))
        if not isinstance(annotations, ArrayObject):
            continue
        for index in range(len(annotations)):
            annotation = CHECKER.dereference(list.__getitem__(annotations, index))
            action = CHECKER.dereference(CHECKER.dictionary_raw(annotation, "/A"))
            if isinstance(action, DictionaryObject) and str(action.get("/S")) == kind:
                result.append(annotation)
    if not result:
        raise SystemExit(f"PDF structure self-test failed: source has no {kind} annotation")
    return result


def destination_name_tree(writer: PdfWriter):
    names = CHECKER.dereference(writer.root_object.get("/Names"))
    return CHECKER.dereference(names.get("/Dests"))


def first_named_destination(writer: PdfWriter):
    tree = destination_name_tree(writer)
    leaf = CHECKER.dereference(list.__getitem__(tree["/Kids"], 0))
    entries = leaf["/Names"]
    wrapper = CHECKER.dereference(list.__getitem__(entries, 1))
    return leaf, entries, wrapper["/D"]


def named_destination_array(writer: PdfWriter, target: str):
    tree = destination_name_tree(writer)
    for leaf_value in tree["/Kids"]:
        leaf = CHECKER.dereference(leaf_value)
        entries = leaf["/Names"]
        for index in range(0, len(entries), 2):
            if str(list.__getitem__(entries, index)) == target:
                wrapper = CHECKER.dereference(list.__getitem__(entries, index + 1))
                return wrapper["/D"]
    raise SystemExit(f"PDF structure self-test failed: destination {target!r} is absent")


def clone_as_stream(value: DictionaryObject) -> DecodedStreamObject:
    stream = DecodedStreamObject()
    for key in value.keys():
        stream[key] = CHECKER.dictionary_raw(value, str(key))
    stream.set_data(b"bounded-hostile-probe")
    return stream


def replace_first_structure_record(writer: PdfWriter, target_type: str) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))

    def visit(value, replace: Callable[[DecodedStreamObject], None]) -> bool:
        resolved = CHECKER.dereference(value)
        if isinstance(resolved, ArrayObject):
            for index in range(len(resolved)):
                child = list.__getitem__(resolved, index)
                child_resolved = CHECKER.dereference(child)
                if (
                    isinstance(child_resolved, DictionaryObject)
                    and str(child_resolved.get("/Type")) == target_type
                ):
                    resolved[index] = clone_as_stream(child_resolved)
                    return True
                if visit(child, lambda stream, index=index: resolved.__setitem__(index, stream)):
                    return True
            return False
        if not isinstance(resolved, DictionaryObject):
            return False
        if str(resolved.get("/Type")) != "/StructElem":
            return False
        child = CHECKER.dictionary_raw(resolved, "/K")
        child_resolved = CHECKER.dereference(child)
        if (
            isinstance(child_resolved, DictionaryObject)
            and str(child_resolved.get("/Type")) == target_type
        ):
            resolved[NameObject("/K")] = clone_as_stream(child_resolved)
            return True
        return visit(child, lambda stream: resolved.__setitem__(NameObject("/K"), stream))

    if not visit(CHECKER.dictionary_raw(structure, "/K"), lambda stream: None):
        raise SystemExit(
            f"PDF structure self-test failed: source has no structure record {target_type}"
        )


def write_writer(writer: PdfWriter, path: pathlib.Path) -> None:
    with path.open("wb") as stream:
        writer.write(stream)


def expect_fail(
    source: pathlib.Path,
    directory: pathlib.Path,
    name: str,
    mutation: Callable[[PdfWriter], None],
    expected_code: str,
) -> None:
    writer = new_writer(source)
    mutation(writer)
    output = directory / f"{name}.pdf"
    write_writer(writer, output)
    try:
        CHECKER.validate_path(output)
    except CHECKER.PdfStructureError as error:
        if error.code != expected_code:
            raise SystemExit(
                f"PDF structure self-test failed: {name} produced [{error.code}], "
                f"expected [{expected_code}]"
            ) from error
        return
    raise SystemExit(f"PDF structure self-test failed: {name} unexpectedly passed")


def expect_fail_message(
    source: pathlib.Path,
    directory: pathlib.Path,
    name: str,
    mutation: Callable[[PdfWriter], None],
    expected_message: str,
) -> None:
    writer = new_writer(source)
    mutation(writer)
    output = directory / f"{name}.pdf"
    write_writer(writer, output)
    try:
        CHECKER.validate_path(output)
    except CHECKER.PdfStructureError as error:
        observed_message = str(error)
        if error.code != "name_tree" or expected_message not in observed_message:
            raise SystemExit(
                f"PDF structure self-test failed: {name} produced "
                f"[{error.code}] {observed_message!r}, expected [name_tree] "
                f"containing {expected_message!r}"
            ) from error
        return
    raise SystemExit(f"PDF structure self-test failed: {name} unexpectedly passed")


def expect_raw_fail(
    source: pathlib.Path,
    directory: pathlib.Path,
    name: str,
    mutation: Callable[[bytes], bytes],
    expected_code: str,
) -> None:
    original = source.read_bytes()
    mutated = mutation(original)
    if mutated == original:
        raise SystemExit(f"PDF structure self-test failed: {name} did not change the bytes")
    output = directory / f"{name}.pdf"
    output.write_bytes(mutated)
    try:
        CHECKER.validate_path(output)
    except CHECKER.PdfStructureError as error:
        if error.code != expected_code:
            raise SystemExit(
                f"PDF structure self-test failed: {name} produced [{error.code}], "
                f"expected [{expected_code}]"
            ) from error
        return
    raise SystemExit(f"PDF structure self-test failed: {name} unexpectedly passed")


def javascript_action() -> DictionaryObject:
    return DictionaryObject(
        {
            NameObject("/S"): NameObject("/JavaScript"),
            NameObject("/JS"): TextStringObject("app.alert('probe')"),
        }
    )


def mutate_open_action_javascript(writer: PdfWriter) -> None:
    writer.root_object[NameObject("/OpenAction")] = javascript_action()


def mutate_acroform(writer: PdfWriter) -> None:
    writer.root_object[NameObject("/AcroForm")] = DictionaryObject()


def mutate_embedded_files(writer: PdfWriter) -> None:
    names = CHECKER.dereference(writer.root_object.get("/Names"))
    names[NameObject("/EmbeddedFiles")] = DictionaryObject()


def mutate_page_additional_action(writer: PdfWriter) -> None:
    writer.pages[0][NameObject("/AA")] = DictionaryObject(
        {NameObject("/O"): javascript_action()}
    )


def mutate_annotation_additional_action(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/AA")] = DictionaryObject(
        {NameObject("/E"): javascript_action()}
    )


def mutate_launch_action(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/A")] = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject("/Launch"),
            NameObject("/F"): TextStringObject("probe"),
        }
    )


def mutate_file_attachment(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/Subtype")] = NameObject("/FileAttachment")


def mutate_direct_destination_and_action(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/Dest")] = TextStringObject("section*.1")


def mutate_open_action_second_page(writer: PdfWriter) -> None:
    action = CHECKER.dereference(writer.root_object.get("/OpenAction"))
    action[NameObject("/D")] = ArrayObject(
        [writer.pages[1].indirect_reference, NameObject("/Fit")]
    )


def mutate_duplicate_link(writer: PdfWriter) -> None:
    annotations, _ = first_annotation(writer)
    annotations.append(annotations[0])


def mutate_oversized_link(writer: PdfWriter) -> None:
    annotations, annotation = first_annotation(writer)
    annotation[NameObject("/Rect")] = RectangleObject([0, 0, 595.276, 841.89])
    annotations.append(annotations[0])


def mutate_annotation_flags(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/F")] = NumberObject(4)


def append_outline_action(writer: PdfWriter, kind: str, **entries) -> None:
    action = first_outline_action(writer)
    chained = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject(kind),
        }
    )
    for key, value in entries.items():
        chained[NameObject(f"/{key}")] = value
    action[NameObject("/Next")] = chained


def mutate_outline_named_print(writer: PdfWriter) -> None:
    append_outline_action(writer, "/Named", N=NameObject("/Print"))


def mutate_outline_reset_form(writer: PdfWriter) -> None:
    append_outline_action(writer, "/ResetForm")


def mutate_outline_goto_3d_view(writer: PdfWriter) -> None:
    append_outline_action(writer, "/GoTo3DView")


def mutate_shifted_hitbox(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    left, bottom, right, top = [float(value) for value in annotation["/Rect"]]
    annotation[NameObject("/Rect")] = RectangleObject(
        [left + 10.0, bottom, right + 10.0, top]
    )


def mutate_swapped_hitboxes(writer: PdfWriter) -> None:
    first, second = first_two_annotations(writer)
    first_rectangle = [float(value) for value in first["/Rect"]]
    second_rectangle = [float(value) for value in second["/Rect"]]
    first[NameObject("/Rect")] = RectangleObject(second_rectangle)
    second[NameObject("/Rect")] = RectangleObject(first_rectangle)


def mutate_named_coordinate(writer: PdfWriter) -> None:
    _, _, destination = first_named_destination(writer)
    destination[2] = FloatObject(float(destination[2]) + 1.0)


def mutate_named_coordinate_type(writer: PdfWriter) -> None:
    _, _, destination = first_named_destination(writer)
    destination[2] = TextStringObject(str(destination[2]))


def mutate_duplicate_destination_name(writer: PdfWriter) -> None:
    _, entries, _ = first_named_destination(writer)
    entries[2] = TextStringObject(str(entries[0]))


def mutate_swapped_name_tree_leaves(writer: PdfWriter) -> None:
    tree = destination_name_tree(writer)
    kids = tree["/Kids"]
    first = list.__getitem__(kids, 0)
    second = list.__getitem__(kids, 1)
    kids[0] = second
    kids[1] = first


def mutate_destination_limits(writer: PdfWriter) -> None:
    leaf, _, _ = first_named_destination(writer)
    leaf["/Limits"][0] = TextStringObject("changed")


def mutate_direct_name_tree_leaf(writer: PdfWriter) -> None:
    tree = destination_name_tree(writer)
    child = CHECKER.dereference(list.__getitem__(tree["/Kids"], 0))
    direct = DictionaryObject(
        {key: CHECKER.dictionary_raw(child, str(key)) for key in child.keys()}
    )
    tree["/Kids"][0] = direct


def mutate_destination_names_nonarray(writer: PdfWriter) -> None:
    leaf, _, _ = first_named_destination(writer)
    leaf[NameObject("/Names")] = TextStringObject("not-an-array")


def mutate_destination_names_empty(writer: PdfWriter) -> None:
    leaf, _, _ = first_named_destination(writer)
    leaf[NameObject("/Names")] = ArrayObject()


def mutate_destination_names_odd(writer: PdfWriter) -> None:
    _, entries, _ = first_named_destination(writer)
    del entries[-1]


def mutate_destination_names_even_wrong_count(writer: PdfWriter) -> None:
    _, entries, _ = first_named_destination(writer)
    del entries[-2:]


def mutate_internal_structure_coordinate(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/GoTo")[0]
    destination = annotation["/A"]["/SD"]
    destination[2] = FloatObject(float(destination[2]) + 1.0)


def mutate_internal_structure_orphan(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/GoTo")[0]
    destination = annotation["/A"]["/SD"]
    destination[0] = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/StructElem"),
            NameObject("/S"): NameObject("/Document"),
        }
    )


def mutate_outline_target_with_matching_coordinates(writer: PdfWriter) -> None:
    action = first_outline_action(writer)
    replacement = named_destination_array(writer, "subsection*.2")
    action[NameObject("/D")] = TextStringObject("subsection*.2")
    action["/SD"][2] = list.__getitem__(replacement, 2)
    action["/SD"][3] = list.__getitem__(replacement, 3)


def mutate_outline_competing_destination(writer: PdfWriter) -> None:
    outlines = CHECKER.dereference(writer.root_object.get("/Outlines"))
    first = CHECKER.dereference(outlines.get("/First"))
    first[NameObject("/Dest")] = TextStringObject("section*.1")


def mutate_outline_count_sign(writer: PdfWriter) -> None:
    outlines = CHECKER.dereference(writer.root_object.get("/Outlines"))
    first = CHECKER.dereference(outlines.get("/First"))
    first[NameObject("/Count")] = NumberObject(abs(int(first["/Count"])))


def mutate_outline_presentation_flag(writer: PdfWriter) -> None:
    outlines = CHECKER.dereference(writer.root_object.get("/Outlines"))
    first = CHECKER.dereference(outlines.get("/First"))
    first[NameObject("/F")] = NumberObject(2)


def mutate_action_alias(writer: PdfWriter) -> None:
    annotations = annotations_with_action(writer, "/URI")
    by_target: dict[str, list[DictionaryObject]] = {}
    for annotation in annotations:
        target = str(annotation["/A"]["/URI"])
        by_target.setdefault(target, []).append(annotation)
    pair = next((items for items in by_target.values() if len(items) >= 2), None)
    if pair is None:
        raise SystemExit("PDF structure self-test failed: no repeated URI target")
    shared_action = writer._add_object(CHECKER.dictionary_raw(pair[0], "/A"))
    pair[0][NameObject("/A")] = shared_action
    pair[1][NameObject("/A")] = shared_action


def mutate_hidden_action_owner(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    metadata = CHECKER.dereference(writer.root_object.get("/Metadata"))
    metadata[NameObject("/A")] = CHECKER.dictionary_raw(annotation, "/A")


def mutate_struct_parent_value(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/StructParent")] = NumberObject(int(annotation["/StructParent"]) + 1000)


def mutate_struct_parent_type(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    annotation[NameObject("/StructParent")] = TextStringObject(str(annotation["/StructParent"]))


def mutate_submicro_hitbox(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    coordinates = [float(value) for value in annotation["/Rect"]]
    coordinates[0] += 1.0e-7
    annotation[NameObject("/Rect")] = RectangleObject(coordinates)


def mutate_hitbox_number_type(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    rectangle = annotation["/Rect"]
    rectangle[0] = TextStringObject(str(rectangle[0]))


def mutate_link_color(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    color = annotation["/C"]
    color[0] = FloatObject(float(color[0]) + 0.01)


def mutate_link_color_type(writer: PdfWriter) -> None:
    _, annotation = first_annotation(writer)
    color = annotation["/C"]
    color[0] = TextStringObject(str(color[0]))


def mutate_open_action_orphan_structure(writer: PdfWriter) -> None:
    action = CHECKER.dereference(writer.root_object.get("/OpenAction"))
    action["/SD"][0] = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/StructElem"),
            NameObject("/S"): NameObject("/Document"),
        }
    )


def mutate_uri_action_type(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    annotation["/A"][NameObject("/S")] = TextStringObject("/URI")


def mutate_uri_to_remote_action(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    annotation["/A"][NameObject("/S")] = NameObject("/GoToR")


def mutate_page_labels_prefix(writer: PdfWriter) -> None:
    labels = CHECKER.dereference(writer.root_object.get("/PageLabels"))
    specification = CHECKER.dereference(labels["/Nums"][1])
    specification[NameObject("/P")] = TextStringObject("probe-")


def mutate_media_box(writer: PdfWriter) -> None:
    box = writer.pages[0]["/MediaBox"]
    box[2] = FloatObject(float(box[2]) + 0.005)


def mutate_page_type(writer: PdfWriter) -> None:
    writer.pages[0][NameObject("/Type")] = TextStringObject("/Page")


def mutate_page_tabs_type(writer: PdfWriter) -> None:
    writer.pages[0][NameObject("/Tabs")] = TextStringObject("/S")


def mutate_inherited_page_rotation(writer: PdfWriter) -> None:
    pages = CHECKER.dereference(writer.root_object.get("/Pages"))
    pages[NameObject("/Rotate")] = NumberObject(90)


def mutate_landscape_page_rotation(writer: PdfWriter) -> None:
    writer.pages[6][NameObject("/Rotate")] = NumberObject(0)


def mutate_landscape_page_rotation_type(writer: PdfWriter) -> None:
    writer.pages[6][NameObject("/Rotate")] = TextStringObject("90")


def mutate_page_struct_parents(writer: PdfWriter) -> None:
    writer.pages[0][NameObject("/StructParents")] = NumberObject(1)


def mutate_role_map(writer: PdfWriter) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))
    role_map = CHECKER.dereference(structure.get("/RoleMap"))
    role_map[NameObject("/Title")] = NameObject("/H1")


def mutate_role_map_control(writer: PdfWriter) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))
    role_map = CHECKER.dereference(structure.get("/RoleMap"))
    role_map[NameObject("/Artifact")] = NameObject("/NonStruct\tprobe")


def mutate_structure_role(writer: PdfWriter) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))
    document = CHECKER.dereference(structure.get("/K"))
    child = CHECKER.dereference(document["/K"][0])
    child[NameObject("/S")] = NameObject("/Sect")


def mutate_structure_alt_text(writer: PdfWriter) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))
    document = CHECKER.dereference(structure.get("/K"))
    child = CHECKER.dereference(document["/K"][0])
    child[NameObject("/Alt")] = TextStringObject("changed accessible semantics")


def mutate_action_stream(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    annotation[NameObject("/A")] = clone_as_stream(annotation["/A"])


def mutate_mcr_stream(writer: PdfWriter) -> None:
    replace_first_structure_record(writer, "/MCR")


def mutate_objr_stream(writer: PdfWriter) -> None:
    replace_first_structure_record(writer, "/OBJR")


def mutate_content_mcid(writer: PdfWriter) -> None:
    content = writer.pages[0]["/Contents"]
    data = content.get_data()
    if data.count(b"/MCID 0") != 1:
        raise SystemExit("PDF structure self-test failed: page-one MCID sentinel changed")
    content.set_data(data.replace(b"/MCID 0", b"/MCID 9", 1))


def mutate_content_tag(writer: PdfWriter) -> None:
    content = writer.pages[0]["/Contents"]
    data = content.get_data()
    needle = b"/text<</MCID 0>> BDC"
    if data.count(needle) != 1:
        raise SystemExit("PDF structure self-test failed: page-one tag sentinel changed")
    content.set_data(data.replace(needle, b"/Link<</MCID 0>> BDC", 1))


def mutate_content_duplicate_mcid(writer: PdfWriter) -> None:
    content = writer.pages[0]["/Contents"]
    data = content.get_data()
    needle = b"/MCID 1>> BDC"
    if data.count(needle) != 1:
        raise SystemExit("PDF structure self-test failed: page-one MCID-one sentinel changed")
    content.set_data(data.replace(needle, b"/MCID 0>> BDC", 1))


def mutate_content_unbalanced_scope(writer: PdfWriter) -> None:
    content = writer.pages[0]["/Contents"]
    data = content.get_data()
    if b"\nEMC\n" not in data:
        raise SystemExit("PDF structure self-test failed: page-one EMC sentinel changed")
    content.set_data(data.replace(b"\nEMC\n", b"\nBMC\n", 1))


def mutate_to_unicode_cmap(writer: PdfWriter) -> None:
    resources = CHECKER.dereference(writer.pages[0].get("/Resources"))
    fonts = CHECKER.dereference(resources.get("/Font"))
    needle = b"<001B> <0041>"
    for key in fonts.keys():
        font = CHECKER.dereference(CHECKER.dictionary_raw(fonts, str(key)))
        if not isinstance(font, DictionaryObject) or "/ToUnicode" not in font:
            continue
        cmap = CHECKER.dereference(CHECKER.dictionary_raw(font, "/ToUnicode"))
        data = cmap.get_data()
        if needle in data:
            cmap.set_data(data.replace(needle, b"<001B> <0042>", 1))
            return
    raise SystemExit("PDF structure self-test failed: ToUnicode sentinel changed")


def mutate_destination_name_encoding(writer: PdfWriter) -> None:
    tree = destination_name_tree(writer)
    for leaf_value in tree["/Kids"]:
        leaf = CHECKER.dereference(leaf_value)
        entries = leaf["/Names"]
        for index in range(0, len(entries), 2):
            if str(list.__getitem__(entries, index)) == "section*.1":
                entries[index] = utf16_text("section*.1")
                return
    raise SystemExit("PDF structure self-test failed: section destination sentinel changed")


def mutate_internal_target_encoding(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/GoTo")[0]
    target = str(annotation["/A"]["/D"])
    annotation["/A"][NameObject("/D")] = utf16_text(target)


def mutate_uri_encoding(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    target = str(annotation["/A"]["/URI"])
    annotation["/A"][NameObject("/URI")] = utf16_text(target)


def mutate_structure_id_encoding(writer: PdfWriter) -> None:
    structure = CHECKER.dereference(writer.root_object.get("/StructTreeRoot"))
    document = CHECKER.dereference(structure.get("/K"))
    document[NameObject("/ID")] = utf16_text(str(document["/ID"]))


def mutate_internal_contents_encoding(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/GoTo")[0]
    annotation[NameObject("/Contents")] = utf16_text("ref")


def mutate_uri_contents_encoding(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    annotation[NameObject("/Contents")] = TextStringObject(str(annotation["/Contents"]))


def mutate_internal_contents_value(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/GoTo")[0]
    annotation[NameObject("/Contents")] = TextStringObject("not-ref")


def mutate_uri_contents_value(writer: PdfWriter) -> None:
    annotation = annotations_with_action(writer, "/URI")[0]
    annotation[NameObject("/Contents")] = utf16_text("https://different.invalid/")


def mutate_outline_title_encoding(writer: PdfWriter) -> None:
    outlines = CHECKER.dereference(writer.root_object.get("/Outlines"))
    first = CHECKER.dereference(outlines.get("/First"))
    first[NameObject("/Title")] = TextStringObject(str(first["/Title"]))


def mutate_language_encoding(writer: PdfWriter) -> None:
    writer.root_object[NameObject("/Lang")] = utf16_text("en-US")


def mutate_invalid_numeric_token(data: bytes) -> bytes:
    needle = b"/MediaBox [ 0 0 595.276 841.89 ]"
    if data.count(needle) != 1:
        raise SystemExit("PDF structure self-test failed: raw MediaBox sentinel changed")
    return data.replace(needle, b"/MediaBox [ + 0 595.276 841.89 ]", 1)


def expect_cli_output_failure(
    source: pathlib.Path,
    targets: pathlib.Path,
    navigation: pathlib.Path,
    name: str,
) -> None:
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-O")
    command.extend(
        ["-I", "-B", str(CHECKER_PATH), str(source), str(targets), str(navigation)]
    )
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode == 0 or "[output]" not in result.stderr:
        raise SystemExit(
            f"PDF structure self-test failed: {name} did not fail with output policy: "
            f"status={result.returncode} stderr={result.stderr!r}"
        )
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise SystemExit(f"PDF structure self-test failed: {name} changed the input PDF")


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} [source.pdf]",
            file=sys.stderr,
        )
        return 2
    source = pathlib.Path(argv[0]) if argv else DEFAULT_PDF
    if not source.is_file() or source.is_symlink():
        raise SystemExit("PDF structure self-test failed: source is absent, non-regular, or symbolic")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    baseline = CHECKER.validate_path(source)
    if len(baseline.targets) != 56 or len(baseline.navigation) != 217:
        raise SystemExit("PDF structure self-test failed: baseline report changed")

    cases = [
        ("open-action-javascript", mutate_open_action_javascript, "catalog_open_action"),
        ("catalog-acroform", mutate_acroform, "catalog_keys"),
        ("name-tree-embedded-files", mutate_embedded_files, "name_tree"),
        ("page-additional-action", mutate_page_additional_action, "page_keys"),
        ("annotation-additional-action", mutate_annotation_additional_action, "annotation_keys"),
        ("launch-action", mutate_launch_action, "annotation_action"),
        ("file-attachment", mutate_file_attachment, "annotation_subtype"),
        ("direct-destination-plus-action", mutate_direct_destination_and_action, "annotation_keys"),
        ("open-action-second-page", mutate_open_action_second_page, "catalog_open_action"),
        ("duplicate-link", mutate_duplicate_link, "annotation_shape"),
        ("oversized-link-overlay", mutate_oversized_link, "annotation_rectangle"),
        ("annotation-flags", mutate_annotation_flags, "annotation_keys"),
        ("outline-next-named-print", mutate_outline_named_print, "annotation_action"),
        ("outline-next-reset-form", mutate_outline_reset_form, "annotation_action"),
        ("outline-next-goto-3d-view", mutate_outline_goto_3d_view, "annotation_action"),
        ("shifted-link-hitbox", mutate_shifted_hitbox, "navigation_digest"),
        ("swapped-link-hitboxes", mutate_swapped_hitboxes, "navigation_digest"),
        ("named-coordinate", mutate_named_coordinate, "navigation_digest"),
        ("named-coordinate-type", mutate_named_coordinate_type, "typed_number"),
        ("duplicate-destination-name", mutate_duplicate_destination_name, "name_tree"),
        ("swapped-name-tree-leaves", mutate_swapped_name_tree_leaves, "name_tree"),
        ("destination-limits", mutate_destination_limits, "name_tree"),
        ("direct-name-tree-leaf", mutate_direct_name_tree_leaf, "name_tree"),
        (
            "internal-structure-coordinate",
            mutate_internal_structure_coordinate,
            "annotation_action",
        ),
        ("internal-structure-orphan", mutate_internal_structure_orphan, "annotation_action"),
        (
            "outline-target-matching-coordinates",
            mutate_outline_target_with_matching_coordinates,
            "outline",
        ),
        ("outline-competing-destination", mutate_outline_competing_destination, "outline"),
        ("outline-count-sign", mutate_outline_count_sign, "outline"),
        ("outline-presentation-flag", mutate_outline_presentation_flag, "outline"),
        ("action-alias", mutate_action_alias, "action_alias"),
        ("hidden-action-owner", mutate_hidden_action_owner, "active_content"),
        ("struct-parent-value", mutate_struct_parent_value, "structure_tree"),
        ("struct-parent-type", mutate_struct_parent_type, "typed_integer"),
        ("submicro-link-hitbox", mutate_submicro_hitbox, "navigation_digest"),
        ("link-hitbox-number-type", mutate_hitbox_number_type, "typed_number"),
        ("link-color", mutate_link_color, "navigation_digest"),
        ("link-color-type", mutate_link_color_type, "typed_number"),
        (
            "open-action-orphan-structure",
            mutate_open_action_orphan_structure,
            "catalog_open_action",
        ),
        ("uri-action-type", mutate_uri_action_type, "typed_name"),
        ("uri-to-remote-action", mutate_uri_to_remote_action, "annotation_action"),
        ("page-label-prefix", mutate_page_labels_prefix, "page_labels"),
        ("media-box", mutate_media_box, "page_geometry"),
        ("page-type", mutate_page_type, "typed_name"),
        ("page-tabs-type", mutate_page_tabs_type, "typed_name"),
        ("inherited-page-rotation", mutate_inherited_page_rotation, "page_tree"),
        ("landscape-page-rotation", mutate_landscape_page_rotation, "typed_integer"),
        (
            "landscape-page-rotation-type",
            mutate_landscape_page_rotation_type,
            "typed_integer",
        ),
        ("page-struct-parents", mutate_page_struct_parents, "typed_integer"),
        ("role-map", mutate_role_map, "structure_digest"),
        ("role-map-control", mutate_role_map_control, "manifest_control"),
        ("structure-role", mutate_structure_role, "structure_digest"),
        ("structure-alt-text", mutate_structure_alt_text, "structure_tree"),
        ("action-stream", mutate_action_stream, "dictionary_shape"),
        ("mcr-stream", mutate_mcr_stream, "structure_tree"),
        ("objr-stream", mutate_objr_stream, "structure_tree"),
        ("content-mcid", mutate_content_mcid, "marked_content"),
        ("content-tag", mutate_content_tag, "marked_content"),
        ("content-duplicate-mcid", mutate_content_duplicate_mcid, "marked_content"),
        ("content-unbalanced-scope", mutate_content_unbalanced_scope, "marked_content"),
        ("to-unicode-cmap", mutate_to_unicode_cmap, "structure_digest"),
        ("destination-name-encoding", mutate_destination_name_encoding, "text_encoding"),
        ("internal-target-encoding", mutate_internal_target_encoding, "text_encoding"),
        ("uri-encoding", mutate_uri_encoding, "text_encoding"),
        ("structure-id-encoding", mutate_structure_id_encoding, "text_encoding"),
        ("internal-contents-encoding", mutate_internal_contents_encoding, "text_encoding"),
        ("uri-contents-encoding", mutate_uri_contents_encoding, "text_encoding"),
        ("internal-contents-value", mutate_internal_contents_value, "annotation_shape"),
        ("uri-contents-value", mutate_uri_contents_value, "annotation_shape"),
        ("outline-title-encoding", mutate_outline_title_encoding, "text_encoding"),
        ("language-encoding", mutate_language_encoding, "text_encoding"),
    ]
    message_cases = [
        (
            "destination-names-nonarray-diagnostic",
            mutate_destination_names_nonarray,
            "leaf /Names must be an array",
        ),
        (
            "destination-names-empty-diagnostic",
            mutate_destination_names_empty,
            "leaf /Names array is empty",
        ),
        (
            "destination-names-odd-diagnostic",
            mutate_destination_names_odd,
            "leaf /Names has an odd item count: 63",
        ),
        (
            "destination-names-count-diagnostic",
            mutate_destination_names_even_wrong_count,
            "canonical destination leaf pair count changed: expected 32, found 31",
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="pid-rs-guide-pdf-structure-self-test-") as temporary:
        directory = pathlib.Path(temporary)
        for name, mutation, expected_code in cases:
            expect_fail(source, directory, name, mutation, expected_code)
        for name, mutation, expected_message in message_cases:
            expect_fail_message(source, directory, name, mutation, expected_message)
        expect_raw_fail(
            source,
            directory,
            "invalid-numeric-token",
            mutate_invalid_numeric_token,
            "pdf_parse_diagnostic",
        )

        io_source = directory / "io-source.pdf"
        shutil.copyfile(source, io_source)
        expect_cli_output_failure(
            io_source,
            io_source,
            directory / "input-alias-navigation.txt",
            "input-path output alias",
        )
        hardlink = directory / "input-hardlink.txt"
        os.link(io_source, hardlink)
        expect_cli_output_failure(
            io_source,
            hardlink,
            directory / "hardlink-navigation.txt",
            "input hard-link output alias",
        )
        shared_output = directory / "shared-output.txt"
        expect_cli_output_failure(
            io_source,
            shared_output,
            shared_output,
            "shared output path",
        )
        symlink_target = directory / "symlink-target.txt"
        symlink_target.write_text("control\n", encoding="utf-8")
        symlink_output = directory / "symlink-output.txt"
        symlink_output.symlink_to(symlink_target)
        expect_cli_output_failure(
            io_source,
            symlink_output,
            directory / "symlink-navigation.txt",
            "symbolic output path",
        )

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise SystemExit("PDF structure self-test failed: canonical source PDF changed")
    print(
        "Mathematical results guide PDF structure self-test passed: "
        f"baseline plus {len(cases)} object-graph mutations, 1 raw-parser mutation, "
        f"4 name-tree diagnostic controls, and 4 output-path controls."
    )
    print(
        "Boundary: source-specific active-content and navigation policy only; "
        "typed represented-binary64 numbers, not lexical PDF-real identity; "
        "not a generic malware-free or viewer-safety claim."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
