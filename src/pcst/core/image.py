"""医学图像数据对象，保留 voxel data 和完整 geometry。

The array contract in this module is deliberately explicit: NumPy data is
``KJI`` (the order returned by :func:`SimpleITK.GetArrayFromImage`), while
``VolumeGeometry`` and every annotation use ``IJK``.  Keeping this object at
the IO boundary prevents callers from accidentally throwing away direction,
origin or spacing metadata when converting an image to NumPy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from pcst.core.geometry import VolumeGeometry


@dataclass(slots=True)
class MedicalImage:
    """One scalar medical image and its canonical image geometry.

    ``data_kji`` is never silently transposed.  Callers that need an IJK
    index should use :class:`pcst.core.geometry.CoordinateService` (or the
    explicit ``ijk_to_kji`` helpers) instead of guessing NumPy axis order.
    """

    data_kji: np.ndarray
    geometry: VolumeGeometry
    source_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data_kji = np.asarray(self.data_kji)
        if self.data_kji.ndim != 3:
            raise ValueError("medical image data must be a 3D KJI array")
        if not isinstance(self.geometry, VolumeGeometry):
            raise TypeError("geometry must be VolumeGeometry")
        expected_shape = tuple(reversed(self.geometry.size_ijk))
        if tuple(int(value) for value in self.data_kji.shape) != expected_shape:
            raise ValueError(
                "medical image KJI shape does not match geometry size_ijk: "
                f"{self.data_kji.shape} vs {expected_shape}"
            )
        if self.source_path is not None:
            self.source_path = Path(self.source_path)
        if not isinstance(self.metadata, dict):
            self.metadata = dict(self.metadata or {})

    @property
    def size_ijk(self) -> tuple[int, int, int]:
        return self.geometry.size_ijk

    @property
    def shape_kji(self) -> tuple[int, int, int]:
        return tuple(int(value) for value in self.data_kji.shape)

    @classmethod
    def from_sitk(
        cls,
        image,
        *,
        source_path: Path | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "MedicalImage":
        """Create a ``MedicalImage`` without losing SimpleITK geometry."""

        geometry = VolumeGeometry.from_sitk(image)
        import SimpleITK as sitk

        return cls(
            data_kji=np.asarray(sitk.GetArrayFromImage(image)),
            geometry=geometry,
            source_path=Path(source_path) if source_path is not None else None,
            metadata=dict(metadata or {}),
        )

    def to_sitk(self):
        """Return a SimpleITK image carrying this object's full geometry."""

        import SimpleITK as sitk

        image = sitk.GetImageFromArray(np.asarray(self.data_kji))
        image.SetSpacing(self.geometry.spacing_mm)
        image.SetOrigin(self.geometry.origin_lps_mm)
        image.SetDirection(self.geometry.direction_ijk_to_lps)
        return image


@dataclass(slots=True)
class LoadedVolume:
    """Worker 传递给 UI 的一次加载结果。

    ``ct_data``/``pet_data`` 的 NumPy 顺序是 KJI；所有 geometry 的 index 顺序是
    IJK。CT geometry 是当前配准后 viewer/annotation 使用的 canonical geometry。
    """

    ct_data: np.ndarray
    pet_data: np.ndarray
    ct_geometry: VolumeGeometry
    pet_geometry: VolumeGeometry | None = None
    patient_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.ct_geometry, VolumeGeometry):
            raise TypeError("ct_geometry must be VolumeGeometry")
        if self.pet_geometry is not None and not isinstance(
            self.pet_geometry, VolumeGeometry
        ):
            raise TypeError("pet_geometry must be VolumeGeometry or None")
        self.ct_data = np.asarray(self.ct_data)
        self.pet_data = np.asarray(self.pet_data)
        if self.ct_data.ndim != 3 or self.pet_data.ndim != 3:
            raise ValueError("CT/PET voxel data must be 3D KJI arrays")
        expected_ct_shape = tuple(reversed(self.ct_geometry.size_ijk))
        if tuple(int(value) for value in self.ct_data.shape) != expected_ct_shape:
            raise ValueError(
                "CT KJI shape does not match geometry size_ijk: "
                f"{self.ct_data.shape} vs {expected_ct_shape}"
            )
        if tuple(int(value) for value in self.pet_data.shape) != tuple(
            int(value) for value in self.ct_data.shape
        ):
            raise ValueError("resampled PET KJI shape must match CT KJI shape")
        if not isinstance(self.patient_info, dict):
            self.patient_info = dict(self.patient_info or {})

    @property
    def pet_shape_kji(self) -> tuple[int, int, int]:
        return tuple(int(value) for value in self.pet_data.shape)


__all__ = ["MedicalImage", "LoadedVolume"]
