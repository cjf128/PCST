"""Canonical medical-3d-box export.

Model-specific formats should be added beside this module; they must consume
the IJK source of truth and derive any physical coordinates through
``VolumeGeometry`` rather than storing a second bbox representation.
"""

from __future__ import annotations

from pathlib import Path

from pcst.core.annotations import AnnotationDocument


def export_canonical_json(document: AnnotationDocument, path: str | Path) -> Path:
    """Validate and atomically write a canonical ``*.boxes.json`` file."""

    return document.save_atomic(path)


__all__ = ["export_canonical_json"]
