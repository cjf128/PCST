# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Viewer3d.ui'
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
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(737, 513)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer_frame = QFrame(Form)
        self.viewer_frame.setObjectName(u"viewer_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.viewer_frame.sizePolicy().hasHeightForWidth())
        self.viewer_frame.setSizePolicy(sizePolicy)
        self.viewer_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.viewer_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.viewer_frame)

        self.frame_6 = QFrame(Form)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setMinimumSize(QSize(30, 0))
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer)

        self.btnRefresh = QPushButton(self.frame_6)
        self.btnRefresh.setObjectName(u"btnRefresh")

        self.horizontalLayout_7.addWidget(self.btnRefresh)

        self.btnReset = QPushButton(self.frame_6)
        self.btnReset.setObjectName(u"btnReset")
        icon = QIcon()
        icon.addFile(u":/icons/icons/fix_light.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnReset.setIcon(icon)

        self.horizontalLayout_7.addWidget(self.btnReset)


        self.verticalLayout.addWidget(self.frame_6)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.btnRefresh.setText(QCoreApplication.translate("Form", u"\u5237\u65b0", None))
        self.btnReset.setText(QCoreApplication.translate("Form", u"\u590d\u4f4d", None))
    # retranslateUi

