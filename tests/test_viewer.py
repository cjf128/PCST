import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from pcst.widgets.ImageViewer import ImageViewer


class ViewerStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_normalized_pan_zoom_state_can_be_shared(self):
        first = ImageViewer(None, None)
        second = ImageViewer(None, None)
        first.resize(220, 180)
        second.resize(220, 180)
        pixmap = QPixmap(100, 80)
        first.load_image(pixmap, 1)
        second.load_image(pixmap, 1)
        first.fitInView(first.pixmap_item)
        second.fitInView(second.pixmap_item)
        first.remember_fit_transform()
        second.remember_fit_transform()
        first.scale(1.75, 1.75)
        state = first.view_state()
        self.assertIsNotNone(state)
        second.apply_view_state(state)
        self.assertAlmostEqual(second.view_state()["zoom"], 1.75, places=3)


if __name__ == "__main__":
    unittest.main()
