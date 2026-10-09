"""Dataset/annotation integrity checks with user-readable diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import SimpleITK as sitk

from pcst.core.annotations import AnnotationDocument, AnnotationValidationError
from pcst.core.dataset import DatasetManifest
from pcst.core.geometry import GeometryValidationError, VolumeGeometry


@dataclass(slots=True)
class ValidationReport:
    """Validation result suitable for both UI and command-line callers."""

    issues: list[str] = field(default_factory=list)
    overlap_pairs: int = 0
    case_count: int = 0
    annotation_count: int = 0

    @property
    def valid(self) -> bool:
        return not self.issues


def validate_annotation_document(
    document: AnnotationDocument,
    *,
    image_path: str | Path | None = None,
    check_image_geometry: bool = False,
    orient_lps: bool = False,
) -> ValidationReport:
    """Check domain invariants and optionally compare against the image file.

    Overlap is counted for statistics but never added to ``issues`` because
    overlapping, containing, and identical boxes are all legal annotation
    states.
    """

    report = ValidationReport()
    try:
        document.validate()
    except (AnnotationValidationError, GeometryValidationError, ValueError) as exc:
        report.issues.append(str(exc))

    annotations = list(getattr(document, "annotations", ()))
    for index, first in enumerate(annotations):
        for second in annotations[index + 1 :]:
            try:
                if first.geometry.overlaps(second.geometry):
                    report.overlap_pairs += 1
            except AttributeError:
                continue

    if image_path is not None:
        path = Path(image_path)
        if not path.is_file():
            report.issues.append(f"图像文件不存在：{path}")
        elif check_image_geometry:
            try:
                image = sitk.ReadImage(str(path))
                if image.GetDimension() != 3:
                    report.issues.append(
                        f"图像必须是 3D：{path}（dimension={image.GetDimension()}）"
                    )
                else:
                    if orient_lps:
                        image = sitk.DICOMOrient(image, "LPS")
                    actual = VolumeGeometry.from_sitk(image)
                    if not actual.almost_equal(document.image_geometry):
                        report.issues.append(
                            "annotation 文件中的 image geometry 与实际图像不匹配。"
                        )
            except Exception as exc:  # SimpleITK exceptions vary by backend.
                report.issues.append(f"无法读取图像 geometry：{exc}")
    return report


def validate_dataset_directory(
    dataset_dir: str | Path,
    *,
    check_image_geometry: bool = False,
    orient_lps: bool = True,
) -> ValidationReport:
    """Validate a ``dataset.json`` plus all ``annotations/*.boxes.json`` files.

    Case IDs and annotation IDs are checked globally.  A missing manifest is
    reported, but the per-case files are still scanned so the user receives a
    complete diagnostic in one pass.
    """

    root = Path(dataset_dir)
    report = ValidationReport()
    manifest_path = root / "dataset.json"
    manifest: DatasetManifest | None = None
    if not manifest_path.is_file():
        report.issues.append(f"dataset.json 不存在：{manifest_path}")
    else:
        try:
            manifest = DatasetManifest.load(manifest_path)
        except Exception as exc:
            report.issues.append(f"dataset.json 无效：{exc}")

    annotation_dir = root / "annotations"
    if not annotation_dir.is_dir():
        report.issues.append(f"annotations 目录不存在：{annotation_dir}")
        return report

    case_ids: dict[str, Path] = {}
    annotation_ids: dict[str, Path] = {}
    manifest_class_ids = (
        {int(item["id"]) for item in manifest.classes} if manifest is not None else None
    )
    for path in sorted(annotation_dir.glob("*.boxes.json")):
        try:
            document = AnnotationDocument.load(path)
        except Exception as exc:
            report.issues.append(f"{path.name} 无效：{exc}")
            continue
        report.case_count += 1
        report.annotation_count += len(document.annotations)
        previous_case = case_ids.get(document.case_id)
        if previous_case is not None:
            report.issues.append(
                f"case_id 重复：{document.case_id!r}（{previous_case.name} 与 {path.name}）"
            )
        else:
            case_ids[document.case_id] = path
        for annotation in document.annotations:
            previous = annotation_ids.get(annotation.id)
            if previous is not None:
                report.issues.append(
                    f"annotation id 重复：{annotation.id!r}（{previous.name} 与 {path.name}）"
                )
            else:
                annotation_ids[annotation.id] = path
            if (
                manifest_class_ids is not None
                and annotation.class_id not in manifest_class_ids
            ):
                report.issues.append(
                    f"{path.name} 的 annotation {annotation.id} 引用了未定义 class_id "
                    f"{annotation.class_id}"
                )
        image_path = Path(document.image_file)
        if not image_path.is_absolute():
            image_path = path.parent / image_path
        child_report = validate_annotation_document(
            document,
            image_path=image_path,
            check_image_geometry=check_image_geometry,
            orient_lps=orient_lps,
        )
        report.issues.extend(f"{path.name}: {issue}" for issue in child_report.issues)
        report.overlap_pairs += child_report.overlap_pairs
    return report


__all__ = [
    "ValidationReport",
    "validate_annotation_document",
    "validate_dataset_directory",
]
