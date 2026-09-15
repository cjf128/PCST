# Copyright (c) 2026 PCST Jinfr
import json
import os
import re
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
from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import (
    QActionGroup,
    QDesktopServices,
    QIcon,
    QImage,
    QColor,
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
from pcst.app.configs import AppConfig, ConfigManager
from pcst.app.defaults import (
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
from pcst.app.mode import LOADMode, SAMMode, VIEWERMode, VIEWMode
from pcst.core import (
    Annotation3D,
    AnnotationDocument,
    AnnotationValidationError,
    CoordinateService,
    LoadedVolume,
    validate_annotation_document,
    validate_dataset_directory,
    VolumeGeometry,
)
from pcst.core.geometry import GeometryValidationError
from pcst.path import ANNOTATIONS_PATH, CACHE_PATH, ICONS_PATH
from pcst.scripts.logger import log_debug, log_error, log_info, log_warning
from pcst.ui.MainWindow_ui import Ui_MainWindow
from pcst.widgets.FileDocker import FileDocker
from pcst.widgets.BoxAnnotationController import BoxAnnotationController
from pcst.widgets.BoxAnnotationPanel import BoxAnnotationPanel
from pcst.widgets.ImageDocker import ImageDocker
from pcst.widgets.InfoDocker import InfoDocker
from pcst.widgets.LoadDialog import LoadDialog
from pcst.widgets.SegmentDocker import SegmentDocker
from pcst.widgets.ShortcutDialog import ShortcutDialog
from pcst.widgets.commands import SegChangeCommand
from pcst.widgets.theme import ThemeManager
from pcst.widgets.Viewer3d import Viewer3D
from pcst.widgets.ViewerBase import ViewerBase
from pcst.widgets.WorkerThread import (
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
        self.setWindowIcon(QIcon(str(ICONS_PATH / "logo.ico")))
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
        # 三个二维视图分别维护层号；数据始终保留为 SimpleITK 的 [z, y, x]。
        self.layers: dict[VIEWMode, int] = {
            VIEWMode.AXIAL: 0,
            VIEWMode.SAGITTAL: 0,
            VIEWMode.CORONAL: 0,
        }
        # 保留当前活动视图信息，兼容原有鼠标交互代码。
        self.layer: int = 0
        self.num = None
        # canonical crosshair 坐标使用 IJK；旧代码通过 property 访问
        # ``crosshair_voxel_xyz`` 时仍得到同一份值，避免出现第二套状态。
        self.crosshair_ijk: list[int] | None = None

        # 坐标参数
        self.y_star: int = 0
        self.y_end: int = 0
        self.x_star: int = 0
        self.x_end: int = 0

        self.radius: int = 5

        self.pet_spacing = (0, 0, 0)
        self.pet_shape = (0, 0, 0)
        self.image_geometry: VolumeGeometry | None = None
        self.coordinate_service: CoordinateService | None = None
        self.annotation_document: AnnotationDocument | None = None
        self.annotation_path: Path | None = None
        self.annotation_dirty = False
        self.current_image_file: Path | None = None
        self.current_case_id: str = ""
        self.current_data_id: str = ""
        self._annotation_save_timer: QTimer | None = None
        self._annotation_save_blocked = False

        # 图像数据
        self.ct: np.ndarray = np.array([])
        self.pet: np.ndarray = np.array([])
        self.seg: np.ndarray = np.array([])
        # 撤销前快照（当前方位的当前层）
        self._seg_before_edit: np.ndarray | None = None
        self._seg_edit_context: tuple[VIEWMode, int] | None = None

        # 状态标志
        self.load_mode = LOADMode.UNLOAD
        self.view_mode = VIEWMode.AXIAL
        self._active_viewer = None

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

        self.setWindowTitle("PCST")

        self.init_ui()
        self.config()
        self.init_shortcuts()
        self.init_connectAction()

    def init_shortcuts(self):
        """从配置初始化快捷键"""
        # 对旧配置做增量合并，确保新增 btn_box 等工具在已有配置中也有默认快捷键。
        shortcuts = {**DEFAULT_SHORTCUTS, **(self._config.shortcuts or {})}

        legacy_targets = {
            "aim_atn": "btn_aim",
            "move_atn": "btn_move",
            "win_atn": "btn_win",
            "paint_atn": "btn_paint",
            "eraser_atn": "btn_eraser",
            "sam_atn": "btn_sam",
        }
        normalized_shortcuts = {}
        for target_name, key_sequence in shortcuts.items():
            target_name = legacy_targets.get(target_name, target_name)
            if hasattr(self, target_name):
                target = getattr(self, target_name)
                target.setShortcut(key_sequence)
                normalized_shortcuts[target_name] = key_sequence

        if not self._config.shortcuts:
            self._config.shortcuts = DEFAULT_SHORTCUTS.copy()
        elif normalized_shortcuts:
            # 自动兼容旧版 QAction 快捷键键名，后续保存时使用新按钮键名。
            self._config.shortcuts = normalized_shortcuts

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
        self.btn_aim.setIcon(QIcon(str(ICONS_PATH / theme / "cursor.png")))
        self.btn_move.setIcon(QIcon(str(ICONS_PATH / theme / "move.png")))
        self.btn_win.setIcon(QIcon(str(ICONS_PATH / theme / "contrast.png")))
        self.btn_paint.setIcon(QIcon(str(ICONS_PATH / theme / "paint.png")))
        self.btn_eraser.setIcon(QIcon(str(ICONS_PATH / theme / "eraser.png")))
        self.redo_atn.setIcon(QIcon(str(ICONS_PATH / theme / "redo.png")))

        self.btn_sam.setIcon(QIcon(str(ICONS_PATH / theme / "meta.png")))
        self.btn_box.setIcon(QIcon(str(ICONS_PATH / theme / "frame.png")))
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

        self.viewer_bases: dict[VIEWMode, ViewerBase] = {}
        self.viewers = {}
        frame_modes = (
            (self.frame_H, VIEWMode.AXIAL),
            (self.frame_S, VIEWMode.SAGITTAL),
            (self.frame_G, VIEWMode.CORONAL),
        )
        for frame, view_mode in frame_modes:
            viewer_base = ViewerBase(frame, self, view_mode)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame_layout.setSpacing(0)
            frame_layout.addWidget(viewer_base)
            self.viewer_bases[view_mode] = viewer_base
            self.viewers[view_mode] = viewer_base.viewer

        # 兼容少量仍以 self.viewer 读取 spacing 的外围代码。
        self.viewer = self.viewers[VIEWMode.AXIAL]
        self._active_viewer = self.viewer

        self.viewer_3d = Viewer3D(self.frame_3d)
        view_3d_layout = QVBoxLayout(self.frame_3d)
        view_3d_layout.setContentsMargins(0, 0, 0, 0)
        view_3d_layout.setSpacing(0)
        view_3d_layout.addWidget(self.viewer_3d)

        self.info_setting = InfoDocker(self, self)
        info_layout = self.InfoSetting.layout()
        if info_layout:
            info_layout.addWidget(self.info_setting)

        self._vtk_actor_cache = None
        self._seg_cache_hash = None
        self._built_thread = None
        self._pending_3d_refresh = False
        self._volume_generation = 0
        self._requested_3d_token = None
        self._refresh_3d_timer = QTimer(self)
        self._refresh_3d_timer.setSingleShot(True)
        self._refresh_3d_timer.timeout.connect(self.view_3d_built)

        self.box_controller = BoxAnnotationController(self)
        self.box_annotation_panel = BoxAnnotationPanel(self, self.box_controller, self.segment_setting)
        # 面板插入现有标注设置滚动区，保留原有标签/SAM 控件布局。
        self.segment_setting.verticalLayout_2.insertWidget(
            max(0, self.segment_setting.verticalLayout_2.count() - 1),
            self.box_annotation_panel,
        )
        self.box_controller.boxes_changed.connect(self._on_boxes_changed)
        self.box_controller.status_message.connect(self._show_box_status)
        self.box_controller.selection_changed.connect(self._on_box_selection_changed)
        self._annotation_save_timer = QTimer(self)
        self._annotation_save_timer.setSingleShot(True)
        self._annotation_save_timer.setInterval(500)
        self._annotation_save_timer.timeout.connect(self._save_annotation_document)
        for viewer in self.viewers.values():
            self.box_controller.attach_viewer(viewer)

        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)
        self.mode_buttons = {
            VIEWERMode.AIM: self.btn_aim,
            VIEWERMode.MOVE: self.btn_move,
            VIEWERMode.WIN: self.btn_win,
            VIEWERMode.PAINT: self.btn_paint,
            VIEWERMode.ERASER: self.btn_eraser,
            VIEWERMode.SAM: self.btn_sam,
            VIEWERMode.BOX_3D: self.btn_box,
        }
        for button in self.mode_buttons.values():
            self.mode_button_group.addButton(button)
        self.btn_aim.setChecked(True)
        for viewer in self.viewers.values():
            viewer.mode = VIEWERMode.AIM

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

        for viewer_mode, button in self.mode_buttons.items():
            button.clicked.connect(
                lambda _checked=False, mode=viewer_mode: self._set_mode(mode)
            )

        self.open_action.triggered.connect(self.load_slot)
        self.add_action.triggered.connect(self.load_Seg_slot)
        self.export_boxes_action.triggered.connect(self.export_boxes_slot)
        self.validate_boxes_action.triggered.connect(self.validate_boxes_slot)
        self.validate_dataset_action.triggered.connect(self.validate_dataset_slot)
        self.save_action.triggered.connect(self.save_slot)
        self.exit_action.triggered.connect(self.close)
        self.crossline_action.triggered.connect(self.crossline_slot)
        self.direction_action.triggered.connect(self.direction_slot)
        self.information_action.triggered.connect(self.information_slot)
        self.actiongithub.triggered.connect(self.open_github_page)
        self.actionversion.triggered.connect(self.show_version_info)

        self.file_action.triggered.connect(self.toggle_toolBar_file)

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

        self.boxCT.clicked.connect(self.update_all)
        self.boxPET.clicked.connect(self.update_all)
        self.boxSeg.clicked.connect(self.update_all)

        for view_mode, viewer_base in self.viewer_bases.items():
            viewer_base.layer_changed.connect(self.on_view_layer_changed)
            viewer_base.screenshot_requested.connect(self.screen_shot)
            viewer_base.viewer.Sam_Signal.connect(
                lambda data, mode=view_mode: self.operation(mode, data)
            )
            viewer_base.viewer.Mode_Signal.connect(self._update_mode_from_buttons)
            viewer_base.viewer.view_state_changed.connect(
                lambda state, source=viewer_base.viewer: self._sync_view_state(source, state)
            )

        self.viewer_3d.refresh_requested.connect(self.refresh_slot)
        self.viewer_3d.reset_requested.connect(self.reset_slot)
        self.viewer_3d.annotation_selected.connect(self._on_3d_annotation_selected)

        # 主题切换信号槽
        self.dark_action.triggered.connect(lambda: self.change_theme("dark"))
        self.light_action.triggered.connect(lambda: self.change_theme("light"))

        # 快捷键设置
        self.shortcut_action.triggered.connect(self.show_shortcut_dialog)

        for viewer in self.viewers.values():
            self.file_Setting.file_name.connect(viewer.patient_name_change)

    def _has_volume(self):
        return hasattr(self, "ct") and self.ct.size > 0

    @property
    def crosshair_voxel_xyz(self):
        """旧 API 兼容别名；返回的三元组语义实际是 IJK。"""

        return self.crosshair_ijk

    @crosshair_voxel_xyz.setter
    def crosshair_voxel_xyz(self, value):
        self.crosshair_ijk = None if value is None else [int(item) for item in value]

    def _clamp_index(self, value, size):
        if size <= 0:
            return 0
        return max(0, min(int(round(value)), size - 1))

    def _volume_shape_xyz(self):
        if not self._has_volume():
            return (0, 0, 0)

        size_z, size_y, size_x = self.ct.shape
        return (size_x, size_y, size_z)

    def _volume_size_ijk(self) -> tuple[int, int, int]:
        """返回 canonical image size，顺序固定为 I, J, K。"""

        if self.image_geometry is not None:
            return self.image_geometry.size_ijk
        if not self._has_volume():
            return (0, 0, 0)
        return (int(self.ct.shape[2]), int(self.ct.shape[1]), int(self.ct.shape[0]))

    def _view_layer_count(self, view_mode: VIEWMode) -> int:
        if not self._has_volume():
            return 0
        if view_mode == VIEWMode.AXIAL:
            return self.ct.shape[0]
        if view_mode == VIEWMode.SAGITTAL:
            return self.ct.shape[2]
        if view_mode == VIEWMode.CORONAL:
            return self.ct.shape[1]
        return 0

    def _get_volume_slice(
        self, volume: np.ndarray, view_mode: VIEWMode, layer: int
    ) -> np.ndarray:
        if view_mode == VIEWMode.AXIAL:
            return volume[layer, :, :]
        if view_mode == VIEWMode.SAGITTAL:
            return volume[:, :, layer]
        if view_mode == VIEWMode.CORONAL:
            return volume[:, layer, :]
        raise ValueError(f"Unsupported view mode: {view_mode}")

    def _set_volume_slice(
        self,
        volume: np.ndarray,
        view_mode: VIEWMode,
        layer: int,
        slice_data: np.ndarray,
    ) -> None:
        if view_mode == VIEWMode.AXIAL:
            volume[layer, :, :] = slice_data
        elif view_mode == VIEWMode.SAGITTAL:
            volume[:, :, layer] = slice_data
        elif view_mode == VIEWMode.CORONAL:
            volume[:, layer, :] = slice_data
        else:
            raise ValueError(f"Unsupported view mode: {view_mode}")

    def _clamp_voxel_xyz(self, voxel_xyz):
        # 旧方法名保留兼容；内部顺序是 IJK，而非 patient/world XYZ。
        return self._clamp_ijk(voxel_xyz)

    def _clamp_ijk(self, ijk) -> list[int]:
        size_i, size_j, size_k = self._volume_size_ijk()
        i, j, k = ijk
        return [
            self._clamp_index(i, size_i),
            self._clamp_index(j, size_j),
            self._clamp_index(k, size_k),
        ]

    def slice_point_to_ijk(self, image_u, image_v, layer, view_mode=None):
        """将 viewer 图像坐标转换为 canonical IJK。"""

        view_mode = view_mode or self.view_mode
        if self.coordinate_service is None:
            raise GeometryValidationError("image geometry is not loaded")
        return list(
            self.coordinate_service.slice_to_ijk(
                view_mode, image_u, image_v, layer
            )
        )

    def ijk_to_slice_point(self, ijk, view_mode=None):
        """将 canonical IJK 转换为 viewer 图像坐标 (u, v, layer)。"""

        view_mode = view_mode or self.view_mode
        if self.coordinate_service is None:
            raise GeometryValidationError("image geometry is not loaded")
        return self.coordinate_service.ijk_to_slice(view_mode, ijk)

    def direction_labels(self, view_mode: VIEWMode) -> tuple[str, str, str, str]:
        """返回当前视图左、右、上、下的 LPS 方位标记。

        ``ImageViewer`` 的像素变换保持历史交互方向：横向坐标递增向右，
        轴向/冠状面的纵向坐标递增向下，矢状面的纵向坐标递减向下。因此
        方位标记必须由 IJK→LPS direction 动态推导，不能假设 direction 是
        identity；斜位采集时使用方向向量的主导 L/P/S 分量作为可读标签。
        """

        fallback = {
            VIEWMode.AXIAL: ("R", "L", "A", "P"),
            VIEWMode.SAGITTAL: ("A", "P", "S", "I"),
            VIEWMode.CORONAL: ("R", "L", "S", "I"),
        }
        if self.image_geometry is None or self.coordinate_service is None or view_mode not in fallback:
            return fallback.get(view_mode, ("", "", "", ""))

        try:
            return self.coordinate_service.orientation_labels(view_mode)
        except (GeometryValidationError, KeyError, ValueError):
            return fallback.get(view_mode, ("", "", "", ""))

    def slice_point_to_voxel_xyz(self, image_x, image_y, layer, view_mode=None):
        """兼容旧调用；等价于 :meth:`slice_point_to_ijk`。"""

        return self.slice_point_to_ijk(image_x, image_y, layer, view_mode)

    def voxel_xyz_to_slice_point(self, voxel_xyz, view_mode=None):
        """兼容旧调用；等价于 :meth:`ijk_to_slice_point`。"""

        return self.ijk_to_slice_point(voxel_xyz, view_mode)

    def _set_layer_controls(self, view_mode: VIEWMode, layer: int):
        if not self._has_volume():
            return

        layer = self._clamp_index(layer, self._view_layer_count(view_mode))
        self.layers[view_mode] = layer
        self.viewer_bases[view_mode].set_layer(layer)
        if self.view_mode == view_mode:
            self.layer = layer

    def _sync_layers_from_crosshair(self):
        if self.crosshair_ijk is None:
            return
        for view_mode in self.viewer_bases:
            _, _, layer = self.ijk_to_slice_point(
                self.crosshair_ijk, view_mode
            )
            self._set_layer_controls(view_mode, layer)

    def on_view_layer_changed(self, view_mode: VIEWMode, layer: int):
        if self.load_mode == LOADMode.UNLOAD or not self._has_volume():
            return

        viewer = self.viewers[view_mode]
        self._active_viewer = viewer
        self.view_mode = view_mode
        layer = self._clamp_index(layer, self._view_layer_count(view_mode))

        if self.crosshair_ijk is None:
            size_i, size_j, size_k = self._volume_size_ijk()
            self.crosshair_ijk = [size_i // 2, size_j // 2, size_k // 2]

        voxel = list(self.crosshair_ijk)
        if view_mode == VIEWMode.AXIAL:
            voxel[2] = layer
        elif view_mode == VIEWMode.SAGITTAL:
            voxel[0] = layer
        elif view_mode == VIEWMode.CORONAL:
            voxel[1] = layer
        self.crosshair_ijk = self._clamp_ijk(voxel)
        self._show_voxel_coordinate_status()
        self._sync_layers_from_crosshair()
        self._seg_before_edit = None
        self._seg_edit_context = None
        self.num = None
        self.update_all()

    def update_crosshair_from_slice_point(self, viewer, point):
        if self.load_mode == LOADMode.UNLOAD or not self._has_volume():
            return

        view_mode = viewer.view_mode
        self._active_viewer = viewer
        self.view_mode = view_mode
        layer = self.layers[view_mode]
        self.crosshair_ijk = self.slice_point_to_ijk(
            point.x(),
            point.y(),
            layer,
            view_mode,
        )
        self._show_voxel_coordinate_status()
        self._sync_layers_from_crosshair()
        self.update_all()

    def _show_voxel_coordinate_status(self) -> None:
        """在状态栏显示当前 voxel 的 IJK 和动态计算的 LPS(mm)。"""

        if self.crosshair_ijk is None or self.coordinate_service is None:
            return
        lps = self.coordinate_service.ijk_to_lps(self.crosshair_ijk)
        self._show_box_status(
            f"IJK: {list(self.crosshair_ijk)}    "
            f"LPS: {tuple(round(value, 3) for value in lps)} mm"
        )

    def sync_crosshair_overlay(self):
        if not hasattr(self, "viewers"):
            return

        if self.crosshair_ijk is None or not self._has_volume():
            for viewer in self.viewers.values():
                viewer.clear_crosshair_point()
            return

        for view_mode, viewer in self.viewers.items():
            image_x, image_y, _ = self.ijk_to_slice_point(
                self.crosshair_ijk, view_mode
            )
            viewer.set_crosshair_point(image_x, image_y)

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

    def screen_shot(self, viewer_base=None):
        if self.load_mode != LOADMode.UNLOAD:
            from datetime import datetime

            if viewer_base is None:
                view_mode = getattr(
                    self._active_viewer, "view_mode", VIEWMode.AXIAL
                )
                viewer_base = self.viewer_bases[view_mode]
            view_mode = viewer_base.view_mode
            view_name = {
                VIEWMode.AXIAL: "H",
                VIEWMode.SAGITTAL: "S",
                VIEWMode.CORONAL: "G",
            }[view_mode]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Screenshot_{view_name}_{timestamp}.png"
            save_path = QFileDialog.getSaveFileName(
                self, "保存图片", filename, "PNG (*.png)"
            )[0]

            viewport = viewer_base.viewer.viewport()
            pixmap = viewport.grab()
            if save_path:
                pixmap.save(save_path)

    def change_slot(self, mode):
        """兼容旧调用：四视图模式下仅切换当前活动视图。"""
        if self.load_mode != LOADMode.UNLOAD and mode in self.viewers:
            self.view_mode = mode
            self._active_viewer = self.viewers[mode]
            self.layer = self.layers[mode]

    def reset_slot(self, view_mode=None):
        """复位二维位面，并复位已经加载的 3D 相机。"""
        if self.load_mode != LOADMode.UNLOAD:
            target_modes = (
                [view_mode] if view_mode in self.viewers else list(self.viewers)
            )
            for mode in target_modes:
                viewer = self.viewers[mode]
                viewer.fitInView(
                    viewer.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio
                )
                viewer.remember_fit_transform()
            self.sync_crosshair_overlay()

        # Viewer3D 内部会在尚未点击刷新时安全地忽略此操作，不会触发 VTK 加载。
        self.viewer_3d.reset_camera()

    def refresh_slot(self):
        """刷新常驻 3D 视图。"""
        self._pending_3d_refresh = False
        self.view_3d_built(force=True)
        log_info("刷新3D视图")

    def _sync_view_state(self, source_viewer, state) -> None:
        """Synchronize pan/zoom across the three 2D views.

        The center is normalized in each image's own pixel rectangle, so the
        differing axial/sagittal/coronal dimensions do not cause an axis swap.
        ``apply_view_state`` never re-emits the signal, preventing feedback
        loops while preserving each view's fitted physical pixel spacing.
        """

        if not isinstance(state, dict):
            return
        for viewer in self.viewers.values():
            if viewer is source_viewer:
                continue
            viewer.apply_view_state(state)

    def _on_3d_annotation_selected(self, annotation_id: str) -> None:
        if hasattr(self, "box_controller"):
            self.box_controller.select(str(annotation_id), center=True)

    def change_theme(self, theme):
        """切换主题"""
        self._config.theme = theme

        config_manager = ConfigManager()
        config_manager.save(self._config)

        ThemeManager.set_theme(theme)

        self.load_atn.setIcon(QIcon(str(ICONS_PATH / theme / "load.png")))
        self.add_atn.setIcon(QIcon(str(ICONS_PATH / theme / "add.png")))
        self.save_atn.setIcon(QIcon(str(ICONS_PATH / theme / "save.png")))
        self.btn_aim.setIcon(QIcon(str(ICONS_PATH / theme / "cursor.png")))
        self.btn_move.setIcon(QIcon(str(ICONS_PATH / theme / "move.png")))
        self.btn_win.setIcon(QIcon(str(ICONS_PATH / theme / "contrast.png")))
        self.btn_paint.setIcon(QIcon(str(ICONS_PATH / theme / "paint.png")))
        self.btn_eraser.setIcon(QIcon(str(ICONS_PATH / theme / "eraser.png")))
        self.redo_atn.setIcon(QIcon(str(ICONS_PATH / theme / "redo.png")))

        self.btn_sam.setIcon(QIcon(str(ICONS_PATH / theme / "meta.png")))
        self.btn_box.setIcon(QIcon(str(ICONS_PATH / theme / "frame.png")))
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
        for viewer in self.viewers.values():
            viewer.setCursor(Qt.CursorShape.ArrowCursor)
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
                self.seg = np.zeros_like(self.seg)
                for viewer in self.viewers.values():
                    viewer.input_box = []
                self.undo_stack.clear()
                self.update_all()
                self.request_3d_refresh()

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
                seg_geometry = VolumeGeometry.from_sitk(seg)
                seg_data = np.asarray(sitk.GetArrayFromImage(seg), dtype=np.uint16)
                geometry_matches = self.image_geometry is None or seg_geometry.almost_equal(
                    self.image_geometry
                )
                if seg_data.shape == self.ct.shape and geometry_matches:
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
                    label_mapping = {}
                    original_seg = seg_data.copy()
                    for i, (old_id, label_info) in enumerate(sorted_labels, 1):
                        new_labels[str(i)] = label_info
                        label_mapping[int(old_id)] = i
                        # 更新seg数组中的标签ID
                        if seg_data.size > 0:
                            seg_data[original_seg == int(old_id)] = i
                    # 替换为新的标签配置
                    self._config.label = new_labels
                    if hasattr(self, "box_controller"):
                        self.box_controller.remap_class_ids(label_mapping)
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

                    self.undo_stack.clear()
                    self.update_all()
                    self.request_3d_refresh()
                    log_info(f"分割文件加载成功: {seg_file}")
                else:
                    log_error(
                        f"分割文件形状不匹配: {seg_data.shape} vs {self.pet.shape}"
                    )
                    QMessageBox.warning(
                        self,
                        "警告！",
                        "输入标签与原始数据的尺寸或图像几何不符，请检查标注是否正确！",
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

    # ------------------------------------------------------------------
    # Canonical 3D annotation document lifecycle
    # ------------------------------------------------------------------
    def _annotation_classes(self) -> list[dict[str, object]]:
        """将当前标签配置转换为 annotation 文档中的 class 表。

        segmentation 使用的标签编号与框的 ``class_id`` 保持一致；框本身
        不写入 ``seg``，因此重叠框、相同几何的不同类别都可以独立保存。
        """

        labels = getattr(self._config, "label", {}) or {}
        result: list[dict[str, object]] = []
        for label_id, label_info in sorted(labels.items(), key=lambda item: int(item[0])):
            try:
                class_id = int(label_id)
            except (TypeError, ValueError):
                continue
            if not isinstance(label_info, dict):
                label_info = {}
            result.append(
                {
                    "id": class_id,
                    "name": str(label_info.get("name", f"Label {class_id}")),
                }
            )
        return result

    def _make_case_id(self) -> str:
        """返回可用于文件名的稳定病例 ID。"""

        raw = str(
            self.patient_id or getattr(self, "current_data_id", "") or "case"
        ).strip()
        # 不把用户的病例名改成 Python/世界坐标意义上的 xyz；这里只做文件名清理。
        case_id = re.sub(r"[^0-9A-Za-z_.-]+", "_", raw).strip("._-")
        return case_id or "case"

    def _annotation_path_for_case(self, case_id: str) -> Path:
        return Path(ANNOTATIONS_PATH) / f"{case_id}.boxes.json"

    def _new_annotation_document(self) -> AnnotationDocument | None:
        if self.image_geometry is None:
            return None
        # Worker/unit-test callers may provide an in-memory volume without a
        # source path; the canonical schema still requires a non-empty image
        # reference, so use a clearly marked placeholder rather than creating
        # an invalid document that fails as soon as the first box is drawn.
        source_file = str(self.current_image_file) if self.current_image_file else ""
        if not source_file or source_file == ".":
            source_file = f"{self.current_case_id or 'case'}.nii.gz"
        image_file = source_file
        return AnnotationDocument(
            case_id=self.current_case_id or self._make_case_id(),
            image_file=image_file,
            image_geometry=self.image_geometry,
            classes=self._annotation_classes(),
        )

    def _annotation_warning(self, title: str, message: str) -> None:
        """显示可读错误；无 GUI（如单元测试/导入检查）时只记录日志。"""

        log_warning(message)
        if self.isVisible():
            QMessageBox.warning(self, title, message, QMessageBox.StandardButton.Ok)

    def _show_box_status(self, message: str) -> None:
        if hasattr(self, "statusbar"):
            self.statusbar.showMessage(message)

    def _sync_annotation_classes(self) -> None:
        """同步标签名称/新增类别，但不重写 annotation 的几何真值。"""

        if self.annotation_document is None:
            return
        classes = self._annotation_classes()
        configured_ids = {int(item["id"]) for item in classes}
        # 已有文件中可能包含当前标签配置尚未定义的类别（例如 class_id=0）。
        # 保留这些 class 定义，避免加载/保存过程中丢失原始 annotation。
        for item in self.annotation_document.classes:
            class_id = int(item["id"])
            if class_id not in configured_ids:
                classes.append({"id": class_id, "name": str(item["name"])})
                configured_ids.add(class_id)
        classes.sort(key=lambda item: int(item["id"]))
        self.annotation_document.classes = classes
        self.annotation_document._validate_classes()
        self.annotation_document._validate_annotations()

    def _clear_annotation_document(self) -> None:
        if self._annotation_save_timer is not None:
            self._annotation_save_timer.stop()
        self.annotation_document = None
        self.annotation_path = None
        self.annotation_dirty = False
        self._annotation_save_blocked = False
        if hasattr(self, "box_controller"):
            self.box_controller.set_document(None)
        if hasattr(self, "box_annotation_panel"):
            self.box_annotation_panel.refresh()

    def _load_annotation_document(self) -> None:
        """为当前病例创建或加载 canonical ``*.boxes.json`` 文档。"""

        self._clear_annotation_document()
        if self.image_geometry is None or self.load_mode == LOADMode.UNLOAD:
            return

        self.current_case_id = self.current_case_id or self._make_case_id()
        target = self._annotation_path_for_case(self.current_case_id)
        document: AnnotationDocument | None = None

        if target.exists():
            try:
                loaded = AnnotationDocument.load(target)
                if not loaded.image_geometry.almost_equal(self.image_geometry):
                    # 几何不一致时绝不静默覆盖旧文件；用户可通过“导出框标注”
                    # 明确选择新文件名。
                    self._annotation_warning(
                        "框标注几何不匹配",
                        f"{target.name} 的 size/spacing/origin/direction 与当前图像不一致，"
                        "已创建空白标注文档；为避免覆盖原文件，自动保存暂时停用。",
                    )
                    document = self._new_annotation_document()
                    self.annotation_path = None
                    self._annotation_save_blocked = True
                else:
                    document = loaded
                    self.annotation_path = target
            except AnnotationValidationError as exc:
                self._annotation_warning(
                    "框标注文件无效",
                    f"无法加载 {target.name}：{exc}\n已创建空白标注文档。",
                )
                document = self._new_annotation_document()
                self.annotation_path = None
                self._annotation_save_blocked = True
        else:
            document = self._new_annotation_document()
            self.annotation_path = target

        self.annotation_document = document
        self.annotation_dirty = False
        if self.annotation_document is not None:
            try:
                self.box_controller.set_document(self.annotation_document)
                self.box_annotation_panel.refresh()
            except Exception as exc:
                # 控制器接线失败不能让图像加载失败，但应留下可诊断日志。
                log_error(f"初始化框标注控制器失败: {exc}")
            if self._annotation_save_blocked:
                self._show_box_status("当前图像几何与已有框文件不匹配，自动保存已停用；请使用导出另存")

    def _on_boxes_changed(self) -> None:
        if self.annotation_document is None:
            return
        try:
            self._sync_annotation_classes()
        except (AnnotationValidationError, ValueError) as exc:
            self._annotation_warning("框标注校验失败", str(exc))
            return
        self.annotation_dirty = True
        if getattr(self.viewer_3d, "is_initialized", False):
            self.request_3d_refresh()
        if self._annotation_save_timer is not None and not self._annotation_save_blocked:
            self._annotation_save_timer.start()

    def _on_box_selection_changed(self, annotation_id) -> None:
        """选择变化只影响 3D 高亮，不改变 annotation 几何。"""

        if annotation_id is not None and self.annotation_document is not None:
            try:
                annotation = self.annotation_document.get(str(annotation_id))
                if self.coordinate_service is not None:
                    start_lps = self.coordinate_service.ijk_to_lps(
                        annotation.geometry.min_ijk
                    )
                    end_lps = self.coordinate_service.ijk_to_lps(
                        tuple(value - 1 for value in annotation.geometry.max_ijk_exclusive)
                    )
                    self._show_box_status(
                        f"{annotation.id} | IJK {list(annotation.geometry.min_ijk)} → "
                        f"{list(annotation.geometry.max_ijk_exclusive)} (exclusive) | "
                        f"LPS start {tuple(round(value, 3) for value in start_lps)} mm, "
                        f"end {tuple(round(value, 3) for value in end_lps)} mm"
                    )
            except KeyError:
                pass
        if getattr(self.viewer_3d, "is_initialized", False):
            self.request_3d_refresh()

    def _save_annotation_document(self) -> bool:
        """将当前文档原子写入 canonical 路径。"""

        if self.annotation_document is None or not self.annotation_dirty:
            return True
        if self._annotation_save_blocked or self.annotation_path is None:
            return False
        try:
            self._sync_annotation_classes()
            self.annotation_document.save_atomic(self.annotation_path)
            self.annotation_dirty = False
            self._show_box_status(f"框标注已自动保存：{self.annotation_path.name}")
            return True
        except (AnnotationValidationError, OSError, ValueError) as exc:
            self._annotation_warning("框标注保存失败", str(exc))
            return False

    def _flush_annotation_save(self) -> bool:
        if self._annotation_save_timer is not None:
            self._annotation_save_timer.stop()
        return self._save_annotation_document()

    def export_boxes_slot(self) -> None:
        """文件菜单：显式导出当前病例的 canonical 框标注 JSON。"""

        if self.annotation_document is None:
            self._annotation_warning("无法导出", "请先加载图像数据。")
            return

        default_name = f"{self.current_case_id or self._make_case_id()}.boxes.json"
        default_path = self.annotation_path or (Path.cwd() / default_name)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出框标注",
            str(default_path),
            "JSON (*.json)",
        )
        if not file_path:
            return
        target = Path(file_path)
        if target.suffix.lower() != ".json":
            target = target.with_suffix(target.suffix + ".json" if target.suffix else ".json")
        try:
            self._sync_annotation_classes()
            self.annotation_document.save_atomic(target)
            if self.annotation_path is None or self._annotation_save_blocked:
                # 用户已明确选择了安全的新路径，可将其作为后续自动保存路径。
                self.annotation_path = target
                self._annotation_save_blocked = False
            if self.annotation_path is not None and target.resolve() == self.annotation_path.resolve():
                self.annotation_dirty = False
            self._show_box_status(f"框标注已导出：{target}")
            log_info(f"导出框标注: {target}")
        except (AnnotationValidationError, OSError, ValueError) as exc:
            self._annotation_warning("框标注导出失败", str(exc))

    def validate_boxes_slot(self) -> None:
        """文件菜单：执行当前文档的结构、几何和文件完整性检查。"""

        issues: list[str] = []
        document = self.annotation_document
        overlap_pairs = 0
        if document is None:
            issues.append("尚未加载图像或框标注文档。")
        else:
            # The shared validator keeps domain checks and overlap statistics
            # available to non-UI callers as well; overlap itself remains a
            # legal state and is reported only as a statistic.
            report = validate_annotation_document(document)
            overlap_pairs = report.overlap_pairs
            issues.extend(report.issues)
            if self.image_geometry is not None and not document.image_geometry.almost_equal(
                self.image_geometry
            ):
                issues.append("annotation 文件中的图像 geometry 与当前图像不匹配。")
            if self.annotation_path is not None and not self.annotation_path.exists():
                # 未保存的新文档不是错误，只作为提示。
                issues.append(f"框标注文件尚未写入磁盘：{self.annotation_path.name}")
            image_file = Path(document.image_file) if document.image_file else None
            if (
                image_file is not None
                and not image_file.is_absolute()
                and self.annotation_path is not None
            ):
                image_file = self.annotation_path.parent / image_file
            if image_file is not None and not image_file.exists():
                issues.append(f"图像文件不存在：{image_file}")
            elif (
                image_file is not None
                and image_file.is_file()
                and image_file.name.lower().endswith((".nii", ".nii.gz"))
            ):
                # NIfTI 的 geometry 是当前预处理流程使用的 LPS geometry；
                # 重新执行同一方向规范化后与文档比较，避免只检查文件存在。
                try:
                    actual_image = sitk.DICOMOrient(
                        sitk.ReadImage(str(image_file)), "LPS"
                    )
                    actual_geometry = VolumeGeometry.from_sitk(actual_image)
                    if not actual_geometry.almost_equal(document.image_geometry):
                        issues.append("annotation 文件中的 image geometry 与实际 NIfTI 元数据不匹配。")
                except Exception as exc:
                    issues.append(f"无法读取图像 geometry：{exc}")

        if issues:
            message = "数据校验发现问题：\n\n" + "\n".join(f"• {issue}" for issue in issues)
            self._annotation_warning("框标注校验", message)
        else:
            count = len(document.annotations) if document is not None else 0
            QMessageBox.information(
                self,
                "框标注校验",
                f"校验通过：{count} 个 annotation。\n"
                f"检测到 {overlap_pairs} 对重叠框（重叠属于合法状态）。",
            )

    def validate_dataset_slot(self) -> None:
        """校验一个 Dataset/目录下的 manifest 和全部病例框文件。"""

        directory = QFileDialog.getExistingDirectory(
            self, "选择数据集目录", str(Path.cwd())
        )
        if not directory:
            return
        report = validate_dataset_directory(
            directory, check_image_geometry=True, orient_lps=True
        )
        summary = (
            f"病例数：{report.case_count}\n"
            f"annotation 数：{report.annotation_count}\n"
            f"重叠框对数：{report.overlap_pairs}（合法）"
        )
        if report.valid:
            QMessageBox.information(self, "数据集校验", "校验通过。\n\n" + summary)
        else:
            details = "\n".join(f"• {issue}" for issue in report.issues)
            self._annotation_warning(
                "数据集校验发现问题", details + "\n\n" + summary
            )

    def on_files_selected(
        self, pet_file: Path, ct_file: Path, file_type: str, data_id: str = ""
    ):
        """处理文件选择"""
        log_info(f"选择文件 - PET: {pet_file}, CT: {ct_file}, 类型: {file_type}")
        # 新病例开始异步加载前，先完成旧病例的 debounce 保存并解除控制器绑定。
        if not self._flush_annotation_save() and self.annotation_dirty:
            self._annotation_warning(
                "无法切换病例",
                "当前三维框标注尚未成功保存。请先使用“导出框标注”另存 JSON，"
                "或修复保存路径/图像几何后再切换病例。",
            )
            return
        self._clear_annotation_document()
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
        self.current_case_id = self._make_case_id()
        self.current_image_file = Path(ct_file)
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
        result,
        pet_data: np.ndarray | None = None,
        ct_spacing: tuple | None = None,
        pet_spacing: tuple | None = None,
        pet_shape: tuple | None = None,
        patient_info=None,
    ):
        """数据加载完成后的处理"""
        # 让仍在后台运行的旧 3D 重建结果失效，避免切换病例后旧 mesh
        # 被异步回调重新放进当前渲染器。
        self._volume_generation += 1
        self._requested_3d_token = None
        self._pending_3d_refresh = False
        self.load_mode = LOADMode.RELOAD

        if isinstance(result, LoadedVolume):
            ct_data = result.ct_data
            pet_data = result.pet_data
            self.image_geometry = result.ct_geometry
            self.coordinate_service = CoordinateService(self.image_geometry)
            ct_spacing = result.ct_geometry.spacing_mm
            pet_spacing = (
                result.pet_geometry.spacing_mm
                if result.pet_geometry is not None
                else result.ct_geometry.spacing_mm
            )
            pet_shape = result.pet_shape_kji
            patient_info = result.patient_info
        else:
            # 兼容旧调用方；新 worker 始终传递 LoadedVolume。
            ct_data = np.asarray(result)
            if self.image_geometry is None:
                fallback_spacing = tuple(ct_spacing or (1.0, 1.0, 1.0))
                self.image_geometry = VolumeGeometry(
                    size_ijk=(ct_data.shape[2], ct_data.shape[1], ct_data.shape[0]),
                    spacing_mm=fallback_spacing,
                    origin_lps_mm=(0.0, 0.0, 0.0),
                    direction_ijk_to_lps=(
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                    ),
                )
                self.coordinate_service = CoordinateService(self.image_geometry)
            pet_data = np.asarray(pet_data) if pet_data is not None else np.array([])
            pet_shape = pet_shape or tuple(int(value) for value in pet_data.shape)
            patient_info = patient_info or {}

        log_info(f"{ct_spacing}, {pet_spacing}, {pet_shape}")
        self.ct_spacing = tuple(ct_spacing or self.image_geometry.spacing_mm)
        for viewer in self.viewers.values():
            viewer.spacing = self.ct_spacing
        self.pet_spacing = tuple(pet_spacing or self.ct_spacing)
        self.pet_shape = tuple(pet_shape or ())

        self.ct = np.asarray(ct_data)
        self.pet = np.asarray(pet_data)
        self.seg = np.zeros(self.ct.shape, dtype=np.uint16)
        self.crosshair_ijk = None
        self.num = None

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
        self.worker_thread.error.connect(self._handle_data_load_error)
        self.worker_thread.start()

    def _load_nifti_files(self, pet_file: Path, ct_file: Path):
        """处理NIfTI文件"""
        self.worker_thread = NiftiWorker(pet_file, ct_file)
        self.worker_thread.finished.connect(self.dialog.close)
        self.worker_thread.finished.connect(self.on_data_loaded)
        self.worker_thread.error.connect(self._handle_data_load_error)
        self.worker_thread.start()

    def _handle_data_load_error(self, message: str) -> None:
        """关闭加载进度框并显示可读错误，避免 worker 失败后界面假死。"""

        self.dialog.close()
        self._annotation_warning("图像加载失败", str(message))

    def setting(self):
        """导入数据后初始化层数"""
        self.seg_file = Path("")
        for viewer in self.viewers.values():
            viewer.information_show = True
            if self.crosshair_ijk is None:
                viewer.position[0] = viewer.width() // 2
                viewer.position[1] = viewer.height() // 2
        if self.load_mode == LOADMode.RELOAD:
            self.crossline_action.setChecked(True)
            for viewer in self.viewers.values():
                viewer.cross_show = True
                viewer.viewport().update()

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

        if self.crosshair_ijk is None:
            size_i, size_j, size_k = self._volume_size_ijk()
            self.crosshair_ijk = [size_i // 2, size_j // 2, size_k // 2]

        for view_mode, viewer_base in self.viewer_bases.items():
            viewer_base.set_layer_range(self._view_layer_count(view_mode) - 1)
        self._sync_layers_from_crosshair()
        self.view_mode = VIEWMode.AXIAL
        self.layer = self.layers[VIEWMode.AXIAL]

        self.update_all()
        self._vtk_actor_cache = None
        self._seg_cache_hash = None
        self._requested_3d_token = None
        self.viewer_3d.clear()
        # 图像 geometry 已确定后再绑定当前病例的框文档；不会在应用启动时触碰 VTK。
        self._load_annotation_document()

    def run_slot(self):
        """运行预测"""
        pass

    def save_slot(self):
        """保存设置"""
        # Ctrl+S/工具栏保存也先落盘框标注；框标注仍可单独通过“导出框标注”另存。
        self._flush_annotation_save()
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
                image = sitk.GetImageFromArray(np.copy(self.seg))
                if self.image_geometry is not None:
                    image.SetSpacing(self.image_geometry.spacing_mm)
                    image.SetOrigin(self.image_geometry.origin_lps_mm)
                    image.SetDirection(self.image_geometry.direction_ijk_to_lps)
                elif hasattr(self, "ct_spacing"):
                    image.SetSpacing(self.ct_spacing)
                self.statusBar().showMessage("已保存文件：" + file_)
                sitk.WriteImage(image, file_)
        else:
            log_warning("无可保存分割图像")
            QMessageBox.warning(
                self, "警告", "无可保存分割图像！", QMessageBox.StandardButton.Ok
            )

    def crossline_slot(self):
        visible = not self.viewer.cross_show
        for viewer in self.viewers.values():
            viewer.cross_show = visible
            viewer.viewport().update()

    def information_slot(self):
        visible = not self.viewer.information_show
        for viewer in self.viewers.values():
            viewer.information_show = visible
            viewer.viewport().update()

    def direction_slot(self):
        visible = not self.viewer.direction_show
        for viewer in self.viewers.values():
            viewer.direction_show = visible
            viewer.viewport().update()

    def _set_mode(self, mode: VIEWERMode):
        if mode != VIEWERMode.BOX_3D and hasattr(self, "box_controller"):
            # 切换到准心/分割等工具时取消尚未提交的框，避免下一次再切回
            # Box 工具时继续使用旧的拖动状态。
            self.box_controller.cancel()
        self.mode_buttons[mode].setChecked(True)
        for viewer in self.viewers.values():
            viewer.mode = mode
        if self.load_mode != LOADMode.UNLOAD:
            self.update_all()

    def _update_mode_from_buttons(self):
        """根据按钮状态更新模式"""
        for mode, button in self.mode_buttons.items():
            if button.isChecked():
                for viewer in self.viewers.values():
                    viewer.mode = mode
                if self.load_mode != LOADMode.UNLOAD:
                    self.update_all()
                return

    def update_all(self):
        """更新-以防按键冲突后仍有残留项"""
        if self.load_mode != LOADMode.UNLOAD:
            for viewer in self.viewers.values():
                viewer.input_box = []
            self.update_image()

    def _handle_sam_error(self, _error_message=""):
        self.dialog.close()
        self.btn_aim.setChecked(True)
        self._set_mode(VIEWERMode.AIM)
        QMessageBox.warning(
            self,
            "警告",
            "SAM分割出现故障！",
            QMessageBox.StandardButton.Ok,
        )

    def operation(self, view_mode: VIEWMode, input_data):
        log_debug(f"SAM操作开始, 方位: {view_mode}, 输入数据: {input_data}")
        if self.SamPredictor is None:
            self._handle_sam_error("SAM 模型尚未加载")
            return
        if hasattr(self, "SamThread") and self.SamThread.isRunning():
            log_warning("已有 SAM 推理任务正在运行")
            return

        self.dialog.setWindowTitle("运行中...")
        self.dialog.show()

        try:
            current_layer = self.layers[view_mode]
            ct_slice = self._get_volume_slice(self.ct, view_mode, current_layer)
            ct_slice = self.normalize(ct_slice, self.ct_ww, self.ct_wl)
            ct_slice = np.stack([ct_slice] * 3, axis=-1)

            pet_slice = self._get_volume_slice(self.pet, view_mode, current_layer)
            pet_slice = self.normalize(pet_slice, self.pet_ww, self.pet_ww / 2)
            pet_slice = cv2.applyColorMap(pet_slice, cv2.COLORMAP_HOT)

            ct_alpha = self.ct_alpha if self.boxCT.isChecked() else 0
            pet_alpha = self.pet_alpha if self.boxPET.isChecked() else 0
            current_slice = cv2.addWeighted(ct_slice, ct_alpha, pet_slice, pet_alpha, 0)
            current_slice = np.ascontiguousarray(current_slice.astype(np.uint8))

            image_key = (
                view_mode,
                current_layer,
                float(self.ct_ww),
                float(self.ct_wl),
                float(self.pet_ww),
                float(ct_alpha),
                float(pet_alpha),
            )
            change_image_mode = image_key != self.num
            if change_image_mode:
                self.num = image_key

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
            old_slice = self._get_volume_slice(
                self.seg, view_mode, current_layer
            ).copy()
            color_label = self.color_label

            # 使用闭包正确捕获old_slice和layer值
            def on_sam_finished(mask):
                self.dialog.close()
                current_seg_slice = self._get_volume_slice(
                    self.seg, view_mode, current_layer
                )
                new_slice = np.where(
                    mask > 0, color_label, current_seg_slice
                )
                self._set_volume_slice(self.seg, view_mode, current_layer, new_slice)
                # 检查变化并提交撤销命令
                if not np.array_equal(old_slice, new_slice):
                    self.commit_seg_change(
                        view_mode, current_layer, old_slice, new_slice, "SAM分割"
                    )
                else:
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
            self.SamThread.error.connect(self._handle_sam_error)
            self.SamThread.start()
        except Exception as e:
            log_error(f"SAM操作失败: {e}")
            self._handle_sam_error()
            return

    def normalize(self, slice, ww, wl):
        window_upper = wl + ww / 2
        window_lower = wl - ww / 2

        slice = np.clip(slice, window_lower, window_upper)
        slice = (slice - window_lower) / (window_upper - window_lower) * 255
        slice = slice.astype(np.uint8)
        return slice

    def update_image(self):
        """同步更新横断面、矢状面和冠状面。"""
        should_fit = self.load_mode in (LOADMode.CHANGE, LOADMode.RELOAD)
        if self.load_mode != LOADMode.UNLOAD:
            for view_mode, viewer in self.viewers.items():
                img = self.prepare_image(view_mode)
                viewer.load_image(img, self.radius)
                if should_fit:
                    viewer.fitInView(
                        viewer.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio
                    )
                    viewer.remember_fit_transform()
                    viewer._scene.setSceneRect(
                        viewer.pixmap_item.sceneBoundingRect()
                    )

        if should_fit:
            self.load_mode = LOADMode.LOADED

        if self.load_mode != LOADMode.UNLOAD:
            self.sync_crosshair_overlay()

    def update_property_and_refresh(self, attr_name, value):
        setattr(self, attr_name, value)
        # 窗宽窗位或融合参数变化后，需要让 SAM 重新编码当前图像。
        self.num = None
        if self.load_mode != LOADMode.UNLOAD:
            self.update_image()
        # 3D 框和 segmentation actor 共用可视化透明度；只有在用户已经
        # 点击过“刷新”并初始化 VTK 后才安排一次轻量重绘。
        if attr_name == "seg_alpha" and getattr(
            getattr(self, "viewer_3d", None), "is_initialized", False
        ):
            self.request_3d_refresh()

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
                    f"{self.ct.shape[2]} {self.ct.shape[1]} {self.ct.shape[0]}"
                )
                info["PET尺寸"] = (
                    f"{self.pet_shape[2]} {self.pet_shape[1]} {self.pet_shape[0]}"
                )

            # Spacing信息
            if hasattr(self, "ct_spacing") and self.ct_spacing:
                info["CT层厚"] = (
                    f"{self.ct_spacing[0]:.3f}, {self.ct_spacing[1]:.3f}, {self.ct_spacing[2]:.3f}"
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
            if not self._flush_annotation_save() and self.annotation_dirty:
                QMessageBox.warning(
                    self,
                    "框标注未保存",
                    "框标注保存失败或当前文件几何不匹配，已取消退出以避免数据丢失。",
                    QMessageBox.StandardButton.Ok,
                )
                event.ignore()
                return
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
                if self.btn_paint.isChecked() or self.btn_eraser.isChecked():
                    viewer, view_mode, layer = self._interaction_context()
                    if viewer is None:
                        event.accept()
                        return
                    if self._seg_before_edit is None:
                        self._seg_before_edit = self._get_volume_slice(
                            self.seg, view_mode, layer
                        ).copy()
                        self._seg_edit_context = (view_mode, layer)
                    self._paint_at_viewer_point(viewer, view_mode, layer)
                    self.update_all()

        event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动重写，用于移动和绘图"""
        super().mouseMoveEvent(event)
        if (
            self.load_mode != LOADMode.UNLOAD
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            viewer, view_mode, layer = self._interaction_context()
            if viewer is None:
                event.accept()
                return
            if self.btn_win.isChecked() and viewer.underMouse():
                delta = viewer.delta

                self.ct_ww = np.clip(self.ct_ww, 1, 4000)
                self.ct_wl = np.clip(self.ct_wl, -2000, 2000)

                self.ct_ww += int(delta.x())
                self.ct_wl += int(delta.y())
                self.image_setting.boxCT_ww.setValue(int(self.ct_ww))
                self.image_setting.boxCT_wl.setValue(int(self.ct_wl))

            elif self.btn_paint.isChecked() or self.btn_eraser.isChecked():
                if self._seg_edit_context is not None:
                    view_mode, layer = self._seg_edit_context
                self._paint_at_viewer_point(viewer, view_mode, layer)
                self.update_all()

        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.btn_paint.isChecked() or self.btn_eraser.isChecked():
            # 鼠标抬起时，将修改前后的当前层切片压入撤销栈
            if self._seg_before_edit is not None and self._seg_edit_context is not None:
                view_mode, layer = self._seg_edit_context
                new_slice = self._get_volume_slice(self.seg, view_mode, layer).copy()
                # 只有当切片确实发生变化时才记录撤销命令
                if not np.array_equal(self._seg_before_edit, new_slice):
                    self.commit_seg_change(
                        view_mode, layer, self._seg_before_edit, new_slice, "绘制"
                    )
                self._seg_before_edit = None
                self._seg_edit_context = None

        event.accept()

    def wheelEvent(self, event):
        super().wheelEvent(event)
        """鼠标滚动重写，用于切换层数，放缩"""
        angle = event.angleDelta()

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.btn_paint.isChecked() or self.btn_eraser.isChecked():
                if angle.y() > 0 and self.radius < 30:
                    self.radius += 1
                    self.segment_setting.boxPaint.setValue(self.radius)
                elif angle.y() < 0 and self.radius > 1:
                    self.radius -= 1
                    self.segment_setting.boxPaint.setValue(self.radius)

        elif self.load_mode != LOADMode.UNLOAD:
            viewer, view_mode, layer = self._interaction_context()
            if viewer is not None and viewer.wheel:
                if angle.y() > 0:
                    layer += 1
                elif angle.y() < 0:
                    layer -= 1
                layer = self._clamp_index(layer, self._view_layer_count(view_mode))
                self.on_view_layer_changed(view_mode, layer)

        event.accept()

    def _interaction_context(self):
        viewer = self._active_viewer
        if viewer not in self.viewers.values():
            return None, None, None
        view_mode = viewer.view_mode
        self.view_mode = view_mode
        self.layer = self.layers[view_mode]
        return viewer, view_mode, self.layer

    def _paint_at_viewer_point(self, viewer, view_mode, layer):
        point = viewer.point
        x, y = point.x(), point.y()
        arr = self._get_volume_slice(self.seg, view_mode, layer).copy()
        rows, cols = arr.shape
        draw_value = self.color_label if viewer.draw_state else 0

        for i in range(max(x - self.radius, 0), min(x + self.radius + 1, cols)):
            for j in range(max(y - self.radius, 0), min(y + self.radius + 1, rows)):
                if (i - x) ** 2 + (j - y) ** 2 <= self.radius**2:
                    arr[j, i] = draw_value

        self._set_volume_slice(self.seg, view_mode, layer, arr)

    def prepare_image(self, view_mode: VIEWMode):
        """更新显示图像"""
        layer = self.layers[view_mode]
        ct = self._get_volume_slice(self.ct, view_mode, layer)
        ct = self.normalize(ct, self.ct_ww, self.ct_wl)

        pet = self._get_volume_slice(self.pet, view_mode, layer)
        pet = self.normalize(pet, self.pet_ww, self.pet_ww / 2)

        new_ct = np.stack([ct] * 3, axis=-1)
        new_pet = cv2.applyColorMap(pet, cv2.COLORMAP_HOT)
        seg = self._get_volume_slice(self.seg, view_mode, layer)

        # 获取标签颜色配置
        label_colors = []
        for label_id, label_info in self._config.label.items():
            # 统一使用 QColor 解析配置，兼容 #RGB/#RRGGBB 和无效配置；
            # 框渲染器也采用同一套回退颜色，避免刷新图像时直接崩溃。
            color = label_info.get("color", "#ffff00") if isinstance(label_info, dict) else "#ffff00"
            qcolor = QColor(str(color))
            if not qcolor.isValid():
                qcolor = QColor("#ffff00")
            label_colors.append(
                (int(label_id), (qcolor.blue(), qcolor.green(), qcolor.red()))
            )

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

    def request_3d_refresh(self, delay_ms: int = 150):
        # 用户第一次点击 3D 刷新前，不启动定时器，也不触碰 VTK。
        if not self.viewer_3d.is_initialized:
            self._pending_3d_refresh = True
            return
        self._refresh_3d_timer.start(max(0, int(delay_ms)))

    def view_3d_built(self, force=False):
        # VTK 只允许通过 Viewer3D 的刷新按钮显式加载。
        if not self.viewer_3d.is_initialized:
            self._pending_3d_refresh = True
            return

        has_segmentation = self.load_mode != LOADMode.UNLOAD and np.any(self.seg)
        has_boxes = (
            self.annotation_document is not None
            and bool(self.annotation_document.annotations)
        )

        def box_actors():
            if not has_boxes or self.image_geometry is None:
                return []
            return self.viewer_3d.build_box_actors(
                self.annotation_document.annotations,
                self.image_geometry,
                self._config.label,
                opacity=self.seg_alpha,
                selected_id=self.box_controller.selected_id,
            )

        if has_segmentation:
            data = np.ascontiguousarray(self.seg.copy())

            data_hash = hash(data.tobytes())
            label_hash = hash(json.dumps(self._config.label, sort_keys=True))
            current_hash = hash((data_hash, label_hash))
            self._requested_3d_hash = current_hash
            generation = self._volume_generation
            self._requested_3d_token = (generation, current_hash)

            if self._built_thread is not None and self._built_thread.isRunning():
                self._pending_3d_refresh = True
                return

            if (
                not force
                and current_hash == self._seg_cache_hash
                and self._vtk_actor_cache is not None
            ):
                self.viewer_3d.set_actor(self._vtk_actor_cache, box_actors())
                return

            def add_vtk_actor(actor):
                if (generation, current_hash) != getattr(
                    self, "_requested_3d_token", None
                ):
                    return
                self._vtk_actor_cache = actor
                self._seg_cache_hash = current_hash
                self.viewer_3d.set_actor(actor, box_actors())

            def on_built_finished():
                if (generation, current_hash) != getattr(
                    self, "_requested_3d_token", None
                ):
                    # 该线程可能属于已切换的病例/旧请求，不能清空新线程状态。
                    return
                self._built_thread = None
                if self._pending_3d_refresh:
                    self._pending_3d_refresh = False
                    self.request_3d_refresh(0)

            def on_built_error(message):
                if (generation, current_hash) != getattr(
                    self, "_requested_3d_token", None
                ):
                    return
                self._built_thread = None
                self._pending_3d_refresh = False
                self._annotation_warning("3D 重建失败", str(message))

            self._built_thread = BuiltThread(
                data,
                self.ct_spacing,
                self._config.label,
                geometry=self.image_geometry,
            )
            self._built_thread.actor_ready.connect(add_vtk_actor)
            self._built_thread.finished.connect(on_built_finished)
            self._built_thread.error.connect(on_built_error)
            self._built_thread.start()
        else:
            self._requested_3d_hash = None
            self._requested_3d_token = None
            self._vtk_actor_cache = None
            self._seg_cache_hash = None
            if has_boxes:
                # 即使当前还没有 segmentation，也可在 3D 刷新后观察框关系。
                self.viewer_3d.set_actor(None, box_actors())
            else:
                self.viewer_3d.clear()

    def commit_seg_change(
        self, view_mode, layer, old_slice, new_slice, description="编辑"
    ):
        """当某一层 seg 发生变化时，调用此函数记录撤销命令"""
        if old_slice is None or new_slice is None:
            return

        command = SegChangeCommand(
            self, view_mode, layer, old_slice, new_slice, description
        )
        self.undo_stack.push(command)


if __name__ == "__main__":
    from pcst.app.configs import ConfigManager

    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    config = config_manager.load()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
