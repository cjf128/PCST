import json
import unittest
from pathlib import Path

from pcst.core.dataset import DatasetManifest
from pcst.core.annotations import AnnotationValidationError


class SchemaFilesTests(unittest.TestCase):
    def test_schema_files_are_valid_json_and_versioned(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("dataset.schema.json", "boxes.schema.json"):
            payload = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["properties"]["schema_version"]["const"], "1.0.0")
            self.assertEqual(payload["properties"]["coordinate_convention"]["properties"]["voxel_axes"]["const"], "IJK")

    def test_dataset_manifest_roundtrip_and_duplicate_class_rejection(self):
        manifest = DatasetManifest(classes=[{"id": 0, "name": "A"}])
        self.assertEqual(manifest.to_dict()["overlap_policy"], "allowed")
        self.assertEqual(
            DatasetManifest.from_dict(manifest.to_dict()).classes,
            [{"id": 0, "name": "A"}],
        )
        with self.assertRaises(AnnotationValidationError):
            DatasetManifest(classes=[{"id": 0, "name": "A"}, {"id": 0, "name": "B"}])


if __name__ == "__main__":
    unittest.main()
