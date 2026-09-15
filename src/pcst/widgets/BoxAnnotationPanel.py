"""三维框 annotation 列表面板。

面板只负责把文档内容映射到 Qt 表格；IJK/KJI/LPS 的转换仍由 core
``CoordinateService`` 和 ``AnnotationDocument`` 负责。框的真实几何不会因
显示的“终点 voxel（包含）”文本而改变。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BoxAnnotationPanel(QWidget):
    """显示、选择和编辑当前病例的 3D AABB annotation。"""

    _HEADERS = ("框 ID", "类别", "病灶 ID", "起点 IJK", "终点 IJK（含）")

    def __init__(self, main_window, controller, parent=None) -> None:
        super().__init__(parent)
        self.main_window = main_window
        self.controller = controller
        self._updating_table = False

        group = QGroupBox("三维框标注", self)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(2, 2, 2, 2)

        self.table = QTableWidget(group)
        self.table.setColumnCount(len(self._HEADERS))
        self.table.setHorizontalHeaderLabels(list(self._HEADERS))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.SelectedClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.setMinimumHeight(130)
        self.table.setAlternatingRowColors(True)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        group_layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.btn_delete = QPushButton("删除框", group)
        self.btn_new_lesion = QPushButton("新建病灶", group)
        self.btn_relation = QPushButton("包含关系", group)
        self.btn_delete.clicked.connect(self.controller.delete_selected)
        self.btn_new_lesion.clicked.connect(self._new_lesion)
        self.btn_relation.clicked.connect(self._set_contained_relation)
        buttons.addWidget(self.btn_delete)
        buttons.addWidget(self.btn_new_lesion)
        buttons.addWidget(self.btn_relation)
        group_layout.addLayout(buttons)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(group)

        self.controller.selection_changed.connect(self._on_controller_selection)
        self.controller.boxes_changed.connect(self.refresh)

    def refresh(self) -> None:
        document = getattr(self.controller, "document", None)
        annotations = list(document.annotations) if document is not None else []
        self._updating_table = True
        try:
            self.table.setRowCount(0)
            for row, annotation in enumerate(annotations):
                self.table.insertRow(row)
                values = (
                    annotation.id,
                    str(annotation.class_id),
                    annotation.lesion_id or "",
                    ", ".join(str(value) for value in annotation.geometry.min_ijk),
                    ", ".join(
                        str(value - 1)
                        for value in annotation.geometry.max_ijk_exclusive
                    ),
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, annotation.id)
                    if column in (0, 3, 4):
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if column == 0:
                        item.setToolTip(annotation.id)
                    if column == 4:
                        item.setToolTip(
                            "医生视图显示包含的最后 voxel；内部使用 max_ijk_exclusive"
                        )
                    self.table.setItem(row, column, item)
            self.table.resizeColumnsToContents()
            if self.table.columnWidth(0) > 160:
                self.table.setColumnWidth(0, 160)
        finally:
            self._updating_table = False
        self._on_controller_selection(getattr(self.controller, "selected_id", None))

    def _row_annotation_id(self, row: int) -> str | None:
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else item.text() or None

    def _on_selection_changed(self) -> None:
        if self._updating_table:
            return
        rows = self.table.selectionModel().selectedRows()
        if rows:
            annotation_id = self._row_annotation_id(rows[0].row())
            if annotation_id:
                # 从列表选择时把三个正交面的当前层同步到框中心，
                # 让选中的框立即在各面可见；点击视图中的框仍保持原地选择。
                self.controller.select(annotation_id, center=True)

    def _on_controller_selection(self, annotation_id) -> None:
        target = None if annotation_id is None else str(annotation_id)
        self._updating_table = True
        try:
            self.table.clearSelection()
            if target is not None:
                for row in range(self.table.rowCount()):
                    if self._row_annotation_id(row) == target:
                        self.table.selectRow(row)
                        break
        finally:
            self._updating_table = False

    def _on_cell_changed(self, row: int, column: int) -> None:
        if self._updating_table:
            return
        annotation_id = self._row_annotation_id(row)
        item = self.table.item(row, column)
        if annotation_id is None or item is None:
            return
        if column == 1:
            try:
                class_id = int(item.text().strip())
            except ValueError:
                self.refresh()
                return
            if not self.controller.set_annotation_class(annotation_id, class_id):
                self.refresh()
        elif column == 2:
            lesion_id = item.text().strip() or None
            if not self.controller.set_annotation_lesion_id(annotation_id, lesion_id):
                self.refresh()

    def _new_lesion(self) -> None:
        annotation_id = getattr(self.controller, "selected_id", None)
        if annotation_id is None:
            return
        current = ""
        if self.controller.document is not None:
            try:
                current = self.controller.document.get(annotation_id).lesion_id or ""
            except KeyError:
                return
        value, accepted = QInputDialog.getText(
            self,
            "设置病灶 ID",
            "病灶 ID（留空将自动生成）：",
            text=current,
        )
        if not accepted:
            return
        if not value.strip():
            from uuid import uuid4

            value = f"lesion_{uuid4().hex[:12]}"
        self.controller.set_annotation_lesion_id(annotation_id, value.strip())

    def _set_contained_relation(self) -> None:
        annotation_id = getattr(self.controller, "selected_id", None)
        document = getattr(self.controller, "document", None)
        if annotation_id is None or document is None:
            return
        lesion_ids = sorted(
            {
                annotation.lesion_id
                for annotation in document.annotations
                if annotation.lesion_id and annotation.id != annotation_id
            }
        )
        value, accepted = QInputDialog.getItem(
            self,
            "设置包含关系",
            "目标 lesion_id（取消表示清除关系）：",
            lesion_ids,
            editable=True,
        )
        if not accepted:
            return
        if not value.strip():
            if not self.controller.set_annotation_relations(annotation_id, []):
                self.refresh()
        else:
            from pcst.core.annotations import Relation

            if not self.controller.set_annotation_relations(
                annotation_id,
                [Relation("contained_in", value.strip())],
            ):
                self.refresh()
