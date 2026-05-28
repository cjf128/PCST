import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QWidget

from ui.ImageDock_ui import Ui_Form


class ImageDocker(QWidget, Ui_Form):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setupUi(self)
        self.init_connectAction()

    def init_connectAction(self):
        """初始化信号与槽连接"""
        self.sldAlphaCt.valueChanged.connect(
            lambda v: self.boxAlphaCt.setValue(v / 100)
        )
        self.boxAlphaCt.valueChanged.connect(
            lambda v: self.sldAlphaCt.setValue(int(v * 100))
        )
        self.sldAlphaPet.valueChanged.connect(
            lambda v: self.boxAlphaPet.setValue(v / 100)
        )
        self.boxAlphaPet.valueChanged.connect(
            lambda v: self.sldAlphaPet.setValue(int(v * 100))
        )
        self.boxAlphaCt.valueChanged.connect(lambda: self.set_alpha("CT"))
        self.boxAlphaPet.valueChanged.connect(lambda: self.set_alpha("PET"))

        self.sldPET_ww.valueChanged.connect(lambda v: self.boxPET_ww.setValue(v / 100))
        self.boxPET_ww.valueChanged.connect(
            lambda v: self.sldPET_ww.setValue(int(v * 100))
        )

        self.boxCT_ww.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("ct_ww", v)
        )
        self.boxCT_wl.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("ct_wl", v)
        )
        self.boxPET_ww.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("pet_ww", v)
        )
        self.boxAlphaCt.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("ct_alpha", v)
        )
        self.boxAlphaPet.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("pet_alpha", v)
        )

        self.btn1.clicked.connect(lambda: self.setwindow(400, 40))
        self.btn2.clicked.connect(lambda: self.setwindow(1500, -600))
        self.btn3.clicked.connect(lambda: self.setwindow(2000, 500))

    def setwindow(self, ww, wl):
        self.boxCT_ww.setValue(ww)
        self.boxCT_wl.setValue(wl)

    def set_alpha(self, state):
        if state == "CT":
            self.ct_alpha = self.boxAlphaCt.value()
            self.boxAlphaPet.setValue(1 - self.ct_alpha)
            self.pet_alpha = 1 - self.ct_alpha
        elif state == "PET":
            self.pet_alpha = self.boxAlphaPet.value()
            self.boxAlphaCt.setValue(1 - self.pet_alpha)
            self.ct_alpha = 1 - self.pet_alpha
        self.main_window.update_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageDocker(None, None)
    window.show()
    sys.exit(app.exec())
