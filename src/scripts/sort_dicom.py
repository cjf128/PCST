# Copyright (c) 2026 PCViewer Jinfr
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pydicom

from scripts.logger import log_debug, log_error, log_info, log_warning


@dataclass
class SeriesInfo:
    series_uid: str
    study_uid: Optional[str]
    modality: str
    description: str
    series_number: Optional[int]
    files: List[Path]


DICOM_EXTENSIONS = {".dcm", ".ima", ""}


def _get_series_info(dicom_file: Path) -> Optional[SeriesInfo]:
    try:
        ds = pydicom.dcmread(str(dicom_file), stop_before_pixels=True)
        return SeriesInfo(
            series_uid=getattr(ds, "SeriesInstanceUID", ""),
            study_uid=getattr(ds, "StudyInstanceUID", None),
            modality=getattr(ds, "Modality", ""),
            description=getattr(ds, "SeriesDescription", ""),
            series_number=getattr(ds, "SeriesNumber", None),
            files=[dicom_file],
        )
    except Exception as e:
        log_error(f"读取DICOM文件失败: {dicom_file}, 错误: {e}")
        return None


def _find_series_files(dicom_file: Path, search_parent: bool = True) -> List[Path]:
    series_info = _get_series_info(dicom_file)
    if not series_info or not series_info.series_uid:
        log_warning(f"无法获取序列信息: {dicom_file}")
        return [dicom_file]

    target_uid = series_info.series_uid
    log_debug(f"目标序列UID: {target_uid}")

    search_dir = dicom_file.parent
    if search_parent and search_dir.name in {"CT", "PET", "PT"}:
        search_dir = search_dir.parent

    series_files = []
    for file_path in search_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in DICOM_EXTENSIONS:
            try:
                ds = pydicom.dcmread(str(file_path), stop_before_pixels=True)
                if getattr(ds, "SeriesInstanceUID", None) == target_uid:
                    series_files.append(file_path)
            except Exception:
                continue

    if not series_files:
        series_files = [dicom_file]

    log_info(f"找到序列文件 {len(series_files)} 个")
    return series_files


def _copy_dicom_file(src: Path, dst_dir: Path) -> bool:
    try:
        if src.suffix.upper() == ".IMA":
            ds = pydicom.dcmread(str(src))
            dst = dst_dir / (src.stem + ".dcm")
            ds.save_as(str(dst))
        else:
            shutil.copy2(str(src), str(dst_dir / src.name))
        return True
    except Exception as e:
        log_error(f"复制文件失败: {src}, 错误: {e}")
        return False


def sort_dicom_series(
    dicom_file: Path,
    ct_path: Path,
    pet_path: Path,
) -> Tuple[bool, str]:
    dicom_file = dicom_file
    ct_dir = ct_path
    pet_dir = pet_path

    ct_dir.mkdir(parents=True, exist_ok=True)
    pet_dir.mkdir(parents=True, exist_ok=True)

    series_info = _get_series_info(dicom_file)
    if not series_info:
        return False, "无法读取DICOM文件信息"

    modality = series_info.modality
    log_info(f"检测到模态: {modality}")

    series_files = _find_series_files(dicom_file)

    if modality == "CT":
        target_dir = ct_dir
    elif modality in {"PT", "PET"}:
        target_dir = pet_dir
    else:
        return False, f"未知的模态类型: {modality}"

    log_info(f"复制{modality}序列文件到: {target_dir}")

    copied_count = sum(1 for src in series_files if _copy_dicom_file(src, target_dir))

    msg = f"成功复制 {copied_count} 个 {modality} 文件"
    log_info(msg)
    return True, msg


def analyze_folder_series(folder_path: str) -> List[SeriesInfo]:
    folder = Path(folder_path)
    series_dict: dict = {}

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            ds = pydicom.dcmread(str(file_path), stop_before_pixels=True)
            series_uid = getattr(ds, "SeriesInstanceUID", None)
            modality = getattr(ds, "Modality", None)

            if series_uid and modality:
                if series_uid not in series_dict:
                    series_dict[series_uid] = SeriesInfo(
                        series_uid=series_uid,
                        study_uid=getattr(ds, "StudyInstanceUID", None),
                        modality=modality,
                        description=getattr(ds, "SeriesDescription", ""),
                        series_number=getattr(ds, "SeriesNumber", None),
                        files=[],
                    )
                series_dict[series_uid].files.append(file_path)
        except Exception:
            continue

    return list(series_dict.values())
