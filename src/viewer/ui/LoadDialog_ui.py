# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LoadDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_LoadDialog(object):
    def setupUi(self, LoadDialog):
        if not LoadDialog.objectName():
            LoadDialog.setObjectName("LoadDialog")
        LoadDialog.resize(421, 198)
        self.verticalLayout_2 = QVBoxLayout(LoadDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.comboBox = QComboBox(LoadDialog)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName("comboBox")

        self.verticalLayout_2.addWidget(self.comboBox)

        self.stackedWidget = QStackedWidget(LoadDialog)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QWidget()
        self.page.setObjectName("page")
        self.verticalLayout = QVBoxLayout(self.page)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label = QLabel(self.page)
        self.label.setObjectName("label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.horizontalLayout_5.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(
            200, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QLineEdit(self.page)
        self.lineEdit.setObjectName("lineEdit")

        self.horizontalLayout.addWidget(self.lineEdit)

        self.btnSearch = QPushButton(self.page)
        self.btnSearch.setObjectName("btnSearch")

        self.horizontalLayout.addWidget(self.btnSearch)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QLabel(self.page)
        self.label_2.setObjectName("label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.label_2)

        self.horizontalSpacer_2 = QSpacerItem(
            200, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lineEdit_2 = QLineEdit(self.page)
        self.lineEdit_2.setObjectName("lineEdit_2")

        self.horizontalLayout_4.addWidget(self.lineEdit_2)

        self.btnSearch_2 = QPushButton(self.page)
        self.btnSearch_2.setObjectName("btnSearch_2")

        self.horizontalLayout_4.addWidget(self.btnSearch_2)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.stackedWidget.addWidget(self.page)

        self.verticalLayout_2.addWidget(self.stackedWidget)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.btnLoad = QPushButton(LoadDialog)
        self.btnLoad.setObjectName("btnLoad")

        self.horizontalLayout_6.addWidget(self.btnLoad)

        self.btnCancel = QPushButton(LoadDialog)
        self.btnCancel.setObjectName("btnCancel")

        self.horizontalLayout_6.addWidget(self.btnCancel)

        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.retranslateUi(LoadDialog)
        self.comboBox.currentIndexChanged.connect(self.stackedWidget.setCurrentIndex)

        self.stackedWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(LoadDialog)

    # setupUi

    def retranslateUi(self, LoadDialog):
        LoadDialog.setWindowTitle(
            QCoreApplication.translate("LoadDialog", "Dialog", None)
        )
        self.comboBox.setItemText(
            0, QCoreApplication.translate("LoadDialog", "NIfTI", None)
        )
        self.comboBox.setItemText(
            1, QCoreApplication.translate("LoadDialog", "DICOM/IMA", None)
        )

        self.label.setText(QCoreApplication.translate("LoadDialog", "PET", None))
        self.btnSearch.setText(
            QCoreApplication.translate("LoadDialog", "\u6d4f\u89c8", None)
        )
        self.label_2.setText(QCoreApplication.translate("LoadDialog", "CT", None))
        self.btnSearch_2.setText(
            QCoreApplication.translate("LoadDialog", "\u6d4f\u89c8", None)
        )
        self.btnLoad.setText(
            QCoreApplication.translate("LoadDialog", "\u5bfc\u5165", None)
        )
        self.btnCancel.setText(
            QCoreApplication.translate("LoadDialog", "\u53d6\u6d88", None)
        )

    # retranslateUi
