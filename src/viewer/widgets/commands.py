from __future__ import annotations

from PySide6.QtGui import QUndoCommand


class SegChangeCommand(QUndoCommand):
    def __init__(self, parent, layer, old_slice, new_slice, description="修改标签"):
        super().__init__(description)
        self.parent = parent
        self.layer = layer
        # 只保存当前层的 2D 切片，降低内存与拷贝开销
        self.old_slice = old_slice.copy() if old_slice is not None else None
        self.new_slice = new_slice.copy()

    def redo(self):
        """重做：将数据设为新值，并更新 UI"""
        self.parent.seg[:, :, self.layer] = self.new_slice
        self.parent.update_all()

    def undo(self):
        """撤销：恢复为旧值，并更新 UI"""
        if self.old_slice is not None:
            self.parent.seg[:, :, self.layer] = self.old_slice
            self.parent.update_all()
