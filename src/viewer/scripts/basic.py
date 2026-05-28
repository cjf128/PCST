# Copyright (c) 2026 PCViewer Jinfr
from typing import Optional

import SimpleITK as sitk


def read_dicom_series(directory: str, modality: Optional[str] = None) -> sitk.Image:
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(directory)
    reader.SetFileNames(dicom_names)
    img = reader.Execute()

    if modality and modality.lower() == "ct":
        stats_filter = sitk.StatisticsImageFilter()
        stats_filter.Execute(img)
        if stats_filter.GetMinimum() >= 0:
            img = img - 1024.0

    return img


def clamp_window(
    image: sitk.Image, window_width: float, window_level: float
) -> sitk.Image:
    upper = window_level + window_width / 2
    lower = window_level - window_width / 2
    return sitk.Clamp(
        sitk.Cast(image, sitk.sitkFloat32),
        sitk.sitkFloat32,
        lower,
        upper,
    )


def clamp_value(image: sitk.Image, lower: float, upper: float) -> sitk.Image:
    return sitk.Clamp(
        sitk.Cast(image, sitk.sitkFloat32),
        sitk.sitkFloat32,
        lower,
        upper,
    )


def resize_image(
    source_img: sitk.Image,
    target_img: sitk.Image,
    interpolator: int = sitk.sitkLinear,
) -> sitk.Image:
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(target_img)
    resampler.SetSize(target_img.GetSize())
    resampler.SetOutputOrigin(target_img.GetOrigin())
    resampler.SetOutputDirection(target_img.GetDirection())
    resampler.SetOutputSpacing(target_img.GetSpacing())
    resampler.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler.SetInterpolator(interpolator)

    if interpolator == sitk.sitkNearestNeighbor:
        resampler.SetOutputPixelType(sitk.sitkUInt8)
    else:
        resampler.SetOutputPixelType(sitk.sitkFloat32)

    resampled = resampler.Execute(source_img)
    resampled.CopyInformation(target_img)
    return resampled
