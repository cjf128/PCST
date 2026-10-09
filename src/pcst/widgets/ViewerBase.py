from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from pcst.app.mode import VIEWMode
from pcst.ui.ViewerBase_ui import Ui_Form
from pcst.widgets.ImageViewer import ImageViewer


class ViewerBase(QWidget, Ui_Form):
    """一个二维方位视图及其层号、滚动条和截图控件。"""

    layer_changed = Signal(object, int)
    screenshot_requested = Signal(object)

    def __init__(
        self,
        parent: QWidget,
        main_window,
        view_mode: VIEWMode,
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.main_window = main_window
        self.view_mode = view_mode

        self.viewer = ImageViewer(self.image_frame, main_window)
        self.viewer.view_mode = view_mode

        image_layout = QVBoxLayout(self.image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        image_layout.addWidget(self.viewer)

        # ViewerBase.ui 已负责 boxLayer 与 sldLayer 的双向同步。
        self.boxLayer.valueChanged.connect(self._on_layer_changed)
        self.btnCa.clicked.connect(lambda: self.screenshot_requested.emit(self))

    def _on_layer_changed(self, value: int) -> None:
        self.layer_changed.emit(self.view_mode, value)

    def set_layer_range(self, maximum: int) -> None:
        maximum = max(0, int(maximum))
        old_box_state = self.boxLayer.blockSignals(True)
        old_slider_state = self.sldLayer.blockSignals(True)
        try:
            self.boxLayer.setRange(0, maximum)
            self.sldLayer.setRange(0, maximum)
        finally:
            self.boxLayer.blockSignals(old_box_state)
            self.sldLayer.blockSignals(old_slider_state)

    def set_layer(self, value: int) -> None:
        value = max(self.boxLayer.minimum(), min(int(value), self.boxLayer.maximum()))
        old_box_state = self.boxLayer.blockSignals(True)
        old_slider_state = self.sldLayer.blockSignals(True)
        try:
            self.boxLayer.setValue(value)
            self.sldLayer.setValue(value)
        finally:
            self.boxLayer.blockSignals(old_box_state)
            self.sldLayer.blockSignals(old_slider_state)
