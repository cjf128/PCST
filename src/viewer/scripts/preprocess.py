# Copyright (c) 2026 PCViewer Jinfr
from pathlib import Path

import SimpleITK as sitk

from viewer.scripts.basic import read_dicom_series, resize_image
from viewer.scripts.pettosuv import pet_to_suv


def process_dicom_data(ct_folder: str, pet_folder: str):
    # 原始CT处理
    ct_img = read_dicom_series(ct_folder, "CT")
    ct_spacing = ct_img.GetSpacing()
    ct_data = sitk.GetArrayFromImage(ct_img)

    # 原始PET处理
    pet_suv_img = pet_to_suv(pet_folder)
    pet_spacing = pet_suv_img.GetSpacing()
    pet_shape = sitk.GetArrayFromImage(pet_suv_img).shape

    # 最后配准
    pet_data = resize_image(pet_suv_img, ct_img, sitk.sitkLinear)
    pet_data = sitk.GetArrayFromImage(pet_data)
    return ct_data, pet_data, ct_spacing, pet_spacing, pet_shape


def process_nifti_data(pet_path: Path, ct_path: Path):
    # 原始CT处理
    ct_img = sitk.ReadImage(ct_path)
    ct_img = sitk.DICOMOrient(ct_img, "LPS")
    ct_spacing = ct_img.GetSpacing()
    ct_data = sitk.GetArrayFromImage(ct_img)

    # 原始PET处理
    pet_img = sitk.ReadImage(pet_path)
    pet_img = sitk.DICOMOrient(pet_img, "LPS")
    pet_spacing = pet_img.GetSpacing()
    pet_shape = sitk.GetArrayFromImage(pet_img).shape

    # 最后配准
    pet_data = resize_image(pet_img, ct_img, sitk.sitkLinear)
    pet_data = sitk.GetArrayFromImage(pet_data)
    return ct_data, pet_data, ct_spacing, pet_spacing, pet_shape
