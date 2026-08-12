"""Fail-closed validator for the JSON Schema subset used by pid-rs audit artifacts.

This intentionally supports only checked-in schemas and raises on unknown assertion keywords.
Pattern assertions are complete-string constraints; schemas must express any allowed prefix or
suffix freedom explicitly.
It is not a general replacement for a Draft 2020-12 implementation.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any


class SchemaValidationError(ValueError):
    """The instance is invalid or the checked-in schema uses an unsupported keyword."""


class SchemaDefinitionError(SchemaValidationError):
    """The schema itself is malformed or uses semantics outside the supported subset."""


class InstanceValidationError(SchemaValidationError):
    """The instance does not satisfy a structurally valid supported schema."""


ANNOTATIONS = {"$id", "$schema", "$defs", "description", "title"}
ASSERTIONS = {
    "$ref",
    "additionalProperties",
    "const",
    "enum",
    "items",
    "maxItems",
    "minimum",
    "minItems",
    "minLength",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "type",
    "uniqueItems",
}
SUPPORTED_TYPES = {
    "array",
    "boolean",
    "integer",
    "null",
    "number",
    "object",
    "string",
}


def _json_token(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise InstanceValidationError(
            f"value is not finite JSON data: {error}"
        ) from error


def _require_finite_json(
    value: Any,
    path: str,
    *,
    error_type: type[SchemaValidationError] = InstanceValidationError,
) -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise error_type(f"{path}: non-finite JSON numbers are forbidden")
    if isinstance(value, float):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_finite_json(item, f"{path}[{index}]", error_type=error_type)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise error_type(f"{path}: JSON object keys must be strings")
            _require_finite_json(item, f"{path}.{key}", error_type=error_type)
    else:
        raise error_type(f"{path}: value is not JSON data: {type(value).__name__}")


def _same_json_value(left: Any, right: Any) -> bool:
    return _json_token(left) == _json_token(right)


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "array": isinstance(value, list),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "object": isinstance(value, dict),
        "string": isinstance(value, str),
    }.get(expected, False)


def _resolve_pointer(root: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise SchemaDefinitionError(f"unsupported non-local $ref: {reference!r}")
    value: Any = root
    for raw_component in reference[2:].split("/"):
        component = raw_component.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or component not in value:
            raise SchemaDefinitionError(f"unresolvable schema $ref: {reference!r}")
        value = value[component]
    return value


def _validate_schema_definition(root: dict[str, Any], *, name: str) -> None:
    """Validate every schema branch before evaluating it against an instance.

    This pass is deliberately independent of instance type and ``oneOf`` selection. Otherwise an
    invalid keyword hidden in a non-matching branch could be mistaken for an ordinary branch
    mismatch and silently weaken the checked-in schema.
    """

    active: set[int] = set()
    complete: set[int] = set()

    def require_non_negative_integer(value: Any, *, path: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise SchemaDefinitionError(
                f"{path}: schema value must be a non-negative integer"
            )

    def visit(rule: Any, path: str) -> None:
        if not isinstance(rule, dict):
            raise SchemaDefinitionError(f"{path}: schema node must be an object")
        identity = id(rule)
        if identity in complete:
            return
        if identity in active:
            raise SchemaDefinitionError(
                f"{path}: recursive schema references are unsupported"
            )
        active.add(identity)
        try:
            if any(not isinstance(key, str) for key in rule):
                raise SchemaDefinitionError(
                    f"{path}: schema object keys must be strings"
                )
            unknown = set(rule) - ANNOTATIONS - ASSERTIONS
            if unknown:
                raise SchemaDefinitionError(
                    f"{path}: unsupported schema keyword(s): "
                    f"{', '.join(sorted(unknown))}"
                )

            definitions = rule.get("$defs")
            if definitions is not None:
                if not isinstance(definitions, dict) or any(
                    not isinstance(key, str) for key in definitions
                ):
                    raise SchemaDefinitionError(
                        f"{path}: schema $defs must be an object with string keys"
                    )
                for key, child in definitions.items():
                    visit(child, f"{path}.$defs.{key}")

            if "$ref" in rule:
                reference = rule["$ref"]
                if not isinstance(reference, str):
                    raise SchemaDefinitionError(f"{path}: schema $ref must be a string")
                if set(rule) - ANNOTATIONS - {"$ref"}:
                    raise SchemaDefinitionError(
                        f"{path}: sibling assertions beside $ref are unsupported"
                    )
                visit(_resolve_pointer(root, reference), f"{path} -> {reference}")

            if "oneOf" in rule:
                variants = rule["oneOf"]
                if not isinstance(variants, list) or not variants:
                    raise SchemaDefinitionError(
                        f"{path}: oneOf must be a non-empty array"
                    )
                for index, variant in enumerate(variants):
                    visit(variant, f"{path}.oneOf[{index}]")

            if "type" in rule:
                expected = rule["type"]
                accepted = [expected] if isinstance(expected, str) else expected
                if (
                    not isinstance(accepted, list)
                    or not accepted
                    or any(not isinstance(item, str) for item in accepted)
                    or len(accepted) != len(set(accepted))
                    or any(item not in SUPPORTED_TYPES for item in accepted)
                ):
                    raise SchemaDefinitionError(
                        f"{path}: invalid schema type declaration"
                    )

            if "enum" in rule:
                choices = rule["enum"]
                if not isinstance(choices, list) or not choices:
                    raise SchemaDefinitionError(
                        f"{path}: schema enum must be a non-empty array"
                    )
                tokens = [_json_token(choice) for choice in choices]
                if len(tokens) != len(set(tokens)):
                    raise SchemaDefinitionError(
                        f"{path}: schema enum values must be unique"
                    )

            required = rule.get("required")
            if required is not None and (
                not isinstance(required, list)
                or any(not isinstance(item, str) for item in required)
                or len(required) != len(set(required))
            ):
                raise SchemaDefinitionError(
                    f"{path}: schema required must be a unique string array"
                )

            properties = rule.get("properties")
            if properties is not None:
                if not isinstance(properties, dict) or any(
                    not isinstance(key, str) for key in properties
                ):
                    raise SchemaDefinitionError(
                        f"{path}: schema properties must be an object with string keys"
                    )
                for key, child in properties.items():
                    visit(child, f"{path}.properties.{key}")

            if "additionalProperties" in rule:
                additional = rule["additionalProperties"]
                if not isinstance(additional, (bool, dict)):
                    raise SchemaDefinitionError(
                        f"{path}: schema additionalProperties must be a boolean or object"
                    )
                if isinstance(additional, dict):
                    visit(additional, f"{path}.additionalProperties")

            for keyword in ("minItems", "maxItems", "minLength"):
                if keyword in rule:
                    require_non_negative_integer(
                        rule[keyword], path=f"{path}.{keyword}"
                    )
            if (
                "minItems" in rule
                and "maxItems" in rule
                and rule["minItems"] > rule["maxItems"]
            ):
                raise SchemaDefinitionError(
                    f"{path}: minItems must not exceed maxItems"
                )

            if "minimum" in rule:
                minimum = rule["minimum"]
                if not isinstance(minimum, (int, float)) or isinstance(minimum, bool):
                    raise SchemaDefinitionError(
                        f"{path}.minimum: schema value must be a finite number"
                    )

            if "uniqueItems" in rule and not isinstance(rule["uniqueItems"], bool):
                raise SchemaDefinitionError(
                    f"{path}: schema uniqueItems must be a boolean"
                )

            if "items" in rule:
                visit(rule["items"], f"{path}.items")

            if "pattern" in rule:
                pattern = rule["pattern"]
                if not isinstance(pattern, str):
                    raise SchemaDefinitionError(
                        f"{path}: schema pattern must be a string"
                    )
                try:
                    re.compile(pattern)
                except re.error as error:
                    raise SchemaDefinitionError(
                        f"{path}: invalid schema pattern: {error}"
                    ) from error
        finally:
            active.remove(identity)
        complete.add(identity)

    _require_finite_json(root, name, error_type=SchemaDefinitionError)
    visit(root, name)


def validate(instance: Any, schema: Any, *, name: str = "instance") -> None:
    """Validate ``instance`` against the supported subset of ``schema``."""

    if not isinstance(schema, dict):
        raise SchemaDefinitionError(f"{name}: schema node must be an object")
    _require_finite_json(instance, name)
    root = schema
    _validate_schema_definition(root, name=f"{name} schema")

    def visit(value: Any, rule: Any, path: str) -> None:
        if not isinstance(rule, dict):
            raise SchemaDefinitionError(f"{path}: schema node must be an object")
        unknown = set(rule) - ANNOTATIONS - ASSERTIONS
        if unknown:
            raise SchemaDefinitionError(
                f"{path}: unsupported schema keyword(s): {', '.join(sorted(unknown))}"
            )

        if "$ref" in rule:
            if len(set(rule) - ANNOTATIONS - {"$ref"}) != 0:
                raise SchemaDefinitionError(
                    f"{path}: sibling assertions beside $ref are unsupported"
                )
            visit(value, _resolve_pointer(root, rule["$ref"]), path)
            return

        if "oneOf" in rule:
            variants = rule["oneOf"]
            if not isinstance(variants, list) or not variants:
                raise SchemaDefinitionError(f"{path}: oneOf must be a non-empty array")
            matches = 0
            for variant in variants:
                try:
                    visit(value, variant, path)
                except InstanceValidationError:
                    continue
                matches += 1
            if matches != 1:
                raise InstanceValidationError(
                    f"{path}: expected exactly one oneOf match, got {matches}"
                )

        if "type" in rule:
            expected = rule["type"]
            accepted = [expected] if isinstance(expected, str) else expected
            if (
                not isinstance(accepted, list)
                or not accepted
                or any(not isinstance(item, str) for item in accepted)
            ):
                raise SchemaDefinitionError(f"{path}: invalid schema type declaration")
            if not any(_type_matches(value, item) for item in accepted):
                raise InstanceValidationError(
                    f"{path}: expected type {' or '.join(accepted)}, got {type(value).__name__}"
                )

        if "const" in rule and not _same_json_value(value, rule["const"]):
            raise InstanceValidationError(f"{path}: value differs from const")
        if "enum" in rule:
            choices = rule["enum"]
            if not isinstance(choices, list) or not any(
                _same_json_value(value, choice) for choice in choices
            ):
                raise InstanceValidationError(f"{path}: value is outside enum")
        if (
            "minimum" in rule
            and _type_matches(value, "number")
            and value < rule["minimum"]
        ):
            raise InstanceValidationError(f"{path}: number is below minimum")

        if isinstance(value, dict):
            required = rule.get("required", [])
            if not isinstance(required, list) or any(
                not isinstance(item, str) for item in required
            ):
                raise SchemaDefinitionError(
                    f"{path}: schema required must be a string array"
                )
            missing = sorted(set(required) - set(value))
            if missing:
                raise InstanceValidationError(
                    f"{path}: missing required keys: {', '.join(missing)}"
                )
            properties = rule.get("properties", {})
            if not isinstance(properties, dict):
                raise SchemaDefinitionError(
                    f"{path}: schema properties must be an object"
                )
            for key, child in value.items():
                if key in properties:
                    visit(child, properties[key], f"{path}.{key}")
                elif rule.get("additionalProperties") is False:
                    raise InstanceValidationError(
                        f"{path}: unexpected property {key!r}"
                    )
                elif isinstance(rule.get("additionalProperties"), dict):
                    visit(child, rule["additionalProperties"], f"{path}.{key}")

        if isinstance(value, list):
            if "minItems" in rule and len(value) < rule["minItems"]:
                raise InstanceValidationError(f"{path}: fewer than minItems")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                raise InstanceValidationError(f"{path}: more than maxItems")
            if rule.get("uniqueItems") is True:
                tokens = [_json_token(item) for item in value]
                if len(tokens) != len(set(tokens)):
                    raise InstanceValidationError(f"{path}: array items are not unique")
            if "items" in rule:
                for index, item in enumerate(value):
                    visit(item, rule["items"], f"{path}[{index}]")

        if isinstance(value, str):
            if "minLength" in rule and len(value) < rule["minLength"]:
                raise InstanceValidationError(f"{path}: shorter than minLength")
            if "pattern" in rule:
                try:
                    matched = re.fullmatch(rule["pattern"], value)
                except (TypeError, re.error) as error:
                    raise SchemaDefinitionError(
                        f"{path}: invalid schema pattern: {error}"
                    ) from error
                if matched is None:
                    raise InstanceValidationError(
                        f"{path}: string does not match pattern"
                    )

    visit(instance, schema, name)
