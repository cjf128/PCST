"""PCST domain primitives that do not depend on the Qt UI."""

from pcst.core.annotations import (
    Annotation3D,
    AnnotationDocument,
    AnnotationValidationError,
    BoundingBox3D,
    BoxGeometry,
    Relation,
)
from pcst.core.image import LoadedVolume
from pcst.core.dataset import DatasetManifest
from pcst.core.image import MedicalImage
from pcst.core.lesion import Lesion
from pcst.core.migrations import MigrationError, migrate_boxes_payload
from pcst.core.geometry import CoordinateService, VolumeGeometry
from pcst.core.schema import (
    SchemaValidationError,
    load_schema,
    validate_boxes_payload,
    validate_dataset_payload,
)
from pcst.core.validation import (
    ValidationReport,
    validate_annotation_document,
    validate_dataset_directory,
)

__all__ = [
    "Annotation3D",
    "AnnotationDocument",
    "AnnotationValidationError",
    "BoundingBox3D",
    "BoxGeometry",
    "CoordinateService",
    "LoadedVolume",
    "MedicalImage",
    "DatasetManifest",
    "Lesion",
    "MigrationError",
    "migrate_boxes_payload",
    "Relation",
    "VolumeGeometry",
    "SchemaValidationError",
    "load_schema",
    "validate_boxes_payload",
    "validate_dataset_payload",
    "ValidationReport",
    "validate_annotation_document",
    "validate_dataset_directory",
]
