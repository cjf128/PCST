"""Annotation model compatibility module.

All canonical annotation classes are implemented in ``annotations.py``; this
module intentionally re-exports them so UI and future services can import a
stable singular module name without duplicating the data model.
"""

from pcst.core.annotations import (
    Annotation3D,
    AnnotationDocument,
    AnnotationValidationError,
    BoundingBox3D,
    BoxGeometry,
    Relation,
)
from pcst.core.dataset import DatasetManifest

__all__ = [
    "Annotation3D",
    "AnnotationDocument",
    "AnnotationValidationError",
    "BoundingBox3D",
    "BoxGeometry",
    "Relation",
    "DatasetManifest",
]
