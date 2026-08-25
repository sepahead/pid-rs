#!/usr/bin/env python3
"""Bind P5's bounded audit key order to the narrow Rust SxPID3 lexical route.

This checker deliberately stops at reviewed source text.  It verifies that the P5 bounded checker
names and hashes the canonical three-source antichain helper, and that the current Rust SxPID3
implementation imports that helper and carries its order through the collection projection, both
pointwise Mobius inversions, and the aligned ``DiscreteSxPid3Result`` fields.

The 108 objects in the bounded audit are keyed scalar expressions: 18 antichain positions times
two representation stages (cumulative values and Mobius atoms) times three components
(informative/misinformative/net).  They are not 108 lattice nodes or 108 PID atoms.  This lane
provides only lexical custody for the shared 18-key carrier and the Rust result's positional route.
It conservatively rejects module-level inner ``cfg``/``cfg_attr`` and unexpected explicit outer
attributes on the five claimed constructs; this is not a full Rust parser or configuration
evaluator.  It does not compare a Rust numeric result, prove Rust name resolution or compilation,
establish binary64 refinement, or say anything about ``discrete_sxpid_n`` or I_min.  ``GO`` means
only that this lane's local lexical obligations hold; it is not scientific validation and
establishes no commit/release identity, source authenticity, or artifact authenticity.
"""

from __future__ import annotations

# Exact checker bytes are pinned by the companion self-test.
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Final, Sequence


FORMAT: Final[str] = "/pid-rs/sxpid3-p5-rust-source-route/v2"
MANIFEST_FORMAT: Final[str] = "/pid-rs/sxpid3-p5-rust-source-route-manifest/v2"
DISCRETE_PID_RELATIVE: Final[str] = "crates/pid-core/src/discrete_pid.rs"
SXPID_RELATIVE: Final[str] = "crates/pid-core/src/sxpid.rs"
PRIMARY_CHECKER_RELATIVE: Final[str] = (
    "scripts/check-sxpid3-bounded-full-coordinates.py"
)
SELF_RELATIVE: Final[str] = "scripts/check-sxpid3-p5-rust-source-route.py"
HELPER_NAME: Final[str] = "discrete_antichains_3"
TARGET_FUNCTION: Final[str] = "sxpid3_from_states_with_cancellation"
TARGET_RESULT: Final[str] = "DiscreteSxPid3Result"
EXPECTED_HELPER_SHA256: Final[str] = (
    "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb07"
)
EXPECTED_PRIMARY_ROUTE_HELPER_AST_SHA256: Final[str] = (
    "0b7921dc355f60001bbae651b03d47bb38422b5d6c23ac4b6b46b799e91fdc36"
)
EXPECTED_PRIMARY_CHECKER_SOURCE_SHA256: Final[str] = (
    "d9d1c540930855b31f8190fdb2095d215c736f6f6c3d19c60e2a353923be06d2"
)
EXPECTED_ROUTE_MANIFEST_SHA256: Final[str] = (
    "e0ef5a05bbade1ccbd83767ee0e1e39f05276790bb2b433dd8e5fff7ea83046a"
)
EXPECTED_RUST_STABLE_KEYS: Final[tuple[str, ...]] = (
    "01",
    "02",
    "04",
    "03",
    "05",
    "06",
    "07",
    "01+02",
    "01+04",
    "01+06",
    "02+04",
    "02+05",
    "03+04",
    "03+05",
    "03+06",
    "05+06",
    "01+02+04",
    "03+05+06",
)
BOUNDARIES: Final[tuple[str, ...]] = (
    "lexical_source_route_only",
    "rust_name_resolution_not_formally_verified",
    "compiled_rust_refinement_open",
    "rust_numeric_values_not_compared",
    "binary64_refinement_not_established",
    "108_keyed_scalar_audit_expressions_not_108_atoms_or_nodes",
    "108_keyed_scalar_audit_expressions_not_108_independent_degrees_of_freedom",
    "git_commit_identity_not_established",
    "release_identity_not_established",
    "source_authenticity_not_established",
    "artifact_authenticity_not_established",
    "GO_is_lane_local_lexical_obligations_only_not_scientific_validation",
    "bounded_repeated_read_race_detection_not_atomic_snapshot_live_monitor_or_authenticity",
    "claimed_construct_outer_attributes_are_exactly_bounded",
    "module_level_inner_cfg_and_cfg_attr_are_rejected",
    "attribute_guard_is_conservative_lexical_not_full_Rust_parsing_or_cfg_evaluation",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def require_isolated_python() -> None:
    require(sys.implementation.name == "cpython", "PYTHON.implementation")
    require(sys.version_info >= (3, 11), "PYTHON.minimum_version")
    require(sys.flags.ignore_environment == 1, "PYTHON.ignore_environment")
    require(sys.flags.safe_path == 1, "PYTHON.safe_path")
    require(sys.flags.isolated == 1, "PYTHON.isolated")
    require(sys.flags.no_site == 1, "PYTHON.no_site")
    require(sys.flags.dont_write_bytecode == 1, "PYTHON.dont_write_bytecode")
    require(sys.flags.optimize in (0, 1), "PYTHON.optimize")


def canonical_json(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_sha256(value: object) -> str:
    return sha256_text(canonical_json(value))


def semantic_ast_value(value: object) -> object:
    if isinstance(value, ast.AST):
        field_names = tuple(value._fields)
        require(len(field_names) == len(set(field_names)), "AST.duplicate_field")
        fields: dict[str, object] = {}
        for field_name in sorted(field_names):
            field_value = getattr(value, field_name)
            if field_name == "type_params":
                require(isinstance(field_value, list), "AST.type_params_shape")
                require(not field_value, "AST.type_params_nonempty")
                continue
            fields[field_name] = semantic_ast_value(field_value)
        return {
            "fields": fields,
            "kind": "ast",
            "node_type": type(value).__name__,
        }
    if value is None:
        return {"kind": "none"}
    if isinstance(value, bool):
        return {"kind": "bool", "value": value}
    if isinstance(value, int):
        return {"kind": "int", "value": str(value)}
    if isinstance(value, float):
        return {"hex": value.hex(), "kind": "float"}
    if isinstance(value, complex):
        return {
            "imag_hex": value.imag.hex(),
            "kind": "complex",
            "real_hex": value.real.hex(),
        }
    if isinstance(value, str):
        return {"kind": "str", "value": value}
    if isinstance(value, bytes):
        return {"hex": value.hex(), "kind": "bytes"}
    if value is Ellipsis:
        return {"kind": "ellipsis"}
    if isinstance(value, list):
        return {"items": [semantic_ast_value(item) for item in value], "kind": "list"}
    if isinstance(value, tuple):
        return {
            "items": [semantic_ast_value(item) for item in value],
            "kind": "tuple",
        }
    raise RuntimeError(f"AST.unsupported_value:{type(value).__name__}")


def ast_identity(node: ast.AST) -> str:
    return canonical_json(semantic_ast_value(node))


def compact(source: str) -> str:
    return re.sub(r"\s+", "", source)


def mask_span(buffer: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if buffer[index] != "\n":
            buffer[index] = " "


def raw_string_end(source: str, start: int) -> int | None:
    """Return a Rust raw-string end offset when ``start`` begins at ``r`` or ``br``."""
    prefix = 1
    if source.startswith("br", start):
        prefix = 2
    elif not source.startswith("r", start):
        return None
    cursor = start + prefix
    hashes = 0
    while cursor < len(source) and source[cursor] == "#":
        hashes += 1
        cursor += 1
    if cursor >= len(source) or source[cursor] != '"':
        return None
    terminator = '"' + "#" * hashes
    close = source.find(terminator, cursor + 1)
    require(close >= 0, "RUST_LEXER.unterminated_raw_string")
    return close + len(terminator)


def quoted_end(source: str, quote: int, delimiter: str) -> int:
    cursor = quote + 1
    while cursor < len(source):
        if source[cursor] == "\\":
            cursor += 2
            continue
        if source[cursor] == delimiter:
            return cursor + 1
        cursor += 1
    raise RuntimeError("RUST_LEXER.unterminated_literal")


def char_literal_end(source: str, start: int) -> int | None:
    quote = start + 1 if source.startswith("b'", start) else start
    if quote >= len(source) or source[quote] != "'":
        return None
    cursor = quote + 1
    if cursor >= len(source) or source[cursor] in "\n\r'":
        return None
    if source[cursor] == "\\":
        cursor += 2
    else:
        cursor += 1
    if cursor < len(source) and source[cursor] == "'":
        return cursor + 1
    return None


def sanitize_rust(source: str) -> str:
    """Mask comments and literals while preserving offsets and newlines."""
    output = list(source)
    cursor = 0
    while cursor < len(source):
        if source.startswith("//", cursor):
            end = source.find("\n", cursor + 2)
            if end < 0:
                end = len(source)
            mask_span(output, cursor, end)
            cursor = end
            continue
        if source.startswith("/*", cursor):
            depth = 1
            end = cursor + 2
            while end < len(source) and depth:
                if source.startswith("/*", end):
                    depth += 1
                    end += 2
                elif source.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            require(depth == 0, "RUST_LEXER.unterminated_block_comment")
            mask_span(output, cursor, end)
            cursor = end
            continue
        raw_end = raw_string_end(source, cursor)
        if raw_end is not None:
            mask_span(output, cursor, raw_end)
            cursor = raw_end
            continue
        quote = cursor + 1 if source.startswith('b"', cursor) else cursor
        if quote < len(source) and source[quote] == '"':
            end = quoted_end(source, quote, '"')
            mask_span(output, cursor, end)
            cursor = end
            continue
        char_end = char_literal_end(source, cursor)
        if char_end is not None:
            mask_span(output, cursor, char_end)
            cursor = char_end
            continue
        cursor += 1
    return "".join(output)


def braced_end(sanitized: str, opening: int) -> int:
    require(
        0 <= opening < len(sanitized) and sanitized[opening] == "{",
        "RUST_SHAPE.open_brace",
    )
    depth = 0
    for index in range(opening, len(sanitized)):
        if sanitized[index] == "{":
            depth += 1
        elif sanitized[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise RuntimeError("RUST_SHAPE.unbalanced_brace")


def unique_named_block(
    source: str,
    sanitized: str,
    pattern: str,
    count_code: str,
) -> tuple[int, int, int]:
    matches = list(re.finditer(pattern, sanitized, flags=re.MULTILINE))
    require(len(matches) == 1, count_code)
    opening = sanitized.find("{", matches[0].end())
    require(opening >= 0, "RUST_SHAPE.missing_body")
    return matches[0].start(), opening, braced_end(sanitized, opening)


def rust_stable_key(row: Sequence[str]) -> str:
    return "+".join(
        f"{int(token.replace('_', ''), 2):02x}" for token in row if token != "0"
    )


def helper_binding(discrete_source: str) -> tuple[dict[str, object], tuple[str, ...]]:
    sanitized = sanitize_rust(discrete_source)
    start, opening, end = unique_named_block(
        discrete_source,
        sanitized,
        r"\bpub\s*\(\s*crate\s*\)\s+fn\s+discrete_antichains_3\s*\(",
        "HELPER.definition_count",
    )
    require(brace_depth(sanitized, start) == 0, "HELPER.module_scope")
    require_attached_outer_attributes(
        sanitized, start, (), "HELPER.attached_outer_attribute"
    )
    signature = compact(sanitized[start : opening + 1])
    require(
        signature == "pub(crate)fndiscrete_antichains_3()->[[u8;3];18]{",
        "HELPER.signature",
    )
    helper_source = discrete_source[start:end]
    helper_sanitized = sanitized[start:end]
    rows = re.findall(
        r"\[\s*(0b[01_]+|0)\s*,\s*(0b[01_]+|0)\s*,\s*(0b[01_]+|0)\s*\]\s*,",
        helper_sanitized,
    )
    require(len(rows) == 18, "HELPER.row_count")
    keys = tuple(rust_stable_key(row) for row in rows)
    require(keys == EXPECTED_RUST_STABLE_KEYS, "HELPER.stable_keys")
    helper_sha256 = sha256_text(helper_source)
    require(helper_sha256 == EXPECTED_HELPER_SHA256, "HELPER.sha256")
    anchor: dict[str, object] = {
        "hash_basis": "exact_utf8_function_source_without_leading_docs",
        "locator": "pub(crate) fn discrete_antichains_3() -> [[u8; 3]; 18]",
        "path": DISCRETE_PID_RELATIVE,
        "role": "canonical_positional_order_of_the_18_three_source_antichains",
        "sha256": helper_sha256,
    }
    return anchor, keys


def unique_assignment(
    tree: ast.Module, name: str, code: str
) -> ast.AnnAssign | ast.Assign:
    values: list[ast.AnnAssign | ast.Assign] = []
    for statement in tree.body:
        if isinstance(statement, ast.AnnAssign):
            if isinstance(statement.target, ast.Name) and statement.target.id == name:
                values.append(statement)
        elif isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in statement.targets
            ):
                values.append(statement)
    require(len(values) == 1, code)
    return values[0]


def assignment_value(statement: ast.AnnAssign | ast.Assign) -> ast.expr:
    value = statement.value
    if value is None:
        raise RuntimeError("PRIMARY_CHECKER.assignment_value")
    return value


def primary_checker_binding(
    checker_source: str, helper_sha256: str
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    tree = ast.parse(checker_source, filename=PRIMARY_CHECKER_RELATIVE)
    path_assignment = unique_assignment(
        tree, "RUST_ANTICHAIN_SOURCE", "PRIMARY_CHECKER.path_assignment_count"
    )
    hash_assignment = unique_assignment(
        tree,
        "EXPECTED_RUST_ANTICHAIN_FUNCTION_SHA256",
        "PRIMARY_CHECKER.helper_hash_assignment_count",
    )
    path_value = assignment_value(path_assignment)
    hash_value = assignment_value(hash_assignment)
    expected_path_value = ast.parse(
        'Path(__file__).resolve().parents[1] / "crates/pid-core/src/discrete_pid.rs"',
        mode="eval",
    ).body
    require(
        ast_identity(path_value) == ast_identity(expected_path_value),
        "PRIMARY_CHECKER.path_binding",
    )
    require(
        isinstance(hash_value, ast.Constant)
        and isinstance(hash_value.value, str)
        and hash_value.value == helper_sha256,
        "PRIMARY_CHECKER.helper_hash_binding",
    )
    helpers = [
        statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name == "rust_antichain_stable_keys"
    ]
    require(len(helpers) == 1, "PRIMARY_CHECKER.route_helper_count")
    helper_ast_identity = ast_identity(helpers[0])
    helper_ast_sha256 = sha256_text(helper_ast_identity)
    require(
        helper_ast_sha256 == EXPECTED_PRIMARY_ROUTE_HELPER_AST_SHA256,
        "PRIMARY_CHECKER.route_helper_ast",
    )
    path_ast_identity = ast_identity(path_value)
    hash_ast_identity = ast_identity(hash_value)
    checker_source_sha256 = sha256_text(checker_source)
    anchors: dict[str, dict[str, object]] = {
        "primary_checker_full_source_bytes": {
            "hash_basis": "exact_complete_utf8_source_bytes",
            "locator": "complete primary bounded-checker source",
            "path": PRIMARY_CHECKER_RELATIVE,
            "role": (
                "local_lexical_byte_identity_only_not_compilation_authenticity_commit_or_release_identity"
            ),
            "sha256": checker_source_sha256,
        },
        "primary_checker_helper_hash_ast": {
            "hash_basis": "version_neutral_semantic_python_ast_canonical_json_without_source_locations",
            "locator": "EXPECTED_RUST_ANTICHAIN_FUNCTION_SHA256",
            "path": PRIMARY_CHECKER_RELATIVE,
            "role": "declares_the_exact_helper_function_hash_consumed_by_the_bounded_checker",
            "sha256": sha256_text(hash_ast_identity),
        },
        "primary_checker_helper_route_ast": {
            "hash_basis": "version_neutral_semantic_python_ast_canonical_json_without_source_locations",
            "locator": "rust_antichain_stable_keys",
            "path": PRIMARY_CHECKER_RELATIVE,
            "role": "reads_hashes_parses_and_reconstructs_the_helpers_18_ordered_keys",
            "sha256": helper_ast_sha256,
        },
        "primary_checker_path_ast": {
            "hash_basis": "version_neutral_semantic_python_ast_canonical_json_without_source_locations",
            "locator": "RUST_ANTICHAIN_SOURCE",
            "path": PRIMARY_CHECKER_RELATIVE,
            "role": "routes_the_bounded_checker_to_the_discrete_pid_helper_source_file",
            "sha256": sha256_text(path_ast_identity),
        },
    }
    binding: dict[str, object] = {
        "complete_source_sha256": checker_source_sha256,
        "declared_helper_function_sha256": helper_sha256,
        "declared_rust_source_path": DISCRETE_PID_RELATIVE,
        "helper_hash_value_ast_sha256": sha256_text(hash_ast_identity),
        "path_expression_ast_sha256": sha256_text(path_ast_identity),
        "route_helper_ast_sha256": helper_ast_sha256,
    }
    return anchors, binding


def brace_depth(sanitized: str, stop: int) -> int:
    depth = 0
    for character in sanitized[:stop]:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
    return depth


def skip_rust_whitespace_backward(sanitized: str, stop: int) -> int:
    while stop > 0 and sanitized[stop - 1].isspace():
        stop -= 1
    return stop


def matching_open_square_backward(sanitized: str, close: int) -> int:
    require(
        0 <= close < len(sanitized) and sanitized[close] == "]",
        "RUST_ATTRIBUTE.close_square",
    )
    depth = 0
    for index in range(close, -1, -1):
        if sanitized[index] == "]":
            depth += 1
        elif sanitized[index] == "[":
            depth -= 1
            if depth == 0:
                return index
    raise RuntimeError("RUST_ATTRIBUTE.unbalanced_square")


def attached_outer_attributes(sanitized: str, item_start: int) -> tuple[str, ...]:
    """Return explicit ``#[...]`` tokens attached to an item, excluding doc comments."""
    reverse_attributes: list[str] = []
    cursor = item_start
    while True:
        attribute_end = skip_rust_whitespace_backward(sanitized, cursor)
        if attribute_end == 0 or sanitized[attribute_end - 1] != "]":
            break
        opening = matching_open_square_backward(sanitized, attribute_end - 1)
        hash_end = skip_rust_whitespace_backward(sanitized, opening)
        if hash_end == 0 or sanitized[hash_end - 1] != "#":
            break
        hash_start = hash_end - 1
        reverse_attributes.append(compact(sanitized[hash_start:attribute_end]))
        cursor = hash_start
    return tuple(reversed(reverse_attributes))


def require_attached_outer_attributes(
    sanitized: str,
    item_start: int,
    expected: tuple[str, ...],
    code: str,
) -> None:
    require(attached_outer_attributes(sanitized, item_start) == expected, code)


def reject_module_inner_cfg_attributes(source: str, code: str) -> None:
    sanitized = sanitize_rust(source)
    matches = re.finditer(
        r"#\s*!\s*\[\s*(?:r#)?(?:cfg_attr|cfg)(?=\s*(?:\(|\]|=))",
        sanitized,
        flags=re.MULTILINE,
    )
    require(
        not any(brace_depth(sanitized, match.start()) == 0 for match in matches),
        code,
    )


def import_binding(sxpid_sanitized: str) -> dict[str, dict[str, object]]:
    statements: list[tuple[int, str]] = []
    for match in re.finditer(r"(?m)^[ \t]*use\s+", sxpid_sanitized):
        end = sxpid_sanitized.find(";", match.end())
        require(end >= 0, "IMPORT.unterminated")
        statement = sxpid_sanitized[match.start() : end + 1]
        if re.search(
            r"\b(?:discrete_antichains_3|discrete_mobius_inversion_3)\b",
            statement,
        ):
            statements.append((match.start(), compact(statement)))
    require(len(statements) == 1, "IMPORT.definition_count")
    start, statement = statements[0]
    require(brace_depth(sxpid_sanitized, start) == 0, "IMPORT.module_scope")
    require_attached_outer_attributes(
        sxpid_sanitized, start, (), "IMPORT.attached_outer_attribute"
    )
    grouped = statement.startswith("usecrate::discrete_pid::{") and statement.endswith(
        "};"
    )
    require(grouped, "IMPORT.route")
    members = statement[len("usecrate::discrete_pid::{") : -2].split(",")
    require(members.count("discrete_antichains_3") == 1, "IMPORT.antichain_member")
    require(
        members.count("discrete_mobius_inversion_3") == 1,
        "IMPORT.mobius_member",
    )
    antichain_route = "use crate::discrete_pid::discrete_antichains_3"
    mobius_route = "use crate::discrete_pid::discrete_mobius_inversion_3"
    return {
        "antichain": {
            "hash_basis": "canonical_module_member_route",
            "locator": "module-scope unaliased import of discrete_antichains_3",
            "path": SXPID_RELATIVE,
            "role": "makes_the_canonical_antichain_helper_name_available_to_the_sxpid3_route",
            "sha256": sha256_text(antichain_route),
        },
        "mobius": {
            "hash_basis": "canonical_module_member_route",
            "locator": "module-scope unaliased import of discrete_mobius_inversion_3",
            "path": SXPID_RELATIVE,
            "role": (
                "lexically_connects_the_same_named_discrete_pid_mobius_member_without_name_resolution_or_compilation"
            ),
            "sha256": sha256_text(mobius_route),
        },
    }


def canonical_anchor(
    locator: str,
    role: str,
    canonical_lexeme: str,
    path: str = SXPID_RELATIVE,
) -> dict[str, object]:
    return {
        "hash_basis": "whitespace_free_comment_and_literal_masked_rust_lexeme",
        "locator": locator,
        "path": path,
        "role": role,
        "sha256": sha256_text(canonical_lexeme),
    }


def mobius_route_bindings(
    discrete_source: str,
) -> dict[str, dict[str, object]]:
    sanitized = sanitize_rust(discrete_source)
    start, opening, end = unique_named_block(
        discrete_source,
        sanitized,
        r"\bpub\s*\(\s*crate\s*\)\s+fn\s+discrete_mobius_inversion_3\s*\(",
        "MOBIUS.definition_count",
    )
    require(brace_depth(sanitized, start) == 0, "MOBIUS.module_scope")
    require_attached_outer_attributes(
        sanitized, start, (), "MOBIUS.attached_outer_attribute"
    )
    signature = compact(sanitized[start : opening + 1])
    expected_signature = (
        "pub(crate)fndiscrete_mobius_inversion_3("
        "antichains:&[[u8;3]],"
        "redundancies:&[f64],"
        ")->Vec<IminPid3Atom>{"
    )
    require(signature == expected_signature, "MOBIUS.signature")

    function_raw_source = discrete_source[start:end]
    function_compact = compact(sanitized[start:end])
    output_mapping = (
        "antichains.iter().enumerate().map(|(idx,ac)|{"
        "letsets:Vec<u8>=ac.iter().copied().filter(|&m|m!=0).collect();"
        "IminPid3Atom{antichain_sets:sets,value:atoms[idx],}"
        "}).collect()"
    )
    require(
        function_compact.endswith(output_mapping + "}"),
        "MOBIUS.output_mapping",
    )
    return {
        "mobius_full_function_bytes": {
            "hash_basis": "exact_complete_utf8_braced_function_bytes_without_leading_docs",
            "locator": "complete discrete_mobius_inversion_3 braced function",
            "path": DISCRETE_PID_RELATIVE,
            "role": (
                "local_lexical_function_byte_identity_only_not_compilation_authenticity_commit_or_release_identity"
            ),
            "sha256": sha256_text(function_raw_source),
        },
        "mobius_function_signature": canonical_anchor(
            "discrete_mobius_inversion_3 signature",
            "fixes_the_unique_three_source_inversion_input_and_output_types_lexically",
            expected_signature,
            DISCRETE_PID_RELATIVE,
        ),
        "mobius_output_mapping": canonical_anchor(
            "final antichains.iter().enumerate() output mapping",
            "returns_each_atoms_idx_value_at_the_same_enumerated_antichain_position_lexically",
            output_mapping,
            DISCRETE_PID_RELATIVE,
        ),
    }


def rust_route_bindings(sxpid_source: str) -> dict[str, dict[str, object]]:
    sanitized = sanitize_rust(sxpid_source)
    import_anchors = import_binding(sanitized)
    function_start, function_opening, function_end = unique_named_block(
        sxpid_source,
        sanitized,
        r"\bfn\s+sxpid3_from_states_with_cancellation\s*\(",
        "TARGET_FUNCTION.definition_count",
    )
    require(brace_depth(sanitized, function_start) == 0, "TARGET_FUNCTION.module_scope")
    require_attached_outer_attributes(
        sanitized,
        function_start,
        (),
        "TARGET_FUNCTION.attached_outer_attribute",
    )
    signature = compact(sanitized[function_start : function_opening + 1])
    expected_signature = (
        "fnsxpid3_from_states_with_cancellation("
        "source_states:[&[Vec<usize>];3],"
        "target_states:&[Vec<usize>],"
        "encoding:DiscreteInputEncoding,"
        "include_pointwise:bool,"
        "budget:ResourceBudget,"
        "cancellation:&CancellationToken,"
        ")->PidResult<DiscreteSxPid3Result>{"
    )
    require(signature == expected_signature, "TARGET_FUNCTION.signature")
    function_raw_source = sxpid_source[function_start:function_end]
    function_sanitized = sanitized[function_start:function_end]
    function_compact = compact(function_sanitized)

    global_calls = list(re.finditer(r"\bdiscrete_antichains_3\s*\(", sanitized))
    require(len(global_calls) == 1, "CALL.global_count")
    require(
        function_start <= global_calls[0].start() < function_end,
        "CALL.function_scope",
    )
    call = "letantichains=discrete_antichains_3();"
    require(function_compact.count(call) == 1, "CALL.shape")

    collection = (
        "letnode_collections:Vec<Vec<u8>>=antichains.iter().map("
        "|ac|ac.iter().copied().filter(|&m|m!=0).collect()).collect();"
    )
    require(function_compact.count(collection) == 1, "COLLECTION.projection")
    cumulative_iteration = "for(idx,collections)innode_collections.iter().enumerate(){"
    cumulative_terms = (
        "let(ip,im)=node_terms_with_cancellation("
        "&pmf,rlz,collections,n_sources,p_t,cancellation)?;"
    )
    cumulative_plus = "cum_plus[idx]=ip;"
    cumulative_minus = "cum_minus[idx]=im;"
    cumulative_route = (
        cumulative_iteration
        + cumulative_terms
        + cumulative_plus
        + cumulative_minus
        + "}"
    )
    require(
        function_compact.count(cumulative_route) == 1,
        "CUMULATIVE.positional_route",
    )
    positive = "letpi_plus=discrete_mobius_inversion_3(&antichains,&cum_plus);"
    negative = "letpi_minus=discrete_mobius_inversion_3(&antichains,&cum_minus);"
    inversion_calls = re.findall(
        r"\bdiscrete_mobius_inversion_3\s*\(", function_sanitized
    )
    require(len(inversion_calls) == 2, "INVERSION.call_count")
    require(function_compact.count(positive) == 1, "INVERSION.positive")
    require(function_compact.count(negative) == 1, "INVERSION.negative")

    pointwise_order = (
        "foriin0..m{"
        "leta=SxPointwiseAtom::new(pi_plus[i].value,pi_minus[i].value);"
        "add_exact_component(&mutavg[i][0],empirical_probability*a.informative_nats(),,)?;"
        "add_exact_component(&mutavg[i][1],empirical_probability*a.misinformative_nats(),,)?;"
        "atoms.push(a);"
        "}"
    )
    averaged_order = (
        "forain&avg{"
        "letinformative=exact_component_total(&a[0],)?;"
        "letmisinformative=exact_component_total(&a[1],)?;"
        "atoms_avg.push(SxAveragedAtom::new(informative,misinformative));"
        "}"
    )
    require(
        function_compact.count(pointwise_order) == 1,
        "RESULT.pointwise_index_order",
    )
    require(
        function_compact.count(averaged_order) == 1,
        "RESULT.averaged_vector_order",
    )

    struct_start, _, struct_end = unique_named_block(
        sxpid_source,
        sanitized,
        r"\bpub\s+struct\s+DiscreteSxPid3Result\b",
        "RESULT.declaration_count",
    )
    require(brace_depth(sanitized, struct_start) == 0, "RESULT.declaration_scope")
    require_attached_outer_attributes(
        sanitized,
        struct_start,
        ("#[derive(Debug,Serialize)]", "#[non_exhaustive]"),
        "RESULT.attached_outer_attribute",
    )
    struct_compact = compact(sanitized[struct_start:struct_end])
    declaration_order = "pubantichains:Vec<Vec<u8>>,pubatoms:Vec<SxAveragedAtom>,"
    require(struct_compact.count(declaration_order) == 1, "RESULT.declaration_order")

    constructor_matches = list(
        re.finditer(r"\bDiscreteSxPid3Result\s*\{", function_sanitized)
    )
    require(len(constructor_matches) == 1, "RESULT.constructor_count")
    constructor_opening = function_start + function_sanitized.find(
        "{", constructor_matches[0].start()
    )
    constructor_end = braced_end(sanitized, constructor_opening)
    constructor_compact = compact(
        sanitized[function_start + constructor_matches[0].start() : constructor_end]
    )
    antichain_field = "antichains:node_collections,"
    atoms_field = "atoms:atoms_avg,"
    require(
        constructor_compact.count(antichain_field) == 1, "RESULT.antichain_projection"
    )
    require(constructor_compact.count(atoms_field) == 1, "RESULT.atom_projection")
    require(
        constructor_compact.index(antichain_field)
        < constructor_compact.index(atoms_field),
        "RESULT.output_order",
    )

    route_positions = tuple(
        function_compact.index(item)
        for item in (
            call,
            collection,
            cumulative_route,
            positive,
            negative,
            pointwise_order,
            averaged_order,
            antichain_field,
            atoms_field,
        )
    )
    require(
        all(
            route_positions[index] < route_positions[index + 1]
            for index in range(len(route_positions) - 1)
        ),
        "ROUTE.anchor_order",
    )

    constructor_order = antichain_field + atoms_field
    return {
        "canonical_helper_call": canonical_anchor(
            "let antichains = discrete_antichains_3();",
            "loads_the_exact_18_antichain_position_order_inside_the_fixed_sxpid3_function",
            call,
        ),
        "collection_projection": canonical_anchor(
            "node_collections projection",
            "removes_only_zero_padding_while_preserving_antichain_position_and_collection_order",
            collection,
        ),
        "cumulative_positional_route": canonical_anchor(
            "node_collections.iter().enumerate() cumulative construction",
            "passes_each_enumerated_collection_to_node_terms_and_writes_both_cumulatives_at_that_same_index_lexically",
            cumulative_route,
        ),
        "import": import_anchors["antichain"],
        "mobius_import": import_anchors["mobius"],
        "negative_inversion": canonical_anchor(
            "pi_minus Mobius inversion",
            "applies_the_same_antichain_order_to_the_misinformative_cumulatives",
            negative,
        ),
        "positive_inversion": canonical_anchor(
            "pi_plus Mobius inversion",
            "applies_the_same_antichain_order_to_the_informative_cumulatives",
            positive,
        ),
        "result_averaged_vector_order": canonical_anchor(
            "ordered avg iteration into atoms_avg",
            "preserves_the_shared_antichain_position_when_materializing_the_averaged_atom_vector",
            averaged_order,
        ),
        "result_declaration_order": canonical_anchor(
            "DiscreteSxPid3Result antichains/atoms declaration order",
            "establishes_only_field_presence_and_that_antichains_precedes_atoms_in_the_struct_declaration",
            declaration_order,
        ),
        "result_pointwise_index_order": canonical_anchor(
            "pi_plus/pi_minus index alignment into avg",
            "uses_one_shared_antichain_position_for_both_inversions_and_both_averaged_components",
            pointwise_order,
        ),
        "result_output_order": canonical_anchor(
            "DiscreteSxPid3Result antichains/atoms constructor projection",
            "returns_node_collections_and_averaged_atoms_in_the_same_positional_order",
            constructor_order,
        ),
        "target_function_signature": canonical_anchor(
            "sxpid3_from_states_with_cancellation signature",
            "limits_this_route_to_exactly_three_sources_and_the_DiscreteSxPid3Result_output",
            expected_signature,
        ),
        "target_full_function_bytes": {
            "hash_basis": "exact_complete_utf8_braced_function_bytes_without_leading_docs",
            "locator": "complete sxpid3_from_states_with_cancellation braced function",
            "path": SXPID_RELATIVE,
            "role": (
                "local_lexical_function_byte_identity_only_not_compilation_authenticity_commit_or_release_identity"
            ),
            "sha256": sha256_text(function_raw_source),
        },
    }


def reject_assert_statements(checker_path: Path) -> None:
    source = checker_path.read_text(encoding="utf-8", errors="strict")
    tree = ast.parse(source, filename=str(checker_path))
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        "CHECKER.assert_statement",
    )


def build_result(
    repo_root: Path,
    checker_path: Path,
) -> dict[str, object]:
    reject_assert_statements(checker_path)
    discrete_path = repo_root / DISCRETE_PID_RELATIVE
    discrete_bytes = discrete_path.read_bytes()
    discrete_source = discrete_bytes.decode("utf-8", errors="strict")
    reject_module_inner_cfg_attributes(
        discrete_source, "DISCRETE_PID.module_inner_cfg_or_cfg_attr"
    )
    sxpid_path = repo_root / SXPID_RELATIVE
    sxpid_bytes = sxpid_path.read_bytes()
    sxpid_source = sxpid_bytes.decode("utf-8", errors="strict")
    reject_module_inner_cfg_attributes(
        sxpid_source, "SXPID.module_inner_cfg_or_cfg_attr"
    )
    primary_checker_path = repo_root / PRIMARY_CHECKER_RELATIVE
    primary_checker_bytes = primary_checker_path.read_bytes()
    require(
        sha256_bytes(primary_checker_bytes) == EXPECTED_PRIMARY_CHECKER_SOURCE_SHA256,
        "PRIMARY_CHECKER.source_sha256",
    )
    primary_checker_source = primary_checker_bytes.decode("utf-8", errors="strict")

    helper_anchor, stable_keys = helper_binding(discrete_source)
    mobius_anchors = mobius_route_bindings(discrete_source)
    checker_anchors, checker_binding = primary_checker_binding(
        primary_checker_source, str(helper_anchor["sha256"])
    )
    rust_anchors = rust_route_bindings(sxpid_source)
    anchors: dict[str, dict[str, object]] = {
        "helper_definition": helper_anchor,
        **mobius_anchors,
        **checker_anchors,
        **rust_anchors,
    }
    stable_order = {
        "count": len(stable_keys),
        "keys": list(stable_keys),
        "keys_sha256": canonical_sha256(list(stable_keys)),
        "role": (
            "reconstructed_Rust_positional_order_connected_to_the_P5_audit_order_by_key_equality_not_lexicographic_identity"
        ),
    }
    audit_expression_context = {
        "expression_count": 108,
        "factorization": {
            "antichain_positions": 18,
            "components": ["informative", "misinformative", "net"],
            "representation_stage_count": 2,
            "representation_stages": ["cumulative_values", "mobius_atoms"],
        },
        "lexical_custody_role": (
            "binds_the_Rust_18_key_positional_carrier_to_the_P5_audit_registry_only_by_key_equality"
        ),
        "numeric_rust_expressions_compared": 0,
        "object_kind": "keyed_scalar_audit_expression",
        "prohibited_interpretations": [
            "108_lattice_nodes",
            "108_PID_atoms",
            "108_independent_degrees_of_freedom",
            "compiled_Rust_agreement",
            "binary64_refinement",
        ],
    }
    scope = {
        "excluded": [
            "discrete_sxpid_n",
            "I_min_measure_estimator_and_lattice_semantics",
            "compiled_or_executed_Rust_behavior",
            "numeric_Rust_agreement",
            "binary64_refinement",
        ],
        "included_function": TARGET_FUNCTION,
        "included_result": TARGET_RESULT,
        "lexical_role": "antichain_key_carrier_and_positional_route",
        "source_count": 3,
    }
    source_stability_scope = {
        "classification": "bounded_repeated_read_race_detection",
        "initial_capture": "exact_source_bytes_decoded_and_used_for_all_lexical_checks",
        "pre_acceptance_check": (
            "one_sequential_end_of_build_exact_byte_reread_of_each_bound_source"
        ),
        "rust_paths": [DISCRETE_PID_RELATIVE, SXPID_RELATIVE],
        "nonclaims": [
            "atomic_snapshot",
            "live_file_monitor",
            "source_authenticity",
            "artifact_authenticity",
            "commit_or_release_identity",
        ],
    }
    manifest = {
        "anchors": anchors,
        "audit_expression_context": audit_expression_context,
        "boundaries": list(BOUNDARIES),
        "format": MANIFEST_FORMAT,
        "primary_checker_ast_binding": checker_binding,
        "scope": scope,
        "source_stability_scope": source_stability_scope,
        "stable_rust_antichain_position_order": stable_order,
    }
    require(
        discrete_path.read_bytes() == discrete_bytes,
        "DISCRETE_PID.unstable_source",
    )
    require(sxpid_path.read_bytes() == sxpid_bytes, "SXPID.unstable_source")
    require(
        primary_checker_path.read_bytes() == primary_checker_bytes,
        "PRIMARY_CHECKER.unstable_source",
    )
    manifest_sha256 = canonical_sha256(manifest)
    require(
        manifest_sha256 == EXPECTED_ROUTE_MANIFEST_SHA256,
        "ROUTE.manifest_sha256",
    )
    return {
        **manifest,
        "format": FORMAT,
        "gate": "GO",
        "route_manifest_format": MANIFEST_FORMAT,
        "route_manifest_sha256": manifest_sha256,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root containing the three bound source files",
    )
    return parser.parse_args()


def main() -> int:
    require_isolated_python()
    arguments = parse_args()
    repo_root = arguments.repo_root.resolve()
    result = build_result(repo_root, Path(__file__).resolve())
    print(canonical_json(result), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, SyntaxError, UnicodeError, ValueError) as error:
        print(f"SxPID3 P5 Rust source route: {error}", file=sys.stderr)
        raise SystemExit(1)
