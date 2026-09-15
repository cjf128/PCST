import tempfile
import unittest
from pathlib import Path

import numpy as np
import SimpleITK as sitk

from pcst.core.annotations import Annotation3D, AnnotationDocument, BoxGeometry
from pcst.core.geometry import VolumeGeometry
from pcst.core.migrations import MigrationError, migrate_boxes_payload
from pcst.core.validation import validate_annotation_document
from pcst.core.validation import validate_dataset_directory
from pcst.core.dataset import DatasetManifest
from pcst.io.nifti_reader import NiftiReadError, read_nifti


class IOTests(unittest.TestCase):
    def test_nifti_reader_keeps_geometry_and_kji(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.nii.gz"
            array_kji = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
            image = sitk.GetImageFromArray(array_kji)
            image.SetSpacing((0.5, 0.75, 2.0))
            image.SetOrigin((-10.0, 20.0, 30.0))
            image.SetDirection((0, -1, 0, 1, 0, 0, 0, 0, 1))
            sitk.WriteImage(image, str(path))

            loaded = read_nifti(path, orient_lps=False)
            self.assertEqual(loaded.shape_kji, (2, 3, 4))
            self.assertEqual(loaded.size_ijk, (4, 3, 2))
            self.assertEqual(loaded.geometry.spacing_mm, (0.5, 0.75, 2.0))
            self.assertEqual(loaded.geometry.origin_lps_mm, (-10.0, 20.0, 30.0))
            self.assertTrue(np.array_equal(loaded.data_kji, array_kji))

            oriented = read_nifti(path, orient_lps=True)
            # Reorientation may permute cardinal axes, but must preserve the
            # physical point represented by the original image corners.
            self.assertTrue(
                np.allclose(
                    loaded.geometry.ijk_to_lps((0, 0, 0)),
                    oriented.geometry.ijk_to_lps(
                        oriented.geometry.lps_to_ijk(
                            loaded.geometry.ijk_to_lps((0, 0, 0))
                        )
                    ),
                )
            )

    def test_nifti_reader_rejects_wrong_extension(self):
        with self.assertRaises(NiftiReadError):
            read_nifti("not-an-image.mha")

    def test_migration_does_not_silently_accept_unknown_version(self):
        with self.assertRaises(MigrationError):
            migrate_boxes_payload({"schema": "medical-3d-box", "schema_version": "0.9.0"})

    def test_validation_counts_overlap_without_failing(self):
        geometry = VolumeGeometry(
            size_ijk=(20, 20, 20),
            spacing_mm=(1, 1, 1),
            origin_lps_mm=(0, 0, 0),
            direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
        )
        first = Annotation3D.new(class_id=0, min_ijk=(1, 1, 1), max_ijk_exclusive=(5, 5, 5))
        second = Annotation3D.new(class_id=0, min_ijk=(2, 2, 2), max_ijk_exclusive=(6, 6, 6))
        document = AnnotationDocument(
            case_id="case",
            image_file="case.nii.gz",
            image_geometry=geometry,
            classes=[{"id": 0, "name": "lesion"}],
            annotations=[first, second],
        )
        report = validate_annotation_document(document)
        self.assertTrue(report.valid)
        self.assertEqual(report.overlap_pairs, 1)

    def test_dataset_validation_checks_global_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "annotations").mkdir()
            DatasetManifest(classes=[{"id": 0, "name": "lesion"}]).save_atomic(
                root / "dataset.json"
            )
            geometry = VolumeGeometry(
                size_ijk=(10, 10, 10),
                spacing_mm=(1, 1, 1),
                origin_lps_mm=(0, 0, 0),
                direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
            )
            annotation = Annotation3D(
                id="ann_same",
                lesion_id="lesion",
                class_id=0,
                geometry=BoxGeometry((1, 1, 1), (3, 3, 3)),
            )
            for name in ("a.boxes.json", "b.boxes.json"):
                AnnotationDocument(
                    case_id="duplicate-case",
                    image_file="missing.nii.gz",
                    image_geometry=geometry,
                    classes=[{"id": 0, "name": "lesion"}],
                    annotations=[annotation.copy()],
                ).save_atomic(root / "annotations" / name)
            report = validate_dataset_directory(root)
            self.assertFalse(report.valid)
            self.assertGreaterEqual(len(report.issues), 3)
            self.assertEqual(report.case_count, 2)
            self.assertEqual(report.annotation_count, 2)


if __name__ == "__main__":
    unittest.main()
