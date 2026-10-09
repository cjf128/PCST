"""医学图像几何和坐标转换。

项目中三类坐标必须明确区分：

* IJK：SimpleITK image index，annotation 的唯一空间；
* KJI：NumPy ``GetArrayFromImage`` 的数组顺序；
* LPS：患者/世界物理坐标，单位为 mm。

这里不假设方向矩阵为 identity，也不把物理坐标写回 annotation 作为第二份真值。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Integral
from typing import Iterable, Sequence

import numpy as np


class GeometryValidationError(ValueError):
    """图像几何元信息不合法。"""


def _as_float_tuple(values: Sequence[float], *, length: int, name: str) -> tuple[float, ...]:
    try:
        value_count = len(values)
    except TypeError as exc:
        raise GeometryValidationError(f"{name} must contain {length} values") from exc
    if value_count != length:
        raise GeometryValidationError(f"{name} must contain {length} values")
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise GeometryValidationError(f"{name} must contain numeric values") from exc
    if not all(isfinite(value) for value in result):
        raise GeometryValidationError(f"{name} must contain finite values")
    return result


@dataclass(frozen=True, slots=True)
class VolumeGeometry:
    """一个医学图像的 IJK → LPS 几何信息。

    ``size_ijk`` 和 ``spacing_mm`` 的顺序均为 ``[I, J, K]``；
    NumPy 数据本身仍然使用 ``[K, J, I]``。
    ``direction_ijk_to_lps`` 使用 SimpleITK 的 row-major 9 元素表示。
    """

    size_ijk: tuple[int, int, int]
    spacing_mm: tuple[float, float, float]
    origin_lps_mm: tuple[float, float, float]
    direction_ijk_to_lps: tuple[float, ...]
    world_coordinate_system: str = "LPS"

    def __post_init__(self) -> None:
        try:
            size_count = len(self.size_ijk)
        except TypeError as exc:
            raise GeometryValidationError(
                "size_ijk must contain three positive integers"
            ) from exc
        if size_count != 3 or any(
            isinstance(value, bool) or not isinstance(value, Integral) or int(value) <= 0
            for value in self.size_ijk
        ):
            raise GeometryValidationError("size_ijk must contain three positive integers")
        normalized_size = tuple(int(value) for value in self.size_ijk)
        object.__setattr__(self, "size_ijk", normalized_size)

        spacing = _as_float_tuple(self.spacing_mm, length=3, name="spacing_mm")
        if any(value <= 0 for value in spacing):
            raise GeometryValidationError("spacing_mm must contain positive values")
        object.__setattr__(self, "spacing_mm", spacing)

        origin = _as_float_tuple(self.origin_lps_mm, length=3, name="origin_lps_mm")
        object.__setattr__(self, "origin_lps_mm", origin)

        direction = _as_float_tuple(
            self.direction_ijk_to_lps, length=9, name="direction_ijk_to_lps"
        )
        matrix = np.asarray(direction, dtype=np.float64).reshape(3, 3)
        determinant = float(np.linalg.det(matrix))
        if abs(determinant) < 1e-8:
            raise GeometryValidationError("direction_ijk_to_lps must be invertible")
        # SimpleITK stores direction cosines.  A valid medical-image direction
        # is an orthonormal basis (allowing a left/right handed flip), not an
        # arbitrary invertible scale/shear matrix.
        if not np.allclose(
            matrix.T @ matrix,
            np.eye(3, dtype=np.float64),
            atol=1e-4,
            rtol=0.0,
        ) or not np.isclose(abs(determinant), 1.0, atol=1e-4, rtol=0.0):
            raise GeometryValidationError(
                "direction_ijk_to_lps must be an orthonormal direction-cosine matrix"
            )
        object.__setattr__(self, "direction_ijk_to_lps", direction)

        if self.world_coordinate_system != "LPS":
            raise GeometryValidationError("world_coordinate_system must be LPS")

    @classmethod
    def from_sitk(cls, image) -> "VolumeGeometry":
        """从 SimpleITK Image 保留完整几何信息。"""

        return cls(
            size_ijk=tuple(int(value) for value in image.GetSize()),
            spacing_mm=tuple(float(value) for value in image.GetSpacing()),
            origin_lps_mm=tuple(float(value) for value in image.GetOrigin()),
            direction_ijk_to_lps=tuple(
                float(value) for value in image.GetDirection()
            ),
        )

    @property
    def direction_matrix(self) -> np.ndarray:
        return np.asarray(self.direction_ijk_to_lps, dtype=np.float64).reshape(3, 3)

    @property
    def inverse_direction_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.direction_matrix)

    def validate_ijk(self, ijk: Sequence[int], *, allow_max: bool = False) -> tuple[int, int, int]:
        """验证一个 IJK index。

        ``allow_max`` 用于 half-open bbox 的 max 边界，允许它等于 image size。
        """

        try:
            value_count = len(ijk)
        except TypeError as exc:
            raise GeometryValidationError("IJK must contain three values") from exc
        if value_count != 3:
            raise GeometryValidationError("IJK must contain three values")
        normalized_values = []
        for value in ijk:
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise GeometryValidationError("IJK values must be integers")
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise GeometryValidationError("IJK values must be integers") from exc
            if not isfinite(numeric) or numeric != round(numeric):
                raise GeometryValidationError("IJK values must be integers")
            normalized_values.append(int(round(numeric)))
        normalized = tuple(normalized_values)
        upper = self.size_ijk if allow_max else tuple(value - 1 for value in self.size_ijk)
        for axis, value in zip("IJK", normalized):
            index = "IJK".index(axis)
            if value < 0 or value > upper[index]:
                limit = self.size_ijk[index] if allow_max else self.size_ijk[index] - 1
                raise GeometryValidationError(
                    f"{axis} index {value} is outside [0, {limit}]"
                )
        return normalized

    def ijk_to_lps(self, ijk: Sequence[float]) -> tuple[float, float, float]:
        """将 IJK 连续坐标转换为 LPS mm。"""

        try:
            value_count = len(ijk)
        except TypeError as exc:
            raise GeometryValidationError("IJK must contain three values") from exc
        if value_count != 3:
            raise GeometryValidationError("IJK must contain three values")
        try:
            index = np.asarray(tuple(float(value) for value in ijk), dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise GeometryValidationError("IJK values must be numeric") from exc
        if not np.all(np.isfinite(index)):
            raise GeometryValidationError("IJK values must be finite")
        point = np.asarray(self.origin_lps_mm) + self.direction_matrix @ (
            index * np.asarray(self.spacing_mm)
        )
        return tuple(float(value) for value in point)

    def lps_to_ijk(self, lps_mm: Sequence[float]) -> tuple[float, float, float]:
        """将 LPS mm 转换为连续 IJK 坐标。"""

        try:
            value_count = len(lps_mm)
        except TypeError as exc:
            raise GeometryValidationError("LPS must contain three values") from exc
        if value_count != 3:
            raise GeometryValidationError("LPS must contain three values")
        try:
            point = np.asarray(tuple(float(value) for value in lps_mm), dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise GeometryValidationError("LPS values must be numeric") from exc
        if not np.all(np.isfinite(point)):
            raise GeometryValidationError("LPS values must be finite")
        index = self.inverse_direction_matrix @ (
            point - np.asarray(self.origin_lps_mm)
        )
        index = index / np.asarray(self.spacing_mm)
        return tuple(float(value) for value in index)

    def voxel_center_lps(self, ijk: Sequence[int]) -> tuple[float, float, float]:
        self.validate_ijk(ijk)
        return self.ijk_to_lps(ijk)

    def bbox_corner_lps(
        self,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
    ) -> tuple[tuple[float, float, float], ...]:
        """返回 AABB 八个物理边界角点（不作为 annotation 真值）。

        IJK index 指向 voxel center，因此 half-open box 的物理边界连续坐标为
        ``min_ijk - 0.5`` 和 ``max_ijk_exclusive - 0.5``。
        """

        min_values = self.validate_ijk(min_ijk)
        max_values = self.validate_ijk(max_ijk_exclusive, allow_max=True)
        for axis, lower, upper, size in zip(
            "IJK", min_values, max_values, self.size_ijk
        ):
            if not 0 <= lower < upper <= size:
                raise GeometryValidationError(
                    f"invalid bbox on {axis}: {lower} <= {upper} is required within [0, {size}]"
                )
        min_edge = tuple(float(value) - 0.5 for value in min_values)
        max_edge = tuple(float(value) - 0.5 for value in max_values)
        corners: list[tuple[float, float, float]] = []
        for i_value in (min_edge[0], max_edge[0]):
            for j_value in (min_edge[1], max_edge[1]):
                for k_value in (min_edge[2], max_edge[2]):
                    corners.append(self.ijk_to_lps((i_value, j_value, k_value)))
        return tuple(corners)

    def to_dict(self) -> dict:
        return {
            "size_ijk": list(self.size_ijk),
            "geometry": {
                "world_coordinate_system": self.world_coordinate_system,
                "spacing_mm": list(self.spacing_mm),
                "origin_lps_mm": list(self.origin_lps_mm),
                "direction_ijk_to_lps": list(self.direction_ijk_to_lps),
            },
        }

    def almost_equal(self, other: "VolumeGeometry", tolerance: float = 1e-5) -> bool:
        """比较两个图像几何，允许 JSON 浮点序列化误差。"""

        if not isinstance(other, VolumeGeometry) or self.size_ijk != other.size_ijk:
            return False
        return bool(
            np.allclose(self.spacing_mm, other.spacing_mm, atol=tolerance, rtol=0)
            and np.allclose(self.origin_lps_mm, other.origin_lps_mm, atol=tolerance, rtol=0)
            and np.allclose(
                self.direction_ijk_to_lps,
                other.direction_ijk_to_lps,
                atol=tolerance,
                rtol=0,
            )
        )

    @classmethod
    def from_dict(cls, payload: dict) -> "VolumeGeometry":
        if not isinstance(payload, dict):
            raise GeometryValidationError("image geometry must be an object")
        extra_image_fields = set(payload).difference({"file", "size_ijk", "geometry"})
        if extra_image_fields:
            raise GeometryValidationError(
                "image contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_image_fields))
            )
        geometry = payload.get("geometry")
        if not isinstance(geometry, dict):
            raise GeometryValidationError("image geometry.geometry must be an object")
        required_geometry_fields = {
            "world_coordinate_system",
            "spacing_mm",
            "origin_lps_mm",
            "direction_ijk_to_lps",
        }
        missing_geometry_fields = required_geometry_fields.difference(geometry)
        if missing_geometry_fields:
            raise GeometryValidationError(
                "image geometry missing required field(s): "
                + ", ".join(sorted(missing_geometry_fields))
            )
        extra_geometry_fields = set(geometry).difference(required_geometry_fields)
        if extra_geometry_fields:
            raise GeometryValidationError(
                "image geometry contains unsupported field(s): "
                + ", ".join(sorted(str(value) for value in extra_geometry_fields))
            )
        try:
            size_ijk = tuple(payload.get("size_ijk", ()))
            spacing_mm = tuple(geometry.get("spacing_mm", ()))
            origin_lps_mm = tuple(geometry.get("origin_lps_mm", ()))
            direction_ijk_to_lps = tuple(geometry.get("direction_ijk_to_lps", ()))
        except TypeError as exc:
            raise GeometryValidationError("image geometry vectors must be arrays") from exc
        return cls(
            size_ijk=size_ijk,
            spacing_mm=spacing_mm,
            origin_lps_mm=origin_lps_mm,
            direction_ijk_to_lps=direction_ijk_to_lps,
            world_coordinate_system=geometry.get("world_coordinate_system", "LPS"),
        )


class CoordinateService:
    """集中管理 IJK/KJI/LPS 和三正交视图之间的转换。"""

    _VIEW_AXES = {
        "AXIAL": ("I", "J", "K"),
        "SAGITTAL": ("J", "K", "I"),
        "CORONAL": ("I", "K", "J"),
    }

    def __init__(self, geometry: VolumeGeometry):
        self.geometry = geometry

    def ijk_to_lps(self, ijk: Sequence[float]) -> tuple[float, float, float]:
        return self.geometry.ijk_to_lps(ijk)

    def lps_to_ijk(self, lps_mm: Sequence[float]) -> tuple[float, float, float]:
        return self.geometry.lps_to_ijk(lps_mm)

    def bbox_corners_lps(
        self,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
    ) -> tuple[tuple[float, float, float], ...]:
        self.validate_bbox(min_ijk, max_ijk_exclusive)
        return self.geometry.bbox_corner_lps(min_ijk, max_ijk_exclusive)

    def bbox_ijk_to_lps_corners(
        self,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
    ) -> tuple[tuple[float, float, float], ...]:
        """Descriptive alias used by exporters and renderers."""

        return self.bbox_corners_lps(min_ijk, max_ijk_exclusive)

    @staticmethod
    def _view_name(view_mode) -> str:
        name = getattr(view_mode, "name", view_mode)
        name = str(name).upper()
        if name in {"VIEWMODE.AXIAL", "0"}:
            return "AXIAL"
        if name in {"VIEWMODE.SAGITTAL", "1"}:
            return "SAGITTAL"
        if name in {"VIEWMODE.CORONAL", "2"}:
            return "CORONAL"
        if name in {"AXIAL", "SAGITTAL", "CORONAL"}:
            return name
        raise GeometryValidationError(f"unsupported view mode: {view_mode}")

    @staticmethod
    def ijk_to_kji(ijk: Sequence[int | float]) -> tuple[int | float, int | float, int | float]:
        try:
            value_count = len(ijk)
        except TypeError as exc:
            raise GeometryValidationError("IJK must contain three values") from exc
        if value_count != 3:
            raise GeometryValidationError("IJK must contain three values")
        return ijk[2], ijk[1], ijk[0]

    @staticmethod
    def kji_to_ijk(kji: Sequence[int | float]) -> tuple[int | float, int | float, int | float]:
        try:
            value_count = len(kji)
        except TypeError as exc:
            raise GeometryValidationError("KJI must contain three values") from exc
        if value_count != 3:
            raise GeometryValidationError("KJI must contain three values")
        return kji[2], kji[1], kji[0]

    @staticmethod
    def ijk_to_numpy_kji(
        ijk: Sequence[int | float],
    ) -> tuple[int | float, int | float, int | float]:
        """Explicitly named alias for the NumPy ``[K, J, I]`` contract."""

        return CoordinateService.ijk_to_kji(ijk)

    @staticmethod
    def numpy_kji_to_ijk(
        kji: Sequence[int | float],
    ) -> tuple[int | float, int | float, int | float]:
        """Explicitly named inverse of :meth:`ijk_to_numpy_kji`."""

        return CoordinateService.kji_to_ijk(kji)

    def slice_to_ijk(
        self,
        view_mode,
        image_u: int | float,
        image_v: int | float,
        layer: int,
    ) -> tuple[int, int, int]:
        view_name = self._view_name(view_mode)
        axes = self._VIEW_AXES[view_name]
        values = {axes[0]: image_u, axes[1]: image_v, axes[2]: layer}
        try:
            ijk = tuple(int(round(values[axis])) for axis in "IJK")
        except (TypeError, ValueError, OverflowError) as exc:
            raise GeometryValidationError("slice coordinates must be numeric") from exc
        return self.geometry.validate_ijk(ijk)

    def ijk_to_slice(
        self,
        view_mode,
        ijk: Sequence[int],
    ) -> tuple[int, int, int]:
        normalized = self.geometry.validate_ijk(ijk)
        view_name = self._view_name(view_mode)
        axes = self._VIEW_AXES[view_name]
        values = dict(zip("IJK", normalized))
        return int(values[axes[0]]), int(values[axes[1]]), int(values[axes[2]])

    def bbox_projection(
        self,
        view_mode,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
        layer: int,
    ) -> dict:
        """将 half-open IJK box 投影成当前位面的 UV 矩形。"""

        min_values_tuple, max_values_tuple = self.validate_bbox(
            min_ijk, max_ijk_exclusive
        )
        min_values = dict(zip("IJK", min_values_tuple))
        max_values = dict(zip("IJK", max_values_tuple))
        view_name = self._view_name(view_mode)
        u_axis, v_axis, normal_axis = self._VIEW_AXES[view_name]
        normal_value = int(layer)
        visible = min_values[normal_axis] <= normal_value < max_values[normal_axis]
        return {
            "view": view_name,
            "visible": visible,
            "u_axis": u_axis,
            "v_axis": v_axis,
            "normal_axis": normal_axis,
            "u0": int(min_values[u_axis]),
            "v0": int(min_values[v_axis]),
            "u1": int(max_values[u_axis]),
            "v1": int(max_values[v_axis]),
        }

    def validate_bbox(
        self,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
    ) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        try:
            min_count = len(min_ijk)
            max_count = len(max_ijk_exclusive)
        except TypeError as exc:
            raise GeometryValidationError(
                "bbox IJK boundaries must contain three values"
            ) from exc
        if min_count != 3 or max_count != 3:
            raise GeometryValidationError("bbox IJK boundaries must contain three values")
        min_values = self.geometry.validate_ijk(min_ijk)
        max_values = self.geometry.validate_ijk(max_ijk_exclusive, allow_max=True)
        for axis, lower, upper, size in zip("IJK", min_values, max_values, self.geometry.size_ijk):
            if not 0 <= lower < upper <= size:
                raise GeometryValidationError(
                    f"invalid bbox on {axis}: {lower} <= {upper} is required within [0, {size}]"
                )
        return min_values, max_values

    def normalize_bbox(
        self,
        start_ijk: Sequence[int],
        end_ijk: Sequence[int],
    ) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """Normalize two inclusive IJK points to a valid half-open bbox."""

        try:
            if len(start_ijk) != 3 or len(end_ijk) != 3:
                raise GeometryValidationError("bbox points must contain three values")
        except TypeError as exc:
            raise GeometryValidationError("bbox points must contain three values") from exc
        values: list[tuple[int, int]] = []
        for start, end in zip(start_ijk, end_ijk):
            if (
                isinstance(start, bool)
                or isinstance(end, bool)
                or not isinstance(start, Integral)
                or not isinstance(end, Integral)
            ):
                raise GeometryValidationError("bbox points must be integers")
            values.append((min(int(start), int(end)), max(int(start), int(end)) + 1))
        minimum = tuple(item[0] for item in values)
        maximum_exclusive = tuple(item[1] for item in values)
        return self.validate_bbox(minimum, maximum_exclusive)

    def bbox_dimensions(self, min_ijk: Sequence[int], max_ijk_exclusive: Sequence[int]) -> tuple[int, int, int]:
        min_values, max_values = self.validate_bbox(min_ijk, max_ijk_exclusive)
        return tuple(upper - lower for lower, upper in zip(min_values, max_values))

    def bbox_ijk_to_kji_slices(
        self,
        min_ijk: Sequence[int],
        max_ijk_exclusive: Sequence[int],
    ) -> tuple[slice, slice, slice]:
        """Return NumPy slices for an IJK half-open box.

        The returned order is ``(K, J, I)`` and can be applied directly to a
        ``GetArrayFromImage`` result.  Keeping this conversion here avoids
        scattered, easy-to-miss ``x/z`` swaps in UI and exporter code.
        """

        min_values, max_values = self.validate_bbox(min_ijk, max_ijk_exclusive)
        imin, jmin, kmin = min_values
        imax, jmax, kmax = max_values
        return slice(kmin, kmax), slice(jmin, jmax), slice(imin, imax)

    def orientation_labels(self, view_mode) -> tuple[str, str, str, str]:
        """Return left/right/top/bottom LPS labels for the rendered view.

        The viewer renders I/J/K slices with the historical PCST flips.  This
        method keeps the direction-cosine interpretation in the coordinate
        service instead of duplicating it in a widget.
        """

        view_name = self._view_name(view_mode)
        axes = {
            "AXIAL": ("I", "J", False),
            "SAGITTAL": ("J", "K", True),
            "CORONAL": ("I", "K", True),
        }[view_name]
        axis_to_component = {"I": 0, "J": 1, "K": 2}
        positive_codes = ("L", "P", "S")
        negative_codes = ("R", "A", "I")

        def positive_code(axis: str) -> str:
            vector = self.geometry.direction_matrix[:, axis_to_component[axis]]
            component = int(np.argmax(np.abs(vector)))
            return (
                positive_codes[component]
                if vector[component] >= 0
                else negative_codes[component]
            )

        opposites = {"L": "R", "R": "L", "P": "A", "A": "P", "S": "I", "I": "S"}
        horizontal_axis, vertical_axis, vertical_positive_up = axes
        horizontal_right = positive_code(horizontal_axis)
        horizontal_left = opposites[horizontal_right]
        vertical_positive = positive_code(vertical_axis)
        if vertical_positive_up:
            vertical_top, vertical_bottom = vertical_positive, opposites[vertical_positive]
        else:
            vertical_top, vertical_bottom = opposites[vertical_positive], vertical_positive
        return horizontal_left, horizontal_right, vertical_top, vertical_bottom
