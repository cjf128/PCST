import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class InfoDocker(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建表格
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["属性", "值"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tableWidget)

    def update_info(self, info):
        """更新信息"""
        # 清空表格
        self.tableWidget.setRowCount(0)

        # 添加信息
        for key, value in info.items():
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            # 属性列
            key_item = QTableWidgetItem(key)
            key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tableWidget.setItem(row, 0, key_item)

            # 值列
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tableWidget.setItem(row, 1, value_item)

        # 设置列宽模式，让两列都填满表格
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InfoDocker(None, None)
    window.show()
    sys.exit(app.exec())
