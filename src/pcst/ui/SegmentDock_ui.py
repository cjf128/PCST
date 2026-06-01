# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SegmentDock.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(263, 435)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 259, 431))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_15 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_15.setSpacing(2)
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.tableWidget = QTableWidget(self.groupBox_3)
        if self.tableWidget.columnCount() < 2:
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget.setObjectName("tableWidget")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setMinimumSize(QSize(0, 120))

        self.verticalLayout_15.addWidget(self.tableWidget)

        self.frame = QFrame(self.groupBox_3)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.frame)
        self.pushButton.setObjectName("pushButton")

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.frame)
        self.pushButton_2.setObjectName("pushButton_2")

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.verticalLayout_15.addWidget(self.frame)

        self.verticalLayout_2.addWidget(self.groupBox_3)

        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_14 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_14.setSpacing(2)
        self.verticalLayout_14.setObjectName("verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(2, 2, 2, 2)
        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName("label")

        self.verticalLayout_14.addWidget(self.label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.sldPaint = QSlider(self.groupBox_2)
        self.sldPaint.setObjectName("sldPaint")
        self.sldPaint.setMinimum(1)
        self.sldPaint.setMaximum(30)
        self.sldPaint.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_2.addWidget(self.sldPaint)

        self.boxPaint = QSpinBox(self.groupBox_2)
        self.boxPaint.setObjectName("boxPaint")
        self.boxPaint.setMinimumSize(QSize(60, 0))
        self.boxPaint.setMaximumSize(QSize(100, 16777215))
        self.boxPaint.setMinimum(1)
        self.boxPaint.setMaximum(30)

        self.horizontalLayout_2.addWidget(self.boxPaint)

        self.verticalLayout_14.addLayout(self.horizontalLayout_2)

        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName("label_9")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy1)

        self.verticalLayout_14.addWidget(self.label_9)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.sldAlphaSeg = QSlider(self.groupBox_2)
        self.sldAlphaSeg.setObjectName("sldAlphaSeg")
        self.sldAlphaSeg.setMaximum(100)
        self.sldAlphaSeg.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_12.addWidget(self.sldAlphaSeg)

        self.boxAlphaSeg = QDoubleSpinBox(self.groupBox_2)
        self.boxAlphaSeg.setObjectName("boxAlphaSeg")
        self.boxAlphaSeg.setMinimumSize(QSize(100, 0))
        self.boxAlphaSeg.setMaximumSize(QSize(100, 16777215))
        self.boxAlphaSeg.setDecimals(2)
        self.boxAlphaSeg.setMaximum(1.000000000000000)
        self.boxAlphaSeg.setSingleStep(0.010000000000000)

        self.horizontalLayout_12.addWidget(self.boxAlphaSeg)

        self.verticalLayout_14.addLayout(self.horizontalLayout_12)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")

        self.verticalLayout_14.addWidget(self.label_2)

        self.frame_2 = QFrame(self.groupBox_2)
        self.frame_2.setObjectName("frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.pushButton_4 = QPushButton(self.frame_2)
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.setCheckable(True)

        self.horizontalLayout_3.addWidget(self.pushButton_4)

        self.pushButton_3 = QPushButton(self.frame_2)
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.setCheckable(True)
        self.pushButton_3.setChecked(True)
        self.pushButton_3.setAutoDefault(False)
        self.pushButton_3.setFlat(False)

        self.horizontalLayout_3.addWidget(self.pushButton_3)

        self.verticalLayout_14.addWidget(self.frame_2)

        self.verticalLayout_2.addWidget(self.groupBox_2)

        self.verticalSpacer = QSpacerItem(
            20, 150, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(Form)
        self.sldPaint.valueChanged.connect(self.boxPaint.setValue)
        self.boxPaint.valueChanged.connect(self.sldPaint.setValue)

        QMetaObject.connectSlotsByName(Form)

    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.groupBox_3.setTitle(
            QCoreApplication.translate("Form", "\u9009\u62e9", None)
        )
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(
            QCoreApplication.translate("Form", "\u6807\u7b7e\u540d", None)
        )
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(
            QCoreApplication.translate("Form", "\u989c\u8272", None)
        )
        self.pushButton.setText(
            QCoreApplication.translate("Form", "\u589e\u52a0", None)
        )
        self.pushButton_2.setText(
            QCoreApplication.translate("Form", "\u5220\u9664", None)
        )
        self.groupBox_2.setTitle(
            QCoreApplication.translate("Form", "\u8bbe\u7f6e", None)
        )
        self.label.setText(
            QCoreApplication.translate("Form", "\u7b14\u5237\u5927\u5c0f", None)
        )
        self.label_9.setText(
            QCoreApplication.translate("Form", "\u900f\u660e\u5ea6\uff1a  ", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("Form", "SAM\u63d0\u793a", None)
        )
        self.pushButton_4.setText("")
        self.pushButton_3.setText("")

    # retranslateUi
