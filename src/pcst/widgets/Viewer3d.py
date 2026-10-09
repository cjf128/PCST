from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from pcst.ui.Viewer3d_ui import Ui_Form
from pcst.scripts.logger import log_error


class Viewer3D(QWidget, Ui_Form):
    """3D 视图容器。

    这里只创建轻量的 Qt 控件。VTK 的原生模块和渲染窗口会在用户点击
    “刷新”后才导入和创建，避免应用启动时就加载 VTK DLL。
    """

    refresh_requested = Signal()
    reset_requested = Signal()
    annotation_selected = Signal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.interactor_widget = None
        self.renderer = None
        self.interactor = None
        self._initialized = False
        self._segmentation_actor = None
        self._box_actors = []
        # VTK may return a new Python wrapper for the same native actor during
        # picking.  Keep the mapping keyed by the native object's stable
        # address instead of ``id(wrapper)``.
        self._box_actor_ids: dict[str, str] = {}

        self.btnRefresh.clicked.connect(self._on_refresh_clicked)
        self.btnReset.clicked.connect(self._on_reset_clicked)

    @property
    def is_initialized(self) -> bool:
        """VTK 渲染窗口是否已经在刷新按钮中成功创建。"""
        return self._initialized

    def _on_refresh_clicked(self) -> None:
        if self._ensure_vtk():
            self.refresh_requested.emit()

    def _on_reset_clicked(self) -> None:
        """交由 MainWindow 统一复位所有二维位面和 3D 相机。"""
        self.reset_requested.emit()

    def _ensure_vtk(self) -> bool:
        """第一次刷新时加载 VTK 并创建渲染窗口。"""
        if self._initialized:
            return True

        try:
            # 必须放在函数内部：这些模块包含原生 DLL，不能在应用启动时加载。
            from vtkmodules.qt.QVTKRenderWindowInteractor import (
                QVTKRenderWindowInteractor,
            )
            from vtkmodules.vtkInteractionStyle import (
                vtkInteractorStyleTrackballCamera,
            )
            from vtkmodules.vtkRenderingCore import vtkRenderer

            # 注册 OpenGL2 渲染后端；避免导入顶层 vtk 包。
            import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

            self.interactor_widget = QVTKRenderWindowInteractor(self.viewer_frame)
            viewer_layout = QVBoxLayout(self.viewer_frame)
            viewer_layout.setContentsMargins(0, 0, 0, 0)
            viewer_layout.setSpacing(0)
            viewer_layout.addWidget(self.interactor_widget)

            self.renderer = vtkRenderer()
            self.renderer.SetBackground(0, 0, 0)
            self.interactor_widget.GetRenderWindow().AddRenderer(self.renderer)
            self.interactor = self.interactor_widget.GetRenderWindow().GetInteractor()
            self.interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
            # Picking is registered only after the lazy VTK initialization.
            # It keeps startup free from VTK imports and lets a 3D click select
            # the same annotation that is highlighted in the 2D viewers/list.
            self.interactor.AddObserver("LeftButtonPressEvent", self._on_left_button_press)
            self.interactor_widget.Initialize()
            # ``Start()`` is intended for a standalone VTK event loop.  In a
            # Qt-embedded widget it can re-enter/block the QApplication (and
            # is particularly fragile on Windows OpenGL contexts); Qt drives
            # the interactor after ``Initialize``.
            self._initialized = True
            return True
        except Exception as exc:
            log_error(f"加载3D视图失败: {exc}")
            QMessageBox.warning(
                self,
                "3D视图加载失败",
                "无法加载 VTK 三维组件，请检查 VTK 安装或 Windows 安全策略。\n"
                f"详细信息：{exc}",
            )
            return False

    def _on_left_button_press(self, _caller, _event) -> None:
        if self.interactor is None or self.renderer is None:
            return
        try:
            from vtkmodules.vtkRenderingCore import vtkPropPicker

            x, y = self.interactor.GetEventPosition()
            picker = vtkPropPicker()
            if not picker.Pick(x, y, 0, self.renderer):
                return
            actor = picker.GetActor()
            annotation_id = self._box_actor_ids.get(self._actor_key(actor))
            if annotation_id:
                self.annotation_selected.emit(annotation_id)
        except Exception as exc:
            # Picking must never break camera interaction; diagnostics are
            # useful for VTK builds that do not provide vtkPropPicker.
            log_error(f"3D框选择失败: {exc}")

    def set_actor(self, actor, box_actors=None) -> None:
        if not self._initialized or self.renderer is None:
            return
        had_scene = self._segmentation_actor is not None or bool(self._box_actors)
        self._segmentation_actor = actor
        self._box_actors = list(box_actors or [])
        previous_ids = dict(self._box_actor_ids)
        self._box_actor_ids = {}
        for box_actor in self._box_actors:
            actor_key = self._actor_key(box_actor)
            annotation_id = getattr(
                box_actor, "_pcst_annotation_id", previous_ids.get(actor_key, "")
            )
            if annotation_id:
                self._box_actor_ids[actor_key] = str(annotation_id)
        self.renderer.RemoveAllViewProps()
        if actor is not None:
            self.renderer.AddActor(actor)
        for box_actor in self._box_actors:
            self.renderer.AddActor(box_actor)
        if not had_scene:
            self.renderer.ResetCamera()
        self.render()

    def clear(self) -> None:
        if not self._initialized or self.renderer is None:
            return
        self.renderer.RemoveAllViewProps()
        self._segmentation_actor = None
        self._box_actors = []
        self._box_actor_ids = {}
        self.render()

    def reset_camera(self) -> None:
        if not self._initialized or self.renderer is None:
            return
        self.renderer.ResetCamera()
        self.render()

    def render(self) -> None:
        if not self._initialized or self.interactor_widget is None:
            return
        self.interactor_widget.GetRenderWindow().Render()

    @staticmethod
    def _actor_key(actor) -> str:
        """Return a stable key for a VTK object across Python wrappers."""

        if actor is None:
            return ""
        try:
            # ``GetAddressAsString`` is exposed by vtkObjectBase and identifies
            # the native object, unlike Python's ``id`` which is wrapper-local.
            return str(actor.GetAddressAsString(""))
        except Exception:
            return str(id(actor))

    def build_box_actors(
        self,
        annotations,
        geometry,
        label_config=None,
        opacity: float = 0.35,
        selected_id: str | None = None,
    ):
        """将 IJK half-open 框转换为 LPS polydata actor。

        该方法只有在用户点击 3D 刷新、VTK 已完成延迟初始化后才会被调用；
        角点由 ``VolumeGeometry`` 计算，因此不会把 direction 当成 identity。
        """

        if not self._initialized:
            return []
        try:
            from vtkmodules.vtkCommonCore import vtkPoints
            from vtkmodules.vtkCommonDataModel import (
                vtkCellArray,
                vtkPolygon,
                vtkPolyData,
            )
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
        except Exception as exc:
            log_error(f"创建3D框失败: {exc}")
            return []

        labels = label_config or {}
        alpha = max(0.0, min(1.0, float(opacity)))
        actors = []
        # Rebuild the mapping on every refresh so removed/duplicated boxes
        # cannot leave stale pick targets behind.
        self._box_actor_ids = {}
        for annotation in annotations or []:
            try:
                corners = geometry.bbox_corner_lps(
                    annotation.geometry.min_ijk,
                    annotation.geometry.max_ijk_exclusive,
                )
            except Exception as exc:
                log_error(f"跳过无效3D框 {getattr(annotation, 'id', '?')}: {exc}")
                continue

            points = vtkPoints()
            for point in corners:
                points.InsertNextPoint(*point)

            # bbox_corner_lps 的顺序为 I/J/K 三重循环（K 最快）。
            face_indices = (
                (0, 4, 6, 2),
                (1, 3, 7, 5),
                (0, 1, 5, 4),
                (2, 6, 7, 3),
                (0, 2, 3, 1),
                (4, 5, 7, 6),
            )
            polygons = vtkCellArray()
            for indices in face_indices:
                polygon = vtkPolygon()
                polygon.GetPointIds().SetNumberOfIds(4)
                for index, point_id in enumerate(indices):
                    polygon.GetPointIds().SetId(index, point_id)
                polygons.InsertNextCell(polygon)

            poly_data = vtkPolyData()
            poly_data.SetPoints(points)
            poly_data.SetPolys(polygons)
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly_data)
            actor = vtkActor()
            actor.SetMapper(mapper)

            label_info = labels.get(
                str(annotation.class_id), labels.get(annotation.class_id, {})
            )
            if not isinstance(label_info, dict):
                label_info = {}
            color = QColor(str(label_info.get("color", "#ffff00")))
            if not color.isValid():
                color = QColor("#ffff00")
            rgb = (color.redF(), color.greenF(), color.blueF())
            property_ = actor.GetProperty()
            property_.SetColor(*rgb)
            property_.SetOpacity(alpha)
            property_.SetEdgeVisibility(True)
            property_.SetEdgeColor(*rgb)
            # Keep the outline readable even when the interior is translucent.
            # Older VTK builds may not expose edge opacity, so guard the call.
            if hasattr(property_, "SetEdgeOpacity"):
                property_.SetEdgeOpacity(1.0)
            property_.SetLineWidth(3.0 if annotation.id == selected_id else 1.5)
            # VTK Python wrappers accept dynamic attributes; set_actor copies
            # this value into an id-keyed mapping for robust picking.
            try:
                actor._pcst_annotation_id = str(annotation.id)
            except Exception:
                pass
            self._box_actor_ids[self._actor_key(actor)] = str(annotation.id)
            actors.append(actor)
        return actors
