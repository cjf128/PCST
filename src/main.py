# Copyright (c) 2026 PCViewer Jinfr
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.app import App
from path import ICONS_PATH
from scripts.logger import log_info, setup_logger


def main() -> int:
    setup_logger()
    log_info("应用程序启动")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICONS_PATH / "logo_2.ico")))
    app.setStyle("Fusion")

    application = App()
    application.run()
    log_info("应用程序初始化完成")

    result = app.exec()
    application.shutdown()
    log_info("应用程序退出")
    return result


if __name__ == "__main__":
    sys.exit(main())
