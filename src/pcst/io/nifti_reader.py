"""SimpleITK based NIfTI reader with an explicit KJI/IJK boundary."""

from __future__ import annotations

from pathlib import Path

import SimpleITK as sitk

from pcst.core.geometry import GeometryValidationError, VolumeGeometry
from pcst.core.image import MedicalImage


class NiftiReadError(ValueError):
    """A NIfTI path could not be read or has invalid image geometry."""


def is_nifti_path(path: str | Path) -> bool:
    """Return whether *path* has a supported NIfTI extension."""

    name = str(path).lower()
    return name.endswith(".nii") or name.endswith(".nii.gz")


def _validate_path(path: str | Path) -> Path:
    target = Path(path)
    if not is_nifti_path(target):
        raise NiftiReadError("only .nii and .nii.gz files are supported")
    if not target.is_file():
        raise NiftiReadError(f"NIfTI file does not exist: {target}")
    return target


def read_nifti_sitk(path: str | Path, *, orient_lps: bool = False) -> sitk.Image:
    """Read a NIfTI image and return its SimpleITK representation.

    ``orient_lps=True`` applies the same canonical orientation policy as the
    desktop pipeline.  SimpleITK preserves oblique direction cosines when
    they cannot be represented by a cardinal reorientation; the resulting
    image's ``GetSize/GetSpacing/GetOrigin/GetDirection`` is therefore the
    geometry that accompanies the returned NumPy data.
    """

    target = _validate_path(path)
    try:
        image = sitk.ReadImage(str(target))
        if image.GetDimension() != 3:
            raise NiftiReadError(
                f"NIfTI image must be 3D; got dimension {image.GetDimension()}"
            )
        if orient_lps:
            image = sitk.DICOMOrient(image, "LPS")
        # Construct once here so malformed direction/spacing fails at the IO
        # boundary rather than much later during annotation editing.
        VolumeGeometry.from_sitk(image)
        return image
    except NiftiReadError:
        raise
    except (GeometryValidationError, RuntimeError, OSError, ValueError) as exc:
        raise NiftiReadError(f"cannot read NIfTI image {target}: {exc}") from exc


def read_nifti(path: str | Path, *, orient_lps: bool = False) -> MedicalImage:
    """Read a NIfTI file as ``MedicalImage(data_kji, geometry)``."""

    target = _validate_path(path)
    image = read_nifti_sitk(target, orient_lps=orient_lps)
    try:
        return MedicalImage.from_sitk(image, source_path=target)
    except (GeometryValidationError, ValueError, TypeError) as exc:
        raise NiftiReadError(f"invalid NIfTI geometry/data {target}: {exc}") from exc


__all__ = ["NiftiReadError", "is_nifti_path", "read_nifti", "read_nifti_sitk"]
