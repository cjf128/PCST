from __future__ import annotations

from PySide6.QtGui import QUndoCommand

from pcst.core.annotations import Annotation3D, AnnotationDocument


class SegChangeCommand(QUndoCommand):
    def __init__(
        self,
        parent,
        view_mode,
        layer,
        old_slice,
        new_slice,
        description="修改标签",
    ):
        super().__init__(description)
        self.parent = parent
        self.view_mode = view_mode
        self.layer = layer
        # 只保存当前层的 2D 切片，降低内存与拷贝开销
        self.old_slice = old_slice.copy() if old_slice is not None else None
        self.new_slice = new_slice.copy()

    def redo(self):
        """重做：将数据设为新值，并更新 UI"""
        self.parent._set_volume_slice(
            self.parent.seg, self.view_mode, self.layer, self.new_slice
        )
        self.parent.update_all()
        self.parent.request_3d_refresh()

    def undo(self):
        """撤销：恢复为旧值，并更新 UI"""
        if self.old_slice is not None:
            self.parent._set_volume_slice(
                self.parent.seg, self.view_mode, self.layer, self.old_slice
            )
            self.parent.update_all()
            self.parent.request_3d_refresh()


def _notify_box_controller(controller) -> None:
    if controller is None:
        return
    controller.boxes_changed.emit()
    controller.update_viewports()


class AddBoxCommand(QUndoCommand):
    """新增一个独立 3D annotation。允许与已有框完全重叠。"""

    def __init__(self, document: AnnotationDocument, annotation: Annotation3D, controller=None):
        super().__init__("新增三维框")
        self.document = document
        self.annotation = annotation.copy()
        self.controller = controller

    def redo(self):
        if not any(item.id == self.annotation.id for item in self.document.annotations):
            self.document.add(self.annotation.copy())
        _notify_box_controller(self.controller)

    def undo(self):
        try:
            self.document.remove(self.annotation.id)
        except KeyError:
            pass
        _notify_box_controller(self.controller)


class UpdateBoxCommand(QUndoCommand):
    """一次拖动产生一条更新命令，避免每个鼠标移动都进入撤销栈。"""

    def __init__(
        self,
        document: AnnotationDocument,
        before: Annotation3D,
        after: Annotation3D,
        controller=None,
    ):
        super().__init__("修改三维框")
        self.document = document
        self.before = before.copy()
        self.after = after.copy()
        self.controller = controller

    def redo(self):
        self.document.update(self.after.copy())
        _notify_box_controller(self.controller)

    def undo(self):
        self.document.update(self.before.copy())
        _notify_box_controller(self.controller)


class DeleteBoxCommand(QUndoCommand):
    """删除一个 annotation，不影响相同 lesion_id 的其他框。"""

    def __init__(self, document: AnnotationDocument, annotation: Annotation3D, controller=None):
        super().__init__("删除三维框")
        self.document = document
        self.annotation = annotation.copy()
        self.controller = controller

    def redo(self):
        try:
            self.document.remove(self.annotation.id)
        except KeyError:
            pass
        _notify_box_controller(self.controller)

    def undo(self):
        if not any(item.id == self.annotation.id for item in self.document.annotations):
            self.document.add(self.annotation.copy())
        _notify_box_controller(self.controller)
