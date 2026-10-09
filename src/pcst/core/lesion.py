"""Small semantic lesion model kept separate from box geometry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pcst.core.annotations import AnnotationValidationError, _validate_json_object


@dataclass(slots=True)
class Lesion:
    """A medical entity that may own one or more :class:`Annotation3D` boxes.

    The canonical V1 JSON stores ``lesion_id`` on each annotation and does not
    require a separate lesion array.  This class is a semantic helper for
    grouping/editing annotations; it deliberately contains no geometry.
    """

    id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise AnnotationValidationError("lesion id must not be empty")
        if not isinstance(self.attributes, dict):
            raise AnnotationValidationError("lesion attributes must be an object")
        _validate_json_object(self.attributes, "lesion attributes")


__all__ = ["Lesion"]
