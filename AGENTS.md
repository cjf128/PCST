# AGENTS.md

# Todo

* [ ] 更换为mobile SAM2 onnx
* [ ] 初始化状态为准星

## 项目概述

PCViewer 是一款基于 PySide6 的 PET/CT 图像全身病灶分割桌面软件，支持横断面/矢状面/冠状面及 3D 视图，集成 SAM2（Segment Anything Model 2）ONNX 模型实现半自动分割。

## 开发命令

```bash
# 安装依赖（使用 uv）
uv sync

# 运行应用
python main.py

# 使用 Nuitka 编译打包
python -m nuitka --standalone --windows-console-mode=disable --enable-plugins=pyside6 main.py
```

## 架构概览

```
main.py          → 入口，初始化 QApplication + App
app/
  app.py         → App 类：加载配置、设置主题、创建 MainWindow
  configs.py     → AppConfig 数据类 + ConfigManager（YAML 读写 config.yaml）
  mode.py        → 枚举：VIEWERMode / LOADMode / VIEWMode / SAMMode
models/
  sam2.py        → SAM2Image 封装：Encoder + Decoder ONNX 推理
widgets/
  MainWindow.py  → 主窗口：所有业务逻辑中心（图像加载、标注绘制、SAM调用、3D重建、撤销重做）
  ImageViewer.py → QGraphicsView 子类：图像渲染、鼠标交互、标注绘制
  WorkerThread.py → 后台线程：DicomWorker / NiftiWorker / SamThread / ModelLoader / BuiltThread(3D)
  SegmentDocker.py → 右侧标注管理面板（标签增删改色、SAM模式切换）
  ImageDocker.py  → 图像设置面板（窗宽窗位、透明度、预设窗）
  FileDocker.py   → 文件列表面板（已导入数据管理、重命名、删除）
  InfoDocker.py   → 信息面板（DICOM 患者信息、图像统计值）
  LoadDialog.py   → 数据导入对话框（NIfTI/DICOM 选择）
  ShortcutDialog.py → 快捷键设置对话框
scripts/
  basic.py       → SimpleITK 工具函数（DICOM 序列读取、窗宽窗位、图像重采样）
  PET2SUV.py     → PET DICOM 转 SUV 值
  preprocess.py  → 数据预处理管线（DICOM/NIfTI → 配准后的 numpy 数组）
  sort_dicom.py  → DICOM 序列分拣（按 modality 分离 CT/PET）
  theme.py       → ThemeManager：dark/light 双主题 QPalette
  logger.py      → 日志系统（文件 + 控制台，保留最近 7 个日志文件）
ui/
  *_ui.py        → Qt Designer 生成的 UI 类（MainWindow_ui、SegmentDock_ui 等）
path.py          → 路径常量（BASE_PATH、ICONS_PATH、MODELS_PATH、CACHE_PATH、LOGS_PATH）
config.yaml      → 运行时配置（已导入数据列表、标签定义、快捷键绑定、主题）
```

## 核心数据流

1. **数据加载**：`LoadDialog` → `MainWindow.on_files_selected()` → 根据文件类型派发 `DicomWorker` 或 `NiftiWorker` → `on_data_loaded()` 接收 numpy 数组
2. **图像融合显示**：`prepare_image()` 将 CT/PET 按窗宽窗位归一化后加权叠加（alpha blending），叠加 segmentation overlay
3. **视图切换**：`change_slot()` 按 `transpose()` 矩阵重排 CT/PET/seg 三数组的轴，切换 AXIAL/SAGITTAL/CORONAL
4. **SAM 分割**：`ImageViewer` 捕获鼠标交互 → `Sam_Signal` → `MainWindow.operation()` 启动 `SamThread` → 回调将 mask 写入 `self.seg[:, :, layer]`
5. **3D 重建**：`view_3d_built()` → `BuiltThread` 用 VTK `DiscreteMarchingCubes` + `WindowedSincPolyDataFilter` 构建 mesh，带 hash 缓存
6. **撤销重做**：每层分割修改通过 `SegChangeCommand`（QUndoCommand 子类）压入 `QUndoStack`，仅存储修改层的 2D 切片副本

## 关键约定

- **配置持久化**：所有运行时状态（导入数据路径、标签定义、快捷键、主题）通过 `ConfigManager` 写入 `config.yaml`
- **缓存/日志清理**：应用退出时自动清理 `data/cache/` 目录；日志最多保留 7 个文件
- **DICOM 数据流**：原始 DICOM 文件 → `sort_dicom_series()` 按 modality 分拣到临时目录 → `process_dicom_data()` 处理后删除临时文件
- **PET 数据处理**：DICOM 格式的 PET 会先通过 `pet_to_suv()` 转换为 SUV 值，再配准到 CT 空间
- **视图坐标系统**：所有视图统一使用 LPS 方向（`sitk.DICOMOrient`），`transpose()` 方法管理不同视图间的坐标转换
- **快捷键**：从 `config.yaml` 的 `shortcuts` 节加载，支持通过 `ShortcutDialog` 运行时修改并持久化
