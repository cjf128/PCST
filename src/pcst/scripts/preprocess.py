# Copyright (c) 2026 PCST Jinfr
from pathlib import Path

import SimpleITK as sitk

from pcst.core.geometry import VolumeGeometry
from pcst.io.nifti_reader import read_nifti_sitk
from pcst.scripts.basic import read_dicom_series, resize_image
from pcst.scripts.pet2suv import pet_to_suv


def process_dicom_data(ct_folder: str, pet_folder: str):
    # 原始CT处理
    ct_img = read_dicom_series(ct_folder, "CT")
    # 所有后续 viewer/annotation 均使用 LPS；方向信息不能在转 NumPy 时丢失。
    ct_img = sitk.DICOMOrient(ct_img, "LPS")
    ct_geometry = VolumeGeometry.from_sitk(ct_img)
    ct_spacing = ct_img.GetSpacing()
    ct_data = sitk.GetArrayFromImage(ct_img)

    # 原始PET处理
    pet_suv_img = pet_to_suv(pet_folder)
    pet_suv_img = sitk.DICOMOrient(pet_suv_img, "LPS")
    pet_geometry = VolumeGeometry.from_sitk(pet_suv_img)
    pet_spacing = pet_suv_img.GetSpacing()
    pet_shape = sitk.GetArrayFromImage(pet_suv_img).shape

    # 最后配准
    pet_data = resize_image(pet_suv_img, ct_img, sitk.sitkLinear)
    pet_data = sitk.GetArrayFromImage(pet_data)
    return (
        ct_data,
        pet_data,
        ct_spacing,
        pet_spacing,
        pet_shape,
        ct_geometry,
        pet_geometry,
    )


def process_nifti_data(pet_path: Path, ct_path: Path):
    # 原始CT处理
    ct_img = read_nifti_sitk(ct_path, orient_lps=True)
    ct_geometry = VolumeGeometry.from_sitk(ct_img)
    ct_spacing = ct_img.GetSpacing()
    ct_data = sitk.GetArrayFromImage(ct_img)

    # 原始PET处理
    pet_img = read_nifti_sitk(pet_path, orient_lps=True)
    pet_geometry = VolumeGeometry.from_sitk(pet_img)
    pet_spacing = pet_img.GetSpacing()
    pet_shape = sitk.GetArrayFromImage(pet_img).shape

    # 最后配准
    pet_data = resize_image(pet_img, ct_img, sitk.sitkLinear)
    pet_data = sitk.GetArrayFromImage(pet_data)
    return (
        ct_data,
        pet_data,
        ct_spacing,
        pet_spacing,
        pet_shape,
        ct_geometry,
        pet_geometry,
    )
