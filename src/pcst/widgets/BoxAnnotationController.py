"""三正交视图中的 3D AABB 创建、选择、编辑和绘制。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

from pcst.app.mode import LOADMode, VIEWERMode, VIEWMode
from pcst.core.annotations import (
    Annotation3D,
    AnnotationDocument,
    AnnotationValidationError,
    BoxGeometry,
    Relation,
)
from pcst.core.geometry import CoordinateService, GeometryValidationError


@dataclass(slots=True)
class _DraftBox:
    viewer: Any
    view_mode: VIEWMode
    start_ijk: tuple[int, int, int]
    current_ijk: tuple[int, int, int]
    min_ijk: tuple[int, int, int]
    max_ijk_exclusive: tuple[int, int, int]
    depth_selection: bool = False


@dataclass(slots=True)
class _DragState:
    annotation_id: str
    viewer: Any
    view_mode: VIEWMode
    kind: str
    handle: tuple[str, ...] | None
    original: Annotation3D
    anchor_ijk: tuple[int, int, int]


class BoxAnnotationController(QObject):
    """使用一个 annotation document 驱动三个二维视图。

    事件过滤器只在 ``VIEWERMode.BOX_3D`` 下接管左键和键盘操作，其他模式仍由
    ImageViewer 原有逻辑处理。框本身不写入 segmentation 数组。
    """

    boxes_changed = Signal()
    selection_changed = Signal(object)
    status_message = Signal(str)

    _VIEW_AXES = {
        VIEWMode.AXIAL: ("I", "J", "K"),
        VIEWMode.SAGITTAL: ("J", "K", "I"),
        VIEWMode.CORONAL: ("I", "K", "J"),
    }

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.document: AnnotationDocument | None = None
        self._viewers: dict[int, Any] = {}
        self.selected_id: str | None = None
        self.hovered_id: str | None = None
        self._draft: _DraftBox | None = None
        self._drag: _DragState | None = None
        self._last_status = ""
        main_window.installEventFilter(self)

    def attach_viewer(self, viewer) -> None:
        """让一个 ImageViewer 支持框事件和前景绘制。"""

        if id(viewer) in self._viewers:
            return
        self._viewers[id(viewer)] = viewer
        viewer.installEventFilter(self)
        viewer.viewport().installEventFilter(self)

    def set_document(self, document: AnnotationDocument | None) -> None:
        self.cancel()
        self.document = document
        self.selected_id = None
        self.hovered_id = None
        self.selection_changed.emit(None)
        self.update_viewports()

    def _is_box_mode(self, viewer=None) -> bool:
        if viewer is not None and getattr(viewer, "mode", None) == VIEWERMode.BOX_3D:
            return True
        button = getattr(self.main_window, "btn_box", None)
        return bool(button is not None and button.isChecked())

    def _viewer_for(self, watched) -> Any | None:
        stale_ids = []
        for viewer_id, viewer in self._viewers.items():
            try:
                if watched is viewer or watched is viewer.viewport():
                    return viewer
            except RuntimeError:
                # Qt parent销毁时 Python wrapper 仍可能短暂留在字典中。
                stale_ids.append(viewer_id)
        for viewer_id in stale_ids:
            self._viewers.pop(viewer_id, None)
        return None

    def eventFilter(self, watched, event) -> bool:
        viewer = self._viewer_for(watched)
        if viewer is not None:
            if event.type() in (
                QEvent.Type.KeyPress,
                QEvent.Type.KeyRelease,
            ):
                # Delete/Escape/Enter 只在 Box 工具激活时由控制器消费，避免
                # 在准心、绘制等旧工具下误删当前框。
                if not self._is_box_mode(viewer):
                    return False
                return self._handle_key_event(event)
            if not self._is_box_mode(viewer):
                return False
            if event.type() == QEvent.Type.Wheel:
                if self._draft is not None and self._draft.depth_selection:
                    return self._handle_depth_wheel(viewer, event)
                return False
            if event.type() == QEvent.Type.MouseButtonPress:
                return self._mouse_press(viewer, event)
            if event.type() == QEvent.Type.MouseMove:
                return self._mouse_move(viewer, event)
            if event.type() == QEvent.Type.MouseButtonRelease:
                return self._mouse_release(viewer, event)
            return False

        if watched is self.main_window and event.type() in (
            QEvent.Type.KeyPress,
            QEvent.Type.KeyRelease,
        ):
            if not self._is_box_mode():
                return False
            return self._handle_key_event(event)
        return False

    def _handle_depth_wheel(self, viewer, event) -> bool:
        """创建框的第二阶段用滚轮选择法向深度。"""

        if self._draft is None or viewer is not self._draft.viewer:
            return True
        delta = int(event.angleDelta().y())
        if delta == 0:
            return True
        view_mode = self._draft.view_mode
        current_layer = self._layer(view_mode)
        step = 1 if delta > 0 else -1
        count = getattr(self.main_window, "_view_layer_count", lambda _mode: 0)(view_mode)
        if count > 0:
            next_layer = max(0, min(current_layer + step, count - 1))
            if next_layer != current_layer and hasattr(
                self.main_window, "on_view_layer_changed"
            ):
                self.main_window.on_view_layer_changed(view_mode, next_layer)
        self._set_status("滚轮选择结束层，单击或按 Enter 完成三维框")
        self.update_viewports()
        event.accept()
        return True

    def _handle_key_event(self, event) -> bool:
        if event.type() != QEvent.Type.KeyPress:
            return False
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return True
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._draft is not None and self._draft.depth_selection:
                self._commit_draft()
                return True
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_id is not None:
                self.delete_selected()
                return True
        return False

    def _loaded(self) -> bool:
        if self.document is None:
            return False
        if getattr(self.main_window, "load_mode", LOADMode.UNLOAD) == LOADMode.UNLOAD:
            return False
        return True

    def _service(self) -> CoordinateService | None:
        if self.document is None:
            return None
        return self.document.coordinate_service

    def _layer(self, view_mode: VIEWMode) -> int:
        layers = getattr(self.main_window, "layers", {})
        return int(layers.get(view_mode, 0))

    @staticmethod
    def _event_position(event) -> QPointF:
        return event.position()

    def _image_point_to_ijk(self, viewer, view_mode: VIEWMode, position: QPointF):
        service = self._service()
        if service is None:
            return None
        image_point = viewer.pixmap_item.mapFromScene(
            viewer.mapToScene(position.toPoint())
        )
        try:
            return service.slice_to_ijk(
                view_mode,
                image_point.x(),
                image_point.y(),
                self._layer(view_mode),
            )
        except (GeometryValidationError, ValueError):
            return None

    def _mouse_press(self, viewer, event) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if not self._loaded():
            self._set_status("请先加载图像数据")
            return True

        self.main_window._active_viewer = viewer
        self.main_window.view_mode = viewer.view_mode
        view_mode = viewer.view_mode
        if self._draft is not None and self._draft.depth_selection:
            if viewer is not self._draft.viewer:
                self._set_status("请在创建框的原位面中点击确认深度")
                return True
            self._commit_draft()
            return True

        ijk = self._image_point_to_ijk(viewer, view_mode, self._event_position(event))
        if ijk is None:
            return True

        hit = self.hit_test(viewer, self._event_position(event))
        if hit is not None:
            annotation = hit["annotation"]
            self.select(annotation.id)
            self._drag = _DragState(
                annotation_id=annotation.id,
                viewer=viewer,
                view_mode=view_mode,
                kind=hit["kind"],
                handle=hit.get("handle"),
                original=annotation.copy(),
                anchor_ijk=ijk,
            )
            return True

        self._draft = _DraftBox(
            viewer=viewer,
            view_mode=view_mode,
            start_ijk=ijk,
            current_ijk=ijk,
            min_ijk=ijk,
            max_ijk_exclusive=tuple(value + 1 for value in ijk),
        )
        self._set_status("拖动鼠标创建矩形，松开后用滚轮选择深度")
        self.update_viewports()
        return True

    def _mouse_move(self, viewer, event) -> bool:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            if self.document is not None:
                hit = self.hit_test(viewer, self._event_position(event))
                hovered_id = hit["annotation"].id if hit is not None else None
                if hovered_id != self.hovered_id:
                    self.hovered_id = hovered_id
                    self.update_viewports()
            return False
        if self._draft is not None:
            if viewer is not self._draft.viewer or self._draft.depth_selection:
                return True
            ijk = self._image_point_to_ijk(
                viewer, self._draft.view_mode, self._event_position(event)
            )
            if ijk is not None:
                self._draft.current_ijk = ijk
                self._update_draft_base_bounds()
                self.update_viewports()
            return True
        if self._drag is None:
            return True

        ijk = self._image_point_to_ijk(
            viewer, self._drag.view_mode, self._event_position(event)
        )
        if ijk is None:
            return True
        self._update_drag(ijk)
        self.update_viewports()
        return True

    def _mouse_release(self, viewer, event) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if self._draft is not None and viewer is self._draft.viewer:
            if not self._draft.depth_selection:
                self._update_draft_base_bounds()
                self._draft.depth_selection = True
                self._set_status("滚轮选择结束层，单击或按 Enter 完成三维框")
                self.update_viewports()
            return True
        if self._drag is not None:
            self._finish_drag()
            return True
        return True

    def _update_draft_base_bounds(self) -> None:
        if self._draft is None:
            return
        view_axes = self._VIEW_AXES[self._draft.view_mode]
        start_values = dict(zip("IJK", self._draft.start_ijk))
        current_values = dict(zip("IJK", self._draft.current_ijk))
        min_values = dict(start_values)
        max_values = {axis: value + 1 for axis, value in start_values.items()}
        for axis in view_axes[:2]:
            lower = min(start_values[axis], current_values[axis])
            upper = max(start_values[axis], current_values[axis]) + 1
            min_values[axis] = lower
            max_values[axis] = upper
        self._draft.min_ijk = tuple(min_values[axis] for axis in "IJK")
        self._draft.max_ijk_exclusive = tuple(max_values[axis] for axis in "IJK")

    def _draft_bounds(self) -> tuple[tuple[int, int, int], tuple[int, int, int]] | None:
        if self._draft is None:
            return None
        min_values = dict(zip("IJK", self._draft.min_ijk))
        max_values = dict(zip("IJK", self._draft.max_ijk_exclusive))
        if self._draft.depth_selection:
            view_axes = self._VIEW_AXES[self._draft.view_mode]
            normal_axis = view_axes[2]
            start_layer = self._draft.start_ijk["IJK".index(normal_axis)]
            current_layer = self._layer(self._draft.view_mode)
            lower = min(start_layer, current_layer)
            upper = max(start_layer, current_layer) + 1
            min_values[normal_axis] = lower
            max_values[normal_axis] = upper
        return tuple(min_values[axis] for axis in "IJK"), tuple(
            max_values[axis] for axis in "IJK"
        )

    def _commit_draft(self) -> None:
        if self._draft is None or self.document is None:
            return
        bounds = self._draft_bounds()
        if bounds is None:
            return
        min_ijk, max_ijk_exclusive = bounds
        try:
            self.document.coordinate_service.validate_bbox(
                min_ijk, max_ijk_exclusive
            )
        except GeometryValidationError as exc:
            self._set_status(f"框坐标无效：{exc}")
            self.cancel()
            return

        annotation = Annotation3D.new(
            class_id=int(getattr(self.main_window, "color_label", 0)),
            min_ijk=min_ijk,
            max_ijk_exclusive=max_ijk_exclusive,
        )
        from pcst.widgets.commands import AddBoxCommand

        try:
            self.main_window.undo_stack.push(
                AddBoxCommand(self.document, annotation, self)
            )
        except (AnnotationValidationError, ValueError) as exc:
            self._set_status(f"创建三维框失败：{exc}")
            self.cancel()
            return
        self._draft = None
        self.select(annotation.id)
        self._center_on_box(annotation.geometry)
        self._set_status(f"已创建三维框 {annotation.id}")
        self.update_viewports()

    def _update_drag(self, ijk: tuple[int, int, int]) -> None:
        if self._drag is None or self.document is None:
            return
        try:
            annotation = self.document.get(self._drag.annotation_id)
        except KeyError:
            self._drag = None
            return

        original = self._drag.original
        min_values = list(original.geometry.min_ijk)
        max_values = list(original.geometry.max_ijk_exclusive)
        view_axes = self._VIEW_AXES[self._drag.view_mode]
        if self._drag.kind == "move":
            anchor = dict(zip("IJK", self._drag.anchor_ijk))
            current = dict(zip("IJK", ijk))
            delta = {axis: current[axis] - anchor[axis] for axis in view_axes[:2]}
            for axis in view_axes[:2]:
                index = "IJK".index(axis)
                size = self.document.image_geometry.size_ijk[index]
                span = original.geometry.max_ijk_exclusive[index] - original.geometry.min_ijk[index]
                shift = max(
                    -original.geometry.min_ijk[index],
                    min(delta[axis], size - original.geometry.max_ijk_exclusive[index]),
                )
                min_values[index] = original.geometry.min_ijk[index] + shift
                max_values[index] = min_values[index] + span
        else:
            handles = self._drag.handle or ()
            current = dict(zip("IJK", ijk))
            for axis in handles:
                index = "IJK".index(axis[0])
                size = self.document.image_geometry.size_ijk[index]
                if axis.endswith("min"):
                    # Treat the opposite side as fixed while allowing the
                    # dragged side to cross it.  Normalizing the two values
                    # here gives the user the expected reverse-drag behavior
                    # instead of getting stuck at a one-voxel clamp.
                    fixed = original.geometry.max_ijk_exclusive[index]
                    dragged = max(0, min(current[axis[0]], size - 1))
                    min_values[index] = min(dragged, fixed - 1)
                    max_values[index] = max(dragged + 1, fixed)
                elif axis.endswith("max"):
                    fixed = original.geometry.min_ijk[index]
                    dragged = max(0, min(current[axis[0]], size - 1))
                    min_values[index] = min(fixed, dragged)
                    max_values[index] = max(fixed + 1, dragged + 1)
        try:
            new_geometry = BoxGeometry(tuple(min_values), tuple(max_values)).validate(
                self.document.image_geometry
            )
        except GeometryValidationError:
            return
        annotation.geometry = new_geometry
        self.document.update(annotation)
        self.boxes_changed.emit()

    def _finish_drag(self) -> None:
        if self._drag is None or self.document is None:
            return
        try:
            current = self.document.get(self._drag.annotation_id).copy()
        except KeyError:
            self._drag = None
            return
        original = self._drag.original
        self._drag = None
        if (
            current.geometry == original.geometry
            and current.class_id == original.class_id
            and current.lesion_id == original.lesion_id
            and current.relations == original.relations
            and current.attributes == original.attributes
        ):
            return
        from pcst.widgets.commands import UpdateBoxCommand

        self.main_window.undo_stack.push(
            UpdateBoxCommand(self.document, original, current, self)
        )
        self._set_status(f"已更新三维框 {current.id}")

    def select(self, annotation_id: str | None, *, center: bool = False) -> None:
        selected_annotation = None
        if annotation_id is not None and self.document is not None:
            try:
                selected_annotation = self.document.get(annotation_id)
            except KeyError:
                annotation_id = None
        self.selected_id = annotation_id
        if center and selected_annotation is not None:
            self._center_on_box(selected_annotation.geometry)
        self.selection_changed.emit(annotation_id)
        self.update_viewports()

    def delete_selected(self) -> None:
        if self.selected_id is None or self.document is None:
            return
        try:
            annotation = self.document.get(self.selected_id).copy()
        except KeyError:
            self.selected_id = None
            return
        try:
            self.document._validate_annotations(
                [item for item in self.document.annotations if item.id != annotation.id]
            )
        except AnnotationValidationError as exc:
            self._set_status(f"无法删除框：{exc}")
            return
        from pcst.widgets.commands import DeleteBoxCommand

        self.main_window.undo_stack.push(DeleteBoxCommand(self.document, annotation, self))
        self.selected_id = None
        self.selection_changed.emit(None)
        self._set_status(f"已删除三维框 {annotation.id}")
        self.update_viewports()

    def cancel(self) -> None:
        restored = False
        if self._drag is not None and self.document is not None:
            try:
                self.document.update(self._drag.original.copy())
                restored = True
            except KeyError:
                pass
        self._draft = None
        self._drag = None
        if restored:
            self.boxes_changed.emit()
        self.update_viewports()

    def set_annotation_class(self, annotation_id: str, class_id: int) -> bool:
        if self.document is None:
            return False
        try:
            annotation = self.document.get(annotation_id)
        except KeyError:
            return False
        before = annotation.copy()
        after = annotation.copy()
        try:
            normalized_class_id = int(class_id)
        except (TypeError, ValueError):
            self._set_status(f"类别编号无效：{class_id}")
            return False
        if normalized_class_id < 0:
            self._set_status("类别编号不能为负数")
            return False
        if self.document.classes and normalized_class_id not in {
            int(item["id"]) for item in self.document.classes
        }:
            self._set_status(f"类别不存在：{normalized_class_id}")
            return False
        after.class_id = normalized_class_id
        from pcst.widgets.commands import UpdateBoxCommand

        self.main_window.undo_stack.push(
            UpdateBoxCommand(self.document, before, after, self)
        )
        return True

    def set_annotation_lesion_id(
        self, annotation_id: str, lesion_id: str | None
    ) -> bool:
        """修改医学语义层的 lesion_id，不改变框的 IJK 几何。"""

        if self.document is None:
            return False
        try:
            annotation = self.document.get(annotation_id)
        except KeyError:
            return False
        normalized = None if lesion_id is None or not str(lesion_id).strip() else str(lesion_id).strip()
        before = annotation.copy()
        after = annotation.copy()
        after.lesion_id = normalized
        try:
            # 用临时文档检查 lesion relation 仍然指向有效的 lesion，避免将
            # 已有 relation 静默悬空；正式修改仍由撤销命令完成。
            AnnotationDocument(
                case_id=self.document.case_id,
                image_file=self.document.image_file,
                image_geometry=self.document.image_geometry,
                annotations=[
                    after if item.id == annotation_id else item.copy()
                    for item in self.document.annotations
                ],
                classes=[dict(item) for item in self.document.classes],
            )
        except Exception as exc:
            self._set_status(f"病灶 ID 无效：{exc}")
            return False
        from pcst.widgets.commands import UpdateBoxCommand

        self.main_window.undo_stack.push(
            UpdateBoxCommand(self.document, before, after, self)
        )
        return True

    def set_annotation_relations(
        self, annotation_id: str, relations: list[Relation | dict]
    ) -> bool:
        """修改 annotation 的医学语义关系（如 ``contained_in``）。"""

        if self.document is None:
            return False
        try:
            annotation = self.document.get(annotation_id)
        except KeyError:
            return False
        try:
            normalized = [
                relation if isinstance(relation, Relation) else Relation.from_dict(relation)
                for relation in relations
            ]
        except AnnotationValidationError as exc:
            self._set_status(f"关系无效：{exc}")
            return False
        before = annotation.copy()
        after = annotation.copy()
        after.relations = normalized
        try:
            AnnotationDocument(
                case_id=self.document.case_id,
                image_file=self.document.image_file,
                image_geometry=self.document.image_geometry,
                annotations=[
                    after if item.id == annotation_id else item.copy()
                    for item in self.document.annotations
                ],
                classes=[dict(item) for item in self.document.classes],
            )
        except Exception as exc:
            self._set_status(f"关系无效：{exc}")
            return False
        from pcst.widgets.commands import UpdateBoxCommand

        self.main_window.undo_stack.push(
            UpdateBoxCommand(self.document, before, after, self)
        )
        return True

    def remap_class_ids(self, mapping: dict[int, int | None]) -> None:
        """同步标签删除/重排；被删除类别的框保留但标记为无效。"""

        if self.document is None:
            return
        changed = False
        for annotation in self.document.annotations:
            if annotation.class_id in mapping:
                target = mapping[annotation.class_id]
                if target is not None and int(target) != int(annotation.class_id):
                    annotation.class_id = int(target)
                    changed = True
        if changed:
            self.boxes_changed.emit()
            self.update_viewports()

    def _center_on_box(self, box: BoxGeometry) -> None:
        center = [
            (lower + upper - 1) // 2
            for lower, upper in zip(box.min_ijk, box.max_ijk_exclusive)
        ]
        if hasattr(self.main_window, "crosshair_ijk"):
            self.main_window.crosshair_ijk = center
        elif hasattr(self.main_window, "crosshair_voxel_xyz"):
            self.main_window.crosshair_voxel_xyz = center
        if hasattr(self.main_window, "_show_voxel_coordinate_status"):
            self.main_window._show_voxel_coordinate_status()
        if hasattr(self.main_window, "_sync_layers_from_crosshair"):
            self.main_window._sync_layers_from_crosshair()
        # ``_sync_layers_from_crosshair`` intentionally only changes the
        # controls (it is also used while handling a single slice event).  A
        # list/3D selection, however, moves all three planes at once, so the
        # rendered pixmaps must be refreshed before updating their overlays.
        if hasattr(self.main_window, "update_all"):
            self.main_window.update_all()
        if hasattr(self.main_window, "sync_crosshair_overlay"):
            self.main_window.sync_crosshair_overlay()

    def _set_status(self, message: str) -> None:
        if message == self._last_status:
            return
        self._last_status = message
        self.status_message.emit(message)
        statusbar = getattr(self.main_window, "statusbar", None)
        if statusbar is not None:
            statusbar.showMessage(message)

    def _label_color(self, class_id: int) -> QColor:
        labels = getattr(getattr(self.main_window, "_config", None), "label", {})
        info = (
            labels.get(str(class_id), labels.get(class_id, {}))
            if isinstance(labels, dict)
            else {}
        )
        color = info.get("color", "#ffff00") if isinstance(info, dict) else "#ffff00"
        qcolor = QColor(str(color))
        if not qcolor.isValid():
            qcolor = QColor("#ffff00")
        return qcolor

    def _projection_points(self, viewer, projection: dict) -> list[QPointF]:
        points = []
        # Pixel coordinates represent voxel centers.  Draw the rectangle on
        # the physical voxel boundaries, i.e. half a pixel outside the first
        # center and half a pixel before the exclusive max center.  The core
        # projection still exposes integer IJK bounds for hit/edit logic.
        u0 = float(projection["u0"]) - 0.5
        u1 = float(projection["u1"]) - 0.5
        v0 = float(projection["v0"]) - 0.5
        v1 = float(projection["v1"]) - 0.5
        for u, v in (
            (u0, v0),
            (u1, v0),
            (u1, v1),
            (u0, v1),
        ):
            scene_point = viewer.pixmap_item.mapToScene(QPointF(float(u), float(v)))
            viewport_point = viewer.mapFromScene(scene_point)
            points.append(QPointF(viewport_point))
        return points

    def _projection_for(self, viewer, annotation: Annotation3D) -> dict | None:
        service = self._service()
        if service is None:
            return None
        try:
            projection = service.bbox_projection(
                viewer.view_mode,
                annotation.geometry.min_ijk,
                annotation.geometry.max_ijk_exclusive,
                self._layer(viewer.view_mode),
            )
        except GeometryValidationError:
            return None
        if not projection["visible"]:
            return None
        return projection

    def _handle_points(self, viewer, projection: dict) -> list[tuple[str, QPointF]]:
        points = self._projection_points(viewer, projection)
        u_mid = (projection["u0"] + projection["u1"] - 1) / 2
        v_mid = (projection["v0"] + projection["v1"] - 1) / 2
        mid_projection = dict(projection)
        handles = [
            ("u0v0", points[0]),
            ("u1v0", points[1]),
            ("u1v1", points[2]),
            ("u0v1", points[3]),
        ]
        for name, u, v in (
            ("u0", float(projection["u0"]) - 0.5, v_mid),
            ("u1", float(projection["u1"]) - 0.5, v_mid),
            ("v0", u_mid, float(projection["v0"]) - 0.5),
            ("v1", u_mid, float(projection["v1"]) - 0.5),
        ):
            scene_point = viewer.pixmap_item.mapToScene(QPointF(float(u), float(v)))
            handles.append((name, QPointF(viewer.mapFromScene(scene_point))))
        return handles

    @staticmethod
    def _distance_squared(first: QPointF, second: QPointF) -> float:
        dx = first.x() - second.x()
        dy = first.y() - second.y()
        return dx * dx + dy * dy

    @staticmethod
    def _point_to_segment_distance_squared(point: QPointF, start: QPointF, end: QPointF) -> float:
        vx = end.x() - start.x()
        vy = end.y() - start.y()
        wx = point.x() - start.x()
        wy = point.y() - start.y()
        length_squared = vx * vx + vy * vy
        if length_squared == 0:
            return BoxAnnotationController._distance_squared(point, start)
        parameter = max(0.0, min(1.0, (wx * vx + wy * vy) / length_squared))
        projection = QPointF(start.x() + parameter * vx, start.y() + parameter * vy)
        return BoxAnnotationController._distance_squared(point, projection)

    def hit_test(self, viewer, position: QPointF) -> dict | None:
        if self.document is None:
            return None
        annotations = list(self.document.annotations)
        if self.selected_id is not None:
            # reversed() 后选中框优先命中，重叠框仍可逐个选择。
            annotations.sort(key=lambda item: item.id == self.selected_id)
        for annotation in reversed(annotations):
            projection = self._projection_for(viewer, annotation)
            if projection is None:
                continue
            points = self._projection_points(viewer, projection)
            handle_map = dict(self._handle_points(viewer, projection))
            for handle_name, handle_point in handle_map.items():
                if self._distance_squared(position, handle_point) <= 10.0**2:
                    affected = self._handle_to_axes(viewer.view_mode, projection, handle_name)
                    return {
                        "annotation": annotation,
                        "kind": "resize",
                        "handle": affected,
                    }
            for start, end in zip(points, points[1:] + points[:1]):
                if self._point_to_segment_distance_squared(position, start, end) <= 7.0**2:
                    return {"annotation": annotation, "kind": "move", "handle": None}
            if QPolygonF(points).containsPoint(position, Qt.FillRule.OddEvenFill):
                return {"annotation": annotation, "kind": "move", "handle": None}
        return None

    def _handle_to_axes(self, view_mode: VIEWMode, projection: dict, handle_name: str):
        u_axis = projection["u_axis"]
        v_axis = projection["v_axis"]
        if handle_name == "u0":
            return (f"{u_axis}min",)
        if handle_name == "u1":
            return (f"{u_axis}max",)
        if handle_name == "v0":
            return (f"{v_axis}min",)
        if handle_name == "v1":
            return (f"{v_axis}max",)
        sides = []
        if handle_name.startswith("u0"):
            sides.append(f"{u_axis}min")
        else:
            sides.append(f"{u_axis}max")
        if handle_name.endswith("v0"):
            sides.append(f"{v_axis}min")
        else:
            sides.append(f"{v_axis}max")
        return tuple(sides)

    def _draw_annotation(self, viewer, painter: QPainter, annotation: Annotation3D) -> None:
        projection = self._projection_for(viewer, annotation)
        if projection is None:
            return
        points = self._projection_points(viewer, projection)
        polygon = QPolygonF(points)
        color = self._label_color(annotation.class_id)
        selected = annotation.id == self.selected_id
        hovered = annotation.id == self.hovered_id
        border = QPen(color, 2.2 if selected else (1.8 if hovered else 1.2))
        border.setCosmetic(True)
        painter.setPen(border)
        fill = QColor(color)
        opacity = float(getattr(self.main_window, "seg_alpha", 0.5))
        fill.setAlphaF(max(0.0, min(1.0, opacity)))
        painter.setBrush(QBrush(fill))
        painter.drawPolygon(polygon)
        if selected:
            handle_pen = QPen(QColor("white"), 1.0)
            handle_pen.setCosmetic(True)
            painter.setPen(handle_pen)
            painter.setBrush(QBrush(color))
            for _, point in self._handle_points(viewer, projection):
                painter.drawEllipse(point, 4.0, 4.0)

    def draw(self, viewer, painter: QPainter) -> None:
        """由 ImageViewer.drawForeground 调用，painter 已切换到 viewport 坐标。"""

        if self.document is None:
            return
        annotations = list(self.document.annotations)
        if self.selected_id is not None:
            # 选中框最后绘制，确保重叠时仍然可见。
            annotations.sort(key=lambda item: item.id == self.selected_id)
        for annotation in annotations:
            self._draw_annotation(viewer, painter, annotation)

        if self._draft is not None:
            bounds = self._draft_bounds()
            if bounds is not None:
                draft = Annotation3D.new(
                    class_id=int(getattr(self.main_window, "color_label", 0)),
                    min_ijk=bounds[0],
                    max_ijk_exclusive=bounds[1],
                )
                self._draw_annotation(viewer, painter, draft)

    def update_viewports(self) -> None:
        for viewer in self._viewers.values():
            viewer.viewport().update()
