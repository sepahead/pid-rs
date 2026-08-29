#!/usr/bin/env python3
"""Fail-closed self-test for the source-specific Pandoc TeX normalizer."""

from __future__ import annotations

import ast
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import NoReturn


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
NORMALIZER = SCRIPT_DIR / "normalize-mathematical-results-guide-pandoc-tex.py"
FAILURE_PREFIX = b"Pandoc TeX normalization failed: "

REQUIRED_CONSTANTS = frozenset(
    {
        "MAX_INPUT_BYTES",
        "LEGACY_PANDOC_VERSION",
        "CANONICAL_PANDOC_VERSION",
        "EXPECTED_HEADING_IDS",
        "TABLE_WRAPPER",
        "NONE_COUNTER",
        "LONGTABLE_BEGIN",
        "LONGTABLE_END",
        "LEGACY_TABLE_PREAMBLE",
        "CANONICAL_TABLE_PREAMBLE",
        "LONGTABLE_SUPPORT_PROJECTION",
        "LEGACY_IMAGE_PREAMBLE",
        "CANONICAL_IMAGE_PREAMBLE",
        "LEGACY_CROSSWALK",
        "CANONICAL_CROSSWALK",
        "CROSSWALK_FRAME_PREFIX",
        "CROSSWALK_FRAME_SUFFIX",
        "DOCUMENT_BEGIN",
        "DOCUMENT_END",
        "TOP_LEVEL_HEADING_IDS",
    }
)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"Pandoc TeX normalizer self-test failed: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


try:
    PHYSICAL_TEMP_ROOT = pathlib.Path(tempfile.gettempdir()).resolve(strict=True)
except OSError as error:
    fail(f"cannot resolve the platform temporary directory: {error}")
require(
    PHYSICAL_TEMP_ROOT.is_dir() and not PHYSICAL_TEMP_ROOT.is_symlink(),
    "resolved platform temporary directory is not a physical directory",
)


def read_bound_constants(path: pathlib.Path) -> dict[str, object]:
    """Read literal contract constants without executing the production module."""

    require(path.is_file() and not path.is_symlink(), "production normalizer is not regular")
    try:
        source = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        fail(f"cannot read production normalizer as UTF-8: {error}")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        fail(f"production normalizer is not valid Python: {error}")

    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in REQUIRED_CONSTANTS:
            continue
        require(target.id not in values, f"duplicate bound constant: {target.id}")
        try:
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "frozenset"
                and len(node.value.args) == 1
                and not node.value.keywords
            ):
                literal_items = ast.literal_eval(node.value.args[0])
                require(
                    isinstance(literal_items, (set, tuple, list)),
                    f"frozenset constant has wrong literal payload: {target.id}",
                )
                values[target.id] = frozenset(literal_items)
            else:
                values[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError) as error:
            fail(f"bound constant is not literal: {target.id}: {error}")

    missing = sorted(REQUIRED_CONSTANTS.difference(values))
    require(not missing, f"production normalizer lost bound constants: {missing}")
    return values


CONTRACT = read_bound_constants(NORMALIZER)
MAX_INPUT_BYTES = CONTRACT["MAX_INPUT_BYTES"]
LEGACY_PANDOC_VERSION = CONTRACT["LEGACY_PANDOC_VERSION"]
CANONICAL_PANDOC_VERSION = CONTRACT["CANONICAL_PANDOC_VERSION"]
EXPECTED_HEADING_IDS = CONTRACT["EXPECTED_HEADING_IDS"]
TABLE_WRAPPER = CONTRACT["TABLE_WRAPPER"]
NONE_COUNTER = CONTRACT["NONE_COUNTER"]
LONGTABLE_BEGIN = CONTRACT["LONGTABLE_BEGIN"]
LONGTABLE_END = CONTRACT["LONGTABLE_END"]
LEGACY_TABLE_PREAMBLE = CONTRACT["LEGACY_TABLE_PREAMBLE"]
CANONICAL_TABLE_PREAMBLE = CONTRACT["CANONICAL_TABLE_PREAMBLE"]
LONGTABLE_SUPPORT_PROJECTION = CONTRACT["LONGTABLE_SUPPORT_PROJECTION"]
LEGACY_IMAGE_PREAMBLE = CONTRACT["LEGACY_IMAGE_PREAMBLE"]
CANONICAL_IMAGE_PREAMBLE = CONTRACT["CANONICAL_IMAGE_PREAMBLE"]
LEGACY_CROSSWALK = CONTRACT["LEGACY_CROSSWALK"]
CANONICAL_CROSSWALK = CONTRACT["CANONICAL_CROSSWALK"]
CROSSWALK_FRAME_PREFIX = CONTRACT["CROSSWALK_FRAME_PREFIX"]
CROSSWALK_FRAME_SUFFIX = CONTRACT["CROSSWALK_FRAME_SUFFIX"]
DOCUMENT_BEGIN = CONTRACT["DOCUMENT_BEGIN"]
DOCUMENT_END = CONTRACT["DOCUMENT_END"]
TOP_LEVEL_HEADING_IDS = CONTRACT["TOP_LEVEL_HEADING_IDS"]

require(isinstance(MAX_INPUT_BYTES, int) and MAX_INPUT_BYTES > 0, "bad byte bound")
require(isinstance(LEGACY_PANDOC_VERSION, str), "bad legacy version constant")
require(
    isinstance(EXPECTED_HEADING_IDS, tuple)
    and len(EXPECTED_HEADING_IDS) > 0
    and all(isinstance(item, str) and item for item in EXPECTED_HEADING_IDS),
    "bad expected-heading-ID constant",
)
for constant_name in (
    "TABLE_WRAPPER",
    "NONE_COUNTER",
    "LONGTABLE_BEGIN",
    "LONGTABLE_END",
    "LEGACY_TABLE_PREAMBLE",
    "CANONICAL_TABLE_PREAMBLE",
    "LONGTABLE_SUPPORT_PROJECTION",
    "LEGACY_IMAGE_PREAMBLE",
    "CANONICAL_IMAGE_PREAMBLE",
    "LEGACY_CROSSWALK",
    "CANONICAL_CROSSWALK",
    "CROSSWALK_FRAME_PREFIX",
    "CROSSWALK_FRAME_SUFFIX",
    "DOCUMENT_BEGIN",
    "DOCUMENT_END",
):
    require(isinstance(CONTRACT[constant_name], str), f"bad string constant: {constant_name}")


TABLE_COUNT = 4


def canonical_heading(index: int, heading_id: str) -> str:
    command = (
        "section"
        if heading_id in TOP_LEVEL_HEADING_IDS
        else "subsection"
    )
    return f"\\{command}{{Synthetic heading {index:02d}}}\\label{{{heading_id}}}\n"


def canonical_table(index: int) -> str:
    return (
        TABLE_WRAPPER
        + LONGTABLE_BEGIN
        + f"synthetic-{index} & value-{index} \\\\\n"
        + LONGTABLE_END
        + "}\n"
    )


def legacy_table(index: int) -> str:
    return (
        LONGTABLE_BEGIN
        + f"synthetic-{index} & value-{index} \\\\\n"
        + LONGTABLE_END
    )


def build_canonical_fixture() -> str:
    parts = [
        "\\documentclass{article}\n",
        CANONICAL_TABLE_PREAMBLE,
        LONGTABLE_SUPPORT_PROJECTION,
        CANONICAL_IMAGE_PREAMBLE,
        DOCUMENT_BEGIN,
    ]
    parts.extend(
        canonical_heading(index, heading_id)
        for index, heading_id in enumerate(EXPECTED_HEADING_IDS, start=1)
    )
    parts.extend(canonical_table(index) for index in range(1, TABLE_COUNT + 1))
    parts.extend(
        (
            CROSSWALK_FRAME_PREFIX,
            CANONICAL_CROSSWALK,
            CROSSWALK_FRAME_SUFFIX,
            "% synthetic canonical trailer\n",
            DOCUMENT_END,
        )
    )
    return "".join(parts)


def build_legacy_fixture() -> str:
    parts = [
        "\\documentclass{article}\n",
        LEGACY_TABLE_PREAMBLE,
        LONGTABLE_SUPPORT_PROJECTION,
        LEGACY_IMAGE_PREAMBLE,
        DOCUMENT_BEGIN,
    ]
    for index, heading_id in enumerate(EXPECTED_HEADING_IDS, start=1):
        parts.append(f"\\hypertarget{{{heading_id}}}{{%\n")
        parts.append(canonical_heading(index, heading_id).removesuffix("\n") + "}\n")
    parts.extend(legacy_table(index) for index in range(1, TABLE_COUNT + 1))
    parts.extend(
        (
            CROSSWALK_FRAME_PREFIX,
            LEGACY_CROSSWALK,
            CROSSWALK_FRAME_SUFFIX,
            "% synthetic canonical trailer\n",
            DOCUMENT_END,
        )
    )
    return "".join(parts)


CANONICAL_FIXTURE = build_canonical_fixture()
LEGACY_FIXTURE = build_legacy_fixture()


def replace_exactly_once(text: str, old: str, new: str, name: str) -> str:
    require(text.count(old) == 1, f"{name}: mutation anchor is not unique")
    mutated = text.replace(old, new, 1)
    require(mutated != text, f"{name}: mutation made no change")
    return mutated


def remove_nth(text: str, token: str, index: int, name: str) -> str:
    require(index >= 0, f"{name}: negative occurrence index")
    cursor = 0
    position = -1
    for _ in range(index + 1):
        position = text.find(token, cursor)
        require(position >= 0, f"{name}: occurrence is absent")
        cursor = position + len(token)
    return text[:position] + text[position + len(token) :]


def replace_nth(text: str, token: str, replacement: str, index: int, name: str) -> str:
    require(index >= 0, f"{name}: negative occurrence index")
    cursor = 0
    position = -1
    for _ in range(index + 1):
        position = text.find(token, cursor)
        require(position >= 0, f"{name}: occurrence is absent")
        cursor = position + len(token)
    mutated = text[:position] + replacement + text[position + len(token) :]
    require(mutated != text, f"{name}: mutation made no change")
    return mutated


def swap_exact_blocks(text: str, first: str, second: str, name: str) -> str:
    require(text.count(first) == 1, f"{name}: first block is not unique")
    require(text.count(second) == 1, f"{name}: second block is not unique")
    sentinel = "__PID_RS_SYNTHETIC_SWAP_SENTINEL__"
    require(sentinel not in text, f"{name}: swap sentinel collision")
    return text.replace(first, sentinel, 1).replace(second, first, 1).replace(
        sentinel, second, 1
    )


@dataclass(frozen=True)
class ContentCase:
    name: str
    version: str
    data: bytes


def encoded(name: str, version: str, text: str) -> ContentCase:
    return ContentCase(name, version, text.encode("utf-8"))


def content_cases() -> list[ContentCase]:
    cases: list[ContentCase] = []
    first_id = EXPECTED_HEADING_IDS[0]
    second_id = EXPECTED_HEADING_IDS[1]
    first_wrapper = f"\\hypertarget{{{first_id}}}{{%\n"
    first_canonical_heading = canonical_heading(1, first_id)
    first_legacy_heading = first_canonical_heading.removesuffix("\n") + "}\n"
    second_wrapper = f"\\hypertarget{{{second_id}}}{{%\n"
    second_canonical_heading = canonical_heading(2, second_id)
    second_legacy_heading = second_canonical_heading.removesuffix("\n") + "}\n"
    first_block = first_wrapper + first_legacy_heading
    second_block = second_wrapper + second_legacy_heading

    def add(name: str, version: str, text: str) -> None:
        cases.append(encoded(name, version, text))

    add(
        "mixed_legacy_table_wrapper",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(LONGTABLE_BEGIN, TABLE_WRAPPER + LONGTABLE_BEGIN, 1),
    )
    add(
        "mixed_canonical_heading_wrapper",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(
            first_canonical_heading, first_wrapper + first_canonical_heading, 1
        ),
    )
    add(
        "wrong_heading_wrapper_id",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            first_wrapper,
            "\\hypertarget{not-an-audited-heading}{%\n",
            "wrong_heading_wrapper_id",
        ),
    )
    add(
        "reordered_heading_blocks",
        LEGACY_PANDOC_VERSION,
        swap_exact_blocks(
            LEGACY_FIXTURE, first_block, second_block, "reordered_heading_blocks"
        ),
    )
    add(
        "missing_heading_wrapper",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE, first_wrapper, "", "missing_heading_wrapper"
        ),
    )
    add(
        "duplicate_heading_wrapper",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            first_wrapper,
            first_wrapper + first_wrapper,
            "duplicate_heading_wrapper",
        ),
    )
    add(
        "malformed_heading_wrapper",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            first_wrapper,
            f"\\hypertarget{{{first_id}}}{{\n",
            "malformed_heading_wrapper",
        ),
    )
    labels_swapped = LEGACY_FIXTURE.replace(
        f"\\label{{{first_id}}}", "\\label{__SWAP_ID__}", 1
    )
    labels_swapped = labels_swapped.replace(
        f"\\label{{{second_id}}}", f"\\label{{{first_id}}}", 1
    ).replace("\\label{__SWAP_ID__}", f"\\label{{{second_id}}}", 1)
    add("reordered_heading_labels", LEGACY_PANDOC_VERSION, labels_swapped)
    add(
        "nonterminal_heading_label",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            first_legacy_heading,
            first_legacy_heading.removesuffix("\n") + "% drift\n",
            "nonterminal_heading_label",
        ),
    )
    add(
        "missing_heading_label",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            f"\\label{{{first_id}}}",
            "",
            "missing_heading_label",
        ),
    )
    add(
        "duplicate_heading_label",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            first_canonical_heading,
            first_canonical_heading + f"\\label{{{first_id}}}\n",
            "duplicate_heading_label",
        ),
    )
    add(
        "wrong_heading_label",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            f"\\label{{{first_id}}}",
            "\\label{not-an-audited-heading}",
            "wrong_heading_label",
        ),
    )
    add(
        "canonical_stray_hypertarget",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE + "\\hypertarget{hostile}{payload}\n",
    )
    add(
        "canonical_wrong_heading_command",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            first_canonical_heading,
            first_canonical_heading.replace("\\section{", "\\subsection{", 1),
            "canonical_wrong_heading_command",
        ),
    )

    add(
        "legacy_missing_table_begin",
        LEGACY_PANDOC_VERSION,
        remove_nth(LEGACY_FIXTURE, LONGTABLE_BEGIN, 0, "legacy_missing_table_begin"),
    )
    add(
        "legacy_duplicate_table_begin",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(LONGTABLE_BEGIN, LONGTABLE_BEGIN * 2, 1),
    )
    first_legacy_table = legacy_table(1)
    reordered_legacy_table = (
        LONGTABLE_END
        + "synthetic-1 & value-1 \\\\\n"
        + LONGTABLE_BEGIN
    )
    add(
        "legacy_reordered_table_begin_end",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            first_legacy_table,
            reordered_legacy_table,
            "legacy_reordered_table_begin_end",
        ),
    )
    add(
        "legacy_changed_table_begin",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(LONGTABLE_BEGIN, "\\begin{longtable}[c]{@{}ll@{}}\n", 1),
    )
    add(
        "legacy_missing_table_end",
        LEGACY_PANDOC_VERSION,
        remove_nth(LEGACY_FIXTURE, LONGTABLE_END, 0, "legacy_missing_table_end"),
    )
    add(
        "legacy_duplicate_table_end",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(LONGTABLE_END, LONGTABLE_END * 2, 1),
    )
    add(
        "legacy_changed_table_end",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(LONGTABLE_END, "\\end{longtable} % drift\n", 1),
    )
    add(
        "legacy_missing_longtable_preamble",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_TABLE_PREAMBLE,
            "",
            "legacy_missing_longtable_preamble",
        ),
    )
    add(
        "legacy_duplicate_longtable_preamble",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_TABLE_PREAMBLE,
            LEGACY_TABLE_PREAMBLE * 2,
            "legacy_duplicate_longtable_preamble",
        ),
    )
    legacy_without_preamble = replace_exactly_once(
        LEGACY_FIXTURE,
        LEGACY_TABLE_PREAMBLE,
        "",
        "legacy_relocated_longtable_preamble",
    )
    add(
        "legacy_relocated_longtable_preamble",
        LEGACY_PANDOC_VERSION,
        legacy_without_preamble.replace(
            DOCUMENT_BEGIN, DOCUMENT_BEGIN + LEGACY_TABLE_PREAMBLE, 1
        ),
    )
    add(
        "legacy_missing_complete_table",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE, legacy_table(1), "", "legacy_missing_complete_table"
        ),
    )
    add(
        "legacy_extra_complete_table",
        LEGACY_PANDOC_VERSION,
        LEGACY_FIXTURE.replace(legacy_table(1), legacy_table(1) * 2, 1),
    )

    add(
        "canonical_missing_table_wrapper",
        CANONICAL_PANDOC_VERSION,
        remove_nth(CANONICAL_FIXTURE, TABLE_WRAPPER, 0, "canonical_missing_table_wrapper"),
    )
    add(
        "canonical_duplicate_table_wrapper",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(TABLE_WRAPPER, TABLE_WRAPPER * 2, 1),
    )
    add(
        "canonical_changed_table_wrapper",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(
            TABLE_WRAPPER,
            TABLE_WRAPPER.replace("do not increment", "never increment"),
            1,
        ),
    )
    canonical_without_wrapper = remove_nth(
        CANONICAL_FIXTURE, TABLE_WRAPPER, 0, "canonical_relocated_table_wrapper"
    )
    add(
        "canonical_relocated_table_wrapper",
        CANONICAL_PANDOC_VERSION,
        canonical_without_wrapper.replace(
            "% synthetic canonical trailer\n",
            TABLE_WRAPPER + "% synthetic canonical trailer\n",
            1,
        ),
    )
    add(
        "canonical_missing_none_counter",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            NONE_COUNTER,
            "",
            "canonical_missing_none_counter",
        ),
    )
    add(
        "canonical_duplicate_none_counter",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            NONE_COUNTER,
            NONE_COUNTER * 2,
            "canonical_duplicate_none_counter",
        ),
    )
    add(
        "canonical_missing_table_begin",
        CANONICAL_PANDOC_VERSION,
        remove_nth(CANONICAL_FIXTURE, LONGTABLE_BEGIN, 0, "canonical_missing_table_begin"),
    )
    add(
        "canonical_duplicate_table_begin",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(LONGTABLE_BEGIN, LONGTABLE_BEGIN * 2, 1),
    )
    first_canonical_table = canonical_table(1)
    reordered_canonical_table = (
        TABLE_WRAPPER
        + LONGTABLE_END
        + "synthetic-1 & value-1 \\\\\n"
        + LONGTABLE_BEGIN
        + "}\n"
    )
    add(
        "canonical_reordered_table_begin_end",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            first_canonical_table,
            reordered_canonical_table,
            "canonical_reordered_table_begin_end",
        ),
    )
    add(
        "canonical_missing_table_end",
        CANONICAL_PANDOC_VERSION,
        remove_nth(CANONICAL_FIXTURE, LONGTABLE_END, 0, "canonical_missing_table_end"),
    )
    add(
        "canonical_duplicate_table_end",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(LONGTABLE_END, LONGTABLE_END * 2, 1),
    )
    add(
        "canonical_missing_table_close",
        CANONICAL_PANDOC_VERSION,
        replace_nth(
            CANONICAL_FIXTURE,
            LONGTABLE_END + "}\n",
            LONGTABLE_END,
            0,
            "canonical_missing_table_close",
        ),
    )
    add(
        "canonical_changed_longtable_preamble",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_TABLE_PREAMBLE,
            CANONICAL_TABLE_PREAMBLE.replace(
                "\\captionsetup[table]{skip=6pt}",
                "\\captionsetup[table]{skip=7pt}",
                1,
            ),
            "canonical_changed_longtable_preamble",
        ),
    )
    add(
        "canonical_duplicate_longtable_preamble",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_TABLE_PREAMBLE,
            CANONICAL_TABLE_PREAMBLE * 2,
            "canonical_duplicate_longtable_preamble",
        ),
    )
    canonical_without_preamble = replace_exactly_once(
        CANONICAL_FIXTURE,
        CANONICAL_TABLE_PREAMBLE,
        "",
        "canonical_relocated_longtable_preamble",
    )
    add(
        "canonical_relocated_longtable_preamble",
        CANONICAL_PANDOC_VERSION,
        canonical_without_preamble.replace(
            DOCUMENT_BEGIN, DOCUMENT_BEGIN + CANONICAL_TABLE_PREAMBLE, 1
        ),
    )

    add(
        "legacy_image_preamble_drift",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_IMAGE_PREAMBLE,
            LEGACY_IMAGE_PREAMBLE.replace("Scale images", "Resize images", 1),
            "legacy_image_preamble_drift",
        ),
    )
    add(
        "legacy_image_preamble_removed",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_IMAGE_PREAMBLE,
            "",
            "legacy_image_preamble_removed",
        ),
    )
    add(
        "legacy_image_preamble_duplicate",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_IMAGE_PREAMBLE,
            LEGACY_IMAGE_PREAMBLE * 2,
            "legacy_image_preamble_duplicate",
        ),
    )
    add(
        "legacy_current_image_preamble",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_IMAGE_PREAMBLE,
            CANONICAL_IMAGE_PREAMBLE,
            "legacy_current_image_preamble",
        ),
    )
    legacy_without_image = replace_exactly_once(
        LEGACY_FIXTURE,
        LEGACY_IMAGE_PREAMBLE,
        "",
        "legacy_relocated_image_preamble",
    )
    add(
        "legacy_relocated_image_preamble",
        LEGACY_PANDOC_VERSION,
        legacy_without_image.replace(
            DOCUMENT_BEGIN, DOCUMENT_BEGIN + LEGACY_IMAGE_PREAMBLE, 1
        ),
    )
    add(
        "canonical_image_preamble_drift",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_IMAGE_PREAMBLE,
            CANONICAL_IMAGE_PREAMBLE.replace("scales image", "resizes image", 1),
            "canonical_image_preamble_drift",
        ),
    )
    add(
        "canonical_image_preamble_removed",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_IMAGE_PREAMBLE,
            "",
            "canonical_image_preamble_removed",
        ),
    )
    add(
        "canonical_image_preamble_duplicate",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_IMAGE_PREAMBLE,
            CANONICAL_IMAGE_PREAMBLE * 2,
            "canonical_image_preamble_duplicate",
        ),
    )
    add(
        "canonical_legacy_image_preamble",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_IMAGE_PREAMBLE,
            LEGACY_IMAGE_PREAMBLE,
            "canonical_legacy_image_preamble",
        ),
    )
    canonical_without_image = replace_exactly_once(
        CANONICAL_FIXTURE,
        CANONICAL_IMAGE_PREAMBLE,
        "",
        "canonical_relocated_image_preamble",
    )
    add(
        "canonical_relocated_image_preamble",
        CANONICAL_PANDOC_VERSION,
        canonical_without_image.replace(
            DOCUMENT_BEGIN, DOCUMENT_BEGIN + CANONICAL_IMAGE_PREAMBLE, 1
        ),
    )

    add(
        "legacy_crosswalk_path_drift",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_CROSSWALK,
            LEGACY_CROSSWALK.replace("audit-coordinate-crosswalk", "wrong-crosswalk", 1),
            "legacy_crosswalk_path_drift",
        ),
    )
    add(
        "legacy_crosswalk_removed",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE, LEGACY_CROSSWALK, "", "legacy_crosswalk_removed"
        ),
    )
    add(
        "legacy_crosswalk_duplicate",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_CROSSWALK,
            LEGACY_CROSSWALK * 2,
            "legacy_crosswalk_duplicate",
        ),
    )
    add(
        "legacy_current_crosswalk",
        LEGACY_PANDOC_VERSION,
        replace_exactly_once(
            LEGACY_FIXTURE,
            LEGACY_CROSSWALK,
            CANONICAL_CROSSWALK,
            "legacy_current_crosswalk",
        ),
    )
    add(
        "canonical_crosswalk_alt_drift",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            CANONICAL_CROSSWALK.replace("The 108 audit", "The 109 audit", 1),
            "canonical_crosswalk_alt_drift",
        ),
    )
    alt_start = CANONICAL_CROSSWALK.find(",alt={")
    alt_end = CANONICAL_CROSSWALK.find("}]", alt_start)
    require(alt_start >= 0 and alt_end > alt_start, "canonical alt-text anchor changed")
    without_alt = (
        CANONICAL_CROSSWALK[:alt_start] + "]" + CANONICAL_CROSSWALK[alt_end + 2 :]
    )
    add(
        "canonical_crosswalk_alt_removed",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            without_alt,
            "canonical_crosswalk_alt_removed",
        ),
    )
    add(
        "canonical_crosswalk_path_drift",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            CANONICAL_CROSSWALK.replace("audit-coordinate-crosswalk", "wrong-crosswalk", 1),
            "canonical_crosswalk_path_drift",
        ),
    )
    add(
        "canonical_crosswalk_removed",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            "",
            "canonical_crosswalk_removed",
        ),
    )
    add(
        "canonical_crosswalk_duplicate",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            CANONICAL_CROSSWALK * 2,
            "canonical_crosswalk_duplicate",
        ),
    )
    add(
        "canonical_legacy_crosswalk",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CANONICAL_CROSSWALK,
            LEGACY_CROSSWALK,
            "canonical_legacy_crosswalk",
        ),
    )
    add(
        "canonical_crosswalk_frame_prefix_removed",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            CROSSWALK_FRAME_PREFIX,
            "",
            "canonical_crosswalk_frame_prefix_removed",
        ),
    )
    canonical_without_crosswalk_frame = replace_exactly_once(
        CANONICAL_FIXTURE,
        CROSSWALK_FRAME_PREFIX + CANONICAL_CROSSWALK + CROSSWALK_FRAME_SUFFIX,
        "",
        "canonical_crosswalk_frame_relocated",
    )
    add(
        "canonical_crosswalk_frame_relocated",
        CANONICAL_PANDOC_VERSION,
        canonical_without_crosswalk_frame.replace(
            DOCUMENT_END,
            DOCUMENT_END
            + CROSSWALK_FRAME_PREFIX
            + CANONICAL_CROSSWALK
            + CROSSWALK_FRAME_SUFFIX,
            1,
        ),
    )

    add(
        "document_begin_removed",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE, DOCUMENT_BEGIN, "", "document_begin_removed"
        ),
    )
    add(
        "document_begin_duplicated",
        CANONICAL_PANDOC_VERSION,
        replace_exactly_once(
            CANONICAL_FIXTURE,
            DOCUMENT_BEGIN,
            DOCUMENT_BEGIN * 2,
            "document_begin_duplicated",
        ),
    )
    add(
        "document_markers_reordered",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE.replace(DOCUMENT_BEGIN, "__DOCUMENT_BEGIN__", 1)
        .replace(DOCUMENT_END, DOCUMENT_BEGIN, 1)
        .replace("__DOCUMENT_BEGIN__", DOCUMENT_END, 1),
    )
    add(
        "content_appended_after_document_end",
        CANONICAL_PANDOC_VERSION,
        CANONICAL_FIXTURE + "% forbidden post-document content\n",
    )

    canonical_bytes = CANONICAL_FIXTURE.encode("utf-8")
    add("input_nul", CANONICAL_PANDOC_VERSION, CANONICAL_FIXTURE + "\x00")
    cases.append(
        ContentCase(
            "input_crlf",
            CANONICAL_PANDOC_VERSION,
            canonical_bytes.replace(b"\n", b"\r\n", 1),
        )
    )
    cases.append(
        ContentCase(
            "input_non_utf8", CANONICAL_PANDOC_VERSION, canonical_bytes + b"\xff\n"
        )
    )
    cases.append(
        ContentCase(
            "input_utf8_bom", CANONICAL_PANDOC_VERSION, b"\xef\xbb\xbf" + canonical_bytes
        )
    )
    cases.append(
        ContentCase("input_without_final_lf", CANONICAL_PANDOC_VERSION, canonical_bytes[:-1])
    )
    cases.append(ContentCase("input_empty", CANONICAL_PANDOC_VERSION, b""))
    cases.append(
        ContentCase(
            "input_oversize",
            CANONICAL_PANDOC_VERSION,
            b"x" * (MAX_INPUT_BYTES + 1),
        )
    )
    add(
        "legacy_shape_current_version",
        CANONICAL_PANDOC_VERSION,
        LEGACY_FIXTURE,
    )
    add(
        "current_shape_legacy_version",
        LEGACY_PANDOC_VERSION,
        CANONICAL_FIXTURE,
    )
    add("valid_but_unsupported_version", "pandoc 3.10.1", CANONICAL_FIXTURE)
    for index, bad_version in enumerate(
        (
            "",
            "Pandoc 3.10.2",
            "pandoc 3",
            "pandoc 3.10.2\n",
            "pandoc 3.10.2.1.9",
            " pandoc 3.10.2",
            "pandoc 3.10.2 --standalone",
            "pandoc v3.10.2",
        ),
        start=1,
    ):
        add(f"version_shape_{index:02d}", bad_version, CANONICAL_FIXTURE)

    names = [case.name for case in cases]
    require(len(names) == len(set(names)), "content-case names are not unique")
    return cases


@dataclass(frozen=True)
class Invocation:
    source: pathlib.Path
    destination: pathlib.Path
    verify_unchanged: Callable[[], None]


@dataclass(frozen=True)
class FilesystemCase:
    name: str
    setup: Callable[[pathlib.Path], Invocation]


def require_absent(path: pathlib.Path, name: str) -> None:
    require(not path.exists() and not path.is_symlink(), f"{name}: output was created")


def regular_input(root: pathlib.Path) -> pathlib.Path:
    source = root / "input.tex"
    source.write_bytes(CANONICAL_FIXTURE.encode("utf-8"))
    return source


def filesystem_cases() -> list[FilesystemCase]:
    def absent_input(root: pathlib.Path) -> Invocation:
        source = root / "absent.tex"
        destination = root / "output.tex"
        return Invocation(
            source,
            destination,
            lambda: require_absent(destination, "absent_input"),
        )

    def symbolic_input(root: pathlib.Path) -> Invocation:
        target = regular_input(root)
        source = root / "symbolic-input.tex"
        source.symlink_to(target.name)
        destination = root / "output.tex"

        def verify() -> None:
            require(source.is_symlink(), "symbolic_input: source link changed")
            require(source.readlink() == pathlib.Path(target.name), "symbolic_input: retargeted")
            require_absent(destination, "symbolic_input")

        return Invocation(source, destination, verify)

    def hardlinked_input(root: pathlib.Path) -> Invocation:
        target = regular_input(root)
        source = root / "hardlinked-input.tex"
        os.link(target, source)
        destination = root / "output.tex"

        def verify() -> None:
            require(target.stat().st_nlink == 2, "hardlinked_input: link count changed")
            require_absent(destination, "hardlinked_input")

        return Invocation(source, destination, verify)

    def directory_input(root: pathlib.Path) -> Invocation:
        source = root / "input-directory"
        source.mkdir()
        destination = root / "output.tex"
        return Invocation(
            source,
            destination,
            lambda: (
                require(source.is_dir(), "directory_input: source changed"),
                require_absent(destination, "directory_input"),
            ),
        )

    def fifo_input(root: pathlib.Path) -> Invocation:
        source = root / "input-fifo"
        os.mkfifo(source)
        destination = root / "output.tex"

        def verify() -> None:
            require(stat.S_ISFIFO(source.lstat().st_mode), "fifo_input: source changed")
            require_absent(destination, "fifo_input")

        return Invocation(source, destination, verify)

    def existing_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "output.tex"
        sentinel = b"do-not-overwrite\n"
        destination.write_bytes(sentinel)
        return Invocation(
            source,
            destination,
            lambda: require(
                destination.read_bytes() == sentinel, "existing_output: bytes changed"
            ),
        )

    def symbolic_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "output.tex"
        destination.symlink_to(source.name)

        def verify() -> None:
            require(destination.is_symlink(), "symbolic_output: link replaced")
            require(destination.readlink() == pathlib.Path(source.name), "symbolic_output: retargeted")

        return Invocation(source, destination, verify)

    def dangling_symbolic_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "output.tex"
        destination.symlink_to("absent-target.tex")

        def verify() -> None:
            require(destination.is_symlink(), "dangling_symbolic_output: link replaced")
            require(
                destination.readlink() == pathlib.Path("absent-target.tex"),
                "dangling_symbolic_output: retargeted",
            )

        return Invocation(source, destination, verify)

    def directory_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "output-directory"
        destination.mkdir()
        return Invocation(
            source,
            destination,
            lambda: require(destination.is_dir(), "directory_output: directory changed"),
        )

    def fifo_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "output-fifo"
        os.mkfifo(destination)
        return Invocation(
            source,
            destination,
            lambda: require(
                stat.S_ISFIFO(destination.lstat().st_mode), "fifo_output: FIFO changed"
            ),
        )

    def missing_output_parent(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "absent-parent" / "output.tex"
        return Invocation(
            source,
            destination,
            lambda: require(
                not destination.parent.exists(), "missing_output_parent: parent created"
            ),
        )

    def nondirectory_output_parent(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        parent = root / "parent-file"
        sentinel = b"parent sentinel\n"
        parent.write_bytes(sentinel)
        destination = parent / "output.tex"
        return Invocation(
            source,
            destination,
            lambda: require(
                parent.read_bytes() == sentinel,
                "nondirectory_output_parent: parent changed",
            ),
        )

    def symbolic_output_parent(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        target = root / "real-parent"
        target.mkdir()
        parent = root / "symbolic-parent"
        parent.symlink_to(target.name, target_is_directory=True)
        destination = parent / "output.tex"

        def verify() -> None:
            require(parent.is_symlink(), "symbolic_output_parent: parent link changed")
            require_absent(target / "output.tex", "symbolic_output_parent")

        return Invocation(source, destination, verify)

    def symbolic_input_parent(root: pathlib.Path) -> Invocation:
        target = root / "real-input-parent"
        target.mkdir()
        source_target = target / "input.tex"
        source_target.write_bytes(CANONICAL_FIXTURE.encode("utf-8"))
        parent = root / "symbolic-input-parent"
        parent.symlink_to(target.name, target_is_directory=True)
        source = parent / source_target.name
        destination = root / "output.tex"

        def verify() -> None:
            require(parent.is_symlink(), "symbolic_input_parent: parent link changed")
            require_absent(destination, "symbolic_input_parent")

        return Invocation(source, destination, verify)

    def same_existing_path(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        before = source.read_bytes()
        return Invocation(
            source,
            source,
            lambda: require(source.read_bytes() == before, "same_existing_path: source changed"),
        )

    def same_absent_path(root: pathlib.Path) -> Invocation:
        source = root / "same-absent.tex"
        return Invocation(
            source,
            source,
            lambda: require_absent(source, "same_absent_path"),
        )

    def hardlink_alias_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        destination = root / "hardlink-output.tex"
        os.link(source, destination)
        before = source.read_bytes()

        def verify() -> None:
            require(source.read_bytes() == before, "hardlink_alias_output: source changed")
            require(destination.stat().st_ino == source.stat().st_ino, "hardlink alias changed")
            require(source.stat().st_nlink == 2, "hardlink_alias_output: link count changed")

        return Invocation(source, destination, verify)

    def dotdot_alias_output(root: pathlib.Path) -> Invocation:
        source = regular_input(root)
        intermediate = root / "intermediate"
        intermediate.mkdir()
        destination = intermediate / ".." / source.name
        before = source.read_bytes()
        return Invocation(
            source,
            destination,
            lambda: require(source.read_bytes() == before, "dotdot_alias_output: source changed"),
        )

    cases = [
        FilesystemCase("absent_input", absent_input),
        FilesystemCase("symbolic_input", symbolic_input),
        FilesystemCase("hardlinked_input", hardlinked_input),
        FilesystemCase("directory_input", directory_input),
        FilesystemCase("fifo_input", fifo_input),
        FilesystemCase("existing_output", existing_output),
        FilesystemCase("symbolic_output", symbolic_output),
        FilesystemCase("dangling_symbolic_output", dangling_symbolic_output),
        FilesystemCase("directory_output", directory_output),
        FilesystemCase("fifo_output", fifo_output),
        FilesystemCase("missing_output_parent", missing_output_parent),
        FilesystemCase("nondirectory_output_parent", nondirectory_output_parent),
        FilesystemCase("symbolic_output_parent", symbolic_output_parent),
        FilesystemCase("symbolic_input_parent", symbolic_input_parent),
        FilesystemCase("same_existing_path", same_existing_path),
        FilesystemCase("same_absent_path", same_absent_path),
        FilesystemCase("hardlink_alias_output", hardlink_alias_output),
        FilesystemCase("dotdot_alias_output", dotdot_alias_output),
    ]
    names = [case.name for case in cases]
    require(len(names) == len(set(names)), "filesystem-case names are not unique")
    return cases


def normalizer_command(optimized: bool, *arguments: str) -> list[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", str(NORMALIZER), *arguments))
    return command


def invoke(optimized: bool, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            normalizer_command(optimized, *arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        fail(f"production normalizer timed out (optimized={optimized})")


def require_rejection(
    result: subprocess.CompletedProcess[bytes], name: str, optimized: bool
) -> None:
    mode = "optimized" if optimized else "normal"
    require(result.returncode == 1, f"{name}/{mode}: exit code was {result.returncode}")
    require(result.stdout == b"", f"{name}/{mode}: rejection wrote stdout")
    require(
        result.stderr.startswith(FAILURE_PREFIX),
        f"{name}/{mode}: rejection lost the fail-closed diagnostic",
    )


def run_positive_cases(optimized: bool) -> int:
    count = 0
    for name, version, source_text, expected_mode, expected_text in (
        (
            "canonical_identity",
            CANONICAL_PANDOC_VERSION,
            CANONICAL_FIXTURE,
            "canonical",
            CANONICAL_FIXTURE,
        ),
        (
            "legacy_semantic_equivalence",
            LEGACY_PANDOC_VERSION,
            LEGACY_FIXTURE,
            "legacy-3.1.3",
            CANONICAL_FIXTURE,
        ),
    ):
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-pandoc-tex-positive-", dir=PHYSICAL_TEMP_ROOT
        ) as raw_root:
            root = pathlib.Path(raw_root)
            source = root / "input.tex"
            destination = root / "output.tex"
            source_bytes = source_text.encode("utf-8")
            expected_bytes = expected_text.encode("utf-8")
            source.write_bytes(source_bytes)
            result = invoke(optimized, version, str(source), str(destination))
            mode = "optimized" if optimized else "normal"
            require(result.returncode == 0, f"{name}/{mode}: positive case failed")
            require(result.stderr == b"", f"{name}/{mode}: positive case wrote stderr")
            if expected_mode == "canonical":
                counters = (
                    "heading_wrappers_removed=0; table_wrappers_inserted=0; "
                    "none_counter_inserted=0; table_preamble_replaced=0; "
                    "image_preamble_replaced=0; crosswalk_projection_replaced=0; "
                    "byte_identity=yes"
                )
            else:
                counters = (
                    f"heading_wrappers_removed={len(EXPECTED_HEADING_IDS)}; "
                    f"table_wrappers_inserted={TABLE_COUNT}; none_counter_inserted=1; "
                    "table_preamble_replaced=1; image_preamble_replaced=1; "
                    "crosswalk_projection_replaced=1; byte_identity=no"
                )
            expected_stdout = (
                "OK: normalized mathematical-results guide Pandoc TeX "
                f"(mode={expected_mode}; {counters})\n"
            ).encode("utf-8")
            require(result.stdout == expected_stdout, f"{name}/{mode}: stdout changed")
            require(destination.is_file(), f"{name}/{mode}: output is absent")
            require(not destination.is_symlink(), f"{name}/{mode}: output is symbolic")
            require(destination.stat().st_nlink == 1, f"{name}/{mode}: output is linked")
            require(destination.read_bytes() == expected_bytes, f"{name}/{mode}: bytes differ")
            require(source.read_bytes() == source_bytes, f"{name}/{mode}: source was modified")
            if name == "canonical_identity":
                require(
                    destination.read_bytes() == source.read_bytes(),
                    f"{name}/{mode}: canonical projection is not byte-identical",
                )
            count += 1
    return count


def run_content_rejections(optimized: bool, cases: list[ContentCase]) -> int:
    count = 0
    for case in cases:
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-pandoc-tex-content-", dir=PHYSICAL_TEMP_ROOT
        ) as raw_root:
            root = pathlib.Path(raw_root)
            source = root / "input.tex"
            destination = root / "output.tex"
            source.write_bytes(case.data)
            result = invoke(optimized, case.version, str(source), str(destination))
            require_rejection(result, case.name, optimized)
            require_absent(destination, case.name)
            require(source.read_bytes() == case.data, f"{case.name}: source was modified")
            count += 1
    return count


def run_filesystem_rejections(optimized: bool, cases: list[FilesystemCase]) -> int:
    count = 0
    for case in cases:
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-pandoc-tex-filesystem-", dir=PHYSICAL_TEMP_ROOT
        ) as raw_root:
            root = pathlib.Path(raw_root)
            invocation = case.setup(root)
            result = invoke(
                optimized,
                CANONICAL_PANDOC_VERSION,
                str(invocation.source),
                str(invocation.destination),
            )
            require_rejection(result, case.name, optimized)
            invocation.verify_unchanged()
            count += 1
    return count


def run_usage_rejections(optimized: bool) -> int:
    argument_sets = (
        (),
        (CANONICAL_PANDOC_VERSION,),
        (CANONICAL_PANDOC_VERSION, "input.tex"),
        (CANONICAL_PANDOC_VERSION, "input.tex", "output.tex", "extra"),
    )
    for index, arguments in enumerate(argument_sets, start=1):
        result = invoke(optimized, *arguments)
        require_rejection(result, f"usage_shape_{index:02d}", optimized)
        require(b"usage:" in result.stderr, f"usage_shape_{index:02d}: usage text absent")
    return len(argument_sets)


def main() -> None:
    if len(sys.argv) != 1:
        fail(f"usage: {sys.argv[0]}")

    require(CANONICAL_FIXTURE.encode("utf-8") != LEGACY_FIXTURE.encode("utf-8"), "fixtures alias")
    require(CANONICAL_FIXTURE.endswith("\n"), "canonical fixture lacks final LF")
    require(LEGACY_FIXTURE.endswith("\n"), "legacy fixture lacks final LF")
    require(len(CANONICAL_FIXTURE.encode("utf-8")) < MAX_INPUT_BYTES, "canonical fixture too large")
    require(len(LEGACY_FIXTURE.encode("utf-8")) < MAX_INPUT_BYTES, "legacy fixture too large")

    hostile_content = content_cases()
    hostile_filesystems = filesystem_cases()
    positive = 0
    rejected = 0
    for optimized in (False, True):
        positive += run_positive_cases(optimized)
        rejected += run_content_rejections(optimized, hostile_content)
        rejected += run_filesystem_rejections(optimized, hostile_filesystems)
        rejected += run_usage_rejections(optimized)

    expected_positive = 2 * 2
    expected_rejected = 2 * (
        len(hostile_content) + len(hostile_filesystems) + 4
    )
    require(positive == expected_positive, "positive process count changed")
    require(rejected == expected_rejected, "rejection process count changed")
    print(
        "OK: Pandoc TeX normalizer self-test "
        f"(positive_processes={positive}; rejected_processes={rejected}; "
        f"content_vectors={len(hostile_content)}; "
        f"filesystem_vectors={len(hostile_filesystems)}; modes=2)"
    )


if __name__ == "__main__":
    main()
