from __future__ import annotations

from copy import deepcopy

APP_NAME = "PCST"
APP_AUTHOR = "Jinfr"
APP_VERSION = "1.0.0"
APP_LICENSE = "Apache License 2.0"
PROJECT_HOMEPAGE_URL = "https://cjf128.github.io/PCST/"
PROJECT_REPOSITORY_URL = "https://github.com/cjf128/PCST"
PROJECT_REPOSITORY_LABEL = "cjf128/PCST"
DISCLAIMER_TEXT = (
    "本软件仅用于科研与教学目的，不作为临床诊断或治疗决策的直接依据。"
)

DEFAULT_LABELS = {
    "1": {"name": "Label 1", "color": "#0000FF"},
    "2": {"name": "Label 2", "color": "#00FF00"},
}

DEFAULT_SHORTCUTS = {
    "load_atn": "Ctrl+O",
    "btn_aim": "1",
    "btn_paint": "4",
    "add_atn": "Ctrl+A",
    "btn_move": "2",
    "btn_eraser": "5",
    "save_atn": "Ctrl+S",
    "btn_win": "3",
    "btn_sam": "6",
    "btn_box": "7",
}


def normalize_label_config(label_config: dict | None) -> dict:
    if not label_config:
        return deepcopy(DEFAULT_LABELS)

    sorted_labels = sorted(label_config.items(), key=lambda item: int(item[0]))
    return {
        str(index): deepcopy(label_info)
        for index, (_, label_info) in enumerate(sorted_labels, 1)
    }
