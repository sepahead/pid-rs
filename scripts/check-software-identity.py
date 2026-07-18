#!/usr/bin/env python3
"""Validate pid-core's embedded, package-safe software identity reference."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-software-identity.py requires Python 3.11 or newer")

import tomllib

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = Path("crates/pid-core/identity/software-identity-reference-v1.json")
DEFAULT_SCHEMA = Path("audit/schemas/software-identity-reference.schema.json")
DEFAULT_CARGO = Path("crates/pid-core/Cargo.toml")
DEFAULT_PYI = Path("crates/pid-python/pid_core_rs.pyi")
EXPECTED_ARTIFACTS = (
    ("method_catalog", "method-catalog.json", "pid-rs/method-catalog", 1),
    (
        "proposed_release_scope",
        "release-scope-1.0.json",
        "pid-rs/release-scope",
        1,
    ),
)
REQUIRED_PACKAGE_FILES = {
    "build.rs",
    "build_support.rs",
    "identity/software-identity-reference-v1.json",
    "src/identity.rs",
    "tests/software_identity.rs",
    "tests/software_identity_build.rs",
}


class IdentityError(RuntimeError):
    """The embedded identity, referenced artifacts, or package inventory disagree."""


RustToken = tuple[str, str]


def _raw_string_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust raw-string token beginning at ``start``, if present."""

    for prefix in ("br", "cr", "r"):
        if not source.startswith(prefix, start):
            continue
        cursor = start + len(prefix)
        while cursor < len(source) and source[cursor] == "#":
            cursor += 1
        if cursor >= len(source) or source[cursor] != '"':
            continue
        terminator = '"' + "#" * (cursor - start - len(prefix))
        end = source.find(terminator, cursor + 1)
        if end < 0:
            raise IdentityError("build.rs contains an unterminated raw string literal")
        end += len(terminator)
        return ("raw_string", source[start:end]), end
    return None


def _quoted_string_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust quoted string/byte-string token beginning at ``start``."""

    prefix_length = 1 if source.startswith(('b"', 'c"'), start) else 0
    quote = start + prefix_length
    if quote >= len(source) or source[quote] != '"':
        return None
    cursor = quote + 1
    while cursor < len(source):
        if source[cursor] == "\\":
            cursor += 2
            continue
        if source[cursor] == '"':
            end = cursor + 1
            return ("string", source[start:end]), end
        cursor += 1
    raise IdentityError("build.rs contains an unterminated string literal")


def _quoted_char_token(source: str, start: int) -> tuple[RustToken, int] | None:
    """Return a Rust character/byte-character token beginning at ``start``."""

    prefix_length = 1 if source.startswith("b'", start) else 0
    quote = start + prefix_length
    if quote >= len(source) or source[quote] != "'":
        return None
    cursor = quote + 1
    if cursor >= len(source):
        return None

    if source[cursor] == "\\":
        cursor += 1
        if cursor >= len(source):
            return None
        escape = source[cursor]
        if escape == "x":
            cursor += 3
        elif escape == "u" and source.startswith("u{", cursor):
            closing_brace = source.find("}", cursor + 2)
            if closing_brace < 0:
                return None
            cursor = closing_brace + 1
        else:
            cursor += 1
    else:
        if source[cursor] in {"'", "\r", "\n"}:
            return None
        cursor += 1

    if cursor >= len(source) or source[cursor] != "'":
        # This was a lifetime such as `'a`, not a character literal.
        return None
    end = cursor + 1
    return ("char", source[start:end]), end


def rust_source_tokens(source: str) -> list[RustToken]:
    """Tokenize the Rust subset needed to identify a live const declaration.

    Rust line comments and nested block comments are discarded. Character,
    quoted-string, and raw-string literals remain single tokens, so
    declaration-shaped text inside them cannot be mistaken for code.
    """

    tokens: list[RustToken] = []
    cursor = 0
    while cursor < len(source):
        if source[cursor].isspace():
            cursor += 1
            continue
        if source.startswith("//", cursor):
            newline = source.find("\n", cursor + 2)
            cursor = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", cursor):
            depth = 1
            cursor += 2
            while cursor < len(source) and depth:
                if source.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif source.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise IdentityError("build.rs contains an unterminated block comment")
            continue

        raw_string = _raw_string_token(source, cursor)
        if raw_string is not None:
            token, cursor = raw_string
            tokens.append(token)
            continue
        quoted_string = _quoted_string_token(source, cursor)
        if quoted_string is not None:
            token, cursor = quoted_string
            tokens.append(token)
            continue
        quoted_char = _quoted_char_token(source, cursor)
        if quoted_char is not None:
            token, cursor = quoted_char
            tokens.append(token)
            continue

        if (
            source.startswith("r#", cursor)
            and cursor + 2 < len(source)
            and (source[cursor + 2].isalpha() or source[cursor + 2] == "_")
        ):
            end = cursor + 3
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            tokens.append(("raw_ident", source[cursor + 2 : end]))
            cursor = end
            continue
        if source[cursor].isalpha() or source[cursor] == "_":
            end = cursor + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            tokens.append(("ident", source[cursor:end]))
            cursor = end
            continue

        tokens.append(("punct", source[cursor]))
        cursor += 1
    return tokens


def validate_build_manifest_declaration(source: str, expected_value: str) -> None:
    """Require one live, literal ``IDENTITY_MANIFEST`` const declaration."""

    tokens = rust_source_tokens(source)
    bindings: list[tuple[int, str]] = []
    for index, (kind, value) in enumerate(tokens):
        if kind not in {"ident", "raw_ident"} or value != "IDENTITY_MANIFEST":
            continue
        previous = index - 1
        while previous >= 0 and tokens[previous] in {
            ("ident", "mut"),
            ("ident", "ref"),
        }:
            previous -= 1
        if previous >= 0 and tokens[previous] in {
            ("ident", "const"),
            ("ident", "static"),
            ("ident", "let"),
        }:
            bindings.append((previous, tokens[previous][1]))

    expected_tokens: list[RustToken] = [
        ("ident", "const"),
        ("ident", "IDENTITY_MANIFEST"),
        ("punct", ":"),
        ("punct", "&"),
        ("ident", "str"),
        ("punct", "="),
        ("string", f'"{expected_value}"'),
        ("punct", ";"),
    ]
    if len(bindings) != 1 or bindings[0][1] != "const":
        raise IdentityError(
            "build.rs does not uniquely embed the checked software-identity manifest"
        )
    declaration_start = bindings[0][0]
    if (
        tokens[declaration_start : declaration_start + len(expected_tokens)]
        != expected_tokens
    ):
        raise IdentityError(
            "build.rs does not uniquely embed the checked software-identity manifest"
        )


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise IdentityError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def load_json(path: Path, *, canonical: bool = False) -> Any:
    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IdentityError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw_bytes != expected.encode("ascii"):
            raise IdentityError(
                f"{path} is not canonical sorted two-space ASCII JSON with one final LF"
            )
    return value


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise IdentityError(
            f"{label}: path must be a non-empty repository-relative string"
        )
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise IdentityError(f"{label}: unsafe repository path {relative!r}")
    current = root
    for component in relative_path.parts:
        current = current / component
        if current.is_symlink():
            raise IdentityError(f"{label}: symlink paths are forbidden: {relative!r}")
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise IdentityError(
            f"{label}: file is missing or escapes the repository: {relative!r}"
        ) from error
    if not resolved.is_file():
        raise IdentityError(f"{label}: expected a regular file: {relative!r}")
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pyi_class(tree: ast.Module, *, path: Path, class_name: str) -> ast.ClassDef:
    """Return one exact top-level class from a parsed Python stub."""

    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    if len(classes) != 1:
        raise IdentityError(
            f"{path}: expected exactly one {class_name} class, found {len(classes)}"
        )
    return classes[0]


def pyi_literal_values(
    tree: ast.Module, *, path: Path, class_name: str, field_name: str
) -> tuple[str | int, ...]:
    """Read one exact ``Class.field: Literal[...]`` annotation from a stub AST."""

    class_node = pyi_class(tree, path=path, class_name=class_name)
    fields = [
        node
        for node in class_node.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == field_name
    ]
    if len(fields) != 1:
        raise IdentityError(
            f"{path}: expected exactly one {class_name}.{field_name} annotation, "
            f"found {len(fields)}"
        )
    annotation = fields[0].annotation
    if not (
        isinstance(annotation, ast.Subscript)
        and isinstance(annotation.value, ast.Name)
        and annotation.value.id == "Literal"
    ):
        raise IdentityError(
            f"{path}: {class_name}.{field_name} must be an explicit Literal annotation"
        )
    try:
        raw_values = ast.literal_eval(annotation.slice)
    except (ValueError, TypeError) as error:
        raise IdentityError(
            f"{path}: cannot evaluate {class_name}.{field_name} Literal"
        ) from error
    values = raw_values if isinstance(raw_values, tuple) else (raw_values,)
    if not values or any(type(value) not in {str, int} for value in values):
        raise IdentityError(
            f"{path}: {class_name}.{field_name} Literal must contain strings or integers"
        )
    return values


def pyi_annotation_shape(annotation: ast.expr) -> str:
    """Return a location-independent AST shape on every supported Python version."""

    return ast.dump(annotation, annotate_fields=True, include_attributes=False)


def pyi_expected_annotation(source: str) -> ast.expr:
    """Parse an expected annotation without relying on version-specific AST constructors."""

    expression = ast.parse(source, mode="eval")
    return expression.body


def validate_pyi_typed_dict_bases(
    tree: ast.Module, *, path: Path, class_names: tuple[str, ...]
) -> None:
    """Require each identity record to remain an ordinary total ``TypedDict``."""

    expected_base = pyi_annotation_shape(pyi_expected_annotation("TypedDict"))
    for class_name in class_names:
        class_node = pyi_class(tree, path=path, class_name=class_name)
        actual_bases = tuple(pyi_annotation_shape(base) for base in class_node.bases)
        if (
            actual_bases != (expected_base,)
            or class_node.keywords
            or class_node.decorator_list
        ):
            raise IdentityError(
                f"{path}: {class_name} must inherit exactly from TypedDict "
                "without class keywords or decorators"
            )


def validate_pyi_typed_dict_fields(
    tree: ast.Module,
    *,
    path: Path,
    class_name: str,
    expected_fields: tuple[tuple[str, str], ...],
) -> None:
    """Bind every field of one identity record to its exact annotation graph."""

    class_node = pyi_class(tree, path=path, class_name=class_name)
    annotations: dict[str, ast.expr] = {}
    for node in class_node.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if not isinstance(node, ast.AnnAssign):
            raise IdentityError(
                f"{path}: {class_name} body may contain only its field annotations "
                "and an optional docstring"
            )
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            raise IdentityError(
                f"{path}: {class_name} fields must use simple annotations"
            )
        if node.value is not None or node.simple != 1:
            raise IdentityError(
                f"{path}: {class_name}.{node.target.id} must be an annotation-only field"
            )
        field_name = node.target.id
        if field_name in annotations:
            raise IdentityError(
                f"{path}: duplicate {class_name}.{field_name} annotation"
            )
        annotations[field_name] = node.annotation

    expected_names = tuple(field_name for field_name, _ in expected_fields)
    if set(annotations) != set(expected_names) or len(annotations) != len(
        expected_names
    ):
        raise IdentityError(
            f"{path}: {class_name} field set mismatch: "
            f"expected={expected_names!r}, got={tuple(annotations)!r}"
        )

    for field_name, expected_source in expected_fields:
        expected_shape = pyi_annotation_shape(pyi_expected_annotation(expected_source))
        if pyi_annotation_shape(annotations[field_name]) != expected_shape:
            raise IdentityError(
                f"{path}: {class_name}.{field_name} annotation must be exactly "
                f"{expected_source}"
            )


def validate_pyi_function_return(
    tree: ast.Module,
    *,
    path: Path,
    function_name: str,
    expected_return: str,
    expected_parameters: tuple[str, ...],
    class_name: str | None = None,
) -> None:
    """Require one exact synchronous stub function at the requested scope."""

    body: list[ast.stmt]
    qualified_name: str
    if class_name is None:
        body = tree.body
        qualified_name = function_name
    else:
        body = pyi_class(tree, path=path, class_name=class_name).body
        qualified_name = f"{class_name}.{function_name}"
    functions = [
        node
        for node in body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(functions) != 1 or not isinstance(functions[0], ast.FunctionDef):
        raise IdentityError(
            f"{path}: expected exactly one synchronous {qualified_name} definition"
        )
    if functions[0].decorator_list:
        raise IdentityError(f"{path}: {qualified_name} must not have decorators")
    arguments = functions[0].args
    positional = tuple(argument.arg for argument in arguments.args)
    if (
        arguments.posonlyargs
        or positional != expected_parameters
        or any(argument.annotation is not None for argument in arguments.args)
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kw_defaults
        or arguments.kwarg is not None
        or arguments.defaults
    ):
        rendered_parameters = ", ".join(expected_parameters)
        raise IdentityError(
            f"{path}: {qualified_name} parameters must be exactly ({rendered_parameters})"
        )
    if functions[0].type_comment is not None or getattr(
        functions[0], "type_params", []
    ):
        raise IdentityError(
            f"{path}: {qualified_name} must not declare a type comment or type parameters"
        )
    if not (
        len(functions[0].body) == 1
        and isinstance(functions[0].body[0], ast.Expr)
        and isinstance(functions[0].body[0].value, ast.Constant)
        and functions[0].body[0].value.value is Ellipsis
    ):
        raise IdentityError(
            f"{path}: {qualified_name} body must be exactly an ellipsis"
        )
    expected_shape = pyi_annotation_shape(pyi_expected_annotation(expected_return))
    returns = functions[0].returns
    if returns is None or pyi_annotation_shape(returns) != expected_shape:
        raise IdentityError(
            f"{path}: {qualified_name} must return exactly {expected_return}"
        )


def validate_pyi_identity_binding_graph(
    tree: ast.Module,
    *,
    path: Path,
    identity_typed_dicts: tuple[str, ...],
) -> None:
    """Reject shadowing or indirection that can detach the checked stub graph."""

    required_imports = {
        "Literal": ("typing", "Literal", None),
        "TypedDict": ("typing", "TypedDict", None),
        "ModuleType": ("types", "ModuleType", None),
    }
    all_imports: list[tuple[str | None, str, str | None, ast.alias]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    raise IdentityError(
                        f"{path}: wildcard imports are forbidden in the checked stub graph"
                    )
                all_imports.append((node.module, alias.name, alias.asname, alias))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                all_imports.append((None, alias.name, alias.asname, alias))

    top_level_import_aliases = {
        id(alias)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    approved_import_aliases: set[int] = set()
    for local_name, expected in required_imports.items():
        bindings = [
            (module, imported, alias_name, alias)
            for module, imported, alias_name, alias in all_imports
            if (alias_name or imported.split(".", 1)[0]) == local_name
        ]
        if len(bindings) != 1 or bindings[0][:3] != expected:
            raise IdentityError(
                f"{path}: {local_name} must be imported exactly once from "
                f"{expected[0]} without an alias"
            )
        if id(bindings[0][3]) not in top_level_import_aliases:
            raise IdentityError(f"{path}: {local_name} import must be top-level")
        approved_import_aliases.add(id(bindings[0][3]))

    stable_declarations = [
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "stable"
    ]
    expected_stable = pyi_annotation_shape(pyi_expected_annotation("_StableModule"))
    if (
        len(stable_declarations) != 1
        or stable_declarations[0].value is not None
        or stable_declarations[0].simple != 1
        or pyi_annotation_shape(stable_declarations[0].annotation) != expected_stable
    ):
        raise IdentityError(f"{path}: stable must be declared exactly as _StableModule")
    allowed_store_nodes = {id(stable_declarations[0].target)}

    exports = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "__all__"
    ]
    if len(exports) != 1 or not isinstance(exports[0].value, (ast.List, ast.Tuple)):
        raise IdentityError(f"{path}: __all__ must be one static top-level sequence")
    export_values = [
        element.value
        for element in exports[0].value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    ]
    if len(export_values) != len(exports[0].value.elts):
        raise IdentityError(f"{path}: __all__ must contain only string literals")
    for required_export in ("software_identity", "stable"):
        if export_values.count(required_export) != 1:
            raise IdentityError(
                f"{path}: __all__ must export {required_export} exactly once"
            )
    allowed_store_nodes.add(id(exports[0].targets[0]))

    protected_names = {
        "Literal",
        "TypedDict",
        "ModuleType",
        "str",
        "int",
        "bool",
        "list",
        "software_identity",
        "_StableModule",
        "stable",
        "__all__",
        *identity_typed_dicts,
    }
    for _, imported, alias_name, alias in all_imports:
        local_name = alias_name or imported.split(".", 1)[0]
        if local_name in protected_names and id(alias) not in approved_import_aliases:
            raise IdentityError(
                f"{path}: checked stub name {local_name} must not be rebound"
            )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and node.id in protected_names
            and id(node) not in allowed_store_nodes
        ):
            raise IdentityError(
                f"{path}: checked stub name {node.id} must not be rebound"
            )
        if isinstance(node, ast.ExceptHandler) and node.name in protected_names:
            raise IdentityError(
                f"{path}: checked stub name {node.name} must not be rebound"
            )
        if (
            isinstance(node, (ast.MatchAs, ast.MatchStar))
            and node.name in protected_names
        ):
            raise IdentityError(
                f"{path}: checked stub name {node.name} must not be rebound"
            )
        if isinstance(node, ast.MatchMapping) and node.rest in protected_names:
            raise IdentityError(
                f"{path}: checked stub name {node.rest} must not be rebound"
            )

    for protected_name in (*identity_typed_dicts, "_StableModule"):
        definitions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == protected_name
        ]
        top_level = pyi_class(tree, path=path, class_name=protected_name)
        if definitions != [top_level]:
            raise IdentityError(
                f"{path}: {protected_name} must have exactly one top-level definition"
            )

    root_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "software_identity"
    )
    stable_class = pyi_class(tree, path=path, class_name="_StableModule")
    stable_functions = [
        node
        for node in stable_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "software_identity"
    ]
    all_functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "software_identity"
    ]
    if len(stable_functions) != 1 or set(map(id, all_functions)) != {
        id(root_function),
        id(stable_functions[0]),
    }:
        raise IdentityError(
            f"{path}: software_identity must have only the checked root and stable definitions"
        )

    stable_bases = tuple(pyi_annotation_shape(base) for base in stable_class.bases)
    expected_module_type = pyi_annotation_shape(pyi_expected_annotation("ModuleType"))
    if (
        stable_bases != (expected_module_type,)
        or stable_class.keywords
        or stable_class.decorator_list
    ):
        raise IdentityError(
            f"{path}: _StableModule must inherit exactly from ModuleType "
            "without class keywords or decorators"
        )


def validate_pyi_identity_literals(path: Path, manifest: dict[str, Any]) -> None:
    """Bind the manifest and complete identity envelope to the Python stub graph."""

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path), type_comments=True)
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise IdentityError(f"cannot parse Python stub {path}: {error}") from error

    api = manifest["api_signature_identity"]
    artifacts = manifest["reference_artifacts"]
    expected_bindings: tuple[tuple[str, str, tuple[str | int, ...]], ...] = (
        ("_SoftwareIdentity", "identity_format", (manifest["identity_format"],)),
        ("_PublicRustApiSignatureIdentity", "epoch", (api["epoch"],)),
        ("_PublicRustApiSignatureIdentity", "revision", (api["revision"],)),
        ("_PublicRustApiSignatureIdentity", "scope", (api["scope"],)),
        ("_PublicRustApiSignatureIdentity", "status", (api["status"],)),
        (
            "_ReferenceArtifactIdentity",
            "kind",
            tuple(artifact["kind"] for artifact in artifacts),
        ),
        (
            "_ReferenceArtifactIdentity",
            "schema_revision",
            tuple(sorted({artifact["schema_revision"] for artifact in artifacts})),
        ),
        (
            "_ReferenceArtifactIdentity",
            "digest_scope",
            (manifest["artifact_digest_scope"],),
        ),
        (
            "_ReferenceArtifactIdentity",
            "role",
            (manifest["reference_artifact_use"],),
        ),
        ("_SoftwareIdentity", "attestation", (manifest["attestation"],)),
    )
    for class_name, field_name, expected in expected_bindings:
        actual = pyi_literal_values(
            tree, path=path, class_name=class_name, field_name=field_name
        )
        if actual != expected:
            raise IdentityError(
                f"{path}: identity Literal {class_name}.{field_name} mismatch: "
                f"expected={expected!r}, got={actual!r}"
            )

    identity_typed_dicts = (
        "_PublicRustApiSignatureIdentity",
        "_WorkspaceGitSourceIdentity",
        "_CargoPackageSourceIdentity",
        "_UnavailableSourceIdentity",
        "_BuildContext",
        "_ReferenceArtifactIdentity",
        "_SoftwareIdentity",
    )
    validate_pyi_typed_dict_bases(tree, path=path, class_names=identity_typed_dicts)
    artifact_kinds = ", ".join(repr(artifact["kind"]) for artifact in artifacts)
    identity_records = (
        (
            "_PublicRustApiSignatureIdentity",
            (
                ("epoch", f"Literal[{api['epoch']!r}]"),
                ("revision", f"Literal[{api['revision']!r}]"),
                ("scope", f"Literal[{api['scope']!r}]"),
                ("status", f"Literal[{api['status']!r}]"),
            ),
        ),
        (
            "_WorkspaceGitSourceIdentity",
            (
                ("kind", "Literal['workspace_git']"),
                ("commit_sha1", "str"),
                ("working_tree_scope", "Literal['crates/pid-core']"),
                ("working_tree", "Literal['clean', 'dirty', 'unknown']"),
            ),
        ),
        (
            "_CargoPackageSourceIdentity",
            (
                ("kind", "Literal['cargo_package']"),
                ("commit_sha1", "str"),
                (
                    "working_tree_scope",
                    "Literal['cargo_vcs_info_dirty_flag']",
                ),
                ("working_tree", "Literal['clean', 'dirty', 'unknown']"),
            ),
        ),
        (
            "_UnavailableSourceIdentity",
            (
                ("kind", "Literal['unavailable']"),
                (
                    "reason",
                    "Literal['invalid_cargo_vcs_info', "
                    "'unrecognized_workspace_layout', 'git_unavailable', "
                    "'invalid_git_commit']",
                ),
            ),
        ),
        (
            "_BuildContext",
            (
                ("rustc_version", "str | None"),
                ("target_triple", "str"),
                ("profile", "str"),
                ("opt_level", "str"),
                ("debug_information", "bool"),
                ("enabled_features", "list[str]"),
            ),
        ),
        (
            "_ReferenceArtifactIdentity",
            (
                ("kind", f"Literal[{artifact_kinds}]"),
                ("repository_path", "str"),
                ("schema", "str"),
                (
                    "schema_revision",
                    f"Literal[{artifacts[0]['schema_revision']!r}]",
                ),
                ("digest_scope", f"Literal[{manifest['artifact_digest_scope']!r}]"),
                ("canonical_json_sha256", "str"),
                ("role", f"Literal[{manifest['reference_artifact_use']!r}]"),
            ),
        ),
        (
            "_SoftwareIdentity",
            (
                ("identity_format", f"Literal[{manifest['identity_format']!r}]"),
                ("package_name", "str"),
                ("package_version", "str"),
                (
                    "public_rust_api_signature_identity",
                    "_PublicRustApiSignatureIdentity",
                ),
                (
                    "source",
                    "_WorkspaceGitSourceIdentity | _CargoPackageSourceIdentity "
                    "| _UnavailableSourceIdentity",
                ),
                ("build", "_BuildContext"),
                ("reference_artifacts", "list[_ReferenceArtifactIdentity]"),
                ("attestation", f"Literal[{manifest['attestation']!r}]"),
            ),
        ),
    )
    for class_name, expected_fields in identity_records:
        validate_pyi_typed_dict_fields(
            tree,
            path=path,
            class_name=class_name,
            expected_fields=expected_fields,
        )
    validate_pyi_function_return(
        tree,
        path=path,
        function_name="software_identity",
        expected_return="_SoftwareIdentity",
        expected_parameters=(),
    )
    validate_pyi_function_return(
        tree,
        path=path,
        class_name="_StableModule",
        function_name="software_identity",
        expected_return="_SoftwareIdentity",
        expected_parameters=("self",),
    )
    validate_pyi_identity_binding_graph(
        tree,
        path=path,
        identity_typed_dicts=identity_typed_dicts,
    )


def cargo_features(path: Path) -> list[str]:
    try:
        with path.open("rb") as handle:
            cargo = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise IdentityError(f"cannot read {path}: {error}") from error
    features = cargo.get("features")
    if not isinstance(features, dict):
        raise IdentityError("pid-core Cargo features table is missing")
    names = sorted(features)
    if features.get("default") != []:
        raise IdentityError("pid-core default features must remain empty")
    normalized: dict[str, str] = {}
    for feature in names:
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", feature) is None:
            raise IdentityError(
                f"Cargo feature name is outside the identity grammar: {feature!r}"
            )
        env_name = "CARGO_FEATURE_" + feature.upper().replace("-", "_")
        previous = normalized.setdefault(env_name, feature)
        if previous != feature:
            raise IdentityError(
                f"Cargo feature environment-name collision: {previous!r} and {feature!r}"
            )

    optional_dependencies: set[str] = set()

    def collect_optional(table: Any) -> None:
        if not isinstance(table, dict):
            return
        for name, specification in table.items():
            if (
                isinstance(specification, dict)
                and specification.get("optional") is True
            ):
                optional_dependencies.add(name)

    collect_optional(cargo.get("dependencies"))
    targets = cargo.get("target", {})
    if isinstance(targets, dict):
        for target in targets.values():
            if isinstance(target, dict):
                collect_optional(target.get("dependencies"))

    explicit_optional_dependencies = {
        item.removeprefix("dep:")
        for members in features.values()
        if isinstance(members, list)
        for item in members
        if isinstance(item, str) and item.startswith("dep:")
    }
    missing_dep_prefix = sorted(optional_dependencies - explicit_optional_dependencies)
    if missing_dep_prefix:
        raise IdentityError(
            "optional pid-core dependencies must use explicit dep: feature edges: "
            + ", ".join(missing_dep_prefix)
        )
    return names


def package_files(root: Path) -> set[str]:
    process = subprocess.run(
        [
            "cargo",
            "package",
            "--locked",
            "--allow-dirty",
            "--no-verify",
            "--list",
            "-p",
            "pid-core",
        ],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise IdentityError(f"cargo package --list failed: {detail}")
    return {line.strip() for line in process.stdout.splitlines() if line.strip()}


def validate_identity(
    *,
    root: Path,
    manifest_path: Path,
    schema_path: Path,
    cargo_path: Path,
    check_package: bool,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    expected_paths = {
        "software identity manifest": DEFAULT_MANIFEST,
        "software identity schema": DEFAULT_SCHEMA,
        "pid-core Cargo manifest": DEFAULT_CARGO,
    }
    supplied_paths = {
        "software identity manifest": manifest_path,
        "software identity schema": schema_path,
        "pid-core Cargo manifest": cargo_path,
    }
    checked_paths: dict[str, Path] = {}
    for label, expected_relative in expected_paths.items():
        supplied = supplied_paths[label]
        try:
            supplied_relative = supplied.absolute().relative_to(root).as_posix()
        except ValueError as error:
            raise IdentityError(f"{label}: path is outside the repository") from error
        if supplied_relative != expected_relative.as_posix():
            raise IdentityError(
                f"{label}: expected {expected_relative.as_posix()!r}, "
                f"got {supplied_relative!r}"
            )
        checked_paths[label] = safe_repo_file(root, supplied_relative, label=label)
    manifest_path = checked_paths["software identity manifest"]
    schema_path = checked_paths["software identity schema"]
    cargo_path = checked_paths["pid-core Cargo manifest"]

    manifest = load_json(manifest_path, canonical=True)
    schema = load_json(schema_path, canonical=True)
    try:
        validate_json_schema(manifest, schema, name="software identity reference")
    except SchemaValidationError as error:
        raise IdentityError(
            f"software identity schema validation failed: {error}"
        ) from error

    expected_features = cargo_features(cargo_path)
    if manifest["recognized_cargo_features"] != expected_features:
        raise IdentityError(
            "recognized Cargo feature inventory disagrees with pid-core Cargo.toml: "
            f"expected={expected_features!r}, "
            f"got={manifest['recognized_cargo_features']!r}"
        )

    artifacts = manifest["reference_artifacts"]
    for index, expected in enumerate(EXPECTED_ARTIFACTS):
        artifact = artifacts[index]
        kind, relative, artifact_schema, schema_revision = expected
        actual_identity = (
            artifact["kind"],
            artifact["repository_path"],
            artifact["schema"],
            artifact["schema_revision"],
        )
        if actual_identity != expected:
            raise IdentityError(
                f"reference_artifacts[{index}] identity mismatch: "
                f"expected={expected!r}, got={actual_identity!r}"
            )
        path = safe_repo_file(root, relative, label=f"reference artifact {kind}")
        referenced = load_json(path, canonical=True)
        if referenced.get("schema") != artifact_schema:
            raise IdentityError(
                f"{relative}: schema identity disagrees with embedded reference"
            )
        if referenced.get("schema_revision") != schema_revision:
            raise IdentityError(
                f"{relative}: schema revision disagrees with embedded reference"
            )
        actual_digest = sha256_file(path)
        if artifact["canonical_json_sha256"] != actual_digest:
            raise IdentityError(
                f"{relative}: SHA-256 mismatch: expected {actual_digest}, "
                f"got {artifact['canonical_json_sha256']}"
            )

    build_source = safe_repo_file(
        root, "crates/pid-core/build.rs", label="build script"
    )
    source_text = build_source.read_text(encoding="utf-8")
    manifest_relative = manifest_path.resolve(strict=True).relative_to(root).as_posix()
    expected_value = Path(manifest_relative).relative_to("crates/pid-core").as_posix()
    validate_build_manifest_declaration(source_text, expected_value)

    pyi_path = safe_repo_file(root, DEFAULT_PYI.as_posix(), label="Python type stub")
    validate_pyi_identity_literals(pyi_path, manifest)

    if check_package:
        packaged = package_files(root)
        missing = sorted(REQUIRED_PACKAGE_FILES - packaged)
        if missing:
            raise IdentityError(
                "pid-core package omits required identity files: " + ", ".join(missing)
            )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--skip-package-list",
        action="store_true",
        help="skip Cargo package inventory (intended only for isolated mutation fixtures)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    manifest = root / DEFAULT_MANIFEST
    schema = root / DEFAULT_SCHEMA
    cargo = root / DEFAULT_CARGO
    try:
        value = validate_identity(
            root=root,
            manifest_path=manifest,
            schema_path=schema,
            cargo_path=cargo,
            check_package=not args.skip_package_list,
        )
    except (IdentityError, ValueError) as error:
        print(f"software identity error: {error}", file=sys.stderr)
        return 1
    print(
        "OK: software identity format "
        f"{value['identity_format']}, {len(value['recognized_cargo_features'])} Cargo "
        f"features, and {len(value['reference_artifacts'])} forensic references are coherent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
