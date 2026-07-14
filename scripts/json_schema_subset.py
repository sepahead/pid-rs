"""Fail-closed validator for the JSON Schema subset used by pid-rs audit artifacts.

This intentionally supports only checked-in schemas and raises on unknown assertion keywords.
It is not a general replacement for a Draft 2020-12 implementation.
"""

from __future__ import annotations

import json
import re
from typing import Any


class SchemaValidationError(ValueError):
    """The instance is invalid or the checked-in schema uses an unsupported keyword."""


ANNOTATIONS = {"$id", "$schema", "$defs", "description", "title"}
ASSERTIONS = {
    "$ref",
    "additionalProperties",
    "const",
    "enum",
    "items",
    "maxItems",
    "minItems",
    "minLength",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "type",
    "uniqueItems",
}


def _json_token(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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
        raise SchemaValidationError(f"unsupported non-local $ref: {reference!r}")
    value: Any = root
    for raw_component in reference[2:].split("/"):
        component = raw_component.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or component not in value:
            raise SchemaValidationError(f"unresolvable schema $ref: {reference!r}")
        value = value[component]
    return value


def validate(instance: Any, schema: Any, *, name: str = "instance") -> None:
    """Validate ``instance`` against the supported subset of ``schema``."""

    if not isinstance(schema, dict):
        raise SchemaValidationError(f"{name}: schema node must be an object")
    root = schema

    def visit(value: Any, rule: Any, path: str) -> None:
        if not isinstance(rule, dict):
            raise SchemaValidationError(f"{path}: schema node must be an object")
        unknown = set(rule) - ANNOTATIONS - ASSERTIONS
        if unknown:
            raise SchemaValidationError(
                f"{path}: unsupported schema keyword(s): {', '.join(sorted(unknown))}"
            )

        if "$ref" in rule:
            if len(set(rule) - ANNOTATIONS - {"$ref"}) != 0:
                raise SchemaValidationError(f"{path}: sibling assertions beside $ref are unsupported")
            visit(value, _resolve_pointer(root, rule["$ref"]), path)
            return

        if "oneOf" in rule:
            variants = rule["oneOf"]
            if not isinstance(variants, list) or not variants:
                raise SchemaValidationError(f"{path}: oneOf must be a non-empty array")
            matches = 0
            for variant in variants:
                try:
                    visit(value, variant, path)
                except SchemaValidationError:
                    continue
                matches += 1
            if matches != 1:
                raise SchemaValidationError(f"{path}: expected exactly one oneOf match, got {matches}")

        if "type" in rule:
            expected = rule["type"]
            accepted = [expected] if isinstance(expected, str) else expected
            if (
                not isinstance(accepted, list)
                or not accepted
                or any(not isinstance(item, str) for item in accepted)
            ):
                raise SchemaValidationError(f"{path}: invalid schema type declaration")
            if not any(_type_matches(value, item) for item in accepted):
                raise SchemaValidationError(
                    f"{path}: expected type {' or '.join(accepted)}, got {type(value).__name__}"
                )

        if "const" in rule and not _same_json_value(value, rule["const"]):
            raise SchemaValidationError(f"{path}: value differs from const")
        if "enum" in rule:
            choices = rule["enum"]
            if not isinstance(choices, list) or not any(
                _same_json_value(value, choice) for choice in choices
            ):
                raise SchemaValidationError(f"{path}: value is outside enum")

        if isinstance(value, dict):
            required = rule.get("required", [])
            if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
                raise SchemaValidationError(f"{path}: schema required must be a string array")
            missing = sorted(set(required) - set(value))
            if missing:
                raise SchemaValidationError(f"{path}: missing required keys: {', '.join(missing)}")
            properties = rule.get("properties", {})
            if not isinstance(properties, dict):
                raise SchemaValidationError(f"{path}: schema properties must be an object")
            for key, child in value.items():
                if key in properties:
                    visit(child, properties[key], f"{path}.{key}")
                elif rule.get("additionalProperties") is False:
                    raise SchemaValidationError(f"{path}: unexpected property {key!r}")
                elif isinstance(rule.get("additionalProperties"), dict):
                    visit(child, rule["additionalProperties"], f"{path}.{key}")

        if isinstance(value, list):
            if "minItems" in rule and len(value) < rule["minItems"]:
                raise SchemaValidationError(f"{path}: fewer than minItems")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                raise SchemaValidationError(f"{path}: more than maxItems")
            if rule.get("uniqueItems") is True:
                tokens = [_json_token(item) for item in value]
                if len(tokens) != len(set(tokens)):
                    raise SchemaValidationError(f"{path}: array items are not unique")
            if "items" in rule:
                for index, item in enumerate(value):
                    visit(item, rule["items"], f"{path}[{index}]")

        if isinstance(value, str):
            if "minLength" in rule and len(value) < rule["minLength"]:
                raise SchemaValidationError(f"{path}: shorter than minLength")
            if "pattern" in rule:
                try:
                    matched = re.search(rule["pattern"], value)
                except (TypeError, re.error) as error:
                    raise SchemaValidationError(f"{path}: invalid schema pattern: {error}") from error
                if matched is None:
                    raise SchemaValidationError(f"{path}: string does not match pattern")

    visit(instance, schema, name)
