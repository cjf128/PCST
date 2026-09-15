"""Reader for canonical ``*.boxes.json`` documents."""

from __future__ import annotations

from pathlib import Path

from pcst.core.annotations import AnnotationDocument, AnnotationValidationError


class AnnotationReadError(ValueError):
    """A canonical annotation file is unreadable or invalid."""


def read_annotations(path: str | Path) -> AnnotationDocument:
    try:
        return AnnotationDocument.load(path)
    except (AnnotationValidationError, OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, AnnotationReadError):
            raise
        raise AnnotationReadError(f"cannot read annotation file {path}: {exc}") from exc


__all__ = ["AnnotationReadError", "read_annotations"]
