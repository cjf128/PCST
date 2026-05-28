import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox

from app.configs import ConfigManager
from ui.LoadDialog_ui import Ui_LoadDialog


class LoadDialog(QDialog, Ui_LoadDialog):
    FilesSelected = Signal(str, str, str, str)

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setupUi(self)
        self.config()

    def config(self) -> None:
        self.load_state: str = self.comboBox.currentText()
        self.setWindowTitle("导入文件")

    @Slot(str)
    def on_comboBox_currentTextChanged(self, text) -> None:
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.load_state = text

    @Slot(bool)
    def on_btnSearch_clicked(self, clicked) -> None:
        if self.load_state == "NIfTI":
            file_filter = "NIfTI Files (*.nii *.nii.gz)"
        else:
            file_filter = "DICOM Files (*.dcm *.IMA *.ima);;All Files (*)"

        file_path, _ = QFileDialog.getOpenFileName(self, "选择PET文件", "", file_filter)
        if file_path:
            self.lineEdit.setText(file_path)

    @Slot(bool)
    def on_btnSearch_2_clicked(self, clicked) -> None:
        if self.load_state == "NIfTI":
            file_filter = "NIfTI Files (*.nii *.nii.gz)"
        else:
            file_filter = "DICOM Files (*.dcm *.IMA *.ima);;All Files (*)"

        file_path, _ = QFileDialog.getOpenFileName(self, "选择CT文件", "", file_filter)
        if file_path:
            self.lineEdit_2.setText(file_path)

    @Slot(bool)
    def on_btnCancel_clicked(self, clicked) -> None:
        self.close()

    @Slot(bool)
    def on_btnLoad_clicked(self, clicked) -> None:
        pet_file = self.lineEdit.text()
        ct_file = self.lineEdit_2.text()

        if not pet_file or not ct_file:
            QMessageBox.warning(
                self, "提示", "请选择PET和CT文件", QMessageBox.StandardButton.Ok
            )
            return

        # 记录文件路径到配置中
        new_data_id = None
        if self.main_window:
            data_count = len(self.main_window._config.data)
            new_data_id = data_count + 1

            if self.load_state == "NIfTI":
                raw_name = Path(pet_file).name
                base_name = raw_name.split(".")[0] if "." in raw_name else raw_name
            else:
                raw_name = Path(pet_file).parent.name
                base_name = raw_name.split(".")[0] if "." in raw_name else raw_name

            self.main_window._config.data[str(new_data_id)] = {
                "pet": pet_file,
                "ct": ct_file,
                "type": self.load_state,
                "name": base_name,
            }

            config_manager = ConfigManager()
            config_manager.save(self.main_window._config)

            if hasattr(self.main_window, "file_Setting"):
                self.main_window.file_Setting.load_file_list()

        self.close()
        self.FilesSelected.emit(pet_file, ct_file, self.load_state, str(new_data_id))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = LoadDialog(None, None)
    ui.show()
    sys.exit(app.exec_())
