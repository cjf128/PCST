# Copyright (c) 2026 PCViewer Jinfr
import json
import os
import shutil
import sys
import warnings
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
import pypinyin as pin
import SimpleITK as sitk
import vtk
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import (
    QActionGroup,
    QDesktopServices,
    QIcon,
    QImage,
    QPixmap,
    QUndoStack,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from viewer.app.configs import AppConfig, ConfigManager
from viewer.app.defaults import (
    APP_AUTHOR,
    APP_LICENSE,
    APP_NAME,
    APP_VERSION,
    DEFAULT_SHORTCUTS,
    DISCLAIMER_TEXT,
    PROJECT_HOMEPAGE_URL,
    PROJECT_REPOSITORY_LABEL,
    PROJECT_REPOSITORY_URL,
    normalize_label_config,
)
from viewer.app.mode import LOADMode, SAMMode, VIEWERMode, VIEWMode
from viewer.path import CACHE_PATH, ICONS_PATH
from viewer.scripts.logger import log_debug, log_error, log_info, log_warning
from viewer.ui.MainWindow_ui import Ui_MainWindow
from viewer.widgets.FileDocker import FileDocker
from viewer.widgets.ImageDocker import ImageDocker
from viewer.widgets.ImageViewer import ImageViewer
from viewer.widgets.InfoDocker import InfoDocker
from viewer.widgets.LoadDialog import LoadDialog
from viewer.widgets.SegmentDocker import SegmentDocker
from viewer.widgets.ShortcutDialog import ShortcutDialog
from viewer.widgets.commands import SegChangeCommand
from viewer.widgets.theme import ThemeManager
from viewer.widgets.WorkerThread import (
    BuiltThread,
    DicomWorker,
    ModelLoader,
    NiftiWorker,
    SamThread,
)

warnings.filterwarnings("ignore")


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._config = config
        self._config.label = normalize_label_config(self._config.label)

        self.patient_id: str = ""

        # 图像透明度参数
        self.ct_alpha: float = 0.5
        self.pet_alpha: float = 0.5
        self.seg_alpha: float = 0.5

        # 窗宽窗位参数
        self.ct_ww: float = 400.0
        self.ct_wl: float = 50.0
        self.pet_ww: float = 2.5

        # 标注与图层参数
        self.color_label: int = 1
        self.layer: int = 0
        self.num: int = -1
        self.crosshair_voxel_xyz: list[int] | None = None

        # 坐标参数
        self.y_star: int = 0
        self.y_end: int = 0
        self.x_star: int = 0
        self.x_end: int = 0

        self.radius: int = 5

        self.pet_spacing = (0, 0, 0)
        self.pet_shape = (0, 0, 0)

        # 图像数据
        self.ct: np.ndarray = np.array([])
        self.pet: np.ndarray = np.array([])
        self.seg: np.ndarray = np.array([])
        # 撤销前快照（当前层）
        self._seg_before_edit: np.ndarray | None = None

        # 状态标志
        self.load_mode = LOADMode.UNLOAD
        self.view_mode = VIEWMode.AXIAL

        # 路径参数
        self.cache_path: Path = CACHE_PATH
        self.data_path: Path = Path("")
        self.seg_file: Path = Path("")
        self.file_type: str = ""

        self.SamPredictor = None
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(10)

        self.model_loader = ModelLoader()
        self.model_loader.finished.connect(self.on_model_loaded)
        self.model_loader.start()

        self.setWindowTitle("PC Viewer")

        self.init_ui()
        self.config()
        self.init_shortcuts()
        self.init_connectAction()

    def init_shortcuts(self):
        """从配置初始化快捷键"""
        shortcuts = self._config.shortcuts or DEFAULT_SHORTCUTS

        for action_name, key_sequence in shortcuts.items():
            if hasattr(self, action_name):
                action = getattr(self, action_name)
                action.setShortcut(key_sequence)

        if not self._config.shortcuts:
            self._config.shortcuts = DEFAULT_SHORTCUTS.copy()

    def config(self) -> None:
        theme = self._config.theme

        self.theme_button_group = QActionGroup(self)
        self.theme_button_group.setExclusive(True)
        self.theme_button_group.addAction(self.dark_action)
        self.theme_button_group.addAction(self.light_action)

        if theme == "dark":
            self.dark_action.setChecked(True)
        else:
            self.light_action.setChecked(True)

        self.load_atn.setIcon(QIcon(str(ICONS_PATH / theme / "load.png")))
        self.add_atn.setIcon(QIcon(str(ICONS_PATH / theme / "add.png")))
        self.save_atn.setIcon(QIcon(str(ICONS_PATH / theme / "save.png")))
        self.aim_atn.setIcon(QIcon(str(ICONS_PATH / theme / "cursor.png")))
        self.move_atn.setIcon(QIcon(str(ICONS_PATH / theme / "move.png")))
        self.win_atn.setIcon(QIcon(str(ICONS_PATH / theme / "contrast.png")))
        self.paint_atn.setIcon(QIcon(str(ICONS_PATH / theme / "paint.png")))
        self.eraser_atn.setIcon(QIcon(str(ICONS_PATH / theme / "eraser.png")))
        self.redo_atn.setIcon(QIcon(str(ICONS_PATH / theme / "redo.png")))

        self.sam_atn.setIcon(QIcon(str(ICONS_PATH / theme / "meta.png")))
        self.data_atn.setIcon(QIcon(str(ICONS_PATH / theme / "database.png")))
        self.setting_atn.setIcon(QIcon(str(ICONS_PATH / theme / "setting.png")))

        self.segment_setting.pushButton_3.setIcon(
            QIcon(str(ICONS_PATH / theme / "frame.png"))
        )
        self.segment_setting.pushButton_4.setIcon(
            QIcon(str(ICONS_PATH / theme / "point.png"))
        )

    def init_ui(self):
        self.file_Setting = FileDocker(self, self)
        self.file_Setting_layout = QVBoxLayout(self.FileSetting)
        self.file_Setting_layout.addWidget(self.file_Setting)
        self.file_Setting_layout.setContentsMargins(0, 0, 0, 0)

        self.image_setting = ImageDocker(self, self)
        self.image_setting_layout = QVBoxLayout(self.ImageSetting)
        self.image_setting_layout.addWidget(self.image_setting)
        self.image_setting_layout.setContentsMargins(0, 0, 0, 0)

        self.segment_setting = SegmentDocker(self, self)
        self.segment_setting_layout = QVBoxLayout(self.SegmentSetting)
        self.segment_setting_layout.addWidget(self.segment_setting)
        self.segment_setting_layout.setContentsMargins(0, 0, 0, 0)
        # 连接SegmentDocker的label_selected信号
        self.segment_setting.label_selected.connect(self.update_color_label)

        self.viewer = ImageViewer(self, self)
        self.image_viewer_layout = QVBoxLayout(self.image_frame)
        self.image_viewer_layout.addWidget(self.viewer)
        self.image_viewer_layout.setContentsMargins(0, 0, 0, 0)

        self.info_setting = InfoDocker(self, self)
        info_layout = self.InfoSetting.layout()
        if info_layout:
            info_layout.addWidget(self.info_setting)

        self.view_3d = None
        self.view_layout = QVBoxLayout()
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        self.view_frame.setLayout(self.view_layout)

        self._vtk_actor_cache = None
        self._seg_cache_hash = None

        self.atn_group = QActionGroup(self)
        self.atn_group.setExclusive(True)
        self.atn_group.addAction(self.aim_atn)
        self.atn_group.addAction(self.move_atn)
        self.atn_group.addAction(self.win_atn)
        self.atn_group.addAction(self.paint_atn)
        self.atn_group.addAction(self.sam_atn)
        self.atn_group.addAction(self.eraser_atn)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.btn_group.addButton(self.btnH)
        self.btn_group.addButton(self.btnS)
        self.btn_group.addButton(self.btnG)
        self.btn_group.addButton(self.btn3D)

        self.undo_action = self.undo_stack.createUndoAction(self, "撤销")
        self.undo_action.setShortcut("Ctrl+Z")
        self.redo_action = self.undo_stack.createRedoAction(self, "重做")
        self.redo_action.setShortcut("Ctrl+Y")
        self.addAction(self.undo_action)
        self.addAction(self.redo_action)

        self.dialog = QDialog(self)
        self.dialog.setWindowModality(Qt.WindowModality.WindowModal)  # 设置为模态对话框
        self.dialog.setFixedSize(300, 100)

        layout = QVBoxLayout()
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # 设置为循环进度条
        progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(progress_bar)
        self.dialog.setLayout(layout)

        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("background-color: #1273ff;")

    def init_connectAction(self):
        """初始化信号与槽连接"""
        self.load_atn.triggered.connect(self.load_slot)
        self.add_atn.triggered.connect(self.load_Seg_slot)
        self.save_atn.triggered.connect(self.save_slot)
        self.redo_atn.triggered.connect(self.redo_slot)
        self.setting_atn.triggered.connect(self.setting_slot)
        self.data_atn.triggered.connect(self.data_slot)

        self.aim_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.AIM))
        self.sam_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.SAM))
        self.paint_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.PAINT))
        self.move_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.MOVE))
        self.win_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.WIN))
        self.eraser_atn.triggered.connect(lambda: self._set_mode(VIEWERMode.ERASER))

        self.open_action.triggered.connect(self.load_slot)
        self.add_action.triggered.connect(self.load_Seg_slot)
        self.save_action.triggered.connect(self.save_slot)
        self.exit_action.triggered.connect(self.close)
        self.crossline_action.triggered.connect(self.crossline_slot)
        self.direction_action.triggered.connect(self.direction_slot)
        self.information_action.triggered.connect(self.information_slot)
        self.actiongithub.triggered.connect(self.open_github_page)
        self.actionversion.triggered.connect(self.show_version_info)

        self.file_action.triggered.connect(self.toggle_toolBar_file)
        self.paint_action.triggered.connect(self.toggle_toolBar_draw)

        # 绑定 dockWidget 显示/隐藏到 action
        self.filesetting_action.triggered.connect(
            lambda: self.dockWidget_2.setVisible(self.filesetting_action.isChecked())
        )
        self.imageseting_action.triggered.connect(
            lambda: self.dockWidget.setVisible(self.imageseting_action.isChecked())
        )
        self.segmentsetting_action.triggered.connect(
            lambda: self.dockWidget_3.setVisible(self.segmentsetting_action.isChecked())
        )
        self.info_action.triggered.connect(
            lambda: self.dockWidget_4.setVisible(self.info_action.isChecked())
        )

        self.boxLayer.valueChanged.connect(
            lambda v: self.update_property_and_refresh("layer", v)
        )

        self.boxCT.clicked.connect(self.update_all)
        self.boxPET.clicked.connect(self.update_all)
        self.boxSeg.clicked.connect(self.update_all)

        self.btnH.clicked.connect(lambda: self.change_slot(VIEWMode.AXIAL))
        self.btnS.clicked.connect(lambda: self.change_slot(VIEWMode.SAGITTAL))
        self.btnG.clicked.connect(lambda: self.change_slot(VIEWMode.CORONAL))
        self.btn3D.clicked.connect(self.view_3d_built)

        self.btnCa.clicked.connect(self.screen_shot)
        self.btnRefresh.clicked.connect(self.refresh_slot)
        self.btnReset.clicked.connect(self.reset_slot)

        self.viewer.Sam_Signal.connect(self.operation)
        self.viewer.Mode_Signal.connect(self._update_mode_from_buttons)

        # 主题切换信号槽
        self.dark_action.triggered.connect(lambda: self.change_theme("dark"))
        self.light_action.triggered.connect(lambda: self.change_theme("light"))

        # 快捷键设置
        self.shortcut_action.triggered.connect(self.show_shortcut_dialog)

        self.file_Setting.file_name.connect(self.viewer.patient_name_change)

    def transpose(self, mode):
        if mode == "trans":
            if self.view_mode == VIEWMode.AXIAL:
                return [1, 2, 0]
            if self.view_mode == VIEWMode.SAGITTAL:
                return [0, 1, 2]
            if self.view_mode == VIEWMode.CORONAL:
                return [0, 2, 1]
        elif mode == "save":
            if self.view_mode == VIEWMode.AXIAL:
                return [2, 0, 1]
            if self.view_mode == VIEWMode.SAGITTAL:
                return [0, 1, 2]
            if self.view_mode == VIEWMode.CORONAL:
                return [0, 2, 1]

    def _has_volume(self):
        return hasattr(self, "ct") and self.ct.size > 0

    def _clamp_index(self, value, size):
        if size <= 0:
            return 0
        return max(0, min(int(round(value)), size - 1))

    def _volume_shape_xyz(self):
        if not self._has_volume():
            return (0, 0, 0)

        rows, cols, layers = self.ct.shape
        if self.view_mode == VIEWMode.AXIAL:
            return (cols, rows, layers)
        if self.view_mode == VIEWMode.CORONAL:
            return (cols, layers, rows)
        if self.view_mode == VIEWMode.SAGITTAL:
            return (layers, cols, rows)
        return (cols, rows, layers)

    def _clamp_voxel_xyz(self, voxel_xyz):
        size_x, size_y, size_z = self._volume_shape_xyz()
        x, y, z = voxel_xyz
        return [
            self._clamp_index(x, size_x),
            self._clamp_index(y, size_y),
            self._clamp_index(z, size_z),
        ]

    def slice_point_to_voxel_xyz(self, image_x, image_y, layer):
        if self.view_mode == VIEWMode.AXIAL:
            voxel_xyz = [image_x, image_y, layer]
        elif self.view_mode == VIEWMode.CORONAL:
            voxel_xyz = [image_x, layer, image_y]
        elif self.view_mode == VIEWMode.SAGITTAL:
            voxel_xyz = [layer, image_x, image_y]
        else:
            voxel_xyz = [image_x, image_y, layer]
        return self._clamp_voxel_xyz(voxel_xyz)

    def voxel_xyz_to_slice_point(self, voxel_xyz):
        x, y, z = self._clamp_voxel_xyz(voxel_xyz)
        if self.view_mode == VIEWMode.AXIAL:
            return x, y, z
        if self.view_mode == VIEWMode.CORONAL:
            return x, z, y
        if self.view_mode == VIEWMode.SAGITTAL:
            return y, z, x
        return x, y, z

    def _set_layer_controls(self, layer):
        if not self._has_volume():
            return

        layer = self._clamp_index(layer, self.ct.shape[2])
        self.layer = layer

        old_sld_state = self.sldLayer.blockSignals(True)
        old_box_state = self.boxLayer.blockSignals(True)
        try:
            self.sldLayer.setValue(layer)
            self.boxLayer.setValue(layer)
        finally:
            self.sldLayer.blockSignals(old_sld_state)
            self.boxLayer.blockSignals(old_box_state)

    def update_crosshair_from_slice_point(self, point):
        if self.load_mode == LOADMode.UNLOAD or not self._has_volume():
            return

        self.crosshair_voxel_xyz = self.slice_point_to_voxel_xyz(
            point.x(),
            point.y(),
            self.layer,
        )
        self.sync_crosshair_overlay()

    def sync_crosshair_overlay(self):
        if not hasattr(self, "viewer"):
            return

        if self.crosshair_voxel_xyz is None or not self._has_volume():
            self.viewer.clear_crosshair_point()
            return

        image_x, image_y, _ = self.voxel_xyz_to_slice_point(self.crosshair_voxel_xyz)
        self.viewer.set_crosshair_point(image_x, image_y)

    def on_model_loaded(self, predictor):
        self.SamPredictor = predictor
        log_info("SAM模型已加载到主窗口")

    def data_slot(self):
        if self.dockWidget_2.isVisible():
            self.dockWidget_2.hide()
        else:
            self.dockWidget_2.show()
            self.dockWidget_2.raise_()

    def setting_slot(self):
        if self.dockWidget.isVisible():
            self.dockWidget.hide()
            self.dockWidget_3.hide()
            self.dockWidget_4.hide()
        else:
            self.dockWidget.show()
            self.dockWidget_3.show()
            self.dockWidget_4.show()
            self.dockWidget.raise_()

    def toggle_toolBar_file(self):
        self.toolBar_file.setVisible(not self.toolBar_file.isVisible())

    def toggle_toolBar_draw(self):
        self.toolBar_draw.setVisible(not self.toolBar_draw.isVisible())

    def screen_shot(self):
        if self.load_mode != LOADMode.UNLOAD:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Screenshot_{timestamp}.png"
            save_path = QFileDialog.getSaveFileName(
                self, "保存图片", filename, "PNG (*.png)"
            )[0]

            viewport = self.viewer.viewport()
            pixmap = viewport.grab()
            if save_path:
                pixmap.save(save_path)

    def change_slot(self, mode):
        if self.load_mode != LOADMode.UNLOAD:
            self.stackedWidget.setCurrentIndex(0)

            save = self.transpose("save")
            self.pet = np.transpose(self.pet, axes=save)
            self.ct = np.transpose(self.ct, axes=save)
            self.seg = np.transpose(self.seg, axes=save)

            self.view_mode = mode
            self.viewer.view_mode = mode

            trans = self.transpose("trans")
            self.pet = np.transpose(self.pet, axes=trans)
            self.ct = np.transpose(self.ct, axes=trans)
            self.seg = np.transpose(self.seg, axes=trans)

            self.load_mode = LOADMode.CHANGE
            self.setting()

    def reset_slot(self):
        """复位处理"""
        if self.load_mode != LOADMode.UNLOAD:
            self.viewer.fitInView(
                self.viewer.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio
            )
            self.sync_crosshair_overlay()

    def refresh_slot(self):
        """刷新视图"""
        if self.btn3D.isChecked():
            self.view_3d_built()
            log_info("刷新3D视图")
        else:
            pass

    def change_theme(self, theme):
        """切换主题"""
        self._config.theme = theme

        config_manager = ConfigManager()
        config_manager.save(self._config)

        ThemeManager.set_theme(theme)

        self.load_atn.setIcon(QIcon(str(ICONS_PATH / theme / "load.png")))
        self.add_atn.setIcon(QIcon(str(ICONS_PATH / theme / "add.png")))
        self.save_atn.setIcon(QIcon(str(ICONS_PATH / theme / "save.png")))
        self.aim_atn.setIcon(QIcon(str(ICONS_PATH / theme / "cursor.png")))
        self.move_atn.setIcon(QIcon(str(ICONS_PATH / theme / "move.png")))
        self.win_atn.setIcon(QIcon(str(ICONS_PATH / theme / "contrast.png")))
        self.paint_atn.setIcon(QIcon(str(ICONS_PATH / theme / "paint.png")))
        self.eraser_atn.setIcon(QIcon(str(ICONS_PATH / theme / "eraser.png")))
        self.redo_atn.setIcon(QIcon(str(ICONS_PATH / theme / "redo.png")))

        self.sam_atn.setIcon(QIcon(str(ICONS_PATH / theme / "meta.png")))
        self.data_atn.setIcon(QIcon(str(ICONS_PATH / theme / "database.png")))
        self.setting_atn.setIcon(QIcon(str(ICONS_PATH / theme / "setting.png")))

        self.segment_setting.pushButton_3.setIcon(
            QIcon(str(ICONS_PATH / theme / "frame.png"))
        )
        self.segment_setting.pushButton_4.setIcon(
            QIcon(str(ICONS_PATH / theme / "point.png"))
        )

        self.update_all()

    def show_shortcut_dialog(self):
        """显示快捷键设置对话框"""
        dialog = ShortcutDialog(self)
        dialog.shortcuts_changed.connect(self._on_shortcuts_changed)
        dialog.exec()

    def _on_shortcuts_changed(self, shortcuts_dict: dict):
        """快捷键更改时的处理"""
        config_manager = ConfigManager()
        self._config.shortcuts = shortcuts_dict
        config_manager.save(self._config)
        self.viewer.setCursor(
            Qt.CursorShape.ArrowCursor
        )  # 切换回默认光标，避免快捷键冲突导致的光标异常
        log_info(f"快捷键已更新: {shortcuts_dict}")

    def open_github_page(self):
        """打开项目主页。"""
        opened = QDesktopServices.openUrl(QUrl(PROJECT_HOMEPAGE_URL))
        if not opened:
            QMessageBox.warning(self, "打开失败", f"无法打开链接：{PROJECT_HOMEPAGE_URL}")

    def show_version_info(self):
        """显示软件信息。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("软件信息")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        info_label = QLabel(dialog)
        info_label.setMinimumWidth(360)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        info_label.setOpenExternalLinks(True)
        info_label.setText(
            f"""
            <h3>{APP_NAME}</h3>
            <p><b>作者名：</b>{APP_AUTHOR}</p>
            <p><b>版本号：</b>{APP_VERSION}</p>
            <p><b>开源协议：</b>{APP_LICENSE}</p>
            <p><b>GitHub 地址：</b>
            <a href="{PROJECT_REPOSITORY_URL}">{PROJECT_REPOSITORY_LABEL}</a></p>
            <p><b>免责声明：</b>{DISCLAIMER_TEXT}</p>
            """
        )
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, dialog)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def redo_slot(self):
        """重做-清空标注"""
        if self.load_mode != LOADMode.UNLOAD:
            reply = QMessageBox.question(
                self,
                "确认",
                "是否确认清空所有标注？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.seg = np.zeros_like(self.ct)
                self.viewer.input_box = []
                self.update_image()

    def load_Seg_slot(self):
        if self.load_mode == LOADMode.UNLOAD:
            log_warning("请先输入原始数据")
            QMessageBox.warning(
                self, "警告！", "请先输入原始数据！", QMessageBox.StandardButton.Ok
            )
            return
        else:
            seg_file, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "NIfTI Files (*.nii *.nii.gz)"
            )
            if seg_file:
                log_info(f"加载分割文件: {seg_file}")
                self.seg_file = Path(seg_file)

                seg = sitk.ReadImage(str(self.seg_file))
                seg = sitk.DICOMOrient(seg, "LPS")
                seg_data = sitk.GetArrayFromImage(seg)
                trans = self.transpose("trans")
                seg_data = np.transpose(seg_data, axes=trans)
                if seg_data.shape == self.ct.shape:
                    self.seg = seg_data

                    # 检查 seg 最大值是否大于当前 label 数目
                    max_label = int(np.max(seg_data))
                    current_label_count = len(self._config.label)

                    log_info(f"当前 label 数量: {current_label_count}")
                    log_info(f"seg 最大值: {max_label}")

                    # 重新排序标签序号，确保连续
                    sorted_labels = sorted(
                        self._config.label.items(), key=lambda x: int(x[0])
                    )
                    new_labels = {}
                    for i, (old_id, label_info) in enumerate(sorted_labels, 1):
                        new_labels[str(i)] = label_info
                        # 更新seg数组中的标签ID
                        if seg_data.size > 0:
                            seg_data[seg_data == int(old_id)] = i
                    # 替换为新的标签配置
                    self._config.label = new_labels
                    current_label_count = len(self._config.label)

                    if max_label > current_label_count:
                        log_info(f"需要添加 {max_label - current_label_count} 个 label")
                        # 自动添加缺失的 label
                        import random

                        for i in range(current_label_count + 1, max_label + 1):
                            # 生成随机颜色
                            r = random.randint(0, 255)
                            g = random.randint(0, 255)
                            b = random.randint(0, 255)
                            color = f"#{r:02x}{g:02x}{b:02x}"
                            # 添加到配置中
                            self._config.label[str(i)] = {
                                "name": f"Label {i}",
                                "color": color,
                            }
                            log_info(f"添加 label {i}: {color}")

                        config_manager = ConfigManager()
                        config_manager.save(self._config)
                        log_info(
                            f"自动添加了 {max_label - current_label_count} 个 label"
                        )

                        # 更新 SegmentDocker 的表格
                        if hasattr(self, "segment_setting"):
                            log_info("更新 SegmentDocker 表格")
                            self.segment_setting.init_labels()
                        else:
                            log_error("segment_setting 不存在")

                    self.update_image()
                    log_info(f"分割文件加载成功: {seg_file}")
                else:
                    log_error(
                        f"分割文件形状不匹配: {seg_data.shape} vs {self.pet.shape}"
                    )
                    QMessageBox.warning(
                        self,
                        "警告！",
                        "输入标签与原始数据不符，请检查标注是否正确！",
                        QMessageBox.StandardButton.Ok,
                    )
                    return
            else:
                return

    def load_slot(self):
        """导入数据对话框"""
        log_info("打开数据加载对话框")
        cache_path = Path(self.cache_path)
        if cache_path.exists():
            for file_path in cache_path.iterdir():
                if file_path.is_dir():
                    shutil.rmtree(str(file_path))
                else:
                    file_path.unlink()

        load_dialog = LoadDialog(self, self)
        load_dialog.FilesSelected.connect(self.on_files_selected)
        load_dialog.show()

    def on_files_selected(
        self, pet_file: Path, ct_file: Path, file_type: str, data_id: str = ""
    ):
        """处理文件选择"""
        log_info(f"选择文件 - PET: {pet_file}, CT: {ct_file}, 类型: {file_type}")
        self.current_data_id = data_id

        self.dialog.setWindowTitle("导入中")
        self.dialog.show()

        pet_path = Path(pet_file)
        patient_id = pet_path.parent.name
        patient_id = pin.slug(patient_id)
        if "-" in patient_id:
            patient_id = patient_id.replace("-", "")
        if "_" in patient_id:
            patient_id = patient_id.replace("_", "")
        if len(patient_id) >= 4 and patient_id[:4].isdigit():
            patient_id = patient_id[4:]

        self.patient_id = patient_id
        self.file_type = file_type

        data_folder = Path(self.cache_path) / self.patient_id
        data_folder.mkdir(parents=True, exist_ok=True)
        self.data_path = data_folder

        if file_type == "NIfTI":
            self._load_nifti_files(pet_file, ct_file)
        else:
            self._load_dicom_files(pet_file, ct_file, data_folder)

    def reload_data(self, data_id):
        """重新导入指定ID的数据"""
        if data_id in self._config.data:
            data_info = self._config.data[data_id]
            pet_file = data_info.get("pet")
            ct_file = data_info.get("ct")
            file_type = data_info.get("type")

            path_exists = True
            if pet_file and not os.path.exists(pet_file):
                path_exists = False
            if ct_file and not os.path.exists(ct_file):
                path_exists = False

            if pet_file and ct_file:
                if path_exists:
                    log_info(
                        f"重新导入数据 - ID: {data_id}, PET: {pet_file}, CT: {ct_file}, 类型: {file_type}"
                    )
                    self.current_data_id = data_id
                    self.on_files_selected(pet_file, ct_file, file_type, data_id)
                else:
                    reply = QMessageBox.warning(
                        self,
                        "路径不存在",
                        "路径不存在，请重新导入",
                        QMessageBox.StandardButton.Ok,
                    )
                    if reply == QMessageBox.StandardButton.Ok:
                        self.file_Setting.delete_data(data_id=data_id)
            else:
                log_error(f"数据ID {data_id} 的文件路径不完整")
        else:
            log_error(f"未找到数据ID {data_id}")

    def on_data_loaded(
        self,
        ct_data: np.ndarray,
        pet_data: np.ndarray,
        ct_spacing: tuple,
        pet_spacing: tuple,
        pet_shape: tuple,
        patient_info=None,
    ):
        """数据加载完成后的处理"""
        self.load_mode = LOADMode.RELOAD

        log_info(f"{ct_spacing}, {pet_spacing}, {pet_shape}")
        self.viewer.spacing = ct_spacing
        self.pet_spacing = pet_spacing
        self.pet_shape = pet_shape

        trans = self.transpose("trans")
        self.ct = np.transpose(ct_data, axes=trans)
        self.pet = np.transpose(pet_data, axes=trans)
        self.seg = np.zeros_like(self.pet, dtype=np.uint8)
        self.crosshair_voxel_xyz = None

        self.undo_stack.clear()
        self.setting()

        # 更新信息显示
        self.update_info_docker(patient_info)
        log_info("信息更新显示")

        # 更新FileDocker的文件列表
        if hasattr(self, "file_Setting"):
            self.file_Setting.load_file_list()

        # 获取当前数据的final_name并发出file_name信号，更新viewer显示
        if hasattr(self, "current_data_id") and self.current_data_id:
            data_id = self.current_data_id
            if data_id in self._config.data:
                raw_name = self._config.data[data_id].get("name", "")
                final_name = raw_name.split(".")[0] if raw_name else ""
                if hasattr(self, "file_Setting"):
                    self.file_Setting.file_name.emit(final_name)
                    self.file_Setting.select_item_by_id(data_id)

    def _load_dicom_files(self, pet_file: Path, ct_file: Path, data_folder: Path):
        """处理DICOM/IMA文件"""
        self.worker_thread = DicomWorker(pet_file, ct_file, data_folder)
        self.worker_thread.finished.connect(self.dialog.close)
        self.worker_thread.finished.connect(self.on_data_loaded)
        self.worker_thread.start()

    def _load_nifti_files(self, pet_file: Path, ct_file: Path):
        """处理NIfTI文件"""
        self.worker_thread = NiftiWorker(pet_file, ct_file)
        self.worker_thread.finished.connect(self.dialog.close)
        self.worker_thread.finished.connect(self.on_data_loaded)
        self.worker_thread.start()

    def setting(self):
        """导入数据后初始化层数"""
        self.seg_file = Path("")
        self.viewer.information_show = True
        if self.crosshair_voxel_xyz is None:
            self.viewer.position[0] = self.viewer.width() // 2
            self.viewer.position[1] = self.viewer.height() // 2

        self.stackedWidget.setCurrentIndex(0)

        if self.load_mode != LOADMode.CHANGE:
            self.image_setting.boxAlphaCt.setValue(self.ct_alpha)
            self.image_setting.boxCT_wl.setValue(int(self.ct_wl))
            self.image_setting.boxCT_ww.setValue(int(self.ct_ww))
            self.image_setting.boxAlphaPet.setValue(self.pet_alpha)

            self.segment_setting.boxPaint.setValue(self.radius)

            pet_max = np.max(self.pet)
            self.pet_ww = pet_max
            self.image_setting.boxPET_ww.setValue(self.pet_ww)

            self.segment_setting.boxAlphaSeg.setValue(self.seg_alpha)

        self.sldLayer.setMaximum(self.ct.shape[2] - 1)
        self.boxLayer.setMaximum(self.ct.shape[2] - 1)
        if self.crosshair_voxel_xyz is None:
            layer = self.ct.shape[2] // 2
        else:
            _, _, layer = self.voxel_xyz_to_slice_point(self.crosshair_voxel_xyz)
        self._set_layer_controls(layer)

        self.update_image()

    def run_slot(self):
        """运行预测"""
        pass

    def save_slot(self):
        """保存设置"""
        if np.any(self.seg):
            current_path = os.getcwd()
            # 设置默认保存名字
            default_name = self.patient_id if self.patient_id else "segmentation"
            default_file = str(Path(current_path) / f"{default_name}.nii.gz")

            file_, ok = QFileDialog.getSaveFileName(
                self, "文件保存", default_file, "NFiTI(*.nii.gz)"
            )

            if file_ != "":
                log_info(f"保存分割文件: {file_}")
                image = np.copy(self.seg)
                save = self.transpose("save")
                image = np.transpose(image, axes=save)
                image = sitk.GetImageFromArray(image)
                self.statusBar().showMessage("已保存文件：" + file_)
                sitk.WriteImage(image, file_)
        else:
            log_warning("无可保存分割图像")
            QMessageBox.warning(
                self, "警告", "无可保存分割图像！", QMessageBox.StandardButton.Ok
            )

    def crossline_slot(self):
        self.viewer.cross_show = not self.viewer.cross_show
        self.viewer.viewport().update()

    def information_slot(self):
        self.viewer.information_show = not self.viewer.information_show
        self.viewer.viewport().update()

    def direction_slot(self):
        self.viewer.direction_show = not self.viewer.direction_show
        self.viewer.viewport().update()

    def _set_mode(self, mode: VIEWERMode):
        if self.load_mode != LOADMode.UNLOAD:
            self.viewer.mode = mode
            self.update_all()

    def _update_mode_from_buttons(self):
        """根据按钮状态更新模式"""
        if self.load_mode != LOADMode.UNLOAD:
            if self.aim_atn.isChecked():
                self.viewer.mode = VIEWERMode.AIM
            elif self.move_atn.isChecked():
                self.viewer.mode = VIEWERMode.MOVE
            elif self.win_atn.isChecked():
                self.viewer.mode = VIEWERMode.WIN
            elif self.paint_atn.isChecked():
                self.viewer.mode = VIEWERMode.PAINT
            elif self.sam_atn.isChecked():
                self.viewer.mode = VIEWERMode.SAM
            elif self.eraser_atn.isChecked():
                self.viewer.mode = VIEWERMode.ERASER
            self.update_all()

    def update_all(self):
        """更新-以防按键冲突后仍有残留项"""
        if self.load_mode != LOADMode.UNLOAD:
            self.viewer.input_box = []
            self.update_image()
            if self.stackedWidget.currentIndex() == 1:
                self.view_3d_built()

    def operation(self, input_data):
        log_debug(f"SAM操作开始, 输入数据: {input_data}")
        self.dialog.setWindowTitle("运行中...")
        self.dialog.show()

        try:
            ct_slice = self.ct[:, :, self.layer]
            ct_slice = self.normalize(ct_slice, self.ct_ww, self.ct_wl)
            ct_slice = np.stack([ct_slice] * 3, axis=-1)

            pet_slice = self.pet[:, :, self.layer]
            pet_slice = self.normalize(pet_slice, self.pet_ww, self.pet_ww / 2)
            pet_slice = cv2.applyColorMap(pet_slice, cv2.COLORMAP_HOT)

            ct_alpha = self.ct_alpha if self.boxCT.isChecked() else 0
            pet_alpha = self.pet_alpha if self.boxPET.isChecked() else 0
            current_slice = cv2.addWeighted(ct_slice, ct_alpha, pet_slice, pet_alpha, 0)

            change_image_mode = False
            if self.layer != self.num:
                change_image_mode = True
                self.num = self.layer

            # 获取当前SAM模式
            current_mode = "BOX"  # 默认BOX模式点
            if hasattr(self, "segment_setting") and hasattr(
                self.segment_setting, "current_mode"
            ):
                sam_mode = self.segment_setting.current_mode
                if sam_mode == SAMMode.BOX:
                    current_mode = "BOX"
                elif sam_mode == SAMMode.ADD:
                    current_mode = "ADD"

            # 在 SAM 修改前先缓存当前层的切片，供撤销使用
            old_slice = self.seg[:, :, self.layer].copy()
            current_layer = self.layer  # 保存当前层索引，避免lambda捕获问题

            # 使用闭包正确捕获old_slice和layer值
            def on_sam_finished(mask):
                self.dialog.close()
                self.seg[:, :, current_layer] = np.where(
                    mask > 0, self.color_label, self.seg[:, :, current_layer]
                )
                # 检查变化并提交撤销命令
                new_slice = self.seg[:, :, current_layer]
                if not np.array_equal(old_slice, new_slice):
                    self.commit_seg_change(
                        current_layer, old_slice, new_slice, "SAM分割"
                    )
                self.update_all()
                self._update_mode_from_buttons()

            # 启动SAM线程
            self.SamThread = SamThread(
                self.SamPredictor,
                current_slice,
                input_data,
                current_mode,
                change_image_mode,
            )
            self.SamThread.finished.connect(on_sam_finished)
            self.SamThread.start()
        except Exception as e:
            log_error(f"SAM操作失败: {e}")
            return

    def normalize(self, slice, ww, wl):
        window_upper = wl + ww / 2
        window_lower = wl - ww / 2

        slice = np.clip(slice, window_lower, window_upper)
        slice = (slice - window_lower) / (window_upper - window_lower) * 255
        slice = slice.astype(np.uint8)
        return slice

    def update_image(self):
        """图像更新"""
        if self.load_mode != LOADMode.UNLOAD:
            img = self.prepare_image()
            self.viewer.load_image(img, self.radius)

        if self.load_mode == LOADMode.CHANGE or self.load_mode == LOADMode.RELOAD:
            self.viewer.fitInView(
                self.viewer.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio
            )
            self.viewer._scene.setSceneRect(self.viewer.pixmap_item.sceneBoundingRect())
            self.load_mode = LOADMode.LOADED

        if self.load_mode != LOADMode.UNLOAD:
            self.sync_crosshair_overlay()

    def update_property_and_refresh(self, attr_name, value):
        old_value = getattr(self, attr_name, None)
        setattr(self, attr_name, value)
        # 如果切换了层，清理编辑缓存
        if attr_name == "layer" and old_value is not None and old_value != value:
            self._seg_before_edit = None
        if self.load_mode != LOADMode.UNLOAD:
            self.update_image()

    def update_color_label(self, label_id):
        """更新颜色标签"""
        self.color_label = label_id

    def update_info_docker(self, patient_info=None):
        """更新信息显示"""
        if self.load_mode != LOADMode.UNLOAD:
            # 收集信息
            info = {}

            # 维度信息
            if hasattr(self, "ct") and self.ct.size > 0:
                info["CT尺寸"] = (
                    f"{self.ct.shape[0]} {self.ct.shape[1]} {self.ct.shape[2]}"
                )
                info["PET尺寸"] = (
                    f"{self.pet_shape[2]} {self.pet_shape[1]} {self.pet_shape[0]}"
                )

            # Spacing信息
            if hasattr(self.viewer, "spacing") and self.viewer.spacing:
                info["CT层厚"] = (
                    f"{self.viewer.spacing[0]:.3f}, {self.viewer.spacing[1]:.3f}, {self.viewer.spacing[2]:.3f}"
                )
                info["PET层厚"] = (
                    f"{self.pet_spacing[0]:.3f}, {self.pet_spacing[1]:.3f}, {self.pet_spacing[2]:.3f}"
                )

            # CT和PET的最小值和最大值
            if hasattr(self, "ct") and self.ct.size > 0:
                info["CT最小值"] = f"{np.min(self.ct):.2f}"
                info["CT最大值"] = f"{np.max(self.ct):.2f}"
            if hasattr(self, "pet") and self.pet.size > 0:
                info["SUV最小值"] = f"{np.min(self.pet):.2f}"
                info["SUV最大值"] = f"{np.max(self.pet):.2f}"

            # 患者信息
            if patient_info:
                # 按照固定顺序添加患者信息
                patient_keys = ["患者名", "性别", "出生日期", "体重"]
                # 仅在DICOM模式下显示患者ID
                if self.file_type != "NIfTI":
                    patient_keys.insert(1, "患者ID")
                for key in patient_keys:
                    if key in patient_info:
                        info[key] = patient_info[key]
                # 添加其他可能的患者信息
                for key, value in patient_info.items():
                    if key not in patient_keys:
                        info[key] = value

            # 更新InfoDocker
            if hasattr(self, "info_setting"):
                self.info_setting.update_info(info)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "退出提示",
            "确定退出?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            config_manager = ConfigManager()
            config_manager.save(self._config)

            log_info("应用程序关闭，清理缓存")
            clear_path = [Path(self.cache_path)]
            for directory_path in clear_path:
                if directory_path.exists():
                    for file_path in directory_path.iterdir():
                        if file_path.is_file() or file_path.is_symlink():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(str(file_path))
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        """鼠标按下事件重写，用于拖拽和绘图"""
        super().mousePressEvent(event)
        if self.load_mode != LOADMode.UNLOAD:
            if event.button() == Qt.MouseButton.RightButton:
                self.update_all()

            elif event.button() == Qt.MouseButton.LeftButton:
                if self.paint_atn.isChecked() or self.eraser_atn.isChecked():
                    # 在开始绘制前，缓存当前层的切片，作为撤销的 old_slice
                    if self._seg_before_edit is None:
                        self._seg_before_edit = self.seg[:, :, self.layer].copy()

                    point = self.viewer.point  # 获取 QPoint 对象
                    x = point.x()  # 获取 x 坐标
                    y = point.y()  # 获取 y 坐标

                    arr = np.array(self.seg[:, :, self.layer], dtype=np.uint8)
                    rows, cols = arr.shape

                    for i in range(
                        max(x - self.radius, 0), min(x + self.radius + 1, cols)
                    ):
                        for j in range(
                            max(y - self.radius, 0), min(y + self.radius + 1, rows)
                        ):
                            distance_squared = (i - x) ** 2 + (j - y) ** 2
                            if distance_squared <= self.radius**2:
                                arr[j, i] = self.viewer.draw_state * self.color_label

                    self.seg[:, :, self.layer] = arr
                    self.update_all()

        event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动重写，用于移动和绘图"""
        super().mouseMoveEvent(event)
        if (
            self.load_mode != LOADMode.UNLOAD
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            if self.win_atn.isChecked() and self.viewer.underMouse():
                delta = self.viewer.delta

                self.ct_ww = np.clip(self.ct_ww, 1, 4000)
                self.ct_wl = np.clip(self.ct_wl, -2000, 2000)

                self.ct_ww += int(delta.x())
                self.ct_wl += int(delta.y())
                self.image_setting.boxCT_ww.setValue(int(self.ct_ww))
                self.image_setting.boxCT_wl.setValue(int(self.ct_wl))

            elif self.paint_atn.isChecked() or self.eraser_atn.isChecked():
                point = self.viewer.point  # 获取 QPoint 对象
                x = point.x()  # 获取 x 坐标
                y = point.y()  # 获取 y 坐标

                arr = np.array(self.seg[:, :, self.layer], dtype=np.uint8)
                rows, cols = arr.shape

                for i in range(max(x - self.radius, 0), min(x + self.radius, cols)):
                    for j in range(max(y - self.radius, 0), min(y + self.radius, rows)):
                        distance_squared = (i - x) ** 2 + (j - y) ** 2
                        if distance_squared <= self.radius**2:
                            arr[j, i] = self.viewer.draw_state * self.color_label

                self.seg[:, :, self.layer] = arr
                self.update_all()

        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.paint_atn.isChecked() or self.eraser_atn.isChecked():
            # 鼠标抬起时，将修改前后的当前层切片压入撤销栈
            if self._seg_before_edit is not None:
                new_slice = self.seg[:, :, self.layer]
                # 只有当切片确实发生变化时才记录撤销命令
                if not np.array_equal(self._seg_before_edit, new_slice):
                    self.commit_seg_change(
                        self.layer, self._seg_before_edit, new_slice, "绘制"
                    )
                self._seg_before_edit = None

        event.accept()

    def wheelEvent(self, event):
        super().wheelEvent(event)
        """鼠标滚动重写，用于切换层数，放缩"""
        angle = event.angleDelta()

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.paint_atn.isChecked() or self.eraser_atn.isChecked():
                if angle.y() > 0 and self.radius < 30:
                    self.radius += 1
                    self.segment_setting.boxPaint.setValue(self.radius)
                elif angle.y() < 0 and self.radius > 1:
                    self.radius -= 1
                    self.segment_setting.boxPaint.setValue(self.radius)

        elif self.load_mode != LOADMode.UNLOAD and self.viewer.wheel:
            old_layer = self.layer
            if angle.y() > 0 and self.layer < self.ct.shape[2] - 1:
                self.layer += 1
                self._set_layer_controls(self.layer)
            elif angle.y() < 0 < self.layer:
                self.layer -= 1
                self._set_layer_controls(self.layer)

            # 切换层时，清理之前层的编辑缓存
            if old_layer != self.layer:
                self._seg_before_edit = None

        self.update_all()

        event.accept()

    def prepare_image(self):
        """更新显示图像"""
        ct = self.ct[:, :, self.layer]
        ct = self.normalize(ct, self.ct_ww, self.ct_wl)

        pet = self.pet[:, :, self.layer]
        pet = self.normalize(pet, self.pet_ww, self.pet_ww / 2)

        new_ct = np.stack([ct] * 3, axis=-1)
        new_pet = cv2.applyColorMap(pet, cv2.COLORMAP_HOT)
        seg = self.seg[:, :, self.layer]

        # 获取标签颜色配置
        label_colors = []
        for label_id, label_info in self._config.label.items():
            # 解析颜色值
            color = label_info["color"]
            # 将十六进制颜色转换为RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            label_colors.append((int(label_id), (b, g, r)))

        # 按标签序号排序
        label_colors.sort(key=lambda x: x[0])

        overlay = np.zeros_like(new_ct)
        # 为每个标签设置颜色
        for label_id, color in label_colors:
            overlay[seg == label_id] = color

        ct_alpha = self.ct_alpha if self.boxCT.isChecked() else 0
        pet_alpha = self.pet_alpha if self.boxPET.isChecked() else 0
        seg_alpha = self.seg_alpha if self.boxSeg.isChecked() else 0
        new_im = cv2.addWeighted(new_ct, ct_alpha, new_pet, pet_alpha, 0)
        mask = seg > 0
        mask = np.stack([mask] * 3, axis=-1)
        new_im = np.where(
            mask, cv2.addWeighted(new_im, 1 - seg_alpha, overlay, seg_alpha, 0), new_im
        )

        height, width, channels = new_im.shape
        bytes_per_line = channels * width
        pre_image = QImage(
            new_im.data, width, height, bytes_per_line, QImage.Format.Format_BGR888
        )
        pre_image = QPixmap.fromImage(pre_image)

        return pre_image

    def view_3d_built(self):
        self.stackedWidget.setCurrentIndex(1)

        # 延迟创建 VTK 组件，避免 Linux 下启动时出现额外原生窗口
        if self.view_3d is None:
            self.view_3d = QVTKRenderWindowInteractor(self.view_frame)
            self.view_layout.addWidget(self.view_3d)

        if not hasattr(self, "renderer"):
            self.renderer = vtk.vtkRenderer()
            self.view_3d.GetRenderWindow().AddRenderer(self.renderer)
            self.iren = self.view_3d.GetRenderWindow().GetInteractor()
            self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
            self.renderer.SetBackground(0, 0, 0)

        if self.load_mode != LOADMode.UNLOAD and np.any(self.seg):
            seg = self.seg.copy()
            save = self.transpose("save")
            seg = np.transpose(seg, axes=save)
            data = np.ascontiguousarray(seg)

            data_hash = hash(data.tobytes())
            label_hash = hash(json.dumps(self._config.label, sort_keys=True))
            current_hash = hash((data_hash, label_hash))

            if (
                current_hash == self._seg_cache_hash
                and self._vtk_actor_cache is not None
            ):
                if self.renderer.GetActors().GetNumberOfItems() == 0:
                    self.renderer.AddActor(self._vtk_actor_cache)
                    self.renderer.ResetCamera()
                self.view_3d.GetRenderWindow().Render()
                return

            self.renderer.RemoveAllViewProps()

            def add_vtk_actor(actor):
                self.renderer.AddActor(actor)
                self.renderer.ResetCamera()
                self._vtk_actor_cache = actor
                self._seg_cache_hash = current_hash
                self.view_3d.GetRenderWindow().Render()

            self.Built_Thread = BuiltThread(
                data, self.viewer.spacing, self._config.label
            )
            self.Built_Thread.actor_ready.connect(add_vtk_actor)
            self.Built_Thread.start()
        else:
            self.renderer.RemoveAllViewProps()
            self._vtk_actor_cache = None
            self._seg_cache_hash = None
            self.renderer.ResetCamera()
            self.view_3d.GetRenderWindow().Render()

    def commit_seg_change(self, layer, old_slice, new_slice, description="编辑"):
        """当某一层 seg 发生变化时，调用此函数记录撤销命令"""
        if old_slice is None or new_slice is None:
            return

        command = SegChangeCommand(self, layer, old_slice, new_slice, description)
        self.undo_stack.push(command)


if __name__ == "__main__":
    from viewer.app.configs import ConfigManager

    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    config = config_manager.load()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
