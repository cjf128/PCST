"""CoordinateService public compatibility module.

The implementation lives in :mod:`pcst.core.geometry`; this module keeps the
coordinate API discoverable under the architecture name used by the project
design without introducing a second conversion implementation.
"""

from pcst.core.geometry import CoordinateService, GeometryValidationError, VolumeGeometry

__all__ = ["CoordinateService", "GeometryValidationError", "VolumeGeometry"]

