# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ShortcutDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QVBoxLayout,
)


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(605, 230)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame_10 = QFrame(Dialog)
        self.frame_10.setObjectName("frame_10")
        self.frame_10.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_10.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frame_10)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(6, 6, 6, 6)
        self.frame = QFrame(self.frame_10)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.frame)
        self.label.setObjectName("label")

        self.horizontalLayout.addWidget(self.label)

        self.load_Edit = QKeySequenceEdit(self.frame)
        self.load_Edit.setObjectName("load_Edit")

        self.horizontalLayout.addWidget(self.load_Edit)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.frame_6 = QFrame(self.frame_10)
        self.frame_6.setObjectName("frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.frame_6)
        self.label_6.setObjectName("label_6")

        self.horizontalLayout_6.addWidget(self.label_6)

        self.aim_edit = QKeySequenceEdit(self.frame_6)
        self.aim_edit.setObjectName("aim_edit")

        self.horizontalLayout_6.addWidget(self.aim_edit)

        self.gridLayout.addWidget(self.frame_6, 0, 1, 1, 1)

        self.frame_9 = QFrame(self.frame_10)
        self.frame_9.setObjectName("frame_9")
        self.frame_9.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_9.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame_9)
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_9 = QLabel(self.frame_9)
        self.label_9.setObjectName("label_9")

        self.horizontalLayout_9.addWidget(self.label_9)

        self.paint_Edit = QKeySequenceEdit(self.frame_9)
        self.paint_Edit.setObjectName("paint_Edit")

        self.horizontalLayout_9.addWidget(self.paint_Edit)

        self.gridLayout.addWidget(self.frame_9, 0, 2, 1, 1)

        self.frame_2 = QFrame(self.frame_10)
        self.frame_2.setObjectName("frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName("label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.add_Edit = QKeySequenceEdit(self.frame_2)
        self.add_Edit.setObjectName("add_Edit")

        self.horizontalLayout_2.addWidget(self.add_Edit)

        self.gridLayout.addWidget(self.frame_2, 1, 0, 1, 1)

        self.frame_5 = QFrame(self.frame_10)
        self.frame_5.setObjectName("frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_5)
        self.label_5.setObjectName("label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.move_Edit = QKeySequenceEdit(self.frame_5)
        self.move_Edit.setObjectName("move_Edit")

        self.horizontalLayout_5.addWidget(self.move_Edit)

        self.gridLayout.addWidget(self.frame_5, 1, 1, 1, 1)

        self.frame_8 = QFrame(self.frame_10)
        self.frame_8.setObjectName("frame_8")
        self.frame_8.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_8 = QLabel(self.frame_8)
        self.label_8.setObjectName("label_8")

        self.horizontalLayout_8.addWidget(self.label_8)

        self.eraser_Edit = QKeySequenceEdit(self.frame_8)
        self.eraser_Edit.setObjectName("eraser_Edit")

        self.horizontalLayout_8.addWidget(self.eraser_Edit)

        self.gridLayout.addWidget(self.frame_8, 1, 2, 1, 1)

        self.frame_3 = QFrame(self.frame_10)
        self.frame_3.setObjectName("frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame_3)
        self.label_3.setObjectName("label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.save_Edit = QKeySequenceEdit(self.frame_3)
        self.save_Edit.setObjectName("save_Edit")

        self.horizontalLayout_3.addWidget(self.save_Edit)

        self.gridLayout.addWidget(self.frame_3, 2, 0, 1, 1)

        self.frame_4 = QFrame(self.frame_10)
        self.frame_4.setObjectName("frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.frame_4)
        self.label_4.setObjectName("label_4")

        self.horizontalLayout_4.addWidget(self.label_4)

        self.win_Edit = QKeySequenceEdit(self.frame_4)
        self.win_Edit.setObjectName("win_Edit")

        self.horizontalLayout_4.addWidget(self.win_Edit)

        self.gridLayout.addWidget(self.frame_4, 2, 1, 1, 1)

        self.frame_7 = QFrame(self.frame_10)
        self.frame_7.setObjectName("frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.frame_7)
        self.label_7.setObjectName("label_7")

        self.horizontalLayout_7.addWidget(self.label_7)

        self.SAM_Edit = QKeySequenceEdit(self.frame_7)
        self.SAM_Edit.setObjectName("SAM_Edit")

        self.horizontalLayout_7.addWidget(self.SAM_Edit)

        self.gridLayout.addWidget(self.frame_7, 2, 2, 1, 1)

        self.verticalLayout.addWidget(self.frame_10)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )

        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.label.setText(
            QCoreApplication.translate("Dialog", "\u5bfc\u5165\u6570\u636e", None)
        )
        self.load_Edit.setKeySequence(
            QCoreApplication.translate("Dialog", "Ctrl+O", None)
        )
        self.label_6.setText(
            QCoreApplication.translate("Dialog", "\u51c6\u5fc3\u5de5\u5177", None)
        )
        self.label_9.setText(
            QCoreApplication.translate("Dialog", "\u6807\u6ce8\u5de5\u5177", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("Dialog", "\u5bfc\u5165\u6807\u6ce8", None)
        )
        self.add_Edit.setKeySequence(
            QCoreApplication.translate("Dialog", "Ctrl+A", None)
        )
        self.label_5.setText(
            QCoreApplication.translate("Dialog", "\u79fb\u52a8\u5de5\u5177", None)
        )
        self.label_8.setText(
            QCoreApplication.translate("Dialog", "\u64e6\u9664\u5de5\u5177", None)
        )
        self.label_3.setText(
            QCoreApplication.translate("Dialog", "\u4fdd\u5b58\u6587\u4ef6", None)
        )
        self.save_Edit.setKeySequence(
            QCoreApplication.translate("Dialog", "Ctrl+S", None)
        )
        self.label_4.setText(
            QCoreApplication.translate("Dialog", "\u8c03\u7a97\u5de5\u5177", None)
        )
        self.label_7.setText(
            QCoreApplication.translate("Dialog", "SAM\u5de5\u5177", None)
        )

    # retranslateUi
