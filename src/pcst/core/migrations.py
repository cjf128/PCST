"""Versioned migration entry point for canonical annotation documents.

V1 has only one schema version.  The explicit dispatcher is intentional:
future versions must add a named migration instead of silently accepting or
dropping fields from an older file.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from pcst.core.annotations import SCHEMA_NAME, SCHEMA_VERSION


class MigrationError(ValueError):
    """The input document cannot be migrated to the requested schema."""


def migrate_boxes_payload(
    payload: Mapping[str, Any], *, target_version: str = SCHEMA_VERSION
) -> dict[str, Any]:
    """Return a migrated copy of a canonical payload.

    The current release is deliberately conservative: a 1.0.0 payload is
    copied without mutation, while missing/unknown versions fail with an
    actionable message.  This prevents a future schema from being mistaken
    for V1 and losing annotation data.
    """

    if not isinstance(payload, Mapping):
        raise MigrationError("annotation document must be an object")
    if target_version != SCHEMA_VERSION:
        raise MigrationError(f"unsupported target schema_version: {target_version!r}")
    schema = payload.get("schema")
    version = payload.get("schema_version")
    if schema != SCHEMA_NAME:
        raise MigrationError(f"unsupported schema: {schema!r}")
    if version != SCHEMA_VERSION:
        raise MigrationError(
            f"unsupported schema_version: {version!r}; supported version is {SCHEMA_VERSION}"
        )
    return deepcopy(dict(payload))


__all__ = ["MigrationError", "migrate_boxes_payload"]
