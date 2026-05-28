from __future__ import annotations

from copy import deepcopy

APP_NAME = "PCViewer"
APP_AUTHOR = "Jinfr"
APP_VERSION = "0.3.1"
APP_LICENSE = "Apache License 2.0"
PROJECT_HOMEPAGE_URL = "https://cjf128.github.io/PCViewer/"
PROJECT_REPOSITORY_URL = "https://github.com/cjf128/PCViewer"
PROJECT_REPOSITORY_LABEL = "cjf128/PCViewer"
DISCLAIMER_TEXT = (
    "本软件仅用于科研与教学目的，不作为临床诊断或治疗决策的直接依据。"
)

DEFAULT_LABELS = {
    "1": {"name": "Label 1", "color": "#0000FF"},
    "2": {"name": "Label 2", "color": "#00FF00"},
}

DEFAULT_SHORTCUTS = {
    "load_atn": "Ctrl+O",
    "aim_atn": "1",
    "paint_atn": "4",
    "add_atn": "Ctrl+A",
    "move_atn": "2",
    "eraser_atn": "5",
    "save_atn": "Ctrl+S",
    "win_atn": "3",
    "sam_atn": "6",
}


def normalize_label_config(label_config: dict | None) -> dict:
    if not label_config:
        return deepcopy(DEFAULT_LABELS)

    sorted_labels = sorted(label_config.items(), key=lambda item: int(item[0]))
    return {
        str(index): deepcopy(label_info)
        for index, (_, label_info) in enumerate(sorted_labels, 1)
    }
