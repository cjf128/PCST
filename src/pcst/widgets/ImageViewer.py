# Copyright (c) 2026 PCST Jinfr
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPen, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from pcst.app.mode import SAMMode, VIEWERMode, VIEWMode


class ImageViewer(QGraphicsView):
    Sam_Signal = Signal(np.ndarray)
    Mode_Signal = Signal()
    # Emitted after a user pan/zoom.  MainWindow uses the normalized image
    # center and relative zoom to synchronize the three orthogonal viewers.
    view_state_changed = Signal(object)

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window

        self.point_list = []
        self.input_box = []
        self.parent = parent

        self.mode = VIEWERMode.AIM
        self.view_mode = VIEWMode.AXIAL

        self.wheel = False
        self.information_show = True
        self.cross_show = False
        self.direction_show = True
        self.patient_name = None

        self.spacing = (1, 1, 1)

        self.pixmap_item = QGraphicsPixmapItem()
        self.rect_item = QGraphicsRectItem()
        self.ellipse_item = QGraphicsEllipseItem()

        self.start_point = QPoint()
        self.end_point = QPoint()
        self.last_mouse_position = QPoint()

        self.draw_state = 0
        self.radius = 0
        self.ellipse_pos = [0, 0]
        self.position = [0, 0, 0]
        self.crosshair_point = None
        self._fit_transform = QTransform()
        self.config()

    def config(self):
        self.setMouseTracking(True)
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QColor(Qt.GlobalColor.black))
        self.setScene(self._scene)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def load_image(self, pixmap, radius):
        global scale_x, scale_y
        self._scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.radius = 2 * radius
        self.ellipse_item = QGraphicsEllipseItem(
            QRect(
                self.ellipse_pos[0],
                self.ellipse_pos[1],
                self.radius + 1,
                self.radius + 1,
            )
        )
        if self.mode in (VIEWERMode.PAINT, VIEWERMode.ERASER):
            self.ellipse_item.setVisible(True)
        else:
            self.ellipse_item.setVisible(False)

        pen = QPen(Qt.GlobalColor.red)
        pen.setWidthF(0.5)
        self.ellipse_item.setPen(pen)

        transform = QTransform()
        transform.rotate(180)

        match self.view_mode:
            case VIEWMode.AXIAL:
                scale_x, scale_y = -self.spacing[0], -self.spacing[1]
            case VIEWMode.SAGITTAL:
                scale_x, scale_y = -self.spacing[1], self.spacing[2]
            case VIEWMode.CORONAL:
                scale_x, scale_y = -self.spacing[0], self.spacing[2]
            case _:
                raise ValueError(f"Unsupported view mode: {self.view_mode}")

        transform.scale(scale_x, scale_y)

        self.pixmap_item.setTransform(transform)
        self.ellipse_item.setTransform(transform)

        self._scene.addItem(self.pixmap_item)
        self._scene.addItem(self.ellipse_item)

        self.rect_item = None
        # Keep the fitted transform across contrast/opacity refreshes.  A
        # property change recreates the pixmap item but must not reset the
        # user's zoom baseline; MainWindow replaces it explicitly for a new
        # case or a reset.

    def remember_fit_transform(self) -> None:
        """Remember the current fitted transform as this view's zoom baseline."""

        self._fit_transform = QTransform(self.transform())

    def _image_center_uv(self) -> tuple[float, float] | None:
        pixmap = self.pixmap_item.pixmap()
        if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
            return None
        viewport_center = QPoint(self.viewport().width() // 2, self.viewport().height() // 2)
        scene_point = self.mapToScene(viewport_center)
        image_point = self.pixmap_item.mapFromScene(scene_point)
        width = max(1, pixmap.width() - 1)
        height = max(1, pixmap.height() - 1)
        return (
            max(0.0, min(1.0, image_point.x() / width)),
            max(0.0, min(1.0, image_point.y() / height)),
        )

    def view_state(self) -> dict[str, object] | None:
        """Return a view-independent pan/zoom state for sibling viewers."""

        center_uv = self._image_center_uv()
        if center_uv is None:
            return None
        fit_scale = abs(float(self._fit_transform.m11()))
        current_scale = abs(float(self.transform().m11()))
        if fit_scale < 1e-9:
            fit_scale = 1.0
        zoom = max(0.05, min(50.0, current_scale / fit_scale))
        return {"center_uv": center_uv, "zoom": zoom}

    def apply_view_state(self, state: object) -> None:
        """Apply a sibling's normalized center/zoom without emitting a loop."""

        if not isinstance(state, dict):
            return
        center_uv = state.get("center_uv")
        if (
            not isinstance(center_uv, (tuple, list))
            or len(center_uv) != 2
        ):
            return
        try:
            u = max(0.0, min(1.0, float(center_uv[0])))
            v = max(0.0, min(1.0, float(center_uv[1])))
            zoom = max(0.05, min(50.0, float(state.get("zoom", 1.0))))
        except (TypeError, ValueError, OverflowError):
            return
        pixmap = self.pixmap_item.pixmap()
        if pixmap.isNull():
            return

        target = QTransform(self._fit_transform)
        target.scale(zoom, zoom)
        self.setTransform(target)
        image_point = QPointF(
            u * max(0, pixmap.width() - 1),
            v * max(0, pixmap.height() - 1),
        )
        self.centerOn(self.pixmap_item.mapToScene(image_point))
        self.viewport().update()

    def _emit_view_state(self) -> None:
        state = self.view_state()
        if state is not None:
            self.view_state_changed.emit(state)

    def _activate(self):
        """记录最近交互的方位视图，供主窗口处理绘制和滚轮事件。"""
        if self.main_window is not None:
            self.main_window._active_viewer = self
            self.main_window.view_mode = self.view_mode

    def mousePressEvent(self, event):
        self._activate()
        super().mousePressEvent(event)
        if self.pixmap_item is not None:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position().toPoint()
                self.last_mouse_position = pos
                self.scene_pos = self.mapToScene(pos)
                self.point = self.pixmap_item.mapFromScene(self.scene_pos).toPoint()
                self.point_list = [self.point.x(), self.point.y()]
                self.ellipse_pos = [
                    self.point.x() - self.radius / 2,
                    self.point.y() - self.radius / 2,
                ]

                if self.mode == VIEWERMode.AIM:
                    self._commit_crosshair_point()

                if self.mode == VIEWERMode.SAM:
                    # 获取当前SAM模式
                    current_mode = SAMMode.BOX  # 默认BOX模式
                    if hasattr(self.main_window, "segment_setting") and hasattr(
                        self.main_window.segment_setting, "current_mode"
                    ):
                        current_mode = self.main_window.segment_setting.current_mode

                    self.setCursor(Qt.CursorShape.CrossCursor)

                    if current_mode == SAMMode.BOX:
                        # BOX模式：画框
                        self.start_point = self.pixmap_item.mapFromScene(
                            self.scene_pos
                        ).toPoint()
                        self.end_point = self.start_point
                        self.rect_item = QGraphicsRectItem(
                            QRect(self.start_point, self.end_point)
                        )
                        scale = self.transform().m11()
                        if scale < 1:
                            pen_size = 2
                        elif scale < 2:
                            pen_size = 1
                        else:
                            pen_size = 0.5
                        self.rect_item.setPen(QPen(Qt.GlobalColor.red, pen_size))
                        self.rect_item.setTransform(self.pixmap_item.transform())
                        self._scene.addItem(self.rect_item)
                    else:
                        # ADD模式：准备画点
                        self.point_item = QGraphicsEllipseItem(
                            QRect(
                                self.point.x() - 5,  # 点的半径为5
                                self.point.y() - 5,
                                10,
                                10,
                            )
                        )
                        # ADD模式用绿色点
                        self.point_item.setBrush(QColor("green"))
                        self.point_item.setTransform(self.pixmap_item.transform())
                        self._scene.addItem(self.point_item)

                if self.mode == VIEWERMode.PAINT:
                    self.draw_state = 1

                if self.mode == VIEWERMode.ERASER:
                    self.draw_state = 0

            if event.button() == Qt.MouseButton.MiddleButton:
                self.mode = VIEWERMode.MOVE
                self.cross_show = False

            if event.button() == Qt.MouseButton.RightButton:
                self.mode = VIEWERMode.ZOOM

        event.ignore()

    def mouseMoveEvent(self, event):
        self._activate()
        super().mouseMoveEvent(event)
        if self.pixmap_item is not None:
            pos = event.position().toPoint()
            self.delta = pos - self.last_mouse_position
            self.last_mouse_position = pos
            self.scene_pos = self.mapToScene(pos)
            self.point = self.pixmap_item.mapFromScene(self.scene_pos).toPoint()
            self.point_list = [self.point.x(), self.point.y()]
            self.ellipse_pos = [
                self.point.x() - self.radius / 2,
                self.point.y() - self.radius / 2,
            ]

            if self.mode == VIEWERMode.AIM and (
                event.buttons() & Qt.MouseButton.LeftButton
            ):
                self._commit_crosshair_point()

            if self.mode == VIEWERMode.MOVE and (
                event.buttons() & Qt.MouseButton.LeftButton
                or event.buttons() & Qt.MouseButton.MiddleButton
            ):
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - self.delta.x()
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - self.delta.y()
                )
                self.position[0] = pos.x()
                self.position[1] = pos.y()
                self.viewport().update()
                self._emit_view_state()

            if (
                self.mode == VIEWERMode.SAM
                and event.buttons() & Qt.MouseButton.LeftButton
            ):
                # 获取当前SAM模式
                current_mode = SAMMode.BOX  # 默认BOX模式
                if hasattr(self.main_window, "segment_setting") and hasattr(
                    self.main_window.segment_setting, "current_mode"
                ):
                    current_mode = self.main_window.segment_setting.current_mode

                if current_mode == SAMMode.BOX:
                    # BOX模式：继续画框
                    self.end_point = self.pixmap_item.mapFromScene(
                        self.scene_pos
                    ).toPoint()
                    if self.rect_item:
                        self.rect_item.setRect(
                            QRect(self.start_point, self.end_point).normalized()
                        )
                        self.input_box = np.array(
                            [
                                self.start_point.x(),
                                self.start_point.y(),
                                self.end_point.x(),
                                self.end_point.y(),
                            ]
                        )
                # ADD和SUB模式：不移动点，点在mousePressEvent时已经确定

            if self.mode == VIEWERMode.PAINT or self.mode == VIEWERMode.ERASER:
                if self.ellipse_item:
                    self.ellipse_item.setVisible(True)
                    self.ellipse_item.setRect(
                        QRect(
                            self.ellipse_pos[0],
                            self.ellipse_pos[1],
                            self.radius + 1,
                            self.radius + 1,
                        )
                    )

            if (
                self.mode == VIEWERMode.ZOOM
                and event.buttons() & Qt.MouseButton.RightButton
            ):
                scale_factor = 1.0 + (self.delta.y() / 100.0)
                scale_factor = max(0.2, min(2, scale_factor))

                self.scale(scale_factor, scale_factor)
                self._emit_view_state()

        event.ignore()

    def mouseReleaseEvent(self, event):
        self._activate()
        super().mouseReleaseEvent(event)
        if self.pixmap_item is not None:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.mode == VIEWERMode.SAM:
                    # 获取当前SAM模式
                    current_mode = SAMMode.BOX  # 默认BOX模式
                    if hasattr(self.main_window, "segment_setting") and hasattr(
                        self.main_window.segment_setting, "current_mode"
                    ):
                        current_mode = self.main_window.segment_setting.current_mode

                    self.setCursor(Qt.CursorShape.ArrowCursor)

                    if current_mode == SAMMode.BOX and np.any(self.input_box):
                        # BOX模式：发送输入框
                        self.Sam_Signal.emit(self.input_box)
                    elif current_mode == SAMMode.ADD:
                        # ADD模式：发送点坐标
                        point_coords = (self.point.x(), self.point.y())
                        self.Sam_Signal.emit(np.array(point_coords))

                    self.mode = VIEWERMode.NORMAL
            else:
                self.Mode_Signal.emit()

            if event.button() == Qt.MouseButton.MiddleButton:
                if hasattr(self.main_window, "crossline_action"):
                    if self.main_window.crossline_action.isChecked():
                        self.cross_show = True

        event.ignore()

    def wheelEvent(self, event):
        self._activate()
        event.ignore()

    def enterEvent(self, event):
        self.wheel = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.wheel = False
        super().leaveEvent(event)

    def patient_name_change(self, file_name):
        self.patient_name = file_name

    def set_crosshair_point(self, image_x, image_y):
        self.crosshair_point = QPointF(float(image_x), float(image_y))
        viewport_point = self._crosshair_viewport_point()
        if viewport_point is not None:
            self.position[0] = viewport_point.x()
            self.position[1] = viewport_point.y()
        self.viewport().update()

    def clear_crosshair_point(self):
        self.crosshair_point = None
        self.viewport().update()

    def _crosshair_viewport_point(self):
        if self.crosshair_point is None or self.pixmap_item is None:
            return None

        scene_point = self.pixmap_item.mapToScene(self.crosshair_point)
        return self.mapFromScene(scene_point)

    def _commit_crosshair_point(self):
        if hasattr(self.main_window, "update_crosshair_from_slice_point"):
            self.main_window.update_crosshair_from_slice_point(self, self.point)
        else:
            self.position[0] = self.last_mouse_position.x()
            self.position[1] = self.last_mouse_position.y()
            self.viewport().update()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        painter.save()
        painter.resetTransform()

        # 三维框 annotation 使用 IJK 作为唯一真值，由控制器投影到当前位面。
        box_controller = getattr(self.main_window, "box_controller", None)
        if box_controller is not None:
            box_controller.draw(self, painter)

        viewport_point = self._crosshair_viewport_point()
        if viewport_point is not None:
            center_x = viewport_point.x()
            center_y = viewport_point.y()
        else:
            center_x = self.position[0]
            center_y = self.position[1]

        if self.view_mode == VIEWMode.AXIAL:
            default_axes = ["R", "L", "A", "P"]
            color = ["red", "blue"]
        elif self.view_mode == VIEWMode.SAGITTAL:
            default_axes = ["A", "P", "S", "I"]
            color = ["green", "red"]
        elif self.view_mode == VIEWMode.CORONAL:
            default_axes = ["R", "L", "S", "I"]
            color = ["green", "blue"]
        else:
            default_axes = ["", "", "", ""]
            color = ["red", "blue"]

        # 方位标记由统一的 geometry 服务推导；没有加载图像时保留历史默认值。
        axes = default_axes
        direction_labels = getattr(self.main_window, "direction_labels", None)
        if direction_labels is not None:
            try:
                axes = list(direction_labels(self.view_mode))
            except Exception:
                axes = default_axes

        if self.direction_show:
            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.setPen(Qt.GlobalColor.yellow)
            margin = 10
            painter.drawText(margin, self.viewport().height() // 2 - 5, axes[0])
            painter.drawText(
                self.viewport().width() - margin - 10,
                self.viewport().height() // 2 - 5,
                axes[1],
            )
            painter.drawText(self.viewport().width() // 2 - 5, margin + 10, axes[2])
            painter.drawText(
                self.viewport().width() // 2 - 5,
                self.viewport().height() - margin,
                axes[3],
            )

        if self.information_show:
            if self.patient_name:
                font = QFont("Arial", 10, QFont.Weight.Bold)
                painter.setFont(font)
                painter.setPen(Qt.GlobalColor.green)
                painter.drawText(10, 20, self.patient_name)

        if self.cross_show:
            penx = QPen(QColor(color[0]), 1, Qt.PenStyle.DashLine)
            peny = QPen(QColor(color[1]), 1, Qt.PenStyle.DashLine)
            painter.setPen(penx)
            painter.drawLine(center_x, 20, center_x, self.viewport().height() - 20)
            painter.setPen(peny)
            painter.drawLine(20, center_y, self.viewport().width() - 20, center_y)

        painter.restore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageViewer(None, None)
    window.show()
    sys.exit(app.exec())
