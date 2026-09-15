# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ViewerBase.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QPushButton,
    QScrollBar, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(622, 410)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.boxLayer = QSpinBox(self.frame)
        self.boxLayer.setObjectName(u"boxLayer")
        self.boxLayer.setMaximum(200)

        self.horizontalLayout.addWidget(self.boxLayer)

        self.sldLayer = QScrollBar(self.frame)
        self.sldLayer.setObjectName(u"sldLayer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sldLayer.sizePolicy().hasHeightForWidth())
        self.sldLayer.setSizePolicy(sizePolicy)
        self.sldLayer.setMaximum(200)
        self.sldLayer.setValue(100)
        self.sldLayer.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout.addWidget(self.sldLayer)

        self.btnCa = QPushButton(self.frame)
        self.btnCa.setObjectName(u"btnCa")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnCa.sizePolicy().hasHeightForWidth())
        self.btnCa.setSizePolicy(sizePolicy1)
        self.btnCa.setMinimumSize(QSize(28, 28))
        self.btnCa.setMaximumSize(QSize(16777215, 16777215))
        self.btnCa.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnCa.setAutoRepeatDelay(300)

        self.horizontalLayout.addWidget(self.btnCa)


        self.verticalLayout.addWidget(self.frame)

        self.image_frame = QFrame(Form)
        self.image_frame.setObjectName(u"image_frame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.image_frame.sizePolicy().hasHeightForWidth())
        self.image_frame.setSizePolicy(sizePolicy2)
        self.image_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.image_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.image_frame)


        self.retranslateUi(Form)
        self.boxLayer.valueChanged.connect(self.sldLayer.setValue)
        self.sldLayer.valueChanged.connect(self.boxLayer.setValue)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.btnCa.setText(QCoreApplication.translate("Form", u"\u622a\u56fe", None))
    # retranslateUi

