# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QMenu,
    QMenuBar,
    QPushButton,
    QScrollBar,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1276, 882)
        MainWindow.setMinimumSize(QSize(0, 0))
        MainWindow.setAnimated(True)
        self.setting_atn = QAction(MainWindow)
        self.setting_atn.setObjectName("setting_atn")
        self.setting_atn.setCheckable(True)
        self.setting_atn.setChecked(True)
        icon = QIcon()
        icon.addFile(
            ":/iocns/icons/setting_dark.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.setting_atn.setIcon(icon)
        self.load_atn = QAction(MainWindow)
        self.load_atn.setObjectName("load_atn")
        icon1 = QIcon()
        icon1.addFile(
            ":/iocns/icons/openfile_dark.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.load_atn.setIcon(icon1)
        self.load_atn.setMenuRole(QAction.MenuRole.NoRole)
        self.load_atn.setIconVisibleInMenu(True)
        self.save_atn = QAction(MainWindow)
        self.save_atn.setObjectName("save_atn")
        icon2 = QIcon()
        icon2.addFile(
            ":/iocns/icons/save_dark.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.save_atn.setIcon(icon2)
        self.move_atn = QAction(MainWindow)
        self.move_atn.setObjectName("move_atn")
        self.move_atn.setCheckable(True)
        self.move_atn.setChecked(False)
        self.win_atn = QAction(MainWindow)
        self.win_atn.setObjectName("win_atn")
        self.win_atn.setCheckable(True)
        self.paint_atn = QAction(MainWindow)
        self.paint_atn.setObjectName("paint_atn")
        self.paint_atn.setCheckable(True)
        self.eraser_atn = QAction(MainWindow)
        self.eraser_atn.setObjectName("eraser_atn")
        self.eraser_atn.setCheckable(True)
        self.exit_action = QAction(MainWindow)
        self.exit_action.setObjectName("exit_action")
        self.save_action = QAction(MainWindow)
        self.save_action.setObjectName("save_action")
        self.open_action = QAction(MainWindow)
        self.open_action.setObjectName("open_action")
        self.sam_atn = QAction(MainWindow)
        self.sam_atn.setObjectName("sam_atn")
        self.sam_atn.setCheckable(True)
        self.file_action = QAction(MainWindow)
        self.file_action.setObjectName("file_action")
        self.file_action.setCheckable(True)
        self.file_action.setChecked(True)
        self.paint_action = QAction(MainWindow)
        self.paint_action.setObjectName("paint_action")
        self.paint_action.setCheckable(True)
        self.paint_action.setChecked(True)
        self.aim_atn = QAction(MainWindow)
        self.aim_atn.setObjectName("aim_atn")
        self.aim_atn.setCheckable(True)
        self.aim_atn.setChecked(False)
        self.crossline_action = QAction(MainWindow)
        self.crossline_action.setObjectName("crossline_action")
        self.crossline_action.setCheckable(True)
        self.crossline_action.setChecked(False)
        self.redo_atn = QAction(MainWindow)
        self.redo_atn.setObjectName("redo_atn")
        self.add_action = QAction(MainWindow)
        self.add_action.setObjectName("add_action")
        self.add_atn = QAction(MainWindow)
        self.add_atn.setObjectName("add_atn")
        self.add_atn.setMenuRole(QAction.MenuRole.NoRole)
        self.imageseting_action = QAction(MainWindow)
        self.imageseting_action.setObjectName("imageseting_action")
        self.imageseting_action.setCheckable(True)
        self.imageseting_action.setChecked(True)
        self.segmentsetting_action = QAction(MainWindow)
        self.segmentsetting_action.setObjectName("segmentsetting_action")
        self.segmentsetting_action.setCheckable(True)
        self.segmentsetting_action.setChecked(True)
        self.info_action = QAction(MainWindow)
        self.info_action.setObjectName("info_action")
        self.info_action.setCheckable(True)
        self.info_action.setChecked(True)
        self.dark_action = QAction(MainWindow)
        self.dark_action.setObjectName("dark_action")
        self.dark_action.setCheckable(True)
        self.dark_action.setChecked(True)
        self.light_action = QAction(MainWindow)
        self.light_action.setObjectName("light_action")
        self.light_action.setCheckable(True)
        self.filesetting_action = QAction(MainWindow)
        self.filesetting_action.setObjectName("filesetting_action")
        self.filesetting_action.setCheckable(True)
        self.filesetting_action.setChecked(True)
        self.data_atn = QAction(MainWindow)
        self.data_atn.setObjectName("data_atn")
        self.data_atn.setCheckable(True)
        self.data_atn.setChecked(True)
        self.data_atn.setMenuRole(QAction.MenuRole.NoRole)
        self.about_action = QAction(MainWindow)
        self.about_action.setObjectName("about_action")
        self.github_action = QAction(MainWindow)
        self.github_action.setObjectName("github_action")
        self.actionhelp = QAction(MainWindow)
        self.actionhelp.setObjectName("actionhelp")
        self.direction_action = QAction(MainWindow)
        self.direction_action.setObjectName("direction_action")
        self.direction_action.setCheckable(True)
        self.direction_action.setChecked(True)
        self.information_action = QAction(MainWindow)
        self.information_action.setObjectName("information_action")
        self.information_action.setCheckable(True)
        self.information_action.setChecked(True)
        self.shortcut_action = QAction(MainWindow)
        self.shortcut_action.setObjectName("shortcut_action")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_5 = QFrame(self.centralwidget)
        self.frame_5.setObjectName("frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_5)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.frame_5)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame_2 = QFrame(self.splitter)
        self.frame_2.setObjectName("frame_2")
        self.frame_2.setMinimumSize(QSize(600, 0))
        self.frame_2.setMaximumSize(QSize(16777215, 16777215))
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_13 = QVBoxLayout(self.frame_2)
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.frame_2)
        self.frame_3.setObjectName("frame_3")
        self.frame_3.setMinimumSize(QSize(0, 0))
        self.frame_3.setMaximumSize(QSize(16777215, 16777215))
        self.frame_3.setStyleSheet("")
        self.horizontalLayout_3 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.boxPET = QCheckBox(self.frame_3)
        self.boxPET.setObjectName("boxPET")
        self.boxPET.setChecked(True)

        self.horizontalLayout_3.addWidget(self.boxPET)

        self.boxCT = QCheckBox(self.frame_3)
        self.boxCT.setObjectName("boxCT")
        self.boxCT.setChecked(True)

        self.horizontalLayout_3.addWidget(self.boxCT)

        self.boxSeg = QCheckBox(self.frame_3)
        self.boxSeg.setObjectName("boxSeg")
        self.boxSeg.setChecked(True)

        self.horizontalLayout_3.addWidget(self.boxSeg)

        self.sldLayer = QScrollBar(self.frame_3)
        self.sldLayer.setObjectName("sldLayer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sldLayer.sizePolicy().hasHeightForWidth())
        self.sldLayer.setSizePolicy(sizePolicy)
        self.sldLayer.setMaximum(200)
        self.sldLayer.setValue(100)
        self.sldLayer.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_3.addWidget(self.sldLayer)

        self.boxLayer = QSpinBox(self.frame_3)
        self.boxLayer.setObjectName("boxLayer")
        self.boxLayer.setMaximum(200)

        self.horizontalLayout_3.addWidget(self.boxLayer)

        self.btnCa = QPushButton(self.frame_3)
        self.btnCa.setObjectName("btnCa")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnCa.sizePolicy().hasHeightForWidth())
        self.btnCa.setSizePolicy(sizePolicy1)
        self.btnCa.setMinimumSize(QSize(28, 28))
        self.btnCa.setMaximumSize(QSize(16777215, 16777215))
        self.btnCa.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnCa.setAutoRepeatDelay(300)

        self.horizontalLayout_3.addWidget(self.btnCa)

        self.verticalLayout_13.addWidget(self.frame_3)

        self.stackedWidget = QStackedWidget(self.frame_2)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QWidget()
        self.page.setObjectName("page")
        self.verticalLayout_2 = QVBoxLayout(self.page)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.image_frame = QFrame(self.page)
        self.image_frame.setObjectName("image_frame")
        self.image_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.image_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout_2.addWidget(self.image_frame)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName("page_2")
        self.verticalLayout_5 = QVBoxLayout(self.page_2)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.view_frame = QFrame(self.page_2)
        self.view_frame.setObjectName("view_frame")
        self.view_frame.setStyleSheet("")
        self.view_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.view_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout_5.addWidget(self.view_frame)

        self.stackedWidget.addWidget(self.page_2)

        self.verticalLayout_13.addWidget(self.stackedWidget)

        self.frame_6 = QFrame(self.frame_2)
        self.frame_6.setObjectName("frame_6")
        self.frame_6.setMinimumSize(QSize(30, 0))
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.btnH = QPushButton(self.frame_6)
        self.btnH.setObjectName("btnH")
        self.btnH.setMaximumSize(QSize(48, 32))
        self.btnH.setCheckable(True)
        self.btnH.setChecked(False)

        self.horizontalLayout_7.addWidget(self.btnH)

        self.btnS = QPushButton(self.frame_6)
        self.btnS.setObjectName("btnS")
        self.btnS.setMaximumSize(QSize(48, 32))
        self.btnS.setCheckable(True)

        self.horizontalLayout_7.addWidget(self.btnS)

        self.btnG = QPushButton(self.frame_6)
        self.btnG.setObjectName("btnG")
        self.btnG.setMaximumSize(QSize(48, 32))
        self.btnG.setCheckable(True)

        self.horizontalLayout_7.addWidget(self.btnG)

        self.btn3D = QPushButton(self.frame_6)
        self.btn3D.setObjectName("btn3D")
        self.btn3D.setMaximumSize(QSize(32, 32))
        self.btn3D.setCheckable(True)

        self.horizontalLayout_7.addWidget(self.btn3D)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_7.addItem(self.horizontalSpacer)

        self.btnRefresh = QPushButton(self.frame_6)
        self.btnRefresh.setObjectName("btnRefresh")

        self.horizontalLayout_7.addWidget(self.btnRefresh)

        self.btnReset = QPushButton(self.frame_6)
        self.btnReset.setObjectName("btnReset")
        icon3 = QIcon()
        icon3.addFile(
            ":/icons/icons/fix_light.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.btnReset.setIcon(icon3)

        self.horizontalLayout_7.addWidget(self.btnReset)

        self.verticalLayout_13.addWidget(self.frame_6)

        self.splitter.addWidget(self.frame_2)

        self.horizontalLayout.addWidget(self.splitter)

        self.verticalLayout.addWidget(self.frame_5)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1276, 33))
        self.muFile = QMenu(self.menuBar)
        self.muFile.setObjectName("muFile")
        self.muView = QMenu(self.menuBar)
        self.muView.setObjectName("muView")
        self.menu_3 = QMenu(self.muView)
        self.menu_3.setObjectName("menu_3")
        self.menu = QMenu(self.menuBar)
        self.menu.setObjectName("menu")
        self.menutheme = QMenu(self.menu)
        self.menutheme.setObjectName("menutheme")
        MainWindow.setMenuBar(self.menuBar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setMinimumSize(QSize(32, 0))
        self.toolBar.setMovable(False)
        MainWindow.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar_file = QToolBar(MainWindow)
        self.toolBar_file.setObjectName("toolBar_file")
        self.toolBar_file.setMinimumSize(QSize(0, 0))
        self.toolBar_file.setMovable(False)
        self.toolBar_file.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar_file)
        self.toolBar_draw = QToolBar(MainWindow)
        self.toolBar_draw.setObjectName("toolBar_draw")
        self.toolBar_draw.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar_draw)
        self.toolBar_run = QToolBar(MainWindow)
        self.toolBar_run.setObjectName("toolBar_run")
        self.toolBar_run.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar_run)
        self.dockWidget = QDockWidget(MainWindow)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidget.setMinimumSize(QSize(230, 39))
        self.dockWidget.setMaximumSize(QSize(500, 524287))
        self.dockWidget.setFloating(False)
        self.dockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidget.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.dockWidgetContents.sizePolicy().hasHeightForWidth()
        )
        self.dockWidgetContents.setSizePolicy(sizePolicy2)
        self.verticalLayout_4 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.ImageSetting = QWidget(self.dockWidgetContents)
        self.ImageSetting.setObjectName("ImageSetting")

        self.verticalLayout_4.addWidget(self.ImageSetting)

        self.dockWidget.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidget)
        self.dockWidget_4 = QDockWidget(MainWindow)
        self.dockWidget_4.setObjectName("dockWidget_4")
        self.dockWidget_4.setMinimumSize(QSize(230, 39))
        self.dockWidget_4.setMaximumSize(QSize(500, 524287))
        self.dockWidget_4.setFloating(False)
        self.dockWidget_4.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidget_4.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockWidget_4.setDockLocation(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dockWidgetContents_4 = QWidget()
        self.dockWidgetContents_4.setObjectName("dockWidgetContents_4")
        self.verticalLayout_7 = QVBoxLayout(self.dockWidgetContents_4)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.InfoSetting = QWidget(self.dockWidgetContents_4)
        self.InfoSetting.setObjectName("InfoSetting")
        self.InfoSetting.setMinimumSize(QSize(0, 0))
        self.verticalLayout_9 = QVBoxLayout(self.InfoSetting)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_7.addWidget(self.InfoSetting)

        self.dockWidget_4.setWidget(self.dockWidgetContents_4)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidget_4
        )
        self.dockWidget_2 = QDockWidget(MainWindow)
        self.dockWidget_2.setObjectName("dockWidget_2")
        self.dockWidget_2.setMinimumSize(QSize(230, 39))
        self.dockWidget_2.setMaximumSize(QSize(500, 524287))
        self.dockWidget_2.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidget_2.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout_8 = QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.FileSetting = QWidget(self.dockWidgetContents_2)
        self.FileSetting.setObjectName("FileSetting")

        self.verticalLayout_8.addWidget(self.FileSetting)

        self.dockWidget_2.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget_2
        )
        self.dockWidget_3 = QDockWidget(MainWindow)
        self.dockWidget_3.setObjectName("dockWidget_3")
        sizePolicy2.setHeightForWidth(
            self.dockWidget_3.sizePolicy().hasHeightForWidth()
        )
        self.dockWidget_3.setSizePolicy(sizePolicy2)
        self.dockWidget_3.setMinimumSize(QSize(230, 39))
        self.dockWidget_3.setMaximumSize(QSize(500, 524287))
        self.dockWidget_3.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidget_3.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockWidgetContents_5 = QWidget()
        self.dockWidgetContents_5.setObjectName("dockWidgetContents_5")
        self.verticalLayout_3 = QVBoxLayout(self.dockWidgetContents_5)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.SegmentSetting = QWidget(self.dockWidgetContents_5)
        self.SegmentSetting.setObjectName("SegmentSetting")

        self.verticalLayout_3.addWidget(self.SegmentSetting)

        self.dockWidget_3.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget_3
        )
        self.dockWidget_4.raise_()

        self.menuBar.addAction(self.muFile.menuAction())
        self.menuBar.addAction(self.menu.menuAction())
        self.menuBar.addAction(self.muView.menuAction())
        self.muFile.addAction(self.open_action)
        self.muFile.addAction(self.add_action)
        self.muFile.addAction(self.save_action)
        self.muFile.addAction(self.exit_action)
        self.muView.addAction(self.file_action)
        self.muView.addAction(self.paint_action)
        self.muView.addAction(self.menu_3.menuAction())
        self.menu_3.addAction(self.information_action)
        self.menu_3.addAction(self.direction_action)
        self.menu_3.addAction(self.crossline_action)
        self.menu.addAction(self.filesetting_action)
        self.menu.addAction(self.imageseting_action)
        self.menu.addAction(self.segmentsetting_action)
        self.menu.addAction(self.info_action)
        self.menu.addSeparator()
        self.menu.addAction(self.menutheme.menuAction())
        self.menu.addSeparator()
        self.menu.addAction(self.shortcut_action)
        self.menutheme.addAction(self.dark_action)
        self.menutheme.addAction(self.light_action)
        self.toolBar.addAction(self.data_atn)
        self.toolBar.addAction(self.setting_atn)
        self.toolBar_file.addAction(self.load_atn)
        self.toolBar_file.addAction(self.add_atn)
        self.toolBar_file.addAction(self.save_atn)
        self.toolBar_draw.addAction(self.aim_atn)
        self.toolBar_draw.addAction(self.move_atn)
        self.toolBar_draw.addAction(self.win_atn)
        self.toolBar_draw.addAction(self.paint_atn)
        self.toolBar_draw.addAction(self.eraser_atn)
        self.toolBar_run.addAction(self.sam_atn)
        self.toolBar_run.addAction(self.redo_atn)

        self.retranslateUi(MainWindow)
        self.sldLayer.valueChanged.connect(self.boxLayer.setValue)
        self.boxLayer.valueChanged.connect(self.sldLayer.setValue)

        self.stackedWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "MainWindow", None)
        )
        self.setting_atn.setText(
            QCoreApplication.translate("MainWindow", "\u8bbe\u7f6e", None)
        )
        self.load_atn.setText(
            QCoreApplication.translate("MainWindow", "\u5bfc\u5165", None)
        )
        # if QT_CONFIG(shortcut)
        self.load_atn.setShortcut(
            QCoreApplication.translate("MainWindow", "Ctrl+O", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.save_atn.setText(
            QCoreApplication.translate("MainWindow", "\u4fdd\u5b58", None)
        )
        # if QT_CONFIG(shortcut)
        self.save_atn.setShortcut(
            QCoreApplication.translate("MainWindow", "Ctrl+S", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.move_atn.setText(
            QCoreApplication.translate("MainWindow", "\u79fb\u52a8", None)
        )
        self.win_atn.setText(
            QCoreApplication.translate("MainWindow", "\u8c03\u7a97", None)
        )
        self.paint_atn.setText(
            QCoreApplication.translate("MainWindow", "\u6807\u6ce8", None)
        )
        self.eraser_atn.setText(
            QCoreApplication.translate("MainWindow", "\u64e6\u9664", None)
        )
        self.exit_action.setText(
            QCoreApplication.translate("MainWindow", "\u9000\u51fa", None)
        )
        self.save_action.setText(
            QCoreApplication.translate("MainWindow", "\u4fdd\u5b58\u4e3a", None)
        )
        self.open_action.setText(
            QCoreApplication.translate(
                "MainWindow", "\u6253\u5f00\u6587\u4ef6\u5939", None
            )
        )
        self.sam_atn.setText(QCoreApplication.translate("MainWindow", "SAM", None))
        self.file_action.setText(
            QCoreApplication.translate(
                "MainWindow", "\u6587\u4ef6\u5de5\u5177\u680f", None
            )
        )
        self.paint_action.setText(
            QCoreApplication.translate(
                "MainWindow", "\u56fe\u50cf\u5de5\u5177\u680f", None
            )
        )
        self.aim_atn.setText(
            QCoreApplication.translate("MainWindow", "\u51c6\u5fc3", None)
        )
        self.crossline_action.setText(
            QCoreApplication.translate("MainWindow", "\u5b9a\u4f4d\u7ebf", None)
        )
        self.redo_atn.setText(
            QCoreApplication.translate("MainWindow", "\u91cd\u505a", None)
        )
        self.add_action.setText(
            QCoreApplication.translate("MainWindow", "\u5bfc\u5165\u6807\u6ce8", None)
        )
        self.add_atn.setText(
            QCoreApplication.translate("MainWindow", "\u5bfc\u5165\u6807\u6ce8", None)
        )
        # if QT_CONFIG(shortcut)
        self.add_atn.setShortcut(
            QCoreApplication.translate("MainWindow", "Ctrl+A", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.imageseting_action.setText(
            QCoreApplication.translate("MainWindow", "\u56fe\u50cf\u8bbe\u7f6e", None)
        )
        self.segmentsetting_action.setText(
            QCoreApplication.translate("MainWindow", "\u6807\u6ce8\u8bbe\u7f6e", None)
        )
        self.info_action.setText(
            QCoreApplication.translate("MainWindow", "\u4fe1\u606f\u8bbe\u7f6e", None)
        )
        self.dark_action.setText(
            QCoreApplication.translate("MainWindow", "\u6697", None)
        )
        # if QT_CONFIG(tooltip)
        self.dark_action.setToolTip(
            QCoreApplication.translate("MainWindow", "\u6697", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.light_action.setText(
            QCoreApplication.translate("MainWindow", "\u4eae", None)
        )
        # if QT_CONFIG(tooltip)
        self.light_action.setToolTip(
            QCoreApplication.translate("MainWindow", "\u4eae", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.filesetting_action.setText(
            QCoreApplication.translate("MainWindow", "\u6587\u4ef6\u7ba1\u7406", None)
        )
        self.data_atn.setText(
            QCoreApplication.translate("MainWindow", "\u6570\u636e", None)
        )
        # if QT_CONFIG(tooltip)
        self.data_atn.setToolTip(
            QCoreApplication.translate("MainWindow", "\u5bfc\u5165\u6570\u636e", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.about_action.setText(
            QCoreApplication.translate("MainWindow", "\u5173\u4e8e", None)
        )
        self.github_action.setText(
            QCoreApplication.translate("MainWindow", "github", None)
        )
        self.actionhelp.setText(
            QCoreApplication.translate("MainWindow", "\u5e2e\u52a9", None)
        )
        self.direction_action.setText(
            QCoreApplication.translate("MainWindow", "\u65b9\u4f4d", None)
        )
        self.information_action.setText(
            QCoreApplication.translate("MainWindow", "\u60a3\u8005\u540d", None)
        )
        self.shortcut_action.setText(
            QCoreApplication.translate("MainWindow", "\u5feb\u6377\u952e", None)
        )
        self.shortcut_action.setIconText(
            QCoreApplication.translate("MainWindow", "\u5feb\u6377\u952e", None)
        )
        self.boxPET.setText(QCoreApplication.translate("MainWindow", "PET", None))
        self.boxCT.setText(QCoreApplication.translate("MainWindow", "CT", None))
        self.boxSeg.setText(QCoreApplication.translate("MainWindow", "Seg", None))
        self.btnCa.setText(
            QCoreApplication.translate("MainWindow", "\u622a\u56fe", None)
        )
        self.btnH.setText(QCoreApplication.translate("MainWindow", "\u6a2a", None))
        self.btnS.setText(QCoreApplication.translate("MainWindow", "\u77e2", None))
        self.btnG.setText(QCoreApplication.translate("MainWindow", "\u51a0", None))
        self.btn3D.setText(QCoreApplication.translate("MainWindow", "3D", None))
        self.btnRefresh.setText(
            QCoreApplication.translate("MainWindow", "\u5237\u65b0", None)
        )
        self.btnReset.setText(
            QCoreApplication.translate("MainWindow", "\u590d\u4f4d", None)
        )
        self.muFile.setTitle(
            QCoreApplication.translate("MainWindow", "\u6587\u4ef6", None)
        )
        self.muView.setTitle(
            QCoreApplication.translate("MainWindow", "\u89c6\u56fe", None)
        )
        self.menu_3.setTitle(
            QCoreApplication.translate("MainWindow", "\u56fe\u50cf\u4fe1\u606f", None)
        )
        self.menu.setTitle(
            QCoreApplication.translate("MainWindow", "\u7f16\u8f91", None)
        )
        self.menutheme.setTitle(
            QCoreApplication.translate("MainWindow", "\u4e3b\u9898", None)
        )
        self.toolBar.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u4fa7\u680f", None)
        )
        self.toolBar_file.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u4e3b\u5de5\u5177\u680f", None)
        )
        self.toolBar_draw.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u5de5\u5177", None)
        )
        self.toolBar_run.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u7a0b\u5e8f", None)
        )
        self.dockWidget.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u56fe\u50cf\u8bbe\u7f6e", None)
        )
        self.dockWidget_4.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u4fe1\u606f\u663e\u793a", None)
        )
        self.dockWidget_2.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u6587\u4ef6\u7ba1\u7406", None)
        )
        self.dockWidget_3.setWindowTitle(
            QCoreApplication.translate("MainWindow", "\u6807\u6ce8\u8bbe\u7f6e", None)
        )

    # retranslateUi
