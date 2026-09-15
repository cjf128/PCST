import unittest

import numpy as np

from pcst.app.mode import VIEWMode
from pcst.core.geometry import CoordinateService, GeometryValidationError, VolumeGeometry
from pcst.core.image import LoadedVolume, MedicalImage


class GeometryTests(unittest.TestCase):
    def test_identity_ijk_lps_and_kji(self):
        geometry = VolumeGeometry(
            size_ijk=(10, 20, 30),
            spacing_mm=(1.0, 1.0, 1.0),
            origin_lps_mm=(0.0, 0.0, 0.0),
            direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        self.assertEqual(geometry.ijk_to_lps((2, 3, 4)), (2.0, 3.0, 4.0))
        service = CoordinateService(geometry)
        self.assertEqual(
            service.orientation_labels(VIEWMode.AXIAL), ("R", "L", "A", "P")
        )
        self.assertEqual(service.ijk_to_kji((2, 3, 4)), (4, 3, 2))
        self.assertEqual(service.kji_to_ijk((4, 3, 2)), (2, 3, 4))
        self.assertEqual(service.ijk_to_numpy_kji((2, 3, 4)), (4, 3, 2))
        self.assertEqual(service.numpy_kji_to_ijk((4, 3, 2)), (2, 3, 4))

    def test_spacing_origin_and_direction(self):
        geometry = VolumeGeometry(
            size_ijk=(10, 20, 30),
            spacing_mm=(0.5, 0.5, 3.0),
            origin_lps_mm=(-10.0, 20.0, 30.0),
            # 90 degree rotation in the I/J plane.
            direction_ijk_to_lps=(0, -1, 0, 1, 0, 0, 0, 0, 1),
        )
        self.assertEqual(geometry.ijk_to_lps((2, 4, 1)), (-12.0, 21.0, 33.0))
        self.assertTrue(
            np.allclose(geometry.lps_to_ijk((-12.0, 21.0, 33.0)), (2.0, 4.0, 1.0))
        )

        flipped = VolumeGeometry(
            size_ijk=(10, 10, 10),
            spacing_mm=(1, 1, 1),
            origin_lps_mm=(5, 6, 7),
            direction_ijk_to_lps=(-1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        self.assertEqual(flipped.ijk_to_lps((2, 3, 4)), (3.0, 9.0, 11.0))
        self.assertTrue(np.allclose(flipped.lps_to_ijk((3.0, 9.0, 11.0)), (2, 3, 4)))
        flipped_service = CoordinateService(flipped)
        self.assertEqual(
            flipped_service.orientation_labels(VIEWMode.AXIAL), ("L", "R", "A", "P")
        )
        rotated_service = CoordinateService(geometry)
        self.assertEqual(
            rotated_service.orientation_labels(VIEWMode.AXIAL), ("A", "P", "L", "R")
        )

        with self.assertRaises(GeometryValidationError):
            VolumeGeometry(
                size_ijk=(10, 10, 10),
                spacing_mm=(1, 1, 1),
                origin_lps_mm=(0, 0, 0),
                direction_ijk_to_lps=(2, 0, 0, 0, 1, 0, 0, 0, 1),
            )

    def test_view_projection_and_bbox_validation(self):
        geometry = VolumeGeometry(
            size_ijk=(100, 80, 60),
            spacing_mm=(1, 1, 1),
            origin_lps_mm=(0, 0, 0),
            direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        service = CoordinateService(geometry)
        projection = service.bbox_projection(
            VIEWMode.AXIAL, (10, 20, 5), (30, 40, 8), layer=6
        )
        self.assertTrue(projection["visible"])
        self.assertEqual((projection["u0"], projection["v0"]), (10, 20))
        self.assertEqual((projection["u1"], projection["v1"]), (30, 40))
        with self.assertRaises(GeometryValidationError):
            service.validate_bbox((10, 20, 5), (10, 40, 8))
        with self.assertRaises(GeometryValidationError):
            service.validate_bbox((0, 0, 0), (101, 1, 1))
        with self.assertRaises(GeometryValidationError):
            service.validate_bbox((1.5, 0, 0), (2, 1, 1))

        self.assertEqual(
            service.normalize_bbox((30, 40, 8), (10, 20, 5)),
            ((10, 20, 5), (31, 41, 9)),
        )

        slices = service.bbox_ijk_to_kji_slices((10, 20, 5), (30, 40, 8))
        volume = np.zeros((60, 80, 100), dtype=np.uint8)
        self.assertEqual(volume[slices].shape, (3, 20, 20))

    def test_bbox_corner_lps_uses_half_open_edges(self):
        geometry = VolumeGeometry(
            size_ijk=(10, 10, 10),
            spacing_mm=(2, 3, 4),
            origin_lps_mm=(10, 20, 30),
            direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        corners = geometry.bbox_corner_lps((1, 2, 3), (3, 5, 4))
        self.assertIn((11.0, 24.5, 40.0), corners)

    def test_loaded_volume_preserves_kji_contract(self):
        geometry = VolumeGeometry(
            size_ijk=(4, 5, 6),
            spacing_mm=(1, 1, 1),
            origin_lps_mm=(0, 0, 0),
            direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        volume = LoadedVolume(
            ct_data=np.zeros((6, 5, 4), dtype=np.float32),
            pet_data=np.zeros((6, 5, 4), dtype=np.float32),
            ct_geometry=geometry,
        )
        self.assertEqual(volume.ct_data.shape, (6, 5, 4))
        with self.assertRaises(ValueError):
            LoadedVolume(
                ct_data=np.zeros((4, 5, 6), dtype=np.float32),
                pet_data=np.zeros((4, 5, 6), dtype=np.float32),
                ct_geometry=geometry,
            )

        image = MedicalImage(np.zeros((6, 5, 4), dtype=np.float32), geometry)
        restored = MedicalImage.from_sitk(image.to_sitk())
        self.assertEqual(restored.shape_kji, (6, 5, 4))
        self.assertEqual(restored.geometry, geometry)


if __name__ == "__main__":
    unittest.main()
