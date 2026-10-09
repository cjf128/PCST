import json
import tempfile
import unittest
from pathlib import Path

from pcst.core.annotations import (
    Annotation3D,
    AnnotationDocument,
    AnnotationValidationError,
    BoxGeometry,
    Relation,
)
from pcst.core.geometry import VolumeGeometry
from pcst.widgets.commands import AddBoxCommand, DeleteBoxCommand, UpdateBoxCommand


def _geometry():
    return VolumeGeometry(
        size_ijk=(64, 64, 32),
        spacing_mm=(0.5, 0.75, 2.0),
        origin_lps_mm=(-10.0, -20.0, -30.0),
        direction_ijk_to_lps=(1, 0, 0, 0, 1, 0, 0, 0, 1),
    )


class AnnotationTests(unittest.TestCase):
    def test_half_open_overlap_and_identical_geometry(self):
        first = Annotation3D.new(class_id=0, min_ijk=(1, 2, 3), max_ijk_exclusive=(10, 20, 8))
        second = Annotation3D.new(class_id=1, min_ijk=(1, 2, 3), max_ijk_exclusive=(10, 20, 8))
        self.assertEqual(first.geometry.dimensions_ijk, (9, 18, 5))
        self.assertEqual(first.geometry.physical_size_mm(_geometry()), (4.5, 13.5, 10.0))
        self.assertEqual(first.geometry.physical_volume_mm3(_geometry()), 607.5)
        self.assertTrue(first.geometry.overlaps(second.geometry))
        self.assertTrue(first.geometry.contains((1, 2, 3)))
        self.assertFalse(first.geometry.contains((10, 2, 3)))
        stats = first.statistics(_geometry())
        self.assertEqual(stats["voxel_size"], [9, 18, 5])
        self.assertEqual(stats["voxel_count"], 810)
        document = AnnotationDocument(
            case_id="case001",
            image_file="case001.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}, {"id": 1, "name": "B"}],
            annotations=[first, second],
        )
        self.assertEqual(len(document.annotations), 2)

    def test_invalid_zero_volume_and_reverse_bounds(self):
        with self.assertRaises(AnnotationValidationError):
            AnnotationDocument(
                case_id="case",
                image_file="image.nii.gz",
                image_geometry=_geometry(),
                classes=[{"id": 0, "name": "A"}],
                annotations=[
                    Annotation3D(
                        id="ann_bad",
                        lesion_id="lesion_bad",
                        class_id=0,
                        geometry=BoxGeometry((2, 2, 2), (2, 5, 5)),
                    )
                ],
            )

        normalized = BoxGeometry.from_inclusive_points((4, 8, 10), (1, 2, 3))
        self.assertEqual(normalized.min_ijk, (1, 2, 3))
        self.assertEqual(normalized.max_ijk_exclusive, (5, 9, 11))

    def test_relations_and_multiple_boxes_per_lesion(self):
        parent = Annotation3D.new(
            class_id=0,
            min_ijk=(1, 1, 1),
            max_ijk_exclusive=(20, 20, 10),
            lesion_id="lesion_parent",
        )
        child = Annotation3D.new(
            class_id=1,
            min_ijk=(2, 2, 2),
            max_ijk_exclusive=(5, 5, 5),
            lesion_id="lesion_child",
        )
        child.relations = [Relation("contained_in", "lesion_parent")]
        sibling = Annotation3D.new(
            class_id=1,
            min_ijk=(30, 30, 10),
            max_ijk_exclusive=(35, 35, 15),
            lesion_id="lesion_child",
        )
        document = AnnotationDocument(
            case_id="case",
            image_file="image.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}, {"id": 1, "name": "B"}],
            annotations=[parent, child, sibling],
        )
        self.assertEqual(len([a for a in document.annotations if a.lesion_id == "lesion_child"]), 2)
        with self.assertRaises(AnnotationValidationError):
            document.remove(parent.id)

    def test_annotation_class_must_be_declared(self):
        annotation = Annotation3D.new(
            class_id=7,
            min_ijk=(1, 1, 1),
            max_ijk_exclusive=(3, 3, 3),
        )
        with self.assertRaises(AnnotationValidationError):
            AnnotationDocument(
                case_id="case",
                image_file="image.nii.gz",
                image_geometry=_geometry(),
                classes=[],
                annotations=[annotation],
            )

    def test_atomic_roundtrip(self):
        annotation = Annotation3D.new(class_id=0, min_ijk=(1, 2, 3), max_ijk_exclusive=(4, 8, 10))
        document = AnnotationDocument(
            case_id="case",
            image_file="image.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}],
            annotations=[annotation],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.boxes.json"
            document.save_atomic(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["coordinate_convention"]["voxel_axes"], "IJK")
            loaded = AnnotationDocument.load(path)
            self.assertEqual(loaded.annotations[0].geometry, annotation.geometry)
            self.assertEqual(loaded.image_geometry, document.image_geometry)

    def test_required_schema_fields_are_checked(self):
        annotation = Annotation3D.new(
            class_id=0,
            min_ijk=(1, 2, 3),
            max_ijk_exclusive=(4, 8, 10),
        )
        payload = AnnotationDocument(
            case_id="case",
            image_file="image.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}],
            annotations=[annotation],
        ).to_dict()
        del payload["coordinate_convention"]
        with self.assertRaises(AnnotationValidationError):
            AnnotationDocument.from_dict(payload)

    def test_schema_rejects_unknown_fields_and_non_json_attributes(self):
        annotation = Annotation3D.new(
            class_id=0,
            min_ijk=(1, 2, 3),
            max_ijk_exclusive=(4, 8, 10),
        )
        payload = AnnotationDocument(
            case_id="case",
            image_file="image.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}],
            annotations=[annotation],
        ).to_dict()
        payload["unexpected"] = True
        with self.assertRaises(AnnotationValidationError) as context:
            AnnotationDocument.from_dict(payload)
        self.assertIn("unexpected", str(context.exception))

        with self.assertRaises(AnnotationValidationError):
            Annotation3D(
                id="ann_bad",
                lesion_id="lesion_bad",
                class_id=0,
                geometry=BoxGeometry((1, 1, 1), (2, 2, 2)),
                attributes={"bad": object()},
            )

    def test_undo_commands_keep_overlapping_annotations_independent(self):
        first = Annotation3D.new(class_id=0, min_ijk=(1, 1, 1), max_ijk_exclusive=(4, 4, 4))
        second = Annotation3D.new(class_id=1, min_ijk=(1, 1, 1), max_ijk_exclusive=(4, 4, 4))
        document = AnnotationDocument(
            case_id="case",
            image_file="image.nii.gz",
            image_geometry=_geometry(),
            classes=[{"id": 0, "name": "A"}, {"id": 1, "name": "B"}],
            annotations=[first],
        )
        add = AddBoxCommand(document, second)
        add.redo()
        self.assertEqual(len(document.annotations), 2)
        add.undo()
        self.assertEqual([item.id for item in document.annotations], [first.id])
        changed = first.copy()
        changed.geometry = BoxGeometry((2, 2, 2), (5, 5, 5))
        update = UpdateBoxCommand(document, first, changed)
        update.redo()
        self.assertEqual(document.get(first.id).geometry, changed.geometry)
        update.undo()
        self.assertEqual(document.get(first.id).geometry, first.geometry)
        delete = DeleteBoxCommand(document, first)
        delete.redo()
        self.assertEqual(document.annotations, [])
        delete.undo()
        self.assertEqual(document.annotations[0].id, first.id)


if __name__ == "__main__":
    unittest.main()
