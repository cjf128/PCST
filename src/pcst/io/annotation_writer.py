"""Atomic writer for canonical ``*.boxes.json`` documents."""

from __future__ import annotations

from pathlib import Path

from pcst.core.annotations import AnnotationDocument, AnnotationValidationError


class AnnotationWriteError(ValueError):
    """A canonical annotation document could not be validated or written."""


def write_annotations(document: AnnotationDocument, path: str | Path) -> Path:
    try:
        return document.save_atomic(path)
    except (AnnotationValidationError, OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, AnnotationWriteError):
            raise
        raise AnnotationWriteError(f"cannot write annotation file {path}: {exc}") from exc


__all__ = ["AnnotationWriteError", "write_annotations"]
