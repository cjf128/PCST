"""Medical-image and canonical annotation IO helpers.

The UI imports these helpers through this package instead of implementing a
second coordinate or JSON conversion path.  The modules intentionally keep
the public API small so future DICOM/NRRD readers can be added without
changing the annotation model.
"""

from pcst.io.annotation_reader import AnnotationReadError, read_annotations
from pcst.io.annotation_writer import AnnotationWriteError, write_annotations
from pcst.io.nifti_reader import (
    NiftiReadError,
    is_nifti_path,
    read_nifti,
    read_nifti_sitk,
)

__all__ = [
    "AnnotationReadError",
    "AnnotationWriteError",
    "NiftiReadError",
    "is_nifti_path",
    "read_annotations",
    "read_nifti",
    "read_nifti_sitk",
    "write_annotations",
]
