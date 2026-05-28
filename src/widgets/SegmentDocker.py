import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QColorDialog,
    QMessageBox,
    QRadioButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from app.configs import ConfigManager
from app.mode import SAMMode
from ui.SegmentDock_ui import Ui_Form


class SegmentDocker(QWidget, Ui_Form):
    # 定义一个信号，用于通知MainWindow更新当前color_label
    label_selected = Signal(int)

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setupUi(self)
        self.init_connectAction()
        self.init_labels()
        self.init_sam_mode_buttons()

    def init_sam_mode_buttons(self):
        """初始化SAM模式按钮"""
        # 创建互斥按钮组
        self.sam_button_group = QButtonGroup(self)
        self.sam_button_group.setExclusive(True)

        # 连接按钮点击事件
        self.pushButton_3.clicked.connect(self.on_box_button_clicked)
        self.pushButton_4.clicked.connect(self.on_add_button_clicked)

        # 添加按钮到组
        self.sam_button_group.addButton(self.pushButton_3)
        self.sam_button_group.addButton(self.pushButton_4)

        # 默认选中BOX模式
        self.pushButton_3.setChecked(True)
        self.current_mode = SAMMode.BOX

    def on_box_button_clicked(self):
        """Box模式"""
        self.current_mode = SAMMode.BOX

    def on_add_button_clicked(self):
        """Add模式"""
        self.current_mode = SAMMode.ADD

    def init_connectAction(self):
        """初始化信号与槽连接"""
        self.sldAlphaSeg.valueChanged.connect(
            lambda v: self.boxAlphaSeg.setValue(v / 100)
        )
        self.boxAlphaSeg.valueChanged.connect(
            lambda v: self.sldAlphaSeg.setValue(int(v * 100))
        )
        self.boxAlphaSeg.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("seg_alpha", v)
        )
        self.boxPaint.valueChanged.connect(
            lambda v: self.main_window.update_property_and_refresh("radius", v)
        )
        self.pushButton.clicked.connect(self.add_label)
        self.pushButton_2.clicked.connect(self.delete_label)
        self.tableWidget.cellChanged.connect(self.update_label)
        self.tableWidget.cellDoubleClicked.connect(self.change_color)
        # 当选择行变化时，发送信号
        self.tableWidget.itemSelectionChanged.connect(self.on_label_selected)
        # 当表格被点击时，处理点击事件
        self.tableWidget.cellClicked.connect(self.on_cell_clicked)

    def init_labels(self):
        """初始化标签表格"""
        # 从MainWindow的配置中加载标签
        if not hasattr(self.main_window, "_config"):
            # 如果没有配置或标签，初始化一个默认标签
            labels = {"1": {"name": "Default", "color": "#FF0000"}}
        else:
            labels = self.main_window._config.label

        # 清空表格
        self.tableWidget.setRowCount(0)

        # 确保表格有3列
        if self.tableWidget.columnCount() < 3:
            self.tableWidget.setColumnCount(3)

        # 设置列标题
        self.tableWidget.setHorizontalHeaderLabels(["", "标签名", "颜色"])

        # 按标签ID排序
        sorted_labels = sorted(labels.items(), key=lambda x: int(x[0]))

        # 清理旧的按钮组
        if hasattr(self, "radio_group"):
            # 移除所有按钮
            for button in self.radio_group.buttons():
                self.radio_group.removeButton(button)

        # 创建新的按钮组
        self.radio_group = QButtonGroup()
        self.radio_group.setExclusive(True)

        # 填充表格
        for idx, (label_id, label_info) in enumerate(sorted_labels):
            self.tableWidget.insertRow(idx)

            radio_widget = QWidget()
            radio_layout = QVBoxLayout(radio_widget)
            radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            radio_button = QRadioButton()
            radio_button.clicked.connect(
                lambda checked, lid=int(label_id): self.on_select_button_clicked(lid)
            )
            radio_layout.addWidget(radio_button)
            radio_widget.setLayout(radio_layout)
            self.tableWidget.setCellWidget(idx, 0, radio_widget)

            # 将radio button添加到按钮组
            self.radio_group.addButton(radio_button)

            # 名称列
            name_item = QTableWidgetItem(label_info["name"])
            self.tableWidget.setItem(idx, 1, name_item)

            # 颜色列
            color_item = QTableWidgetItem()
            color = QColor(label_info["color"])
            color_item.setBackground(color)
            # 不显示颜色文本
            color_item.setText("")
            self.tableWidget.setItem(idx, 2, color_item)

        # 默认选中第一个按钮
        if self.radio_group.buttons():
            self.radio_group.buttons()[0].setChecked(True)
            # 发送第一个标签的选择信号
            if sorted_labels:
                first_label_id = int(sorted_labels[0][0])
                self.on_select_button_clicked(first_label_id)

        # 禁用整行选择
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # 设置列宽，固定列宽
        self.tableWidget.setColumnWidth(0, 35)  # Select列固定宽度35
        self.tableWidget.setColumnWidth(1, 100)  # Name列固定宽度100
        self.tableWidget.setColumnWidth(2, 100)  # Color列固定宽度100

    def add_label(self):
        """添加新标签"""
        # 打开颜色选择对话框
        color_dialog = QColorDialog()
        color_dialog.setWindowTitle("选择标签颜色")

        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            new_color = color_dialog.currentColor().name()

            # 从MainWindow的配置中获取标签
            labels = self.main_window._config.label

            # 生成新标签ID
            label_ids = [int(id) for id in labels.keys()]
            new_id = str(max(label_ids) + 1) if label_ids else "1"

            # 添加新标签
            labels[new_id] = {"name": f"Label {new_id}", "color": new_color}

            # 更新表格
            self.init_labels()

            # 选中刚添加的新标签（最后一个）
            if self.radio_group.buttons():
                last_button = self.radio_group.buttons()[-1]
                last_button.setChecked(True)
                self.on_select_button_clicked(int(new_id))

    def delete_label(self):
        """删除选中标签"""
        # 从MainWindow的配置中获取标签
        labels = self.main_window._config.label

        # 确保至少有一个标签且不是最后一个标签
        if len(labels) > 1:
            target_id = None
            sorted_items = sorted(labels.items(), key=lambda x: int(x[0]))
            for idx, (label_id, _) in enumerate(sorted_items):
                radio_widget = self.tableWidget.cellWidget(idx, 0)
                radio = radio_widget.findChild(QRadioButton)
                if radio and radio.isChecked():
                    target_id = int(label_id)
                    break

            if target_id is None:
                return

            # 2. 这里的逻辑约束：序号1通常不让删
            if target_id == 1:
                QMessageBox.warning(self, "警告", "序号为1的标签不能删除！")
                return

            # 3. 处理数组 seg (关键步骤)
            if hasattr(self.main_window, "seg"):
                seg = self.main_window.seg

                # 第一步：将要删除的 ID 区域置为 0
                seg[seg == target_id] = 0

                # 第二步：将所有大于 target_id 的像素值减 1
                # 这样 3 变 2, 4 变 3，以此类推，实现了重排映射
                seg[seg > target_id] -= 1

            # 4. 更新配置文件中的字典
            # 先删除目标
            if str(target_id) in labels:
                del labels[str(target_id)]

            # 重新构建连续的字典 { "1": info, "2": info ... }
            remaining_labels = sorted(labels.items(), key=lambda x: int(x[0]))
            new_labels = {}
            for i, (old_id, info) in enumerate(remaining_labels, 1):
                new_labels[str(i)] = info

            self.main_window._config.label = new_labels

            # 5. 保存并刷新 UI
            ConfigManager().save(self.main_window._config)
            self.init_labels()
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.clear()
            if hasattr(self.main_window, "update_image"):
                self.main_window.update_image()
        else:
            # 只有一个标签时，提示不能删除
            QMessageBox.warning(self, "警告", "至少需要保留一个标签！")

    def update_label(self, row, column):
        """更新标签信息"""
        if column == 1:  # 只处理名称列的修改（现在名称列的索引是1）
            # 从MainWindow的配置中获取标签
            if not hasattr(self.main_window, "_config"):
                return
            else:
                labels = self.main_window._config.label

            # 按标签ID排序
            sorted_labels = sorted(labels.items(), key=lambda x: int(x[0]))
            if row < len(sorted_labels):
                label_id = sorted_labels[row][0]
                # 更新名称
                name_item = self.tableWidget.item(row, 1)
                assert name_item is not None
                labels[label_id]["name"] = name_item.text()

                # 保存配置
                config_manager = ConfigManager()
                config_manager.save(self.main_window._config)

    def change_color(self, row, column):
        """修改标签颜色"""
        if column == 2:  # 只处理颜色列的双击（现在颜色列的索引是2）
            # 打开颜色选择对话框
            color_dialog = QColorDialog()
            # 从MainWindow的配置中获取当前颜色
            labels = self.main_window._config.label
            # 按标签ID排序
            sorted_labels = sorted(labels.items(), key=lambda x: int(x[0]))
            if row < len(sorted_labels):
                label_id = sorted_labels[row][0]
                current_color = labels[label_id]["color"]
                color_dialog.setCurrentColor(QColor(current_color))

                if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
                    new_color = color_dialog.currentColor().name()

                    # 更新表格
                    color_item = self.tableWidget.item(row, 2)
                    assert color_item is not None
                    color_item.setBackground(QColor(new_color))
                    # 不显示颜色文本
                    color_item.setText("")

                    # 更新配置
                    labels[label_id]["color"] = new_color

                    # 保存配置
                    config_manager = ConfigManager()
                    config_manager.save(self.main_window._config)

                    # 刷新图像
                    if hasattr(self.main_window, "update_image"):
                        self.main_window.update_image()

    def on_label_selected(self):
        """当选择标签时，发送信号给MainWindow"""
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # 获取标签ID（按表格显示顺序）
            labels = self.main_window._config.label
            # 按标签ID排序
            sorted_labels = sorted(labels.items(), key=lambda x: int(x[0]))
            if row < len(sorted_labels):
                label_id = int(sorted_labels[row][0])
                # 发送信号
                self.label_selected.emit(label_id)

    def on_select_button_clicked(self, label_id):
        """当点击选择按钮时，发送信号给MainWindow"""
        # 发送信号
        self.label_selected.emit(label_id)

    def on_cell_clicked(self, row, column):
        """当点击表格单元格时，选中对应行的radio button"""
        # 获取当前行的radio button
        radio_widget = self.tableWidget.cellWidget(row, 0)
        if radio_widget:
            # 获取widget中的radio button
            radio_button = radio_widget.findChild(QRadioButton)
            if radio_button:
                radio_button.setChecked(True)
                # 获取标签ID
                labels = self.main_window._config.label
                sorted_labels = sorted(labels.items(), key=lambda x: int(x[0]))
                if row < len(sorted_labels):
                    label_id = int(sorted_labels[row][0])
                    # 发送选择信号
                    self.on_select_button_clicked(label_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SegmentDocker(None, None)
    window.show()
    sys.exit(app.exec())
