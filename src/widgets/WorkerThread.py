# Copyright (c) 2026 PCViewer Jinfr
import shutil
from pathlib import Path
from typing import Tuple

import numpy as np
import SimpleITK as sitk
import vtk
from PySide6.QtCore import QThread, Signal
from vtkmodules.util import numpy_support

from path import MODELS_PATH
from scripts.logger import log_debug, log_error, log_info
from scripts.preprocess import process_dicom_data, process_nifti_data
from scripts.sort_dicom import sort_dicom_series


class DicomWorker(QThread):
    finished = Signal(np.ndarray, np.ndarray, tuple, tuple, tuple, dict)

    def __init__(self, pet_file: Path, ct_file: Path, cache_folder: Path):
        super().__init__()
        self.pet_file = pet_file
        self.ct_file = ct_file
        self.cache_folder = cache_folder

    def run(self):
        ct_folder = self.cache_folder / "CT"
        pet_folder = self.cache_folder / "PET"
        ct_folder.mkdir(exist_ok=True)
        pet_folder.mkdir(exist_ok=True)

        success_ct, msg_ct = sort_dicom_series(
            self.ct_file, ct_folder, pet_folder
        )
        log_info(f"CT处理结果: {msg_ct}")

        success_pet, msg_pet = sort_dicom_series(
            self.pet_file, ct_folder, pet_folder
        )
        log_info(f"PET处理结果: {msg_pet}")

        if not success_ct or not success_pet:
            log_error("DICOM文件处理失败")
            return

        log_info("开始处理DICOM数据")
        try:
            ct_data, pet_data, ct_spacing, pet_spacing, pet_shape = process_dicom_data(
                str(ct_folder), str(pet_folder)
            )

            # 提取患者信息
            patient_info = {}
            # 从DICOM文件中提取患者信息
            try:
                # 获取CT文件夹中的第一个DICOM文件
                ct_files = list(ct_folder.glob("*.dcm"))
                if ct_files:
                    ct_file = str(ct_files[0])
                    img = sitk.ReadImage(ct_file)
                    # 提取DICOM标签
                    if "0010|0010" in img.GetMetaDataKeys():
                        patient_info["患者名"] = img.GetMetaData("0010|0010")
                    if "0010|0020" in img.GetMetaDataKeys():
                        patient_info["患者ID"] = img.GetMetaData("0010|0020")
                    if "0010|0030" in img.GetMetaDataKeys():
                        patient_info["出生日期"] = img.GetMetaData("0010|0030")
                    if "0010|0040" in img.GetMetaDataKeys():
                        patient_info["性别"] = img.GetMetaData("0010|0040")
                    if "0010|1030" in img.GetMetaDataKeys():
                        patient_info["体重"] = img.GetMetaData("0010|1030")
            except Exception as e:
                log_error(f"提取DICOM患者信息时发生错误: {e}")

            shutil.rmtree(str(ct_folder))
            shutil.rmtree(str(pet_folder))

            log_info(
                f"DICOM数据处理完成, CT形状: {ct_data.shape}, PET形状: {pet_shape}"
            )
            self.finished.emit(
                ct_data, pet_data, ct_spacing, pet_spacing, pet_shape, patient_info
            )
        except Exception as e:
            log_error(f"处理DICOM数据时发生错误: {e}")


class NiftiWorker(QThread):
    finished = Signal(np.ndarray, np.ndarray, tuple, tuple, tuple)

    def __init__(self, pet_path: Path, ct_path: Path):
        super().__init__()
        self.pet_path = pet_path
        self.ct_path = ct_path

    def run(self):
        log_info("开始处理NIfTI数据")
        try:
            ct_data, pet_data, ct_spacing, pet_spacing, pet_shape = process_nifti_data(
                self.pet_path, self.ct_path
            )

            log_info(
                f"NIfTI数据处理完成, CT形状: {ct_data.shape}, PET形状: {pet_shape}"
            )
            self.finished.emit(ct_data, pet_data, ct_spacing, pet_spacing, pet_shape)
        except Exception as e:
            log_error(f"处理NIfTI数据时发生错误: {e}")


class SamThread(QThread):
    finished = Signal(np.ndarray)

    def __init__(
        self, predictor, current_slice, input_data, mode, change_image_mode=True
    ):
        super().__init__()
        self.predictor = predictor
        self.current_slice = current_slice
        self.input_data = input_data
        self.mode = mode
        self.change_image_mode = change_image_mode

    def _normalize_box(self) -> Tuple[int, int, int, int]:
        box = self.input_data.copy()
        if box[0] > box[2]:
            box[0], box[2] = box[2], box[0]
        if box[1] > box[3]:
            box[1], box[3] = box[3], box[1]
        return int(box[0]), int(box[1]), int(box[2]), int(box[3])

    def run(self):
        log_debug(f"开始SAM预测, 模式: {self.mode}, 输入数据: {self.input_data}")
        try:
            if self.change_image_mode:
                self.predictor.set_image(self.current_slice)

            if self.mode == "BOX":
                # BOX模式
                x1, y1, x2, y2 = self._normalize_box()
                masks = self.predictor.set_box(((x1, y1), (x2, y2)), label_id=0)
                mask = masks[0].astype(np.uint8)
            elif self.mode in ["ADD", "SUB"]:
                # ADD或SUB模式
                point_coords = self.input_data
                masks = self.predictor.add_point(point_coords, True, label_id=0)
                mask = masks[0].astype(np.uint8)
            else:
                log_error(f"未知的SAM模式: {self.mode}")
                return

            log_debug(f"SAM预测完成, mask形状: {mask.shape}")
            self.finished.emit(mask)
        except Exception as e:
            log_error(f"SAM预测时发生错误: {e}")
            import traceback

            traceback.print_exc()


class ModelLoader(QThread):
    finished = Signal(object)

    _ENCODER_MODEL = "checkpoints/sam2.1_hiera_base_plus_encoder.onnx"
    _DECODER_MODEL = "checkpoints/sam2.1_hiera_base_plus_decoder.onnx"

    def run(self):
        log_info("开始加载SAM2模型")
        try:
            from models.sam2 import SAM2Image

            encoder_path = MODELS_PATH / self._ENCODER_MODEL
            decoder_path = MODELS_PATH / self._DECODER_MODEL

            log_debug(f"编码器路径: {encoder_path}")
            log_debug(f"解码器路径: {decoder_path}")

            predictor = SAM2Image(str(encoder_path), str(decoder_path))
            log_info("SAM2模型加载完成")
            self.finished.emit(predictor)
        except Exception as e:
            log_error(f"加载SAM2模型时发生错误: {e}")


class BuiltThread(QThread):
    actor_ready = Signal(object)

    def __init__(
        self,
        data: np.ndarray,
        spacing: Tuple[float, float, float],
        label_config: None | dict,
    ):
        super().__init__()
        self.data = data
        self.spacing = spacing
        self.label_config = label_config or {}

    def _create_lookup_table(self) -> vtk.vtkLookupTable:
        # 计算需要的颜色表大小
        max_label = 0
        if self.label_config:
            max_label = max(int(label_id) for label_id in self.label_config.keys())
        # 确保至少有3个颜色值
        num_values = max(max_label + 1, 3)

        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(num_values)

        # 设置背景颜色（标签0）
        lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)

        # 根据标签配置设置颜色
        for label_id, label_info in self.label_config.items():
            try:
                label_idx = int(label_id)
                if label_idx > 0 and label_idx < num_values:
                    # 解析颜色值
                    color_hex = label_info.get("color", "#0000FF")
                    # 移除 # 号
                    if color_hex.startswith("#"):
                        color_hex = color_hex[1:]
                    # 解析 RGB 值
                    r = int(color_hex[0:2], 16) / 255.0
                    g = int(color_hex[2:4], 16) / 255.0
                    b = int(color_hex[4:6], 16) / 255.0
                    # 设置颜色
                    lut.SetTableValue(label_idx, r, g, b, 1.0)
            except (ValueError, IndexError):
                pass

        # 设置默认颜色（如果标签配置中没有）
        for i in range(1, num_values):
            # 检查是否已经设置了颜色
            has_color = False
            for label_id in self.label_config:
                if int(label_id) == i:
                    has_color = True
                    break
            if not has_color:
                # 设置默认颜色
                if i == 1:
                    lut.SetTableValue(i, 0.0, 0.0, 1.0, 1.0)  # 蓝色
                elif i == 2:
                    lut.SetTableValue(i, 0.0, 1.0, 0.0, 1.0)  # 绿色
                else:
                    # 生成其他默认颜色
                    hue = (i - 3) / 6.0
                    r, g, b = self._hue_to_rgb(hue)
                    lut.SetTableValue(i, r, g, b, 1.0)

        lut.SetRange(0, num_values - 1)
        lut.Build()
        return lut

    def _hue_to_rgb(self, hue):
        """将色相转换为RGB颜色"""
        hue = hue % 1.0
        if hue < 1 / 6:
            return 1.0, hue * 6.0, 0.0
        elif hue < 1 / 3:
            return (1 / 3 - hue) * 6.0, 1.0, 0.0
        elif hue < 1 / 2:
            return 0.0, 1.0, (hue - 1 / 3) * 6.0
        elif hue < 2 / 3:
            return 0.0, (2 / 3 - hue) * 6.0, 1.0
        elif hue < 5 / 6:
            return (hue - 2 / 3) * 6.0, 0.0, 1.0
        else:
            return 1.0, 0.0, (1.0 - hue) * 6.0

    def run(self):
        log_debug(f"开始3D重建, 数据形状: {self.data.shape}")
        try:
            image_data = np.ascontiguousarray(self.data)

            vtk_data = vtk.vtkImageData()
            d, h, w = image_data.shape
            vtk_data.SetDimensions(w, h, d)
            vtk_data.SetSpacing(self.spacing)

            vtk_arr = numpy_support.numpy_to_vtk(
                image_data.ravel(), deep=True, array_type=vtk.VTK_UNSIGNED_SHORT
            )
            vtk_data.GetPointData().SetScalars(vtk_arr)

            # 计算需要生成的值范围
            max_label = 0
            if self.label_config:
                max_label = max(int(label_id) for label_id in self.label_config.keys())
            # 确保至少生成1和2
            max_value = max(max_label, 2)

            dmc = vtk.vtkDiscreteMarchingCubes()
            dmc.SetInputData(vtk_data)
            dmc.GenerateValues(max_value, 1, max_value)
            dmc.Update()

            smoother = vtk.vtkWindowedSincPolyDataFilter()
            smoother.SetInputConnection(dmc.GetOutputPort())
            smoother.SetNumberOfIterations(20)
            smoother.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(smoother.GetOutputPort())
            lut = self._create_lookup_table()
            mapper.SetLookupTable(lut)
            # 使用颜色表的实际范围
            mapper.SetScalarRange(lut.GetRange())
            mapper.ScalarVisibilityOn()

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetInterpolationToGouraud()
            actor.GetProperty().SetAmbient(0.2)
            actor.GetProperty().SetDiffuse(0.8)

            log_debug("3D重建完成")
            self.actor_ready.emit(actor)
        except Exception as e:
            log_error(f"3D重建时发生错误: {e}")
