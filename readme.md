# PCST

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/) [![Framework](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython/) [![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](LICENSE)

PCST 是一款基于 SAM 的 PET/CT 图像全身病灶分割软件，提供影像分析、病灶分割、标注管理和 3D 可视化功能。

![PCST SAM 分割](assets/mobilesam.png)

---

## 主要功能

- **文件管理**：支持导入、重命名、删除PET/CT数据
- **图像查看**：支持横断面、矢状面、冠状面和3D视图
- **图像分割**：支持手动绘制和SAM（Segment Anything Model）自动分割
- **数据存储**：将导入的文件路径记录到YAML配置文件
- **实时反馈**：运行SAM时显示进度弹窗

![image](assets/image.png)

---

## 环境要求

- Python 3.12+

### 使用pip安装

```bash
pip install -e.
```

### 使用uv

```bash
uv sync
```

### 使用前先准备 ONNX 模型与示例数据

将 [MobileSAM ONNX](https://huggingface.co/datasets/Jinfr/PCST/tree/main) 模型放到 `src/pcst/models/checkpoints` 下，文件名保持为 `mobile_sam_encoder.onnx` 和 `mobile_sam_decoder.onnx`。

### 运行软件

```bash
uv run pcst
```

---

## 开源协议

本项目采用 **Apache License 2.0** 开源协议。
在遵守许可证条款的前提下，允许自由使用、修改和分发。

---

## 免责声明

本软件仅用于科研与教学目的，
不作为临床诊断或治疗决策的直接依据。

---

# 参考:

Segment Anything: https://github.com/facebookresearch/segment-anything

MobileSAM: https://github.com/ChaoningZhang/MobileSAM

-----------------------------------------------------
