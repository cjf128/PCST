"""与 UI 解耦的 3D AABB annotation 模型和 JSON 持久化。"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from numbers import Integral
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pcst.core.geometry import CoordinateService, GeometryValidationError, VolumeGeometry
from pcst.core.schema import SchemaValidationError, validate_boxes_payload


SCHEMA_NAME = "medical-3d-box"
SCHEMA_VERSION = "1.0.0"


class AnnotationValidationError(ValueError):
    """annotation 文档或 annotation 对象不符合 schema。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _string_or_none(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AnnotationValidationError(f"{field_name} must be a non-empty string or null")
    return value


def _validate_json_value(value: Any, field_name: str) -> None:
    """Reject values that would be silently lost by ``json.dump``."""

    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if isfinite(value):
            return
        raise AnnotationValidationError(f"{field_name} must contain finite numbers")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{field_name}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AnnotationValidationError(
                    f"{field_name} object keys must be strings"
                )
            _validate_json_value(item, f"{field_name}.{key}")
        return
    raise AnnotationValidationError(
        f"{field_name} contains unsupported value type {type(value).__name__}"
    )


def _validate_json_object(value: dict[str, Any], field_name: str) -> None:
    if not isinstance(value, dict):
        raise AnnotationValidationError(f"{field_name} must be an object")
    _validate_json_value(value, field_name)


@dataclass(frozen=True, slots=True)
class BoxGeometry:
    """三维 axis-aligned bounding box，使用 half-open IJK。"""

    min_ijk: tuple[int, int, int]
    max_ijk_exclusive: tuple[int, int, int]

    def __post_init__(self) -> None:
        try:
            min_count = len(self.min_ijk)
            max_count = len(self.max_ijk_exclusive)
        except TypeError as exc:
            raise AnnotationValidationError(
                "bbox boundaries must contain three values"
            ) from exc
        if min_count != 3 or max_count != 3:
            raise AnnotationValidationError("bbox boundaries must contain three values")
        normalized_min = []
        normalized_max = []
        for lower, upper in zip(self.min_ijk, self.max_ijk_exclusive):
            if isinstance(lower, bool) or isinstance(upper, bool) or not isinstance(lower, Integral) or not isinstance(upper, Integral):
                raise AnnotationValidationError("bbox boundaries must be integers")
            lower_int = int(lower)
            upper_int = int(upper)
            if lower_int < 0 or upper_int <= 0 or lower_int >= upper_int:
                raise AnnotationValidationError(
                    "bbox must satisfy 0 <= min_ijk < max_ijk_exclusive"
                )
            normalized_min.append(lower_int)
            normalized_max.append(upper_int)
        object.__setattr__(self, "min_ijk", tuple(normalized_min))
        object.__setattr__(self, "max_ijk_exclusive", tuple(normalized_max))

    def validate(self, geometry: VolumeGeometry) -> "BoxGeometry":
        service = CoordinateService(geometry)
        min_values, max_values = service.validate_bbox(
            self.min_ijk, self.max_ijk_exclusive
        )
        return BoxGeometry(min_values, max_values)

    @property
    def dimensions_ijk(self) -> tuple[int, int, int]:
        return tuple(
            upper - lower
            for lower, upper in zip(self.min_ijk, self.max_ijk_exclusive)
        )

    @property
    def voxel_count(self) -> int:
        i_size, j_size, k_size = self.dimensions_ijk
        return i_size * j_size * k_size

    def physical_size_mm(self, geometry: VolumeGeometry) -> tuple[float, float, float]:
        """按 I/J/K 轴返回动态物理尺寸，不写入 JSON。"""

        self.validate(geometry)
        return tuple(
            float(length) * float(spacing)
            for length, spacing in zip(self.dimensions_ijk, geometry.spacing_mm)
        )

    def physical_volume_mm3(self, geometry: VolumeGeometry) -> float:
        size_i, size_j, size_k = self.physical_size_mm(geometry)
        return size_i * size_j * size_k

    def contains(self, ijk: Sequence[int]) -> bool:
        try:
            if len(ijk) != 3:
                return False
        except TypeError:
            return False
        if any(isinstance(value, bool) or not isinstance(value, Integral) for value in ijk):
            return False
        return all(
            lower <= int(value) < upper
            for value, lower, upper in zip(
                ijk, self.min_ijk, self.max_ijk_exclusive
            )
        )

    def overlaps(self, other: "BoxGeometry") -> bool:
        if not isinstance(other, BoxGeometry):
            return False
        return all(
            left_min < right_max and right_min < left_max
            for left_min, left_max, right_min, right_max in zip(
                self.min_ijk,
                self.max_ijk_exclusive,
                other.min_ijk,
                other.max_ijk_exclusive,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "aabb",
            "space": "voxel_index",
            "bbox": {
                "min_ijk": list(self.min_ijk),
                "max_ijk_exclusive": list(self.max_ijk_exclusive),
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BoxGeometry":
        if not isinstance(payload, Mapping):
            raise AnnotationValidationError("annotation geometry must be an object")
        extra_fields = set(payload).difference({"type", "space", "bbox"})
        if extra_fields:
            raise AnnotationValidationError(
                "annotation geometry contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_fields))
            )
        if payload.get("type") != "aabb":
            raise AnnotationValidationError("annotation geometry.type must be aabb")
        if payload.get("space") != "voxel_index":
            raise AnnotationValidationError(
                "annotation geometry.space must be voxel_index"
            )
        bbox = payload.get("bbox")
        if not isinstance(bbox, Mapping):
            raise AnnotationValidationError("annotation geometry.bbox must be an object")
        extra_bbox_fields = set(bbox).difference({"min_ijk", "max_ijk_exclusive"})
        if extra_bbox_fields:
            raise AnnotationValidationError(
                "annotation bbox contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_bbox_fields))
            )
        try:
            min_ijk = tuple(bbox["min_ijk"])
            max_ijk_exclusive = tuple(bbox["max_ijk_exclusive"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AnnotationValidationError(
                "annotation bbox must contain integer min_ijk and max_ijk_exclusive"
            ) from exc
        if len(min_ijk) != 3 or len(max_ijk_exclusive) != 3:
            raise AnnotationValidationError("annotation bbox boundaries must have length 3")
        return cls(min_ijk=min_ijk, max_ijk_exclusive=max_ijk_exclusive)

    @classmethod
    def from_inclusive_points(
        cls,
        start_ijk: Sequence[int],
        end_ijk: Sequence[int],
    ) -> "BoxGeometry":
        """Normalize two inclusive voxel points into a half-open box."""

        try:
            if len(start_ijk) != 3 or len(end_ijk) != 3:
                raise AnnotationValidationError("bbox points must contain three values")
        except TypeError as exc:
            raise AnnotationValidationError("bbox points must contain three values") from exc
        try:
            starts = tuple(int(value) for value in start_ijk)
            ends = tuple(int(value) for value in end_ijk)
        except (TypeError, ValueError, OverflowError) as exc:
            raise AnnotationValidationError("bbox points must be integers") from exc
        if any(
            isinstance(value, bool) or not isinstance(value, Integral)
            for value in (*start_ijk, *end_ijk)
        ):
            raise AnnotationValidationError("bbox points must be integers")
        minimum = tuple(min(left, right) for left, right in zip(starts, ends))
        maximum_exclusive = tuple(max(left, right) + 1 for left, right in zip(starts, ends))
        return cls(minimum, maximum_exclusive)


# Public name used by the domain design document.  Keep ``BoxGeometry`` as
# the implementation name for compatibility with the existing widgets.
BoundingBox3D = BoxGeometry


@dataclass(frozen=True, slots=True)
class Relation:
    type: str
    target_lesion_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.type, str) or not self.type.strip():
            raise AnnotationValidationError("relation.type must not be empty")
        if not isinstance(self.target_lesion_id, str) or not self.target_lesion_id.strip():
            raise AnnotationValidationError("relation.target_lesion_id must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {"type": self.type, "target_lesion_id": self.target_lesion_id}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Relation":
        if not isinstance(payload, Mapping):
            raise AnnotationValidationError("relation must be an object")
        extra_fields = set(payload).difference({"type", "target_lesion_id"})
        if extra_fields:
            raise AnnotationValidationError(
                "relation contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_fields))
            )
        relation_type = payload.get("type")
        target_lesion_id = payload.get("target_lesion_id")
        if not isinstance(relation_type, str) or not isinstance(target_lesion_id, str):
            raise AnnotationValidationError(
                "relation must contain type and target_lesion_id"
            )
        return cls(type=relation_type, target_lesion_id=target_lesion_id)


@dataclass(slots=True)
class Annotation3D:
    id: str
    lesion_id: str | None
    class_id: int
    geometry: BoxGeometry
    relations: list[Relation] = field(default_factory=list)
    attributes: dict[str, Any] = field(
        default_factory=lambda: {"reviewed": False, "note": ""}
    )

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise AnnotationValidationError("annotation id must not be empty")
        if self.lesion_id is not None and (
            not isinstance(self.lesion_id, str) or not self.lesion_id.strip()
        ):
            raise AnnotationValidationError("lesion_id must be non-empty or null")
        if isinstance(self.class_id, bool) or not isinstance(self.class_id, Integral):
            raise AnnotationValidationError("class_id must be a non-negative integer")
        normalized_class_id = int(self.class_id)
        if normalized_class_id < 0:
            raise AnnotationValidationError("class_id must be non-negative")
        self.class_id = normalized_class_id
        if not isinstance(self.relations, list):
            raise AnnotationValidationError("relations must be an array")
        self.relations = [
            relation if isinstance(relation, Relation) else Relation.from_dict(relation)
            for relation in self.relations
        ]
        if not isinstance(self.attributes, dict):
            raise AnnotationValidationError("attributes must be an object")
        _validate_json_object(self.attributes, "attributes")

    @classmethod
    def new(
        cls,
        *,
        class_id: int,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
        lesion_id: str | None = None,
    ) -> "Annotation3D":
        annotation_id = f"ann_{uuid.uuid4().hex}"
        if lesion_id is None:
            lesion_id = f"lesion_{uuid.uuid4().hex[:12]}"
        return cls(
            id=annotation_id,
            lesion_id=lesion_id,
            class_id=class_id,
            geometry=BoxGeometry(
                tuple(min_ijk),
                tuple(max_ijk_exclusive),
            ),
            attributes={"reviewed": False, "note": ""},
        )

    def validate(self, image_geometry: VolumeGeometry) -> "Annotation3D":
        # 允许 UI 在编辑对象后再次校验所有标量字段；几何仍由统一
        # CoordinateService 检查，避免只检查 bbox 而放过非法 class/ID。
        self.__post_init__()
        try:
            self.geometry.validate(image_geometry)
        except GeometryValidationError as exc:
            raise AnnotationValidationError(f"annotation {self.id}: {exc}") from exc
        return self

    def copy(self) -> "Annotation3D":
        return Annotation3D(
            id=self.id,
            lesion_id=self.lesion_id,
            class_id=self.class_id,
            geometry=BoxGeometry(
                tuple(self.geometry.min_ijk),
                tuple(self.geometry.max_ijk_exclusive),
            ),
            relations=list(self.relations),
            attributes=deepcopy(self.attributes),
        )

    def statistics(self, image_geometry: VolumeGeometry) -> dict[str, Any]:
        """Return dynamic voxel/physical statistics (never persisted as truth)."""

        self.validate(image_geometry)
        dimensions = self.geometry.dimensions_ijk
        physical_size = self.geometry.physical_size_mm(image_geometry)
        return {
            "voxel_size": list(dimensions),
            "voxel_count": self.geometry.voxel_count,
            "physical_size_mm": list(physical_size),
            "physical_volume_mm3": self.geometry.physical_volume_mm3(image_geometry),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lesion_id": self.lesion_id,
            "class_id": self.class_id,
            "geometry": self.geometry.to_dict(),
            "relations": [relation.to_dict() for relation in self.relations],
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Annotation3D":
        if not isinstance(payload, Mapping):
            raise AnnotationValidationError("annotation must be an object")
        required_fields = {"id", "lesion_id", "class_id", "geometry", "relations", "attributes"}
        extra_fields = set(payload).difference(required_fields)
        if extra_fields:
            raise AnnotationValidationError(
                "annotation contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_fields))
            )
        missing_fields = required_fields.difference(payload.keys())
        if missing_fields:
            raise AnnotationValidationError(
                "annotation missing required field(s): " + ", ".join(sorted(missing_fields))
            )
        annotation_id = payload.get("id")
        class_id_value = payload.get("class_id")
        if (
            not isinstance(annotation_id, str)
            or not annotation_id.strip()
            or isinstance(class_id_value, bool)
            or not isinstance(class_id_value, int)
        ):
            raise AnnotationValidationError("annotation requires id and integer class_id")
        class_id = class_id_value
        relations_payload = payload.get("relations")
        if not isinstance(relations_payload, list):
            raise AnnotationValidationError("annotation.relations must be an array")
        attributes = payload.get("attributes")
        if not isinstance(attributes, dict):
            raise AnnotationValidationError("annotation.attributes must be an object")
        return cls(
            id=annotation_id,
            lesion_id=_string_or_none(payload.get("lesion_id"), "lesion_id"),
            class_id=class_id,
            geometry=BoxGeometry.from_dict(payload.get("geometry", {})),
            relations=[Relation.from_dict(value) for value in relations_payload],
            attributes=dict(attributes),
        )


@dataclass(slots=True)
class AnnotationDocument:
    """单个病例的 annotation 文件。IJK bbox 是唯一 annotation 真值。"""

    case_id: str
    image_file: str
    image_geometry: VolumeGeometry
    annotations: list[Annotation3D] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    schema: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise AnnotationValidationError("case_id must not be empty")
        if not isinstance(self.image_file, str) or not self.image_file.strip():
            raise AnnotationValidationError("image.file must be a non-empty string")
        if not isinstance(self.image_geometry, VolumeGeometry):
            raise AnnotationValidationError("image_geometry must be VolumeGeometry")
        if not isinstance(self.annotations, list):
            raise AnnotationValidationError("annotations must be an array")
        if not isinstance(self.classes, list):
            raise AnnotationValidationError("classes must be an array")
        if self.schema != SCHEMA_NAME:
            raise AnnotationValidationError(f"unsupported schema: {self.schema}")
        if self.schema_version != SCHEMA_VERSION:
            raise AnnotationValidationError(
                f"unsupported schema_version: {self.schema_version}"
            )
        self._validate_classes()
        self._validate_annotations()

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
            class_id_value = item.get("id")
            name = item.get("name")
            if (
                isinstance(class_id_value, bool)
                or not isinstance(class_id_value, int)
                or not isinstance(name, str)
            ):
                raise AnnotationValidationError("class requires integer id and name")
            class_id = class_id_value
            if class_id < 0 or not name.strip() or class_id in seen:
                raise AnnotationValidationError("class id must be unique and name non-empty")
            seen.add(class_id)
            normalized.append({"id": class_id, "name": name})
        self.classes = normalized

    def _validate_annotations(
        self, annotations: Iterable[Annotation3D] | None = None
    ) -> None:
        items = list(self.annotations if annotations is None else annotations)
        seen_ids: set[str] = set()
        class_ids = {int(item["id"]) for item in self.classes}
        lesion_ids = {
            annotation.lesion_id
            for annotation in items
            if isinstance(annotation, Annotation3D) and annotation.lesion_id is not None
        }
        for annotation in items:
            if not isinstance(annotation, Annotation3D):
                raise AnnotationValidationError("annotations must contain Annotation3D objects")
            if annotation.id in seen_ids:
                raise AnnotationValidationError(f"duplicate annotation id: {annotation.id}")
            seen_ids.add(annotation.id)
            annotation.validate(self.image_geometry)
            if annotation.class_id not in class_ids:
                raise AnnotationValidationError(
                    f"annotation {annotation.id} references unknown class_id {annotation.class_id}"
                )
            for relation in annotation.relations:
                if relation.target_lesion_id not in lesion_ids:
                    raise AnnotationValidationError(
                        f"annotation {annotation.id} relation target lesion_id "
                        f"{relation.target_lesion_id!r} does not exist"
                    )

    def validate(self) -> None:
        """重新执行文档级校验，供保存前和数据完整性检查使用。"""

        self._validate_classes()
        self._validate_annotations()

    @property
    def coordinate_service(self) -> CoordinateService:
        return CoordinateService(self.image_geometry)

    @property
    def lesion_ids(self) -> tuple[str, ...]:
        """Stable sorted semantic lesion IDs referenced by this document."""

        return tuple(
            sorted(
                {
                    annotation.lesion_id
                    for annotation in self.annotations
                    if annotation.lesion_id is not None
                }
            )
        )

    def annotations_for_lesion(self, lesion_id: str) -> tuple[Annotation3D, ...]:
        return tuple(
            annotation
            for annotation in self.annotations
            if annotation.lesion_id == lesion_id
        )

    def add(self, annotation: Annotation3D) -> None:
        if any(item.id == annotation.id for item in self.annotations):
            raise AnnotationValidationError(f"duplicate annotation id: {annotation.id}")
        self._validate_annotations([*self.annotations, annotation])
        self.annotations.append(annotation)

    def get(self, annotation_id: str) -> Annotation3D:
        for annotation in self.annotations:
            if annotation.id == annotation_id:
                return annotation
        raise KeyError(annotation_id)

    def remove(self, annotation_id: str) -> Annotation3D:
        for index, annotation in enumerate(self.annotations):
            if annotation.id == annotation_id:
                candidate = [
                    item for item_index, item in enumerate(self.annotations) if item_index != index
                ]
                self._validate_annotations(candidate)
                return self.annotations.pop(index)
        raise KeyError(annotation_id)

    def update(self, annotation: Annotation3D) -> None:
        for index, current in enumerate(self.annotations):
            if current.id == annotation.id:
                candidate = list(self.annotations)
                candidate[index] = annotation
                self._validate_annotations(candidate)
                self.annotations[index] = annotation
                return
        raise KeyError(annotation.id)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "image": {
                "file": self.image_file,
                **self.image_geometry.to_dict(),
            },
            "coordinate_convention": {
                "bbox_space": "voxel_index",
                "voxel_axes": "IJK",
                "bbox_representation": "min_max",
                "min_boundary": "inclusive",
                "max_boundary": "exclusive",
                "world_coordinate_system": "LPS",
                "physical_unit": "mm",
            },
            "overlap_policy": "allowed",
            "classes": [dict(item) for item in self.classes],
            "annotations": [annotation.to_dict() for annotation in self.annotations],
        }
        try:
            validate_boxes_payload(payload)
        except SchemaValidationError as exc:
            raise AnnotationValidationError(f"schema validation failed: {exc}") from exc
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AnnotationDocument":
        if not isinstance(payload, Mapping):
            raise AnnotationValidationError("annotation document must be an object")
        # Route every load through the explicit version dispatcher.  V1 is a
        # no-op migration, but future schema versions must be registered there
        # instead of being silently interpreted as the current structure.
        try:
            from pcst.core.migrations import MigrationError, migrate_boxes_payload

            payload = migrate_boxes_payload(payload)
        except MigrationError as exc:
            raise AnnotationValidationError(str(exc)) from exc
        try:
            validate_boxes_payload(payload)
        except SchemaValidationError as exc:
            raise AnnotationValidationError(f"schema validation failed: {exc}") from exc
        if payload.get("schema") != SCHEMA_NAME:
            raise AnnotationValidationError(
                f"schema must be {SCHEMA_NAME!r}"
            )
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise AnnotationValidationError(
                f"unsupported schema_version: {payload.get('schema_version')!r}"
            )
        if payload.get("overlap_policy") != "allowed":
            raise AnnotationValidationError("overlap_policy must be allowed")
        image = payload.get("image")
        if not isinstance(image, Mapping):
            raise AnnotationValidationError("image must be an object")
        if "annotations" not in payload:
            raise AnnotationValidationError("annotations is required")
        annotations_payload = payload.get("annotations")
        if not isinstance(annotations_payload, list):
            raise AnnotationValidationError("annotations must be an array")
        if "classes" not in payload:
            raise AnnotationValidationError("classes is required")
        classes = payload.get("classes")
        if not isinstance(classes, list):
            raise AnnotationValidationError("classes must be an array")
        case_id = payload.get("case_id")
        image_file = image.get("file")
        if not isinstance(case_id, str) or not case_id.strip():
            raise AnnotationValidationError("case_id must be a non-empty string")
        if not isinstance(image_file, str) or not image_file.strip():
            raise AnnotationValidationError("image.file must be a non-empty string")
        try:
            image_geometry = VolumeGeometry.from_dict(dict(image))
            return cls(
                case_id=case_id,
                image_file=image_file,
                image_geometry=image_geometry,
                annotations=[Annotation3D.from_dict(item) for item in annotations_payload],
                classes=list(classes),
            )
        except GeometryValidationError as exc:
            raise AnnotationValidationError(f"invalid image geometry: {exc}") from exc

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
    def load(cls, path: str | Path) -> "AnnotationDocument":
        target = Path(path)
        try:
            with target.open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
        except json.JSONDecodeError as exc:
            raise AnnotationValidationError(f"invalid JSON: {exc}") from exc
        except (OSError, UnicodeError) as exc:
            raise AnnotationValidationError(f"cannot read annotation file: {exc}") from exc
        return cls.from_dict(payload)


__all__ = [
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "Annotation3D",
    "AnnotationDocument",
    "AnnotationValidationError",
    "BoundingBox3D",
    "BoxGeometry",
    "Relation",
]
