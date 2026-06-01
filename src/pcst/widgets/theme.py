from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeManager:
    @staticmethod
    def get_dark_palette() -> QPalette:
        palette = QPalette()

        dark_bg = QColor(35, 38, 42)
        darker_bg = QColor(25, 27, 30)
        border_gray = QColor(50, 53, 58)

        text_primary = QColor(220, 223, 228)
        text_secondary = QColor(160, 165, 175)

        accent_blue = QColor(61, 142, 201)
        accent_hover = QColor(71, 162, 221)

        palette.setColor(QPalette.ColorRole.Window, dark_bg)
        palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        palette.setColor(QPalette.ColorRole.Base, darker_bg)
        palette.setColor(QPalette.ColorRole.AlternateBase, border_gray)
        palette.setColor(QPalette.ColorRole.ToolTipBase, darker_bg)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
        palette.setColor(QPalette.ColorRole.Text, text_primary)
        palette.setColor(QPalette.ColorRole.Button, dark_bg)
        palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Highlight, accent_blue)
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, accent_blue)
        palette.setColor(QPalette.ColorRole.LinkVisited, accent_hover)

        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Highlight,
            QColor(45, 50, 55),
        )

        return palette

    @staticmethod
    def get_light_palette() -> QPalette:
        palette = QPalette()

        light_bg = QColor(250, 250, 248)
        mid_bg = QColor(242, 241, 238)

        text_primary = QColor(35, 38, 42)
        text_secondary = QColor(120, 125, 135)

        accent_blue = QColor(41, 128, 185)
        accent_hover = QColor(52, 152, 219)

        palette.setColor(QPalette.ColorRole.Window, light_bg)
        palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.AlternateBase, mid_bg)
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
        palette.setColor(QPalette.ColorRole.Text, text_primary)
        palette.setColor(QPalette.ColorRole.Button, mid_bg)
        palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Highlight, accent_blue)
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, accent_blue)
        palette.setColor(QPalette.ColorRole.LinkVisited, accent_hover)

        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            text_secondary,
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Highlight,
            QColor(200, 205, 210),
        )

        return palette

    @classmethod
    def set_theme(cls, theme: str = "dark") -> None:
        app = QApplication.instance()
        if not app:
            return

        assert isinstance(app, QApplication)

        app.setStyle("Fusion")

        if theme == "dark":
            app.setPalette(cls.get_dark_palette())
        else:
            app.setPalette(cls.get_light_palette())
