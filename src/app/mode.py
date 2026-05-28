from enum import Enum


class VIEWERMode(Enum):
    NORMAL = 0
    AIM = 1
    MOVE = 2
    WIN = 3
    PAINT = 4
    SAM = 5
    ERASER = 6
    ZOOM = 7


class LOADMode(Enum):
    UNLOAD = 0
    LOADED = 1
    RELOAD = 2
    CHANGE = 3


class VIEWMode(Enum):
    AXIAL = 0
    SAGITTAL = 1
    CORONAL = 2
    VIEW_3D = 3


class SAMMode(Enum):
    BOX = 0
    ADD = 1
