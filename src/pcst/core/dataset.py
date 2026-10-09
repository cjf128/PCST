"""Dataset-level manifest for canonical 3D box projects.

The manifest deliberately contains only project conventions and class
definitions.  Per-case image geometry and annotations live in the individual
``*.boxes.json`` files, so an annotation remains portable and independently
validatable.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from pcst.core.annotations import AnnotationValidationError, SCHEMA_NAME, SCHEMA_VERSION
from pcst.core.schema import SchemaValidationError, validate_dataset_payload


@dataclass(slots=True)
class DatasetManifest:
    """The canonical ``dataset.json`` metadata document."""

    classes: list[dict[str, Any]] = field(default_factory=list)
    schema: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    dimension: int = 3
    annotation_type: str = "aabb"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_NAME:
            raise AnnotationValidationError(f"unsupported schema: {self.schema}")
        if self.schema_version != SCHEMA_VERSION:
            raise AnnotationValidationError(
                f"unsupported schema_version: {self.schema_version}"
            )
        if self.dimension != 3 or self.annotation_type != "aabb":
            raise AnnotationValidationError(
                "dataset dimension must be 3 and annotation_type must be aabb"
            )
        if not isinstance(self.classes, list):
            raise AnnotationValidationError("classes must be an array")
        self._validate_classes()

    def _validate_classes(self) -> None:
        seen: set[int] = set()
        normalized: list[dict[str, Any]] = []
        for item in self.classes:
            if not isinstance(item, Mapping):
                raise AnnotationValidationError("classes entries must be objects")
            extra_fields = set(item).difference({"id", "name"})
            if extra_fields:
                raise AnnotationValidationError(
                    "class contains unsupported field(s): "
                    + ", ".join(sorted(str(value) for value in extra_fields))
                )
            class_id = item.get("id")
            name = item.get("name")
            if (
                isinstance(class_id, bool)
                or not isinstance(class_id, int)
                or class_id < 0
                or not isinstance(name, str)
                or not name.strip()
                or class_id in seen
            ):
                raise AnnotationValidationError(
                    "class requires a unique non-negative integer id and non-empty name"
                )
            seen.add(class_id)
            normalized.append({"id": class_id, "name": name})
        self.classes = normalized

    @property
    def coordinate_convention(self) -> dict[str, str]:
        return {
            "bbox_space": "voxel_index",
            "voxel_axes": "IJK",
            "bbox_representation": "min_max",
            "min_boundary": "inclusive",
            "max_boundary": "exclusive",
            "world_coordinate_system": "LPS",
            "physical_unit": "mm",
        }

    def to_dict(self) -> dict[str, Any]:
        self._validate_classes()
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "dimension": self.dimension,
            "annotation_type": self.annotation_type,
            "coordinate_convention": self.coordinate_convention,
            "overlap_policy": "allowed",
            "classes": [dict(item) for item in self.classes],
        }
        try:
            validate_dataset_payload(payload)
        except SchemaValidationError as exc:
            raise AnnotationValidationError(f"schema validation failed: {exc}") from exc
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DatasetManifest":
        if not isinstance(payload, Mapping):
            raise AnnotationValidationError("dataset manifest must be an object")
        try:
            validate_dataset_payload(payload)
        except SchemaValidationError as exc:
            raise AnnotationValidationError(f"schema validation failed: {exc}") from exc
        return cls(
            schema=payload["schema"],
            schema_version=payload["schema_version"],
            dimension=payload["dimension"],
            annotation_type=payload["annotation_type"],
            classes=list(payload["classes"]),
        )

    def save_atomic(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise
        return target

    @classmethod
    def load(cls, path: str | Path) -> "DatasetManifest":
        target = Path(path)
        try:
            with target.open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
        except json.JSONDecodeError as exc:
            raise AnnotationValidationError(f"invalid JSON: {exc}") from exc
        except (OSError, UnicodeError) as exc:
            raise AnnotationValidationError(f"cannot read dataset manifest: {exc}") from exc
        return cls.from_dict(payload)


__all__ = ["DatasetManifest"]
