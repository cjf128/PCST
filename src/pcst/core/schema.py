"""Small, dependency-free JSON Schema validator used by the canonical files.

The project ships the schemas in ``schemas/``.  Runtime environments used for
the desktop application do not need the optional :mod:`jsonschema` package,
so this module implements the subset of draft 2020-12 keywords used by the
project schemas.  Domain-level checks (for example, ``min < max`` and class
references) remain in :mod:`pcst.core.annotations`.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from pcst.path import BASE_PATH


class SchemaValidationError(ValueError):
    """A JSON value does not conform to one of the PCST schemas."""


def _schema_file(name: str) -> Path:
    """Resolve a schema both from a source checkout and a bundled install."""

    candidates = (
        # Nuitka standalone bundle (``nuitka-built.ps1`` copies schemas here).
        BASE_PATH / "schemas" / name,
        # ``src/pcst/core/schema.py`` -> repository root.
        Path(__file__).resolve().parents[3] / "schemas" / name,
        # Wheel data included next to the installed ``pcst`` package.
        Path(__file__).resolve().parents[2] / "schemas" / name,
        # Optional package-data location for a future wheel/Nuitka bundle.
        Path(__file__).resolve().parent.parent / "schemas" / name,
        Path.cwd() / "schemas" / name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SchemaValidationError(f"schema file not found: {name}")


def load_schema(name: str) -> dict[str, Any]:
    try:
        with _schema_file(name).open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"cannot read schema {name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SchemaValidationError(f"schema {name} must be a JSON object")
    return payload


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        # bool is an int subclass in Python, but is not a JSON integer.
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _format_path(path: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{path}[{key}]"
    return f"{path}.{key}" if path else key


def validate_json_schema(
    value: Any,
    schema: Mapping[str, Any],
    *,
    path: str = "$",
) -> None:
    """Validate a JSON-compatible value against the supported schema subset."""

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(
            f"{path} must equal {schema['const']!r}; got {value!r}"
        )

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = (
            expected_type if isinstance(expected_type, list) else [expected_type]
        )
        if not any(_type_matches(value, str(item)) for item in expected_types):
            expected = " or ".join(str(item) for item in expected_types)
            raise SchemaValidationError(
                f"{path} must be {expected}; got {type(value).__name__}"
            )

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < int(min_length):
            raise SchemaValidationError(
                f"{path} must contain at least {min_length} characters"
            )

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            raise SchemaValidationError(f"{path} must be finite")
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaValidationError(
                f"{path} must be >= {schema['minimum']}; got {value}"
            )
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise SchemaValidationError(
                f"{path} must be > {schema['exclusiveMinimum']}; got {value}"
            )

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            raise SchemaValidationError(
                f"{path} must contain at least {schema['minItems']} items"
            )
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise SchemaValidationError(
                f"{path} must contain at most {schema['maxItems']} items"
            )
        prefix_items = schema.get("prefixItems")
        if isinstance(prefix_items, list):
            for index, item_schema in enumerate(prefix_items):
                if index < len(value):
                    validate_json_schema(
                        value[index], item_schema, path=_format_path(path, index)
                    )
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                validate_json_schema(item, item_schema, path=_format_path(path, index))

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise SchemaValidationError(f"{path}.properties must be an object")
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise SchemaValidationError(f"{path}.required must be an array")
        for key in required:
            if key not in value:
                raise SchemaValidationError(f"{_format_path(path, str(key))} is required")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                validate_json_schema(
                    item, properties[key], path=_format_path(path, str(key))
                )
            elif additional is False:
                raise SchemaValidationError(
                    f"{_format_path(path, str(key))} is not allowed by the schema"
                )
            elif isinstance(additional, Mapping):
                validate_json_schema(
                    item, additional, path=_format_path(path, str(key))
                )


def validate_boxes_payload(payload: Any) -> None:
    validate_json_schema(payload, load_schema("boxes.schema.json"))


def validate_dataset_payload(payload: Any) -> None:
    validate_json_schema(payload, load_schema("dataset.schema.json"))


__all__ = [
    "SchemaValidationError",
    "load_schema",
    "validate_boxes_payload",
    "validate_dataset_payload",
    "validate_json_schema",
]
