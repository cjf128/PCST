import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QWidget

from app.configs import ConfigManager
from ui.FileDock_ui import Ui_Form


class FileDocker(QWidget, Ui_Form):
    """文件管理器窗口部件，用于显示和管理已导入的医学影像文件列表"""

    file_name = Signal(str)

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setupUi(self)
        self.config()

    def config(self) -> None:
        """初始化模型与信号"""
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["数据名称"])
        self.treeView.setModel(self.model)
        self.treeView.setRootIsDecorated(False)
        self.treeView.header().setStretchLastSection(True)
        self.treeView.doubleClicked.connect(self.on_item_double_clicked)
        self.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.on_context_menu)
        self.load_file_list()

    def load_file_list(self):
        """增量加载配置中的数据项到模型中"""
        if not self.main_window or not hasattr(self.main_window, "_config"):
            return
        data = self.main_window._config.data
        if not data:
            return

        existing_ids = set()
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item:
                existing_ids.add(str(item.data(Qt.ItemDataRole.UserRole)))

        new_ids = set(str(k) for k in data.keys())
        ids_to_add = new_ids - existing_ids
        ids_to_remove = existing_ids - new_ids

        for data_id in ids_to_remove:
            for row in range(self.model.rowCount()):
                item = self.model.item(row, 0)
                if item and str(item.data(Qt.ItemDataRole.UserRole)) == data_id:
                    self.model.removeRow(row)
                    break

        used_names = set(
            self.model.item(row, 0).text() for row in range(self.model.rowCount())
        )

        for data_id in sorted(
            ids_to_add, key=lambda x: int(x) if x.isdigit() else float("inf")
        ):
            info = data.get(data_id) or (
                data.get(int(data_id)) if data_id.isdigit() else None
            )
            if not info:
                continue

            raw_name = info.get("name")
            if not raw_name:
                pet_path = info.get("pet", "")
                raw_name = Path(pet_path).name if pet_path else f"数据_{data_id}"

            base_name = raw_name.split(".")[0]
            final_name = base_name
            counter = 1
            while final_name in used_names:
                final_name = f"{base_name}_{counter}"
                counter += 1
            used_names.add(final_name)

            self.main_window._config.data[data_id]["name"] = final_name
            config_manager = ConfigManager()
            config_manager.save(self.main_window._config)

            row = [QStandardItem(final_name)]
            row[0].setData(data_id, Qt.ItemDataRole.UserRole)
            self.model.appendRow(row)

        self.treeView.resizeColumnToContents(0)

    def on_item_double_clicked(self, index):
        """双击项后重载数据并发出名称信号"""
        item = self.model.itemFromIndex(index)
        data_id = item.data(Qt.ItemDataRole.UserRole)

        name = ""
        if data_id and self.main_window and hasattr(self.main_window, "_config"):
            if data_id in self.main_window._config.data:
                raw_name = self.main_window._config.data[data_id].get(
                    "name", item.text()
                )
                name = raw_name.split(".")[0]

        if data_id and self.main_window and hasattr(self.main_window, "reload_data"):
            self.main_window.reload_data(data_id)

        self.file_name.emit(name)

    def on_context_menu(self, position):
        index = self.treeView.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")
        rename_action.triggered.connect(lambda: self.rename_data(index=index))
        delete_action.triggered.connect(lambda: self.delete_data(index=index))
        menu.exec(self.treeView.mapToGlobal(position))

    def rename_data(self, index):
        item = self.model.itemFromIndex(index)
        data_id = item.data(Qt.ItemDataRole.UserRole)

        if data_id and self.main_window and hasattr(self.main_window, "_config"):
            new_name, ok = QInputDialog.getText(
                self, "重命名", "请输入新的名称:", text=item.text()
            )
            if ok and new_name:
                if data_id in self.main_window._config.data:
                    self.main_window._config.data[data_id]["name"] = new_name
                    config_manager = ConfigManager()
                    config_manager.save(self.main_window._config)
                    item.setText(new_name)

            self.file_name.emit(new_name)

    def delete_data(self, *, index=None, data_id=None):
        item = None
        if index:
            item = self.model.itemFromIndex(index)
            data_id = item.data(Qt.ItemDataRole.UserRole)
        elif data_id:
            data_id = data_id

        if data_id and self.main_window and hasattr(self.main_window, "_config"):
            current_id = getattr(self.main_window, "current_data_id", "")
            if current_id and str(current_id) == str(data_id):
                QMessageBox.warning(
                    self,
                    "无法删除",
                    "该数据正在使用中，无法删除",
                    QMessageBox.StandardButton.Ok,
                )
                return

            reply = QMessageBox.StandardButton.Yes
            if item:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    f"确定要删除数据 {item.text()} 吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

            if reply == QMessageBox.StandardButton.Yes:
                if data_id in self.main_window._config.data:
                    del self.main_window._config.data[data_id]

                    sorted_ids = sorted(
                        self.main_window._config.data.keys(),
                        key=lambda x: int(x) if str(x).isdigit() else float("inf"),
                    )
                    new_data = {}
                    for new_id, old_id in enumerate(sorted_ids, start=1):
                        new_data[str(new_id)] = self.main_window._config.data[old_id]
                    self.main_window._config.data = new_data

                    from app.configs import ConfigManager

                    config_manager = ConfigManager()
                    config_manager.save(self.main_window._config)

                    self.model.clear()
                    self.model.setHorizontalHeaderLabels(["数据名称"])

                    used_names = set()
                    for new_id, info in new_data.items():
                        raw_name = info.get("name")
                        if not raw_name:
                            pet_path = info.get("pet", "")
                            raw_name = (
                                Path(pet_path).name if pet_path else f"数据_{new_id}"
                            )

                        base_name = raw_name.split(".")[0]
                        final_name = base_name
                        counter = 1
                        while final_name in used_names:
                            final_name = f"{base_name}_{counter}"
                            counter += 1
                        used_names.add(final_name)

                        row = [QStandardItem(final_name)]
                        row[0].setData(new_id, Qt.ItemDataRole.UserRole)
                        self.model.appendRow(row)

                    self.treeView.resizeColumnToContents(0)

    def select_item_by_id(self, data_id):
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item:
                item_id = str(item.data(Qt.ItemDataRole.UserRole))
                if item_id == str(data_id):
                    index = self.model.indexFromItem(item)
                    selection_model = self.treeView.selectionModel()
                    selection_model.clearSelection()
                    selection_model.select(index, selection_model.SelectionFlag.Select)
                    selection_model.setCurrentIndex(
                        index, selection_model.SelectionFlag.NoUpdate
                    )
                    break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileDocker(None, None)
    window.show()
    sys.exit(app.exec())
